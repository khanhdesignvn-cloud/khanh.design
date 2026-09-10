import importlib.util,json,sqlite3,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('migration',Path(__file__).parents[1]/'scripts/set-project-presentations.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class PresentationMigration(unittest.TestCase):
 def test_preserves_all_content_and_backup_and_refuses_stale_revision(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'db.sqlite';backup=Path(d)/'backup.sqlite'
   original={'projects':[{'id':'farm','name':'Farm','groups':[{'id':'g','category':'Category','items':[{'id':'i','files':[{'name':'private.png'}]}]}],'shareToken':'keep'},{'id':'other','name':'Other','groups':[]}]}
   with sqlite3.connect(db) as c:c.execute('CREATE TABLE workspace(id TEXT,payload TEXT,revision INT)');c.execute('INSERT INTO workspace VALUES(?,?,?)',('main',json.dumps(original),4))
   self.assertEqual(mod.migrate(db,backup,4,{'farm':'catalog'}),5)
   with sqlite3.connect(backup) as c:self.assertEqual(json.loads(c.execute('SELECT payload FROM workspace').fetchone()[0]),original)
   with sqlite3.connect(db) as c:changed=json.loads(c.execute('SELECT payload FROM workspace').fetchone()[0])
   self.assertEqual(changed['projects'][0].pop('presentation'),'catalog');self.assertTrue(changed['projects'][0].pop('updatedAt'));self.assertEqual(changed,original)
   with self.assertRaises(ValueError):mod.migrate(db,Path(d)/'stale.sqlite',4,{'farm':'design'})
