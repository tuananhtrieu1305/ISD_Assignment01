param(
    [Parameter(Mandatory = $true)]
    [string]$DocumentPath,
    [Parameter(Mandatory = $true)]
    [string]$BuildLogPath,
    [Parameter(Mandatory = $true)]
    [string]$PageMapPath,
    [string]$PdfPath = ""
)

$ErrorActionPreference = "Stop"
$documentFullPath = [System.IO.Path]::GetFullPath($DocumentPath)
$buildLogFullPath = [System.IO.Path]::GetFullPath($BuildLogPath)
$pageMapFullPath = [System.IO.Path]::GetFullPath($PageMapPath)
$pdfFullPath = if ($PdfPath) { [System.IO.Path]::GetFullPath($PdfPath) } else { "" }

if (-not (Test-Path -LiteralPath $documentFullPath)) {
    throw "DOCX not found: $documentFullPath"
}
if (-not (Test-Path -LiteralPath $buildLogFullPath)) {
    throw "Build log not found: $buildLogFullPath"
}

$targets = (Get-Content -LiteralPath $buildLogFullPath -Raw -Encoding UTF8 | ConvertFrom-Json).navigation_targets
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($documentFullPath, $false, $false, $false)

    # Update footer page-number fields and any other fields in every story range.
    foreach ($story in $document.StoryRanges) {
        $current = $story
        while ($null -ne $current) {
            if ($current.Fields.Count -gt 0) {
                [void]$current.Fields.Update()
            }
            $current = $current.NextStoryRange
        }
    }
    foreach ($section in $document.Sections) {
        foreach ($header in $section.Headers) {
            if ($header.Exists -and $header.Range.Fields.Count -gt 0) {
                [void]$header.Range.Fields.Update()
            }
        }
        foreach ($footer in $section.Footers) {
            if ($footer.Exists -and $footer.Range.Fields.Count -gt 0) {
                [void]$footer.Range.Fields.Update()
            }
        }
    }

    $document.Repaginate()
    $pages = [ordered]@{}
    $missing = New-Object System.Collections.Generic.List[string]
    foreach ($target in $targets) {
        $name = [string]$target.bookmark
        if ($document.Bookmarks.Exists($name)) {
            $bookmark = $document.Bookmarks.Item($name)
            $pages[$name] = [int]$bookmark.Range.Information(3)
        }
        else {
            $missing.Add($name)
        }
    }

    $pageCount = [int]$document.ComputeStatistics(2)
    $document.Save()
    if ($pdfFullPath) {
        $pdfDirectory = Split-Path -Parent $pdfFullPath
        if ($pdfDirectory) {
            New-Item -ItemType Directory -Path $pdfDirectory -Force | Out-Null
        }
        # 17 = wdExportFormatPDF; optimized for print and includes document structure tags.
        $document.ExportAsFixedFormat($pdfFullPath, 17, $false, 0, 0, 1, $pageCount, 0, $true, $true, 1, $true, $true, $false)
    }

    $result = [ordered]@{
        schema_version = 1
        source = "Microsoft Word pagination"
        document = $documentFullPath
        page_count = $pageCount
        resolved_targets = $pages.Count
        missing_targets = @($missing)
        pages = $pages
    }
    $json = $result | ConvertTo-Json -Depth 8
    $pageMapDirectory = Split-Path -Parent $pageMapFullPath
    if ($pageMapDirectory) {
        New-Item -ItemType Directory -Path $pageMapDirectory -Force | Out-Null
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($pageMapFullPath, $json + [Environment]::NewLine, $utf8NoBom)
    Write-Output "Word pagination complete: $pageCount pages, $($pages.Count) targets, $($missing.Count) missing."
}
finally {
    if ($null -ne $document) {
        $document.Close($false)
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($document)
    }
    if ($null -ne $word) {
        $word.Quit()
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
