[CmdletBinding()]
param([switch]$Verify)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskOut=Join-Path $taskRoot 'docs/reorganization'
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
public class ReorgLiveRecord { public string path,sha256; public long bytes; }
public static class ReorgLiveBaseline {
    static HashSet<string> skip=new HashSet<string>(new string[]{".git",".openai","node_modules","__pycache__",".pytest_cache",".ruff_cache",".ipynb_checkpoints",".expo","site-packages","venv","env",".uv-cache","dist","build","coverage","contact_sheets"});
    public static string Hash(string path) { using(var f=File.OpenRead(path)) using(var s=SHA256.Create()) return BitConverter.ToString(s.ComputeHash(f)).Replace("-","").ToLowerInvariant(); }
    public static ReorgLiveRecord[] Scan(string root,string[] folders) {
        var result=new List<ReorgLiveRecord>();
        foreach(var folder in folders) {
            string top=Path.Combine(root,folder); if(!Directory.Exists(top)) continue;
            var stack=new Stack<string>(); stack.Push(top); int count=0;
            while(stack.Count>0) {
                string current=stack.Pop();
                foreach(var d in Directory.EnumerateDirectories(current)) {
                    string n=Path.GetFileName(d);
                    if(skip.Contains(n) || n.StartsWith(".venv") || n.StartsWith("docx_render") || (File.GetAttributes(d)&FileAttributes.ReparsePoint)!=0) continue;
                    stack.Push(d);
                }
                foreach(var f in Directory.EnumerateFiles(current)) {
                    string n=Path.GetFileName(f);
                    if(n==".env" || n.StartsWith(".env.")&&n!=".env.example" || n.EndsWith(".pyc") || n.EndsWith(".pyo") || n.EndsWith(".log") || n.EndsWith(".tsbuildinfo")) continue;
                    result.Add(new ReorgLiveRecord{path=f.Substring(root.Length+1).Replace('\\','/'),bytes=new FileInfo(f).Length,sha256=Hash(f)}); count++;
                }
            }
            Console.WriteLine("Baseline "+folder+": "+count+" files");
        }
        return result.ToArray();
    }
}
'@
$taskManifestPath=Join-Path $taskOut 'live_baseline_manifest.json'
if($Verify) {
    $taskDoc=Get-Content $taskManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskFailed=[Collections.Generic.List[object]]::new()
    foreach($taskRow in $taskDoc.files) {
        $taskPath=Join-Path $taskRoot $taskRow.path
        if(!(Test-Path -LiteralPath $taskPath) -or [ReorgLiveBaseline]::Hash($taskPath) -ne $taskRow.sha256) {$taskFailed.Add($taskRow.path)}
    }
    $taskReceipt=[ordered]@{status=$(if($taskFailed.Count -eq 0){'PASS'}else{'FAIL'});file_count=$taskDoc.files.Count;manifest_sha256=[ReorgLiveBaseline]::Hash($taskManifestPath);mismatches=$taskFailed.ToArray();mode='read-only SHA256, no source/model imports'}
    [IO.File]::WriteAllText((Join-Path $taskOut 'live_preservation_receipt.json'),($taskReceipt | ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
    if($taskFailed.Count) {throw 'Live source preservation failed'}
    Write-Output "Live preservation PASS: $($taskDoc.files.Count) unchanged files."
    exit
}
if(Test-Path -LiteralPath $taskManifestPath) {throw 'Baseline already exists; use -Verify, do not overwrite'}
$taskRows=[Collections.Generic.List[object]]::new()
$taskFolders=@('apps','src','experiments','data','artifacts','report','releases','requirements','deploy','term_paper','tests','discovering_ai_agent','agent02_assignment')
foreach($taskRow in [ReorgLiveBaseline]::Scan($taskRoot,$taskFolders)) {$taskRows.Add($taskRow)}
foreach($taskName in @('pyproject.toml','uv.lock','.python-version','render.yaml')) {
    $taskPath=Join-Path $taskRoot $taskName
    $taskRows.Add([pscustomobject]@{path=$taskName;bytes=(Get-Item -LiteralPath $taskPath).Length;sha256=[ReorgLiveBaseline]::Hash($taskPath)})
}
foreach($taskFile in Get-ChildItem (Join-Path $taskRoot 'scripts') -File) {
    if(!$taskFile.Name.StartsWith('reorganization_')) {$taskRows.Add([pscustomobject]@{path='scripts/'+$taskFile.Name;bytes=$taskFile.Length;sha256=[ReorgLiveBaseline]::Hash($taskFile.FullName)})}
}
$taskManifest=[ordered]@{files=$taskRows.ToArray();count=$taskRows.Count;bytes=($taskRows | Measure-Object bytes -Sum).Sum;exclusions='environment/cache/build/dist/private env/nested metadata; agent web dist is backed up separately';scientific_execution=$false;writer='Windows .NET SHA256 streams'}
[IO.File]::WriteAllText($taskManifestPath,($taskManifest | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
Write-Output "Live baseline saved: $($taskRows.Count) files."
