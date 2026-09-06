import json
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
ADMIN = ROOT / "100/admin/index.html"


class SlideAdminFrontendTests(unittest.TestCase):
    def test_admin_flow_is_responsive_and_renders_user_text_safely(self):
        published = {
            "schema_version": 1, "revision": "published-1",
            "order": ["base-one", "base-two"], "hidden": [], "overrides": {}, "custom_slides": [],
        }
        requests = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 800})

                def api(route, request):
                    requests.append((request.method, request.url, request.post_data))
                    path = request.url.split("sslip.io", 1)[-1]
                    if path == "/setup-status":
                        route.fulfill(json={"setup_required": False})
                    elif path == "/login":
                        route.fulfill(json={"csrf_token": "csrf-test"})
                    elif path == "/slides":
                        route.fulfill(json={"published": published, "draft": None})
                    elif path == "/draft":
                        route.fulfill(json={"draft": json.loads(request.post_data)})
                    elif path == "/images":
                        route.fulfill(status=201, json={"path": "assets/admin/test.webp"})
                    elif path in ("/publish", "/rollback"):
                        route.fulfill(status=202, json={"id": "deploy-1", "state": "queued"})
                    else:
                        route.fulfill(status=404, json={"error": "not_found"})

                page.route("https://slide-admin.103-142-26-14.sslip.io/**", api)
                page.goto(ADMIN.as_uri(), wait_until="load")
                self.assertTrue(page.locator("#login-view").is_visible())
                self.assertTrue(page.locator("#workspace").is_hidden())
                page.locator("#password").fill("not stored")
                page.locator("#login-form button").click()
                page.locator("#workspace").wait_for(state="visible")
                self.assertEqual(3, page.locator(".workspace > section").count())

                page.locator('[data-slide-id="base-two"] [data-action="up"]').click()
                self.assertEqual("base-two", page.locator(".slide-item").first.get_attribute("data-slide-id"))
                self.assertIn("Chưa lưu", page.locator("#draft-status").text_content())
                page.locator('[data-slide-id="base-two"] [data-action="toggle"]').click()
                self.assertIn("base-two", page.locator('[data-slide-id="base-two"]').get_attribute("class"))

                page.locator("#add-slide").click()
                custom = page.locator(".slide-item.custom").last
                custom.click()
                attack = '<img src=x onerror="window.xss=1">'
                page.locator("#field-title").fill(attack)
                page.locator("#field-title").dispatch_event("input")
                self.assertEqual(attack, page.locator("#preview-title").text_content())
                self.assertIsNone(page.evaluate("window.xss"))
                self.assertEqual(0, page.locator("#preview img[src='x']").count())
                page.locator("#save-draft").click()
                page.locator("#message", has_text="Đã lưu bản nháp").wait_for()
                self.assertTrue(any(method == "PUT" and url.endswith("/draft") for method, url, _ in requests))

                page.set_viewport_size({"width": 390, "height": 844})
                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 390)
                ratio = page.locator("#preview").evaluate("el => getComputedStyle(el).aspectRatio")
                self.assertIn("16", ratio)

                page.reload(wait_until="load")
                page.locator("#password").fill("not stored")
                page.locator("#login-form button").click()
                page.locator("#workspace").wait_for(state="visible")
                self.assertGreater(page.locator(".slide-item.custom").count(), 0)
            finally:
                browser.close()

    def test_first_run_requires_confirmation_and_never_stores_password(self):
        published = {
            "schema_version": 1, "revision": "published-1", "order": ["base-one"],
            "hidden": [], "overrides": {}, "custom_slides": [],
        }
        setup_payloads = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()

                def api(route, request):
                    path = request.url.split("sslip.io", 1)[-1]
                    if path == "/setup-status":
                        route.fulfill(json={"setup_required": True})
                    elif path == "/setup":
                        setup_payloads.append(json.loads(request.post_data))
                        route.fulfill(json={"csrf_token": "setup-csrf"})
                    elif path == "/slides":
                        route.fulfill(json={"published": published, "draft": None})
                    else:
                        route.fulfill(status=404, json={"error": "not_found"})

                page.route("https://slide-admin.103-142-26-14.sslip.io/**", api)
                page.goto(ADMIN.as_uri(), wait_until="load")
                page.locator("#setup-form").wait_for(state="visible")
                self.assertTrue(page.locator("#login-form").is_hidden())
                self.assertGreaterEqual(int(page.locator("#new-password").get_attribute("minlength")), 12)

                page.locator("#new-password").fill("a private password")
                page.locator("#confirm-password").fill("does not match")
                page.locator("#setup-form button").click()
                self.assertEqual([], setup_payloads)
                self.assertIn("khớp", page.locator("#login-error").text_content())

                secret = '<img src=x onerror="window.xss=1">long-password'
                page.locator("#new-password").fill(secret)
                page.locator("#confirm-password").fill(secret)
                page.locator("#setup-form button").click()
                page.locator("#workspace").wait_for(state="visible")
                self.assertEqual([{"password": secret}], setup_payloads)
                self.assertEqual("", page.locator("#new-password").input_value())
                self.assertEqual("", page.locator("#confirm-password").input_value())
                self.assertNotIn(secret, page.evaluate("JSON.stringify(localStorage)"))
                self.assertIsNone(page.evaluate("window.xss"))
                self.assertEqual(0, page.locator("img[src='x']").count())
            finally:
                browser.close()

    def test_admin_javascript_has_no_html_injection_sink(self):
        source = (ROOT / "100/admin/app.js").read_text(encoding="utf-8")
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("eval(", source)
        self.assertNotRegex(source, r"\.on(?:error|load|click)\s*=")


if __name__ == "__main__":
    unittest.main()
