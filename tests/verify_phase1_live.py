"""Read-only Phase 1 HTTPS verification on actual shared projects."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
OUT=Path('/tmp/phase1-evidence');OUT.mkdir(exist_ok=True)
BASE='https://khanh.design'
shares=[('dd95800d-dccb-4982-9dc7-b9694ff106be','design','Hạng mục','Showcase'),('1f7102fc-3893-49bc-8d21-fc3eab494fc2','catalog','Sản phẩm','Bộ sưu tập')]
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(args=['--no-sandbox'])
 for token,kind,item_label,gallery in shares:
  for width in [1440,390]:
   page=browser.new_page(viewport={'width':width,'height':900});errors=[];writes=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   def readonly(r):
    if r.request.method not in ('GET','HEAD'):writes.append(r.request.url);r.abort()
    else:r.continue_()
   page.route('**/*',readonly)
   response=page.request.get(BASE+'/api/project/'+token);assert response.status==200
   payload=response.json();data=payload['data'];assert data['presentation']==kind;assert data['updatedAt'];assert 'shareToken' not in data
   items=[i for g in data['groups'] for i in g['items']];done=sum(i['status']=='Hoàn thành' for i in items)
   navigation=page.goto(BASE+'/p/'+token)
   assert navigation is not None and navigation.status==200
   expect(page.locator('.workarea')).to_have_attribute('data-presentation',kind)
   expect(page.locator('.project-intro')).to_contain_text(data['name'])
   expect(page.locator('.intro-progress')).to_contain_text(f'{done} / {len(items)}')
   page.get_by_role('tab',name=item_label,exact=True).click()
   expect(page.locator('.table-name')).to_have_count(len(items))
   page.get_by_label('Chọn nhóm').select_option(data['groups'][0]['id'])
   page.reload();expect(page.get_by_label('Chọn nhóm')).to_have_value(data['groups'][0]['id'])
   expect(page.get_by_role('tab',name=item_label,exact=True)).to_have_attribute('data-state','active')
   page.locator('.project-breadcrumb').get_by_role('button',name=data['name'],exact=True).click()
   expect(page.get_by_label('Chọn nhóm')).to_have_value('all')
   page.get_by_label('Tìm hạng mục',exact=True).fill(items[0]['name'])
   page.get_by_label('Lọc tệp đính kèm').select_option('missing')
   page.reload()
   expect(page.get_by_label('Tìm hạng mục',exact=True)).to_have_value(items[0]['name'])
   expect(page.get_by_label('Lọc tệp đính kèm')).to_have_value('missing')
   page.locator('.project-breadcrumb').get_by_role('button',name=data['name'],exact=True).click()
   page.get_by_role('tab',name='Sơ đồ',exact=True).click()
   root=page.get_by_role('button',name='Thu/mở dự án',exact=True)
   root.click();expect(page.locator('[data-level=line]')).to_have_count(0)
   page.reload();expect(page.locator('[data-level=line]')).to_have_count(0)
   page.get_by_role('button',name='Thu/mở dự án',exact=True).click()
   expect(page.locator('[data-level=line]')).to_have_count(len(data['groups']))
   page.get_by_role('tab',name=gallery,exact=True).click()
   assert 'Thêm ảnh' not in page.locator('.showcase').inner_text()
   # Lazy artwork must finish loading before screenshot evidence is captured.
   if page.locator('.showcase-image img').count():
    page.wait_for_function("Array.from(document.querySelectorAll('.showcase-image img')).filter(e=>{const r=e.getBoundingClientRect();return r.top<innerHeight&&r.bottom>0}).every(e=>e.complete&&e.naturalWidth>0)")
   assert page.evaluate('document.documentElement.scrollWidth')<=width
   page.screenshot(path=str(OUT/f'live-{kind}-{width}.png'))
   assert not errors and not writes,(errors,writes)
   results.append({'url':BASE+'/p/'+token,'width':width,'presentation':kind,'groups':len(data['groups']),'items':len(items),'done':done,'updatedAt':data['updatedAt'],'browser_errors':errors,'writes':writes,'intro_navigation_gallery':'PASS'})
   page.close()
 for route,status in [('/admin',200),('/100/',200),('/khesanhfarm/',200),('/api/project/not-a-real-token',404)]:
  page=browser.new_page();r=page.request.get(BASE+route);assert r.status==status;(results.append({'route':route,'status':r.status}));page.close()
 page=browser.new_page();assert page.request.get(BASE+'/api/workspace').json()['data']['projects']==[]
 browser.close()
(OUT/'https-live.json').write_text(json.dumps(results,ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False))
