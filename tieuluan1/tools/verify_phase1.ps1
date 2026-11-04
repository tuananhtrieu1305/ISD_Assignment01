[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$phaseRoot = Join-Path $root 'term_paper'

$required = @(
    'config/requirements_matrix.md',
    'config/report_outline.md',
    'config/style_spec.md',
    'config/experiment_contract.md',
    'sources/source_registry.csv',
    'sources/bibliography.bib',
    'sources/dataset_cards/README.md'
)

foreach ($relative in $required) {
    $path = Join-Path $phaseRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Missing Phase 1 deliverable: $relative"
    }
}

$registryPath = Join-Path $phaseRoot 'sources/source_registry.csv'
$registry = @(Import-Csv -LiteralPath $registryPath)
if ($registry.Count -ne 8) {
    throw "Expected 8 dataset registry rows, got $($registry.Count)"
}
if ((@($registry.dataset_id | Sort-Object -Unique)).Count -ne 8) {
    throw 'dataset_id values are not unique'
}

$bibPath = Join-Path $phaseRoot 'sources/bibliography.bib'
$bibText = Get-Content -Raw -Encoding utf8 -LiteralPath $bibPath
$bibKeys = [regex]::Matches($bibText, '@[A-Za-z]+\{([^,]+),') | ForEach-Object { $_.Groups[1].Value }
if ($bibKeys.Count -lt 20) {
    throw "Initial bibliography is too small: $($bibKeys.Count) entries"
}

$hashRecords = @(Import-Csv -LiteralPath (Join-Path $phaseRoot 'artifacts/manifests/source_hashes.csv'))
$knownHashes = @{}
foreach ($record in $hashRecords) { $knownHashes[$record.sha256] = $true }

foreach ($row in $registry) {
    foreach ($column in @('dataset_id','chapter','canonical_name','official_or_primary_url','accessed_at','license_status','local_path','physical_size_bytes','logical_size','sha256_or_manifest_sha256','citation_key')) {
        if ([string]::IsNullOrWhiteSpace($row.$column)) {
            throw "Registry row $($row.dataset_id) is missing $column"
        }
    }
    if ($row.official_or_primary_url -notmatch '^https://') {
        throw "Registry row $($row.dataset_id) does not use an HTTPS source URL"
    }
    if ($row.accessed_at -ne '2026-10-05') {
        throw "Unexpected access date for $($row.dataset_id): $($row.accessed_at)"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $root $row.local_path))) {
        throw "Missing local provenance path for $($row.dataset_id): $($row.local_path)"
    }
    if ($bibKeys -notcontains $row.citation_key) {
        throw "Missing bibliography key for $($row.dataset_id): $($row.citation_key)"
    }
    if (-not $knownHashes.ContainsKey($row.sha256_or_manifest_sha256)) {
        throw "Registry hash is absent from Phase 0 source_hashes.csv: $($row.dataset_id)"
    }
}

$cards = @(Get-ChildItem -LiteralPath (Join-Path $phaseRoot 'sources/dataset_cards') -Filter 'ch*.md' -File)
if ($cards.Count -ne 8) {
    throw "Expected 8 dataset cards, got $($cards.Count)"
}
foreach ($card in $cards) {
    $text = Get-Content -Raw -Encoding utf8 -LiteralPath $card.FullName
    if (($text -split "`n" | Where-Object { $_ -match '^## ' }).Count -lt 5) {
        throw "Dataset card $($card.Name) has fewer than five level-2 sections"
    }
    foreach ($pattern in @('Dataset ID:', 'https://', 'Local:', 'SHA-256', 'label|target|Output|output')) {
        if ($text -notmatch $pattern) {
            throw "Dataset card $($card.Name) is missing required evidence matching: $pattern"
        }
    }
}

$outline = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $phaseRoot 'config/report_outline.md')
if (($outline -split "`n" | Where-Object { $_ -match '^#### ' }).Count -lt 20) {
    throw 'Report outline does not reach heading level 3 throughout the document'
}
if (-not $outline.Contains('| **64** |')) {
    throw 'Missing total page budget of 64 pages before appendices'
}
if (([regex]::Matches($outline, '\|---')).Count -lt 2) {
    throw 'Missing a separate image/table budget table'
}

$matrix = Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $phaseRoot 'config/requirements_matrix.md')
foreach ($id in @('STR-01','STR-02','STR-03','STR-04','STR-05','STR-06','DATA-01','DATA-02','DATA-03','DATA-04','DATA-05','DATA-06','DATA-07','DATA-08','EXP-01','EXP-04','EXP-07','EXP-10','EXP-11','DEP-01','DOC-01','DOC-06')) {
    if (-not $matrix.Contains($id)) { throw "Requirements matrix is missing $id" }
}

$primaryHistoryKeys = @('mcculloch1943logical','turing1950computing','mccarthy1955dartmouth','rosenblatt1958perceptron','rumelhart1986backprop','lecun1998document','hochreiter1997lstm','krizhevsky2012imagenet','vaswani2017attention')
foreach ($key in $primaryHistoryKeys) {
    if ($bibKeys -notcontains $key) { throw "Missing primary history source: $key" }
}

Write-Host "PASS Phase 1: $($registry.Count) registry rows; $($cards.Count) dataset cards; $($bibKeys.Count) bibliography entries; outline/requirements/style/contract present."
