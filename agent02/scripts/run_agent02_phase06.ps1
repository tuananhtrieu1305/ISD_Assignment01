param(
    [ValidateSet('status','prepare','declare','train','declare-eval','evaluate')]
    [string]$Task = 'status',
    [switch]$Resume
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$arguments = @($Task)
if ($Resume) { $arguments += '--resume' }
& (Join-Path $repo 'scripts/run_experiment.ps1') -Framework torch -Distribution Ubuntu -Module agent02_assignment.phase06 -ModuleArguments $arguments
