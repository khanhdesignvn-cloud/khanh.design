import http.client
import json
import tempfile
import threading
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.course_application_server import CourseApplicationHandler, CourseApplicationService
from backend.course_learning_portal import CourseLearningPortal, RUBRIC_KEYS, WEEKS

ORIGIN = "https://khanh.design"


class RunningPortalServer:
    def __init__(self, folder: Path):
        self.portal = CourseLearningPortal(
            students_path=folder / "students.json",
            submissions_path=folder / "submissions.json",
            token_secret_path=folder / "token-secret",
            admin_key_path=folder / "admin-key.json",
            clock=lambda: 1_800_000_000,
        )
        self.portal.configure_admin("admin-test-key")
        self.portal.activate_student(
            application_id="11111111-1111-4111-8111-111111111111",
            display_name="Nguyễn Văn An",
            phone="0912 345 678",
            cohort="2026-09",
        )
        self.portal.activate_student(
            application_id="22222222-2222-4222-8222-222222222222",
            display_name="Trần Thị Bình",
            phone="0988 111 222",
            cohort="2026-09",
        )
        self.service = CourseApplicationService(folder / "applications.json", rate_limit=100, portal=self.portal)
        self.server = self.service.make_server(("127.0.0.1", 0), CourseApplicationHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)

    def request(self, method, path, *, payload=None, token=None, origin=ORIGIN):
        headers = {"Origin": origin}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse(); raw = response.read(); response_headers = dict(response.getheaders()); connection.close()
        return response.status, response_headers, json.loads(raw) if raw else None

    def student_login(self, application_id, phone):
        status, _, body = self.request("POST", "/course/portal/login", payload={"application_id": application_id, "phone": phone})
        assert status == 200, body
        return body["token"]

    def admin_login(self):
        status, _, body = self.request("POST", "/course/admin/login", payload={"key": "admin-test-key"})
        assert status == 200, body
        return body["token"]


class LearningPortalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.folder = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def valid_submission(week=1):
        return {
            "week": week,
            "artifact_url": "https://docs.google.com/document/d/example",
            "note": "Bản đã ẩn danh dữ liệu khách hàng.",
            "self_scores": {key: 3 for key in RUBRIC_KEYS},
        }

    def test_public_week_contract_contains_six_integrated_artifacts(self):
        self.assertEqual([item["week"] for item in WEEKS], [1, 2, 3, 4, 5, 6])
        for item in WEEKS:
            self.assertTrue(item["title"])
            self.assertTrue(item["artifact"])
            self.assertEqual(set(item["rubric"]), set(RUBRIC_KEYS))

    def test_student_login_requires_active_exact_application_and_phone(self):
        with RunningPortalServer(self.folder) as api:
            ok, _, response = api.request("POST", "/course/portal/login", payload={"application_id": "11111111-1111-4111-8111-111111111111", "phone": "0912345678"})
            bad_phone, _, bad_response = api.request("POST", "/course/portal/login", payload={"application_id": "11111111-1111-4111-8111-111111111111", "phone": "0900000000"})
            unknown, _, _ = api.request("POST", "/course/portal/login", payload={"application_id": "33333333-3333-4333-8333-333333333333", "phone": "0912345678"})
        self.assertEqual(ok, 200); self.assertEqual(set(response), {"token", "student", "expires_in"})
        self.assertEqual(response["student"]["display_name"], "Nguyễn Văn An")
        self.assertNotIn("phone", response["student"])
        self.assertEqual(bad_phone, 401); self.assertEqual(bad_response, {"error": "invalid_credentials"})
        self.assertEqual(unknown, 401)

    def test_submission_versions_increment_and_other_student_is_isolated(self):
        with RunningPortalServer(self.folder) as api:
            token_a = api.student_login("11111111-1111-4111-8111-111111111111", "0912345678")
            token_b = api.student_login("22222222-2222-4222-8222-222222222222", "0988111222")
            first, _, one = api.request("POST", "/course/portal/submissions", payload=self.valid_submission(), token=token_a)
            second, _, two = api.request("POST", "/course/portal/submissions", payload=self.valid_submission(), token=token_a)
            status_b, _, submissions_b = api.request("GET", "/course/portal/submissions", token=token_b)
            status_a, _, submissions_a = api.request("GET", "/course/portal/submissions", token=token_a)
        self.assertEqual((first, second), (201, 201)); self.assertEqual((one["version"], two["version"]), (1, 2))
        self.assertEqual(status_b, 200); self.assertEqual(submissions_b["submissions"], [])
        self.assertEqual(status_a, 200); self.assertEqual(len(submissions_a["submissions"]), 2)
        self.assertNotIn("student_id", json.dumps(submissions_a))

    def test_submission_validation_rejects_unsafe_url_bad_week_unknown_keys_and_scores(self):
        cases = [
            {**self.valid_submission(), "week": 7},
            {**self.valid_submission(), "artifact_url": "javascript:alert(1)"},
            {**self.valid_submission(), "extra": "no"},
            {**self.valid_submission(), "self_scores": {key: 5 for key in RUBRIC_KEYS}},
        ]
        with RunningPortalServer(self.folder) as api:
            token = api.student_login("11111111-1111-4111-8111-111111111111", "0912345678")
            statuses = [api.request("POST", "/course/portal/submissions", payload=payload, token=token)[0] for payload in cases]
        self.assertEqual(statuses, [400, 400, 400, 400])
        self.assertFalse((self.folder / "submissions.json").exists())

    def test_admin_dashboard_and_review_require_admin_role(self):
        with RunningPortalServer(self.folder) as api:
            student = api.student_login("11111111-1111-4111-8111-111111111111", "0912345678")
            _, _, created = api.request("POST", "/course/portal/submissions", payload=self.valid_submission(), token=student)
            forbidden, _, _ = api.request("GET", "/course/admin/dashboard", token=student)
            admin = api.admin_login()
            dashboard_status, _, dashboard = api.request("GET", "/course/admin/dashboard", token=admin)
            review_status, _, reviewed = api.request("PATCH", f"/course/admin/submissions/{created['id']}", payload={"review_status": "PASSED", "instructor_score": 88, "instructor_feedback": "Đạt, có thể dùng tuần sau."}, token=admin)
            _, _, own = api.request("GET", "/course/portal/submissions", token=student)
        self.assertEqual(forbidden, 403); self.assertEqual(dashboard_status, 200)
        self.assertEqual(dashboard["summary"]["submitted"], 1); self.assertEqual(len(dashboard["students"]), 2)
        self.assertEqual(review_status, 200); self.assertEqual(reviewed["review_status"], "PASSED")
        self.assertEqual(own["submissions"][0]["instructor_score"], 88)

    def test_options_and_auth_failures_do_not_leak_or_write(self):
        with RunningPortalServer(self.folder) as api:
            status, headers, _ = api.request("OPTIONS", "/course/portal/submissions")
            me_status, me_headers, _ = api.request("OPTIONS", "/course/portal/me")
            dashboard_status, dashboard_headers, _ = api.request("OPTIONS", "/course/admin/dashboard")
            unauthorized, _, body = api.request("GET", "/course/portal/submissions")
            bad_origin, bad_headers, _ = api.request("OPTIONS", "/course/portal/submissions", origin="https://evil.test")
        self.assertEqual(status, 204); self.assertIn("Authorization", headers["Access-Control-Allow-Headers"])
        self.assertEqual(me_status, 204); self.assertIn("Authorization", me_headers["Access-Control-Allow-Headers"]); self.assertIn("GET", me_headers["Access-Control-Allow-Methods"])
        self.assertEqual(dashboard_status, 204); self.assertIn("Authorization", dashboard_headers["Access-Control-Allow-Headers"]); self.assertIn("GET", dashboard_headers["Access-Control-Allow-Methods"])
        self.assertEqual(unauthorized, 401); self.assertEqual(body, {"error": "authentication_required"})
        self.assertEqual(bad_origin, 403); self.assertNotIn("Access-Control-Allow-Origin", bad_headers)
        self.assertFalse((self.folder / "submissions.json").exists())


if __name__ == "__main__":
    unittest.main()
