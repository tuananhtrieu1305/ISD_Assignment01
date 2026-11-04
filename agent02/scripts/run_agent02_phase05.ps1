[CmdletBinding(PositionalBinding=$false)]
param([ValidateSet('status','declare','evaluate')][string]$Task='status')
$ErrorActionPreference='Stop'
$agent02Repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
& (Join-Path $agent02Repo 'scripts/run_experiment.ps1') -Framework torch -Distribution Ubuntu -Module agent02_assignment.phase05 -ModuleArguments @($Task)
if ($LASTEXITCODE -ne 0) { throw "Agent02 Phase 5 exited $LASTEXITCODE" }
