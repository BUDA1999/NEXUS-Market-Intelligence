"""NEXUS safety primitives for validation only.

No broker connection, Forex contract sizing, margin, swaps, costs, or conversions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation


class SafetyError(ValueError):
    """Raised when market data or a proposed paper trade fails safety checks."""


def _decimal(value: object, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise SafetyError(f"{field} must be a valid number") from None
    if not result.is_finite():
        raise SafetyError(f"{field} must be finite")
    return result


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: Decimal
    ask: Decimal
    timestamp: datetime
    source: str

    @classmethod
    def build(cls, symbol: str, bid: object, ask: object,
              timestamp: datetime, source: str) -> "Quote":
        if not isinstance(symbol, str) or not symbol.strip():
            raise SafetyError("symbol is required")
        if not isinstance(source, str) or not source.strip():
            raise SafetyError("quote source is required")
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise SafetyError("timestamp must include timezone information")
        if timestamp.utcoffset() is None:
            raise SafetyError("timestamp must include timezone information")
        b, a = _decimal(bid, "bid"), _decimal(ask, "ask")
        if b <= 0 or a <= 0:
            raise SafetyError("bid and ask must be greater than zero")
        if a < b:
            raise SafetyError("ask cannot be lower than bid")
        return cls(symbol.strip().upper(), b, a, timestamp, source.strip())

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid

    def assert_fresh(self, max_age_seconds: int,
                     now: datetime | None = None) -> None:
        if max_age_seconds < 0:
            raise SafetyError("max_age_seconds cannot be negative")
        current = now or datetime.now(timezone.utc)
        if not isinstance(current, datetime) or current.tzinfo is None or current.utcoffset() is None:
            raise SafetyError("now must include timezone information")
        age = (current - self.timestamp).total_seconds()
        if age < -5:
            raise SafetyError("quote timestamp is in the future")
        if age > max_age_seconds:
            raise SafetyError(f"stale quote: {age:.1f}s old; limit is {max_age_seconds}s")


@dataclass(frozen=True)
class RiskCheck:
    entry: Decimal
    stop: Decimal
    quantity: Decimal
    capital: Decimal
    max_risk_pct: Decimal

    @classmethod
    def build(cls, entry: object, stop: object, quantity: object,
              capital: object, max_risk_pct: object) -> "RiskCheck":
        values = {
            "entry": _decimal(entry, "entry"),
            "stop": _decimal(stop, "stop"),
            "quantity": _decimal(quantity, "quantity"),
            "capital": _decimal(capital, "capital"),
            "max_risk_pct": _decimal(max_risk_pct, "max_risk_pct"),
        }
        if values["entry"] <= 0 or values["stop"] <= 0:
            raise SafetyError("entry and stop must be greater than zero")
        if values["quantity"] <= 0 or values["capital"] <= 0:
            raise SafetyError("quantity and capital must be greater than zero")
        if not (Decimal("0") < values["max_risk_pct"] <= Decimal("100")):
            raise SafetyError("max_risk_pct must be between 0 and 100")
        if values["entry"] == values["stop"]:
            raise SafetyError("stop must differ from entry")
        return cls(**values)

    @property
    def estimated_loss(self) -> Decimal:
        # Generic linear instrument calculation; excludes costs and FX conversion.
        return abs(self.entry - self.stop) * self.quantity

    @property
    def risk_pct(self) -> Decimal:
        return (self.estimated_loss / self.capital) * Decimal("100")

    def assert_within_limit(self) -> None:
        if self.risk_pct > self.max_risk_pct:
            raise SafetyError(f"risk {self.risk_pct:.4f}% exceeds limit {self.max_risk_pct:.4f}%")
