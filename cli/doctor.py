#!/usr/bin/env python3
"""Zero-third-party-dependency diagnostic for NEXUS and TradingAgents."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

OK, INFO, WARN, FAIL = "ok", "info", "warn", "fail"
MIN_FREE_BYTES = 2 * 1024**3
REQUIRED_ENGINE = {
    "pandas": "pkg install python-pandas (native Termux route is experimental)",
    "numpy": "pkg install python-numpy (native Termux route is experimental)",
    "cryptography": "pkg install python-cryptography (native Termux route is experimental)",
    "langchain_core": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "langgraph": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "langgraph.checkpoint.sqlite": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "rich": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "typer": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "questionary": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "dotenv": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "requests": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "markdown_it": "install engine dependencies (see TERMUX-INSTALACAO.md)",
    "typing_extensions": "install engine dependencies (see TERMUX-INSTALACAO.md)",
}
OPTIONAL_ENGINE = {
    "yfinance": "market-data extra; not verified for live Forex",
    "curl_cffi": "native/market extra; Android build uncertain",
    "stockstats": "optional indicator package",
    "langchain_openai": "OpenAI-compatible provider client",
    "langchain_anthropic": "Anthropic provider client",
    "langchain_google_genai": "Google provider client",
}
KEY_NAMES = (
    "DEEPSEEK_API_KEY", "GOOGLE_API_KEY", "OPENROUTER_API_KEY",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "GROQ_API_KEY",
    "MISTRAL_API_KEY", "MOONSHOT_API_KEY", "NVIDIA_API_KEY", "ZHIPU_API_KEY",
    "MINIMAX_API_KEY", "DASHSCOPE_API_KEY", "OPENAI_COMPATIBLE_API_KEY",
)

class Doctor:
    def __init__(self): self.items = []
    def add(self, level, name, detail, hint=""):
        self.items.append({"level":level,"name":name,"detail":detail,"hint":hint})
    @property
    def exit_code(self): return 1 if any(x["level"] == FAIL for x in self.items) else 0

def safe_find_spec(module):
    try: return importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, ValueError): return False

def run(profile="paper"):
    r=Doctor()
    is_termux=bool(os.environ.get("TERMUX_VERSION")) or Path('/data/data/com.termux/files/usr').is_dir()
    r.add(OK if is_termux else WARN,"Termux","detected" if is_termux else "not detected; Android compatibility cannot be inferred")
    version=sys.version_info
    if version >= (3,11): r.add(OK,"Python",sys.version.split()[0])
    elif profile=="engine": r.add(FAIL,"Python",sys.version.split()[0],"TradingAgents requires Python >=3.11")
    else: r.add(WARN,"Python",sys.version.split()[0],"NEXUS Paper uses standard library; engine requires >=3.11")
    r.add(OK,"SQLite",sqlite3.sqlite_version)
    try:
        free=shutil.disk_usage(Path.home()).free
        level=FAIL if profile=="engine" and free<MIN_FREE_BYTES else (WARN if free<MIN_FREE_BYTES else OK)
        r.add(level,"free storage",f"{free/1024**3:.2f} GiB", "engine route needs more space; do not proceed below 2 GiB" if level!=OK else "")
    except OSError as exc: r.add(WARN,"free storage",str(exc))
    r.add(INFO,"architecture",os.uname().machine if hasattr(os,"uname") else "unknown")
    for name in ("nexus_termux.py","nexus-start.sh","nexus_backup.py","pyproject.toml","cli/main.py"):
        exists=Path(name).exists()
        r.add(OK if exists else WARN,name,"present" if exists else "missing (wrong directory or incomplete clone)")
    for key in KEY_NAMES:
        if os.environ.get(key): r.add(INFO,"provider key","environment variable configured",key)
    # Report only that a local .env exists, never parse/print values.
    envfile=Path('.env')
    if envfile.is_file(): r.add(INFO,".env","file exists; contents not inspected")
    if profile=="engine":
        for mod,hint in REQUIRED_ENGINE.items():
            found=safe_find_spec(mod)
            r.add(OK if found else FAIL,mod,"import spec present" if found else "missing",hint if not found else "")
        for mod,hint in OPTIONAL_ENGINE.items():
            r.add(OK if safe_find_spec(mod) else WARN,mod,"import spec present" if safe_find_spec(mod) else "optional/missing",hint)
    return r

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=('paper','engine'),default='paper')
    p.add_argument('--json',action='store_true',help='emit JSON; never includes secret values')
    p.add_argument('--strict',action='store_true',help='return failure if warnings exist')
    args=p.parse_args(argv); report=run(args.profile)
    if args.json: print(json.dumps(report.items,indent=2))
    else:
        for item in report.items:
            tag={'ok':'[OK]','info':'[INFO]','warn':'[AVISO]','fail':'[FALHA]'}[item['level']]
            print(f"{tag} {item['name']}: {item['detail']}")
            if item['hint']: print('       '+item['hint'])
        print(f"Resumo: {len(report.items)} verificações; saída {report.exit_code}")
    if args.strict and any(x['level']==WARN for x in report.items): return 1
    return report.exit_code
if __name__=='__main__': raise SystemExit(main())
