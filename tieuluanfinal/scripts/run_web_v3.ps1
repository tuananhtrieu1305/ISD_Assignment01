[CmdletBinding()]
param(
 [ValidateSet('install','dev','build','test','test:coverage','test:legacy','e2e','preview','type-check','lint','install:browsers','format:v3')][string]$Action = 'dev'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runtime = Join-Path $repo '.local/node-v22.23.4-win-x64'
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'node.exe'))) { throw 'Run scripts/bootstrap_web_v3.ps1 first' }
$previousPath = $env:PATH
$previousCache = $env:npm_config_cache
$previousBrowser = $env:PLAYWRIGHT_BROWSERS_PATH
$env:PATH = "$runtime;$previousPath"
$env:npm_config_cache = Join-Path $repo '.local/npm-cache'
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $repo '.local/ms-playwright'
Push-Location (Join-Path $repo 'apps/web')
try {
 if ($Action -eq 'install') { & (Join-Path $runtime 'npm.cmd') ci --no-fund --no-audit }
 else { & (Join-Path $runtime 'npm.cmd') run $Action }
 if ($LASTEXITCODE -ne 0) { throw "Web action failed: $Action ($LASTEXITCODE)" }
} finally { Pop-Location; $env:PATH = $previousPath; $env:npm_config_cache = $previousCache; $env:PLAYWRIGHT_BROWSERS_PATH = $previousBrowser }
