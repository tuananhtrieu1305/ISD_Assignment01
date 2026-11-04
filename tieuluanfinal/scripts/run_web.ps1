[CmdletBinding()]
param([int]$Port=8040)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$linux=(& wsl.exe -d Ubuntu --exec wslpath -a $repo.Replace('\','/')).Trim()
if($LASTEXITCODE -ne 0){throw 'Cannot resolve workspace in WSL Ubuntu'}
& wsl.exe -d Ubuntu --exec "$linux/project01/environment/llm_v2/.venv/bin/python" -B "$linux/tieuluanfinal/scripts/serve_final.py" --port $Port --live
