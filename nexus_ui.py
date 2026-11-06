"""Framed, compact JD NEXUS dashboard; standard-library-only presentation."""
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
    try: width=shutil.get_terminal_size(fallback=(40,24)).columns
    except OSError: width=40
    return max(24,min(60,width))

def _color(text, code, stream):
    return f"{code}{text}{RESET}" if getattr(stream,"isatty",lambda:False)() and not os.environ.get("NO_COLOR") else text

def _wrap(text,width):
    return textwrap.wrap(str(text),max(1,width),break_long_words=False,break_on_hyphens=False) or [""]

def _row(text,width,stream,code=WHITE):
    inside=width-4
    for part in _wrap(text,inside):
        # Frame is always exactly width characters; no terminal control chars included in sizing.
        print(_color("║ ",CYAN,stream)+_color(part.ljust(inside),code,stream)+_color(" ║",CYAN,stream),file=stream)

def _top(width,stream): print(_color("╔"+"═"*(width-2)+"╗",CYAN,stream),file=stream)
def _rule(width,stream): print(_color("╠"+"═"*(width-2)+"╣",CYAN,stream),file=stream)
def _bottom(width,stream): print(_color("╚"+"═"*(width-2)+"╝",CYAN,stream),file=stream)
def _section(title,width,stream): _rule(width,stream); _row(title,width,stream,CYAN+BOLD)

def render_header(stream=None,width=None):
    stream=stream or sys.stdout;width=width or terminal_width(stream)
    _top(width,stream)
    art=("      ██╗ ██████╗", "      ██║ ██╔══██╗", "      ██║ ██║  ██║",
         " ██   ██║ ██║  ██║", " ╚█████╔╝ ██████╔╝", "  ╚════╝  ╚═════╝")
    for line in art: _row(line,width,stream,CYAN+BOLD)
    _row("",width,stream)
    _row("♓ PISCES EDITION",width,stream,GOLD+BOLD)
    _row("JD NEXUS TERMINAL",width,stream,WHITE+BOLD)
    _row("THINK BEYOND THE MARKET",width,stream,CYAN)
    _row("♓ PISCES | TRADER: JADILSON T.",width,stream,GOLD)
    _row("><(((°> PEIXE AZUL",width,stream,BLUE)
    _row("<°)))>< PEIXE DOURADO",width,stream,GOLD)
    _rule(width,stream)

def _quote(n,symbol):
    row=n.db.execute("SELECT bid,ask,updated_at FROM quotes WHERE symbol=?",(symbol,)).fetchone()
    if not row:return "INDISPONÍVEL — sem cotação manual"
    try:
        ts=datetime.fromisoformat(row["updated_at"])
        age=(datetime.now(timezone.utc)-ts.astimezone(timezone.utc)).total_seconds()
    except (ValueError,TypeError):return "ERRO — horário inválido"
    state="MANUAL ANTIGA" if age< -5 or age>1800 else "MANUAL"
    try: updated=ts.astimezone(timezone.utc).strftime("%d/%m %H:%M UTC")
    except (ValueError,OverflowError):updated="hora inválida"
    return f"{row['bid']} / {row['ask']} | {state} | {updated}"

def render_dashboard(n,status,stream=None,width=None):
    stream=stream or sys.stdout;width=width or terminal_width(stream);width=max(24,min(60,width))
    render_header(stream,width)
    _row("STATUS: PAPER LOCAL | COTAÇÕES: MANUAIS",width,stream,GOLD+BOLD)
    _row("IA: NÃO LIGADA | BROKER: NÃO CONFIGURADO",width,stream)
    _row("MODO: PAPER — ORDENS REAIS DESATIVADAS",width,stream,WHITE+BOLD)
    integrity=status.get("database_integrity","not-checked")
    health=("ERRO SQLite" if integrity not in ("ok","not-checked","não verificada")
            else "BASE OK" if status.get("database_exists") else "BASE NOVA")
    _row(f"SISTEMA: {health} | REDE NÃO VERIFICADA",width,stream)
    _section("MERCADO | timeframe: n/a",width,stream)
    _row("EUR/USD: "+_quote(n,"EUR/USD"),width,stream)
    _row("XAU/USD: "+_quote(n,"XAU/USD"),width,stream)
    _row("Variação/direção: indisponível sem feed real",width,stream,GRAY)
    s=n.summary()
    _section("CONTA PAPER",width,stream)
    _row(f"CAPITAL: {fmt_money(s['equity'])} | P&L UTC: {fmt_money(s['daily_pnl'])}",width,stream,WHITE+BOLD)
    unreal="sem cotação" if s["unpriced"] else fmt_money(s["unrealized"])+" est."
    _row(f"NÃO REALIZADO: {unreal} | ABERTAS: {s['open_count']}",width,stream)
    _row(f"EXPOSIÇÃO: {fmt_money(s['exposure'])} / teto {fmt_money(s['exposure_cap'])}",width,stream)
    _section("AGENTES IA | DESATIVADOS — não integrados",width,stream)
    _row("Fornecedor/modelo: não configurados no painel",width,stream)
    # Compact agent status, no fake RUNNING/COMPLETED states.
    for name in AGENT_NAMES: _row(name+": DISABLED",width,stream)

def render_menu(stream=None,width=None,selected=None):
    stream=stream or sys.stdout;width=width or terminal_width(stream);width=max(24,min(60,width))
    _section("MENU DE OPÇÕES",width,stream)
    items=("[1] Cotação manual","[2] Nova posição PAPER","[3] Posições abertas","[4] Histórico",
           "[5] Fechar posição PAPER","[6] Resumo da conta","[7] Detalhes da posição",
           "[8] Limites de risco","[9] Exportar CSV/TXT","[b] Backup SQLite",
           "[r] Restaurar backup","[a] Diagnóstico local","[h] Ajuda","[0] Sair")
    inside=width-4
    if inside>=52:
        for i in range(0,len(items),2):
            a=items[i]; b=items[i+1] if i+1<len(items) else ""
            a=(">" if selected and a.startswith(f"[{selected}]") else " ")+a
            b=(">" if selected and b.startswith(f"[{selected}]") else " ")+b if b else ""
            _row(f"{a:<26} {b}",width,stream)
    else:
        for item in items:
            chosen=bool(selected and item.startswith(f"[{selected}]"))
            _row(("> " if chosen else "")+item,width,stream,CYAN+BOLD if chosen else WHITE)
    _row("ENTER: continuar | PAPER | sem broker/feed",width,stream,GRAY)
    _bottom(width,stream)

def fmt_money(value): return f"${Decimal(value):,.2f}"
