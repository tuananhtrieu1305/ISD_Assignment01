#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
task_mode=${1:-cpu}
task_port=${2:-5000}
case "$task_mode" in cpu|local_gpu) ;; *) exit 2 ;; esac
[[ "$task_port" =~ ^[0-9]+$ ]] || exit 2
export AI_SERVING_MODE="$task_mode"
export AI_CORS_ORIGINS="${3:-http://localhost:5173,http://127.0.0.1:5173}"
export AI_JOB_DB="/tmp/ai-paper-v3/jobs.db"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
exec "$task_runtime/.venv-torch/bin/python" -m gunicorn --bind "127.0.0.1:$task_port" \
 --workers 1 --threads 2 --timeout 120 'apps.api.v3.server:create_app()'
