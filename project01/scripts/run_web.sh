#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$PROJECT_ROOT/environment/llm_v2/.venv/bin/python" && "$(uname -s)" == Linux* ]]; then
  exec "$PROJECT_ROOT/environment/llm_v2/.venv/bin/python" -B "$PROJECT_ROOT/scripts/serve_llm_v2.py" --port "${1:-8031}" --live
fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$PROJECT_ROOT/scripts/run_web.ps1")" -Port "${1:-8031}"
