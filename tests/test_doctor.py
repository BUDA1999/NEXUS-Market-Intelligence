import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cli'))
import doctor

class DoctorTests(unittest.TestCase):
    def test_zero_third_party_report_runs(self):
        r=doctor.run('paper')
        self.assertTrue(any(x['name']=='Python' for x in r.items))
        self.assertTrue(any(x['name']=='SQLite' for x in r.items))
    def test_secret_values_never_reported(self):
        secret='do-not-print-this-secret'
        with patch.dict(os.environ,{'DEEPSEEK_API_KEY':secret},clear=True): r=doctor.run('paper')
        self.assertNotIn(secret,str(r.items))
        self.assertTrue(any(x['hint']=='DEEPSEEK_API_KEY' for x in r.items))
    def test_nested_spec_missing_parent_does_not_crash(self):
        with patch.object(doctor.importlib.util,'find_spec',side_effect=ModuleNotFoundError):
            self.assertFalse(doctor.safe_find_spec('langgraph.checkpoint.sqlite'))
    def test_json_cli(self):
        root=Path(__file__).resolve().parents[1]
        result=subprocess.run([sys.executable,'-m','cli.doctor','--json'],cwd=root,capture_output=True,text=True)
        self.assertIn('"name": "Python"',result.stdout)
        self.assertNotIn('do-not-print',result.stdout)
if __name__=='__main__': unittest.main()
