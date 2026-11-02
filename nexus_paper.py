"""NEXUS offline paper-order validation. No broker, network or execution."""
from __future__ import annotations
import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum

ALLOWED_SYMBOLS = {"EUR/USD", "XAU/USD"}

class OrderRejected(ValueError):
    """Raised when order parameters or risk controls fail."""

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass(frozen=True)
class RiskLimits:
    max_risk_fraction: float = 0.01
    max_notional_fraction: float = 1.0
    max_daily_loss_fraction: float = 0.03

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if not math.isfinite(value) or value <= 0 or value > 1:
                raise OrderRejected(f"{name} must be greater than 0 and at most 1")

@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: Side
    entry: float
    stop_loss: float
    take_profit: float
    equity: float
    risk_fraction: float = 0.01
    daily_pnl: float = 0.0

@dataclass(frozen=True)
class PaperOrder:
    order_id: str
    created_at: str
    symbol: str
    side: str
    entry: float
    stop_loss: float
    take_profit: float
    units: float
    notional: float
    risk_amount: float
    reward_risk: float
    status: str = "VALIDATED_NOT_OPEN"
    mode: str = "PAPER_ONLY"

def validate_and_size(req: OrderRequest, limits: RiskLimits = RiskLimits()) -> PaperOrder:
    limits.validate()
    if req.symbol not in ALLOWED_SYMBOLS:
        raise OrderRejected(f"Unsupported symbol: {req.symbol}; allowed: EUR/USD, XAU/USD")
    if not isinstance(req.side, Side):
        raise OrderRejected("side must be BUY or SELL")
    for name, value in (("entry", req.entry), ("stop_loss", req.stop_loss),
                        ("take_profit", req.take_profit), ("equity", req.equity),
                        ("risk_fraction", req.risk_fraction), ("daily_pnl", req.daily_pnl)):
        if not math.isfinite(value):
            raise OrderRejected(f"{name} must be finite")
    if min(req.entry, req.stop_loss, req.take_profit, req.equity) <= 0:
        raise OrderRejected("prices and equity must be positive")
    if req.risk_fraction <= 0 or req.risk_fraction > limits.max_risk_fraction:
        raise OrderRejected(f"risk_fraction exceeds configured cap ({limits.max_risk_fraction:.2%})")
    if req.daily_pnl <= -req.equity * limits.max_daily_loss_fraction:
        raise OrderRejected("daily loss limit reached; no more simulated orders today")
    if req.side is Side.BUY:
        if not req.stop_loss < req.entry < req.take_profit:
            raise OrderRejected("BUY requires stop_loss < entry < take_profit")
    else:
        if not req.take_profit < req.entry < req.stop_loss:
            raise OrderRejected("SELL requires take_profit < entry < stop_loss")
    unit_risk = abs(req.entry - req.stop_loss)
    unit_reward = abs(req.take_profit - req.entry)
    risk_amount = req.equity * req.risk_fraction
    units_by_risk = risk_amount / unit_risk
    max_notional = req.equity * limits.max_notional_fraction
    units = min(units_by_risk, max_notional / req.entry)
    if not math.isfinite(units) or units <= 0:
        raise OrderRejected("position size is invalid")
    return PaperOrder(
        order_id=f"PAPER-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}",
        created_at=datetime.now(timezone.utc).isoformat(),
        symbol=req.symbol, side=req.side.value, entry=req.entry,
        stop_loss=req.stop_loss, take_profit=req.take_profit, units=units,
        notional=units * req.entry, risk_amount=units * unit_risk,
        reward_risk=unit_reward / unit_risk,
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="NEXUS offline paper-order validator (no broker/API).")
    parser.add_argument("--symbol", choices=sorted(ALLOWED_SYMBOLS), required=True)
    parser.add_argument("--side", choices=[s.value for s in Side], required=True)
    parser.add_argument("--entry", type=float, required=True, help="Example price only; you supply it")
    parser.add_argument("--stop", type=float, required=True)
    parser.add_argument("--take", type=float, required=True)
    parser.add_argument("--equity", type=float, required=True, help="Simulated account equity in USD")
    parser.add_argument("--daily-pnl", type=float, default=0.0, help="User-supplied simulated daily P&L; not tracked")
    parser.add_argument("--risk", type=float, default=0.01, help="Fraction, default 0.01 (1 percent)")
    args = parser.parse_args()
    try:
        order = validate_and_size(OrderRequest(
            symbol=args.symbol, side=Side(args.side), entry=args.entry,
            stop_loss=args.stop, take_profit=args.take, equity=args.equity,
            risk_fraction=args.risk, daily_pnl=args.daily_pnl,
        ))
    except OrderRejected as exc:
        parser.error(str(exc))
    print(json.dumps(asdict(order), indent=2))

if __name__ == "__main__":
    main()
