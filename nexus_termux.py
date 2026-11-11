#!/usr/bin/env python3
"""NEXUS Termux paper terminal. Standard library only; manual quotes, no broker."""
from __future__ import annotations
import argparse
import csv
from contextlib import closing
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from nexus_safety import Quote, SafetyError

SYMBOLS = {"EUR/USD", "XAU/USD"}
D = Decimal
UTC = timezone.utc
DEFAULT_DB = Path(os.environ.get("NEXUS_DB", "~/.nexus-trading/nexus.sqlite3")).expanduser()
MAX_RISK = D("0.01")
MAX_DAILY_LOSS = D("0.03")
MAX_EXPOSURE = D("1.00")
MAX_QUOTES_AGE_SECONDS = 1800
MAX_RISK, MIN_RISK = D("0.01"), D("0.001")
MAX_DAILY_LOSS, MIN_DAILY_LOSS = D("0.10"), D("0.01")
MAX_EXPOSURE, MIN_EXPOSURE = D("2.00"), D("0.10")
RISK_DEFAULTS = {"max_risk": MAX_RISK, "max_daily_loss": D("0.03"), "max_exposure": D("1.00")}
DATA_DIR = DEFAULT_DB.parent
BACKUP_DIR = DATA_DIR / "backups"
REPORT_DIR = DATA_DIR / "reports"


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
        self._connect()
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
        self._load()

    def _connect(self):
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")

    def _load(self):
        self.initial_capital = dec(self.setting("initial_capital") or "1000")
        if self.initial_capital <= 0: raise ValueError("capital inicial deve ser positivo")
        bounds={"max_risk":(MIN_RISK,MAX_RISK),"max_daily_loss":(MIN_DAILY_LOSS,MAX_DAILY_LOSS),
                "max_exposure":(MIN_EXPOSURE,MAX_EXPOSURE)}
        for key, default in RISK_DEFAULTS.items():
            raw=self.setting(key)
            value=dec(raw,key) if raw is not None else default
            low,high=bounds[key]
            if not low <= value <= high: raise ValueError(f"configuração de risco inválida: {key}")
            setattr(self,key,value)

    def quote_age(self, symbol):
        row = self.db.execute("SELECT updated_at FROM quotes WHERE symbol=?", (symbol,)).fetchone()
        if not row: return None
        return (datetime.now(UTC) - datetime.fromisoformat(row[0])).total_seconds()

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
        if symbol not in SYMBOLS:
            raise ValueError("símbolo de cotação não permitido")
        row = self.db.execute("SELECT * FROM quotes WHERE symbol=?", (symbol,)).fetchone()
        if not row:
            raise ValueError(f"sem cotação simulada para {symbol}; introduz bid/ask primeiro")
        q = dict(row)
        try:
            validated = Quote.build(
                symbol=symbol,
                bid=q["bid"],
                ask=q["ask"],
                timestamp=datetime.fromisoformat(q["updated_at"]),
                source=q["source"],
            )
            if require_fresh:
                validated.assert_fresh(MAX_QUOTES_AGE_SECONDS)
        except SafetyError as exc:
            message = str(exc)
            if "stale quote" in message:
                raise ValueError("cotação manual antiga (>30 min); atualiza bid/ask antes da ordem") from None
            if "future" in message:
                raise ValueError("horário da cotação está no futuro; atualiza bid/ask") from None
            raise ValueError("cotação guardada inválida; atualiza bid/ask antes da ordem") from None
        except (KeyError, TypeError, ValueError):
            raise ValueError("cotação guardada inválida; atualiza bid/ask antes da ordem") from None
        return q

    def manual_halt(self):
        """Read the persistent Paper kill switch; unknown states fail closed."""
        raw = self.setting("paper_halted")
        if raw is None or raw == "0":
            return False
        if raw == "1":
            return True
        raise ValueError("estado do kill switch inválido; Paper bloqueado")

    def set_kill_switch(self, halted, reason="manual"):
        """Persist the Paper-only entry stop. Existing positions remain manageable."""
        if not isinstance(halted, bool):
            raise ValueError("estado do kill switch deve ser booleano")
        with self.db:
            self.db.execute(
                "INSERT INTO settings(key,value) VALUES('paper_halted',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                ("1" if halted else "0",),
            )
            self.db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
                            (stamp(), "PAPER_KILL_SWITCH", json.dumps(
                                {"halted": halted, "reason": str(reason)[:120]}, sort_keys=True)))
        return halted

    def halted(self):
        return self.manual_halt() or self.daily_pnl() <= -self.initial_capital * self.max_daily_loss

    def open_position(self, symbol, side, stop, target, risk_fraction=None):
        side = side.upper()
        if symbol not in SYMBOLS or side not in {"BUY", "SELL"}:
            raise ValueError("símbolo/lado inválido")
        q = self.quote(symbol, require_fresh=True)
        bid, ask = D(q['bid']), D(q['ask'])
        entry = ask if side == "BUY" else bid
        stop, target = dec(stop, "stop"), dec(target, "take-profit")
        risk_fraction = self.max_risk if risk_fraction in (None, "") else dec(risk_fraction, "risco")
        if risk_fraction <= 0 or risk_fraction > self.max_risk:
            raise ValueError(f"risco por posição tem de ser >0 e no máximo {self.max_risk * 100}%")
        if stop <= 0 or target <= 0:
            raise ValueError("stop e take-profit têm de ser positivos")
        if (side == "BUY" and not stop < entry < target) or (side == "SELL" and not target < entry < stop):
            raise ValueError("BUY exige stop < entrada < alvo; SELL exige alvo < entrada < stop")
        equity = self.equity()
        daily = self.daily_pnl()
        if self.manual_halt():
            raise ValueError("kill switch Paper persistente ativo; novas posições bloqueadas")
        if equity <= 0 or self.daily_pnl() <= -self.initial_capital * self.max_daily_loss:
            raise ValueError(f"limite de perda diária ({self.max_daily_loss * 100}% do capital inicial) atingido")
        unit_risk = abs(entry - stop)
        units_by_risk = equity * risk_fraction / unit_risk
        open_rows = self.db.execute("SELECT symbol,side,entry,units FROM positions WHERE status='OPEN'").fetchall()
        exposure = sum((D(r['entry']) * D(r['units']) for r in open_rows), D(0))
        units = min(units_by_risk, max(D(0), equity * self.max_exposure - exposure) / entry)
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


    # --- Read-only account views ---
    def _unrealized(self, row):
        q = self.db.execute("SELECT bid,ask FROM quotes WHERE symbol=?", (row["symbol"],)).fetchone()
        if not q: return None
        mark = D(q["bid"] if row["side"] == "BUY" else q["ask"])
        diff = mark - D(row["entry"]) if row["side"] == "BUY" else D(row["entry"]) - mark
        return diff * D(row["units"])

    def summary(self):
        opened = self.db.execute("SELECT * FROM positions WHERE status='OPEN'").fetchall()
        closed = self.db.execute("SELECT COUNT(*) FROM positions WHERE status='CLOSED'").fetchone()[0]
        exposure = sum((D(r["entry"]) * D(r["units"]) for r in opened), D(0))
        marks = [self._unrealized(r) for r in opened]
        daily = self.daily_pnl()
        loss_limit = self.initial_capital * self.max_daily_loss
        equity = self.equity()
        return {"capital_initial": self.initial_capital, "equity": equity,
                "realized": equity-self.initial_capital,
                "unrealized": sum((x for x in marks if x is not None), D(0)),
                "unpriced": sum(x is None for x in marks), "daily_pnl": daily,
                "daily_limit": loss_limit, "daily_remaining": max(D(0), loss_limit+daily),
                "halted": self.halted(), "manual_halt": self.manual_halt(), "open_count": len(opened), "closed_count": closed,
                "exposure": exposure, "exposure_cap": equity*self.max_exposure,
                "max_risk": self.max_risk, "max_daily_loss": self.max_daily_loss,
                "max_exposure": self.max_exposure}

    def position_detail(self, position_id):
        r = self.db.execute("SELECT * FROM positions WHERE id=?", (position_id,)).fetchone()
        if not r: raise ValueError("posição não encontrada")
        row = dict(r)
        unit_risk = abs(D(row["entry"])-D(row["stop"]))
        return {"row": row, "risk_at_stop": unit_risk*D(row["units"]),
                "unrealized": self._unrealized(r) if row["status"] == "OPEN" else None,
                "quote_age": self.quote_age(row["symbol"])}

    def set_risk(self, max_risk=None, max_daily_loss=None, max_exposure=None):
        proposed = {}
        bounds = (("max_risk", max_risk, MIN_RISK, MAX_RISK),
                  ("max_daily_loss", max_daily_loss, MIN_DAILY_LOSS, MAX_DAILY_LOSS),
                  ("max_exposure", max_exposure, MIN_EXPOSURE, MAX_EXPOSURE))
        for key, raw, low, high in bounds:
            if raw in (None, ""): continue
            value = dec(raw, key)
            if not low <= value <= high:
                raise ValueError(f"{key} fora do intervalo {low*100}%–{high*100}%")
            proposed[key] = value
        if not proposed: return {}
        # Validate the whole update before committing any setting.
        with self.db:
            for key, value in proposed.items():
                self.db.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key,str(value)))
            self.db.execute("INSERT INTO events(at,kind,payload) VALUES(?,?,?)",
                            (stamp(), "RISK_UPDATED", json.dumps({k:str(v) for k,v in proposed.items()},sort_keys=True)))
        for key, value in proposed.items(): setattr(self, key, value)
        return proposed

    def export_history(self, directory=None):
        target = Path(directory or (self.path.parent / "reports")).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        base = "nexus-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        csv_path, txt_path = target/(base+".csv"), target/(base+".txt")
        fields = ("id","symbol","side","entry","stop","target","units","opened_at","status","close_price","closed_at","pnl","close_reason")
        rows = self.db.execute("SELECT * FROM positions ORDER BY id").fetchall()
        with csv_path.open("w",newline="",encoding="utf-8") as fh:
            writer=csv.writer(fh); writer.writerow(fields)
            for r in rows: writer.writerow([r[k] for k in fields])
        summary=self.summary()
        txt_path.write_text("\n".join([
            "NEXUS — relatório de paper trading (SIMULAÇÃO, sem broker)", f"gerado: {stamp()}",
            f"capital inicial: {fmt_money(summary['capital_initial'])}", f"saldo realizado: {fmt_money(summary['equity'])}",
            f"P&L realizado: {fmt_money(summary['realized'])} | não realizado: {fmt_money(summary['unrealized'])}",
            f"operações: {summary['open_count']} aberta(s), {summary['closed_count']} fechada(s)",
            "Cotações manuais; não são preços executáveis nem representam spread real.", ""]),encoding="utf-8")
        return csv_path, txt_path

    def backup_database(self, directory=None):
        target = Path(directory or (self.path.parent / "backups")).expanduser()
        target.mkdir(parents=True,exist_ok=True)
        dest=target/(self.path.stem+"-"+datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")+".sqlite3")
        with closing(sqlite3.connect(dest)) as out:
            self.db.backup(out)
        return dest

    def restore_database(self, source, backup_directory=None):
        source=Path(source).expanduser().resolve()
        active=self.path.resolve()
        if source == active or (source.exists() and active.exists() and source.samefile(active)):
            raise ValueError("restauro exige um backup diferente da base ativa")
        if not source.is_file(): raise FileNotFoundError("ficheiro de backup não encontrado")
        # Backup API reads the source consistently and replaces the destination via SQLite.
        # Close other NEXUS sessions first. The safety snapshot is retained for recovery.
        with closing(sqlite3.connect(source.as_uri()+"?mode=ro",uri=True)) as src:
            if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("backup inválido: integrity_check falhou")
            tables={r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            required={"settings":{"key","value"},"quotes":{"symbol","bid","ask","source","updated_at"},
                      "positions":{"id","symbol","side","entry","stop","target","units","opened_at","status","close_price","closed_at","pnl","close_reason"},
                      "events":{"id","at","kind","payload"}}
            if not set(required).issubset(tables): raise ValueError("backup sem esquema NEXUS")
            for table, columns in required.items():
                if not columns.issubset({r[1] for r in src.execute(f"PRAGMA table_info({table})")}):
                    raise ValueError(f"backup com esquema inválido em {table}")
            initial=src.execute("SELECT value FROM settings WHERE key='initial_capital'").fetchone()
            if not initial or dec(initial[0],"capital inicial") <= 0: raise ValueError("capital inicial inválido no backup")
            bounds={"max_risk":(MIN_RISK,MAX_RISK),"max_daily_loss":(MIN_DAILY_LOSS,MAX_DAILY_LOSS),
                    "max_exposure":(MIN_EXPOSURE,MAX_EXPOSURE)}
            for key,(low,high) in bounds.items():
                item=src.execute("SELECT value FROM settings WHERE key=?",(key,)).fetchone()
                if item and not low <= dec(item[0],key) <= high:
                    raise ValueError(f"limite inválido no backup: {key}")
            safety_copy=self.backup_database(backup_directory)
            self.db.commit()
            src.backup(self.db)
        self._load()
        self._event("DATABASE_RESTORED", {"source_name":source.name,"pre_restore_backup":safety_copy.name})
        return safety_copy

    def close(self): self.db.close()


def fmt_money(x): return f"${D(x):,.2f}"
def show(n, selected=None):
    from nexus_ui import render_dashboard, render_menu
    from nexus_status import inspect_status
    render_dashboard(n, inspect_status(n.path))
    render_menu(selected=selected)

def prompt_decimal(label): return dec(input(label).strip(), label)

def show_summary(n):
    s=n.summary()
    print("\n=== RESUMO DA CONTA (PAPER) ===")
    for label,key in (("Capital inicial","capital_initial"),("Saldo realizado","equity"),
                      ("P&L realizado","realized"),("P&L não realizado estimado","unrealized"),
                      ("P&L fechado hoje UTC","daily_pnl"),("Limite diário","daily_limit"),
                      ("Limite diário restante","daily_remaining"),("Exposição aberta","exposure"),
                      ("Teto de exposição","exposure_cap")):
        print(f"{label}: {fmt_money(s[key])}")
    print(f"Posições: {s['open_count']} abertas / {s['closed_count']} fechadas; sem cotação: {s['unpriced']}")
    print(f"Limites: risco {s['max_risk']*100}% | perda diária {s['max_daily_loss']*100}% | exposição {s['max_exposure']*100}%")
    print(f"Bloqueio Paper: {'ATIVO' if s['halted'] else 'não'} | kill switch: {'ATIVO' if s['manual_halt'] else 'inativo'}")
    print("Estimativas usam últimas cotações manuais, que podem estar antigas; não são equity de corretora.")

def show_detail(n):
    pid=int(input("ID da posição: ").strip()); d=n.position_detail(pid); r=d['row']
    print(f"\n#{r['id']} {r['status']} {r['side']} {r['symbol']}")
    print(f"Entrada {r['entry']} | SL {r['stop']} | TP {r['target']} | unidades {r['units']}")
    print(f"Risco estimado até SL: {fmt_money(d['risk_at_stop'])}")
    print("P&L não realizado estimado: " + (fmt_money(d['unrealized']) if d['unrealized'] is not None else "sem cotação"))
    age=d['quote_age']; print("Idade da cotação manual: " + (f"{max(0,age):.0f} s" if age is not None else "sem cotação"))

def show_risk(n):
    print(f"Atual: risco/posição {n.max_risk*100}%, perda diária {n.max_daily_loss*100}%, exposição {n.max_exposure*100}%")
    print("Faixas: risco 0.1–1%; perda diária 1–10%; exposição 10–200%.")
    print("Enter mantém o limite atual.")
    a=input("Novo risco por posição (%): ").strip()
    b=input("Novo limite de perda diária (%): ").strip()
    c=input("Nova exposição máxima (%): ").strip()
    changes=n.set_risk(max_risk=dec(a,"risco")/100 if a else None,
                       max_daily_loss=dec(b,"perda")/100 if b else None,
                       max_exposure=dec(c,"exposição")/100 if c else None)
    print("Limites atualizados." if changes else "Sem alterações.")

def show_system_status(n):
    from nexus_status import inspect_status, format_status
    print(format_status(inspect_status(n.path)))

def show_help():
    print("\nNEXUS Market Intelligence — ajuda")
    print("0 sair | 1 cotação manual | 2 abrir simulada | 3 abertas | 4 histórico | 5 fechar simulada")
    print("6 resumo | 7 detalhes | 8 limites | 9 exportar CSV/TXT | b backup | r restaurar | a estado | k kill switch | h ajuda")
    print("Só Paper Trading. Sem API de mercado, corretora, preço ao vivo ou monitorização em background.")
    print("Restauro substitui o estado atual, após criar automaticamente uma cópia de segurança.")
    print("k ativa/desativa kill switch Paper persistente; não envia nem fecha ordens reais.")

def run_menu(n):
    selected=None
    while True:
        show(n, selected)
        choice=input("\nNEXUS > ").strip().lower()
        selected=choice
        try:
            if choice=="0": return
            elif choice=="1":
                s=input("Símbolo (EUR/USD ou XAU/USD): ").strip().upper()
                b=prompt_decimal("Bid manual: "); a=prompt_decimal("Ask manual: ")
                closed=n.update_quote(s,b,a)
                print(f"Cotação manual guardada. Saídas simuladas acionadas: {len(closed)}")
            elif choice=="2":
                s=input("Símbolo (EUR/USD ou XAU/USD): ").strip().upper()
                side=input("Lado BUY/SELL: ").strip().upper()
                stop=prompt_decimal("Stop-loss: "); target=prompt_decimal("Take-profit: ")
                p=n.open_position(s,side,stop,target)
                print("Posição simulada aberta:",json.dumps(p,ensure_ascii=False))
            elif choice=="3":
                rows=n.positions("OPEN")
                if not rows: print("Sem posições abertas.")
                for r in rows: print(f"#{r['id']} {r['side']} {r['symbol']} entrada={r['entry']} unidades={r['units']} SL={r['stop']} TP={r['target']}")
            elif choice=="4":
                for r in n.positions(): print(f"#{r['id']} {r['status']} {r['side']} {r['symbol']} P&L={r['pnl'] or '—'} motivo={r['close_reason'] or '—'}")
            elif choice=="5":
                pid=int(input("ID da posição: ")); print("Fecho simulado:",json.dumps(n.close_position(pid)))
            elif choice=="6": show_summary(n)
            elif choice=="7": show_detail(n)
            elif choice=="8": show_risk(n)
            elif choice=="9":
                csv_path,txt_path=n.export_history(); print(f"Exportados:\n{csv_path}\n{txt_path}")
            elif choice=="b": print("Cópia criada:",n.backup_database())
            elif choice=="r":
                backups=sorted((n.path.parent/"backups").glob("*.sqlite3"),reverse=True)
                if not backups: print("Nenhuma cópia .sqlite3 encontrada.")
                else:
                    for i,path in enumerate(backups,1): print(f"{i}. {path.name}")
                    selected=int(input("Número da cópia: ").strip())
                    if not 1 <= selected <= len(backups): raise ValueError("seleção fora da lista")
                    if input("Restauro substitui o estado atual. Escreve RESTORE para confirmar: ").strip()!="RESTORE": print("Restauro cancelado.")
                    else: print("Restaurado; cópia do estado anterior:",n.restore_database(backups[selected-1]))
            elif choice=="a": show_system_status(n)
            elif choice=="k":
                active=n.manual_halt()
                if active:
                    if input("Kill switch ativo. Escreve RESUME para permitir novas posições Paper: ").strip() == "RESUME":
                        n.set_kill_switch(False, "explicit-resume")
                        print("Kill switch desativado; Paper continua sem broker.")
                    else: print("Kill switch mantido ativo.")
                else:
                    if input("Escreve HALT para bloquear novas posições Paper: ").strip() == "HALT":
                        n.set_kill_switch(True, "manual-menu")
                        print("Kill switch persistente ATIVO; posições existentes continuam geríveis.")
                    else: print("Ativação cancelada.")
            elif choice=="h": show_help()
            else: print("Opção inválida.")
        except (ValueError, sqlite3.Error, OSError) as exc: print(f"\033[31mNão executado: {exc}\033[0m")
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
