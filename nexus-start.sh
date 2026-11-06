#!/data/data/com.termux/files/usr/bin/bash
# NEXUS manual paper demo only — does not install software or start the AI engine.
set -e
DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if ! command -v python >/dev/null 2>&1; then
  echo 'Python não encontrado. No Termux instala com: pkg install python' >&2
  exit 1
fi
exec python "$DIR/nexus_termux.py" "$@"
