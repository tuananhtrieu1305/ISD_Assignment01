#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "$(uname -s)" == Linux* ]]; then
  exec "$TASK_ROOT/project01/environment/llm_v2/.venv/bin/python" -B "$TASK_ROOT/tieuluanfinal/scripts/serve_final.py" --port "${1:-8040}" --live
fi
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$TASK_ROOT/tieuluanfinal/scripts/run_web.ps1")" -Port "${1:-8040}"
