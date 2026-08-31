from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "index.html"
CSS = ROOT / "styles.css"
JS = ROOT / "app.js"


def test_homepage_has_personal_brand_structure_and_no_hkm_copy():
    html = PAGE.read_text(encoding="utf-8")
    required = [
        "khanh.design",
        "Nguyễn Quốc Khánh",
        "Brand identity designer",
        'id="about"',
        'id="projects"',
        'id="services"',
        'id="process"',
        'id="contact"',
    ]
    assert not [item for item in required if item not in html]
    assert "HOÀNG KIM MINH" not in html
    assert "FURNITURE" not in html


def test_projects_use_real_khanh_design_assets():
    html = PAGE.read_text(encoding="utf-8")
    for project in ["SONCA", "Hemp &amp; Co.", "Khe Sanh", "99 ý tưởng logo quả chuối"]:
        assert project in html
    for image in ["sonca.webp", "hemp-co.webp", "khe-sanh.webp", "ribbon-banana.webp"]:
        assert f"assets/{image}" in html
        assert (ROOT / "assets" / image).exists()
    assert 'loading="lazy"' not in html


def test_project_brief_form_is_functional_and_safe():
    html = PAGE.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    required_html = [
        'id="project-form"',
        'name="name"',
        'name="phone"',
        'name="email"',
        'name="brand"',
        'name="service"',
        'name="budget"',
        'name="story"',
        'id="form-success"',
    ]
    assert not [item for item in required_html if item not in html]
    assert "localStorage.setItem" in js
    assert "mailto:hi@nguyenquockhanh.vn" in js
    assert "encodeURIComponent" in js
    assert ".textContent" in js
    assert "innerHTML" not in js


def test_accessibility_and_responsive_motion_contract():
    html = PAGE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    js = JS.read_text(encoding="utf-8")
    assert 'class="skip-link"' in html
    assert 'aria-controls="mobile-menu"' in html
    assert "prefers-reduced-motion" in css
    assert "IntersectionObserver" in js
    assert "Escape" in js
    assert "@media(max-width:800px)" in css


def test_content_remains_visible_without_intersection_observer():
    css = CSS.read_text(encoding="utf-8")
    assert ".reveal{opacity:0" not in css
    assert "@keyframes revealIn" in css


def test_demo_follows_the_manus_reference_visual_system():
    html = PAGE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert 'class="hero-image"' in html
    assert 'class="hero-arch"' in html
    assert 'class="project-ribbon ' in html
    assert html.count('class="ribbon-card"') == 4
    assert "--gold:#c59b63" in css
    assert ".hero-image" in css
    assert ".hero-arch" in css
    assert "--signal:" not in css
