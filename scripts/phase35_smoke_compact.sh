#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
task_bundle="$("$task_runtime/.venv-torch/bin/python" -c 'import json;print(json.load(open("artifacts/manifests/phase35/compact_bundle_r2.json"))["root"])')"
case "$task_bundle" in /tmp/phase35_cpu_*) ;; *) exit 2 ;; esac
[[ -f "$task_bundle/bundle_manifest.json" ]] || exit 2
cd "$task_bundle"
export PYTHONPATH="$task_bundle" AI_SERVING_MODE=cpu
export AI_JOB_DB=/tmp/ai-paper-phase35-r2/jobs.db
export AI_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
export AI_TRUSTED_HOSTS=localhost,127.0.0.1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=''
exec "$task_runtime/.venv-torch/bin/python" -m gunicorn --bind 127.0.0.1:5000 \
 --workers 1 --threads 2 --timeout 120 'apps.api.v3.server:create_app()'
