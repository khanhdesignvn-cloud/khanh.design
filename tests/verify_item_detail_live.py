"""Read-only HTTPS smoke: real shared data and artwork, no fixtures or writes."""
import hashlib,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE=os.environ.get('ITEM_LIVE_BASE','https://khanh.design')
TOKEN='dd95800d-dccb-4982-9dc7-b9694ff106be'
OUT=Path('/tmp/item-detail-evidence/live');OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
 browser=pw.chromium.launch(args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':1000},has_touch=True)
 page=context.new_page();errors=[];mutations=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 def readonly(r):
  if r.request.method not in ('GET','HEAD'):
   if r.request.url.startswith(BASE+'/'):mutations.append(r.request.url)
   r.abort()
  else:r.continue_()
 context.route('**/*',readonly)
 data=page.request.get(BASE+'/api/project/'+TOKEN).json()['data']
 group,item=next((g,i) for g in data['groups'] for i in g['items'] if i.get('driveUrl') and len([f for f in i.get('files',[]) if f['type']=='image'])>1)
 files=[f for f in item['files'] if f['type']=='image']
 page.goto(BASE+'/p/'+TOKEN)
 page.get_by_role('tab',name='Sản phẩm',exact=True).click()
 page.locator('.table-name').filter(has_text=item['name']).click()
 link=page.get_by_role('link',name='TẢI FILE GỐC',exact=True)
 expect(link).to_have_attribute('href',item['driveUrl'])
 # Wait until the sheet's entrance transition is finished before evidence.
 page.wait_for_function("document.querySelector('.detail-panel').getBoundingClientRect().right <= innerWidth+1")
 link.hover();page.wait_for_timeout(650)
 hover=link.evaluate('(e)=>({position:getComputedStyle(e).backgroundPosition,transform:getComputedStyle(e).transform})');print('hover',hover)
 assert hover['position'].startswith('100%')
 page.screenshot(path=str(OUT/'drive-desktop.png'))
 with page.expect_popup() as popup:
  link.click()
 popup.value.wait_for_url(lambda u:'drive.google.com' in u or 'docs.google.com' in u)
 popup_url=popup.value.url;popup.value.close()
 trigger=page.locator('.file-tile').filter(has_text=files[1]['name']);trigger.click()
 viewer=page.locator('.showcase-slideshow');stage=viewer.locator('.showcase-slide-stage img')
 expect(viewer.get_by_text(f'2 / {len(files)}',exact=True)).to_be_visible()
 expect(stage).to_have_attribute('src',files[1]['url'])
 page.wait_for_function("document.querySelector('.showcase-slide-stage img').naturalWidth>0")
 expect(viewer.locator('.item-slide-thumbnails button')).to_have_count(len(files))
 viewer.get_by_role('button',name='Phóng to ảnh',exact=True).click()
 expect(viewer.get_by_role('button',name='Đặt lại thu phóng')).to_have_text('125%')
 viewer.get_by_role('button',name='Đặt lại thu phóng').click()
 with page.expect_download() as event:
  viewer.get_by_role('button',name='Tải ảnh hiện tại',exact=True).click()
 d=event.value;assert d.failure() is None
 dest=OUT/d.suggested_filename;d.save_as(str(dest))
 original=page.request.get(BASE+files[1]['url'] if files[1]['url'].startswith('/') else files[1]['url']).body()
 assert dest.read_bytes()==original
 page.screenshot(path=str(OUT/'slideshow-desktop.png'))
 viewer.get_by_role('button',name='Toàn màn hình',exact=True).click();page.wait_for_function('!!document.fullscreenElement')
 viewer.get_by_role('button',name='Thoát toàn màn hình',exact=True).click();page.wait_for_function('!document.fullscreenElement')
 page.keyboard.press('Escape');expect(trigger).to_be_focused()
 page.set_viewport_size({'width':390,'height':844});trigger.click()
 expect(viewer).to_be_visible()
 stagebox=viewer.locator('.showcase-slide-stage').bounding_box();y=stagebox['y']+stagebox['height']/2
 cdp=context.new_cdp_session(page)
 for typ,pts in [('touchStart',[{'x':310,'y':y}]),('touchMove',[{'x':60,'y':y+3}]),('touchEnd',[])]:
  cdp.send('Input.dispatchTouchEvent',{'type':typ,'touchPoints':pts})
 expect(viewer.get_by_text(f'3 / {len(files)}',exact=True)).to_be_visible()
 page.wait_for_function("document.querySelector('.showcase-slide-stage img').naturalWidth>0")
 page.screenshot(path=str(OUT/'slideshow-mobile.png'))
 viewer.get_by_role('button',name='Đóng trình chiếu',exact=True).click()
 expect(page.locator('.detail-panel')).to_be_visible()
 page.locator('.detail-panel').evaluate('(e)=>e.scrollTop=0')
 page.screenshot(path=str(OUT/'detail-mobile.png'))
 assert errors==[],errors;assert mutations==[],mutations
 result={'url':BASE+'/p/'+TOKEN,'item':item['name'],'image_count':len(files),'popup_url':popup_url,'download_filename':d.suggested_filename,'download_bytes':len(original),'sha256':hashlib.sha256(original).hexdigest(),'browser_errors':errors,'mutations':mutations,'desktop_mobile':'PASS'}
 (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
 browser.close()
