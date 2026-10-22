$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$folder = Join-Path $repo 'artifacts/manifests/phase33/acceptance-e2e-v3-screenshots'
$images = @(Get-ChildItem -LiteralPath $folder -Filter '*.png' -File | Sort-Object Name)
if ($images.Count -ne 7) { throw 'Expected7 reviewed screenshots' }
$rows = @($images | ForEach-Object { @{path=$_.FullName.Substring($repo.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
$destination = Join-Path $repo 'artifacts/manifests/phase33/visual_qa.json'
if (Test-Path -LiteralPath $destination) { throw 'Visual evidence already exists' }
$proof = @{status='PASS';images=$rows;method='Assistant viewed all7 actual final PNGs via image tool; no synthesized screenshots';scope='Desktop CNN/RNN/LSTM/KG/agent +mobile home/CNN; not all viewport/browser combinations';notes=@('No overlapping cards or page-width overflow in reviewed screenshots','Mobile JSON grouped in expandable details; active dataset tab visible','Citation/hash wrap; zero agent node durations labeled uninstrumented','Axe and keyboard checks separate from visual inspection');cloud_deployed=$false}
[IO.File]::WriteAllText($destination, ($proof | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
Write-Output 'Visual QA sealed7images'
