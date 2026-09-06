"""Loopback HTTP API for the slide administration frontend."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import subprocess
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from backend.slide_admin import (
        PublishBusy,
        SessionStore,
        SlideValidationError,
        process_uploaded_image,
        save_draft_atomic,
        validate_slide_config,
        verify_password,
    )
except ModuleNotFoundError:  # Installed modules live side by side.
    from slide_admin import (  # type: ignore[no-redef]
        PublishBusy,
        SessionStore,
        SlideValidationError,
        process_uploaded_image,
        save_draft_atomic,
        validate_slide_config,
        verify_password,
    )

try:
    from backend.slide_publisher import SlidePublisher
except ModuleNotFoundError:
    from slide_publisher import SlidePublisher  # type: ignore[no-redef]


ALLOWED_ORIGINS = frozenset({"https://khanh.design", "https://www.khanh.design"})
DEFAULT_PORT = 8093
DEFAULT_STATE_DIR = Path.home() / ".local/share/khanh-slide-admin"


def resolve_password_hash(cli_value: str, environ: dict[str, str] | os._Environ[str] | None = None) -> str:
    """Resolve the password verifier without requiring it in the process list."""
    environment = os.environ if environ is None else environ
    value = cli_value or environment.get("SLIDE_ADMIN_PASSWORD_HASH", "")
    if not value:
        raise ValueError("password hash is required")
    return value


def validate_bind_host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("server host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("server host must be loopback-only")
    return str(address)


class SlideAdminService:
    def __init__(
        self,
        *,
        password_hash: str,
        published_path: str | Path,
        draft_path: str | Path,
        base_ids: list[str],
        login_limit: int = 5,
        login_window_seconds: float = 60,
        max_json_bytes: int = 512 * 1024,
        image_dir: str | Path | None = None,
        max_upload_bytes: int = 8 * 1024 * 1024,
        publisher: Any | None = None,
        clock=time.monotonic,
    ):
        if not password_hash:
            raise ValueError("password hash is required")
        if login_limit < 1 or login_window_seconds <= 0:
            raise ValueError("invalid login rate limit")
        self.password_hash = password_hash
        self.published_path = Path(published_path)
        self.draft_path = Path(draft_path)
        self.base_ids = list(base_ids)
        self.sessions = SessionStore(clock=clock)
        self.login_limit = login_limit
        self.login_window_seconds = login_window_seconds
        self.max_json_bytes = max_json_bytes
        self.image_dir = Path(image_dir) if image_dir is not None else self.published_path.parent / "assets/admin"
        self.max_upload_bytes = max_upload_bytes
        self.publisher = publisher
        self.clock = clock
        self._login_attempts: dict[str, list[float]] = {}

    def make_server(self, address, handler_class):
        server = ThreadingHTTPServer(address, handler_class)
        server.slide_admin_service = self  # type: ignore[attr-defined]
        return server

    def login_allowed(self, client: str) -> bool:
        now = self.clock()
        active = [stamp for stamp in self._login_attempts.get(client, []) if stamp > now - self.login_window_seconds]
        self._login_attempts[client] = active
        return len(active) < self.login_limit

    def record_failed_login(self, client: str) -> None:
        self._login_attempts.setdefault(client, []).append(self.clock())

    def clear_login_attempts(self, client: str) -> None:
        self._login_attempts.pop(client, None)

    def load_slides(self) -> dict[str, Any]:
        published = json.loads(self.published_path.read_text(encoding="utf-8"))
        draft = json.loads(self.draft_path.read_text(encoding="utf-8")) if self.draft_path.exists() else None
        return {"published": published, "draft": draft}


class SlideAdminHandler(BaseHTTPRequestHandler):
    server_version = "SlideAdminAPI/1"

    @property
    def service(self) -> SlideAdminService:
        return self.server.slide_admin_service  # type: ignore[attr-defined]

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        return origin is None or origin in ALLOWED_ORIGINS

    def _cors(self) -> None:
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: int, *, clear_cookie: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self._cors()
        if clear_cookie:
            self.send_header("Set-Cookie", "slide_admin_session=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict")
        self.end_headers()

    def _read_json(self) -> object:
        if self.headers.get_content_type() != "application/json":
            raise TypeError("json_required")
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            raise ValueError("invalid_request") from None
        if size < 0:
            raise ValueError("invalid_request")
        if size > self.service.max_json_bytes:
            raise OverflowError("payload_too_large")
        try:
            return json.loads(self.rfile.read(size))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("invalid_json") from None

    def _session_token(self) -> str | None:
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
        except Exception:
            return None
        morsel = cookie.get("slide_admin_session")
        return morsel.value if morsel else None

    def _require_session(self, *, csrf: bool = False) -> str | None:
        token = self._session_token()
        expected = self.service.sessions.get_csrf(token)
        if expected is None:
            self._send_json(401, {"error": "authentication_required"})
            return None
        if csrf and not self.service.sessions.validate(token, self.headers.get("X-CSRF-Token")):
            self._send_json(403, {"error": "csrf_invalid"})
            return None
        return token

    def _reject_bad_origin(self) -> bool:
        if self._origin_allowed():
            return False
        self._send_json(403, {"error": "origin_not_allowed"})
        return True

    def do_OPTIONS(self) -> None:
        if self._reject_bad_origin():
            return
        if self.path not in {"/login", "/logout", "/slides", "/draft", "/images", "/publish", "/rollback"}:
            self._send_json(404, {"error": "not_found"})
            return
        self.send_response(204)
        self._cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-CSRF-Token")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        if self._reject_bad_origin():
            return
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path.startswith("/deployment/"):
            if self._require_session() is None:
                return
            if self.service.publisher is None:
                self._send_json(503, {"error": "publisher_unavailable"})
                return
            try:
                deployment_id = self.path.removeprefix("/deployment/")
                self._send_json(200, self.service.publisher.deployment(deployment_id))
            except KeyError:
                self._send_json(404, {"error": "deployment_not_found"})
            return
        if self.path != "/slides":
            self._send_json(404, {"error": "not_found"})
            return
        if self._require_session() is None:
            return
        try:
            self._send_json(200, self.service.load_slides())
        except (OSError, ValueError, json.JSONDecodeError):
            self._send_json(500, {"error": "storage_unavailable"})

    def do_POST(self) -> None:
        if self._reject_bad_origin():
            return
        if self.path == "/login":
            self._login()
            return
        if self.path == "/logout":
            token = self._require_session(csrf=True)
            if token is not None:
                self.service.sessions.revoke(token)
                self._send_empty(204, clear_cookie=True)
            return
        if self.path == "/images":
            self._upload_image()
            return
        if self.path in {"/publish", "/rollback"}:
            self._publication_action()
            return
        self._send_json(404, {"error": "not_found"})

    def _publication_action(self) -> None:
        if self._require_session(csrf=True) is None:
            return
        try:
            payload = self._read_json()
            if payload != {}:
                raise ValueError("invalid request")
            if self.service.publisher is None:
                self._send_json(503, {"error": "publisher_unavailable"})
                return
            if self.path == "/publish":
                if not self.service.draft_path.exists():
                    self._send_json(409, {"error": "draft_required"})
                    return
                config = json.loads(self.service.draft_path.read_text(encoding="utf-8"))
                result = self.service.publisher.publish(config)
            else:
                result = self.service.publisher.rollback()
            status = 202 if result.get("state") in {"queued", "building"} else 200
            if result.get("state") == "failure":
                status = 502
            self._send_json(status, result)
        except TypeError:
            self._send_json(415, {"error": "json_required"})
        except OverflowError:
            self._send_json(413, {"error": "payload_too_large"})
        except PublishBusy:
            self._send_json(409, {"error": "publish_in_progress"})
        except (ValueError, SlideValidationError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid_publication"})
        except (OSError, subprocess.SubprocessError):
            self._send_json(500, {"error": "publisher_unavailable"})

    def _upload_image(self) -> None:
        if self._require_session(csrf=True) is None:
            return
        try:
            size = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._send_json(400, {"error": "invalid_request"})
            return
        if size < 1:
            self._send_json(400, {"error": "invalid_image"})
            return
        if size > self.service.max_upload_bytes:
            self._send_json(413, {"error": "payload_too_large"})
            return
        try:
            path = process_uploaded_image(
                self.rfile.read(size), self.headers.get_content_type(), self.service.image_dir,
                max_bytes=self.service.max_upload_bytes,
            )
            self._send_json(201, {"path": path})
        except SlideValidationError:
            self._send_json(400, {"error": "invalid_image"})
        except OSError:
            self._send_json(500, {"error": "storage_unavailable"})

    def _login(self) -> None:
        client = self.client_address[0]
        if not self.service.login_allowed(client):
            self._send_json(429, {"error": "rate_limited"})
            return
        try:
            payload = self._read_json()
        except TypeError:
            self._send_json(415, {"error": "json_required"})
            return
        except OverflowError:
            self._send_json(413, {"error": "payload_too_large"})
            return
        except ValueError:
            self._send_json(400, {"error": "invalid_json"})
            return
        if not isinstance(payload, dict) or set(payload) != {"password"} or not verify_password(payload.get("password"), self.service.password_hash):
            self.service.record_failed_login(client)
            self._send_json(401, {"error": "invalid_credentials"})
            return
        self.service.clear_login_attempts(client)
        token, csrf = self.service.sessions.create()
        self.send_response(200)
        body = json.dumps({"csrf_token": csrf}, separators=(",", ":")).encode()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", f"slide_admin_session={token}; Path=/; HttpOnly; Secure; SameSite=Strict")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self) -> None:
        if self._reject_bad_origin():
            return
        if self.path != "/draft":
            self._send_json(404, {"error": "not_found"})
            return
        if self._require_session(csrf=True) is None:
            return
        try:
            config = validate_slide_config(self._read_json(), self.service.base_ids)
            save_draft_atomic(self.service.draft_path, config)
            self._send_json(200, {"draft": config})
        except TypeError:
            self._send_json(415, {"error": "json_required"})
        except OverflowError:
            self._send_json(413, {"error": "payload_too_large"})
        except (ValueError, SlideValidationError):
            self._send_json(400, {"error": "invalid_draft"})
        except OSError:
            self._send_json(500, {"error": "storage_unavailable"})

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Loopback slide administration API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--password-hash", default="")
    args = parser.parse_args()
    try:
        password_hash = resolve_password_hash(args.password_hash)
    except ValueError:
        parser.error("--password-hash or SLIDE_ADMIN_PASSWORD_HASH is required")
    published_path = args.repo / "100/slide-config.json"
    published = json.loads(published_path.read_text(encoding="utf-8"))
    base_ids = [item for item in published["order"] if not item.startswith("custom-")]
    service = SlideAdminService(
        password_hash=password_hash,
        published_path=published_path,
        draft_path=args.state_dir / "draft.json",
        base_ids=base_ids,
        publisher=SlidePublisher(args.repo, args.state_dir / "deployments.json"),
    )
    server = service.make_server((validate_bind_host(args.host), args.port), SlideAdminHandler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
