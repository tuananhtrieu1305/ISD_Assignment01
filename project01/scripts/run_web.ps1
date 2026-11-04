[CmdletBinding()]
param([int]$Port=8031)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$taskLinuxRoot=(& wsl.exe -d Ubuntu --exec wslpath -a $taskRoot.Replace('\','/')).Trim()
if($LASTEXITCODE -ne 0){throw 'Cannot resolve workspace in Ubuntu'}
& wsl.exe -d Ubuntu --exec "$taskLinuxRoot/project01/environment/llm_v2/.venv/bin/python" -B "$taskLinuxRoot/project01/scripts/serve_llm_v2.py" --port $Port --live
if($LASTEXITCODE -ne 0){throw "Web process failed: $LASTEXITCODE"}
