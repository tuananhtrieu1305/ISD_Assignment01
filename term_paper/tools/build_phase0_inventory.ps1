[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
$manifestRoot = Join-Path $workspace 'term_paper\artifacts\manifests'
$folderManifestRoot = Join-Path $manifestRoot 'folder_manifests'
[void](New-Item -ItemType Directory -Force -Path $manifestRoot, $folderManifestRoot)

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Content, $encoding)
}

function Write-CsvUtf8NoBom {
    param([string]$Path, [object[]]$Rows)
    $content = ($Rows | ConvertTo-Csv -NoTypeInformation) -join "`r`n"
    if ($content.Length -gt 0) {
        $content += "`r`n"
    }
    Write-Utf8NoBom -Path $Path -Content $content
}

function Get-RelativePathNormalized {
    param([string]$Path)
    $absolute = [System.IO.Path]::GetFullPath($Path)
    if ($absolute.StartsWith($workspace + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $absolute.Substring($workspace.Length + 1).Replace('\', '/')
    }
    return $absolute.Replace('\', '/')
}

function Get-FileSha256 {
    param([string]$Path)
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function New-FileHashRecord {
    param(
        [string]$Category,
        [string]$Chapter,
        [string]$Dataset,
        [string]$Path,
        [string]$Kind = 'file'
    )
    $item = Get-Item -LiteralPath $Path
    return [pscustomobject][ordered]@{
        category = $Category
        chapter = $Chapter
        dataset = $Dataset
        path = Get-RelativePathNormalized $item.FullName
        kind = $Kind
        size_bytes = [int64]$item.Length
        file_count = 1
        sha256 = Get-FileSha256 $item.FullName
        hash_basis = 'file_content'
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        manifest_path = ''
    }
}

function New-FolderManifestRecord {
    param(
        [string]$Id,
        [string]$Category,
        [string]$Chapter,
        [string]$Dataset,
        [string]$Path,
        [string]$IncludeRegex = '.*',
        [string]$ExcludeRegex = '^$'
    )
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $files = @(
        Get-ChildItem -LiteralPath $resolved -Recurse -File |
            Where-Object {
                $rel = Get-RelativePathNormalized $_.FullName
                ($rel -match $IncludeRegex) -and ($rel -notmatch $ExcludeRegex)
            } |
            Sort-Object FullName
    )
    $rows = @(
        foreach ($file in $files) {
            [pscustomobject][ordered]@{
                path = Get-RelativePathNormalized $file.FullName
                size_bytes = [int64]$file.Length
                last_write_utc = $file.LastWriteTimeUtc.ToString('o')
            }
        }
    )
    $manifestPath = Join-Path $folderManifestRoot ($Id + '.csv')
    Write-CsvUtf8NoBom -Path $manifestPath -Rows $rows
    $totalBytes = [int64](($files | Measure-Object -Property Length -Sum).Sum)
    if ($null -eq $totalBytes) { $totalBytes = 0 }
    $latest = $files | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    return [pscustomobject][ordered]@{
        category = $Category
        chapter = $Chapter
        dataset = $Dataset
        path = Get-RelativePathNormalized $resolved
        kind = 'folder_manifest'
        size_bytes = $totalBytes
        file_count = $files.Count
        sha256 = Get-FileSha256 $manifestPath
        hash_basis = 'sorted_path_size_mtime_manifest'
        last_write_utc = if ($null -ne $latest) { $latest.LastWriteTimeUtc.ToString('o') } else { '' }
        manifest_path = Get-RelativePathNormalized $manifestPath
    }
}

function Get-NotebookAuditRecord {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path
    $notebook = Get-Content -Raw -Encoding UTF8 -LiteralPath $item.FullName | ConvertFrom-Json
    $cells = @($notebook.cells)
    $markdownCells = @($cells | Where-Object { $_.cell_type -eq 'markdown' })
    $codeCells = @($cells | Where-Object { $_.cell_type -eq 'code' })
    $executedCells = @($codeCells | Where-Object { $null -ne $_.execution_count })
    $errorOutputs = 0
    $outputCount = 0
    $outputsWithoutExecutionCount = 0
    foreach ($cell in $codeCells) {
        $outputs = @($cell.outputs)
        $outputCount += $outputs.Count
        $errorOutputs += @($outputs | Where-Object { $_.output_type -eq 'error' }).Count
        if (($null -eq $cell.execution_count) -and ($outputs.Count -gt 0)) {
            $outputsWithoutExecutionCount += 1
        }
    }

    $sourceParts = New-Object System.Collections.Generic.List[string]
    foreach ($cell in $cells) {
        if ($null -ne $cell.source) {
            [void]$sourceParts.Add((@($cell.source) -join ''))
        }
    }
    $allSource = $sourceParts -join "`n"
    $title = ''
    foreach ($cell in $markdownCells) {
        $text = @($cell.source) -join ''
        $match = [regex]::Match($text, '(?m)^#\s+(.+)$')
        if ($match.Success) {
            $title = $match.Groups[1].Value.Trim()
            break
        }
    }

    $executionCounts = @($executedCells | ForEach-Object { [int]$_.execution_count } | Sort-Object)
    $contiguous = $false
    if (($codeCells.Count -gt 0) -and ($executionCounts.Count -eq $codeCells.Count)) {
        $expected = @(1..$codeCells.Count)
        $contiguous = (($executionCounts -join ',') -eq ($expected -join ','))
    }

    $pathNormalized = Get-RelativePathNormalized $item.FullName
    $chapter = if ($pathNormalized.StartsWith('pipeline/')) { '2' } elseif ($pathNormalized.StartsWith('A05/')) { '3' } elseif ($pathNormalized.StartsWith('A06/')) { '4' } else { '' }
    $issues = New-Object System.Collections.Generic.List[string]
    if ($errorOutputs -gt 0) { [void]$issues.Add('error_outputs_present') }
    if ($outputsWithoutExecutionCount -gt 0) { [void]$issues.Add('outputs_without_execution_count') }
    if (($codeCells.Count -gt 0) -and (-not $contiguous)) { [void]$issues.Add('execution_counts_not_complete_contiguous') }

    return [pscustomobject][ordered]@{
        chapter = $chapter
        path = $pathNormalized
        title = $title
        sha256 = Get-FileSha256 $item.FullName
        size_bytes = [int64]$item.Length
        nbformat = [int]$notebook.nbformat
        total_cells = $cells.Count
        markdown_cells = $markdownCells.Count
        code_cells = $codeCells.Count
        executed_code_cells = $executedCells.Count
        unexecuted_code_cells = $codeCells.Count - $executedCells.Count
        output_count = $outputCount
        error_outputs = $errorOutputs
        outputs_without_execution_count = $outputsWithoutExecutionCount
        execution_counts_complete_contiguous = $contiguous
        numpy = [regex]::IsMatch($allSource, '(?i)\bnumpy\b|\bnp\.')
        sklearn = [regex]::IsMatch($allSource, '(?i)sklearn|scikit-learn')
        keras = [regex]::IsMatch($allSource, '(?i)\bkeras\b|SimpleRNN|Sequential')
        tensorflow = [regex]::IsMatch($allSource, '(?i)tensorflow|\btf\.')
        pytorch = [regex]::IsMatch($allSource, '(?i)\bpytorch\b|\btorch\b|torch\.')
        scratch_signal = [regex]::IsMatch($allSource, '(?i)from scratch|def\s+(relu|sigmoid|softmax|conv2d_valid|max_pool2d|train_teacher|train_improved|binary_cross_entropy)|manual rnn forward')
        deployment_signal = [regex]::IsMatch($allSource, '(?i)streamlit|fastapi|flask|gradio|docker|deployment|api endpoint')
        http_url_count = [regex]::Matches($allSource, 'https?://').Count
        issues = $issues -join ';'
    }
}

$gitStatusBefore = @(& git -C $workspace status --porcelain=v1 2>$null)

$notebookPaths = @(
    Get-ChildItem -LiteralPath (Join-Path $workspace 'pipeline'), (Join-Path $workspace 'A05'), (Join-Path $workspace 'A06') -Recurse -File -Filter '*.ipynb' |
        Sort-Object FullName |
        Select-Object -ExpandProperty FullName
)
$notebookAudit = @($notebookPaths | ForEach-Object { Get-NotebookAuditRecord -Path $_ })
$notebookAuditPath = Join-Path $manifestRoot 'notebook_audit.csv'
Write-CsvUtf8NoBom -Path $notebookAuditPath -Rows $notebookAudit

$hashRecords = New-Object System.Collections.Generic.List[object]
foreach ($notebook in $notebookPaths) {
    $relative = Get-RelativePathNormalized $notebook
    $chapter = if ($relative.StartsWith('pipeline/')) { '2' } elseif ($relative.StartsWith('A05/')) { '3' } else { '4' }
    [void]$hashRecords.Add((New-FileHashRecord -Category 'notebook' -Chapter $chapter -Dataset '' -Path $notebook))
}

$importantRawFiles = @(
    @{ chapter='2'; dataset='CDC Diabetes binary'; path='datasets\diabetes\diabetes.csv' },
    @{ chapter='2'; dataset='Vietnam House Price'; path='datasets\housing_price\vietnam_housing_dataset.csv' },
    @{ chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior\customers.csv' },
    @{ chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior\products.csv' },
    @{ chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior\transactions.csv' },
    @{ chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior\sessions.csv' },
    @{ chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior\reviews.csv' },
    @{ chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior\README.md' },
    @{ chapter='3'; dataset='CDC Diabetes 012'; path='A05\datasets\diabetes\diabetes_012_health_indicators_BRFSS2015.csv' },
    @{ chapter='4'; dataset='UCI Online Retail II'; path='A06\datasets\customer\online_retail_II.xlsx' },
    @{ chapter='4'; dataset='AAPL 2015-2025'; path='A06\datasets\stock\AAPL_2015_2025.csv' }
)
foreach ($record in $importantRawFiles) {
    $absolute = Join-Path $workspace $record.path
    if (Test-Path -LiteralPath $absolute) {
        [void]$hashRecords.Add((New-FileHashRecord -Category 'raw_dataset' -Chapter $record.chapter -Dataset $record.dataset -Path $absolute))
    }
}

$folderRecords = New-Object System.Collections.Generic.List[object]
$folderSpecs = @(
    @{ id='ch2_customer_behavior_top_level'; category='raw_dataset_group'; chapter='2'; dataset='Synthetic Customer Behavior'; path='datasets\customer_behavior'; include='^datasets/customer_behavior/[^/]+$'; exclude='^$' },
    @{ id='ch3_eurosat'; category='raw_dataset_group'; chapter='3'; dataset='EuroSAT'; path='A05\datasets\eurosat\EuroSAT_RGB'; include='.*'; exclude='^$' },
    @{ id='ch3_oxford_pets'; category='raw_dataset_group'; chapter='3'; dataset='Oxford-IIIT Pet'; path='A05\datasets\oxford_pets'; include='.*'; exclude='^$' },
    @{ id='ch4_processed_data'; category='processed_dataset_group'; chapter='4'; dataset='RNN shared processed arrays'; path='A06\datasets\processed'; include='.*'; exclude='^$' },
    @{ id='ch3_figures'; category='figure_group'; chapter='3'; dataset='A05 CNN'; path='A05\results\figures'; include='(?i)\.(png|jpg|jpeg|svg)$'; exclude='^$' },
    @{ id='ch4_figures'; category='figure_group'; chapter='4'; dataset='A06 RNN'; path='A06\results\figures'; include='(?i)\.(png|jpg|jpeg|svg)$'; exclude='^$' }
)
foreach ($spec in $folderSpecs) {
    $absolute = Join-Path $workspace $spec.path
    if (Test-Path -LiteralPath $absolute) {
        $folderRecord = New-FolderManifestRecord -Id $spec.id -Category $spec.category -Chapter $spec.chapter -Dataset $spec.dataset -Path $absolute -IncludeRegex $spec.include -ExcludeRegex $spec.exclude
        [void]$folderRecords.Add($folderRecord)
        [void]$hashRecords.Add($folderRecord)
    }
}

$checkpointFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $workspace 'pipeline') -Recurse -File |
        Where-Object { $_.Extension -in @('.npz', '.joblib') }
    Get-ChildItem -LiteralPath (Join-Path $workspace 'A05\models') -Recurse -File |
        Where-Object { $_.Extension -in @('.keras', '.pt', '.pth', '.npz', '.joblib') }
    Get-ChildItem -LiteralPath (Join-Path $workspace 'A06\models') -Recurse -File |
        Where-Object { $_.Extension -in @('.keras', '.pt', '.pth', '.npz', '.joblib') }
)
$checkpointFiles = @($checkpointFiles | Sort-Object FullName -Unique)
foreach ($file in $checkpointFiles) {
    $relative = Get-RelativePathNormalized $file.FullName
    $chapter = if ($relative.StartsWith('pipeline/')) { '2' } elseif ($relative.StartsWith('A05/')) { '3' } else { '4' }
    [void]$hashRecords.Add((New-FileHashRecord -Category 'model_or_preprocessor' -Chapter $chapter -Dataset '' -Path $file.FullName))
}

$evidenceFiles = New-Object System.Collections.Generic.List[System.IO.FileInfo]
foreach ($pattern in @(
    'pipeline\*\*.csv', 'pipeline\*\*.json',
    'A05\results\metrics\*.csv', 'A05\results\metrics\*.json',
    'A05\results\hyperparameters\*.csv', 'A05\results\hyperparameters\*.json',
    'A05\results\dataset_audit.json',
    'A06\results\metrics\*.json', 'A06\results\metrics\*.md',
    'A06\results\predictions\*.csv'
)) {
    foreach ($file in Get-ChildItem -Path (Join-Path $workspace $pattern) -File -ErrorAction SilentlyContinue) {
        [void]$evidenceFiles.Add($file)
    }
}
$evidenceFiles = @($evidenceFiles | Sort-Object FullName -Unique)
foreach ($file in $evidenceFiles) {
    $relative = Get-RelativePathNormalized $file.FullName
    $chapter = if ($relative.StartsWith('pipeline/')) { '2' } elseif ($relative.StartsWith('A05/')) { '3' } else { '4' }
    $category = if ($relative -match '/predictions/') { 'prediction' } elseif ($relative -match 'hyperparameter') { 'hyperparameter_result' } else { 'metric_or_metadata' }
    [void]$hashRecords.Add((New-FileHashRecord -Category $category -Chapter $chapter -Dataset '' -Path $file.FullName))
}

$reportFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $workspace 'A05\report') -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.docx', '.md', '.json') }
    Get-ChildItem -LiteralPath (Join-Path $workspace 'A06\report') -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in @('.docx', '.md', '.json') }
)
$reportFiles = @($reportFiles | Sort-Object FullName -Unique)
foreach ($file in $reportFiles) {
    $chapter = if ((Get-RelativePathNormalized $file.FullName).StartsWith('A05/')) { '3' } else { '4' }
    [void]$hashRecords.Add((New-FileHashRecord -Category 'report' -Chapter $chapter -Dataset '' -Path $file.FullName))
}

$externalStyleReference = 'C:\Users\anhca\Documents\Intel_sys_dev\A06_Assignment_Report.docx'
if (Test-Path -LiteralPath $externalStyleReference) {
    [void]$hashRecords.Add((New-FileHashRecord -Category 'external_style_reference' -Chapter '' -Dataset '' -Path $externalStyleReference))
}

$hashRecordsSorted = @($hashRecords | Sort-Object category, chapter, dataset, path)
$sourceHashesPath = Join-Path $manifestRoot 'source_hashes.csv'
Write-CsvUtf8NoBom -Path $sourceHashesPath -Rows $hashRecordsSorted

$inventory = [ordered]@{
    schema_version = 1
    generated_at_client_date = '2026-10-05'
    generated_at_utc = [DateTime]::UtcNow.ToString('o')
    workspace = $workspace.Replace('\', '/')
    scope = @('pipeline', 'A05', 'A06', 'selected root datasets', 'external DOCX style reference')
    mutation_policy = 'Read source artifacts only; all generated files are under term_paper/.'
    git_status_before = $gitStatusBefore
    notebooks = [ordered]@{
        count = $notebookAudit.Count
        by_chapter = [ordered]@{
            chapter_2 = @($notebookAudit | Where-Object { $_.chapter -eq '2' }).Count
            chapter_3 = @($notebookAudit | Where-Object { $_.chapter -eq '3' }).Count
            chapter_4 = @($notebookAudit | Where-Object { $_.chapter -eq '4' }).Count
        }
        error_output_count = [int](($notebookAudit | Measure-Object -Property error_outputs -Sum).Sum)
        notebooks_with_execution_metadata_issues = @($notebookAudit | Where-Object { $_.issues -ne '' } | Select-Object -ExpandProperty path)
        audit_path = Get-RelativePathNormalized $notebookAuditPath
    }
    datasets = @($folderRecords | Where-Object { $_.category -match 'dataset' })
    model_and_preprocessor_artifact_count = $checkpointFiles.Count
    metric_prediction_metadata_file_count = $evidenceFiles.Count
    figure_groups = @($folderRecords | Where-Object { $_.category -eq 'figure_group' })
    report_file_count = $reportFiles.Count + $(if (Test-Path -LiteralPath $externalStyleReference) { 1 } else { 0 })
    hash_record_count = $hashRecordsSorted.Count
    hash_registry_path = Get-RelativePathNormalized $sourceHashesPath
    folder_manifest_directory = Get-RelativePathNormalized $folderManifestRoot
}
$inventoryPath = Join-Path $manifestRoot 'source_inventory.json'
Write-Utf8NoBom -Path $inventoryPath -Content (($inventory | ConvertTo-Json -Depth 12) + "`n")

$summary = [ordered]@{
    source_inventory = Get-RelativePathNormalized $inventoryPath
    source_hashes = Get-RelativePathNormalized $sourceHashesPath
    notebook_audit = Get-RelativePathNormalized $notebookAuditPath
    notebook_count = $notebookAudit.Count
    hash_record_count = $hashRecordsSorted.Count
    folder_manifest_count = $folderRecords.Count
    git_status_before_count = $gitStatusBefore.Count
}
Write-Output ($summary | ConvertTo-Json -Depth 4)
