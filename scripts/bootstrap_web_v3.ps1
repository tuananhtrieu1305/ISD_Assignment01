[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$version = '22.23.4'
$expected = 'cbc74b5e0982c9dbb41525fd8fb5dcd32fbee237863f7829072f4639a1ce5f20'
$local = Join-Path $repo '.local'
$runtime = Join-Path $local "node-v$version-win-x64"
$archive = Join-Path $local "node-v$version-win-x64.zip"
New-Item -ItemType Directory -Path $local -Force | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'node.exe'))) {
 if (-not (Test-Path -LiteralPath $archive)) {
  Invoke-WebRequest -UseBasicParsing -Uri "https://nodejs.org/dist/v$version/node-v$version-win-x64.zip" -OutFile $archive
 }
 if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'Node archive hash mismatch; no extraction' }
 Expand-Archive -LiteralPath $archive -DestinationPath $local
}
if ((& (Join-Path $runtime 'node.exe') --version) -ne "v$version") { throw 'Unexpected Node version' }
Write-Output "Node v$version available at $runtime; no global PATH/system install or Python environment changes."
