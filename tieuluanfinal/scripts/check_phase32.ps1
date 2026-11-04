[CmdletBinding()]
param([string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'run_experiment.ps1'
& $runner -Distribution $Distribution -Framework torch -Module scripts.verify_phase32 -ModuleArguments @('--verify-only')
if ($LASTEXITCODE -ne 0) { throw 'Phase32 read-only verification failed' }
