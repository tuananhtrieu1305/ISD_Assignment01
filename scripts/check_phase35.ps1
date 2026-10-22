[CmdletBinding()]
param([string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'run_docs_v3.ps1') -Distribution $Distribution -Module scripts.phase35_release -Arguments @('--stage','verify')
if ($LASTEXITCODE -ne 0) { throw 'Phase35 read-only verification failed' }
