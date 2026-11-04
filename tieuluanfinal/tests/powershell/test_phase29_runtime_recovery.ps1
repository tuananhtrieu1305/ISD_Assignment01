$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskScript = Join-Path $taskRoot 'scripts/recover_phase29_runtime_r1.sh'
if (-not (Test-Path -LiteralPath $taskScript)) { throw 'RED: versioned runtime recovery script missing' }
$taskSource = Get-Content -Raw -Encoding UTF8 -LiteralPath $taskScript
foreach ($taskRequired in @('sync --locked --extra torch', 'sync --locked --extra keras', 'phase29_runtime_recovery_r1', 'b0c71fd20e221ed3456278e1916079c46ac206831a98dcf40d3b8f7a83477862', 'phase21_tools.sh', '20 * 1024')) {
    if (-not $taskSource.Contains($taskRequired)) { throw ('Recovery guard missing: ' + $taskRequired) }
}
foreach ($taskForbidden in @('scripts/doctor.py', 'scripts/bootstrap.sh', 'rm -', 'uv lock', 'unregister', 'keras-torch', 'artifacts/manifests/environment.json')) {
    if ($taskSource.Contains($taskForbidden)) { throw ('Unsafe recovery operation: ' + $taskForbidden) }
}
Write-Output 'PASS: immutable-lock and non-overwrite runtime recovery guards'
