import test from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import fs from 'node:fs';
const source=fs.readFileSync(new URL('../app/model.ts',import.meta.url),'utf8').replace("import khesanhProject from './data/khesanh-project.json';",'const khesanhProject={};');
const modelUrl='data:text/javascript;base64,'+Buffer.from(ts.transpile(source,{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022})).toString('base64');
const model=await import(modelUrl);
const routeSource=fs.readFileSync(new URL('../app/api/project/[token]/route.ts',import.meta.url),'utf8')
 .replace("import {env} from 'cloudflare:workers';",'const env=globalThis.__projectionTestEnv;')
 .replace("from '../../../model'",`from '${modelUrl}'`);
let workspace={projects:[{id:'p',name:'Farm',subtitle:'',shareToken:'valid-token',internalNote:'secret',groups:[]}]};
globalThis.__projectionTestEnv={DB:{prepare(){return {bind(){return {async first(){return {payload:JSON.stringify(workspace),revision:9}}}}}}}};
const route=await import('data:text/javascript;base64,'+Buffer.from(ts.transpile(routeSource,{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022})).toString('base64'));
test('public endpoint applies projection, disables caching and rejects revoked tokens',async()=>{
 const get=token=>route.GET(new Request('https://example.test/api/project/'+token),{params:Promise.resolve({token})});
 const response=await get('valid-token'),body=await response.json();
 assert.equal(response.status,200);
 assert.equal(body.data.internalNote,undefined);
 assert.equal(body.data.shareToken,undefined);
 assert.equal(response.headers.get('cache-control'),'private, no-store');
 workspace.projects[0].shareToken='replacement-token';
 assert.equal((await get('valid-token')).status,404);
 assert.equal((await get('bad')).status,404);
});
test('public projection excludes undeclared internal fields at every level without changing stored data',()=>{
 assert.equal(typeof model.publicProject,'function','public allowlist projection is missing');
 const item={id:'i',name:'Product',status:'Hoàn thành',note:'Public design note',images:['/api/image/abc'],files:[{id:'a',name:'stored-original.png',url:'/api/image/abc',type:'image',internalNote:'secret'}],internalNote:'secret',audit:[{actor:'owner'}]};
 const project={id:'p',name:'Farm',subtitle:'Brand',shareToken:'secret-token',internalNote:'secret',history:[{}],members:[{}],groups:[{id:'g',name:'Line',category:'Category',internalNote:'secret',items:[item]}]};
 const before=structuredClone(project), safe=model.publicProject(project);
 assert.deepEqual(safe,{id:'p',name:'Farm',subtitle:'Brand',groups:[{id:'g',name:'Line',category:'Category',items:[{id:'i',name:'Product',status:'Hoàn thành',note:'Public design note',images:['/api/image/abc'],files:[{id:'a',name:'stored-original.png',url:'/api/image/abc',type:'image'}]}]}]});
 assert.deepEqual(project,before);
 safe.groups[0].items[0].images.push('new');
 assert.deepEqual(project,before);
});
