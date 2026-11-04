[CmdletBinding(PositionalBinding=$false)]
param(
    [Parameter(Mandatory=$true, Position=0)][ValidateSet('scratch', 'keras', 'torch')][string]$Framework,
    [Parameter(Mandatory=$true, Position=1)][string]$Module,
    [string]$Distribution = 'Ubuntu-24.04',
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$ModuleArguments
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$linuxRepo = (& wsl.exe --distribution $Distribution --exec wslpath -a $repo).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve repository inside WSL.' }
& wsl.exe --distribution $Distribution --exec bash "$linuxRepo/scripts/run_experiment.sh" $Framework $Module @ModuleArguments
if ($LASTEXITCODE -ne 0) { throw "Module exited with code $LASTEXITCODE" }
