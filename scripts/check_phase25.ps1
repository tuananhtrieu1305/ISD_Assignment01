param([switch]$Lock)
$ErrorActionPreference = 'Stop'
$taskRunner = Join-Path $PSScriptRoot 'run_experiment.ps1'
$taskRoot = Split-Path $PSScriptRoot -Parent
Push-Location $taskRoot
try {
    if (Test-Path -LiteralPath 'artifacts/manifests/phase25/core_lock.json') {
        & $taskRunner -Framework torch -Module scripts.verify_phase25
        return
    }
    # Sequential coverage writers: separate venvs share the same Linux data file.
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
        'tests/core', '--ignore=tests/core/test_keras_core.py', '-q', '--cov',
        '--cov-config=experiments/configs/v3/phase25_coverage.ini',
        '--cov-report=json:artifacts/manifests/phase25/core_coverage_torch.json',
        '--junitxml=artifacts/manifests/phase25/core-tests-torch.xml'
    )
    & $taskRunner -Framework keras -Module pytest -ModuleArguments @(
        'tests/core/test_keras_core.py', '-q', '--cov', '--cov-append',
        '--cov-config=experiments/configs/v3/phase25_coverage.ini',
        '--cov-report=json:artifacts/manifests/phase25/core_coverage_combined.json',
        '--junitxml=artifacts/manifests/phase25/core-tests-keras.xml'
    )
    foreach ($taskImplementation in @('pytorch', 'keras')) {
        $taskFramework = if ($taskImplementation -eq 'pytorch') { 'torch' } else { 'keras' }
        foreach ($taskDevice in @('cpu', 'gpu')) {
            $taskProbeExtras = if ($taskDevice -eq 'cpu') { @('--parity-only') } else { @() }
            & $taskRunner -Framework $taskFramework -Module coverage -ModuleArguments (@(
                'run', '--append', '--rcfile=experiments/configs/v3/phase25_coverage.ini',
                '-m', 'scripts.phase25_backend_probe', '--implementation', $taskImplementation,
                '--device', $taskDevice
            ) + $taskProbeExtras)
        }
    }
    & $taskRunner -Framework torch -Module coverage -ModuleArguments @(
        'json', '--rcfile=experiments/configs/v3/phase25_coverage.ini',
        '-o', 'artifacts/manifests/phase25/core_coverage_combined.json'
    )
    & $taskRunner -Framework torch -Module pytest -ModuleArguments @(
        'tests/contracts', 'tests/api', 'tests/test_environment_contract.py',
        'tests/test_scratch_v2_smoke.py', 'tests/data', '-q',
        '--junitxml=artifacts/manifests/phase25/regression-tests.xml'
    )
    & $taskRunner -Framework torch -Module scripts.prepare_phase25
    $taskVerifyArguments = if ($Lock) { @('--lock') } else { @() }
    & $taskRunner -Framework torch -Module scripts.verify_phase25 -ModuleArguments $taskVerifyArguments
}
finally { Pop-Location }
