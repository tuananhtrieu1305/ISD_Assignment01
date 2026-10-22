param([switch]$Train)
$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = Split-Path $PSScriptRoot -Parent
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase26/revisions/r2/experiment_lock.json') {
        & $taskRunner -Framework torch -Module scripts.verify_phase26_roundtrip_v1
        return
    }
    if (Test-Path -LiteralPath 'artifacts/manifests/phase26/revisions/r2/release.json') {
        throw 'Release already declared. Do not replace test evidence; use phase26_controller --stage train/status.'
    }
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
        'tests/ch02_ml', '--ignore=tests/ch02_ml/test_native_keras.py', '-q', '--cov',
        '--cov-config=experiments/configs/v3/phase26_coverage.ini', '--cov-fail-under=0',
        '--cov-report=json:artifacts/manifests/phase26/revisions/r2/coverage_torch.json',
        '--junitxml=artifacts/manifests/phase26/revisions/r2/unit-torch.xml'
    )
    & $taskRunner -Framework keras -Module pytest -ModuleArguments @(
        'tests/ch02_ml/test_native_keras.py', '-q', '--cov', '--cov-append',
        '--cov-config=experiments/configs/v3/phase26_coverage.ini', '--cov-fail-under=0',
        '--cov-report=json:artifacts/manifests/phase26/revisions/r2/coverage_combined.json',
        '--junitxml=artifacts/manifests/phase26/revisions/r2/unit-keras.xml'
    )
    if ($Train) {
        & $taskRunner -Framework torch -Module coverage -ModuleArguments @(
            'run','--append','--rcfile=experiments/configs/v3/phase26_coverage.ini',
            '-m','scripts.prepare_phase26'
        )
        & $taskRunner -Framework torch -Module scripts.phase26_controller -ModuleArguments @('--stage','train')
    }
}
finally { Pop-Location }
