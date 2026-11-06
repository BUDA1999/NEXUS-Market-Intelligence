import tempfile
import unittest
from contextlib import closing
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import sqlite3
from nexus_termux import Nexus
from nexus_ui import render_dashboard, render_header, render_menu, terminal_width

class UiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.n=Nexus(Path(self.tmp.name)/'n.sqlite')
    def tearDown(self): self.n.close(); self.tmp.cleanup()
    def test_header_stays_inside_45_columns_and_keeps_brand(self):
        out=StringIO(); render_header(out,width=40)
        lines=out.getvalue().splitlines()
        self.assertTrue(all(len(line)<=40 for line in lines))
        self.assertIn('JD NEXUS',out.getvalue()); self.assertIn('PISCES EDITION',out.getvalue())
        self.assertIn('THINK BEYOND THE MARKET',out.getvalue()); self.assertIn('><(((°>',out.getvalue())
    def test_dashboard_narrow_has_no_horizontal_overflow_or_fake_data(self):
        out=StringIO(); render_dashboard(self.n,{},out,width=42)
        text=out.getvalue()
        self.assertTrue(all(len(line)<=42 for line in text.splitlines()))
        self.assertIn('EUR/USD: UNAVAILABLE',text); self.assertIn('XAU/USD: UNAVAILABLE',text)
        self.assertIn('no live',text); self.assertIn('all DISABLED',text)
        self.assertNotIn('AI: CONNECTED',text); self.assertIn('PAPER ONLY',text)
    def test_invalid_quote_timestamp_is_reported_without_crash(self):
        with self.n.db:
            self.n.db.execute("INSERT INTO quotes VALUES(?,?,?,?,?)",("EUR/USD","1.1","1.2","manual","bad-time"))
        out=StringIO(); render_dashboard(self.n,{},out,width=45)
        self.assertIn("ERROR — invalid timestamp",out.getvalue())
    def test_quotes_show_manual_vs_stale_and_no_fake_variation(self):
        self.n.update_quote('EUR/USD','1.1','1.1002')
        out=StringIO(); render_dashboard(self.n,{},out,width=45)
        text=out.getvalue()
        self.assertIn('MANUAL',text); self.assertIn('change / direction: unavailable',text)
    def test_agents_are_idle_disabled_not_fake_running(self):
        out=StringIO(); render_dashboard(self.n,{},out,width=45); text=out.getvalue()
        for agent in ('Fundamental Analyst','Sentiment Analyst','News Analyst','Market Analyst',
                      'Bull Researcher','Bear Researcher','Research Manager','Trader Agent',
                      'Risk Manager','Portfolio Manager'):
            self.assertIn(agent,text)
        self.assertNotIn('RUNNING',text); self.assertNotIn('COMPLETED',text)
    def test_menu_shows_only_existing_functions_and_wraps(self):
        out=StringIO(); render_menu(out,width=40); text=out.getvalue()
        self.assertTrue(all(len(line)<=40 for line in text.splitlines()))
        for item in ('1 Cotação manual','2 Abrir posição (paper)','5 Fechar posição (paper)',
                     'a Diagnóstico local','0 Sair'):
            self.assertIn(item,text)
        for pending in ('Run AI Analysis','New BUY Order','New SELL Order','Broker API'):
            self.assertNotIn(pending,text)
        selected=StringIO(); render_menu(selected,width=40,selected='4')
        self.assertIn('> 4 Histórico',selected.getvalue())
    def test_terminal_width_falls_back_to_40(self):
        class Broken:
            def fileno(self): raise OSError
        with patch('nexus_ui.shutil.get_terminal_size',side_effect=OSError):
            self.assertEqual(terminal_width(Broken()),40)
    def test_very_narrow_terminal_is_still_clamped_and_wrapped(self):
        out=StringIO(); render_dashboard(self.n,{},out,width=24); render_menu(out,width=24)
        self.assertTrue(all(len(line)<=24 for line in out.getvalue().splitlines()))

if __name__=='__main__': unittest.main()
