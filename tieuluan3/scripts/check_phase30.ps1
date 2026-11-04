param([string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $taskRoot
try {
    & (Join-Path $PSScriptRoot 'run_experiment.ps1') -Distribution $Distribution -Framework torch -Module scripts.verify_phase30 -ModuleArguments @('--verify-only')
}
finally { Pop-Location }
