import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from backend.slide_admin import PublishBusy
from backend.slide_publisher import SlidePublisher


class SlidePublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.remote = root / "remote.git"
        self.repo = root / "repo"
        subprocess.run(["git", "init", "--bare", str(self.remote)], check=True, capture_output=True)
        subprocess.run(["git", "init", "-b", "main", str(self.repo)], check=True, capture_output=True)
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        self.git("remote", "add", "origin", str(self.remote))
        (self.repo / "100/assets/admin").mkdir(parents=True)
        self.initial = {
            "schema_version": 1, "revision": "initial", "order": ["base-one"],
            "hidden": [], "overrides": {}, "custom_slides": [],
        }
        (self.repo / "100/slide-config.json").write_text(json.dumps(self.initial), encoding="utf-8")
        (self.repo / "README.md").write_text("initial\n", encoding="utf-8")
        self.git("add", "100/slide-config.json", "README.md")
        self.git("commit", "-m", "initial")
        self.git("push", "-u", "origin", "main")
        self.publisher = SlidePublisher(self.repo, root / "state/ledger.json")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.repo, check=check, capture_output=True, text=True)

    def draft(self, revision="revision-2", image=""):
        custom = []
        order = ["base-one"]
        if image:
            custom = [{
                "id": "custom-one", "eyebrow": "Nhãn", "title": "Tiêu đề",
                "body": ["Nội dung"], "note": "", "image": image,
            }]
            order.append("custom-one")
        return {
            "schema_version": 1, "revision": revision, "order": order,
            "hidden": [], "overrides": {}, "custom_slides": custom,
        }

    def test_publish_commits_config_and_referenced_images_but_not_unrelated_files(self):
        image = self.repo / "100/assets/admin/11111111-1111-1111-1111-111111111111.webp"
        image.write_bytes(b"published image")
        (self.repo / "100/qa-output.txt").write_text("never stage", encoding="utf-8")
        (self.repo / "notes.txt").write_text("never stage", encoding="utf-8")
        result = self.publisher.publish(self.draft(image="assets/admin/11111111-1111-1111-1111-111111111111.webp"))
        self.assertEqual("queued", result["state"])
        changed = self.git("show", "--name-only", "--format=", "HEAD").stdout.splitlines()
        self.assertEqual([
            "100/assets/admin/11111111-1111-1111-1111-111111111111.webp",
            "100/slide-config.json",
        ], sorted(changed))
        self.assertIn("?? 100/qa-output.txt", self.git("status", "--short").stdout)
        self.assertIn("?? notes.txt", self.git("status", "--short").stdout)

    def test_publish_without_changes_creates_no_duplicate_commit(self):
        before = self.git("rev-parse", "HEAD").stdout.strip()
        result = self.publisher.publish(self.initial)
        self.assertEqual("unchanged", result["state"])
        self.assertEqual(before, self.git("rev-parse", "HEAD").stdout.strip())

    def test_push_failure_is_recorded_as_failure(self):
        self.git("remote", "set-url", "origin", str(self.repo.parent / "missing.git"))
        result = self.publisher.publish(self.draft())
        self.assertEqual("failure", result["state"])
        self.assertEqual("push_failed", result["error"])
        self.assertEqual("failure", self.publisher.deployment(result["id"])["state"])

    def test_publish_lock_returns_conflict(self):
        with self.publisher.lock.acquire():
            with self.assertRaises(PublishBusy):
                self.publisher.publish(self.draft())

    def test_rollback_creates_new_commit_restoring_previous_config(self):
        published = self.publisher.publish(self.draft())
        self.assertEqual("queued", published["state"])
        changed_sha = self.git("rev-parse", "HEAD").stdout.strip()
        rolled_back = self.publisher.rollback()
        self.assertEqual("queued", rolled_back["state"])
        rollback_sha = self.git("rev-parse", "HEAD").stdout.strip()
        self.assertNotEqual(changed_sha, rollback_sha)
        self.assertEqual(self.initial, json.loads((self.repo / "100/slide-config.json").read_text(encoding="utf-8")))
        self.assertIn("Hoàn tác", self.git("log", "-1", "--pretty=%s").stdout)

    def test_deployment_states_are_explicit(self):
        entry = self.publisher.create_deployment("rev")
        self.assertEqual("queued", entry["state"])
        for state in ("building", "success", "failure"):
            updated = self.publisher.set_deployment_state(entry["id"], state)
            self.assertEqual(state, updated["state"])
        with self.assertRaises(ValueError):
            self.publisher.set_deployment_state(entry["id"], "mystery")


if __name__ == "__main__":
    unittest.main()
