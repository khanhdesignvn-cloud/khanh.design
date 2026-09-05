from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "ai-learning"
PAGE = SITE / "index.html"
CSS = SITE / "styles.css"


class CoursePageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.labels_for = set()
        self.inputs = {}
        self.heading_levels = []
        self.title = []
        self.meta = {}
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag in {"a", "link", "script"}:
            value = attrs.get("href") or attrs.get("src")
            if value:
                self.links.append(value)
        if tag == "label" and attrs.get("for"):
            self.labels_for.add(attrs["for"])
        if tag in {"input", "textarea", "select"} and attrs.get("name"):
            self.inputs[attrs["name"]] = attrs
        if tag in {f"h{i}" for i in range(1, 7)}:
            self.heading_levels.append(int(tag[1]))
        if tag == "title":
            self.in_title = True
        if tag == "meta" and attrs.get("name"):
            self.meta[attrs["name"]] = attrs.get("content", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.meta["canonical"] = attrs.get("href", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def page_data():
    html = PAGE.read_text(encoding="utf-8")
    parser = CoursePageParser()
    parser.feed(html)
    return html, parser


def test_microsite_has_course_metadata_and_relative_assets():
    html, page = page_data()
    css = CSS.read_text(encoding="utf-8")
    assert "AI Vận Hành Doanh Nghiệp" in "".join(page.title)
    assert "6 tuần" in page.meta["description"]
    assert page.meta["canonical"].endswith("/ai-learning/")
    assert 'href="styles.css"' in html
    assert 'href="favicon.svg"' in html
    assert (SITE / "favicon.svg").exists()
    assert 'src="app.js"' in html
    for link in page.links:
        parsed = urlparse(link)
        if parsed.scheme or link.startswith("//"):
            assert link == page.meta["canonical"] or parsed.scheme in {"mailto", "tel"}, f"Unexpected external asset/link: {link}"
    assert "http://" not in css and "https://" not in css


def test_page_contains_complete_honest_course_content():
    html, page = page_data()
    required_sections = {
        "outcomes",
        "curriculum",
        "format",
        "instructor",
        "pricing",
        "faq",
        "apply",
    }
    assert required_sections <= page.ids
    assert len(re.findall(r'class="[^"]*\bweek-card\b[^"]*"', html)) == 6
    assert "Claude là công cụ AI trung tâm" in html
    assert "Tối đa 15 học viên" in html
    assert "3.900.000" in html and "4.900.000" in html
    assert "hoàn phí" in html.lower()
    lowered = re.sub(r"\s+", " ", html.lower())
    for unsupported_claim in ("x10 doanh thu", "80% công việc", "cam kết thay thế nhân sự", "ai thay thế nhân sự"):
        assert unsupported_claim not in lowered


def test_page_is_semantic_accessible_and_responsive():
    html, page = page_data()
    css = CSS.read_text(encoding="utf-8")
    assert 'class="skip-link"' in html
    assert 'href="#main-content"' in html
    assert page.heading_levels[0] == 1
    assert page.heading_levels.count(1) == 1
    assert all(next_level - level <= 1 for level, next_level in zip(page.heading_levels, page.heading_levels[1:]))
    assert 'aria-live="polite"' in html
    assert "prefers-reduced-motion" in css
    assert "@media" in css
    assert "min-height:44px" in css.replace(" ", "")
    assert "overflow-x" in css


def test_visual_system_follows_approved_v3_reference_and_google_sans_flex():
    html, _ = page_data()
    css = CSS.read_text(encoding="utf-8")
    assert ":root" in css
    for token in ("--purple:", "--purple-deep:", "--bg-soft:"):
        assert token in css
    assert "Google Sans Flex" in css
    assert "google-sans-flex" in css
    assert (SITE / "assets" / "google-sans-flex-vietnamese-wght-normal.woff2").exists()
    assert (SITE / "assets" / "google-sans-flex-latin-ext-wght-normal.woff2").exists()
    assert 'class="solutions"' in html
    assert 'class="gallery-track"' in html
    assert html.count("data:image/jpeg;base64,") >= 5
    assert ".sol-panels" in css
    assert "grid" in css
    assert "clamp(" in css
