$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = Split-Path $PSScriptRoot -Parent
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase27/experiment_lock.json') {
        & $taskRunner -Framework torch -Module scripts.release_phase27 -ModuleArguments @('--verify-only')
        & $taskRunner -Framework torch -Module scripts.verify_phase27 -ModuleArguments @('--stage','full')
    }
    else {
        & $taskRunner -Framework torch -Module scripts.phase27_controller -ModuleArguments @('--stage','status')
        Write-Output 'Phase27 not released. This command does not train, evaluate TEST or replace evidence.'
    }
}
finally { Pop-Location }
