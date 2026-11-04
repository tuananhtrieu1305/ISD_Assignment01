#!/usr/bin/env bash
source "$(dirname -- "${BASH_SOURCE[0]}")/runtime_common.sh"
if (( $# < 2 )); then
  echo 'Usage: bash scripts/run_experiment.sh <scratch|keras|torch> <python.module> [args...]' >&2
  exit 2
fi
task_framework=$1
task_module=$2
shift 2
case "$task_framework" in
  scratch|torch) task_env=torch; export KERAS_BACKEND=torch ;;
  keras)
    task_env=keras
    task_backend=$("$task_runtime/.venv-torch/bin/python" -c \
      'import json,sys; print(json.load(open(sys.argv[1]))["keras_backend"])' "$task_runtime/ready.json")
    export KERAS_BACKEND=tensorflow
    if [[ "$task_backend" == keras-torch ]]; then export KERAS_BACKEND=torch; fi
    if [[ "$task_backend" == tensorflow ]]; then
      task_tf_libraries=$("$task_runtime/.venv-keras/bin/python" scripts/tensorflow_libraries.py --library-path)
      export LD_LIBRARY_PATH="$task_tf_libraries${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    fi
    ;;
  *) echo "Unknown framework: $task_framework" >&2; exit 2 ;;
esac
exec "$task_runtime/.venv-$task_env/bin/python" -m "$task_module" "$@"
