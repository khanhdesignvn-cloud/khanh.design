"""Phase 1 on built assets; intercept fixture GETs and block writes."""
import os, unittest
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
BASE=os.environ.get('ITEM_BASE_URL','http://127.0.0.1:8795')
class Phase1Browser(unittest.TestCase):
 def test_types_navigation_memory_and_clean_client(self):
  with sync_playwright() as pw:
   browser=pw.chromium.launch(args=['--no-sandbox'])
   for width in [1280,390]:
    page=browser.new_page(viewport={'width':width,'height':844}); errors=[]; writes=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    def route(r):
     if r.request.method not in ('GET','HEAD'): writes.append(r.request.url);r.abort()
     elif '/api/project/' in r.request.url:
      kind=r.request.url.rsplit('/',1)[-1]
      r.fulfill(json={'data':{'id':kind,'name':'Demo '+kind,'subtitle':'Public summary','presentation':kind,'updatedAt':'2026-09-10T00:00:00.000Z','groups':[{'id':'g','name':'Line','category':'Category','items':[{'id':'i','name':'Leaf','status':'Đang triển khai','note':'','images':[]}]}]},'revision':1})
     else:r.continue_()
    page.route('**/*',route)
    for kind,item,gallery in [('design','Hạng mục','Showcase'),('course','Bài học','Học liệu'),('catalog','Sản phẩm','Bộ sưu tập')]:
     page.goto(BASE+'/p/'+kind)
     expect(page.locator('.project-intro')).to_contain_text('Public summary')
     expect(page.locator('.project-intro')).to_contain_text('10/9/2026')
     page.get_by_role('tab',name=gallery,exact=True).click()
     expect(page.locator('.showcase')).not_to_contain_text('Thêm ảnh')
     page.get_by_role('tab',name=item,exact=True).click()
     page.get_by_label('Chọn nhóm').select_option('g')
     page.get_by_role('textbox',name='Tìm hạng mục').fill('Leaf')
     page.reload()
     expect(page.get_by_role('tab',name=item,exact=True)).to_have_attribute('data-state','active')
     expect(page.get_by_role('textbox',name='Tìm hạng mục')).to_have_value('Leaf')
     expect(page.get_by_label('Chọn nhóm')).to_have_value('g')
     page.locator('.table-name').click()
     expect(page.locator('.detail-breadcrumb')).to_contain_text('Category')
     page.locator('.detail-breadcrumb').get_by_role('button',name='Line',exact=True).click()
     expect(page.locator('.detail-panel')).not_to_be_visible()
     expect(page.get_by_label('Chọn nhóm')).to_have_value('g')
     page.locator('.project-breadcrumb').get_by_role('button',name='Demo '+kind,exact=True).click()
     expect(page.get_by_label('Chọn nhóm')).to_have_value('all')
     expect(page.get_by_role('textbox',name='Tìm hạng mục')).to_have_value('')
     self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
     out=Path('/tmp/phase1-evidence');out.mkdir(exist_ok=True)
     page.screenshot(path=str(out/f'{kind}-{width}.png'))
    self.assertEqual(errors,[]);self.assertEqual(writes,[]);page.close()
   browser.close()
 def test_scroll_and_map_position_survive_tabs_and_reload(self):
  with sync_playwright() as pw:
   browser=pw.chromium.launch(args=['--no-sandbox']);page=browser.new_page(viewport={'width':1280,'height':844})
   fixture={'id':'position','name':'Position','subtitle':'','groups':[{'id':'g','name':'Long group','items':[{'id':str(i),'name':'Item '+str(i),'status':'Đang triển khai','note':'','images':[]} for i in range(30)]}]}
   page.route('**/api/project/**',lambda r:r.fulfill(json={'data':fixture}))
   page.goto(BASE+'/p/position');page.get_by_role('tab',name='Hạng mục',exact=True).click()
   page.locator('.table-wrap').evaluate('(e)=>e.scrollTop=400');page.wait_for_timeout(200)
   page.get_by_role('tab',name='Showcase',exact=True).click();page.get_by_role('tab',name='Hạng mục',exact=True).click()
   self.assertGreater(page.locator('.table-wrap').evaluate('(e)=>e.scrollTop'),350)
   page.reload();expect(page.locator('.table-wrap')).to_be_visible();page.wait_for_timeout(200)
   self.assertGreater(page.locator('.table-wrap').evaluate('(e)=>e.scrollTop'),350)
   page.get_by_role('tab',name='Sơ đồ',exact=True).click()
   page.get_by_role('button',name='Phóng to',exact=True).click()
   page.locator('.canvas').evaluate('(e)=>{e.scrollTop=400;e.scrollLeft=100}');page.wait_for_timeout(200)
   page.reload();expect(page.locator('.canvas')).to_be_visible();page.wait_for_timeout(200)
   self.assertGreater(page.locator('.canvas').evaluate('(e)=>e.scrollTop'),350)
   expect(page.locator('.map-footer')).to_contain_text('120%')
   browser.close()
