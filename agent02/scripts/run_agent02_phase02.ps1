[CmdletBinding(PositionalBinding=$false)]
param(
    [ValidateSet('status', 'write-protocol', 'smoke', 'verify-smoke')]
    [string]$Task = 'status'
)
$ErrorActionPreference = 'Stop'
$agent02Repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$agent02Wrapper = Join-Path $agent02Repo 'scripts/run_experiment.ps1'
& $agent02Wrapper -Framework torch -Distribution Ubuntu -Module agent02_assignment.phase02 -ModuleArguments @($Task)
if ($LASTEXITCODE -ne 0) { throw "Agent02 Phase 2 failed with exit code $LASTEXITCODE" }
