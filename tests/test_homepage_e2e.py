import contextlib
import functools
import http.server
import threading
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def site_url():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser, site_url):
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    page = context.new_page()
    page.set_default_timeout(5_000)
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(site_url)
    yield page
    assert errors == []
    context.close()


def test_seed_views_search_filter_and_map_controls(page):
    expect(page.locator("h2", has_text="100 năm cà phê Khe Sanh")).to_be_visible()
    expect(page.locator("[data-group-card]")).to_have_count(4)
    expect(page.locator("[data-item-card]")).to_have_count(13)
    expect(page.get_by_text("0 / 13", exact=True)).to_be_visible()
    expected_groups = {
        "core": ["Logo & biểu tượng", "Màu sắc & typography", "Pattern & brand guidelines"],
        "media": ["Key visual & poster", "Banner & bài đăng mạng xã hội", "Video giới thiệu"],
        "space": ["Cổng chào & sân khấu", "Gian hàng & bảng chỉ dẫn", "Photobooth & check-in"],
        "gift": ["Thư mời & vé tham dự", "Túi quà & bao bì cà phê", "Áo, mũ & quà lưu niệm", "Ví dụ"],
    }
    previous_bottom = None
    for group_id, names in expected_groups.items():
        cards = page.locator(f'[data-item-card][data-group-id="{group_id}"]')
        assert cards.locator("h4").all_inner_texts() == names
        boxes = [cards.nth(index).bounding_box() for index in range(cards.count())]
        top, bottom = min(box["y"] for box in boxes), max(box["y"] + box["height"] for box in boxes)
        if previous_bottom is not None:
            assert top >= previous_bottom + 20
        previous_bottom = bottom

    page.get_by_role("tab", name="Bảng").click()
    expect(page.get_by_role("table")).to_be_visible()
    expect(page.locator("tbody tr")).to_have_count(13)
    page.get_by_role("tab", name="Showcase").click()
    expect(page.get_by_text("Chưa có hình ảnh", exact=False)).to_be_visible()

    page.get_by_role("tab", name="Sơ đồ").click()
    page.get_by_role("searchbox", name="Tìm hạng mục").fill("Logo")
    expect(page.locator("[data-item-card]")).to_have_count(1)
    page.get_by_role("searchbox", name="Tìm hạng mục").fill("")
    page.get_by_label("Lọc trạng thái").select_option("done")
    expect(page.locator("[data-item-card]")).to_have_count(0)
    page.get_by_label("Lọc trạng thái").select_option("all")

    canvas = page.locator("[data-map-viewport]")
    before = canvas.get_attribute("data-transform")
    page.get_by_role("button", name="Phóng to").click()
    assert canvas.get_attribute("data-transform") != before
    page.get_by_role("button", name="Vừa màn hình").click()
    expect(canvas).to_have_attribute("data-scale", "1")
    box = canvas.bounding_box()
    page.mouse.move(box["x"] + 300, box["y"] + 250)
    page.mouse.down()
    page.mouse.move(box["x"] + 350, box["y"] + 280)
    page.mouse.up()
    expect(canvas).not_to_have_attribute("data-x", "0")


def test_group_item_crud_status_and_local_storage_persistence(page):
    page.get_by_role("button", name="Nhóm mới").click()
    page.get_by_label("Tên nhóm").fill("Nhóm thử nghiệm")
    page.get_by_role("button", name="Lưu").click()
    expect(page.get_by_text("Nhóm thử nghiệm", exact=True)).to_be_visible()

    group = page.locator("[data-group-card]", has_text="Nhóm thử nghiệm")
    group.get_by_role("button", name="Thêm hạng mục").click()
    page.get_by_label("Tên hạng mục").fill("Hạng mục an toàn <img src=x onerror=alert(1)>")
    page.get_by_role("button", name="Lưu").click()
    item = page.locator("[data-item-card]", has_text="Hạng mục an toàn")
    expect(item).to_be_visible()
    expect(item.locator("img")).to_have_count(0)

    item.click()
    page.get_by_label("Trạng thái", exact=True).select_option("done")
    page.get_by_role("button", name="Lưu").click()
    expect(page.get_by_text("1 / 14", exact=True)).to_be_visible()
    page.reload()
    expect(page.get_by_text("Nhóm thử nghiệm", exact=True)).to_be_visible()
    expect(page.get_by_text("1 / 14", exact=True)).to_be_visible()

    page.locator("[data-group-card]", has_text="Nhóm thử nghiệm").get_by_role("button", name="Sửa nhóm").click()
    page.get_by_label("Tên nhóm").fill("Nhóm đã sửa")
    page.get_by_role("button", name="Lưu").click()
    expect(page.get_by_text("Nhóm đã sửa", exact=True)).to_be_visible()
    page.locator("[data-group-card]", has_text="Nhóm đã sửa").get_by_role("button", name="Xóa nhóm").click()
    page.get_by_role("button", name="Xác nhận xóa").click()
    expect(page.get_by_text("Nhóm đã sửa", exact=True)).to_have_count(0)


def test_project_crud_image_indexeddb_reset_and_storage_error(page):
    page.get_by_role("button", name="Dự án mới").click()
    page.get_by_label("Tên dự án").fill("Dự án mùa thu")
    page.get_by_label("Mã dự án").fill("MUA26")
    page.get_by_label("Mô tả").fill("Bộ nhận diện mới")
    page.get_by_role("button", name="Lưu").click()
    expect(page.locator("h2", has_text="Dự án mùa thu")).to_be_visible()
    page.get_by_role("button", name="Sửa dự án").click()
    page.get_by_label("Tên dự án").fill("Dự án mùa thu 2026")
    page.get_by_role("button", name="Lưu").click()
    expect(page.locator("h2", has_text="Dự án mùa thu 2026")).to_be_visible()

    page.get_by_role("button", name="Xóa dự án").click()
    page.get_by_role("button", name="Xác nhận xóa").click()
    expect(page.locator("h2", has_text="100 năm cà phê Khe Sanh")).to_be_visible()

    page.get_by_role("tab", name="Showcase").click()
    page.get_by_label("Thêm ảnh showcase").set_input_files({
        "name": "sample.png", "mimeType": "image/png",
        "buffer": bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc000000301010018dd8db10000000049454e44ae426082")
    })
    expect(page.get_by_alt_text("sample.png")).to_be_visible()
    page.reload()
    page.get_by_role("tab", name="Showcase").click()
    expect(page.get_by_alt_text("sample.png")).to_be_visible()

    page.get_by_role("button", name="Khôi phục dữ liệu mẫu").click()
    page.get_by_role("button", name="Xác nhận khôi phục").click()
    expect(page.locator("[data-group-card]")).to_have_count(4)
    expect(page.locator("[data-item-card]")).to_have_count(13)

    page.evaluate("Object.defineProperty(Storage.prototype, 'setItem', {value() { throw new DOMException('full', 'QuotaExceededError') }})")
    page.get_by_role("button", name="Nhóm mới").click()
    page.get_by_label("Tên nhóm").fill("Không lưu được")
    page.get_by_role("button", name="Lưu").click()
    expect(page.get_by_role("alert")).to_contain_text("Không thể lưu")


def test_mobile_layout_focus_and_no_page_overflow(browser, site_url):
    context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = context.new_page()
    page.goto(site_url)
    expect(page.locator("[data-mobile-menu]")).to_be_visible()
    root = page.locator(".root-card")
    core = page.locator('[data-group-card][data-group-id="core"]')
    expect(root).to_be_visible()
    expect(core).to_be_visible()
    host_box = page.locator(".view-host").bounding_box()
    for card in (root, core):
        box = card.bounding_box()
        assert box["x"] < host_box["x"] + host_box["width"]
        assert box["x"] + box["width"] > host_box["x"]
        assert box["y"] < host_box["y"] + host_box["height"]
        assert box["y"] + box["height"] > host_box["y"]
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement === document.querySelector('.skip-link')")
    assert page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
    context.close()
