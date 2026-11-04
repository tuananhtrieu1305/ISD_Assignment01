#!/usr/bin/env bash
# Source this file; environments and cache share one ext4 filesystem for hardlinks.
set -euo pipefail
task_repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
task_runtime="${AI_RUNTIME_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/ai-term-paper-v3}"
export UV_CACHE_DIR="$task_runtime/cache"
export UV_PYTHON_INSTALL_DIR="$task_runtime/python"
export UV_LINK_MODE=hardlink
export RUFF_CACHE_DIR="$task_runtime/cache/ruff"
export PYTHONPATH="$task_repo${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export JUPYTER_PATH="$task_runtime/share/jupyter${JUPYTER_PATH:+:$JUPYTER_PATH}"
task_uv="$task_runtime/bin/uv"
cd "$task_repo"
