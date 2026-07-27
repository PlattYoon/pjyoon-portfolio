#!/usr/bin/env bash
# IDA — dev loop: Jupyter server (with Jupyter AI) + extension host hints.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
[ -d ".venv" ] && source .venv/bin/activate

if [ -f ".env" ]; then
  set -a; # shellcheck disable=SC1091
  source .env; set +a
fi

echo "==> Starting JupyterLab with Jupyter AI on http://localhost:8888"
echo "    (Open VS Code separately and connect to this kernel/server.)"
jupyter lab \
  --no-browser \
  --ServerApp.token="${JUPYTER_TOKEN:-ida-dev}" \
  --port="${JUPYTER_PORT:-8888}"
