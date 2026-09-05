import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDENT = ROOT / "hoc-vien"
ADMIN = ROOT / "quan-ly"
LANDING = ROOT / "ai-learning" / "index.html"


def read(path):
    return path.read_text(encoding="utf-8")


def test_student_and_admin_portal_assets_exist_and_javascript_parses():
    for folder in (STUDENT, ADMIN):
        for name in ("index.html", "styles.css", "app.js"):
            assert (folder / name).exists(), f"missing {folder.name}/{name}"
        result = subprocess.run(["node", "--check", str(folder / "app.js")], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_student_page_has_accessible_login_submission_and_progress_regions():
    html = read(STUDENT / "index.html")
    for marker in (
        'id="student-login"',
        'name="application_id"',
        'name="phone"',
        'id="student-app"',
        'id="week-list"',
        'id="submission-form"',
        'name="artifact_url"',
        'name="note"',
        'id="submission-history"',
        'aria-live="polite"',
    ):
        assert marker in html
    assert html.count('type="range"') == 4
    assert 'href="/ai-learning/"' in html


def test_admin_page_has_login_summary_filters_and_review_form():
    html = read(ADMIN / "index.html")
    for marker in (
        'id="admin-login"',
        'name="admin_key"',
        'id="admin-app"',
        'id="summary-cards"',
        'id="student-table"',
        'id="review-form"',
        'name="review_status"',
        'name="instructor_score"',
        'name="instructor_feedback"',
        'aria-live="polite"',
    ):
        assert marker in html


def test_portal_javascript_uses_safe_dom_and_session_only_auth():
    combined = read(STUDENT / "app.js") + "\n" + read(ADMIN / "app.js")
    assert "innerHTML" not in combined
    assert "localStorage" not in combined
    assert "sessionStorage" in combined
    assert "textContent" in combined
    assert "createElement" in combined
    assert "Authorization" in combined
    assert "/course/portal/" in combined
    assert "/course/admin/" in combined
    assert not re.search(r"admin[_-]?(key|token)\s*=\s*['\"][^'\"]+", combined, re.I)


def test_portal_visual_system_is_responsive_and_keyboard_visible():
    for folder in (STUDENT, ADMIN):
        css = read(folder / "styles.css")
        assert "Google Sans Flex" in css
        assert "@media" in css and "max-width" in css
        assert ":focus-visible" in css
        assert "prefers-reduced-motion" in css
        assert "overflow-wrap" in css or "word-break" in css
        assert "#161616" in css
        assert "[hidden]" in css and "!important" in css


def test_landing_page_links_to_student_portal_without_exposing_admin():
    html = read(LANDING)
    assert 'href="/hoc-vien/"' in html
    assert 'href="/quan-ly/"' not in html
