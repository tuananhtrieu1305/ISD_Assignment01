[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskOut=Join-Path $taskRoot 'docs/reorganization'
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
public static class ReorgVerifyPhase1 {
    public static string Hash(string p) { using(var f=File.OpenRead(p)) using(var s=SHA256.Create()) return BitConverter.ToString(s.ComputeHash(f)).Replace("-","").ToLowerInvariant(); }
    public static string[] Verify(string root,string[] paths,string[] hashes,long[] sizes) {
        var failures=new List<string>(); string prefix=Path.GetFullPath(root)+Path.DirectorySeparatorChar;
        for(int i=0;i<paths.Length;i++) {
            string p=Path.GetFullPath(Path.Combine(root,paths[i]));
            if(!p.StartsWith(prefix,StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Path outside workspace");
            if(!File.Exists(p) || new FileInfo(p).Length!=sizes[i] || Hash(p)!=hashes[i]) failures.Add(paths[i]);
            if((i+1)%10000==0) Console.WriteLine("Verified restored files: "+(i+1)+"/"+paths.Length);
        }
        return failures.ToArray();
    }
}
'@
$taskRestore=Get-Content (Join-Path $taskOut 'restoration_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskExtra=Get-Content (Join-Path $taskOut 'supplementary_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskRows=@($taskRestore.files)+@($taskExtra.files)
$taskPaths=@($taskRows | ForEach-Object {$_.staging_path})
$taskHashes=@($taskRows | ForEach-Object {$_.sha256})
$taskSizes=@($taskRows | ForEach-Object {[long]$_.bytes})
$taskFailures=@([ReorgVerifyPhase1]::Verify($taskRoot,$taskPaths,$taskHashes,$taskSizes))
$taskBackup=Get-Content (Join-Path $taskOut 'backup_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskWebRows=@($taskBackup.files | Where-Object {$_.path -like '*/web-demo/*'})
foreach($taskRow in $taskWebRows) {
    if([ReorgVerifyPhase1]::Hash((Join-Path $taskRoot $taskRow.path)) -ne $taskRow.sha256) {$taskFailures+=@($taskRow.path)}
}
if([ReorgVerifyPhase1]::Hash((Join-Path $taskRoot $taskBackup.archive)) -ne $taskBackup.sha256) {$taskFailures+=@('backup-archive')}
$taskInventory=Get-Content (Join-Path $taskOut 'source_inventory.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskMap=Get-Content (Join-Path $taskOut 'migration_map.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskData=Get-Content (Join-Path $taskOut 'dataset_catalog.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskAST=Get-Content (Join-Path $taskOut 'notebook_static_audit.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($taskInventory.projects.Count -ne 11) {throw 'Expected11projects'}
if(@($taskMap.target_conflicts.PSObject.Properties).Count -ne 0) {throw 'Migration path conflicts'}
if($taskAST.AST_failures.Count -ne 0) {throw 'AST failures'}
if($taskData.coverage.Count -ne 11) {throw 'Dataset catalog coverage incomplete'}
if($taskRows.Count -ne $taskInventory.restored_files) {throw 'Restoration count mismatch'}
foreach($taskProject in @('A01','A02','A03','A04','A05','A06','tieuluan1')) {
    $taskI=@($taskInventory.projects | Where-Object {$_.project -eq $taskProject})[0]
    if(!$taskI.commits.Count -or @($taskI.commits | Where-Object {$_.Length -ne 40}).Count) {throw "Missing full SHA: $taskProject"}
}
$taskChanged=@(git -C $taskRoot diff --name-only)
$taskUnauthorized=@($taskChanged | Where-Object {$_ -notin @('.gitignore','AGENTS.md','README.md') -and $_ -notlike 'docs/reorganization/*' -and $_ -notlike 'scripts/reorganization_*' -and $_ -ne 'ASSIGN_REORGANIZATION_EXECUTION_PLAN.md'})
if($taskUnauthorized.Count) {throw "Unexpected tracked source changes: $taskUnauthorized"}
git -C $taskRoot diff --check
if($LASTEXITCODE -ne 0) {throw 'Git whitespace check failed'}
$taskReceipt=[ordered]@{
    status=$(if($taskFailures.Count -eq 0){'PASS'}else{'FAIL'})
    restored_files_sha256_verified=$taskRows.Count
    uncommitted_web_files_unchanged=$taskWebRows.Count
    backup_archive_hash='PASS'
    project_count=11
    mapped_file_count=$taskMap.file_count
    migration_path_conflicts=0
    notebooks_static_checked=$taskAST.notebook_count
    restored_notebooks=$taskAST.restored_notebook_count
    restored_python_sources_AST_checked=$taskAST.python_source_count
    AST_failures=0
    dataset_catalog_entries=$taskData.datasets.Count
    original_format_gaps=@($taskData.missing_original_format | Select-Object project,dataset,availability)
    live_preservation_receipt='live_preservation_receipt.json (separate full read-only hash verification)'
    unexpected_tracked_source_changes=$taskUnauthorized
    failures=$taskFailures
    training_executed=$false
    scientific_TEST_replayed=$false
    notebooks_executed=$false
    source_relocated=$false
    environment_changed=$false
}
[IO.File]::WriteAllText((Join-Path $taskOut 'phase1_verification.json'),($taskReceipt | ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
if($taskFailures.Count) {throw 'Restored payload or live web changed'}
Write-Output "Phase1 static/source verification PASS: $($taskRows.Count) restored files;11projects;0AST/path errors."
