"""Real Chromium UI tests. Only fixture GETs; every mutation is blocked.
Run: SHOWCASE_BASE_URL=http://127.0.0.1:8795 python -m unittest discover -s tests -p test_showcase_browser.py -v
Requires Python playwright and its Chromium browser.
"""
import os
import unittest
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('SHOWCASE_BASE_URL', 'http://127.0.0.1:8795')

def image(n):
    return {'id': str(n), 'name': f'design-{n}.png', 'url': f'/fixture/design-{n}.png', 'type': 'image'}

def item(id, name, files, images=None, **kwargs):
    return dict(id=id, name=name, status='Đợi duyệt', note='', images=images or [], files=files, **kwargs)

FIXTURE = {'data': {'projects': [{'id': 'khesanh', 'name': 'Showcase fixture', 'subtitle': '', 'groups': [
    {'id': 'g1', 'name': 'Nhận diện', 'items': [item('a', 'Logo kỷ niệm', [image(1), image(2)])]},
    {'id': 'g2', 'name': 'Ấn phẩm', 'items': [item('b', 'Thiệp mời', [image(3), {'id': 'pdf', 'name': 'guide.pdf', 'url': '/fixture/guide.pdf', 'type': 'pdf'}, {'id': 'drive', 'name': 'Drive source', 'url': 'https://drive.google.com/file/d/fixture/view', 'type': 'drive'}]), item('c', 'Tài liệu riêng', [], driveUrl='https://drive.google.com/drive/folders/fixture'), item('d', 'Ảnh cũ', [], ['/fixture/legacy.png'])]}
]}]}, 'revision': 42}

class ShowcaseBrowser(unittest.TestCase):
    def setUp(self):
        self.pw = sync_playwright().start()
        self.addCleanup(self.pw.stop)
        self.browser = self.pw.chromium.launch(headless=True, args=['--no-sandbox'])
        self.addCleanup(self.browser.close)
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 900}, has_touch=True)
        self.page = self.context.new_page()
        self.mutations = []
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        def route(req):
            if req.request.method not in ('GET', 'HEAD'):
                self.mutations.append(req.request.url)
                req.abort()
            elif '/api/workspace' in req.request.url:
                req.fulfill(json=FIXTURE)
            elif '/fixture/' in req.request.url:
                req.fulfill(content_type='image/svg+xml', body='<svg xmlns="http://www.w3.org/2000/svg" width="300" height="800"><rect width="300" height="800" fill="#215534"/><text x="12" y="40" fill="white">Showcase fixture</text></svg>')
            else:
                req.continue_()
        self.page.route('**/*', route)
        self.page.goto(BASE + '/admin')
        self.page.get_by_role('tab', name='Showcase', exact=True).click()
        expect(self.page.get_by_text('Logo kỷ niệm', exact=True)).to_be_visible()

    def tearDown(self):
        try:
            self.assertEqual(self.mutations, [], 'UI must never attempt database/media mutations')
            self.assertEqual(self.errors, [], 'No browser errors')
        finally:
            pass  # addCleanup also runs if setUp fails.

    def test_all_images_grouped_without_cropping_and_separate_links(self):
        cards = self.page.locator('.showcase-card')
        expect(cards).to_have_count(4)
        expect(cards.nth(0).locator('img')).to_have_count(2)
        expect(self.page.locator('.showcase img')).to_have_count(4)
        for img in self.page.locator('.showcase img').all():
            self.assertEqual(img.evaluate('(e)=>getComputedStyle(e).objectFit'), 'contain')
        expect(self.page.get_by_role('link', name='guide.pdf')).to_have_attribute('href', '/fixture/guide.pdf')
        expect(self.page.get_by_role('link', name='Drive source')).to_have_attribute('target', '_blank')
        expect(self.page.get_by_role('link', name='Thư mục Google Drive')).to_have_attribute('href', 'https://drive.google.com/drive/folders/fixture')

    def test_exact_image_continuous_order_controls_keyboard_focus_and_fullscreen(self):
        trigger = self.page.get_by_role('button', name='Xem design-2.png · Logo kỷ niệm', exact=True)
        trigger.click()
        dialog = self.page.get_by_role('dialog')
        expect(dialog).to_be_visible()
        expect(dialog.locator('img')).to_have_attribute('src', '/fixture/design-2.png')
        expect(dialog.get_by_role('heading')).to_have_text('Logo kỷ niệm')
        expect(dialog.get_by_text('2 / 4', exact=True)).to_be_visible()
        self.page.keyboard.press('ArrowRight')
        expect(dialog.locator('img')).to_have_attribute('src', '/fixture/design-3.png')
        expect(dialog.get_by_role('heading')).to_have_text('Thiệp mời')
        dialog.get_by_role('button', name='Ảnh tiếp').click()
        expect(dialog.locator('img')).to_have_attribute('src', '/fixture/legacy.png')
        dialog.get_by_role('button', name='Ảnh tiếp').click()
        expect(dialog.get_by_text('1 / 4', exact=True)).to_be_visible()
        self.page.keyboard.press('ArrowLeft')
        expect(dialog.get_by_text('4 / 4', exact=True)).to_be_visible()
        dialog.get_by_role('button', name='Ảnh trước').click()
        expect(dialog.get_by_text('3 / 4', exact=True)).to_be_visible()
        dialog.get_by_role('button', name='Toàn màn hình', exact=True).click()
        self.page.wait_for_function('!!document.fullscreenElement')
        dialog.get_by_role('button', name='Thoát toàn màn hình', exact=True).click()
        self.page.wait_for_function('!document.fullscreenElement')
        self.page.keyboard.press('Escape')
        expect(dialog).not_to_be_visible()
        expect(trigger).to_be_focused()
        trigger.click()
        dialog.get_by_role('button', name='Đóng trình chiếu').click()
        expect(dialog).not_to_be_visible()

    def test_mobile_swipe_no_crop_no_overflow_and_focus_trap(self):
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.get_by_role('button', name='Xem design-2.png · Logo kỷ niệm', exact=True).click()
        dialog = self.page.get_by_role('dialog')
        expect(dialog).to_be_visible()
        stage = dialog.locator('.showcase-slide-stage')
        # Trusted Chromium touch input on the real component; no backend calls.
        cdp = self.context.new_cdp_session(self.page)
        def swipe(x1, y1, x2, y2):
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x1, 'y': y1}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x2, 'y': y2}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        swipe(310, 400, 50, 405)
        expect(dialog.get_by_text('3 / 4', exact=True)).to_be_visible()
        swipe(50, 400, 310, 405)
        expect(dialog.get_by_text('2 / 4', exact=True)).to_be_visible()
        # Vertical scrolling and small taps must not change slides.
        for end in [(200, 700), (205, 402)]:
            swipe(200, 400, *end)
        expect(dialog.get_by_text('2 / 4', exact=True)).to_be_visible()
        self.assertEqual(dialog.locator('img').evaluate('(e)=>getComputedStyle(e).objectFit'), 'contain')
        box = dialog.bounding_box()
        assert box is not None
        self.assertLessEqual(box['x'] + box['width'], 391)
        self.assertLessEqual(box['y'] + box['height'], 845)
        for _ in range(8):
            self.page.keyboard.press('Tab')
            self.assertTrue(dialog.evaluate('(e)=>e.contains(document.activeElement)'))
        self.page.screenshot(path='/tmp/showcase-mobile-slideshow.png')
        dialog.get_by_role('button', name='Đóng trình chiếu').click()
        self.assertTrue(self.page.locator('.showcase').evaluate('(e)=>e.scrollWidth<=e.clientWidth'))
        self.page.screenshot(path='/tmp/showcase-mobile-gallery.png')

    def test_filtered_single_image_legacy_filename_and_empty_state(self):
        search = self.page.get_by_role('textbox', name='Tìm hạng mục')
        search.fill('Ảnh cũ')
        expect(self.page.locator('.showcase img')).to_have_count(1)
        self.page.locator('.showcase-image').click()
        dialog = self.page.get_by_role('dialog')
        expect(dialog.get_by_text('legacy.png', exact=True)).to_be_visible()
        expect(dialog.get_by_text('1 / 1', exact=True)).to_be_visible()
        expect(dialog.get_by_role('button', name='Ảnh tiếp')).to_be_disabled()
        expect(dialog.get_by_role('button', name='Ảnh trước')).to_be_disabled()
        self.page.keyboard.press('ArrowRight')
        expect(dialog.get_by_text('1 / 1', exact=True)).to_be_visible()
        self.page.keyboard.press('Escape')
        search.fill('No matching item')
        expect(self.page.locator('.showcase img')).to_have_count(0)
        expect(self.page.get_by_text('Showcase của dự án', exact=True)).to_be_visible()
        self.page.get_by_role('button', name='Chọn hạng mục').click()
        expect(self.page.get_by_role('tab', name='Sản phẩm', exact=True)).to_have_attribute('data-state', 'active')

if __name__ == '__main__':
    unittest.main()
