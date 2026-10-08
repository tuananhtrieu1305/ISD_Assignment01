[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
$manifestRoot = Join-Path $workspace 'term_paper\artifacts\manifests'
$inventoryPath = Join-Path $manifestRoot 'source_inventory.json'
$hashesPath = Join-Path $manifestRoot 'source_hashes.csv'
$auditPath = Join-Path $manifestRoot 'notebook_audit.csv'

$required = @($inventoryPath, $hashesPath, $auditPath, (Join-Path $manifestRoot 'gap_analysis.md'))
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath $_) })
if ($missing.Count -gt 0) {
    throw "Missing Phase 0 deliverables: $($missing -join ', ')"
}

$inventory = Get-Content -Raw -Encoding UTF8 -LiteralPath $inventoryPath | ConvertFrom-Json
$hashes = @(Import-Csv -LiteralPath $hashesPath)
$audit = @(Import-Csv -LiteralPath $auditPath)
$errors = New-Object System.Collections.Generic.List[string]

if ($hashes.Count -ne [int]$inventory.hash_record_count) {
    [void]$errors.Add("Hash row mismatch: CSV=$($hashes.Count), inventory=$($inventory.hash_record_count)")
}
if ($audit.Count -ne [int]$inventory.notebooks.count) {
    [void]$errors.Add("Notebook row mismatch: CSV=$($audit.Count), inventory=$($inventory.notebooks.count)")
}

foreach ($row in $hashes) {
    if ($row.hash_basis -eq 'file_content') {
        $path = if ([System.IO.Path]::IsPathRooted($row.path)) { $row.path } else { Join-Path $workspace ($row.path.Replace('/', '\')) }
        if (-not (Test-Path -LiteralPath $path)) {
            [void]$errors.Add("Missing hashed file: $($row.path)")
            continue
        }
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        if ($actual -ne $row.sha256) {
            [void]$errors.Add("Hash mismatch: $($row.path)")
        }
    }
    elseif ($row.hash_basis -eq 'sorted_path_size_mtime_manifest') {
        $manifestPath = Join-Path $workspace ($row.manifest_path.Replace('/', '\'))
        if (-not (Test-Path -LiteralPath $manifestPath)) {
            [void]$errors.Add("Missing folder manifest: $($row.manifest_path)")
            continue
        }
        $actualManifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash.ToLowerInvariant()
        if ($actualManifestHash -ne $row.sha256) {
            [void]$errors.Add("Folder manifest hash mismatch: $($row.manifest_path)")
        }
        $manifestRows = @(Import-Csv -LiteralPath $manifestPath)
        if ($manifestRows.Count -ne [int]$row.file_count) {
            [void]$errors.Add("Folder manifest count mismatch: $($row.manifest_path)")
        }
        foreach ($manifestRow in $manifestRows) {
            $sourcePath = Join-Path $workspace ($manifestRow.path.Replace('/', '\'))
            if (-not (Test-Path -LiteralPath $sourcePath)) {
                [void]$errors.Add("Missing source listed by folder manifest: $($manifestRow.path)")
                continue
            }
            $sourceItem = Get-Item -LiteralPath $sourcePath
            if ([int64]$sourceItem.Length -ne [int64]$manifestRow.size_bytes) {
                [void]$errors.Add("Size mismatch for folder-manifest source: $($manifestRow.path)")
            }
        }
    }
}

function Get-SourceStatusLines {
    param([string[]]$Lines)
    return @(
        foreach ($line in $Lines) {
            if ($line.Length -lt 4) { continue }
            $path = $line.Substring(3).Trim('"')
            if ($path -match '^(pipeline|A05|A06)/') {
                $line
            }
        }
    ) | Sort-Object
}

$baselineSourceStatus = @(Get-SourceStatusLines -Lines @($inventory.git_status_before))
$currentStatus = @(& git -C $workspace status --porcelain=v1 2>$null)
$currentSourceStatus = @(Get-SourceStatusLines -Lines $currentStatus)
if (($baselineSourceStatus -join "`n") -ne ($currentSourceStatus -join "`n")) {
    [void]$errors.Add('Git status under pipeline/A05/A06 changed during Phase 0.')
}

$result = [ordered]@{
    passed = ($errors.Count -eq 0)
    notebook_rows = $audit.Count
    hash_rows_verified = $hashes.Count
    folder_manifests_verified = @($hashes | Where-Object { $_.hash_basis -eq 'sorted_path_size_mtime_manifest' }).Count
    source_git_status_unchanged = (($baselineSourceStatus -join "`n") -eq ($currentSourceStatus -join "`n"))
    errors = @($errors)
}
Write-Output ($result | ConvertTo-Json -Depth 5)
if ($errors.Count -gt 0) { exit 1 }
