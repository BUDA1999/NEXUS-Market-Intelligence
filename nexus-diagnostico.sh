#!/usr/bin/env bash
# Diagnóstico NEXUS: sem instalar dependências, ler segredos ou alterar ficheiros.
printf '%s\n' '===== NEXUS: DIAGNÓSTICO ====='
printf '\n[AMBIENTE]\n'
printf 'Sistema/arquitetura: '; uname -sm
printf 'Shell atual: %s\n' "${SHELL:-desconhecida}"
if [ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files/usr ]; then echo 'Termux: detetado'; else echo 'Termux: não detetado'; fi
printf '\n[PYTHON E GIT]\n'
if command -v python >/dev/null 2>&1; then
  python --version
  python -c 'import sys; print("Python >= 3.11:", "sim" if sys.version_info >= (3,11) else "não")'
else echo 'Python: não encontrado'; fi
if command -v git >/dev/null 2>&1; then git --version; else echo 'Git: não encontrado'; fi
printf '\n[MEMÓRIA E ESPAÇO]\n'
if command -v free >/dev/null 2>&1; then free -h; else echo 'free não disponível'; fi
df -h "$HOME"
printf '\n[REPOSITÓRIO]\n'
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P) || exit 1
if command -v git >/dev/null 2>&1 && git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf 'Commit: '; git -C "$repo" log -1 --format='%h %s' 2>/dev/null || true
  if git -C "$repo" diff --quiet && git -C "$repo" diff --cached --quiet; then echo 'Ficheiros acompanhados: sem alterações'; else echo 'Ficheiros acompanhados: com alterações'; fi
else echo 'Pasta não é um repositório Git ou git não está disponível.'; fi
printf '\n[MÓDULOS]\n'
for item in pyproject.toml tradingagents/agents tradingagents/graph cli/main.py nexus-banner.sh nexus; do
  if [ -e "$repo/$item" ]; then printf '[PRESENTE] %s\n' "$item"; else printf '[AUSENTE]  %s\n' "$item"; fi
done
printf '\nEste teste não confirma dependências, APIs, compatibilidade Termux nem funcionamento dos agentes.\n'
printf 'Nunca partilhes chaves API, tokens ou ficheiros .env.\n'
