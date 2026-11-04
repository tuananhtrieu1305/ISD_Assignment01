$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$introPath = Join-Path $repo 'term_paper\report\sections\00_mo_dau.md'
$historyPath = Join-Path $repo 'term_paper\report\sections\01_lich_su_ai.md'
$bibPath = Join-Path $repo 'term_paper\sources\bibliography.bib'
$assetDir = Join-Path $repo 'term_paper\report\assets\ch1'
$timelineCsvPath = Join-Path $assetDir 'timeline_sources.csv'
$timelineMmdPath = Join-Path $assetDir 'ai_history_timeline.mmd'
$timelineSvgPath = Join-Path $assetDir 'ai_history_timeline.svg'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw "ASSERTION FAILED: $Message" }
}

function Get-WordCount {
    param([string]$Text)
    $plain = $Text -replace '(?s)<!--.*?-->', ' '
    $plain = $plain -replace '\[@[^\]]+\]', ' '
    $plain = $plain -replace '[#*`|]', ' '
    return ([regex]::Matches($plain, '[\p{L}\p{N}]+(?:[-][\p{L}\p{N}]+)*')).Count
}

function Assert-Heading {
    param([string]$Text, [string]$Heading)
    $pattern = '(?m)^' + [regex]::Escape($Heading) + '$'
    Assert-True ([regex]::IsMatch($Text, $pattern)) "Missing heading: $Heading"
}

$requiredFiles = @(
    $introPath,
    $historyPath,
    $bibPath,
    $timelineCsvPath,
    $timelineMmdPath,
    $timelineSvgPath,
    (Join-Path $assetDir 'README.md')
)
foreach ($path in $requiredFiles) {
    Assert-True (Test-Path -LiteralPath $path -PathType Leaf) "Missing file: $path"
    Assert-True ((Get-Item -LiteralPath $path).Length -gt 0) "Empty file: $path"
}

$intro = Get-Content -LiteralPath $introPath -Raw -Encoding UTF8
$history = Get-Content -LiteralPath $historyPath -Raw -Encoding UTF8
$bib = Get-Content -LiteralPath $bibPath -Raw -Encoding UTF8
$mmd = Get-Content -LiteralPath $timelineMmdPath -Raw -Encoding UTF8

$introWords = Get-WordCount $intro
$historyWords = Get-WordCount $history
Assert-True ($introWords -ge 1700 -and $introWords -le 2400) "Introduction word count $introWords is outside 1700-2400"
Assert-True ($historyWords -ge 3600 -and $historyWords -le 4800) "Chapter 1 word count $historyWords is outside 3600-4800"

Assert-True ([regex]::IsMatch($intro, '(?m)^# [^#].+$')) 'Introduction title is missing'
foreach ($prefix in @('## 0.1.','## 0.2.','## 0.3.','## 0.4.')) {
    Assert-True ([regex]::IsMatch($intro, '(?m)^' + [regex]::Escape($prefix))) "Missing introduction section: $prefix"
}

# Use numbered-prefix checks to avoid locale-sensitive literal handling.
foreach ($prefix in @('## 1.1.','## 1.2.','## 1.3.','## 1.4.','## 1.5.','## 1.6.')) {
    Assert-True ([regex]::IsMatch($history, '(?m)^' + [regex]::Escape($prefix))) "Missing Chapter 1 section: $prefix"
}
foreach ($prefix in @('### 1.1.1.','### 1.1.2.','### 1.2.1.','### 1.2.2.','### 1.3.1.','### 1.3.2.','### 1.4.1.','### 1.4.2.','### 1.5.1.','### 1.5.2.','### 1.5.3.','### 1.6.1.','### 1.6.2.')) {
    Assert-True ([regex]::IsMatch($history, '(?m)^' + [regex]::Escape($prefix))) "Missing Chapter 1 subsection: $prefix"
}

foreach ($token in @('RQ1','RQ2','RQ3','scratch','Keras','PyTorch','TRAIN','VALIDATION','TEST','inference')) {
    Assert-True ($intro.Contains($token)) "Introduction missing required token: $token"
}
foreach ($token in @('McCulloch','Turing','Dartmouth','perceptron','backpropagation','ImageNet','AlexNet','RNN','LSTM','attention','Transformer','foundation model','AI t' + [char]0x1ea1 + 'o sinh')) {
    Assert-True ($history -match [regex]::Escape($token)) "Chapter 1 missing required topic: $token"
}

Assert-True (-not [regex]::IsMatch($intro + $history, 'https?://')) 'Raw URL found in manuscript body'
Assert-True (-not [regex]::IsMatch($intro + $history, '(?i)\b(TODO|TBD|FIXME|XXX)\b')) 'Placeholder found in manuscript'
Assert-True (-not [regex]::IsMatch($intro + $history, '(?m)^>')) 'Block quote found; long quotations are not permitted in Phase 2'
Assert-True ($history.Contains('../assets/ch1/ai_history_timeline.svg')) 'Chapter 1 does not reference the timeline SVG'

$bibMatches = [regex]::Matches($bib, '(?m)^@[A-Za-z]+\{([^,]+),')
$bibKeys = @($bibMatches | ForEach-Object { $_.Groups[1].Value })
Assert-True ($bibKeys.Count -ge 38) "Bibliography has only $($bibKeys.Count) entries"
$duplicateBibKeys = @($bibKeys | Group-Object | Where-Object { $_.Count -ne 1 })
Assert-True ($duplicateBibKeys.Count -eq 0) 'Duplicate bibliography key found'

$citationMatches = [regex]::Matches($intro + "`n" + $history, '@([A-Za-z0-9_-]+)')
$citationKeys = @($citationMatches | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
Assert-True ($citationKeys.Count -ge 25) "Only $($citationKeys.Count) unique citation keys used"
$missingCitationKeys = @($citationKeys | Where-Object { $_ -notin $bibKeys })
Assert-True ($missingCitationKeys.Count -eq 0) "Citation keys missing from bibliography: $($missingCitationKeys -join ', ')"

$timelineRows = @(Import-Csv -LiteralPath $timelineCsvPath -Encoding UTF8)
Assert-True ($timelineRows.Count -eq 18) "Timeline source map must contain 18 events, found $($timelineRows.Count)"
Assert-True (@($timelineRows.event_id | Sort-Object -Unique).Count -eq $timelineRows.Count) 'Duplicate timeline event_id'
$missingTimelineKeys = @($timelineRows.citation_key | Where-Object { $_ -notin $bibKeys } | Sort-Object -Unique)
Assert-True ($missingTimelineKeys.Count -eq 0) "Timeline citation keys missing from bibliography: $($missingTimelineKeys -join ', ')"
foreach ($year in @('1943','1950','1955','1956','1958','1966','1973','1986','1997','2009','2012','2017','2020','2021','2022')) {
    Assert-True ($mmd.Contains($year)) "Mermaid timeline missing year: $year"
}

try {
    [xml]$svg = Get-Content -LiteralPath $timelineSvgPath -Raw -Encoding UTF8
} catch {
    throw "Timeline SVG is not valid XML: $($_.Exception.Message)"
}
Assert-True ($null -ne $svg.svg) 'Timeline SVG root element is missing'
Assert-True ($svg.svg.width -eq '1600' -and $svg.svg.height -eq '1050') 'Timeline SVG dimensions changed unexpectedly'
Assert-True ($null -ne $svg.svg.title -and $null -ne $svg.svg.desc) 'Timeline SVG requires title and description'

Write-Output 'PHASE 2 VERIFICATION: PASS'
Write-Output "Introduction words: $introWords"
Write-Output "Chapter 1 words: $historyWords"
Write-Output "Unique manuscript citation keys: $($citationKeys.Count)"
Write-Output "Bibliography entries: $($bibKeys.Count)"
Write-Output "Timeline source rows: $($timelineRows.Count)"
