// Run against a live build; no authentication or persisted uploads required.
import assert from 'node:assert/strict';
const base=process.env.TEST_BASE_URL||'http://127.0.0.1:8794';
for (const mb of [0.5,2,30,50]) {
 const form=new FormData();
 form.append('file',new Blob([new Uint8Array(mb*1024*1024)],{type:'image/png'}),'limit-probe.png');
 const r=await fetch(base+'/api/upload',{method:'POST',body:form,headers:{Origin:new URL(base).origin}});
 const text=await r.text();
 assert.equal(r.status,403,`${mb} MiB must reach auth, got ${r.status}: ${text}`);
 assert.match(r.headers.get('content-type')||'',/application\/json/);
 console.log(`PASS ${mb} MiB reaches upload authorization (JSON 403)`);
}
