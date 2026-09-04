"""Privacy-first course application HTTP service."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import tempfile
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ALLOWED_ORIGINS = frozenset(
    {
        "https://khanhdesignvn-cloud.github.io",
        "https://khanh.design",
        "https://www.khanh.design",
    }
)
ALLOWED_KEYS = frozenset(
    {
        "full_name",
        "phone",
        "email",
        "industry",
        "role",
        "challenge",
        "commitment",
        "data_consent",
        "website",
    }
)
TEXT_LIMITS = {
    "full_name": 120,
    "phone": 32,
    "email": 254,
    "industry": 120,
    "role": 64,
    "challenge": 2000,
}
ALLOWED_ROLES = frozenset(
    {
        "Chủ doanh nghiệp",
        "Marketing/Nội dung",
        "Marketing / Nội dung",
        "Bán hàng",
        "Chăm sóc khách hàng/Vận hành",
        "Quản lý vận hành",
        "Khác",
    }
)
TAG_PATTERN = re.compile(r"<[^>]*>")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_CHARS_PATTERN = re.compile(r"^\+?[0-9\s().-]+$")
MAX_BODY_BYTES = 16 * 1024
DEFAULT_STORE_PATH = Path.home() / ".local" / "share" / "khanh-design-course" / "applications.json"
DEFAULT_PORT = 8092


def validate_bind_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("server host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("server host must be loopback-only")
    return str(address)


def clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = unicodedata.normalize("NFC", value)
    without_markup = TAG_PATTERN.sub(" ", normalized)
    return " ".join(without_markup.split())


def validate_payload(payload: object) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(payload, dict):
        return {}, ["body"]
    errors = set(payload) - ALLOWED_KEYS
    cleaned: dict[str, Any] = {}
    for field, maximum in TEXT_LIMITS.items():
        value = clean_text(payload.get(field))
        if not value or len(value) > maximum:
            errors.add(field)
        else:
            cleaned[field] = value
    email = cleaned.get("email", "")
    if email and not EMAIL_PATTERN.fullmatch(email):
        errors.add("email")
    phone = cleaned.get("phone", "")
    digits = re.sub(r"\D", "", phone)
    if phone and (not PHONE_CHARS_PATTERN.fullmatch(phone) or not 8 <= len(digits) <= 15):
        errors.add("phone")
    if cleaned.get("role") not in ALLOWED_ROLES:
        errors.add("role")
    for field in ("commitment", "data_consent"):
        if payload.get(field) is not True:
            errors.add(field)
        else:
            cleaned[field] = True
    if errors:
        return {}, sorted(errors)
    cleaned["email"] = cleaned["email"].casefold()
    return cleaned, []


class DuplicateApplication(Exception):
    """Raised without PII when an email or phone is already stored."""


class CourseApplicationService:
    """Configuration and process-local state for the HTTP handler."""

    def __init__(
        self,
        store_path: str | Path,
        *,
        replace_func=os.replace,
        rate_limit: int = 5,
        rate_window_seconds: float = 60,
        clock=time.monotonic,
    ):
        if rate_limit < 1 or rate_window_seconds <= 0:
            raise ValueError("rate limit and window must be positive")
        self.store_path = Path(store_path)
        self.lock = threading.Lock()
        self.replace_func = replace_func
        self.rate_limit = rate_limit
        self.rate_window_seconds = rate_window_seconds
        self.clock = clock
        self.rate_lock = threading.Lock()
        self.rate_events: dict[str, list[float]] = {}

    def make_server(
        self,
        address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
    ) -> ThreadingHTTPServer:
        server = ThreadingHTTPServer(address, handler_class)
        server.course_application_service = self  # type: ignore[attr-defined]
        return server

    def allow_request(self, client_key: str) -> bool:
        now = self.clock()
        cutoff = now - self.rate_window_seconds
        with self.rate_lock:
            active = [stamp for stamp in self.rate_events.get(client_key, []) if stamp > cutoff]
            if len(active) >= self.rate_limit:
                self.rate_events[client_key] = active
                return False
            active.append(now)
            self.rate_events[client_key] = active
            return True

    def store(self, application: dict[str, Any]) -> None:
        """Append an application with one lock and an atomic replacement."""
        with self.lock:
            self.store_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if self.store_path.exists():
                applications = json.loads(self.store_path.read_text(encoding="utf-8"))
            else:
                applications = []
            email_key = application["email"].casefold()
            phone_key = re.sub(r"\D", "", application["phone"])
            if any(
                existing.get("email", "").casefold() == email_key
                or re.sub(r"\D", "", existing.get("phone", "")) == phone_key
                for existing in applications
            ):
                raise DuplicateApplication
            applications.append(application)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.store_path.name}.",
                suffix=".tmp",
                dir=self.store_path.parent,
            )
            try:
                os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
                    json.dump(applications, temporary, ensure_ascii=False, separators=(",", ":"))
                    temporary.flush()
                    os.fsync(temporary.fileno())
                self.replace_func(temporary_name, self.store_path)
            except BaseException:
                try:
                    os.unlink(temporary_name)
                except FileNotFoundError:
                    pass
                raise


class CourseApplicationHandler(BaseHTTPRequestHandler):
    server_version = "CourseApplicationAPI/1"

    @property
    def service(self) -> CourseApplicationService:
        return self.server.course_application_service  # type: ignore[attr-defined]

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def _send_no_content(self) -> None:
        self.send_response(204)
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_OPTIONS(self) -> None:
        if self.path != "/course/apply":
            self._send_json(404, {"error": "not_found"})
            return
        origin = self.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "not_found"})

    def _client_key(self) -> str:
        peer = self.client_address[0]
        try:
            peer_address = ipaddress.ip_address(peer)
        except ValueError:
            return peer
        forwarded = self.headers.get("CF-Connecting-IP", "")
        if peer_address.is_loopback and forwarded:
            try:
                return str(ipaddress.ip_address(forwarded.strip()))
            except ValueError:
                pass
        return str(peer_address)

    def do_POST(self) -> None:
        if self.path != "/course/apply":
            self._send_json(404, {"error": "not_found"})
            return
        if self.headers.get("Origin") not in ALLOWED_ORIGINS:
            self._send_json(403, {"error": "origin_not_allowed"})
            return
        if self.headers.get_content_type() != "application/json":
            self._send_json(415, {"error": "json_required"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(400, {"error": "invalid_request"})
            return
        if content_length < 0:
            self._send_json(400, {"error": "invalid_request"})
            return
        if content_length > MAX_BODY_BYTES:
            self._send_json(413, {"error": "payload_too_large"})
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return

        if isinstance(payload, dict) and payload.get("website"):
            self._send_no_content()
            return
        if not self.service.allow_request(self._client_key()):
            self._send_json(429, {"error": "rate_limited"})
            return
        cleaned, field_errors = validate_payload(payload)
        if field_errors:
            self._send_json(400, {"error": "invalid_fields", "fields": field_errors})
            return
        application_id = str(uuid.uuid4())
        application = {
            "id": application_id,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "review_status": "NEW",
            **cleaned,
        }
        try:
            self.service.store(application)
        except DuplicateApplication:
            self._send_json(409, {"error": "duplicate_application"})
            return
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self._send_json(500, {"error": "storage_unavailable"})
            return
        self._send_json(201, {"id": application_id, "status": "received"})

    def log_message(self, format: str, *args: object) -> None:
        # Avoid logs containing paths or other request-controlled data.
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Private course application API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE_PATH)
    parser.add_argument("--rate-limit", type=int, default=5)
    parser.add_argument("--rate-window", type=float, default=60)
    args = parser.parse_args()
    host = validate_bind_host(args.host)
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    service = CourseApplicationService(
        args.store,
        rate_limit=args.rate_limit,
        rate_window_seconds=args.rate_window,
    )
    server = service.make_server((host, args.port), CourseApplicationHandler)
    print(f"Course application API listening on {host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
