from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_homepage_uses_maintainable_local_assets_and_preserves_routes():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert '<html lang="vi">' in html
    assert 'href="assets/home.css"' in html
    assert 'src="assets/home-db.js"' in html
    assert 'src="assets/home.js"' in html
    assert "khe-sanh-design-map" not in html
    assert "<main" in html and "<dialog" in html
    for route in ("100/index.html", "khesanhfarm/index.html", "quan-ly/index.html"):
        assert (ROOT / route).is_file()


def test_homepage_javascript_avoids_unsafe_user_content_rendering():
    source = (ROOT / "assets/home.js").read_text(encoding="utf-8")
    assert "textContent" in source
    assert ".innerHTML" not in source
