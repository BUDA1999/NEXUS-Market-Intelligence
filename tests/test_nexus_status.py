import os
import sqlite3
import tempfile
import unittest
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch
from nexus_status import inspect_status, format_status
from nexus_termux import Nexus, run_menu

class StatusTests(unittest.TestCase):
    def test_offline_and_no_secrets(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'DEEPSEEK_API_KEY':'private-fake-key'},clear=True):
            s=inspect_status(Path(d)/'missing.sqlite')
            text=format_status(s)
        self.assertNotIn('private-fake-key',text)
        self.assertIn('não integrado',text)
        self.assertIn('não verificada',text)
        self.assertFalse(s['database_exists'])
    def test_database_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'paper.sqlite'
            with closing(sqlite3.connect(db)) as c:
                c.execute('CREATE TABLE sentinel (v TEXT)'); c.execute("INSERT INTO sentinel VALUES ('unchanged')"); c.commit()
            result=inspect_status(db)
            with closing(sqlite3.connect(db)) as c: value=c.execute('SELECT v FROM sentinel').fetchone()[0]
            self.assertEqual(result['database_integrity'],'ok'); self.assertEqual(value,'unchanged')
    def test_menu_a_reports_real_status(self):
        with tempfile.TemporaryDirectory() as d:
            n=Nexus(Path(d)/'paper.sqlite')
            try:
                out=StringIO()
                with patch('builtins.input',side_effect=['a','','0']), redirect_stdout(out): run_menu(n)
                self.assertIn('ESTADO LOCAL',out.getvalue())
                self.assertIn('não integrado ao painel',out.getvalue())
                self.assertIn('Ordens reais: desativadas',out.getvalue())
            finally: n.close()
    def test_module_absence_is_safe(self):
        with patch('nexus_status.importlib.util.find_spec',side_effect=ModuleNotFoundError):
            s=inspect_status('/nonexistent/nexus.sqlite')
        self.assertFalse(any(s['engine_modules'].values()))

if __name__=='__main__': unittest.main()
