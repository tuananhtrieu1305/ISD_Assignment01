[CmdletBinding(PositionalBinding=$false)]
param(
    [ValidateSet('preflight', 'inspect-reference')]
    [string]$Task = 'preflight'
)
$ErrorActionPreference = 'Stop'
$agent02Repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$agent02Wrapper = Join-Path $agent02Repo 'scripts/run_experiment.ps1'
# The shared wrapper chooses the existing pinned Linux runtime and restores repo cwd.
& $agent02Wrapper -Framework torch -Distribution Ubuntu -Module agent02_assignment.phase01 -ModuleArguments @($Task)
if ($LASTEXITCODE -ne 0) { throw "Agent02 preflight failed with exit code $LASTEXITCODE" }
