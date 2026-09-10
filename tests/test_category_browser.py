"""Production-assets Chromium checks. Public live is read-only; admin writes isolated stage only."""
import os, json, time, uuid, hmac, hashlib, base64, sqlite3
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
BASE=os.environ.get('FARM_BASE','http://127.0.0.1:8795')
TOKEN='1f7102fc-3893-49bc-8d21-fc3eab494fc2'
PID='3cc585ac-3cdb-4b70-9e71-cc8369b66499'
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1600,'height':1000})
 errors=[]
 page.on('pageerror',lambda e: errors.append(str(e)))
 response=page.goto(BASE+'/p/'+TOKEN)
 assert response.status==200
 kind=page.request.get(BASE+'/api/project/'+TOKEN).json()['data'].get('presentation','design')
 item_label,gallery_label,report_label=('Sản phẩm','Bộ sưu tập','Hồ sơ sản phẩm') if kind=='catalog' else ('Hạng mục','Showcase','Slide tổng')
 expect(page.locator('[data-level=category]')).to_have_count(4)
 expect(page.locator('[data-level=line]')).to_have_count(13)
 expect(page.locator('[data-level=product]')).to_have_count(18)
 # Four distinct horizontal columns, not combined labels.
 xs=page.locator('.root-node,[data-level]').evaluate_all('(els)=>els.map(e=>({level:e.dataset.level||"root",x:parseFloat(getComputedStyle(e).left)}))')
 assert len(set(e['x'] for e in xs))==4, xs
 line=page.locator('[data-level=line]').first
 line.locator('.group-name').click()
 expect(line.locator('.group-name')).to_have_attribute('aria-expanded','false')
 count=page.locator('[data-level=product]').count();assert count<18
 category=page.locator('[data-level=category]').first.locator('.group-name')
 category.click();expect(page.locator('[data-level=line]')).to_have_count(10)
 category.click();expect(page.locator('[data-level=line]')).to_have_count(13)
 expect(page.locator('[data-level=line]').first.locator('.group-name')).to_have_attribute('aria-expanded','false')
 page.get_by_role('button',name='Thu/mở dự án',exact=True).click()
 expect(page.locator('[data-level]')).to_have_count(0)
 page.get_by_role('button',name='Thu/mở dự án',exact=True).click()
 expect(page.locator('[data-level=category]')).to_have_count(4)
 page.locator('[data-level=line]').first.locator('.group-name').click()
 expect(page.locator('[data-level=product]')).to_have_count(18)
 page.locator('.item-open').first.click()
 expect(page.locator('.read-only-detail')).to_be_visible()
 expect(page.locator('.read-only-detail .status')).to_have_count(1)
 page.keyboard.press('Escape')
 page.get_by_role('tab',name=item_label,exact=True).click()
 expect(page.locator('.table-group')).to_have_count(13)
 expect(page.locator('.table-name')).to_have_count(18)
 assert 'Cà phê / Cà phê hạt' in page.locator('.table-group-head').first.inner_text()
 page.get_by_role('tab',name=gallery_label,exact=True).click()
 expect(page.locator('.showcase')).to_be_visible()
 page.get_by_role('tab',name=report_label,exact=True).click()
 expect(page.locator('.report-slide')).to_have_count(16)
 assert 'Cà phê / Cà phê hạt' in page.locator('.contents-list').inner_text()
 page.get_by_role('tab',name='Sơ đồ',exact=True).click()
 page.get_by_role('button',name='Vừa màn hình',exact=True).click()
 page.screenshot(path='/tmp/farm-'+('live' if BASE.startswith('https:') else 'stage')+'-map.png')
 page.set_viewport_size({'width':390,'height':844})
 page.get_by_role('button',name='Vừa màn hình',exact=True).click()
 expect(page.locator('[data-level=category]')).to_have_count(4)
 page.screenshot(path='/tmp/farm-'+('live' if BASE.startswith('https:') else 'stage')+'-mobile.png')
 print('PUBLIC PASS: HTTP200, 4 columns, 4/13/18 nodes, independent root/category/line collapse, leaf detail, table/showcase/report, desktop/mobile')
 if BASE=='http://127.0.0.1:8795':
  secret=Path('/tmp/farm-stage-dist/server/.dev.vars').read_text().strip().split('=',1)[1]
  nonce=str(uuid.uuid4());exp=int(time.time())+3600
  payload=base64.urlsafe_b64encode(json.dumps(dict(sub='admin',exp=exp,nonce=nonce)).encode()).decode().rstrip('=')
  token=payload+'.'+hmac.new(secret.encode(),payload.encode(),hashlib.sha256).hexdigest()
  db=sqlite3.connect('/tmp/farm-stage-state/v3/d1/miniflare-D1DatabaseObject/faaf2b0445ab934c3aac48ddf0cdfade8f9bac050be98993748742cdd2cb05fb.sqlite')
  db.execute('INSERT INTO admin_sessions(id,expires_at) VALUES(?,?)',(nonce,exp));db.commit()
  headers={'Cookie':'__Host-design-admin='+token}
  # Server auth via headers is kept solely on loopback staging.
  page.context.set_extra_http_headers(headers)
  page.set_viewport_size({'width':1600,'height':1000})
  page.goto(BASE+'/admin')
  page.get_by_role('button',name='Chọn hoặc quản lý dự án:',exact=False).click()
  page.get_by_role('menuitem',name='Khe Sanh Farm',exact=True).click()
  expect(page.locator('[data-level=category]')).to_have_count(4)
  page.get_by_role('button',name='Đổi tên danh mục Cà phê',exact=True).click()
  page.get_by_role('dialog').get_by_label('Tên',exact=True).fill('Cà phê kiểm thử')
  with page.expect_response(lambda r:'/api/workspace' in r.url and r.request.method=='PUT') as saved:
   page.get_by_role('dialog').get_by_role('button',name='Lưu',exact=True).click()
  assert saved.value.status==200
  page.reload()
  page.get_by_role('button',name='Chọn hoặc quản lý dự án:',exact=False).click()
  page.get_by_role('menuitem',name='Khe Sanh Farm',exact=True).click()
  expect(page.locator('[data-level=category]').first).to_contain_text('Cà phê kiểm thử')
  page.get_by_role('button',name='Thêm dòng vào Cà phê kiểm thử',exact=True).click()
  dlg=page.get_by_role('dialog');expect(dlg.locator('input[list=category-options]')).to_have_value('Cà phê kiểm thử')
  dlg.get_by_label('Tên',exact=True).fill('Dòng kiểm thử')
  with page.expect_response(lambda r:'/api/workspace' in r.url and r.request.method=='PUT') as saved:
   dlg.get_by_role('button',name='Lưu',exact=True).click()
  assert saved.value.status==200
  expect(page.locator('[data-level=line]')).to_have_count(14)
  # Trusted pointer drag between two product lines in different categories.
  page.get_by_role('button',name='Vừa màn hình',exact=True).click()
  source=page.locator('[data-level=line]').first
  target=page.locator('[data-level=line]').filter(has_text='Trà hoà tan').first
  source_id=json.loads(source.get_attribute('data-drop'))['id']
  a=source.locator('.grip').bounding_box();b=target.locator('.group-name').bounding_box()
  page.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);page.mouse.down()
  page.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2,steps=12)
  with page.expect_response(lambda r:'/api/workspace' in r.url and r.request.method=='PUT') as moved:
   page.mouse.up()
  assert moved.value.status==200
  result=page.request.get(BASE+'/api/workspace',headers=headers).json()
  assert next(g for p in result['data']['projects'] if p['id']==PID for g in p['groups'] if g['id']==source_id)['category']=='Trà'
  original=json.loads(Path('/tmp/farm-stage-migration-backup/main-before.json').read_text())
  farm=next(p for p in result['data']['projects'] if p['id']==PID)
  old=next(p for p in original['projects'] if p['id']==PID)
  assert {g['id']:g['items'] for g in farm['groups'] if g['id'] in {x['id'] for x in old['groups']}}=={g['id']:g['items'] for g in old['groups']}
  assert [p for p in result['data']['projects'] if p['id']!=PID]==[p for p in original['projects'] if p['id']!=PID]
  # Persistence validator and optimistic concurrency, real HTTP not mocks.
  invalid=json.loads(json.dumps(result));next(p for p in invalid['data']['projects'] if p['id']==PID)['groups'][0]['category']={'bad':True}
  assert page.request.put(BASE+'/api/workspace',headers=headers,data=invalid).status==400
  stale=dict(result,revision=result['revision']-1)
  assert page.request.put(BASE+'/api/workspace',headers=headers,data=stale).status==409
  page.get_by_role('button',name='Chọn hoặc quản lý dự án:',exact=False).click()
  legacy=next(p for p in result['data']['projects'] if p['id']!=PID and '100' in p['name'])
  page.get_by_role('menuitem',name=legacy['name'],exact=True).click()
  expect(page.locator('[data-level=category]')).to_have_count(0)
  expect(page.locator('[data-level=line]')).to_have_count(len(legacy['groups']))
  expect(page.locator('[data-level=product]')).to_have_count(sum(len(g['items']) for g in legacy['groups']))
  print('ADMIN STAGE PASS: category rename + line creation persisted/reloaded, category validation400, stale revision409, all original leaves/other projects preserved, legacy map unchanged')
 assert errors==[],errors
 browser.close()
