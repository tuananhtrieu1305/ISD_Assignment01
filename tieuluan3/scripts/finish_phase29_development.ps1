param([switch]$Watch, [string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskLock = $null
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase29/experiment_lock.json') { throw 'Released Phase29: audit-only, never overwrite evidence.' }
    $taskLock = [IO.File]::Open((Join-Path $taskRoot 'artifacts/manifests/phase29/.development_pipeline.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    Write-Output ("Development pipeline watcher PID=" + $PID + "; waits for108 selections/controller exit; NO TEST.")
    do {
        $taskActive = Get-Content -Raw -Encoding UTF8 artifacts/manifests/phase29/active_controller.json | ConvertFrom-Json
        if ($null -eq $taskActive.pid) { break }
        if (-not $Watch) { throw 'Queue/coverage writer active; use -Watch or wait.' }
        Start-Sleep -Seconds 30
    } while ($true)
    if ($taskActive.status -ne 'finished') { throw 'Training controller failed; inspect its log. Do not blindly restart or begin acceptance.' }
    $taskRelease = Get-Content -Raw -Encoding UTF8 artifacts/manifests/phase29/release.json | ConvertFrom-Json
    if ($taskRelease.runs.Count -ne 108) { throw 'Expected108 LSTM declaration.' }
    foreach ($taskEntry in $taskRelease.runs) {
        if (-not (Test-Path -LiteralPath ('artifacts/manifests/phase29/runs/' + $taskEntry.run_id + '/selection.json'))) { throw 'Incomplete selection matrix.' }
    }
    if (Test-Path -LiteralPath 'artifacts/manifests/phase29/pretest_verification.json') { throw 'Pretest evidence is sealed; inspect/reuse it, do not overwrite.' }
    & $taskRunner -Distribution $Distribution -Framework torch -Module coverage -ModuleArguments @('run','--append','--rcfile=experiments/configs/v3/phase29_coverage.ini','-m','pytest','tests/lstm29','-k','not keras_lstm_gpu','-q','--junitxml=artifacts/manifests/phase29/development-torch-tests.xml')
    & $taskRunner -Distribution $Distribution -Framework keras -Module coverage -ModuleArguments @('run','--append','--rcfile=experiments/configs/v3/phase29_coverage.ini','-m','pytest','tests/lstm29/test_lstm_core.py::test_keras_lstm_gpu_graph_resume_and_adam','-q','--junitxml=artifacts/manifests/phase29/development-keras-tests.xml')
    & $taskRunner -Distribution $Distribution -Framework torch -Module pytest -ModuleArguments @('tests/data','tests/contracts','tests/api','tests/test_environment_contract.py','tests/test_scratch_v2_smoke.py','-q','--junitxml=artifacts/manifests/phase29/development-regression-tests.xml')
    & $taskRunner -Distribution $Distribution -Framework torch -Module pytest -ModuleArguments @('tests/test_phase26_preservation.py','-q','--junitxml=artifacts/manifests/phase29/development-preservation-tests.xml')
    & $taskRunner -Distribution $Distribution -Framework torch -Module scripts.phase29_receipts -ModuleArguments @('--method','scratch')
    & $taskRunner -Distribution $Distribution -Framework torch -Module scripts.phase29_receipts -ModuleArguments @('--method','pytorch')
    & $taskRunner -Distribution $Distribution -Framework keras -Module scripts.phase29_receipts -ModuleArguments @('--method','keras')
    & $taskRunner -Distribution $Distribution -Framework torch -Module scripts.verify_phase29_validation
    & $taskRunner -Distribution $Distribution -Framework torch -Module coverage -ModuleArguments @('json','--rcfile=experiments/configs/v3/phase29_coverage.ini','-o','artifacts/manifests/phase29/development_coverage.json')
    & $taskRunner -Distribution $Distribution -Framework torch -Module scripts.prepare_phase29_pretest
    Write-Output 'Development checks/pretest proof complete. NO TEST was opened. Inspect proof, then explicitly lock-test/test; report/visual QA/release still required.'
}
finally {
    if ($null -ne $taskLock) { $taskLock.Dispose() }
    Pop-Location
}
