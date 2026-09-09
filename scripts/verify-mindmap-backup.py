#!/usr/bin/env python3
"""Non-destructive isolated restore exercise for a quiesced runtime snapshot.

Copies all state into a private temporary directory, verifies byte identity,
then opens copied SQLite databases and validates integrity/workspace JSON.
Never opens production databases or changes a source snapshot.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import sqlite3
import tempfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_restore(snapshot):
    state = pathlib.Path(snapshot) / 'state'
    if not state.is_dir():
        raise ValueError('Snapshot has no state directory')
    files = sorted(p for p in state.rglob('*') if p.is_file())
    if any(p.is_symlink() for p in state.rglob('*')):
        raise ValueError('Symlinks in backup state are not allowed')
    if not list(state.rglob('*.sqlite')):
        raise ValueError('Snapshot has no SQLite databases')
    report = {'files': len(files), 'databases': 0, 'workspace_revisions': {}}
    with tempfile.TemporaryDirectory(prefix='mindmap-restore-') as tmp:
        restored = pathlib.Path(tmp) / 'state'
        shutil.copytree(state, restored)
        for original in files:
            if digest(original) != digest(restored / original.relative_to(state)):
                raise ValueError('Restored file checksum mismatch')
        for db in restored.rglob('*.sqlite'):
            with sqlite3.connect(db) as conn:
                if conn.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise ValueError('Restored SQLite integrity check failed')
                report['databases'] += 1
                if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='workspace'").fetchone():
                    for key, payload, revision in conn.execute('SELECT id,payload,revision FROM workspace'):
                        json.loads(payload)
                        report['workspace_revisions'][key] = revision
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(verify_restore(args.snapshot), sort_keys=True))
