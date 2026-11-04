import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nexus_backup import backup_database

class BackupTests(unittest.TestCase):
    def test_makes_consistent_backup(self):
        with tempfile.TemporaryDirectory() as t:
            db=Path(t)/'live.sqlite'; out=Path(t)/'nested'/'snapshot.sqlite'
            with sqlite3.connect(db) as c: c.execute('create table t(x)'); c.execute('insert into t values(7)')
            backup_database(db,out)
            with sqlite3.connect(out) as c: self.assertEqual(c.execute('select x from t').fetchone(),(7,))
    def test_refuses_same_destination(self):
        with tempfile.TemporaryDirectory() as t:
            db=Path(t)/'live.sqlite'; sqlite3.connect(db).close()
            with self.assertRaises(ValueError): backup_database(db,db)
    def test_requires_existing_source(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileNotFoundError): backup_database(Path(t)/'missing',Path(t)/'out')
if __name__=='__main__': unittest.main()
