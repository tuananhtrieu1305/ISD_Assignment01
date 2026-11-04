[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskP2=Join-Path $taskRoot 'docs/reorganization/phase2'
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Security.Cryptography;
public static class ReorgPhase3Preserve {
    public static string Hash(string p) {using(var f=File.OpenRead(p)) using(var s=SHA256.Create()) return BitConverter.ToString(s.ComputeHash(f)).Replace("-","").ToLowerInvariant();}
    public static string[] Verify(string root,string[] paths,string[] hashes,long[] sizes) {
        var errors=new System.Collections.Generic.List<string>();
        for(int i=0;i<paths.Length;i++) {
            string path=Path.GetFullPath(Path.Combine(root,paths[i]));
            if(!path.StartsWith(Path.GetFullPath(root)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Unsafe baseline path");
            if(!File.Exists(path) || new FileInfo(path).Length!=sizes[i] || Hash(path)!=hashes[i]) errors.Add(paths[i]);
            if((i+1)%20000==0) Console.WriteLine("Original-byte preservation "+(i+1)+"/"+paths.Length);
        }
        return errors.ToArray();
    }
}
'@
$taskMap=Get-Content (Join-Path $taskP2 'canonical_map.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskOverrides=Get-Content (Join-Path $taskRoot 'docs/reorganization/phase3/preservation_overrides.json') -Raw -Encoding UTF8|ConvertFrom-Json
$taskOverrideIndex=@{}
foreach($taskRow in $taskOverrides.files){$taskOverrideIndex[$taskRow.original_baseline]=$taskRow.baseline_path}
foreach($taskRow in $taskMap.files){if($taskOverrideIndex.ContainsKey($taskRow.baseline_path)){$taskRow.baseline_path=$taskOverrideIndex[$taskRow.baseline_path]}}
$taskPaths=@($taskMap.files | ForEach-Object {$_.baseline_path})
$taskHashes=@($taskMap.files | ForEach-Object {$_.sha256})
$taskSizes=@($taskMap.files | ForEach-Object {[long]$_.bytes})
$taskFailures=@([ReorgPhase3Preserve]::Verify($taskRoot,$taskPaths,$taskHashes,$taskSizes))
$taskHandoff=Get-Content (Join-Path $taskRoot 'docs/reorganization/phase1_handoff.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach($taskRow in $taskHandoff.files) {
    if([ReorgPhase3Preserve]::Hash((Join-Path $taskRoot $taskRow.path)) -ne $taskRow.sha256) {$taskFailures+=@($taskRow.path)}
}
$taskDoc=[ordered]@{status=$(if($taskFailures.Count){'FAIL'}else{'PASS'});original_file_rows=$taskMap.files.Count;sha256_verified=$true;phase1_handoff_files=$taskHandoff.files.Count;failures=$taskFailures;scientific_TEST_forward=0;training_steps=0;mapping='canonical_map.json baseline_path resolves immutable original, not active revision'}
[IO.File]::WriteAllText((Join-Path $taskRoot 'docs/reorganization/phase3/original_byte_preservation.json'),($taskDoc | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
if($taskFailures.Count){throw "Original-byte preservation mismatch: $($taskFailures.Count)"}
Write-Output "Original-byte preservation PASS: $($taskMap.files.Count) rows +19Phase1handoff files"
