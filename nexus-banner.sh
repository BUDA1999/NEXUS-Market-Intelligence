#!/usr/bin/env bash
# TradingAgents by Tauric Research — NEXUS interface customization.
# This banner checks files only; it does not start agents or connect APIs.
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
if [[ "${1:-}" == "--install" ]]; then
  rc="$HOME/.bashrc"
  touch "$rc"
  if ! grep -Fq '# NEXUS_TRADINGAGENTS_FOLDER' "$rc"; then
    cat >> "$rc" <<'HOOK'

# NEXUS_TRADINGAGENTS_FOLDER
__nexus_previous_dir=""
__nexus_folder_startup() {
  local repo="$HOME/TradingAgents"
  if [[ "$PWD" == "$repo" && "$__nexus_previous_dir" != "$PWD" ]]; then
    bash "$repo/nexus-banner.sh"
  fi
  __nexus_previous_dir="$PWD"
}
PROMPT_COMMAND="${PROMPT_COMMAND:+${PROMPT_COMMAND};}__nexus_folder_startup"
HOOK
    echo "NEXUS: configurado em $rc para $HOME/TradingAgents."
  else
    echo "NEXUS: configuração já presente em $rc."
  fi
  exit 0
fi
if [[ -t 1 && -n "${TERM:-}" ]]; then clear; fi
if [[ -t 1 ]]; then G=$'\033[1;32m'; C=$'\033[1;36m'; D=$'\033[0;90m'; R=$'\033[0m'; else G=''; C=''; D=''; R=''; fi
printf '%s\n' "${G}  ████████╗ █████╗" '  ╚══██╔══╝██╔══██╗' '     ██║   ███████║' '     ██║   ██╔══██║' '     ██║   ██║  ██║' "     ╚═╝   ╚═╝  ╚═╝${R}"
printf '\n%s\n' "${C}  TRADING AGENTS × N E X U S${R}" '  TAURIC RESEARCH FRAMEWORK' '  MULTI-AGENT LLM FINANCIAL TRADING FRAMEWORK' '  -------------------------------------------'
check() {
  if [[ -e "$repo/$1" ]]; then printf '  %s[FOUND]%s   %s\n' "$G" "$R" "$2"; else printf '  %s[MISSING]%s %s\n' "$D" "$R" "$2"; fi
}
printf '\n%s\n' "${C}  REPOSITORY MODULES${R}"
check 'tradingagents/agents' 'Agent modules'
check 'tradingagents/graph' 'LangGraph engine'
check 'tradingagents/default_config.py' 'Default config'
check 'cli/main.py' 'CLI interface'
check 'pyproject.toml' 'Python project'
printf '\n%s\n' "${C}  AGENT ARCHITECTURE (FILES ONLY)${R}"
check 'tradingagents/agents/analysts/fundamentals_analyst.py' 'Fundamentals analyst'
check 'tradingagents/agents/analysts/sentiment_analyst.py' 'Sentiment analyst'
check 'tradingagents/agents/analysts/news_analyst.py' 'News analyst'
check 'tradingagents/agents/analysts/market_analyst.py' 'Market / technical analyst'
check 'tradingagents/agents/researchers/bull_researcher.py' 'Bull researcher'
check 'tradingagents/agents/researchers/bear_researcher.py' 'Bear researcher'
check 'tradingagents/agents/managers/research_manager.py' 'Research manager'
check 'tradingagents/agents/trader/trader.py' 'Trader'
check 'tradingagents/agents/risk_mgmt' 'Risk management'
check 'tradingagents/agents/managers/portfolio_manager.py' 'Portfolio manager'
printf '\n%s\n' "${C}  NEXUS INTERFACE READY${R}" '  File checks only — agents and APIs not started.' "  $(date '+%d/%m/%Y %H:%M:%S')" '  Tauric Research × NEXUS customization' '  THINK BEYOND THE MARKET.'
