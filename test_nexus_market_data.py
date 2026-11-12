import json
from decimal import Decimal
import unittest
from unittest.mock import patch
from nexus_market_data import fetch_rate, MarketDataError, IndicativeRate

class FakeResponse:
    status = 200
    def __init__(self, data): self.data = json.dumps(data).encode()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, limit=-1): return self.data[:limit]

def fake_opener(data):
    def open(request, timeout=0):
        assert request.full_url.startswith("https://api.twelvedata.com/exchange_rate?")
        return FakeResponse(data)
    return open

class MarketDataTests(unittest.TestCase):
    def test_valid_rate_is_read_only_and_timestamped(self):
        r=fetch_rate("EUR/USD",api_key="secret",now=1000,opener=fake_opener({"symbol":"EUR/USD","rate":"1.1","timestamp":990}),)
        self.assertEqual(r.rate, Decimal("1.1"))
        self.assertEqual(r.age_seconds,10)
        self.assertEqual(r.status,"RECENTE")

    def test_stale_rate_is_flagged_not_falsely_fresh(self):
        r=fetch_rate("XAU/USD",api_key="secret",now=2000,opener=fake_opener({"symbol":"XAU/USD","rate":"4000","timestamp":1500}))
        self.assertIn("ANTIGA",r.status)

    def test_future_timestamp_rejected(self):
        with self.assertRaisesRegex(MarketDataError,"futuro"):
            fetch_rate("EUR/USD",api_key="secret",now=1000,opener=fake_opener({"symbol":"EUR/USD","rate":"1.1","timestamp":1100}))

    def test_symbol_mismatch_rejected(self):
        with self.assertRaisesRegex(MarketDataError,"símbolo diferente"):
            fetch_rate("EUR/USD",api_key="secret",now=1000,opener=fake_opener({"symbol":"XAU/USD","rate":"1.1","timestamp":990}))

    def test_invalid_nonfinite_value_rejected(self):
        with self.assertRaises(MarketDataError):
            fetch_rate("EUR/USD",api_key="secret",now=1000,opener=fake_opener({"symbol":"EUR/USD","rate":"NaN","timestamp":990}))

    def test_errors_do_not_echo_api_response_or_secret(self):
        with self.assertRaises(MarketDataError) as ctx:
            fetch_rate("EUR/USD",api_key="SECRETKEY",now=1000,opener=fake_opener({"status":"error","message":"SECRETKEY"}))
        self.assertNotIn("SECRETKEY",str(ctx.exception))

    def test_unapproved_symbol_rejected_before_network(self):
        with self.assertRaises(MarketDataError):
            fetch_rate("USD/JPY",api_key="secret",opener=lambda *a,**k: self.fail("network should not run"))

if __name__ == "__main__": unittest.main()
