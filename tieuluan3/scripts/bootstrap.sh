#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
if [[ "$(uname -r)" != *microsoft* ]]; then
  echo 'This bootstrap targets WSL2, not native Windows or a generic Linux host.' >&2; exit 2
fi
nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader
task_free=$(df -B1 --output=avail "$task_repo" | tail -1 | tr -d ' ')
task_min=$((20 * 1024 * 1024 * 1024))
if [[ -x "$task_runtime/.venv-torch/bin/python" ]]; then task_min=$((2 * 1024 * 1024 * 1024)); fi
if (( task_free < task_min )); then
  echo "Insufficient host storage: $task_free bytes available; $task_min required." >&2
  exit 2
fi
bash scripts/phase21_tools.sh
UV_PROJECT_ENVIRONMENT="$task_runtime/.venv-torch" "$task_uv" sync --locked --extra torch
mkdir -p artifacts/manifests/phase21
task_backend=tensorflow
if [[ -f "$task_runtime/ready.json" && "${AI_RETRY_TENSORFLOW:-0}" != 1 ]]; then
  task_backend=$("$task_runtime/.venv-torch/bin/python" -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["keras_backend"])' "$task_runtime/ready.json")
fi
if [[ "$task_backend" == tensorflow ]]; then
  UV_PROJECT_ENVIRONMENT="$task_runtime/.venv-keras" "$task_uv" sync --locked --extra keras
  "$task_runtime/.venv-keras/bin/python" scripts/tensorflow_libraries.py
  task_tf_libraries=$("$task_runtime/.venv-keras/bin/python" scripts/tensorflow_libraries.py --library-path)
  if ! LD_LIBRARY_PATH="$task_tf_libraries${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
    timeout 600 "$task_runtime/.venv-keras/bin/python" scripts/gpu_smoke.py \
    --framework tensorflow --device gpu --output artifacts/manifests/phase21/tensorflow-probe.json \
    > artifacts/manifests/phase21/tensorflow-probe.log 2>&1; then
  echo 'Official TensorFlow GPU probe failed; preserving evidence and selecting Keras 3/PyTorch.'
    task_backend=keras-torch
  fi
fi
if [[ "$task_backend" == keras-torch ]]; then
  "$task_runtime/.venv-keras/bin/python" scripts/tensorflow_libraries.py --cleanup
  UV_PROJECT_ENVIRONMENT="$task_runtime/.venv-keras" "$task_uv" sync --locked --extra keras-torch
fi
"$task_runtime/.venv-torch/bin/python" scripts/doctor.py --runtime "$task_runtime" --keras-backend "$task_backend"
"$task_runtime/.venv-torch/bin/python" scripts/register_kernels.py --runtime "$task_runtime" --keras-backend "$task_backend"
cp artifacts/manifests/environment.json "$task_runtime/ready.json"
echo 'Bootstrap and measured doctor checks passed.'
