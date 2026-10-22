$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase28/experiment_lock.json') {
        & $taskRunner -Framework torch -Module scripts.release_phase28 -ModuleArguments @('--verify-only')
        & $taskRunner -Framework torch -Module scripts.verify_phase28
    }
    else {
        & $taskRunner -Framework torch -Module scripts.verify_phase28 -ModuleArguments @('--status')
        Write-Output 'Phase28 not released. No training, TEST evaluation or coverage writing was performed.'
    }
}
finally { Pop-Location }
