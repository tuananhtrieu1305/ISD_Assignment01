#!/usr/bin/env bash
# Versioned recovery only; never call the legacy bootstrap/doctor artifact writers.
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
[[ "$(id -un)" == tuananh ]] || { echo 'Unexpected WSL user' >&2; exit 2; }
[[ "$task_runtime" == /home/tuananh/.local/share/ai-term-paper-v3 ]] || { echo 'Unexpected recovery root' >&2; exit 2; }
[[ "$(sha256sum uv.lock | cut -d ' ' -f 1)" == b0c71fd20e221ed3456278e1916079c46ac206831a98dcf40d3b8f7a83477862 ]] || { echo 'Frozen dependency lock changed' >&2; exit 2; }
task_free=$(df -B1 --output=avail "$task_repo" | tail -1 | tr -d ' ')
(( task_free >= 20 * 1024 * 1024 * 1024 )) || { echo 'Host below 20 GiB recovery headroom' >&2; exit 2; }
export PATH="/usr/lib/wsl/lib:$PATH"
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
bash scripts/phase21_tools.sh
UV_PROJECT_ENVIRONMENT="$task_runtime/.venv-torch" "$task_uv" sync --locked --extra torch
UV_PROJECT_ENVIRONMENT="$task_runtime/.venv-keras" "$task_uv" sync --locked --extra keras
"$task_runtime/.venv-keras/bin/python" scripts/tensorflow_libraries.py
"$task_runtime/.venv-torch/bin/python" -m scripts.phase29_runtime_recovery_r1 --runtime "$task_runtime"
