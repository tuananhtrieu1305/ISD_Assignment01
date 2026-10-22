param([string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
& "$PSScriptRoot/run_experiment.ps1" -Distribution $Distribution -Framework torch -Module scripts.release_phase31 -ModuleArguments @('--verify-only')
if ($LASTEXITCODE -ne 0) { throw 'Phase31 read-only verification failed' }
