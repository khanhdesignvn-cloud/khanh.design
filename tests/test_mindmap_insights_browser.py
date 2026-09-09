"""Built public UI, intercepted fixture reads only; block all mutations."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('ITEM_BASE_URL', 'http://127.0.0.1:8795')
FIXTURE = {'id':'p','name':'Farm','subtitle':'','groups':[{'id':'g','category':'Cà phê','name':'Cao cấp','items':[
 {'id':'a','name':'Hạt rang','status':'Hoàn thành','note':'Yêu cầu màu xanh','images':[]},
 {'id':'b','name':'Lá','status':'Đang triển khai','note':'','images':[], 'driveUrl':'https://drive.google.com/drive/folders/example'}]}]}

class InsightsBrowser(unittest.TestCase):
    def test_search_filters_navigation_and_mobile(self):
        with sync_playwright() as pw:
            browser=pw.chromium.launch(args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':900})
            page.set_default_timeout(7000)
            errors=[]; mutations=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            def route(r):
                if r.request.method not in ('GET','HEAD'):
                    mutations.append(r.request.url); r.abort()
                elif '/api/project/' in r.request.url: r.fulfill(json={'data':FIXTURE,'revision':1})
                else: r.continue_()
            page.route('**/*',route)
            page.goto(BASE+'/p/insights-fixture')
            page.get_by_role('tab',name='Tổng quan',exact=True).click()
            expect(page.locator('.insight-project')).to_have_count(1)
            expect(page.locator('.insight-project')).to_contain_text('1 / 2 hoàn thành')
            expect(page.locator('.insight-result')).to_have_count(2)
            page.get_by_role('textbox',name='Tìm hạng mục').fill('mau xanh')
            expect(page.locator('.insight-result')).to_have_count(1)
            expect(page.locator('.insight-result')).to_contain_text('Farm / Cà phê / Cao cấp')
            page.locator('.insight-result').click()
            expect(page.locator('.detail-panel')).to_be_visible()
            expect(page.locator('.detail-panel')).to_contain_text('Hạt rang')
            page.locator('.detail-panel').get_by_role('button',name='Close',exact=True).click()
            page.get_by_role('textbox',name='Tìm hạng mục').fill('')
            page.get_by_label('Lọc tệp đính kèm').select_option('missing')
            expect(page.locator('.insight-result')).to_have_count(1)
            page.get_by_role('tab',name='Sản phẩm',exact=True).click()
            expect(page.locator('.table-name')).to_have_count(1)
            page.get_by_label('Lọc tệp đính kèm').select_option('all')
            page.get_by_role('textbox',name='Tìm hạng mục').fill('01.02')
            expect(page.locator('.table-name')).to_have_count(1)
            expect(page.locator('.table-name')).to_contain_text('Lá')
            page.get_by_role('textbox',name='Tìm hạng mục').fill('')
            page.get_by_role('tab',name='Tổng quan',exact=True).click()
            out=Path('/tmp/mindmap-upgrade-evidence');out.mkdir(exist_ok=True)
            page.screenshot(path=str(out/'overview-desktop.png'))
            page.set_viewport_size({'width':390,'height':844})
            expect(page.locator('.insight-result').first).to_be_visible()
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path=str(out/'overview-mobile.png'))
            self.assertEqual(errors,[])
            self.assertEqual(mutations,[])
