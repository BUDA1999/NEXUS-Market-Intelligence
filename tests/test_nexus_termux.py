import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from decimal import Decimal as D
from pathlib import Path
from nexus_termux import Nexus, show, run_menu
from unittest.mock import patch

class TermuxPaperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.n=Nexus(Path(self.tmp.name)/'test.db',D('10000'))
        self.n.update_quote('EUR/USD','1.0999','1.1001')
    def tearDown(self): self.n.close(); self.tmp.cleanup()

    def test_show_has_identity_and_keeps_menu_features(self):
        output=StringIO()
        with patch('builtins.input',side_effect=['0']), redirect_stdout(output): run_menu(self.n)
        text=output.getvalue()
        for required in ('JD NEXUS MARKET INTELLIGENCE','♓ PEIXES','STAY LIVE',
                         'COTAÇÕES MANUAIS','1 Atualizar cotação manual',
                         '2 Nova posição simulada','4 Histórico'):
            self.assertIn(required,text)
        self.assertEqual(len(self.n.positions()),0)
        self.assertEqual(len(self.n.quotes()),1)

    def test_buy_sizes_and_persists(self):
        p=self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.assertEqual(p['mode'],'PAPER_ONLY')
        self.assertLessEqual(D(p['risk_at_stop']),D('100'))
        self.assertEqual(len(self.n.positions('OPEN')),1)
    def test_rejects_wrong_direction(self):
        with self.assertRaises(ValueError): self.n.open_position('EUR/USD','BUY','1.11','1.12')
    def test_daily_quote_triggers_stop(self):
        p=self.n.open_position('EUR/USD','BUY','1.09','1.12')
        closed=self.n.update_quote('EUR/USD','1.08','1.0802')
        self.assertEqual(closed[0]['reason'],'STOP_LOSS')
        self.assertEqual(self.n.positions('OPEN'),[])
    def test_take_profit_on_quote_refresh(self):
        self.n.open_position('EUR/USD','BUY','1.09','1.12')
        closed=self.n.update_quote('EUR/USD','1.12','1.1202')
        self.assertEqual(closed[0]['reason'],'TAKE_PROFIT')
    def test_spread_is_reflected_in_exit_pnl(self):
        self.n.open_position('EUR/USD','BUY','1.09','1.12')
        p=self.n.close_position(1)
        self.assertLess(D(p['pnl']),0)
    def test_rejects_no_quote(self):
        with self.assertRaises(ValueError): self.n.open_position('XAU/USD','BUY','2600','2700')
    def test_manual_quote_validation(self):
        with self.assertRaises(ValueError): self.n.update_quote('EUR/USD','1.1','1.09')

if __name__=='__main__': unittest.main()
