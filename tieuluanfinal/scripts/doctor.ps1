param([string]$Distribution = 'Ubuntu-24.04')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxRepo = (& wsl.exe --distribution $Distribution --exec wslpath -a $repo).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve repository inside WSL.' }
& wsl.exe --distribution $Distribution --exec bash "$linuxRepo/scripts/doctor.sh"
if ($LASTEXITCODE -ne 0) { throw 'Doctor failed. Read artifacts/manifests/environment.json.' }
