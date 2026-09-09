"""Explicit, revision-guarded one-project migration. Never rewrites items or other rows.
Usage: python scripts/migrate-farm-categories.py DB BACKUP_DIR EXPECTED_REVISION
"""
import copy
import json
import sqlite3
import sys
from pathlib import Path

PROJECT = '3cc585ac-3cdb-4b70-9e71-cc8369b66499'

def migrate(db, backup_dir, expected):
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=False)
    c = sqlite3.connect(db, timeout=20)
    with sqlite3.connect(backup_dir / 'workspace.sqlite') as backup:
        c.backup(backup)
        assert backup.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    c.execute('BEGIN IMMEDIATE')
    payload, revision = c.execute("SELECT payload,revision FROM workspace WHERE id='main'").fetchone()
    if revision != expected:
        c.rollback()
        raise RuntimeError(f'Revision changed: expected {expected}, actual {revision}; no mutation')
    before = json.loads(payload)
    after = copy.deepcopy(before)
    p = next(p for p in after['projects'] if p['id'] == PROJECT)
    assert len(p['groups']) == 13 and sum(len(g['items']) for g in p['groups']) == 18
    for g in p['groups']:
        assert 'category' not in g and ' · ' in g['name'], 'Already migrated or unexpected group'
        category, line = g['name'].split(' · ', 1)
        assert category in ['Cà phê', 'Trà', 'Dược liệu', 'Thực phẩm'] and line.strip()
        g['category'], g['name'] = category, line
    assert len({g['category'] for g in p['groups']}) == 4
    old = next(p for p in before['projects'] if p['id'] == PROJECT)
    assert [g['items'] for g in old['groups']] == [g['items'] for g in p['groups']]
    assert [g['id'] for g in old['groups']] == [g['id'] for g in p['groups']]
    assert [p for p in before['projects'] if p['id'] != PROJECT] == [p for p in after['projects'] if p['id'] != PROJECT]
    (backup_dir / 'main-before.json').write_text(payload)
    result = c.execute("UPDATE workspace SET payload=?,revision=revision+1 WHERE id='main' AND revision=?", (json.dumps(after, ensure_ascii=False, separators=(',', ':')), expected))
    assert result.rowcount == 1
    c.commit()
    assert json.loads(c.execute("SELECT payload FROM workspace WHERE id='main'").fetchone()[0]) == after
    print(json.dumps({'revision_before': revision, 'revision_after': revision+1, 'categories': 4, 'lines': 13, 'products': 18, 'items_ids_attachments_unchanged': True, 'other_projects_unchanged': True, 'backup': str(backup_dir)}, ensure_ascii=False))

if __name__ == '__main__':
    migrate(sys.argv[1], sys.argv[2], int(sys.argv[3]))
