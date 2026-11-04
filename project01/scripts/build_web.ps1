$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$taskNode=Join-Path $taskRoot '.local\node-v22.23.4-win-x64\node.exe'
$taskVite=Join-Path $taskRoot 'node_modules\vite\bin\vite.js'
if(-not (Test-Path -LiteralPath $taskNode) -or -not (Test-Path -LiteralPath $taskVite)){throw 'Read README: use the existing Node22 toolchain, or npm ci inside web/frontend on a fresh machine'}
& $taskNode $taskVite build (Join-Path $taskRoot 'project01\web\frontend') --config (Join-Path $taskRoot 'project01\web\frontend\vite.config.js')
if($LASTEXITCODE -ne 0){throw "Frontend build failed: $LASTEXITCODE"}
