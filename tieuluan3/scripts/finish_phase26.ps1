param([switch]$EvaluateTest)
$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskBase = 'artifacts/manifests/phase26/revisions/r2'
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath "$taskBase/experiment_lock.json") {
        & $taskRunner -Framework torch -Module scripts.verify_phase26_roundtrip_v1
        return
    }
    if (-not (Test-Path -LiteralPath "$taskBase/pretest_verification.json")) {
        # Append after training, sequential writers only. Never overwrite test evidence after sealing.
        & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
            'tests/ch02_ml','--ignore=tests/ch02_ml/test_native_keras.py','-q','--cov','--cov-append',
            '--cov-config=experiments/configs/v3/phase26_coverage.ini','--cov-fail-under=0',
            "--cov-report=json:$taskBase/coverage_combined.json","--junitxml=$taskBase/unit-torch.xml"
        )
        & $taskRunner -Framework keras -Module pytest -ModuleArguments @(
            'tests/ch02_ml/test_native_keras.py','-q','--cov','--cov-append',
            '--cov-config=experiments/configs/v3/phase26_coverage.ini','--cov-fail-under=0',
            "--cov-report=json:$taskBase/coverage_combined.json","--junitxml=$taskBase/unit-keras.xml"
        )
        & $taskRunner -Framework torch -Module scripts.verify_phase26_roundtrip_v1 -ModuleArguments @('--pretest')
    }
    if ($EvaluateTest) {
        & $taskRunner -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','lock-test')
        & $taskRunner -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','test')
        & $taskRunner -Framework torch -Module coverage -ModuleArguments @(
            'json','--rcfile=experiments/configs/v3/phase26_coverage.ini',
            '-o',"$taskBase/coverage_final.json"
        )
        & $taskRunner -Framework torch -Module scripts.summarize_phase26
    }
}
finally { Pop-Location }
