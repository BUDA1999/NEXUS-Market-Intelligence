"""Local, read-only NEXUS readiness report; no connections or secret values."""
from __future__ import annotations
import importlib.util
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

# Presence of a key is not evidence that a provider is reachable or usable.
KEYS = {"OpenAI":"OPENAI_API_KEY", "Anthropic":"ANTHROPIC_API_KEY",
        "Google Gemini":"GOOGLE_API_KEY", "DeepSeek":"DEEPSEEK_API_KEY",
        "Qwen":"DASHSCOPE_API_KEY", "OpenRouter":"OPENROUTER_API_KEY", "Groq":"GROQ_API_KEY"}
MODULES = ("langgraph", "langchain_core", "pandas", "dotenv")

def has_spec(name):
    try: return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError): return False

def inspect_status(db_path):
    db=Path(db_path).expanduser()
    integrity="não verificada"
    if db.is_file():
        try:
            with closing(sqlite3.connect(db.resolve().as_uri()+"?mode=ro",uri=True,timeout=1)) as c:
                integrity=c.execute("PRAGMA integrity_check").fetchone()[0]
        except (sqlite3.Error,OSError) as exc:
            integrity="erro: "+type(exc).__name__
    return {
        "python":sys.version.split()[0],
        "engine_modules":{name:has_spec(name) for name in MODULES},
        "keys":{name:bool(os.environ.get(env,"").strip()) for name,env in KEYS.items()},
        "database_exists":db.is_file(), "database_integrity":integrity,
        "ai":"não integrado ao painel", "market":"cotações manuais; feed ao vivo não integrado",
        "automation":"não implementada", "broker":"não conectado", "real_orders":"desativadas",
        "connectivity":"não verificada; nenhum pedido de rede efetuado",
    }

def format_status(s):
    lines=["=== JD NEXUS — ESTADO LOCAL ===", f"Python: {s['python']}",
           "Módulos do motor detetados (não prova instalação completa):"]
    lines += [f"  {k}: {'presente' if v else 'ausente'}" for k,v in s['engine_modules'].items()]
    lines += ["Chaves detetadas no ambiente atual (valores ocultos; .env não verificado):"]
    lines += [f"  {k}: {'configurada' if v else 'não detetada'}" for k,v in s['keys'].items()]
    lines += [f"IA: {s['ai']}",f"Mercado: {s['market']}",f"Automação: {s['automation']}",
              f"Corretora: {s['broker']}",f"Ordens reais: {s['real_orders']}",
              f"Conectividade: {s['connectivity']}",
              f"SQLite: {'presente' if s['database_exists'] else 'ausente'}; integridade: {s['database_integrity']}"]
    return '\n'.join(lines)
