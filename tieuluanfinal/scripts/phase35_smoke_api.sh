#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
export AI_SERVING_MODE=cpu
export AI_JOB_DB=/tmp/ai-paper-phase35-r1/jobs.db
export AI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
export AI_TRUSTED_HOSTS=localhost,127.0.0.1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=''
exec "$task_runtime/.venv-torch/bin/python" -m gunicorn --bind 127.0.0.1:5000 \
 --workers 1 --threads 2 --timeout 120 'apps.api.v3.server:create_app()'
