$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$node=Join-Path $repo '.local/node-v22.23.4-win-x64/node.exe'
$vite=Join-Path $repo 'node_modules/vite/bin/vite.js'
& $node $vite build "$repo/tieuluanfinal/web/frontend" --config "$repo/tieuluanfinal/web/frontend/vite.config.ts"
if($LASTEXITCODE -ne 0){throw 'Paper frontend build failed'}
& $node $vite build "$repo/tieuluanfinal/web/agent/web/frontend" --config "$repo/tieuluanfinal/web/agent/web/frontend/vite.config.js" --base /multi-agent/
if($LASTEXITCODE -ne 0){throw 'Agent frontend build failed'}
