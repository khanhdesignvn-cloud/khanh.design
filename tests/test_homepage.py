from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "index.html"
TARGET = "/ai-learning/"


def test_root_redirects_visitors_to_course_site():
    html = PAGE.read_text(encoding="utf-8")
    assert '<meta http-equiv="refresh" content="0; url=/ai-learning/">' in html
    assert f'location.replace("{TARGET}")' in html
    assert f'href="{TARGET}"' in html
    assert "AI Vận Hành Doanh Nghiệp" in html
    assert "Brand identity designer" not in html
