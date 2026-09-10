import test from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import fs from 'node:fs';
const url=s=>'data:text/javascript;base64,'+Buffer.from(ts.transpile(s,{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022})).toString('base64');
const model=url(fs.readFileSync(new URL('../app/model.ts',import.meta.url),'utf8').replace("import khesanhProject from './data/khesanh-project.json';",'const khesanhProject={};'));
let data={projects:[{id:'p',name:'Project',subtitle:'Summary',groups:[]}]},revision=5,denied=false;
globalThis.__phase1Env={DB:{prepare(sql){
 return {bind(...args){
  return {
   async first(){return {payload:JSON.stringify(data),revision}},
   async run(){
    if(sql.startsWith('UPDATE')){
     if(args[2]!==revision)return {meta:{changes:0}};
     data=JSON.parse(args[0]);revision++;
    }
    return {meta:{changes:1}};
   }
  };
 }};
}}};
globalThis.__phase1Denied=()=>denied;
const source=fs.readFileSync(new URL('../app/api/workspace/route.ts',import.meta.url),'utf8').replace("import {authorizeWrite,adminSession} from '../../admin';","const authorizeWrite=async()=>globalThis.__phase1Denied()?new Response('Forbidden',{status:403}):null;const adminSession=async()=>({isAdmin:true});").replace("import {env} from 'cloudflare:workers';","const env=globalThis.__phase1Env;").replace("from '../../model'",`from '${model}'`);
const {PUT}=await import(url(source));
const put=(payload,rev=revision)=>PUT(new Request('https://example.test/api/workspace',{method:'PUT',body:JSON.stringify({data:payload,revision:rev})}));
test('workspace API persists all presentation types, stamps updates, denies invalid/stale/unauthorized writes',async()=>{
 for(const kind of ['design','course','catalog']){const next=structuredClone(data);next.projects[0].presentation=kind;const r=await put(next);assert.equal(r.status,200);assert.equal(data.projects[0].presentation,kind);assert.ok((await r.json()).updatedAt.p);}
 const prior=structuredClone(data);const bad=structuredClone(data);bad.projects[0].presentation='unknown';
 const original=console.error;console.error=()=>{};try{assert.equal((await put(bad)).status,400)}finally{console.error=original}
 assert.deepEqual(data,prior);assert.equal((await put(prior,revision-1)).status,409);
 denied=true;assert.equal((await put(prior)).status,403);assert.deepEqual(data,prior);
});
