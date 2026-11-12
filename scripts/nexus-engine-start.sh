#!/usr/bin/env bash
# Start TradingAgents with private local OpenRouter config; no order execution.
set -euo pipefail
REPO_DIR="${NEXUS_REPO_DIR:-$HOME/NEXUS-Market-Intelligence}"
KEY_FILE="${NEXUS_CONFIG_DIR:-$HOME/.config/nexus}/openrouter.env"
MODEL_FILE="${NEXUS_CONFIG_DIR:-$HOME/.config/nexus}/models.env"
if [[ ! -r "$KEY_FILE" || ! -r "$MODEL_FILE" ]]; then
  echo 'OpenRouter ainda não configurado. Executa primeiro: bash scripts/setup-openrouter.sh' >&2
  exit 2
fi
if [[ ! -x "$REPO_DIR/.venv/bin/tradingagents" ]]; then
  echo "Motor TradingAgents não encontrado em $REPO_DIR/.venv/bin/tradingagents" >&2
  exit 2
fi
set -a
# shellcheck disable=SC1090
. "$KEY_FILE"
# shellcheck disable=SC1090
. "$MODEL_FILE"
set +a
cd "$REPO_DIR"
exec "$REPO_DIR/.venv/bin/tradingagents" "$@"
