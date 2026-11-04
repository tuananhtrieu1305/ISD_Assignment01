[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$DocumentPath,
    [Parameter(Mandatory=$true)][string]$ReceiptPath
)
$ErrorActionPreference = 'Stop'
$p35Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$p35Document = (Resolve-Path -LiteralPath $DocumentPath).Path
$p35Receipt = [IO.Path]::GetFullPath((Join-Path $p35Root $ReceiptPath))
if (-not $p35Document.StartsWith($p35Root + '\', [StringComparison]::OrdinalIgnoreCase) -or
    -not $p35Receipt.StartsWith($p35Root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Workspace path guard' }
if (Test-Path -LiteralPath $p35Receipt) { throw 'Receipt already exists' }
$p35Before = (Get-FileHash -LiteralPath $p35Document -Algorithm SHA256).Hash.ToLowerInvariant()
$p35Word = $null
$p35Doc = $null
$p35Result = [ordered]@{ source=$DocumentPath; sha256=$p35Before; status='FAIL'; read_only=$true; saved=$false; existing_word_session_used=$false }
try {
    # Own hidden instance, never attach to or close the user's active document/session.
    $p35Word = New-Object -ComObject Word.Application
    $p35Word.Visible = $false
    $p35Word.DisplayAlerts = 0
    $p35Word.AutomationSecurity = 3
    $p35Result.word_version = $p35Word.Version
    $p35Confirm = $false
    $p35ReadOnly = $true
    $p35AddRecent = $false
    $p35Doc = $p35Word.Documents.Open([ref]$p35Document, [ref]$p35Confirm, [ref]$p35ReadOnly, [ref]$p35AddRecent)
    $p35Result.field_update_first_error_index = $p35Doc.Fields.Update()
    $p35Doc.Repaginate()
    $p35Statistic = 2
    $p35Result.pages = $p35Doc.ComputeStatistics([ref]$p35Statistic)
    $p35Result.tables = $p35Doc.Tables.Count
    $p35Result.bookmarks = $p35Doc.Bookmarks.Count
    $p35Result.sections = $p35Doc.Sections.Count
    $p35Result.paragraphs = $p35Doc.Paragraphs.Count
    $p35Result.status = 'PASS'
    if ($p35Result.field_update_first_error_index -ne 0) { $p35Result.status = 'FAIL' }
} catch {
    $p35Result.error = $_.Exception.Message
} finally {
    $p35NoSave = 0
    if ($null -ne $p35Doc) {
        try { $p35Doc.Close([ref]$p35NoSave) } catch { $p35Result.close_error = $_.Exception.Message }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($p35Doc)
    }
    if ($null -ne $p35Word) {
        try { $p35Word.Quit([ref]$p35NoSave) } catch { $p35Result.quit_error = $_.Exception.Message }
        [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($p35Word)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
$p35Result.source_unchanged = $p35Before -eq (Get-FileHash -LiteralPath $p35Document -Algorithm SHA256).Hash.ToLowerInvariant()
if (-not $p35Result.source_unchanged) { $p35Result.status = 'FAIL' }
$p35Json = $p35Result | ConvertTo-Json -Depth 6
[IO.File]::WriteAllText($p35Receipt, $p35Json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
$p35Json
if ($p35Result.status -ne 'PASS') { throw 'Word read-only open validation failed' }
