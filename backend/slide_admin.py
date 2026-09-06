"""Security-sensitive domain logic for slide administration."""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import tempfile
import threading
import time
import unicodedata
import uuid
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps, UnidentifiedImageError


_SCRYPT_N = 1 << 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LENGTH = 32


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("password must not be empty")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R,
        p=_SCRYPT_P, dklen=_SCRYPT_LENGTH,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded_hash.split("$")
        if algorithm != "scrypt":
            return False
        digest = hashlib.scrypt(
            password.encode("utf-8"), salt=_decode(salt), n=int(n), r=int(r),
            p=int(p), dklen=len(_decode(expected)),
        )
        return hmac.compare_digest(digest, _decode(expected))
    except (AttributeError, TypeError, ValueError):
        return False


class SessionStore:
    def __init__(self, *, ttl_seconds: float = 3600, clock=time.monotonic):
        if ttl_seconds <= 0:
            raise ValueError("session TTL must be positive")
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._sessions: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def create(self) -> tuple[str, str]:
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[token] = (csrf, self.clock() + self.ttl_seconds)
        return token, csrf

    def get_csrf(self, token: str | None) -> str | None:
        if not token:
            return None
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return None
            csrf, expires_at = session
            if self.clock() >= expires_at:
                self._sessions.pop(token, None)
                return None
            return csrf

    def validate(self, token: str | None, csrf: str | None) -> bool:
        expected = self.get_csrf(token)
        return bool(expected and csrf and hmac.compare_digest(expected, csrf))

    def revoke(self, token: str | None) -> None:
        if token:
            with self._lock:
                self._sessions.pop(token, None)


class SlideValidationError(ValueError):
    """Raised when draft data cannot be safely represented."""


_TAG_PATTERN = re.compile(r"<[^>]*>")
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,79}$")
_IMAGE_PATTERN = re.compile(r"^assets/admin/[a-f0-9-]+\.(?:jpe?g|png|webp)$", re.I)


def sanitize_text(value: object, maximum: int, *, required: bool = True) -> str:
    if not isinstance(value, str):
        raise SlideValidationError("invalid text")
    normalized = unicodedata.normalize("NFC", value)
    cleaned = " ".join(_TAG_PATTERN.sub(" ", normalized).split())
    if (required and not cleaned) or len(cleaned) > maximum:
        raise SlideValidationError("invalid text length")
    return cleaned


def validate_slide_config(config: object, base_ids: list[str]) -> dict:
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise SlideValidationError("invalid schema")
    required_keys = {"schema_version", "revision", "order", "hidden", "overrides", "custom_slides"}
    if set(config) != required_keys:
        raise SlideValidationError("invalid fields")
    revision = sanitize_text(config.get("revision"), 120)
    if len(base_ids) != len(set(base_ids)) or not all(_ID_PATTERN.fullmatch(item) for item in base_ids):
        raise SlideValidationError("invalid base ids")
    custom_input = config.get("custom_slides")
    if not isinstance(custom_input, list) or len(custom_input) > 100:
        raise SlideValidationError("invalid custom slides")
    custom = []
    custom_ids = []
    allowed_custom = {"id", "eyebrow", "title", "body", "note", "image"}
    for slide in custom_input:
        if not isinstance(slide, dict) or set(slide) != allowed_custom:
            raise SlideValidationError("invalid custom slide")
        slide_id = slide.get("id")
        if not isinstance(slide_id, str) or not _ID_PATTERN.fullmatch(slide_id):
            raise SlideValidationError("invalid custom id")
        body = slide.get("body")
        if not isinstance(body, list) or not 1 <= len(body) <= 12:
            raise SlideValidationError("invalid body")
        cleaned_body = [sanitize_text(item, 2000) for item in body]
        if sum(map(len, cleaned_body)) > 2000:
            raise SlideValidationError("body too long")
        image = slide.get("image")
        if image and (not isinstance(image, str) or not _IMAGE_PATTERN.fullmatch(image)):
            raise SlideValidationError("invalid image")
        custom_ids.append(slide_id)
        custom.append({
            "id": slide_id,
            "eyebrow": sanitize_text(slide.get("eyebrow"), 120, required=False),
            "title": sanitize_text(slide.get("title"), 240),
            "body": cleaned_body,
            "note": sanitize_text(slide.get("note"), 300, required=False),
            "image": image or "",
        })
    all_ids = base_ids + custom_ids
    if len(all_ids) != len(set(all_ids)):
        raise SlideValidationError("duplicate id")
    order = config.get("order")
    if not isinstance(order, list) or len(order) != len(all_ids) or len(set(order)) != len(order) or set(order) != set(all_ids):
        raise SlideValidationError("invalid order")
    hidden = config.get("hidden")
    if not isinstance(hidden, list) or len(hidden) != len(set(hidden)) or not set(hidden) <= set(all_ids):
        raise SlideValidationError("invalid hidden")
    override_input = config.get("overrides")
    if not isinstance(override_input, dict) or not set(override_input) <= set(base_ids):
        raise SlideValidationError("invalid overrides")
    overrides = {}
    for slide_id, override in override_input.items():
        if not isinstance(override, dict) or set(override) != {"title"}:
            raise SlideValidationError("invalid override")
        overrides[slide_id] = {"title": sanitize_text(override.get("title"), 240)}
    return {
        "schema_version": 1, "revision": revision, "order": list(order),
        "hidden": list(hidden), "overrides": overrides, "custom_slides": custom,
    }


def save_draft_atomic(path, payload: dict) -> None:
    target = os.fspath(path)
    parent = os.path.dirname(target)
    os.makedirs(parent, mode=0o700, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{os.path.basename(target)}.", suffix=".tmp", dir=parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(payload, output, ensure_ascii=False, separators=(",", ":"))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


class PublishBusy(RuntimeError):
    """Raised when another publish or rollback operation owns the lock."""


class PublishLock:
    def __init__(self):
        self._lock = threading.Lock()

    @contextmanager
    def acquire(self):
        if not self._lock.acquire(blocking=False):
            raise PublishBusy("publish already in progress")
        try:
            yield
        finally:
            self._lock.release()


def ensure_repo_path(repo_root, relative_path: str) -> Path:
    if not isinstance(relative_path, str):
        raise SlideValidationError("invalid path")
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or not candidate.parts or candidate.parts[0] != "100":
        raise SlideValidationError("path must be below 100")
    if any(part in ("", ".", "..") for part in candidate.parts):
        raise SlideValidationError("invalid path traversal")
    root = Path(repo_root).resolve()
    destination = root.joinpath(*candidate.parts)
    try:
        destination.resolve().relative_to((root / "100").resolve())
    except ValueError as exc:
        raise SlideValidationError("path escapes 100") from exc
    return destination


def process_uploaded_image(
    data: bytes,
    claimed_mime: str,
    target_dir: str | Path,
    *,
    max_bytes: int = 8 * 1024 * 1024,
    max_pixels: int = 40_000_000,
) -> str:
    """Verify and normalize a user image, returning its public relative path."""
    if not isinstance(data, bytes) or not data or len(data) > max_bytes:
        raise SlideValidationError("invalid image size")
    mime_formats = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
    expected_format = mime_formats.get(claimed_mime.lower() if isinstance(claimed_mime, str) else "")
    if expected_format is None:
        raise SlideValidationError("unsupported image type")
    try:
        with Image.open(io.BytesIO(data)) as source:
            source.verify()
        with Image.open(io.BytesIO(data)) as source:
            if source.format != expected_format or source.width * source.height > max_pixels:
                raise SlideValidationError("image content does not match request")
            normalized = ImageOps.exif_transpose(source)
            normalized.thumbnail((1600, 900), Image.Resampling.LANCZOS)
            if normalized.mode not in ("RGB", "RGBA"):
                normalized = normalized.convert("RGBA" if "transparency" in normalized.info else "RGB")
            normalized.load()
    except SlideValidationError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise SlideValidationError("invalid image") from exc

    directory = Path(target_dir)
    directory.mkdir(parents=True, mode=0o700, exist_ok=True)
    name = f"{uuid.uuid4()}.webp"
    destination = directory / name
    descriptor, temporary = tempfile.mkstemp(prefix=".upload-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "wb") as output:
            normalized.save(output, "WEBP", quality=86, method=6)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
        os.chmod(destination, 0o600)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return f"assets/admin/{name}"
