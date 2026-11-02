import unittest
from nexus_paper import OrderRejected, OrderRequest, Side, validate_and_size

class PaperRiskTests(unittest.TestCase):
    def request(self, **changes):
        data = dict(symbol="EUR/USD", side=Side.BUY, entry=1.10,
                    stop_loss=1.09, take_profit=1.12, equity=1000,
                    risk_fraction=0.01)
        data.update(changes)
        return OrderRequest(**data)

    def test_sizes_order_with_one_percent_risk(self):
        order = validate_and_size(self.request())
        self.assertEqual(order.mode, "PAPER_ONLY")
        self.assertEqual(order.status, "VALIDATED_NOT_OPEN")
        self.assertLessEqual(order.risk_amount, 10.0)
        self.assertAlmostEqual(order.reward_risk, 2.0)
        self.assertLessEqual(order.notional, 1000.0)

    def test_rejects_bad_buy_stop_order(self):
        with self.assertRaises(OrderRejected):
            validate_and_size(self.request(stop_loss=1.11))

    def test_rejects_risk_over_one_percent(self):
        with self.assertRaises(OrderRejected):
            validate_and_size(self.request(risk_fraction=0.02))

    def test_rejects_symbols_outside_scope(self):
        with self.assertRaises(OrderRejected):
            validate_and_size(self.request(symbol="AAPL"))

    def test_daily_drawdown_stops_new_orders(self):
        with self.assertRaises(OrderRejected):
            validate_and_size(self.request(daily_pnl=-30.0))

    def test_sell_direction_and_bounds(self):
        order = validate_and_size(self.request(side=Side.SELL, entry=1.1,
                                               stop_loss=1.11, take_profit=1.08))
        self.assertEqual(order.side, "SELL")

if __name__ == "__main__":
    unittest.main()
