#!/usr/bin/env bash
set -euo pipefail
docs35_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
docs35_runtime=/home/tuananh/.local/share/ai-term-paper-docs-v1
docs35_python="$docs35_runtime/.venv/bin/python"
[[ -x "$docs35_python" && -x "$docs35_runtime/bin/soffice" ]] || { echo 'Bootstrap the authorized document toolchain first' >&2; exit 2; }
export PATH="$docs35_runtime/bin:$docs35_runtime/.venv/bin:$PATH"
export PYTHONPATH="$docs35_repo"
export PYTHONDONTWRITEBYTECODE=1
export UV_CACHE_DIR="$docs35_runtime/uv-cache"
export RUFF_CACHE_DIR="$docs35_runtime/ruff-cache"
export FONTCONFIG_FILE="$docs35_runtime/fonts.conf"
export XDG_CACHE_HOME="$docs35_runtime/cache"
export LC_ALL=C.UTF-8
export SAL_USE_VCLPLUGIN=svp
export SAL_DISABLE_OPENCL=1
export CUDA_VISIBLE_DEVICES=''
unset KERAS_BACKEND LD_LIBRARY_PATH
cd "$docs35_repo"
docs35_mode=$1
docs35_target=$2
shift 2
case "$docs35_mode" in
    module) exec "$docs35_python" -B -m "$docs35_target" "$@" ;;
    file) exec "$docs35_python" -B "$docs35_target" "$@" ;;
    *) echo 'Unknown document command mode' >&2; exit 2 ;;
esac
