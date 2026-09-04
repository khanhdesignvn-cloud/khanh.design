"""Private learning portal domain service for the six-week course."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import tempfile
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

RUBRIC_KEYS = ("completeness", "quality", "safety", "repeatability")
WEEKS = (
    {"week": 1, "title": "Làm chủ Claude và tư duy giao việc", "artifact": "Bản đồ cơ hội AI và ba quy trình ưu tiên", "rubric": RUBRIC_KEYS},
    {"week": 2, "title": "Xây trợ lý hiểu doanh nghiệp", "artifact": "Claude Project, hồ sơ doanh nghiệp và checklist chất lượng", "rubric": RUBRIC_KEYS},
    {"week": 3, "title": "Xây hệ thống nội dung marketing", "artifact": "Lịch nội dung 7 ngày và gói nội dung đa kênh", "rubric": RUBRIC_KEYS},
    {"week": 4, "title": "Xây trợ lý bán hàng", "artifact": "Kịch bản khám phá, xử lý từ chối và chuỗi theo dõi ba chạm", "rubric": RUBRIC_KEYS},
    {"week": 5, "title": "Chăm sóc khách hàng và vận hành", "artifact": "Bộ FAQ–chuyển cấp và một SOP nội bộ", "rubric": RUBRIC_KEYS},
    {"week": 6, "title": "Tự động hóa và bàn giao hệ thống", "artifact": "Workflow chạy thử và hồ sơ bàn giao bộ máy AI", "rubric": RUBRIC_KEYS},
)
REVIEW_STATUSES = frozenset({"SUBMITTED", "NEEDS_REVISION", "PASSED"})
TAG_PATTERN = re.compile(r"<[^>]*>")
PBKDF2_ROUNDS = 200_000


class PortalValidationError(ValueError):
    def __init__(self, fields: list[str]):
        super().__init__("invalid portal fields")
        self.fields = sorted(set(fields))


class PortalAuthenticationError(PermissionError):
    pass


def _clean_text(value: object, maximum: int) -> str | None:
    if not isinstance(value, str):
        return None
    value = unicodedata.normalize("NFC", value)
    value = " ".join(TAG_PATTERN.sub(" ", value).split())
    return value if value and len(value) <= maximum else None


def _phone_key(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    digits = re.sub(r"\D", "", value)
    if 8 <= len(digits) <= 15:
        return digits
    return None


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _derive_hash(value: str, salt: bytes) -> str:
    return _b64(hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt, PBKDF2_ROUNDS))


def _read_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"invalid list store: {path.name}")
    return value


def _read_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"invalid object store: {path.name}")
    return value


def _atomic_write(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try: os.unlink(temporary_name)
        except FileNotFoundError: pass
        raise


def public_weeks() -> list[dict[str, Any]]:
    return [{**item, "rubric": list(item["rubric"])} for item in WEEKS]


class CourseLearningPortal:
    def __init__(self, *, students_path: str | Path, submissions_path: str | Path, token_secret_path: str | Path, admin_key_path: str | Path, clock=time.time):
        self.students_path = Path(students_path)
        self.submissions_path = Path(submissions_path)
        self.token_secret_path = Path(token_secret_path)
        self.admin_key_path = Path(admin_key_path)
        self.clock = clock
        self.lock = threading.Lock()

    def _now_iso(self) -> str:
        return datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()

    def _token_secret(self) -> bytes:
        with self.lock:
            if self.token_secret_path.exists():
                secret = self.token_secret_path.read_bytes()
                if len(secret) < 32: raise ValueError("portal token secret is invalid")
                return secret
            self.token_secret_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            secret = secrets.token_bytes(32)
            descriptor = os.open(self.token_secret_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(secret); handle.flush(); os.fsync(handle.fileno())
            return secret

    def _issue_token(self, subject: str, role: str, ttl: int) -> str:
        payload = json.dumps({"sub": subject, "role": role, "exp": int(self.clock()) + ttl}, separators=(",", ":"), sort_keys=True).encode()
        encoded = _b64(payload)
        signature = _b64(hmac.new(self._token_secret(), encoded.encode(), hashlib.sha256).digest())
        return f"{encoded}.{signature}"

    def verify_token(self, token: str | None, role: str) -> str:
        if not token or "." not in token: raise PortalAuthenticationError
        encoded, signature = token.split(".", 1)
        expected = _b64(hmac.new(self._token_secret(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise PortalAuthenticationError
        try: payload = json.loads(_unb64(encoded))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError): raise PortalAuthenticationError from None
        if payload.get("role") != role or not isinstance(payload.get("sub"), str) or payload.get("exp", 0) <= self.clock():
            raise PortalAuthenticationError
        return payload["sub"]

    def activate_student(self, *, application_id: str, display_name: str, phone: str, cohort: str) -> dict[str, Any]:
        try: student_id = str(uuid.UUID(application_id))
        except (ValueError, AttributeError): raise PortalValidationError(["application_id"]) from None
        name = _clean_text(display_name, 120); phone_key = _phone_key(phone); cohort_value = _clean_text(cohort, 32)
        errors = [key for key, value in (("display_name", name), ("phone", phone_key), ("cohort", cohort_value)) if not value]
        if errors: raise PortalValidationError(errors)
        salt = secrets.token_bytes(16)
        record = {"id": student_id, "display_name": name, "phone_salt": _b64(salt), "phone_hash": _derive_hash(phone_key, salt), "active": True, "cohort": cohort_value, "activated_at": self._now_iso()}
        with self.lock:
            students = _read_list(self.students_path)
            students = [item for item in students if item.get("id") != student_id]
            students.append(record); _atomic_write(self.students_path, students)
        return {"id": student_id, "display_name": name, "cohort": cohort_value, "active": True}

    def configure_admin(self, key: str) -> None:
        clean = _clean_text(key, 256)
        if not clean or len(clean) < 12: raise PortalValidationError(["key"])
        salt = secrets.token_bytes(16)
        _atomic_write(self.admin_key_path, {"salt": _b64(salt), "hash": _derive_hash(clean, salt)})

    def student_login(self, application_id: object, phone: object) -> dict[str, Any]:
        phone_key = _phone_key(phone)
        try: student_id = str(uuid.UUID(str(application_id)))
        except (ValueError, AttributeError): raise PortalAuthenticationError from None
        if not phone_key: raise PortalAuthenticationError
        for student in _read_list(self.students_path):
            if student.get("id") != student_id or student.get("active") is not True: continue
            try: matches = hmac.compare_digest(student["phone_hash"], _derive_hash(phone_key, _unb64(student["phone_salt"])))
            except (KeyError, ValueError): matches = False
            if matches:
                return {"token": self._issue_token(student_id, "student", 12 * 3600), "student": {"id": student_id, "display_name": student["display_name"], "cohort": student["cohort"]}, "expires_in": 12 * 3600}
        raise PortalAuthenticationError

    def admin_login(self, key: object) -> dict[str, Any]:
        if not isinstance(key, str): raise PortalAuthenticationError
        configured = _read_object(self.admin_key_path)
        if not configured: raise RuntimeError("admin_not_configured")
        try: matches = hmac.compare_digest(configured["hash"], _derive_hash(key, _unb64(configured["salt"])))
        except (KeyError, ValueError): matches = False
        if not matches: raise PortalAuthenticationError
        return {"token": self._issue_token("owner", "admin", 4 * 3600), "expires_in": 4 * 3600}

    def student_profile(self, student_id: str) -> dict[str, Any]:
        student = next((item for item in _read_list(self.students_path) if item.get("id") == student_id and item.get("active") is True), None)
        if not student: raise PortalAuthenticationError
        own = self.list_submissions(student_id)
        latest = {str(item["week"]): item for item in own}
        return {"student": {"id": student_id, "display_name": student["display_name"], "cohort": student["cohort"]}, "progress": {str(week): latest.get(str(week)) for week in range(1, 7)}}

    def _validate_submission(self, payload: object) -> dict[str, Any]:
        allowed = {"week", "artifact_url", "note", "self_scores"}
        if not isinstance(payload, dict): raise PortalValidationError(["body"])
        errors = set(payload) - allowed
        week = payload.get("week")
        if not isinstance(week, int) or not 1 <= week <= 6: errors.add("week")
        url = _clean_text(payload.get("artifact_url"), 2000)
        parsed = urlparse(url or "")
        if not url or parsed.scheme != "https" or not parsed.netloc: errors.add("artifact_url")
        note = _clean_text(payload.get("note"), 1000)
        if not note: errors.add("note")
        scores = payload.get("self_scores")
        if not isinstance(scores, dict) or set(scores) != set(RUBRIC_KEYS) or any(type(value) is not int or not 1 <= value <= 4 for value in scores.values()): errors.add("self_scores")
        if errors: raise PortalValidationError(list(errors))
        return {"week": week, "artifact_url": url, "note": note, "self_scores": {key: scores[key] for key in RUBRIC_KEYS}}

    @staticmethod
    def _public_submission(item: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in item.items() if key != "student_id"}

    def submit(self, student_id: str, payload: object) -> dict[str, Any]:
        cleaned = self._validate_submission(payload)
        with self.lock:
            submissions = _read_list(self.submissions_path)
            version = 1 + max((int(item.get("version", 0)) for item in submissions if item.get("student_id") == student_id and item.get("week") == cleaned["week"]), default=0)
            item = {"id": str(uuid.uuid4()), "student_id": student_id, **cleaned, "version": version, "submitted_at": self._now_iso(), "review_status": "SUBMITTED", "instructor_score": None, "instructor_feedback": "", "reviewed_at": None}
            submissions.append(item); _atomic_write(self.submissions_path, submissions)
        return self._public_submission(item)

    def list_submissions(self, student_id: str) -> list[dict[str, Any]]:
        own = [self._public_submission(item) for item in _read_list(self.submissions_path) if item.get("student_id") == student_id]
        return sorted(own, key=lambda item: (item.get("week", 0), item.get("version", 0)), reverse=True)

    def dashboard(self) -> dict[str, Any]:
        students = _read_list(self.students_path); submissions = _read_list(self.submissions_path)
        rows=[]
        for student in students:
            if student.get("active") is not True: continue
            own=[item for item in submissions if item.get("student_id") == student.get("id")]
            latest={}
            for item in own:
                week=str(item.get("week"));
                if week not in latest or item.get("version", 0)>latest[week].get("version", 0): latest[week]=self._public_submission(item)
            rows.append({"id": student["id"], "display_name": student["display_name"], "cohort": student["cohort"], "progress": latest})
        return {"summary": {"students": len(rows), "submitted": sum(1 for item in submissions if item.get("review_status") == "SUBMITTED"), "needs_revision": sum(1 for item in submissions if item.get("review_status") == "NEEDS_REVISION"), "passed": sum(1 for item in submissions if item.get("review_status") == "PASSED")}, "students": rows}

    def review(self, submission_id: str, payload: object) -> dict[str, Any]:
        allowed={"review_status","instructor_score","instructor_feedback"}
        if not isinstance(payload,dict): raise PortalValidationError(["body"])
        errors=set(payload)-allowed; status=payload.get("review_status"); score=payload.get("instructor_score"); feedback=_clean_text(payload.get("instructor_feedback"),2000)
        if status not in REVIEW_STATUSES: errors.add("review_status")
        if type(score) is not int or not 0 <= score <= 100: errors.add("instructor_score")
        if not feedback: errors.add("instructor_feedback")
        if errors: raise PortalValidationError(list(errors))
        with self.lock:
            submissions=_read_list(self.submissions_path); found=None
            for item in submissions:
                if item.get("id")==submission_id:
                    item.update({"review_status":status,"instructor_score":score,"instructor_feedback":feedback,"reviewed_at":self._now_iso()}); found=item; break
            if found is None: raise KeyError(submission_id)
            _atomic_write(self.submissions_path,submissions)
        return self._public_submission(found)
