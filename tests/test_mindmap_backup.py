import importlib.util
import pathlib
import sqlite3
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'verify-mindmap-backup.py'

class BackupTests(unittest.TestCase):
    def test_daily_job_verifies_before_publishing_and_retains_history(self):
        job = SCRIPT.with_name('backup-khanh-design.sh')
        self.assertTrue(job.exists(), 'safe daily backup job is missing')
        source = job.read_text()
        self.assertIn('flock -n', source)
        self.assertIn('verify-mindmap-backup', source)
        self.assertLess(source.index('verify-mindmap-backup'), source.index('mv "$tmp" "$snapshot"'))
        self.assertNotIn('-mtime +14', source)
        self.assertNotIn('rm -f "$backup_root"', source)
        self.assertIn('No automatic pruning', source)

    def test_snapshot_can_be_restored_and_detects_corrupt_database(self):
        self.assertTrue(SCRIPT.exists(), 'verified isolated restore implementation is missing')
        spec = importlib.util.spec_from_file_location('backup', SCRIPT)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            db = root / 'state' / 'v3' / 'd1' / 'test.sqlite'
            db.parent.mkdir(parents=True)
            with sqlite3.connect(db) as conn:
                conn.execute('CREATE TABLE workspace(id TEXT, payload TEXT, revision INTEGER)')
                conn.execute('INSERT INTO workspace VALUES(?,?,?)', ('main', '{"projects":[]}', 7))
            (root / 'state' / 'blob').write_bytes(b'original artwork')
            report = mod.verify_restore(root)
            self.assertEqual(report['databases'], 1)
            self.assertEqual(report['workspace_revisions'], {'main': 7})
            self.assertEqual(report['files'], 2)
            self.assertEqual(sqlite3.connect(db).execute('SELECT revision FROM workspace').fetchone()[0], 7)
            db.write_bytes(b'not sqlite')
            with self.assertRaises(sqlite3.DatabaseError):
                mod.verify_restore(root)

if __name__ == '__main__':
    unittest.main()
