import http.client
import json
import subprocess
import tempfile
import threading
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from backend.slide_admin import hash_password
from backend.slide_admin_server import SlideAdminService, SlideAdminHandler
from backend.slide_publisher import SlidePublisher


ORIGIN = "https://khanh.design"


class SlideAdminApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.published = root / "repo" / "100" / "slide-config.json"
        self.published.parent.mkdir(parents=True)
        self.config = {
            "schema_version": 1,
            "revision": "published-1",
            "order": ["base-one"],
            "hidden": [],
            "overrides": {},
            "custom_slides": [],
        }
        self.published.write_text(json.dumps(self.config), encoding="utf-8")
        subprocess.run(["git", "init", "-b", "main", str(root / "repo")], check=True, capture_output=True)
        subprocess.run(["git", "init", "--bare", str(root / "remote.git")], check=True, capture_output=True)
        for args in (
            ("config", "user.name", "Test"), ("config", "user.email", "test@example.com"),
            ("remote", "add", "origin", str(root / "remote.git")),
            ("add", "100/slide-config.json"), ("commit", "-m", "initial"),
            ("push", "-u", "origin", "main"),
        ):
            subprocess.run(["git", *args], cwd=root / "repo", check=True, capture_output=True)
        self.publisher = SlidePublisher(root / "repo", root / "state/ledger.json")
        self.service = SlideAdminService(
            password_hash=hash_password("correct horse"),
            published_path=self.published,
            draft_path=root / "state" / "draft.json",
            base_ids=["base-one"],
            login_limit=2,
            login_window_seconds=60,
            max_json_bytes=1024,
            image_dir=root / "repo" / "100/assets/admin",
            publisher=self.publisher,
        )
        self.server = self.service.make_server(("127.0.0.1", 0), SlideAdminHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, method, path, payload=None, headers=None, raw=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        request_headers = {"Origin": ORIGIN}
        request_headers.update(headers or {})
        body = raw
        if payload is not None:
            body = json.dumps(payload).encode()
            request_headers.setdefault("Content-Type", "application/json")
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        data = response.read()
        result = json.loads(data) if data else None
        response_headers = dict(response.getheaders())
        connection.close()
        return response.status, result, response_headers

    def login(self):
        status, body, headers = self.request("POST", "/login", {"password": "correct horse"})
        self.assertEqual(200, status)
        return headers["Set-Cookie"].split(";", 1)[0], body["csrf_token"]

    def test_health_is_public_and_contains_no_sensitive_configuration(self):
        status, body, headers = self.request("GET", "/health")
        self.assertEqual((200, {"status": "ok"}), (status, body))
        self.assertNotIn("password", json.dumps(body).lower())
        self.assertEqual(ORIGIN, headers["Access-Control-Allow-Origin"])
        self.assertEqual("true", headers["Access-Control-Allow-Credentials"])

    def test_origin_is_exact_and_preflight_allows_credentials(self):
        status, _, headers = self.request("OPTIONS", "/draft", headers={"Origin": "https://evil.example"})
        self.assertEqual(403, status)
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        status, _, headers = self.request("OPTIONS", "/draft")
        self.assertEqual(204, status)
        self.assertEqual("Content-Type, X-CSRF-Token", headers["Access-Control-Allow-Headers"])

    def test_bad_login_is_rate_limited_but_good_login_returns_secure_cookie(self):
        for expected in (401, 401, 429):
            status, _, _ = self.request("POST", "/login", {"password": "wrong"})
            self.assertEqual(expected, status)
        self.service.clear_login_attempts("127.0.0.1")
        status, body, headers = self.request("POST", "/login", {"password": "correct horse"})
        self.assertEqual(200, status)
        self.assertTrue(body["csrf_token"])
        cookie = headers["Set-Cookie"]
        for flag in ("HttpOnly", "Secure", "SameSite=Strict", "Path=/"):
            self.assertIn(flag, cookie)

    def test_slides_require_login_and_return_published_plus_draft(self):
        self.assertEqual(401, self.request("GET", "/slides")[0])
        cookie, _ = self.login()
        status, body, _ = self.request("GET", "/slides", headers={"Cookie": cookie})
        self.assertEqual(200, status)
        self.assertEqual(self.config, body["published"])
        self.assertIsNone(body["draft"])

    def test_put_draft_requires_session_and_matching_csrf(self):
        self.assertEqual(401, self.request("PUT", "/draft", self.config)[0])
        cookie, csrf = self.login()
        self.assertEqual(403, self.request("PUT", "/draft", self.config, {"Cookie": cookie})[0])
        draft = dict(self.config, revision="draft-2")
        status, body, _ = self.request(
            "PUT", "/draft", draft,
            {"Cookie": cookie, "X-CSRF-Token": csrf},
        )
        self.assertEqual((200, "draft-2"), (status, body["draft"]["revision"]))
        self.assertEqual(draft, json.loads(self.service.draft_path.read_text(encoding="utf-8")))

    def test_logout_revokes_session(self):
        cookie, csrf = self.login()
        status, _, headers = self.request(
            "POST", "/logout", {}, {"Cookie": cookie, "X-CSRF-Token": csrf}
        )
        self.assertEqual(204, status)
        self.assertIn("Max-Age=0", headers["Set-Cookie"])
        self.assertEqual(401, self.request("GET", "/slides", headers={"Cookie": cookie})[0])

    def test_rejects_invalid_json_content_type_and_oversized_body(self):
        self.assertEqual(415, self.request("POST", "/login", raw=b"{}", headers={"Content-Type": "text/plain"})[0])
        self.assertEqual(400, self.request("POST", "/login", raw=b"{", headers={"Content-Type": "application/json"})[0])
        oversized = b"x" * (self.service.max_json_bytes + 1)
        self.assertEqual(413, self.request("POST", "/login", raw=oversized, headers={"Content-Type": "application/json"})[0])

    def test_image_upload_requires_auth_csrf_and_real_supported_image(self):
        source = BytesIO()
        Image.new("RGB", (40, 20), "red").save(source, "PNG")
        data = source.getvalue()
        self.assertEqual(401, self.request("POST", "/images", raw=data, headers={"Content-Type": "image/png"})[0])
        cookie, csrf = self.login()
        status, body, _ = self.request(
            "POST", "/images", raw=data,
            headers={"Content-Type": "image/png", "Cookie": cookie, "X-CSRF-Token": csrf},
        )
        self.assertEqual(201, status)
        self.assertRegex(body["path"], r"^assets/admin/[0-9a-f-]{36}\.webp$")
        self.assertTrue((self.service.image_dir.parent.parent / body["path"]).exists())
        self.assertEqual(400, self.request(
            "POST", "/images", raw=b"fake",
            headers={"Content-Type": "image/png", "Cookie": cookie, "X-CSRF-Token": csrf},
        )[0])

    def test_publish_rollback_and_deployment_endpoints(self):
        cookie, csrf = self.login()
        draft = dict(self.config, revision="published-2", hidden=["base-one"])
        auth = {"Cookie": cookie, "X-CSRF-Token": csrf}
        self.assertEqual(200, self.request("PUT", "/draft", draft, auth)[0])
        status, deployment, _ = self.request("POST", "/publish", {}, auth)
        self.assertEqual((202, "queued"), (status, deployment["state"]))
        status, fetched, _ = self.request(
            "GET", f"/deployment/{deployment['id']}", headers={"Cookie": cookie}
        )
        self.assertEqual((200, deployment["id"]), (status, fetched["id"]))
        status, rolled_back, _ = self.request("POST", "/rollback", {}, auth)
        self.assertEqual((202, "queued"), (status, rolled_back["state"]))
        restored = json.loads(self.published.read_text(encoding="utf-8"))
        self.assertEqual("published-1", restored["revision"])


if __name__ == "__main__":
    unittest.main()
