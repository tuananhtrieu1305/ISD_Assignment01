[CmdletBinding()]
param([switch]$ArchiveOnly)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskP3=Join-Path $taskRoot 'docs/reorganization/phase3'
Add-Type -AssemblyName System.IO.Compression.FileSystem
function Assert-WorkspacePath([string]$Path){
    $taskResolved=[IO.Path]::GetFullPath($Path)
    if(-not $taskResolved.StartsWith($taskRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Cleanup target outside workspace'}
    if($taskResolved -match '\\(\.git|\.local|node_modules|datasets|artifacts)(\\|$)' -and $taskResolved -notmatch '\\apps\\web\\node_modules(\\|$)'){throw 'Protected cleanup target'}
    return $taskResolved
}
$taskArchiveDir=Join-Path $taskRoot 'tieuluan3/provenance/build_history'
[IO.Directory]::CreateDirectory($taskArchiveDir)|Out-Null
$taskArchive=Join-Path $taskArchiveDir 'root-dist-before-reorg.zip'
$taskDist=Assert-WorkspacePath (Join-Path $taskRoot 'dist')
if((Test-Path -LiteralPath $taskDist) -and ($ArchiveOnly -or -not (Test-Path (Join-Path $taskP3 'build_history_backup.json')))){
    if(-not (Test-Path -LiteralPath $taskArchive)){[IO.Compression.ZipFile]::CreateFromDirectory($taskDist,$taskArchive,[IO.Compression.CompressionLevel]::Optimal,$true)}
    $taskZip=[IO.Compression.ZipFile]::OpenRead($taskArchive)
    try{
        $taskFiles=@([IO.Directory]::GetFiles($taskDist,'*',[IO.SearchOption]::AllDirectories))
        $taskMembers=@($taskZip.Entries|Where-Object {-not $_.FullName.EndsWith('/')})
        if($taskFiles.Count -ne $taskMembers.Count){throw 'Generated build archive count mismatch'}
        foreach($taskEntry in $taskMembers){
            $taskRelative=$taskEntry.FullName.Substring('dist/'.Length)
            $taskOriginal=Join-Path $taskDist $taskRelative
            if(-not (Test-Path -LiteralPath $taskOriginal) -or (Get-Item -LiteralPath $taskOriginal).Length -ne $taskEntry.Length){throw 'Generated build archive size mismatch'}
            $taskHash=[Security.Cryptography.SHA256]::Create()
            $taskArchivedStream=$taskEntry.Open()
            try{$taskArchivedHash=[BitConverter]::ToString($taskHash.ComputeHash($taskArchivedStream)).Replace('-','').ToLowerInvariant()}finally{$taskArchivedStream.Dispose();$taskHash.Dispose()}
            if($taskArchivedHash -ne (Get-FileHash -LiteralPath $taskOriginal -Algorithm SHA256).Hash.ToLowerInvariant()){throw 'Generated build archive byte mismatch'}
        }
    }finally{$taskZip.Dispose()}
    $taskBackup=[ordered]@{status='PASS';path='tieuluan3/provenance/build_history/root-dist-before-reorg.zip';sha256=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant();file_count=$taskFiles.Count;bytes=(Get-Item -LiteralPath $taskArchive).Length;note='Generated historical build directories archived outside active source; no unique scientific baseline deleted'}
    [IO.File]::WriteAllText((Join-Path $taskP3 'build_history_backup.json'),($taskBackup|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
}
if($ArchiveOnly){Write-Output 'Generated build history archive ready';return}
foreach($taskReceipt in @('e2e.json','clean_checkout.json','original_byte_preservation.json')){
    $taskDoc=Get-Content (Join-Path $taskP3 $taskReceipt) -Raw -Encoding UTF8|ConvertFrom-Json
    if($taskDoc.status -ne 'PASS'){throw "Cleanup gate not PASS: $taskReceipt"}
}
if(-not (Test-Path (Join-Path $taskP3 'build_history_backup.json'))){throw 'Generated build history backup missing'}
$taskTargets=@('apps','dist','.ruff_cache','docs/reorganization/staging','.render-reorg','docs/reorganization/phase3/clean_checkout','docs/reorganization/phase3/unit_tmp')
$taskProjects=@('A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02')
foreach($taskProject in $taskProjects){foreach($taskName in @('reference_ui','reference_backend','legacy_runtime')){$taskTargets+=@("$taskProject/web/$taskName")}}
$taskTargets+=@(Get-ChildItem (Join-Path $taskRoot 'docs/reorganization/phase2') -Directory -Filter 'unit_tmp_*'|ForEach-Object {$_.FullName.Substring($taskRoot.Length+1)})
$taskMap=Get-Content (Join-Path $taskRoot 'docs/reorganization/phase2/canonical_map.json') -Raw -Encoding UTF8|ConvertFrom-Json
$taskOverrides=Get-Content (Join-Path $taskP3 'preservation_overrides.json') -Raw -Encoding UTF8|ConvertFrom-Json
$taskIndex=@{};foreach($taskEntry in $taskOverrides.files){$taskIndex[$taskEntry.original_baseline]=$taskEntry.baseline_path}
$taskPrefixes=@($taskTargets|ForEach-Object {$_.Replace('\','/').TrimEnd('/')+'/'})
foreach($taskEntry in $taskMap.files){
    $taskBaseline=$taskEntry.baseline_path
    if($taskIndex.ContainsKey($taskBaseline)){$taskBaseline=$taskIndex[$taskBaseline]}
    foreach($taskPrefix in $taskPrefixes){if($taskBaseline.StartsWith($taskPrefix,[StringComparison]::OrdinalIgnoreCase)){throw "Refuse cleanup of an immutable baseline: $taskBaseline"}}
}
$taskRemoved=@()
foreach($taskTarget in $taskTargets){
    $taskAbsolute=Assert-WorkspacePath (Join-Path $taskRoot $taskTarget)
    if(-not (Test-Path -LiteralPath $taskAbsolute)){continue}
    # Canonical scientific baselines and original web copies live outside every deletion target.
    Remove-Item -LiteralPath $taskAbsolute -Recurse -Force -ErrorAction Stop
    $taskRemoved+=@($taskTarget)
    Write-Output "Removed verified duplicate/generated path: $taskTarget"
}
$taskDoc=[ordered]@{status='PASS';removed=$taskRemoved;kept=@('all11canonical projects','all datasets/checkpoints/metrics/reports','Phase1backups','Phase3original web snapshots','root node_modules and .local tools','all provenance runtime views','.git');source_gate='Phase3 original-byte SHA256 PASS +11web E2E PASS +3clean-checkout PASS';training_steps=0;scientific_TEST_forward=0}
[IO.File]::WriteAllText((Join-Path $taskP3 'cleanup_receipt.json'),($taskDoc|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
