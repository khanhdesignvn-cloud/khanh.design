import test from 'node:test';
import assert from 'node:assert/strict';
import ts from 'typescript';
import fs from 'node:fs';
const source=fs.readFileSync(new URL('../app/model.ts',import.meta.url),'utf8').replace("import khesanhProject from './data/khesanh-project.json';",'const khesanhProject={};');
const model=await import('data:text/javascript;base64,'+Buffer.from(ts.transpile(source,{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022})).toString('base64'));
const groups=[{id:'a',name:'Hạt',category:'Cà phê',items:[{id:'i',files:[{id:'file'}]}]},{id:'b',name:'Lá',category:'Trà',items:[]},{id:'c',name:'Bột',category:'Cà phê',items:[]}];
test('category layout creates true parents and independent collapse without changing leaves',()=>{
 const before=structuredClone(groups);const l=model.layoutHierarchy(groups,[]);
 assert.equal(l.categories.length,2);assert.equal(l.placed.length,3);
 const c=model.layoutHierarchy(groups,['category:Cà phê']);assert.deepEqual(c.placed.map(g=>g.id),['b']);
 const line=model.layoutHierarchy(groups,['a']);assert.equal(line.placed.find(g=>g.id==='a').hidden,true);assert.equal(line.placed.find(g=>g.id==='c').hidden,false);
 assert.equal(model.layoutHierarchy(groups,['root']).placed.length,0);assert.deepEqual(groups,before);
 assert.equal(model.layoutHierarchy([{id:'legacy',name:'Legacy',items:[]}],[]).categories.length,0);
});
test('moving a line across categories reparents it and preserves attachments',()=>{
 const d={projects:[{id:'p',groups}]};const next=model.moveNode(d,'p',{kind:'group',id:'a'},{kind:'group',id:'b'});
 assert.equal(next.projects[0].groups.find(g=>g.id==='a').category,'Trà');assert.deepEqual(next.projects[0].groups.find(g=>g.id==='a').items,groups[0].items);assert.equal(groups[0].category,'Cà phê');
});
