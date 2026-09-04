import http.client
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import backend.course_application_server as server_module
from backend.course_application_server import CourseApplicationHandler, CourseApplicationService


ALLOWED_ORIGIN = "https://khanhdesignvn-cloud.github.io"


class RunningServer:
    def __init__(self, store_path, **service_options):
        service_options.setdefault("rate_limit", 100)
        self.service = CourseApplicationService(store_path=store_path, **service_options)
        self.server = self.service.make_server(("127.0.0.1", 0), CourseApplicationHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, *, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        payload = response.read()
        result = response.status, dict(response.getheaders()), payload
        connection.close()
        return result


class CourseApplicationApiTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store_path = Path(self.tempdir.name) / "applications.json"

    def tearDown(self):
        self.tempdir.cleanup()

    def valid_payload(self, **overrides):
        payload = {
            "full_name": "Nguyễn Văn An",
            "phone": "+84 912 345 678",
            "industry": "Bán lẻ / Thương mại",
            "expectation": "Chuẩn hóa phản hồi khách hàng",
            "data_consent": True,
            "website": "",
        }
        payload.update(overrides)
        return payload

    def post(self, api, payload, **headers):
        request_headers = {
            "Origin": ALLOWED_ORIGIN,
            "Content-Type": "application/json",
        }
        request_headers.update(headers)
        return api.request(
            "POST",
            "/course/apply",
            body=json.dumps(payload).encode("utf-8"),
            headers=request_headers,
        )

    def test_health_returns_non_sensitive_status(self):
        with RunningServer(self.store_path) as api:
            status, headers, body = api.request("GET", "/health")

        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_options_allows_only_exact_configured_origin(self):
        with RunningServer(self.store_path) as api:
            allowed_status, allowed_headers, _ = api.request(
                "OPTIONS",
                "/course/apply",
                headers={
                    "Origin": ALLOWED_ORIGIN,
                    "Access-Control-Request-Method": "POST",
                },
            )
            denied_status, denied_headers, denied_body = api.request(
                "OPTIONS",
                "/course/apply",
                headers={
                    "Origin": f"{ALLOWED_ORIGIN}.evil.test",
                    "Access-Control-Request-Method": "POST",
                },
            )

        self.assertEqual(allowed_status, 204)
        self.assertEqual(allowed_headers["Access-Control-Allow-Origin"], ALLOWED_ORIGIN)
        self.assertEqual(allowed_headers["Access-Control-Allow-Methods"], "POST, OPTIONS")
        self.assertEqual(allowed_headers["Access-Control-Allow-Headers"], "Content-Type")
        self.assertEqual(allowed_headers["Vary"], "Origin")
        self.assertEqual(denied_status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", denied_headers)
        self.assertEqual(json.loads(denied_body), {"error": "origin_not_allowed"})

    def test_valid_application_is_created_without_echoing_pii(self):
        with RunningServer(self.store_path) as api:
            status, headers, body = self.post(api, self.valid_payload())

        response = json.loads(body)
        self.assertEqual(status, 201)
        self.assertEqual(headers["Access-Control-Allow-Origin"], ALLOWED_ORIGIN)
        self.assertEqual(set(response), {"id", "status"})
        self.assertEqual(response["status"], "received")
        self.assertNotIn("912 345 678", body.decode("utf-8"))

        stored = json.loads(self.store_path.read_text(encoding="utf-8"))
        self.assertEqual(len(stored), 1)
        self.assertEqual(
            set(stored[0]),
            {
                "id",
                "submitted_at",
                "review_status",
                "full_name",
                "phone",
                "industry",
                "expectation",
                "data_consent",
            },
        )
        self.assertEqual(stored[0]["review_status"], "NEW")

    def test_invalid_fields_and_unknown_keys_return_safe_400_errors(self):
        invalid_cases = {
            "missing_name": ({key: value for key, value in self.valid_payload().items() if key != "full_name"}, "full_name"),
            "bad_phone": (self.valid_payload(phone="call-me"), "phone"),
            "bad_industry": (self.valid_payload(industry="Không có trong danh sách"), "industry"),
            "string_consent": (self.valid_payload(data_consent="true"), "data_consent"),
            "too_long": (self.valid_payload(expectation="x" * 2001), "expectation"),
            "unknown_key": (self.valid_payload(secret="do not accept"), "secret"),
        }
        with RunningServer(self.store_path) as api:
            for label, (payload, expected_field) in invalid_cases.items():
                with self.subTest(label=label):
                    status, _, body = self.post(api, payload)
                    response = json.loads(body)
                    self.assertEqual(status, 400)
                    self.assertEqual(response["error"], "invalid_fields")
                    self.assertIn(expected_field, response["fields"])
                    self.assertNotIn("912 345 678", body.decode("utf-8"))

        self.assertFalse(self.store_path.exists())

    def test_text_is_nfc_normalized_markup_stripped_and_whitespace_collapsed(self):
        payload = self.valid_payload(
            full_name="  A\u0301n   <b>User</b>\n",
            industry="  Dịch   vụ  ",
            expectation="<script>alert(1)</script>   Cần\n hỗ trợ",
        )
        with RunningServer(self.store_path) as api:
            status, _, _ = self.post(api, payload)

        self.assertEqual(status, 201)
        stored = json.loads(self.store_path.read_text(encoding="utf-8"))[0]
        self.assertEqual(stored["full_name"], "Án User")
        self.assertEqual(stored["industry"], "Dịch vụ")
        self.assertEqual(stored["expectation"], "alert(1) Cần hỗ trợ")
        self.assertNotIn("<", json.dumps(stored, ensure_ascii=False))

    def test_honeypot_submission_gets_no_content_and_is_not_written(self):
        with RunningServer(self.store_path) as api:
            status, _, body = self.post(api, self.valid_payload(website="https://bot.test"))

        self.assertEqual(status, 204)
        self.assertEqual(body, b"")
        self.assertFalse(self.store_path.exists())

    def test_request_body_over_16kb_is_rejected_before_json_processing(self):
        oversized = b"{" + (b"x" * (16 * 1024)) + b"}"
        with RunningServer(self.store_path) as api:
            status, _, body = api.request(
                "POST",
                "/course/apply",
                body=oversized,
                headers={"Origin": ALLOWED_ORIGIN, "Content-Type": "application/json"},
            )

        self.assertEqual(status, 413)
        self.assertEqual(json.loads(body), {"error": "payload_too_large"})
        self.assertFalse(self.store_path.exists())

    def test_post_requires_json_content_type(self):
        with RunningServer(self.store_path) as api:
            status, _, body = api.request(
                "POST",
                "/course/apply",
                body=b"full_name=somebody",
                headers={"Origin": ALLOWED_ORIGIN, "Content-Type": "text/plain"},
            )

        self.assertEqual(status, 415)
        self.assertEqual(json.loads(body), {"error": "json_required"})

    def test_rate_limit_is_per_valid_forwarded_ip(self):
        with RunningServer(self.store_path, rate_limit=1, rate_window_seconds=60) as api:
            first_status, _, _ = self.post(
                api,
                self.valid_payload(),
                **{"CF-Connecting-IP": "203.0.113.10"},
            )
            blocked_status, _, blocked_body = self.post(
                api,
                self.valid_payload(phone="0988 111 222"),
                **{"CF-Connecting-IP": "203.0.113.10"},
            )
            other_status, _, _ = self.post(
                api,
                self.valid_payload(phone="0988 111 333"),
                **{"CF-Connecting-IP": "203.0.113.11"},
            )

        self.assertEqual(first_status, 201)
        self.assertEqual(blocked_status, 429)
        self.assertEqual(json.loads(blocked_body), {"error": "rate_limited"})
        self.assertEqual(other_status, 201)

    def test_malformed_forwarded_ip_cannot_rotate_rate_limit_identity(self):
        with RunningServer(self.store_path, rate_limit=1, rate_window_seconds=60) as api:
            first_status, _, _ = self.post(
                api,
                self.valid_payload(),
                **{"CF-Connecting-IP": "not-an-ip-1"},
            )
            blocked_status, _, blocked_body = self.post(
                api,
                self.valid_payload(phone="0988 111 222"),
                **{"CF-Connecting-IP": "not-an-ip-2"},
            )

        self.assertEqual(first_status, 201)
        self.assertEqual(blocked_status, 429)
        self.assertEqual(json.loads(blocked_body), {"error": "rate_limited"})

    def test_duplicate_normalized_phone_returns_409_without_pii(self):
        with RunningServer(self.store_path) as api:
            first_status, _, _ = self.post(api, self.valid_payload())
            phone_status, _, phone_body = self.post(
                api,
                self.valid_payload(phone="+84 (912) 345-678"),
            )

        self.assertEqual(first_status, 201)
        self.assertEqual(phone_status, 409)
        self.assertEqual(json.loads(phone_body), {"error": "duplicate_application"})
        self.assertNotIn("912", phone_body.decode("utf-8"))
        self.assertEqual(len(json.loads(self.store_path.read_text(encoding="utf-8"))), 1)
    def test_atomic_replace_failure_preserves_original_store(self):
        original = b'[{"phone":"0900000000"}]'
        self.store_path.write_bytes(original)

        def fail_replace(_source, _destination):
            raise OSError("simulated replacement failure")

        service = CourseApplicationService(
            self.store_path,
            replace_func=fail_replace,
            rate_limit=100,
        )
        with self.assertRaises(OSError):
            service.store({"phone": "0911111111"})

        self.assertEqual(self.store_path.read_bytes(), original)
        self.assertEqual(list(self.store_path.parent.glob(".*.tmp")), [])

    def test_default_storage_and_cli_are_private_loopback_only(self):
        root = Path(__file__).resolve().parents[1]
        default_store = server_module.DEFAULT_STORE_PATH
        self.assertTrue(default_store.is_absolute())
        self.assertNotIn(root, default_store.parents)
        self.assertEqual(server_module.validate_bind_host("127.0.0.1"), "127.0.0.1")
        with self.assertRaises(ValueError):
            server_module.validate_bind_host("0.0.0.0")
        result = subprocess.run(
            [sys.executable, str(root / "backend" / "course_application_server.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--store", result.stdout)
        self.assertIn("--port", result.stdout)


if __name__ == "__main__":
    unittest.main()
