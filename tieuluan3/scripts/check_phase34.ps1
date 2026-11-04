[CmdletBinding()]
param([string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'run_experiment.ps1') -Distribution $Distribution -Framework torch -Module scripts.verify_phase34 -ModuleArguments @('--stage','verify-only')
if ($LASTEXITCODE -ne 0) { throw 'Phase34 read-only verification failed' }
