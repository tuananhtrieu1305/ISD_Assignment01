param([ValidateRange(1,24)][int]$TimeoutHours = 8)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskWaiterLock = $null
Push-Location $taskRoot
try {
    $taskWaiterLock = [IO.File]::Open((Join-Path $taskRoot 'artifacts/manifests/phase28/.acceptance_waiter.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $taskDeadline = [DateTime]::UtcNow.AddHours($TimeoutHours)
    $taskLastState = ''
    $taskLastControllerPid = $null
    Write-Output ('Acceptance waiter host PID=' + $PID + '; no training or TEST command is invoked here.')
    while ($true) {
        if ([DateTime]::UtcNow -ge $taskDeadline) { throw 'Wait timeout; inspect queue. No acceptance was started.' }
        $taskActive = Get-Content -Raw -LiteralPath 'artifacts/manifests/phase28/active_controller.json' | ConvertFrom-Json
        $taskCheckpoint = Get-Content -Raw -LiteralPath 'artifacts/manifests/phase28/checkpoint.json' | ConvertFrom-Json
        $taskState = [string]$taskCheckpoint.completed_runs + ': ' + $taskCheckpoint.current_run
        if ($taskState -ne $taskLastState) { Write-Output $taskState; $taskLastState = $taskState }
        if ($null -ne $taskActive.pid) { $taskLastControllerPid = [int]$taskActive.pid }
        if ($null -eq $taskActive.pid) {
            if ($taskActive.status -ne 'finished') { throw 'Controller did not finish successfully; inspect logs. No acceptance was started.' }
            $taskRelease = Get-Content -Raw -LiteralPath 'artifacts/manifests/phase28/release.json' | ConvertFrom-Json
            $taskComplete = @($taskRelease.runs | Where-Object { Test-Path -LiteralPath ('artifacts/manifests/phase28/runs/' + $_.run_id + '/selection.json') }).Count
            if ($taskComplete -ne 132) { throw 'Controller stopped with missing selections. No automatic retry or retraining.' }
            # Wait for process exit, including coverage's final flush, not only a mutable PID=null marker.
            if ($null -ne $taskLastControllerPid) {
                & wsl.exe --distribution Ubuntu-24.04 --exec test -d ('/proc/' + $taskLastControllerPid)
                if ($LASTEXITCODE -eq 0) { Start-Sleep -Seconds 2; continue }
                if ($LASTEXITCODE -ne 1) { throw 'Cannot verify old controller exit; do not risk concurrent coverage writers.' }
            }
            break
        }
        Start-Sleep -Seconds 15
    }
    & (Join-Path $PSScriptRoot 'finish_phase28.ps1')
    Write-Output 'Acceptance pipeline ended. Visual inspection/seal/release are still required; Phase28 is not automatically marked COMPLETE.'
}
finally {
    if ($null -ne $taskWaiterLock) { $taskWaiterLock.Dispose() }
    Pop-Location
}
