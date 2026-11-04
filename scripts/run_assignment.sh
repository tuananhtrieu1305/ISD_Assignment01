#!/usr/bin/env bash
set -euo pipefail
task_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_framework=$1
shift
task_runtime="${AI_RUNTIME_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/ai-term-paper-v3}"
if [[ "$task_framework" == auto ]]; then
  task_project=""
  task_notebook=""
  task_previous=""
  for task_arg in "$@"; do
    if [[ "$task_previous" == --project ]]; then task_project="$task_arg"; fi
    if [[ "$task_previous" == --notebook ]]; then task_notebook="$task_arg"; fi
    task_previous="$task_arg"
  done
  case "$task_project" in A01|A02|A03|A04|A05|A06|tieuluan1|tieuluan2|tieuluan3|agent01|agent02) ;; *) echo 'Unknown project' >&2; exit 2 ;; esac
  task_framework=$("$task_runtime/.venv-torch/bin/python" -B -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next((r["framework"] for r in d["notebooks"] if r["path"]==sys.argv[2]),d["default_framework"]))' "$task_repo/$task_project/project.json" "$task_notebook")
fi
case "$task_framework" in
  keras)
    task_python="$task_runtime/.venv-keras/bin/python"
    export KERAS_BACKEND=tensorflow
    task_libs=$("$task_python" -B -c 'import sys; from pathlib import Path; site=Path(sys.prefix)/f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"; print(":".join(str(p) for p in sorted((site/"nvidia").glob("*/lib"))))')
    export LD_LIBRARY_PATH="$task_libs${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    ;;
  torch|scratch)
    task_python="$task_runtime/.venv-torch/bin/python"
    export KERAS_BACKEND=torch
    ;;
  *) echo 'Framework must be torch, scratch or keras' >&2; exit 2 ;;
esac
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
exec "$task_python" -B "$task_repo/scripts/run_assignment.py" --framework "$task_framework" "$@"
