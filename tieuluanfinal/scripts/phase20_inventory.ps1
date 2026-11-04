param(
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,
    [ValidateSet("before", "after")]
    [string]$Snapshot = "before"
)

$ErrorActionPreference = "Stop"
$workspace = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputRoot = [System.IO.Path]::GetFullPath((Join-Path $workspace $OutputDirectory))

if (-not $outputRoot.StartsWith($workspace, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Output directory must remain inside workspace: $outputRoot"
}

New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

function Get-GitPathSet {
    param([string[]]$Arguments)
    $set = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $lines = & git @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Arguments -join ' ') failed"
    }
    foreach ($line in $lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            [void]$set.Add(($line -replace '\\', '/'))
        }
    }
    return ,$set
}

$tracked = Get-GitPathSet -Arguments @("ls-files")
$untracked = Get-GitPathSet -Arguments @("ls-files", "--others", "--exclude-standard")
$ignored = Get-GitPathSet -Arguments @("ls-files", "--others", "--ignored", "--exclude-standard")

function Get-Disposition {
    param([string]$Path)

    $p = $Path.ToLowerInvariant()

    if ($p.StartsWith('data/raw/ch5/') -or $p.StartsWith('term_paper/knowledge_rag/data/raw/')) {
        return @('KEEP', 'Locked Ch5 raw snapshot; upstream cache bytes are part of the immutable source snapshot')
    }

    if ($p -match '(^|/)(\.venv[^/]*|node_modules|__pycache__|\.pytest_cache|\.uv-cache|\.ipython|\.expo|dist)(/|$)') {
        return @("REMOVE", "Dependency environment, cache, or generated build output")
    }
    if ($p.StartsWith("mobile/")) {
        return @("REMOVE", "Legacy mobile client is outside the V3 React web and Python API product")
    }
    if ($p -match '^a05/(datasets|results|models)/') {
        return @("REGENERATE", "Legacy A05 data or experiment output; recoverable from Git/source notebook")
    }
    if ($p -match '^a05/report/(docx_render|docx_assets)/') {
        return @("REGENERATE", "Rendered report asset; final DOCX and report source are preserved")
    }
    if ($p -eq 'a05/report/a05_assignment_report.docx') {
        return @("MIGRATE", "Style/reference DOCX moved to releases/v2/references")
    }
    if ($p -match '^a06/(datasets|results|models)/') {
        return @("REGENERATE", "Legacy A06 data or experiment output replaced by V3 RNN-LSTM work")
    }
    if ($p -match '^a06/report/(a05_reference_|docx_render|a06_a05style_)') {
        return @("REGENERATE", "Intermediate report render/unpacked reference")
    }
    if ($p -eq 'a06/report/a06_assignment_report.docx') {
        return @("MIGRATE", "Legacy RNN report moved to releases/v2/references")
    }
    if ($p.StartsWith("datasets/")) {
        return @("REGENERATE", "Legacy dataset replaced by the Phase 23 registry and official snapshots")
    }
    if ($p -match '^artifacts/(a03_|docx_work|house_models|customer_behavior_models|diabetes_models|pycache_tmp)') {
        return @("REGENERATE", "Legacy generated artifact outside the V3 artifact contract")
    }
    if ($p -match '^artifacts/(house_pipeline|customer_churn_pipeline|diabetes_pipeline)') {
        return @("REGENERATE", "Legacy serialized pipeline replaced by V3 models")
    }
    if ($p -match '^artifacts/(a02_extracted|.*_metadata\.json$)') {
        return @("REGENERATE", "Legacy derived text or metadata")
    }
    if ($p -match '^pipeline/(customer_behavior|house_price|diabetes)/') {
        return @("REGENERATE", "Notebook-generated legacy model output")
    }
    if ($p -match '^pipeline04/(cifar10|customer_behavior|house_price|mnist|diabetes)/') {
        return @("REGENERATE", "Notebook-generated legacy CNN output")
    }
    if ($p.StartsWith("term_paper/artifacts/")) {
        return @("REGENERATE", "V2 Ch2-Ch4 artifacts will be replaced by V3 experiments")
    }
    if ($p.StartsWith("term_paper/knowledge_rag/data/processed/")) {
        return @("REGENERATE", "Derived Ch5 index/graph data; raw snapshot, source, config, metrics, and public TEST results remain")
    }
    if ($p.StartsWith("term_paper/knowledge_rag/artifacts/predictions/phase14/")) {
        return @("REGENERATE", "Validation/smoke predictions can be rebuilt without reopening public TEST")
    }
    if ($p -match '^term_paper/report/(qa|qa_phase8|qa_phase19)/') {
        return @("REGENERATE", "Rendered page QA; release DOCX is preserved")
    }
    if ($p -eq 'term_paper/report/tieu_luan_ai_ml_cnn_rnn_kg_rag.docx' -or
        $p -eq 'term_paper/report/tieu_luan_ai_ml_cnn_rnn.docx') {
        return @("MIGRATE", "Released DOCX moved to releases/v2")
    }
    if ($p.StartsWith("backend/models/")) {
        return @("KEEP", "Current compact deployment artifact; retained until Phase 30/32 migration")
    }
    if ($p.StartsWith("term_paper/knowledge_rag/artifacts/predictions/phase15/")) {
        return @("KEEP", "Sealed Ch5 public TEST predictions; must not be regenerated")
    }
    return @("KEEP", "Source, configuration, test, documentation, or small retained artifact")
}

$records = [System.Collections.Generic.List[object]]::new()
$files = Get-ChildItem -LiteralPath $workspace -File -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object {
        -not $_.FullName.StartsWith((Join-Path $workspace ".git") + '\', [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $_.FullName.StartsWith($outputRoot, [System.StringComparison]::OrdinalIgnoreCase)
    }

Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Security.Cryptography;
using System.Collections.Concurrent;
using System.Threading.Tasks;

public static class Phase20Hashes {
    public static ConcurrentDictionary<string, string> Compute(string[] paths) {
        var hashes = new ConcurrentDictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        Parallel.ForEach(paths, new ParallelOptions { MaxDegreeOfParallelism = 8 }, path => {
            using (var sha = SHA256.Create())
            using (var stream = File.OpenRead(path)) {
                hashes[path] = BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
            }
        });
        return hashes;
    }
}
'@
Write-Output ("Hashing " + $files.Count + " files with 8 I/O workers")
$hashes = [Phase20Hashes]::Compute([string[]]@($files | ForEach-Object FullName))

foreach ($file in $files) {
    $relative = $file.FullName.Substring($workspace.Length + 1) -replace '\\', '/'
    $hash = $hashes[$file.FullName]

    $gitState = if ($tracked.Contains($relative)) {
        "tracked"
    }
    elseif ($ignored.Contains($relative)) {
        "ignored"
    }
    elseif ($untracked.Contains($relative)) {
        "untracked"
    }
    else {
        "outside-git-index"
    }

    $classification = Get-Disposition -Path $relative
    $records.Add([pscustomobject]@{
        path = $relative
        bytes = $file.Length
        sha256 = $hash
        git_state = $gitState
        disposition = $classification[0]
        reason = $classification[1]
    })
}

$csvPath = Join-Path $outputRoot "$Snapshot-files.csv"
$records | Sort-Object path | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding UTF8

$groups = $records | Group-Object disposition | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{
        disposition = $_.Name
        files = $_.Count
        bytes = [long](($_.Group | Measure-Object bytes -Sum).Sum)
    }
}
$gitGroups = $records | Group-Object git_state | Sort-Object Name | ForEach-Object {
    [pscustomobject]@{
        git_state = $_.Name
        files = $_.Count
        bytes = [long](($_.Group | Measure-Object bytes -Sum).Sum)
    }
}
$summary = [ordered]@{
    snapshot = $Snapshot
    generated_at = (Get-Date).ToString("o")
    workspace = $workspace
    file_count = $records.Count
    total_bytes = [long](($records | Measure-Object bytes -Sum).Sum)
    sha256_manifest = (Get-FileHash -Algorithm SHA256 -LiteralPath $csvPath).Hash.ToLowerInvariant()
    by_disposition = @($groups)
    by_git_state = @($gitGroups)
}
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $outputRoot "$Snapshot-summary.json") -Encoding UTF8

Write-Output ($summary | ConvertTo-Json -Depth 6)

