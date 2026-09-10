import test from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import fs from 'node:fs';
const source=fs.readFileSync(new URL('../app/model.ts',import.meta.url),'utf8').replace("import khesanhProject from './data/khesanh-project.json';",'const khesanhProject={};');
const model=await import('data:text/javascript;base64,'+Buffer.from(ts.transpile(source,{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022})).toString('base64'));
test('update stamps only changed projects and ignores client supplied timestamps',()=>{
 assert.equal(typeof model.stampProjects,'function');
 const old={projects:[{id:'p',name:'P',subtitle:'',groups:[],updatedAt:'2026-01-01T00:00:00.000Z'}]};
 const unchanged=structuredClone(old);unchanged.projects[0].updatedAt='forged';
 assert.equal(model.stampProjects(unchanged,old,'2026-09-10T00:00:00.000Z').projects[0].updatedAt,old.projects[0].updatedAt);
 unchanged.projects[0].presentation='course';
 assert.equal(model.stampProjects(unchanged,old,'2026-09-10T00:00:00.000Z').projects[0].updatedAt,'2026-09-10T00:00:00.000Z');
});
test('presentation is explicit, backwards compatible, validated and public-safe',()=>{
 assert.equal(typeof model.presentationFor,'function');
 assert.equal(model.presentationFor({name:'Khe Sanh Farm'}).type,'design','never infer from names');
 assert.equal(model.presentationFor({presentation:'course'}).item,'Bài học');
 assert.equal(model.presentationFor({presentation:'catalog'}).item,'Sản phẩm');
 assert.equal(model.validPresentation(undefined),true);
 for(const value of ['design','course','catalog'])assert.equal(model.validPresentation(value),true);
 for(const value of [null,{},'evil'])assert.equal(model.validPresentation(value),false);
 const p={id:'p',name:'P',subtitle:'Summary',presentation:'catalog',updatedAt:'2026-09-10T00:00:00.000Z',internalNote:'SECRET',groups:[]};
 const safe=model.publicProject(p);
 assert.equal(safe.presentation,'catalog');assert.equal(safe.updatedAt,p.updatedAt);assert.equal(safe.internalNote,undefined);
});
