param([switch]$ResumeTraining)
$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskPipelineLock = $null
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase28/experiment_lock.json') {
        & $taskRunner -Framework torch -Module scripts.release_phase28 -ModuleArguments @('--verify-only')
        & $taskRunner -Framework torch -Module scripts.verify_phase28
        return
    }
    $taskActivePath = 'artifacts/manifests/phase28/active_controller.json'
    if (Test-Path -LiteralPath $taskActivePath) {
        $taskActive = Get-Content -Raw -LiteralPath $taskActivePath | ConvertFrom-Json
        if ($null -ne $taskActive.pid) { throw 'Check the existing WSL controller PID before starting another queue/coverage writer.' }
    }
    if ($ResumeTraining) {
        & $taskRunner -Framework torch -Module scripts.phase28_r2 -ModuleArguments @('--stage','train')
    }
    $taskRelease = Get-Content -Raw -LiteralPath 'artifacts/manifests/phase28/release.json' | ConvertFrom-Json
    foreach ($taskEntry in $taskRelease.runs) {
        if (-not (Test-Path -LiteralPath ('artifacts/manifests/phase28/runs/' + $taskEntry.run_id + '/selection.json'))) {
            throw 'Validation matrix incomplete; resume its controller, do not write acceptance evidence yet.'
        }
    }
    $taskPipelineLock = [IO.File]::Open((Join-Path (Get-Location).Path 'artifacts/manifests/phase28/.acceptance_pipeline.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    & (Join-Path $taskRoot 'tests/powershell/test_phase28_entrypoints.ps1') -Evidence green
    & $taskRunner -Framework torch -Module coverage -ModuleArguments @('run','--append','--rcfile=experiments/configs/v3/phase28_coverage.ini','-m','pytest','tests/recurrent','-k','not keras','-q','--junitxml=artifacts/manifests/phase28/rnn-tests.xml')
    & $taskRunner -Framework keras -Module coverage -ModuleArguments @('run','--append','--rcfile=experiments/configs/v3/phase28_coverage.ini','-m','pytest','tests/recurrent/test_training.py::test_keras_gpu_recurrent_step_resume_and_canonical_adam','-q','--junitxml=artifacts/manifests/phase28/keras-final-tests.xml')
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @('tests/data','tests/contracts','tests/api','tests/test_environment_contract.py','tests/test_scratch_v2_smoke.py','-q','--junitxml=artifacts/manifests/phase28/regression-tests.xml')
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @('tests/test_phase26_preservation.py','-q','--junitxml=artifacts/manifests/phase28/preservation-tests.xml')
    & $taskRunner -Framework torch -Module scripts.phase28_r2 -ModuleArguments @('--stage','receipts','--method','scratch')
    & $taskRunner -Framework torch -Module scripts.phase28_r2 -ModuleArguments @('--stage','receipts','--method','pytorch')
    & $taskRunner -Framework keras -Module scripts.phase28_r2 -ModuleArguments @('--stage','receipts','--method','keras')
    & $taskRunner -Framework torch -Module scripts.verify_phase28
    & $taskRunner -Framework torch -Module scripts.export_phase28
    & $taskRunner -Framework torch -Module scripts.summarize_phase28
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @('tests/test_phase28_report_acceptance.py','-q','--junitxml=artifacts/manifests/phase28/report-tests.xml')
    & $taskRunner -Framework torch -Module coverage -ModuleArguments @('json','--rcfile=experiments/configs/v3/phase28_coverage.ini','-o','artifacts/manifests/phase28/final_coverage.json')
    Write-Output 'Validation-only pipeline finished. Inspect figures; record visual QA; seal report; update handoff report; then release_phase28 --lock. TEST remains Phase29.'
}
finally {
    if ($null -ne $taskPipelineLock) { $taskPipelineLock.Dispose() }
    Pop-Location
}
