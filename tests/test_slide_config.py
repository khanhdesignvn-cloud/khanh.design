import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT / "100" / "index.html"
CONFIG = ROOT / "100" / "slide-config.json"
SCRIPT = ROOT / "100" / "slide-config.js"


def validate_with_node(config, known_ids):
    program = """
const engine = require(process.argv[1]);
const config = JSON.parse(process.argv[2]);
const known = JSON.parse(process.argv[3]);
try { engine.validateConfig(config, known); process.stdout.write('valid'); }
catch (error) { process.stdout.write(error.message); process.exitCode = 2; }
"""
    return subprocess.run(
        ["node", "-e", program, str(SCRIPT), json.dumps(config), json.dumps(known_ids)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


class SlideConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        html = DECK.read_text(encoding="utf-8")
        self.known_ids = re.findall(r'<section class="s[^>]*data-slide-id="([^"]+)"', html)

    def assert_invalid(self, mutate):
        candidate = json.loads(json.dumps(self.config))
        mutate(candidate)
        result = validate_with_node(candidate, self.known_ids)
        self.assertEqual(2, result.returncode, result.stdout)

    def test_published_config_covers_every_stable_base_slide(self):
        self.assertEqual(1, self.config["schema_version"])
        self.assertIsInstance(self.config["revision"], str)
        self.assertTrue(self.config["revision"])
        self.assertEqual(29, len(self.known_ids))
        self.assertEqual(29, len(set(self.known_ids)))
        self.assertEqual(self.known_ids, self.config["order"])
        self.assertEqual([], self.config["hidden"])
        self.assertEqual({}, self.config["overrides"])
        self.assertEqual([], self.config["custom_slides"])
        self.assertEqual(0, validate_with_node(self.config, self.known_ids).returncode)

    def test_validator_rejects_duplicate_unknown_and_missing_ids(self):
        self.assert_invalid(lambda data: data["order"].__setitem__(1, data["order"][0]))
        self.assert_invalid(lambda data: data["order"].__setitem__(0, "unknown-slide"))
        self.assert_invalid(lambda data: data["order"].pop())

    def test_validator_rejects_markup_long_content_and_external_images(self):
        def add_custom(data):
            data["custom_slides"] = [{
                "id": "custom-one", "eyebrow": "Nhãn", "title": "Tiêu đề",
                "body": ["Nội dung"], "note": "Ghi chú", "image": "assets/admin/a.jpg",
            }]
            data["order"].append("custom-one")

        def with_markup(data):
            add_custom(data)
            data["custom_slides"][0]["title"] = "<img onerror=alert(1)>"

        def with_long_content(data):
            add_custom(data)
            data["custom_slides"][0]["body"] = ["x" * 2001]

        def with_external_image(data):
            add_custom(data)
            data["custom_slides"][0]["image"] = "https://example.com/a.jpg"

        self.assert_invalid(with_markup)
        self.assert_invalid(with_long_content)
        self.assert_invalid(with_external_image)

    def test_deck_loads_config_before_navigation_snapshot(self):
        html = DECK.read_text(encoding="utf-8")
        loader = html.index('src="slide-config.js"')
        apply_call = html.index("window.SlideConfig.loadAndApply().then")
        snapshot = html.index("const slides = [...document.querySelectorAll('.s')]")
        self.assertLess(loader, apply_call)
        self.assertLess(apply_call, snapshot)


if __name__ == "__main__":
    unittest.main()
