import tempfile
import unittest
from contextlib import closing, redirect_stdout
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

    def test_show_has_compact_identity_status_and_existing_menu(self):
        output=StringIO()
        with redirect_stdout(output): show(self.n)
        text=output.getvalue()
        for required in ('JD NEXUS','PISCES EDITION','THINK BEYOND THE MARKET',
                         'STATUS: PAPER LOCAL','MERCADO','CONTA PAPER',
                         'AGENTES IA','MANUAIS','IA: NÃO LIGADA','BROKER: NÃO',
                         '[1] Cotação manual','[2] Nova posição PAPER','[4] Histórico'):
            self.assertIn(required,text)
        self.assertEqual(len(self.n.positions()),0)
        self.assertEqual(len(self.n.quotes()),1)


    def test_summary_and_detail_are_read_only(self):
        p=self.n.open_position('EUR/USD','BUY','1.09','1.12')
        before=self.n.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        summary=self.n.summary(); detail=self.n.position_detail(p['id'])
        after=self.n.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        self.assertEqual(summary['open_count'],1)
        self.assertEqual(detail['row']['status'],'OPEN')
        self.assertEqual(before,after)

    def test_risk_config_validates_all_before_mutating(self):
        with self.assertRaises(ValueError): self.n.set_risk(max_risk='0.005',max_daily_loss='0.5')
        self.assertEqual(self.n.max_risk,D('0.01'))
        self.assertEqual(self.n.max_daily_loss,D('0.03'))
        changed=self.n.set_risk(max_risk='0.005',max_daily_loss='0.04',max_exposure='1.5')
        self.assertEqual(changed['max_risk'],D('0.005'))
        self.n.close(); self.n=Nexus(Path(self.tmp.name)/'test.db',D('10000'))
        self.assertEqual(self.n.max_risk,D('0.005'))
        self.assertEqual(self.n.max_daily_loss,D('0.04'))

    def test_export_history_csv_and_report(self):
        self.n.open_position('EUR/USD','BUY','1.09','1.12')
        csv_path,txt_path=self.n.export_history(Path(self.tmp.name)/'reports')
        self.assertIn('EUR/USD',csv_path.read_text())
        self.assertIn('SIMULAÇÃO',txt_path.read_text())

    def test_backup_restore_creates_safety_copy_and_recovers_settings(self):
        self.n.set_risk(max_risk='0.005')
        self.n.open_position('EUR/USD','BUY','1.09','1.12')
        backup=self.n.backup_database(Path(self.tmp.name)/'backups')
        self.n.close(); Path(self.tmp.name,'test.db').unlink()
        # Recreate a different active DB to validate restoring into an existing state.
        self.n=Nexus(Path(self.tmp.name)/'test.db',D('2000'))
        safety=self.n.restore_database(backup,Path(self.tmp.name)/'safety')
        self.assertTrue(safety.is_file())
        self.assertEqual(self.n.initial_capital,D('10000'))
        self.assertEqual(self.n.max_risk,D('0.005'))
        self.assertEqual(len(self.n.positions('OPEN')),1)

    def test_restore_refuses_active_db_and_invalid_file(self):
        with self.assertRaises(ValueError): self.n.restore_database(self.n.path)
        bad=Path(self.tmp.name)/'bad.sqlite3'; bad.write_text('not sqlite')
        with self.assertRaises(Exception): self.n.restore_database(bad)


    def test_original_menu_numbers_stay_in_place(self):
        from nexus_termux import show
        out=StringIO()
        with redirect_stdout(out): show(self.n)
        text=out.getvalue()
        self.assertIn("[1] Cotação manual",text)
        self.assertIn("[2] Nova posição PAPER",text)
        self.assertIn("[3] Posições abertas",text)
        self.assertIn("[4] Histórico",text)
        self.assertIn("[5] Fechar posição PAPER",text)
        self.assertIn("[0] Sair",text)
        self.assertIn("[6] Resumo da conta",text)

    def test_menu_workflows_summary_help_export_backup_restore(self):
        self.n.open_position('EUR/USD','BUY','1.09','1.12')
        output=StringIO()
        inputs=['6','','7','1','','8','','','','','9','','b','','r','1','CANCELAR','','h','','0']
        with patch('builtins.input',side_effect=inputs), redirect_stdout(output): run_menu(self.n)
        text=output.getvalue()
        for value in ('RESUMO DA CONTA','Risco estimado até SL','Sem alterações.',
                      'Exportados:','Cópia criada:','Restauro cancelado.','JD NEXUS'):
            self.assertIn(value,text)
        self.assertEqual(len(self.n.positions('OPEN')),1)

    def test_corrupt_risk_settings_fails_closed_and_restore_rejects(self):
        backup=self.n.backup_database(Path(self.tmp.name)/'backups')
        import sqlite3
        with closing(sqlite3.connect(backup)) as db:
            with db: db.execute("INSERT INTO settings(key,value) VALUES('max_risk','0.50')")
        before=self.n.initial_capital
        with self.assertRaises(ValueError): self.n.restore_database(backup,Path(self.tmp.name)/'safety')
        self.assertEqual(self.n.initial_capital,before)
        self.assertEqual(len(self.n.quotes()),1)

    def test_restore_creates_new_recovery_copy(self):
        backup=self.n.backup_database(Path(self.tmp.name)/'backups')
        self.n.open_position('EUR/USD','BUY','1.09','1.12')
        safety=self.n.restore_database(backup,Path(self.tmp.name)/'safety')
        self.assertEqual(len(self.n.positions('OPEN')),0)
        import sqlite3
        with closing(sqlite3.connect(safety)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM positions WHERE status='OPEN'").fetchone()[0],1)

    def test_buy_sizes_and_persists(self):
        p=self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.assertEqual(p['mode'],'PAPER_ONLY')
        self.assertLessEqual(D(p['risk_at_stop']),D('100'))
        self.assertEqual(len(self.n.positions('OPEN')),1)
    def test_persistent_kill_switch_blocks_new_entries_after_restart(self):
        self.n.set_kill_switch(True, "test")
        self.assertTrue(self.n.summary()["manual_halt"])
        self.assertEqual(self.n.db.execute("SELECT value FROM settings WHERE key='paper_halted'").fetchone()[0], "1")
        self.n.close(); self.n=Nexus(Path(self.tmp.name)/'test.db',D('10000'))
        with self.assertRaisesRegex(ValueError, "kill switch Paper persistente"):
            self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.n.set_kill_switch(False, "explicit-resume")
        self.assertFalse(self.n.manual_halt())
        self.assertEqual(self.n.open_position('EUR/USD','BUY','1.09','1.12')['mode'], 'PAPER_ONLY')

    def test_invalid_kill_switch_state_fails_closed(self):
        with self.n.db:
            self.n.db.execute("INSERT INTO settings(key,value) VALUES('paper_halted','maybe')")
        with self.assertRaisesRegex(ValueError, "estado do kill switch inválido"):
            self.n.open_position('EUR/USD','BUY','1.09','1.12')

    def test_kill_switch_does_not_prevent_managing_existing_positions(self):
        pos=self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.n.set_kill_switch(True)
        self.assertEqual(self.n.close_position(pos['id'])['reason'], 'MANUAL_SIMULATED')

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

    def test_corrupt_stored_quote_fails_closed_before_open(self):
        self.n.db.execute("UPDATE quotes SET ask='NaN' WHERE symbol='EUR/USD'")
        self.n.db.commit()
        with self.assertRaisesRegex(ValueError, "cotação guardada inválida"):
            self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.assertEqual(self.n.positions('OPEN'), [])

    def test_stored_quote_with_invalid_timestamp_fails_closed(self):
        self.n.db.execute("UPDATE quotes SET updated_at='SECRET-NOT-A-TIMESTAMP' WHERE symbol='EUR/USD'")
        self.n.db.commit()
        with self.assertRaisesRegex(ValueError, "cotação guardada inválida") as ctx:
            self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.assertNotIn('SECRET', str(ctx.exception))
        self.assertEqual(self.n.positions('OPEN'), [])

    def test_stored_quote_wrong_source_fails_closed(self):
        self.n.db.execute("UPDATE quotes SET source=' ' WHERE symbol='EUR/USD'")
        self.n.db.commit()
        with self.assertRaisesRegex(ValueError, "cotação guardada inválida"):
            self.n.open_position('EUR/USD','BUY','1.09','1.12')
        self.assertEqual(self.n.positions('OPEN'), [])

if __name__=='__main__': unittest.main()
