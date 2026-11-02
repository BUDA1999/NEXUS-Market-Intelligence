#!/data/data/com.termux/files/usr/bin/bash
# JD NEXUS — Pisces Edition
# Uso: bash nexus-banner.sh [--install|--remove]
# Identidade visual apenas: não inicia agentes nem operações.

if [ "${1:-}" = "--install" ]; then
  DEST="$HOME/.nexus-banner.sh"
  if [ "$0" != "$DEST" ]; then
    cp "$0" "$DEST" || { echo 'Erro ao copiar o banner.' >&2; exit 1; }
  fi
  chmod +x "$DEST" || exit 1
  touch "$HOME/.bashrc" || exit 1
  if ! grep -Fxq '# BEGIN JD NEXUS PISCES' "$HOME/.bashrc"; then
    cat >> "$HOME/.bashrc" <<'HOOK'

# BEGIN JD NEXUS PISCES
[ -x "$HOME/.nexus-banner.sh" ] && "$HOME/.nexus-banner.sh"
# END JD NEXUS PISCES
HOOK
  fi
  echo '✔ Instalado. Fecha e abre o Termux.'
  exit 0
fi
if [ "${1:-}" = "--remove" ]; then
  if [ -f "$HOME/.bashrc" ]; then
    tmp=$(mktemp "$HOME/.bashrc.nexus.XXXXXX") || exit 1
    awk '/^# BEGIN JD NEXUS PISCES$/ {skip=1; next} /^# END JD NEXUS PISCES$/ {skip=0; next} !skip {print}' "$HOME/.bashrc" > "$tmp" || { rm -f "$tmp"; exit 1; }
    cat "$tmp" > "$HOME/.bashrc" || { rm -f "$tmp"; exit 1; }
    rm -f "$tmp"
  fi
  rm -f "$HOME/.nexus-banner.sh"
  echo '✔ Removido.'
  exit 0
fi

R=$'\033[0m'
CY=$'\033[38;5;51m'
CY2=$'\033[38;5;45m'
CY3=$'\033[38;5;39m'
WH=$'\033[1;97m'
NV=$'\033[38;5;27m'
W=36

line() {
  local c="$1" t="$2" n l r
  n=${#t}; l=$(( (W - n) / 2 )); r=$(( W - n - l ))
  printf '%s║%s%*s%s%s%s%*s%s║%s\n' "$NV" "$R" "$l" "" "$c" "$t" "$R" "$r" "" "$NV" "$R"
}

if [ -t 1 ] && [ -n "${TERM:-}" ]; then clear; fi
printf '%s╔%s╗%s\n' "$NV" "$(printf '═%.0s' $(seq 1 $W))" "$R"
line "$CY"  '≈  ≈≈  ≈≈≈  ≈≈  ≈  ≈≈  ≈≈≈  ≈≈  ≈'
line ''     ''
line "$CY"  '     ██╗██████╗ '
line "$CY"  '     ██║██╔══██╗'
line "$CY2" '     ██║██║  ██║'
line "$CY2" '██   ██║██║  ██║'
line "$CY3" '╚█████╔╝██████╔╝'
line "$CY3" ' ╚════╝ ╚═════╝ '
line ''     ''
line "$WH"  '✦  ♓  ✦'
line ''     ''
line "$WH"  'P I S C E S  •  N E X U S'
line "$CY"  '──────────────────────'
line "$WH"  'THINK BEYOND THE MARKET'
line ''     ''
line "$CY"  '≈  ≈≈  ≈≈≈  ≈≈  ≈  ≈≈  ≈≈≈  ≈≈  ≈'
printf '%s╚%s╝%s\n' "$NV" "$(printf '═%.0s' $(seq 1 $W))" "$R"
