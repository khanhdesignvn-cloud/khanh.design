import http.client
import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from backend.slide_admin import hash_password
from backend.slide_admin_server import SlideAdminHandler, SlideAdminService
from backend.slide_publisher import SlidePublisher


ORIGIN = "https://khanh.design"


class SlideAdminEndToEndTests(unittest.TestCase):
    """Run the complete publication cycle against a disposable local remote."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.remote = self.root / "remote.git"
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "-b", "main", str(self.repo)], check=True, capture_output=True)
        self.git("config", "user.name", "Slide E2E")
        self.git("config", "user.email", "slide-e2e@example.invalid")
        self.git("remote", "add", "origin", str(self.remote))
        (self.repo / "100").mkdir(parents=True)
        self.baseline = {
            "schema_version": 1,
            "revision": "baseline-local",
            "order": ["base-one", "base-two"],
            "hidden": [],
            "overrides": {},
            "custom_slides": [],
        }
        self.config_path = self.repo / "100/slide-config.json"
        self.config_path.write_text(json.dumps(self.baseline), encoding="utf-8")
        self.git("add", "100/slide-config.json")
        self.git("commit", "-m", "baseline")
        self.git("push", "-u", "origin", "main")

        state = self.root / "state"
        self.publisher = SlidePublisher(self.repo, state / "deployments.json")
        self.service = SlideAdminService(
            password_hash=hash_password("local e2e password"),
            published_path=self.config_path,
            draft_path=state / "draft.json",
            base_ids=["base-one", "base-two"],
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

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    def request(self, method, path, payload=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        request_headers = {"Origin": ORIGIN, **(headers or {})}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            request_headers["Content-Type"] = "application/json"
        connection.request(method, path, body=body, headers=request_headers)
        response = connection.getresponse()
        raw = response.read()
        result = json.loads(raw) if raw else None
        response_headers = dict(response.getheaders())
        connection.close()
        return response.status, result, response_headers

    def remote_config(self):
        text = subprocess.run(
            ["git", f"--git-dir={self.remote}", "show", "main:100/slide-config.json"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        return json.loads(text)

    def test_login_draft_publish_confirm_and_rollback_restores_baseline(self):
        status, login, headers = self.request(
            "POST", "/login", {"password": "local e2e password"}
        )
        self.assertEqual(200, status)
        auth = {
            "Cookie": headers["Set-Cookie"].split(";", 1)[0],
            "X-CSRF-Token": login["csrf_token"],
        }

        changed = dict(
            self.baseline,
            revision="local-e2e-published",
            order=["base-two", "base-one"],
        )
        status, saved, _ = self.request("PUT", "/draft", changed, auth)
        self.assertEqual((200, changed), (status, saved["draft"]))
        status, preview_data, _ = self.request("GET", "/slides", headers={"Cookie": auth["Cookie"]})
        self.assertEqual((200, changed), (status, preview_data["draft"]))

        status, published, _ = self.request("POST", "/publish", {}, auth)
        self.assertEqual((202, "queued"), (status, published["state"]))
        self.assertEqual(changed, self.remote_config())
        self.publisher.set_deployment_state(published["id"], "success")
        status, deployment, _ = self.request(
            "GET", f"/deployment/{published['id']}", headers={"Cookie": auth["Cookie"]}
        )
        self.assertEqual((200, "success"), (status, deployment["state"]))

        status, rolled_back, _ = self.request("POST", "/rollback", {}, auth)
        self.assertEqual((202, "queued"), (status, rolled_back["state"]))
        self.assertEqual(self.baseline, self.remote_config())
        self.publisher.set_deployment_state(rolled_back["id"], "success")
        self.assertEqual(self.baseline, json.loads(self.config_path.read_text(encoding="utf-8")))
        self.assertEqual("", self.git("status", "--porcelain"))


if __name__ == "__main__":
    unittest.main()
