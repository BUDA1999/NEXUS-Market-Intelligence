"""Compact, responsive terminal presentation for the existing NEXUS Paper panel."""
from __future__ import annotations
import os
import shutil
import sys
import textwrap
from datetime import datetime, timezone
from decimal import Decimal

CYAN="\033[96m"; BLUE="\033[94m"; GOLD="\033[93m"; WHITE="\033[97m"; GRAY="\033[90m"; RESET="\033[0m"; BOLD="\033[1m"
AGENT_NAMES=("Fundamental Analyst","Sentiment Analyst","News Analyst","Market Analyst",
             "Bull Researcher","Bear Researcher","Research Manager","Trader Agent",
             "Risk Manager","Portfolio Manager")

def terminal_width(stream=None):
    stream=stream or sys.stdout
    try: width=shutil.get_terminal_size(fallback=(40,24)).columns
    except OSError: width=40
    return max(20,width)

def _paint(text,color,enabled): return f"{color}{text}{RESET}" if enabled else text

def _wrap(label,width):
    # No mid-word splitting; narrow screens get one or more clean lines.
    return textwrap.wrap(str(label),width=max(1,width),break_long_words=False,break_on_hyphens=False) or [""]

def _emit(lines,stream,width,color):
    for line in lines:
        print(_paint(line,color[0],color[1]),file=stream)

def _section(title,width,stream,color):
    for line in _wrap(title,width): print(_paint(line,color[0],color[1]),file=stream)
    print(_paint("─"*min(width, max(8,len(title))),color[2],color[1]),file=stream)

def render_header(stream=None,width=None):
    stream=stream or sys.stdout; width=width or terminal_width(stream)
    enabled=bool(getattr(stream,"isatty",lambda:False)()) and not os.environ.get("NO_COLOR")
    w=max(20,width)
    lines=[]
    lines += _wrap("JD NEXUS  |  ♓ PISCES EDITION",w)
    lines += _wrap("THINK BEYOND THE MARKET",w)
    lines += _wrap("><(((°>  JD  <°)))><",w)
    lines += _wrap("JD NEXUS MARKET INTELLIGENCE",w)
    for i,line in enumerate(lines):
        col=GOLD if "PISCES" in line or "><(" in line else (CYAN if i==0 else WHITE)
        print(_paint(line,col+BOLD if i==0 else col,enabled),file=stream)

def _quote_state(n, symbol):
    row=n.db.execute("SELECT bid,ask,updated_at,source FROM quotes WHERE symbol=?",(symbol,)).fetchone()
    if not row: return "UNAVAILABLE — no quote saved"
    try:
        ts=datetime.fromisoformat(row["updated_at"])
        age=(datetime.now(timezone.utc)-ts.astimezone(timezone.utc)).total_seconds()
    except (ValueError,TypeError): return "ERROR — invalid timestamp"
    freshness="STALE" if age < -5 or age > 1800 else "MANUAL"
    try: updated=ts.astimezone(timezone.utc).strftime("%m-%d %H:%M UTC")
    except (ValueError,OverflowError): updated="timestamp invalid"
    # Quotes have no reliable previous close; never infer price change/direction.
    return f"bid {row['bid']} / ask {row['ask']} | {freshness} | {updated}"

def render_dashboard(n, status, stream=None, width=None):
    stream=stream or sys.stdout; width=width or terminal_width(stream); inner=max(20,width-2)
    enabled=bool(getattr(stream,"isatty",lambda:False)()) and not os.environ.get("NO_COLOR")
    colors=(CYAN,enabled,BLUE)
    render_header(stream,width)
    _section("SYSTEM STATUS",inner,stream,colors)
    integrity = status.get("database_integrity", "not-checked")
    health = ("SQLite read error" if integrity not in ("ok", "not-checked", "não verificada")
              else "SQLite accessible; no full check")
    state_lines=["AI: DISCONNECTED (not integrated)","MARKET: MANUAL QUOTES ONLY",
                 "BROKER: NOT CONFIGURED","MODE: PAPER ONLY","HEALTH: "+health]
    for line in state_lines:
        for part in _wrap(line,inner): print(part,file=stream)
    _section("MARKET OVERVIEW | timeframe: n/a",inner,stream,colors)
    for symbol in ("EUR/USD","XAU/USD"):
        for part in _wrap(f"{symbol}: {_quote_state(n,symbol)}",inner): print(part,file=stream)
    for part in _wrap("change / direction: unavailable (no live feed)",inner): print(part,file=stream)
    s=n.summary()
    _section("PAPER ACCOUNT",inner,stream,colors)
    unrealized = ("unavailable (no quote)" if s['unpriced'] else f"{s['unrealized']:.2f} (estimate)")
    account=[f"Balance (paper): {s['equity']:.2f}",
             "Available capital: n/a (no margin model)",
             f"Daily P&L (UTC): {s['daily_pnl']:.2f}", f"Unrealized P&L: {unrealized}",
             f"Open positions: {s['open_count']} | Closed: {s['closed_count']}",
             f"Exposure: {s['exposure']:.2f} / {s['exposure_cap']:.2f}",
             f"Daily P&L remaining: {s['daily_remaining']:.2f} (realized only)"]
    for line in account:
        for part in _wrap(line,inner): print(part,file=stream)
    _section("AI AGENTS | all DISABLED",inner,stream,colors)
    for part in _wrap("Provider/model: not configured",inner): print(part,file=stream)
    for name in AGENT_NAMES:
        for part in _wrap(name+": DISABLED",inner): print(part,file=stream)

def render_menu(stream=None,width=None,selected=None):
    stream=stream or sys.stdout; width=width or terminal_width(stream); inner=max(20,width-2)
    enabled=bool(getattr(stream,"isatty",lambda:False)()) and not os.environ.get("NO_COLOR")
    for line in _wrap("OPERATIONS — existing actions preserved",inner):
        print(_paint(line,BOLD,enabled),file=stream)
    items=("1 Cotação manual","2 Abrir posição (paper)","3 Posições abertas","4 Histórico",
           "5 Fechar posição (paper)","6 Resumo da conta","7 Detalhes da posição",
           "8 Limites de risco","9 Exportar CSV/TXT","b Backup SQLite",
           "r Restaurar (confirmação)","a Diagnóstico local","h Ajuda","0 Sair")
    for item in items:
        key=item.split(" ",1)[0]
        chosen=selected is not None and key.lower()==str(selected).lower()
        prefix="> " if chosen else "  "
        color=CYAN if chosen else WHITE
        for index,line in enumerate(_wrap(item,inner-len(prefix))):
            lead=prefix if index==0 else "  "
            print(_paint(lead+line,color+BOLD if chosen else color,enabled),file=stream)
    for line in _wrap("Enter = continuar | dados manuais | ordens reais desativadas",inner):
        print(_paint(line,GRAY,enabled),file=stream)
