param([switch]$Execute, [switch]$Resume)

$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$manifestRoot = Join-Path $workspace 'artifacts\manifests\phase20'
$inventoryPath = Join-Path $manifestRoot 'before-files.csv'

function Resolve-WorkspaceTarget {
    param([string]$Relative)
    $target = [System.IO.Path]::GetFullPath((Join-Path $workspace $Relative))
    if (-not $target.StartsWith($workspace + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
        $target.StartsWith((Join-Path $workspace '.git') + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
        $target -eq (Join-Path $workspace '.git')) {
        throw "Unsafe target: $target"
    }
    return $target
}

if (-not (Test-Path -LiteralPath $inventoryPath)) { throw 'Run phase20_inventory.ps1 before cleanup.' }
$inventory = @(Import-Csv -LiteralPath $inventoryPath)
$events = [System.Collections.Generic.List[object]]::new()
if ($Resume -and (Test-Path -LiteralPath (Join-Path $manifestRoot 'operations.csv'))) {
    foreach ($event in Import-Csv -LiteralPath (Join-Path $manifestRoot 'operations.csv')) { $events.Add($event) }
}

function Move-Scoped {
    param([string]$From, [string]$To)
    $source = Resolve-WorkspaceTarget $From
    $destination = Resolve-WorkspaceTarget $To
    if (-not (Test-Path -LiteralPath $source)) {
        if ($Resume -and (Test-Path -LiteralPath $destination)) { return }
        throw "Missing migration source: $From"
    }
    if (Test-Path -LiteralPath $destination) { throw "Migration destination exists: $To" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Move-Item -LiteralPath $source -Destination $destination
    $events.Add([pscustomobject]@{action='MIGRATE'; source=$From; destination=$To; recovery=$To})
    $events | Export-Csv -LiteralPath (Join-Path $manifestRoot 'operations.csv') -NoTypeInformation -Encoding UTF8
}

function Remove-Scoped {
    param([string]$Relative, [string]$Recovery)
    $target = Resolve-WorkspaceTarget $Relative
    if (-not (Test-Path -LiteralPath $target)) { return }
    $events.Add([pscustomobject]@{action='REMOVE'; source=$Relative; destination=''; recovery=$Recovery})
    Remove-Item -LiteralPath $target -Recurse -Force
    $events | Export-Csv -LiteralPath (Join-Path $manifestRoot 'operations.csv') -NoTypeInformation -Encoding UTF8
}

$migrations = @(
    @('term_paper/report/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx', 'releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.docx'),
    @('term_paper/report/Tieu_luan_AI_ML_CNN_RNN.docx', 'releases/v2/Tieu_luan_AI_ML_CNN_RNN.docx'),
    @('term_paper/report/qa_phase19/word_final.pdf', 'releases/v2/Tieu_luan_AI_ML_CNN_RNN_KG_RAG.pdf'),
    @('term_paper/report/qa_phase19/final_release_manifest.json', 'releases/v2/qa/final_release_manifest.json'),
    @('term_paper/report/qa_phase19/phase19_verification.json', 'releases/v2/qa/phase19_verification.json'),
    @('term_paper/report/qa_phase19/visual_qa.json', 'releases/v2/qa/visual_qa.json'),
    @('term_paper/report/qa_phase19/word_page_map_final.json', 'releases/v2/qa/word_page_map_final.json'),
    @('A05/report/A05_Assignment_Report.docx', 'releases/v2/references/A05_Assignment_Report.docx'),
    @('A06/report/A06_Assignment_Report.docx', 'releases/v2/references/A06_Assignment_Report.docx'),
    @('A03_CT_anhtt.053.docx', 'releases/v2/references/A03_CT_anhtt.053.docx'),
    @('pipeline', 'experiments/notebooks/legacy/pipeline'),
    @('pipeline04', 'experiments/notebooks/legacy/pipeline04'),
    @('A05/notebooks', 'experiments/notebooks/legacy/A05'),
    @('A06/notebooks', 'experiments/notebooks/legacy/A06'),
    @('term_paper/notebooks', 'experiments/notebooks/legacy/term_paper'),
    @('term_paper/src', 'src/term_paper/src'),
    @('term_paper/tools', 'src/term_paper/tools'),
    @('term_paper/deployment/app', 'src/term_paper/deployment/app'),
    @('term_paper/tests', 'tests/legacy_v2/term_paper'),
    @('A06/src', 'src/legacy_a06'),
    @('A06/tests', 'tests/legacy_v2/A06'),
    @('term_paper/config', 'experiments/configs/legacy_v2'),
    @('term_paper/report', 'report'),
    @('term_paper/sources', 'report/references'),
    @('term_paper/knowledge_rag/data/raw', 'data/raw/ch5'),
    @('term_paper/knowledge_rag/config', 'experiments/configs/ch5'),
    @('term_paper/knowledge_rag/artifacts/metrics', 'artifacts/metrics/ch5'),
    @('term_paper/knowledge_rag/artifacts/manifests', 'artifacts/manifests/ch5'),
    @('term_paper/knowledge_rag/artifacts/figures', 'artifacts/figures/ch5'),
    @('term_paper/knowledge_rag/artifacts/predictions/phase15', 'artifacts/predictions/ch5/phase15'),
    @('term_paper/knowledge_rag/evaluation_contract.md', 'docs/ch5/evaluation_contract.md'),
    @('term_paper/knowledge_rag/graph_schema.md', 'docs/ch5/graph_schema.md'),
    @('term_paper/knowledge_rag/README.md', 'docs/ch5/README_v2.md'),
    @('term_paper/knowledge_rag/phase13_build_report.md', 'docs/ch5/phase13_build_report.md'),
    @('term_paper/knowledge_rag/phase14_build_report.md', 'docs/ch5/phase14_build_report.md'),
    @('term_paper/knowledge_rag/phase15_experiment_report.md', 'docs/ch5/phase15_experiment_report.md'),
    @('term_paper/knowledge_rag/phase16_deployment_report.md', 'docs/ch5/phase16_deployment_report.md'),
    @('term_paper/knowledge_rag/notebooks', 'experiments/notebooks/legacy/ch5'),
    @('backend/tests', 'tests/api'),
    @('backend', 'apps/api'),
    @('web', 'apps/web'),
    @('neo4j_scripts', 'docs/legacy_v2/neo4j_scripts'),
    @('PIPELINE_UPGRADE_PLAN.md', 'docs/legacy_v2/PIPELINE_UPGRADE_PLAN.md'),
    @('RENDER_DEPLOY.md', 'docs/legacy_v2/RENDER_DEPLOY.md'),
    @('build_a03_report.py', 'report/tools/legacy_v2/build_a03_report.py'),
    @('tools_extract_pdf_text.py', 'report/tools/legacy_v2/tools_extract_pdf_text.py')
)

if (-not $Execute) {
    $migrations | ForEach-Object { [pscustomobject]@{source=$_[0]; destination=$_[1]} } | Format-Table -AutoSize
    Write-Output 'Preview only. Use -Execute after reviewing before-files.csv.'
    exit 0
}

if (-not $Resume) {
(& git status --porcelain=v1) | Set-Content -LiteralPath (Join-Path $manifestRoot 'git-status-before.txt') -Encoding UTF8
(& git rev-parse HEAD) | Set-Content -LiteralPath (Join-Path $manifestRoot 'git-head-before.txt') -Encoding UTF8
$migrations | ForEach-Object { [pscustomobject]@{source=$_[0]; destination=$_[1]} } |
    Export-Csv -LiteralPath (Join-Path $manifestRoot 'migration-plan.csv') -NoTypeInformation -Encoding UTF8
$inventory | Where-Object { $_.disposition -eq 'KEEP' } |
    Export-Csv -LiteralPath (Join-Path $manifestRoot 'keep-list-before.csv') -NoTypeInformation -Encoding UTF8
}

# Freeze the exact dirty working-tree sources before performing any deletion or move.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$releaseRoot = Resolve-WorkspaceTarget 'releases/v2'
New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
$archivePath = Join-Path $releaseRoot 'source_snapshot.zip'
if (-not $Resume) {
if (Test-Path -LiteralPath $archivePath) { throw 'Snapshot already exists; inspect recovery state before rerunning.' }
$archive = [System.IO.Compression.ZipFile]::Open($archivePath, [System.IO.Compression.ZipArchiveMode]::Create)
$archived = [System.Collections.Generic.List[object]]::new()
try {
    foreach ($record in $inventory) {
        $relative = $record.path
        $isSource = $relative -match '\.(py|ps1|mjs|js|jsx|ts|tsx|css|html|md|txt|json|yaml|yml|toml|bib|csv|ipynb)$' -or
            $relative -match '(^|/)(LICENSE|\.gitignore|\.python-version|Dockerfile|\.env\.example)$' -or
            $relative.StartsWith('term_paper/report/assets/')
        $skip = $relative -match '(^|/)(\.venv[^/]*|node_modules|__pycache__|\.pytest_cache|\.uv-cache|\.ipython|\.expo|dist)(/|$)' -or
            ($relative -match '(^|/)\.env($|\.)' -and $relative -notmatch '(^|/)\.env\.example$') -or
            $relative -match '^(datasets/|A05/datasets/|A06/datasets/|term_paper/knowledge_rag/data/)' -or
            $relative -match '^term_paper/report/qa' -or
            $relative -match '^artifacts/'
        if ($isSource -and -not $skip) {
            $path = Resolve-WorkspaceTarget $relative
            if ((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() -ne $record.sha256) {
                # Plan status may be updated after the initial inventory. Capture current bytes explicitly.
                $record.sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
            }
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive, $path, $relative, [System.IO.Compression.CompressionLevel]::Optimal
            ) | Out-Null
            $archived.Add([pscustomobject]@{path=$relative; sha256=$record.sha256})
        }
    }
}
finally { $archive.Dispose() }
$archived | Export-Csv -LiteralPath (Join-Path $releaseRoot 'source_snapshot_manifest.csv') -NoTypeInformation -Encoding UTF8
}
else {
    $archived = @(Import-Csv -LiteralPath (Join-Path $releaseRoot 'source_snapshot_manifest.csv'))
}

# Verify every ZIP member before cleaning the source tree.
$archive = [System.IO.Compression.ZipFile]::OpenRead($archivePath)
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    foreach ($record in $archived) {
        $stream = $archive.GetEntry($record.path).Open()
        try { $actual = [System.BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
        finally { $stream.Dispose() }
        if ($actual -ne $record.sha256) { throw "Snapshot verification failed: $($record.path)" }
    }
}
finally { $archive.Dispose(); $sha.Dispose() }

# Preserve the small old inference bundle so app imports and existing demos remain usable.
$runtimeFiles = @(
    'term_paper/artifacts/models/ch2/ch2_diabetes_binary_numpy_seed42.npz',
    'term_paper/artifacts/models/ch2/ch2_diabetes_binary_preprocessor.joblib',
    'term_paper/artifacts/models/ch3/ch3_eurosat_numpy_seed42.npz',
    'term_paper/artifacts/models/ch3/ch3_eurosat_preprocessor.json',
    'term_paper/artifacts/models/ch4/ch4_online_retail_customer_week_numpy_seed42.npz',
    'term_paper/artifacts/models/ch4/ch4_aapl_next_close_numpy_seed42.npz',
    'A06/models/preprocessing/customer_feature_scaler.joblib',
    'A06/models/preprocessing/stock_feature_scaler.joblib',
    'A06/models/preprocessing/stock_target_scaler.joblib'
)
foreach ($relative in $runtimeFiles) {
    Move-Scoped $relative ('artifacts/models/v2/' + [System.IO.Path]::GetFileName($relative))
}
Move-Scoped 'term_paper/artifacts/metrics' 'releases/v2/metrics'

# Preserve private local settings without placing their values in logs or release ZIPs.
if (Test-Path -LiteralPath (Join-Path $workspace 'mobile/.env')) {
    Move-Scoped 'mobile/.env' '.local/phase20/mobile.env'
}

$preRemove = @(
    'backend/__pycache__', 'web/node_modules', 'web/dist',
    '.pytest_cache', '.uv-cache', '.ipython',
    'term_paper/report/__pycache__'
)
foreach ($target in $preRemove) { Remove-Scoped $target 'Recreate from dependency lockfile or report renderer' }

# Move only verified scoped paths. Original namespaces are kept for serialized Ch5 object compatibility.
foreach ($mapping in $migrations) { Move-Scoped $mapping[0] $mapping[1] }
foreach ($target in @('report/qa', 'report/qa_phase8', 'report/qa_phase19')) {
    Remove-Scoped $target 'Rebuild from preserved DOCX; final PDF and release QA metadata are in releases/v2'
}

# Retirement targets contain only source already captured in the verified snapshot, or old generated output.
$retire = @('A05', 'A06', 'mobile', 'datasets', 'term_paper')
foreach ($target in $retire) {
    Remove-Scoped $target 'releases/v2/source_snapshot.zip for sources; original Git HEAD for tracked data/output'
}
foreach ($target in @('customer_behavior', 'house_price', 'diabetes')) {
    Remove-Scoped ('experiments/notebooks/legacy/pipeline/' + $target) 'Original Git HEAD and archived notebook'
}
foreach ($target in @('cifar10', 'customer_behavior', 'house_price', 'mnist', 'diabetes', 'archived_tabular')) {
    Remove-Scoped ('experiments/notebooks/legacy/pipeline04/' + $target) 'Original Git HEAD and archived notebook'
}

# Existing root artifact children are all obsolete; preserve the new V3 subdirectories.
$keepArtifactDirectories = @('manifests', 'metrics', 'figures', 'models', 'predictions')
foreach ($item in Get-ChildItem -LiteralPath (Join-Path $workspace 'artifacts') -Force) {
    if ($item.Name -notin $keepArtifactDirectories) {
        Remove-Scoped ('artifacts/' + $item.Name) 'Original Git HEAD; derived from legacy notebooks/report tools'
    }
}

# Remove caches that moved along with retained source trees.
$cacheDirs = Get-ChildItem -LiteralPath $workspace -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @('__pycache__', '.pytest_cache', '.ipynb_checkpoints') -and
        -not $_.FullName.StartsWith((Join-Path $workspace '.git') + '\', [System.StringComparison]::OrdinalIgnoreCase) -and
        -not $_.FullName.StartsWith((Join-Path $workspace 'data\raw') + '\', [System.StringComparison]::OrdinalIgnoreCase) } |
    Sort-Object { $_.FullName.Length } -Descending
foreach ($item in $cacheDirs) {
    Remove-Scoped $item.FullName.Substring($workspace.Length + 1) 'Generated cache'
}

foreach ($relative in @(
    'src/common', 'src/ch02_ml', 'src/ch03_cnn', 'src/ch04_rnn_lstm', 'src/ch05_knowledge_rag',
    'src/ch06_multi_agent', 'experiments/runners', 'data/interim', 'data/processed', 'data/splits',
    'report/build', 'report/tools', 'releases/v3'
)) { New-Item -ItemType Directory -Force -Path (Resolve-WorkspaceTarget $relative) | Out-Null }

$events | Export-Csv -LiteralPath (Join-Path $manifestRoot 'operations.csv') -NoTypeInformation -Encoding UTF8
$releaseFiles = Get-ChildItem -LiteralPath $releaseRoot -File -Recurse | ForEach-Object {
    [pscustomobject]@{
        path=$_.FullName.Substring($workspace.Length + 1).Replace('\', '/')
        bytes=$_.Length
        sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
@{
    git_head=(& git rev-parse HEAD)
    generated_at=(Get-Date).ToString('o')
    snapshot_entries=$archived.Count
    files=@($releaseFiles)
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $releaseRoot 'release_manifest.json') -Encoding UTF8

Write-Output ("Verified source snapshot entries: " + $archived.Count)
Write-Output ("Migration/deletion operations: " + $events.Count)
