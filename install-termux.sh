#!/data/data/com.termux/files/usr/bin/bash
# NEXUS staged Termux setup. Paper panel is the safe default; engine install is experimental.
set -uo pipefail
DRY=0; UPDATE=0; INSTALL_ENGINE=0; WITH_MARKET=0; BUILD_TOOLS=0; SKIP_SYSTEM=0
LOG="${HOME}/nexus-install.log"
FAILED=(); WARNED=()
say(){ printf '%s\n' "$*"; }
warn(){ printf '[AVISO] %s\n' "$*"; WARNED+=("$*"); }
fail(){ printf '[FALHA] %s\n' "$*"; FAILED+=("$*"); }
die(){ printf '[ABORTA] %s\n' "$*" >&2; exit 1; }
run(){ printf '+ %s\n' "$*" >>"$LOG" 2>/dev/null || true; if [ "$DRY" -eq 1 ]; then printf '  (dry-run)'; printf ' %q' "$@"; printf '\n'; return 0; fi; "$@" >>"$LOG" 2>&1; }
usage(){ cat <<'EOF'
Usage: bash install-termux.sh [--dry-run] [--update] [--install-engine]
                              [--with-market] [--build-tools] [--skip-system]
Default installs/checks only prerequisites for the NEXUS standard-library Paper panel.
--install-engine is blocked until compatibility and dependency constraints are resolved.
--with-market is reserved for a future experimental market-data installation.
EOF
}
for arg in "$@"; do case "$arg" in
  --dry-run) DRY=1;; --update) UPDATE=1;; --install-engine) INSTALL_ENGINE=1;;
  --with-market) WITH_MARKET=1;; --build-tools) BUILD_TOOLS=1;; --skip-system) SKIP_SYSTEM=1;;
  -h|--help) usage; exit 0;; *) die "opção desconhecida: $arg";; esac; done
if [ "$DRY" -eq 1 ]; then LOG=/dev/null; else (umask 077; : >>"$LOG") 2>/dev/null || LOG=/dev/null; fi
say '===== NEXUS: SETUP TERMUX EM ETAPAS ====='
[ -n "${TERMUX_VERSION:-}" ] || [ -d /data/data/com.termux/files/usr ] || die 'Termux não detetado; este instalador não é para Linux/PC.'
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || die 'diretório do script inválido'
cd "$DIR" || die 'não foi possível entrar no diretório do repositório'
if [ "$WITH_MARKET" -eq 1 ] && [ "$INSTALL_ENGINE" -eq 0 ]; then die "--with-market requer --install-engine, que ainda está bloqueado"; fi
[ -f pyproject.toml ] || die 'pyproject.toml ausente: execute a partir do clone completo'
[ -f cli/doctor.py ] || die 'cli/doctor.py ausente'
[ -f nexus_termux.py ] || die 'nexus_termux.py ausente'
if ! command -v pkg >/dev/null 2>&1 && [ "$SKIP_SYSTEM" -eq 0 ]; then die 'pkg ausente; usa --skip-system se já instalaste Python/Git manualmente'; fi
if [ "$DRY" -eq 0 ]; then command -v python >/dev/null 2>&1 || { [ "$SKIP_SYSTEM" -eq 0 ] && run pkg install -y python; }; fi
command -v python >/dev/null 2>&1 || { [ "$DRY" -eq 1 ] && warn 'Python ainda ausente; dry-run não instalou pacotes' || die 'Python ausente'; }
if command -v python >/dev/null 2>&1; then python -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || die 'NEXUS Paper requer Python >=3.10'; fi
if [ "$SKIP_SYSTEM" -eq 0 ]; then
  [ "$UPDATE" -eq 0 ] || { say '-- atualizar índices/pacotes do Termux'; run pkg update -y && run pkg upgrade -y || warn 'atualização pkg falhou'; }
  for package in python git; do
    if ! command -v "$package" >/dev/null 2>&1; then run pkg install -y "$package" || fail "pkg install $package"; fi
  done
else warn 'pacotes do sistema ignorados'; fi
if [ "$INSTALL_ENGINE" -eq 1 ]; then
  warn 'Instalação do motor bloqueada: constraints Pandas conflitam com pyproject.toml; validar primeiro as dependências no Termux.'
  fail 'motor não instalado; consulta TERMUX-INSTALACAO.md'
else warn 'motor de IA não instalado; permanece separado do painel Paper'; fi
say '-- verificação NEXUS (sem dependências externas)'
if [ "$DRY" -eq 0 ] && command -v python >/dev/null 2>&1; then python -m cli.doctor --profile paper || fail 'doctor paper'; else say '  (dry-run) python -m cli.doctor --profile paper'; fi
say "Resumo: ${#FAILED[@]} falhas; ${#WARNED[@]} avisos; log: $LOG"
for item in "${FAILED[@]}"; do say "  - $item"; done
say 'Próximo passo: python nexus_termux.py --check; depois bash nexus-start.sh'
[ "$INSTALL_ENGINE" -eq 0 ] || say 'Rota engine não equivale a integração NEXUS/Forex nem foi validada no Android.'
[ "${#FAILED[@]}" -eq 0 ]
