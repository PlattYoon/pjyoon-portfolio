#!/usr/bin/env bash
# IDA — Jupyter AI in VS Code : environment setup
# Idempotent-ish. Safe to re-run. Tested on macOS + Ubuntu; on Windows use Git Bash or WSL.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> IDA setup starting in $ROOT"

# --- 1. Python venv ---------------------------------------------------------
PYTHON="${PYTHON:-python3}"
if [ ! -d ".venv" ]; then
  echo "==> Creating virtual environment (.venv)"
  "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip wheel >/dev/null

# --- 2. Core Python deps ----------------------------------------------------
# jupyter-ai v3 is required: the persona framework (BasePersona + entry-point
# personas in personas/) only exists in v3. v2's %%ai magics are gone; drop them.
echo "==> Installing Python dependencies"
pip install \
  "jupyterlab>=4.2" \
  "jupyter-ai>=3.0.0" \
  "jupyter-ai-persona-manager>=0.0.11" \
  "anthropic" \
  "openai" \
  "huggingface_hub" \
  "python-dotenv"

# --- 2b. IDA personas -------------------------------------------------------
# Register the four @IDA-* personas as native Jupyter AI personas (entry points).
if [ -f "personas/pyproject.toml" ]; then
  echo "==> Installing IDA personas (@IDA-Unblock / -Focus / -Nearby / -Checkin)"
  pip install ./personas
fi

# Optional: local model serving (Qwen3 / Llama via vLLM). Heavy — only on a GPU box.
if [ "${INSTALL_VLLM:-0}" = "1" ]; then
  echo "==> Installing vLLM for local model serving (GPU required)"
  pip install "vllm>=0.5.0"
fi

# --- 3. Env file ------------------------------------------------------------
if [ ! -f ".env" ]; then
  echo "==> No .env found — copying from .env.example (edit it before running dev.sh)"
  cp .env.example .env
fi

# --- 4. VS Code extension deps ---------------------------------------------
if command -v node >/dev/null 2>&1; then
  if [ -f "src/package.json" ]; then
    echo "==> Installing VS Code extension deps (npm)"
    (cd src && npm install)
  else
    echo "==> src/package.json not present yet — skipping npm install"
  fi
else
  echo "!!  Node.js not found. Install Node 18+ to build the VS Code extension."
fi

# --- 5. Verify Jupyter AI + personas are discoverable -----------------------
# v3: jupyter-ai is a SERVER extension and personas are entry points, so check
# both, not the old labextension list.
echo "==> Verifying jupyter-ai server extension is enabled"
jupyter server extension list 2>&1 | grep -i "jupyter_ai_persona_manager" || \
  echo "!!  jupyter_ai_persona_manager not enabled — check the jupyter-ai v3 install."

echo "==> Verifying the four IDA personas registered"
python - <<'PY'
from importlib.metadata import entry_points
ida = [e.name for e in entry_points(group="jupyter_ai.personas") if e.name.startswith("ida-")]
print("   found:", ", ".join(sorted(ida)) or "(none)")
assert len(ida) == 4, "expected 4 IDA personas; is personas/ installed?"
PY

cat <<'EOF'

==> Setup complete.

Next:
  1. Edit .env  (API keys and/or local model endpoint)
  2. bash scripts/dev.sh
  3. Open the workspace in VS Code and reload the window.

Model backend options (see docs/ARCHITECTURE.md §6):
  - API mode:   set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env
  - Local mode: run vLLM (INSTALL_VLLM=1 bash scripts/setup.sh) and set MODEL_BASE_URL
EOF
