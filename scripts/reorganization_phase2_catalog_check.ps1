[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskProjects=@('A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02')
Add-Type -TypeDefinition @'
using System;
using System.IO;
public static class ReorgCatalogSizes {
    public static void Verify(string root,string[] paths,long[] sizes) {
        string prefix=Path.GetFullPath(root)+Path.DirectorySeparatorChar;
        for(int i=0;i<paths.Length;i++) {
            string file=Path.GetFullPath(Path.Combine(root,paths[i]));
            if(!file.StartsWith(prefix,StringComparison.OrdinalIgnoreCase) || !File.Exists(file)) throw new InvalidDataException("Missing or unsafe dataset path: "+paths[i]);
            if(sizes[i]>=0 && new FileInfo(file).Length!=sizes[i]) throw new InvalidDataException("Dataset size mismatch: "+paths[i]);
        }
    }
}
'@
$taskResults=@()
foreach($taskProject in $taskProjects){
    $taskPath=Join-Path $taskRoot "$taskProject/datasets/catalog.json"
    $taskCatalog=Get-Content -LiteralPath $taskPath -Raw -Encoding UTF8|ConvertFrom-Json
    $taskFiles=@($taskCatalog.datasets|ForEach-Object {$_.files}|Where-Object {$_})
    $taskPaths=@($taskFiles|ForEach-Object {$_.path})
    $taskSizes=@($taskFiles|ForEach-Object {if($_.PSObject.Properties.Name -contains 'bytes'){[long]$_.bytes}else{[long]-1}})
    [ReorgCatalogSizes]::Verify($taskRoot,$taskPaths,$taskSizes)
    $taskResults+=@([ordered]@{project=$taskProject;catalog="$taskProject/datasets/catalog.json";sha256=(Get-FileHash -LiteralPath $taskPath -Algorithm SHA256).Hash.ToLowerInvariant();file_references=$taskFiles.Count;status='PASS'})
    Write-Output "Catalog paths/sizes PASS: $taskProject/$($taskFiles.Count)"
}
$taskDoc=[ordered]@{status='PASS';scope='Native filesystem existence and byte size; original scientific SHA256 preservation has independent full read-back receipt';projects=$taskResults}
[IO.File]::WriteAllText((Join-Path $taskRoot 'docs/reorganization/phase2/catalog_paths_sizes.json'),($taskDoc|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
