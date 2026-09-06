import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "100" / "index.html"


class SlideBaselineTests(unittest.TestCase):
    def test_current_deck_has_approved_29_slide_order(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(SLIDES.as_uri(), wait_until="load")
                titles = page.locator("section.s").evaluate_all(
                    "nodes => nodes.map(node => node.dataset.t)"
                )
            finally:
                browser.close()

        self.assertEqual(29, len(titles))
        self.assertEqual(
            [
                "Bốn nhóm ứng dụng · Tổng quan",
                "Hệ chữ",
                "Hoa văn & ngôn ngữ phụ trợ",
                "Bốn nhóm ứng dụng",
                "Hoa văn phụ trợ",
            ],
            titles[13:18],
        )


if __name__ == "__main__":
    unittest.main()
