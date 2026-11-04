[CmdletBinding(PositionalBinding=$false)]
param(
    [ValidateSet('status', 'declare', 'train')]
    [string]$Task = 'status',
    [switch]$Resume
)
$ErrorActionPreference = 'Stop'
$agent02Repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$agent02Arguments = @($Task)
if ($Resume) { $agent02Arguments += '--resume' }
& (Join-Path $agent02Repo 'scripts/run_experiment.ps1') -Framework torch -Distribution Ubuntu -Module agent02_assignment.phase04 -ModuleArguments $agent02Arguments
if ($LASTEXITCODE -ne 0) { throw "Agent02 Phase 4 failed with exit code $LASTEXITCODE" }
