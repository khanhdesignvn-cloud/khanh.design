import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const root = new URL('../', import.meta.url);

test('Khe Sanh checklist contains all 61 documented items in 8 groups', () => {
  const project = JSON.parse(fs.readFileSync(new URL('../app/data/khesanh-project.json', import.meta.url), 'utf8'));
  assert.equal(project.groups.length, 8);
  assert.deepEqual(project.groups.map(group => group.items.length), [8, 7, 11, 8, 9, 7, 5, 6]);
  const items = project.groups.flatMap(group => group.items);
  assert.equal(items.length, 61);
  assert.equal(new Set(items.map(item => item.id)).size, 61);
  assert.equal(items[0].id, 'KS100-01.01');
  assert.equal(items.at(-1).id, 'KS100-08.06');
  for (const item of items) {
    assert.equal(item.status, 'Chưa giao việc');
    assert.match(item.note, /NỘI DUNG MẪU:/);
    assert.match(item.note, /THIẾT KẾ & BÀN GIAO:/);
    assert.match(item.note, /CẦN CHỐT:/);
  }
});

test('new items default to the unassigned status, not active work', () => {
  const model = fs.readFileSync(new URL('../app/model.ts', import.meta.url), 'utf8');
  assert.match(model, /statuses=\['Chưa giao việc','Đang triển khai','Đợi duyệt','Hoàn thành'\]/);
  assert.match(model, /initial:Data=\{projects:\[khesanhProject/);
  const workspace = fs.readFileSync(new URL('../app/workspace.tsx', import.meta.url), 'utf8');
  assert.match(workspace, /status:statuses\[0\]/);
});

test('item codes are computed from position, not baked into names', () => {
  const project = JSON.parse(fs.readFileSync(new URL('../app/data/khesanh-project.json', import.meta.url), 'utf8'));
  for (const group of project.groups) {
    assert.doesNotMatch(group.name, /^\d{2} · /, `group name should be clean: ${group.name}`);
    for (const item of group.items) {
      assert.doesNotMatch(item.name, /^\d{2}\.\d{2} · /, `item name should be clean: ${item.name}`);
    }
  }
  const model = fs.readFileSync(new URL('../app/model.ts', import.meta.url), 'utf8');
  assert.match(model, /export const groupCode=\(i:number\)=>String\(i\+1\)\.padStart\(2,'0'\)/);
  assert.match(model, /export const itemCode=\(gi:number,ii:number\)=>/);
});
