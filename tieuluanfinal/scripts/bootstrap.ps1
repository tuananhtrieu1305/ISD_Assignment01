param([string]$Distribution = 'Ubuntu-24.04', [switch]$RetryTensorFlow)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxRepo = (& wsl.exe --distribution $Distribution --exec wslpath -a $repo).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve repository inside WSL.' }
if ($RetryTensorFlow) {
    & wsl.exe --distribution $Distribution --exec env AI_RETRY_TENSORFLOW=1 bash "$linuxRepo/scripts/bootstrap.sh"
} else {
    & wsl.exe --distribution $Distribution --exec bash "$linuxRepo/scripts/bootstrap.sh"
}
if ($LASTEXITCODE -ne 0) { throw 'Bootstrap failed. Read artifacts/manifests/phase21/*.log.' }
