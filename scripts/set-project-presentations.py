"""Explicit metadata-only migration, revision-guarded. Never uses names or seeds."""
import argparse, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path

def migrate(db_path, backup_path, expected_revision, assignments):
    if not assignments or any(v not in ('design','course','catalog') for v in assignments.values()):
        raise ValueError('Invalid explicit presentation assignments')
    db=sqlite3.connect(db_path)
    try:
        Path(backup_path).parent.mkdir(parents=True,exist_ok=True)
        if Path(backup_path).exists(): raise ValueError('Backup already exists')
        with sqlite3.connect(backup_path) as backup:
            db.backup(backup)
            assert backup.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        db.execute('BEGIN IMMEDIATE')
        payload,revision=db.execute("SELECT payload,revision FROM workspace WHERE id='main'").fetchone()
        if revision!=expected_revision: raise ValueError('Workspace revision changed; inspect again')
        data=json.loads(payload)
        projects={p['id']:p for p in data['projects']}
        if not set(assignments)<=projects.keys(): raise ValueError('Project ID not found')
        now=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
        for pid,kind in assignments.items():
            projects[pid]['presentation']=kind
            projects[pid]['updatedAt']=now
        db.execute("UPDATE workspace SET payload=?,revision=revision+1 WHERE id='main' AND revision=?",(json.dumps(data,ensure_ascii=False,separators=(',',':')),revision))
        db.commit()
        return revision+1
    except Exception:
        db.rollback();raise
    finally: db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('db');p.add_argument('backup');p.add_argument('revision',type=int);p.add_argument('assignments',help='JSON object of explicit project IDs to types')
    a=p.parse_args();print('Updated revision:',migrate(a.db,a.backup,a.revision,json.loads(a.assignments)))
