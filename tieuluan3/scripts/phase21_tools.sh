#!/usr/bin/env bash
set -euo pipefail

task_runtime="${AI_RUNTIME_ROOT:-${XDG_DATA_HOME:-$HOME/.local/share}/ai-term-paper-v3}"
task_uv_version=0.13.1
task_tools="$task_runtime/tools"
mkdir -p "$task_tools" "$task_runtime/bin" "$task_runtime/cache" "$task_runtime/python"
if [[ ! -x "$task_runtime/bin/uv" ]]; then
    task_archive=uv-x86_64-unknown-linux-gnu.tar.gz
    curl --fail --location --retry 3 --output "$task_tools/$task_archive" \
        "https://github.com/astral-sh/uv/releases/download/$task_uv_version/$task_archive"
    curl --fail --location --retry 3 --output "$task_tools/$task_archive.sha256" \
        "https://github.com/astral-sh/uv/releases/download/$task_uv_version/$task_archive.sha256"
    (cd "$task_tools" && sha256sum --check "$task_archive.sha256")
    tar -xzf "$task_tools/$task_archive" -C "$task_tools"
    install -m 755 "$task_tools/uv-x86_64-unknown-linux-gnu/uv" "$task_runtime/bin/uv"
fi
export UV_CACHE_DIR="$task_runtime/cache"
export UV_PYTHON_INSTALL_DIR="$task_runtime/python"
"$task_runtime/bin/uv" --version
[[ "$("$task_runtime/bin/uv" --version)" == "uv $task_uv_version"* ]] || {
    echo 'Unexpected uv version; refusing to silently change the resolver.' >&2; exit 2;
}
"$task_runtime/bin/uv" python install 3.11.17
"$task_runtime/bin/uv" python find 3.11.17
