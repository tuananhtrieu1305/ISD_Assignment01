param([switch]$EvaluateTest)
$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = Split-Path $PSScriptRoot -Parent
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase27/experiment_lock.json') {
        & $taskRunner -Framework torch -Module scripts.verify_phase27 -ModuleArguments @('--stage','full')
        & $taskRunner -Framework torch -Module scripts.release_phase27 -ModuleArguments @('--verify-only')
        return
    }
    if (-not (Test-Path -LiteralPath 'artifacts/manifests/phase27/pretest_verification.json')) {
        & $taskRunner -Framework torch -Module scripts.phase27_controller -ModuleArguments @('--stage','train')
        & $taskRunner -Framework torch -Module coverage -ModuleArguments @(
            'run','--append','--rcfile=experiments/configs/v3/phase27_coverage.ini',
            '-m','pytest','tests/cnn','-q','-k','not keras',
            '--junitxml=artifacts/manifests/phase27/cnn_tests.xml'
        )
        & $taskRunner -Framework keras -Module coverage -ModuleArguments @(
            'run','--append','--rcfile=experiments/configs/v3/phase27_coverage.ini',
            '-m','pytest','tests/cnn/test_training.py::test_keras_gpu_resume_and_scratch_parity','-q',
            '--junitxml=artifacts/manifests/phase27/keras_trainer_tests.xml'
        )
        & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
            'tests/cnn/test_demo.py','-q','--junitxml=artifacts/manifests/phase27/demo_tests.xml'
        )
        & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
            'tests/data','tests/contracts','tests/api','tests/test_environment_contract.py',
            'tests/test_scratch_v2_smoke.py','-q',
            '--junitxml=artifacts/manifests/phase27/regression-tests.xml'
        )
        & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
            'tests/test_phase26_preservation.py','-q',
            '--junitxml=artifacts/manifests/phase27/preservation-tests.xml'
        )
        & $taskRunner -Framework torch -Module coverage -ModuleArguments @(
            'json','--rcfile=experiments/configs/v3/phase27_coverage.ini',
            '-o','artifacts/manifests/phase27/pretest_coverage.json'
        )
        & $taskRunner -Framework torch -Module scripts.verify_phase27 -ModuleArguments @('--stage','pretest')
    }
    if (-not $EvaluateTest) {
        Write-Output 'Validation/pretest ready. TEST is still sealed; use -EvaluateTest only for authorized Phase27 completion.'
        return
    }
    & $taskRunner -Framework torch -Module scripts.phase27_controller -ModuleArguments @('--stage','lock-test')
    & $taskRunner -Framework torch -Module scripts.phase27_controller -ModuleArguments @('--stage','test')
    & $taskRunner -Framework torch -Module scripts.verify_phase27 -ModuleArguments @('--stage','full')
    & $taskRunner -Framework torch -Module scripts.export_phase27
    & $taskRunner -Framework torch -Module scripts.smoke_phase27
    & $taskRunner -Framework torch -Module scripts.summarize_phase27
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
        'tests/test_phase27_report_acceptance.py','-q',
        '--junitxml=artifacts/manifests/phase27/report-tests.xml'
    )
    & $taskRunner -Framework torch -Module coverage -ModuleArguments @(
        'json','--rcfile=experiments/configs/v3/phase27_coverage.ini',
        '-o','artifacts/manifests/phase27/final_coverage.json'
    )
    Write-Output 'Model/TEST/report pipeline finished. Review figures and final evidence before scripts.release_phase27 --lock.'
}
finally { Pop-Location }
