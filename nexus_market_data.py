"""Read-only indicative market rates from Twelve Data; never feeds Paper orders."""
from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

API_ROOT = "https://api.twelvedata.com/exchange_rate"
SYMBOLS = ("EUR/USD", "XAU/USD")
MAX_BODY = 128 * 1024

class MarketDataError(ValueError):
    pass

@dataclass(frozen=True)
class IndicativeRate:
    symbol: str
    rate: Decimal
    timestamp: int
    age_seconds: int
    status: str


def fetch_rate(symbol: str, *, api_key: str | None = None, now: int | None = None,
               opener=None, timeout: int = 12) -> IndicativeRate:
    """Fetch one source timestamped rate. Does not store it or alter Paper state."""
    if symbol not in SYMBOLS:
        raise MarketDataError("símbolo não permitido")
    key = api_key if api_key is not None else os.environ.get("TWELVE_DATA_API_KEY", "")
    key = key.strip()
    if not key or any(c in key for c in "\r\n"):
        raise MarketDataError("falta TWELVE_DATA_API_KEY ou está inválida")
    query = urllib.parse.urlencode({"symbol": symbol, "apikey": key})
    url = API_ROOT + "?" + query
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "JD-NEXUS-Paper/1.0"}, method="GET")
    if opener is None:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(NoRedirect()).open
    try:
        with opener(request, timeout=timeout) as response:
            if response.status != 200:
                raise MarketDataError(f"API devolveu HTTP {response.status}")
            body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise MarketDataError("resposta da API demasiado grande")
        data = json.loads(body)
    except urllib.error.HTTPError as exc:
        raise MarketDataError(f"API devolveu HTTP {exc.code}; verifica chave/limites") from None
    except urllib.error.URLError:
        raise MarketDataError("falha de rede ao consultar a API") from None
    except (TimeoutError, OSError):
        raise MarketDataError("falha de rede/timeout ao consultar a API") from None
    except (ValueError, TypeError):
        raise MarketDataError("resposta inválida da API") from None
    if not isinstance(data, dict) or data.get("status") == "error" or "rate" not in data or "timestamp" not in data:
        raise MarketDataError("a API não devolveu taxa e timestamp válidos")
    if data.get("symbol") != symbol:
        raise MarketDataError("a API devolveu símbolo diferente do pedido")
    try:
        rate = Decimal(str(data["rate"]))
        timestamp = int(data["timestamp"])
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        raise MarketDataError("a API devolveu valores inválidos") from None
    if not rate.is_finite() or rate <= 0 or timestamp <= 0:
        raise MarketDataError("a API devolveu valores fora do intervalo")
    age = int(now if now is not None else time.time()) - timestamp
    if age < -30:
        raise MarketDataError("timestamp futuro inesperado; taxa rejeitada")
    status = "RECENTE" if age <= 300 else "ANTIGA — não usar como atual"
    return IndicativeRate(symbol, rate, timestamp, max(age, 0), status)


def fetch_supported(*, api_key: str | None = None, now: int | None = None, opener=None):
    """Return each valid symbol independently; errors avoid exposing API response/key."""
    results = []
    for symbol in SYMBOLS:
        try:
            results.append(fetch_rate(symbol, api_key=api_key, now=now, opener=opener))
        except MarketDataError as exc:
            results.append((symbol, str(exc)))
    return results
