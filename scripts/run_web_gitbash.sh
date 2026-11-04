#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s <A01|A02|A03|A04|A05|A06|tieuluan1|tieuluan2|tieuluan3|agent01|agent02> [port]\n' "$0" >&2
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 2
fi

project="$1"
case "$project" in
  A01|A02|A03|A04|A05|A06|tieuluan1|tieuluan2|tieuluan3|agent01|agent02) ;;
  *)
    printf 'Unknown project: %s\n' "$project" >&2
    usage
    exit 2
    ;;
esac

port="${2:-}"
if [[ -n "$port" && ! "$port" =~ ^[0-9]+$ ]]; then
  printf 'Port must be a number: %s\n' "$port" >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
runner_windows="$(cygpath -w "$script_dir/run_web.ps1")"

command=(
  powershell.exe
  -NoProfile
  -ExecutionPolicy Bypass
  -File "$runner_windows"
  -Project "$project"
)

if [[ -n "$port" ]]; then
  command+=(-Port "$port")
fi

exec "${command[@]}"
