#!/usr/bin/env bash
# One-time secure OpenRouter setup for the Debian/proot TradingAgents environment.
set -euo pipefail
REPO_DIR="${NEXUS_REPO_DIR:-$HOME/NEXUS-Market-Intelligence}"
CONFIG_DIR="${NEXUS_CONFIG_DIR:-$HOME/.config/nexus}"
KEY_FILE="$CONFIG_DIR/openrouter.env"
MODEL_FILE="$CONFIG_DIR/models.env"
BASHRC="${NEXUS_BASHRC:-$HOME/.bashrc}"

if [[ ! -t 0 ]]; then
  echo 'Executa este instalador numa sessão interativa do Debian; a chave será ocultada.' >&2
  exit 2
fi
if [[ ! -x "$REPO_DIR/.venv/bin/tradingagents" ]]; then
  echo "Não encontrei o motor instalado em $REPO_DIR/.venv/bin/tradingagents" >&2
  echo 'Confirma que estás no Debian/proot e que instalaste o projeto com pip.' >&2
  exit 2
fi

printf 'Chave OpenRouter (entrada oculta): ' >&2
IFS= read -r -s OPENROUTER_API_KEY
printf '\n' >&2
if [[ ! "$OPENROUTER_API_KEY" =~ ^sk-or-v1-[A-Za-z0-9_-]+$ ]]; then
  unset OPENROUTER_API_KEY
  echo 'Formato de chave inválido; nenhuma configuração foi alterada.' >&2
  exit 2
fi

umask 077
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
if [[ -e "$KEY_FILE" ]]; then
  cp -p "$KEY_FILE" "$KEY_FILE.backup.$(date +%Y%m%d%H%M%S)"
fi
TMP_FILE="$KEY_FILE.tmp.$$"
printf 'OPENROUTER_API_KEY=%s\n' "$OPENROUTER_API_KEY" > "$TMP_FILE"
chmod 600 "$TMP_FILE"
mv -f "$TMP_FILE" "$KEY_FILE"
unset OPENROUTER_API_KEY

cat > "$MODEL_FILE" <<'EOF'
export TRADINGAGENTS_LLM_PROVIDER=openrouter
export TRADINGAGENTS_QUICK_THINK_PROVIDER=openrouter
export TRADINGAGENTS_DEEP_THINK_PROVIDER=openrouter
export TRADINGAGENTS_QUICK_THINK_LLM=baidu/ernie-5.5-flash-preview:free
export TRADINGAGENTS_DEEP_THINK_LLM=baidu/ernie-5.5-flash-preview:free
export TRADINGAGENTS_OUTPUT_LANGUAGE=Portuguese
EOF
chmod 600 "$MODEL_FILE"

START_MARKER='# NEXUS_MODELS_ENV_START'
if ! grep -Fq "$START_MARKER" "$BASHRC" 2>/dev/null; then
  touch "$BASHRC"
  cat >> "$BASHRC" <<'EOF'

# NEXUS_MODELS_ENV_START
if [ -r "$HOME/.config/nexus/models.env" ]; then
  . "$HOME/.config/nexus/models.env"
fi
# NEXUS_MODELS_ENV_END
EOF
fi

cat <<EOF
Configuração OpenRouter preparada.
Chave guardada fora do repositório em $KEY_FILE (modo 600); não foi impressa.
Fornecedor/modelo guardados em $MODEL_FILE e carregados em novas sessões.
Nenhuma chamada a modelo foi feita. Fecha e reabre Debian para aplicar a configuração.
Para arrancar o motor: bash "$REPO_DIR/scripts/nexus-engine-start.sh"
Isto não liga o motor ao painel Paper nem executa operações de trading.
EOF
