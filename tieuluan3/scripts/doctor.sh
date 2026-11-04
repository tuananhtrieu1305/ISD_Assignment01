#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
if [[ ! -f "$task_runtime/ready.json" ]]; then
  echo 'No completed bootstrap. Run scripts/bootstrap.ps1 first.' >&2; exit 2
fi
task_backend=$("$task_runtime/.venv-torch/bin/python" -c \
  'import json,sys; print(json.load(open(sys.argv[1]))["keras_backend"])' "$task_runtime/ready.json")
"$task_runtime/.venv-torch/bin/python" scripts/doctor.py --runtime "$task_runtime" --keras-backend "$task_backend"
