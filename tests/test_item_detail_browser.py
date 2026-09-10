"""Public item-detail tests on built assets. Fixture GETs only, no data writes.
ITEM_BASE_URL=https://khanh.design python -m unittest discover -s tests -p test_item_detail_browser.py -v
"""
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from test_showcase_browser import FIXTURE, assert_private_ui
BASE = os.environ.get('ITEM_BASE_URL', 'http://127.0.0.1:8795')
OUT = Path(os.environ.get('ITEM_EVIDENCE', '/tmp/item-detail-evidence'))

class ItemDetailBrowser(unittest.TestCase):
    def setUp(self):
        self.pw = sync_playwright().start()
        self.addCleanup(self.pw.stop)
        self.browser = self.pw.chromium.launch(args=['--no-sandbox'])
        self.addCleanup(self.browser.close)
        self.context = self.browser.new_context(viewport={'width':1280,'height':900}, has_touch=True)
        self.page = self.context.new_page()
        self.mutations = []; self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        def route(r):
            if r.request.method not in ('GET','HEAD'):
                self.mutations.append(r.request.url); r.abort()
            elif '/api/project/' in r.request.url:
                r.fulfill(json={'data':FIXTURE['data']['projects'][0]})
            elif '/fixture/' in r.request.url:
                r.fulfill(content_type='image/svg+xml', body='<svg xmlns="http://www.w3.org/2000/svg" width="300" height="800"><rect width="300" height="800" fill="#215534"/></svg>')
            else: r.continue_()
        self.page.route('**/*', route)
        self.page.goto(BASE+'/p/item-detail-fixture')
        self.page.get_by_role('tab',name='Hạng mục',exact=True).click()
        OUT.mkdir(exist_ok=True)
    def tearDown(self):
        self.assertEqual(self.errors,[])
        self.assertEqual(self.mutations,[])
    def test_pdf_preview_and_report_hide_filenames(self):
        self.page.locator('.table-name').filter(has_text='Thiệp mời').click()
        assert_private_ui(self, self.page)
        self.page.locator('.file-tile').nth(1).click()
        expect(self.page.locator('.lightbox iframe')).to_have_attribute('title', 'Tài liệu PDF')
        expect(self.page.locator('.lightbox a')).to_have_attribute('href', '/fixture/guide.pdf')
        assert_private_ui(self, self.page)
        self.page.locator('.lightbox').get_by_role('button', name='Close', exact=True).click()
        expect(self.page.locator('.lightbox')).not_to_be_visible()
        self.page.locator('.detail-panel').get_by_role('button', name='Close', exact=True).click()
        expect(self.page.locator('.detail-panel')).not_to_be_visible()
        self.page.get_by_role('tab', name='Slide tổng', exact=True).click()
        for _ in range(4):
            self.page.locator('.slide-navigation').get_by_role('button', name='Tiếp').click()
            assert_private_ui(self, self.page)
        self.page.locator('.report-slide.current .report-gallery button').first.click()
        assert_private_ui(self, self.page)

    def test_drive_original_link(self):
        self.page.locator('.table-name').filter(has_text='Tài liệu riêng').click()
        link=self.page.get_by_role('link',name='TẢI FILE GỐC',exact=True)
        expect(link).to_be_visible()
        expect(link).to_have_attribute('href','https://drive.google.com/drive/folders/fixture')
        expect(link).to_have_attribute('target','_blank')
        self.assertIn('noopener',link.get_attribute('rel'))
        self.assertIn('linear-gradient',link.evaluate('(e)=>getComputedStyle(e).backgroundImage'))
        expect(link.locator('svg')).to_have_count(1)
        self.page.screenshot(path=str(OUT/'drive-button-desktop.png'))

    def test_item_scoped_slideshow(self):
        self.page.locator('.table-name').filter(has_text='Logo kỷ niệm').click()
        assert_private_ui(self, self.page)
        trigger=self.page.locator('.file-tile').nth(1)
        trigger.click()
        viewer=self.page.locator('.showcase-slideshow')
        expect(viewer).to_be_visible()
        assert_private_ui(self, self.page)
        expect(viewer.get_by_text('2 / 2',exact=True)).to_be_visible()
        stage=viewer.locator('.showcase-slide-stage img')
        expect(stage).to_have_attribute('src','/fixture/design-2.png')
        self.page.keyboard.press('ArrowRight')
        expect(stage).to_have_attribute('src','/fixture/design-1.png')
        self.page.keyboard.press('ArrowLeft')
        expect(viewer.get_by_text('2 / 2',exact=True)).to_be_visible()
        viewer.get_by_role('button',name='Ảnh trước',exact=True).click()
        expect(viewer.get_by_text('1 / 2',exact=True)).to_be_visible()
        viewer.get_by_role('button',name='Ảnh tiếp',exact=True).click()
        viewer.get_by_role('button',name='Phóng to ảnh',exact=True).click()
        expect(viewer.get_by_role('button',name='Đặt lại thu phóng')).to_have_text('125%')
        viewer.get_by_role('button',name='Thu nhỏ ảnh',exact=True).click()
        expect(viewer.get_by_role('button',name='Đặt lại thu phóng')).to_have_text('100%')
        viewer.get_by_role('button',name='Phóng to ảnh',exact=True).click()
        viewer.get_by_role('button',name='Đặt lại thu phóng').click()
        expect(viewer.get_by_role('button',name='Đặt lại thu phóng')).to_have_text('100%')
        thumbs=viewer.locator('.item-slide-thumbnails button')
        expect(thumbs).to_have_count(2)
        thumbs.nth(0).click()
        expect(stage).to_have_attribute('src','/fixture/design-1.png')
        with self.page.expect_download() as event:
            viewer.get_by_role('button',name='Tải ảnh hiện tại',exact=True).click()
        download=event.value
        self.assertEqual(download.suggested_filename,'design-1.png')
        self.assertIsNone(download.failure())
        download.save_as(str(OUT/'fixture-download.png'))
        viewer.get_by_role('button',name='Toàn màn hình',exact=True).click()
        self.page.wait_for_function('!!document.fullscreenElement')
        viewer.get_by_role('button',name='Thoát toàn màn hình',exact=True).click()
        self.page.wait_for_function('!document.fullscreenElement')
        self.page.screenshot(path=str(OUT/'item-desktop.png'))
        self.page.keyboard.press('Escape')
        expect(viewer).not_to_be_visible()
        expect(trigger).to_be_focused()
        expect(self.page.locator('.detail-panel')).to_be_visible()

    def test_mobile_item_swipe(self):
        self.page.set_viewport_size({'width':390,'height':844})
        self.page.locator('.table-name').filter(has_text='Logo kỷ niệm').click()
        self.page.locator('.file-tile').nth(1).click()
        viewer=self.page.locator('.showcase-slideshow')
        expect(viewer).to_be_visible()
        assert_private_ui(self, self.page)
        self.assertEqual(viewer.locator('.showcase-slide-controls span').evaluate('(e)=>getComputedStyle(e).color'),'rgb(245, 245, 245)')
        box=viewer.locator('.showcase-slide-stage').bounding_box()
        assert box
        y=box['y']+box['height']/2
        cdp=self.context.new_cdp_session(self.page)
        for typ,points in [('touchStart',[{'x':310,'y':y}]),('touchMove',[{'x':60,'y':y+3}]),('touchEnd',[])]:
            cdp.send('Input.dispatchTouchEvent',{'type':typ,'touchPoints':points})
        expect(viewer.get_by_text('1 / 2',exact=True)).to_be_visible()
        bounds=viewer.bounding_box(); assert bounds
        self.assertGreaterEqual(bounds['x'],0); self.assertGreaterEqual(bounds['y'],0)
        self.assertLessEqual(bounds['x']+bounds['width'],391)
        self.assertLessEqual(bounds['y']+bounds['height'],845)
        self.assertEqual(viewer.locator('.showcase-slide-stage img').evaluate('(e)=>getComputedStyle(e).objectFit'),'contain')
        for _ in range(12):
            self.page.keyboard.press('Tab')
            self.assertTrue(viewer.evaluate('(e)=>e.contains(document.activeElement)'))
        self.page.screenshot(path=str(OUT/'item-mobile.png'))
        viewer.get_by_role('button',name='Đóng trình chiếu',exact=True).click()
        expect(self.page.locator('.detail-panel')).to_be_visible()

if __name__=='__main__': unittest.main()
