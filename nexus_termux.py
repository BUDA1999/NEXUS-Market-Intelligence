#!/usr/bin/env python3
"""NEXUS Termux paper terminal. Standard library only; manual quotes, no broker."""
from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

SYMBOLS = {"EUR/USD", "XAU/USD"}
D = Decimal
UTC = timezone.utc
DEFAULT_DB = Path(os.environ.get("NEXUS_DB", "~/.nexus-trading/nexus.sqlite3")).expanduser()
MAX_RISK = D("0.01")
MAX_DAILY_LOSS = D("0.03")
MAX_EXPOSURE = D("1.00")
MAX_QUOTES_AGE_SECONDS = 1800


def dec(value, name="value"):
    try:
        result = D(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{name} deve ser um número válido") from None
    if not result.is_finite():
        raise ValueError(f"{name} deve ser finito")
    return result


def stamp():
    return datetime.now(UTC).isoformat(timespec="seconds")


class Nexus:
    def __init__(self, db_path=DEFAULT_DB, capital=D("1000")):
        self.path = Path(db_path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS quotes(
                symbol TEXT PRIMARY KEY, bid TEXT NOT NULL, ask TEXT NOT NULL,
                source TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS positions(
                id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
                side TEXT NOT NULL, entry TEXT NOT NULL, stop TEXT NOT NULL,
                target TEXT NOT NULL, units TEXT NOT NULL, opened_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'OPEN', close_price TEXT,
                closed_at TEXT, pnl TEXT, close_reason TEXT);
            CREATE TABLE IF NOT EXISTS events(
                id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                kind TEXT NOT NULL, payload TEXT NOT NULL);
        """)
        self.db.commit()
        self.db.execute("INSERT OR IGNORE INTO settings VALUES('initial_capital', ?)", (str(dec(capital, 'capital')),))
        self.db.commit()
        self.initial_capital = dec(self.setting("initial_capital"))
        if self.initial_capital <= 0:
            raise ValueError("capital inicial deve ser positivo")

    def setting(self, key):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def equity(self):
        # Retain decimal handling for the stored realized P&L values.
        realized = sum((D(r[0]) for r in self.db.execute("SELECT pnl FROM positions WHERE status='CLOSED'")), D(0))
        return self.initial_capital + realized

    def daily_pnl(self):
        today = datetime.now(UTC).date().isoformat()
        rows = self.db.execute("SELECT pnl,closed_at FROM positions WHERE status='CLOSED'").fetchall()
        return sum((D(r['pnl']) for r in rows if r['closed_at'][:10] == today), D(0))

    def _event(self, kind, payload):
        self.db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
                        (stamp(), kind, json.dumps(payload, sort_keys=True)))
        self.db.commit()

    def update_quote(self, symbol, bid, ask):
        if symbol not in SYMBOLS:
            raise ValueError("símbolo permitido: EUR/USD ou XAU/USD")
        bid, ask = dec(bid, "bid"), dec(ask, "ask")
        if bid <= 0 or ask < bid:
            raise ValueError("preços inválidos: precisam ser positivos e ask >= bid")
        self.db.execute("INSERT INTO quotes VALUES(?,?,?,?,?) ON CONFLICT(symbol) DO UPDATE SET bid=excluded.bid, ask=excluded.ask, source=excluded.source, updated_at=excluded.updated_at",
                        (symbol, str(bid), str(ask), "MANUAL — introduzida pelo utilizador", stamp()))
        self.db.commit()
        closed = self._check_exits(symbol, bid, ask)
        self._event("QUOTE_UPDATED", {"symbol": symbol, "bid": str(bid), "ask": str(ask), "auto_closed": closed})
        return closed

    def quote(self, symbol, require_fresh=False):
        row = self.db.execute("SELECT * FROM quotes WHERE symbol=?", (symbol,)).fetchone()
        if not row:
            raise ValueError(f"sem cotação simulada para {symbol}; introduz bid/ask primeiro")
        q = dict(row)
        if require_fresh:
            age = (datetime.now(UTC) - datetime.fromisoformat(q['updated_at'])).total_seconds()
            if age > MAX_QUOTES_AGE_SECONDS:
                raise ValueError("cotação manual antiga (>30 min); atualiza bid/ask antes da ordem")
        return q

    def open_position(self, symbol, side, stop, target, risk_fraction=D("0.01")):
        side = side.upper()
        if symbol not in SYMBOLS or side not in {"BUY", "SELL"}:
            raise ValueError("símbolo/lado inválido")
        q = self.quote(symbol, require_fresh=True)
        bid, ask = D(q['bid']), D(q['ask'])
        entry = ask if side == "BUY" else bid
        stop, target = dec(stop, "stop"), dec(target, "take-profit")
        risk_fraction = dec(risk_fraction, "risco")
        if risk_fraction <= 0 or risk_fraction > MAX_RISK:
            raise ValueError("risco por posição tem de ser >0 e no máximo 1%")
        if stop <= 0 or target <= 0:
            raise ValueError("stop e take-profit têm de ser positivos")
        if (side == "BUY" and not stop < entry < target) or (side == "SELL" and not target < entry < stop):
            raise ValueError("BUY exige stop < entrada < alvo; SELL exige alvo < entrada < stop")
        equity = self.equity()
        daily = self.daily_pnl()
        if equity <= 0 or daily <= -self.initial_capital * MAX_DAILY_LOSS:
            raise ValueError("limite de perda diária (3% do capital inicial) atingido")
        unit_risk = abs(entry - stop)
        units_by_risk = equity * risk_fraction / unit_risk
        open_rows = self.db.execute("SELECT symbol,side,entry,units FROM positions WHERE status='OPEN'").fetchall()
        exposure = sum((D(r['entry']) * D(r['units']) for r in open_rows), D(0))
        units = min(units_by_risk, max(D(0), equity * MAX_EXPOSURE - exposure) / entry)
        if units <= 0:
            raise ValueError("limite de exposição total atingido")
        risk_money = units * unit_risk
        self.db.execute("INSERT INTO positions(symbol,side,entry,stop,target,units,opened_at,status) VALUES(?,?,?,?,?,?,?,'OPEN')",
                        (symbol, side, str(entry), str(stop), str(target), str(units), stamp()))
        self.db.commit()
        pid = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        data = {"id": pid, "symbol": symbol, "side": side, "entry": str(entry), "stop": str(stop),
                "target": str(target), "units": str(units), "risk_at_stop": str(risk_money), "mode": "PAPER_ONLY"}
        self._event("PAPER_POSITION_OPENED", data)
        return data

    def _check_exits(self, symbol, bid, ask):
        rows = self.db.execute("SELECT * FROM positions WHERE symbol=? AND status='OPEN'", (symbol,)).fetchall()
        closed = []
        for r in rows:
            stop, target = D(r['stop']), D(r['target'])
            side = r['side']
            reason = None
            if side == "BUY":
                if bid <= stop: reason, price = "STOP_LOSS", bid
                elif bid >= target: reason, price = "TAKE_PROFIT", bid
                else: continue
                pnl = (price - D(r['entry'])) * D(r['units'])
            else:
                if ask >= stop: reason, price = "STOP_LOSS", ask
                elif ask <= target: reason, price = "TAKE_PROFIT", ask
                else: continue
                pnl = (D(r['entry']) - price) * D(r['units'])
            self.db.execute("UPDATE positions SET status='CLOSED',close_price=?,closed_at=?,pnl=?,close_reason=? WHERE id=?",
                            (str(price), stamp(), str(pnl), reason, r['id']))
            closed.append({"id": r['id'], "reason": reason, "price": str(price), "pnl": str(pnl)})
        if closed: self.db.commit()
        return closed

    def close_position(self, position_id):
        r = self.db.execute("SELECT * FROM positions WHERE id=? AND status='OPEN'", (position_id,)).fetchone()
        if not r: raise ValueError("posição aberta não encontrada")
        q = self.quote(r['symbol'], require_fresh=True)
        price = D(q['bid'] if r['side'] == 'BUY' else q['ask'])
        pnl = (price - D(r['entry'])) * D(r['units']) if r['side']=='BUY' else (D(r['entry'])-price)*D(r['units'])
        self.db.execute("UPDATE positions SET status='CLOSED',close_price=?,closed_at=?,pnl=?,close_reason='MANUAL_SIMULATED' WHERE id=?",
                        (str(price), stamp(), str(pnl), position_id))
        self.db.commit()
        item = {"id": position_id, "price": str(price), "pnl": str(pnl), "reason": "MANUAL_SIMULATED"}
        self._event("PAPER_POSITION_CLOSED", item)
        return item

    def positions(self, status=None):
        if status: return self.db.execute("SELECT * FROM positions WHERE status=? ORDER BY id DESC", (status,)).fetchall()
        return self.db.execute("SELECT * FROM positions ORDER BY id DESC LIMIT 50").fetchall()

    def quotes(self): return self.db.execute("SELECT * FROM quotes ORDER BY symbol").fetchall()

    def close(self): self.db.close()


def fmt_money(x): return f"${D(x):,.2f}"
def show(n):
    print(" SIMULAÇÃO APENAS — SEM BROKER / SEM COTAÇÕES AO VIVO")
    print(f" Capital: {fmt_money(n.equity())} | P&L diário fechado: {fmt_money(n.daily_pnl())}")
    print("─"*50)
    for q in n.quotes(): print(f" {q['symbol']:7} bid {q['bid']} / ask {q['ask']} [manual]")
    print("\n 1 Atualizar cotação manual   2 Nova posição simulada")
    print(" 3 Posições abertas           4 Histórico")
    print(" 5 Fechar posição              0 Sair")


def prompt_decimal(label): return dec(input(label).strip(), label)

def run_menu(n):
    from jd_banner import jd_banner
    jd_banner()
    while True:
        show(n)
        choice=input("\nNEXUS > ").strip()
        try:
            if choice=="0": return
            if choice=="1":
                s=input("Símbolo (EUR/USD ou XAU/USD): ").strip().upper()
                b=prompt_decimal("Bid manual: "); a=prompt_decimal("Ask manual: ")
                closed=n.update_quote(s,b,a)
                print(f"Cotação manual guardada. Saídas simuladas acionadas: {len(closed)}")
            elif choice=="2":
                s=input("Símbolo (EUR/USD ou XAU/USD): ").strip().upper()
                side=input("Lado BUY/SELL: ").strip().upper()
                stop=prompt_decimal("Stop-loss: "); target=prompt_decimal("Take-profit: ")
                p=n.open_position(s,side,stop,target)
                print("Posição simulada aberta:", json.dumps(p,ensure_ascii=False))
            elif choice=="3":
                rows=n.positions("OPEN")
                if not rows: print("Sem posições abertas.")
                for r in rows: print(f"#{r['id']} {r['side']} {r['symbol']} entrada={r['entry']} unidades={r['units']} SL={r['stop']} TP={r['target']}")
            elif choice=="4":
                for r in n.positions(): print(f"#{r['id']} {r['status']} {r['side']} {r['symbol']} P&L={r['pnl'] or '—'} motivo={r['close_reason'] or '—'}")
            elif choice=="5":
                pid=int(input("ID da posição: ")); print("Fecho simulado:",json.dumps(n.close_position(pid)))
            else: print("Opção inválida.")
        except (ValueError, sqlite3.Error) as exc: print(f"\033[31mNão executado: {exc}\033[0m")
        input("\nEnter para continuar...")


def main():
    parser=argparse.ArgumentParser(description="NEXUS Termux Paper Trading — simulação sem broker")
    parser.add_argument("--db",default=str(DEFAULT_DB)); parser.add_argument("--capital",default="1000")
    parser.add_argument("--check",action="store_true",help="verificar runtime SQLite Python")
    args=parser.parse_args()
    if args.check:
        print(f"Python {sys.version.split()[0]} | SQLite {sqlite3.sqlite_version} | NEXUS stdlib OK")
        return
    n=Nexus(args.db,dec(args.capital,"capital"))
    try:
        if not sys.stdin.isatty(): parser.error("abre uma sessão interativa do Termux para usar o painel")
        run_menu(n)
    except KeyboardInterrupt: print("\nNEXUS encerrado; dados simulados guardados.")
    finally: n.close()

if __name__=="__main__": main()
