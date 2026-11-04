[CmdletBinding()]
param(
 [ValidateSet('cpu','local_gpu')][string]$Mode = 'cpu',
 [ValidateRange(1024,65535)][int]$Port = 5000,
 [string]$Distribution = 'Ubuntu',
 [string]$CorsOrigins = 'http://localhost:5173,http://127.0.0.1:5173'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxRepo = (& wsl.exe --distribution $Distribution --exec wslpath -a $repo).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve WSL repository' }
& wsl.exe --distribution $Distribution --exec bash "$linuxRepo/scripts/run_api_v3.sh" $Mode $Port $CorsOrigins
if ($LASTEXITCODE -ne 0) { throw "API exited with code $LASTEXITCODE" }
