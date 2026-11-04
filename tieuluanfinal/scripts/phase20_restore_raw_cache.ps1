$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$prefix = 'term_paper/knowledge_rag/data/raw/finqa/'
$records = Import-Csv -LiteralPath (Join-Path $workspace 'artifacts/manifests/phase20/before-files.csv') |
    Where-Object { $_.path.StartsWith($prefix) -and $_.path.Contains('/__pycache__/') }
$log = @()
foreach ($record in $records) {
    $relative = $record.path.Substring($prefix.Length)
    $target = [IO.Path]::GetFullPath((Join-Path $workspace ('data/raw/ch5/finqa/' + $relative)))
    $allowed = Join-Path $workspace 'data\raw\ch5\finqa'
    if (-not $target.StartsWith($allowed + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "Unsafe raw restore target" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    $url = 'https://raw.githubusercontent.com/czyssrs/FinQA/0f16e2867befa6840783e58be38c9efb9229d742/' + $relative
    if (-not (Test-Path -LiteralPath $target)) { Invoke-WebRequest -Uri $url -OutFile $target -UseBasicParsing }
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    if ($actual -ne $record.sha256) { throw "Raw restore hash mismatch: $relative" }
    $log += [pscustomobject]@{path=$relative; source=$url; sha256=$actual; status='RESTORED_EXACT_BYTES'}
}
$log | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $workspace 'artifacts/manifests/phase20/raw-cache-restoration.json') -Encoding UTF8
Write-Output ('Restored and verified raw snapshot files: ' + $log.Count)
