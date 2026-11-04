import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from nexus_safety import Quote, RiskCheck, SafetyError

class QuoteTests(unittest.TestCase):
    def test_valid_quote_and_spread(self):
        q=Quote.build('eurusd','1.0800','1.0802',datetime.now(timezone.utc),'manual')
        self.assertEqual(q.symbol,'EURUSD'); self.assertEqual(q.spread,Decimal('0.0002'))
    def test_rejects_inverted_market(self):
        with self.assertRaises(SafetyError): Quote.build('EURUSD','1.2','1.1',datetime.now(timezone.utc),'manual')
    def test_rejects_stale_quote(self):
        q=Quote.build('EURUSD','1.1','1.2',datetime.now(timezone.utc)-timedelta(minutes=5),'manual')
        with self.assertRaises(SafetyError): q.assert_fresh(30)
    def test_rejects_naive_timestamp(self):
        with self.assertRaises(SafetyError): Quote.build('EURUSD','1','1.1',datetime.now(),'manual')
    def test_rejects_nonpositive_quote(self):
        with self.assertRaises(SafetyError): Quote.build('EURUSD','0','1',datetime.now(timezone.utc),'manual')
    def test_rejects_future_quote(self):
        q=Quote.build('EURUSD','1','1.1',datetime.now(timezone.utc)+timedelta(minutes=1),'test')
        with self.assertRaises(SafetyError): q.assert_fresh(60)

class RiskTests(unittest.TestCase):
    def test_risk_inside_limit(self):
        r=RiskCheck.build('100','99','1','1000','1'); r.assert_within_limit()
        self.assertEqual(r.risk_pct,Decimal('0.1'))
    def test_risk_over_limit_is_rejected(self):
        r=RiskCheck.build('100','90','2','1000','1')
        with self.assertRaises(SafetyError): r.assert_within_limit()
    def test_rejects_nonfinite_quantity(self):
        with self.assertRaises(SafetyError): RiskCheck.build('100','99','NaN','1000','1')

if __name__=='__main__': unittest.main()
