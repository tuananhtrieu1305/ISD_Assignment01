[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskOut = Join-Path $taskRoot 'docs/reorganization'
$taskSelection = Get-Content (Join-Path $taskOut 'selection.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskFree = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($taskRoot)).AvailableFreeSpace
if ($taskFree -lt ($taskSelection.selected_bytes + 5GB)) { throw 'Not enough disk headroom for staging' }
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -ReferencedAssemblies System.IO.Compression,System.IO.Compression.FileSystem -TypeDefinition @'
using System;
using System.IO;
using System.IO.Compression;
using System.Text;
using System.Security.Cryptography;
using System.Collections.Generic;
public class ReorgRestoreRecord {
    public string project, commit, path, oid, sha256, staging_path;
    public long bytes;
}
public static class ReorgNativeRestore {
    static string Hex(byte[] b) { return BitConverter.ToString(b).Replace("-", "").ToLowerInvariant(); }
    static string[] Hash(Stream input, long size, Stream output) {
        using(var s1 = SHA1.Create()) using(var s2 = SHA256.Create()) {
            byte[] h = Encoding.ASCII.GetBytes("blob " + size + "\0");
            s1.TransformBlock(h,0,h.Length,null,0);
            byte[] buffer = new byte[1024*1024]; int n; long count = 0;
            while((n=input.Read(buffer,0,buffer.Length)) > 0) {
                s1.TransformBlock(buffer,0,n,null,0); s2.TransformBlock(buffer,0,n,null,0);
                if(output != null) output.Write(buffer,0,n); count+=n;
            }
            if(count != size) throw new InvalidDataException("Length mismatch");
            s1.TransformFinalBlock(new byte[0],0,0); s2.TransformFinalBlock(new byte[0],0,0);
            return new string[]{ Hex(s1.Hash), Hex(s2.Hash) };
        }
    }
    public static ReorgRestoreRecord[] Restore(string zipPath, string staging, string repo, string project, string commit, string[] definitions) {
        var wanted = new Dictionary<string,string[]>();
        foreach(var line in definitions) { var p=line.Split('\t'); wanted.Add(p[2],p); }
        var records = new List<ReorgRestoreRecord>();
        using(var z=ZipFile.OpenRead(zipPath)) {
            foreach(var entry in z.Entries) {
                string[] spec; if(!wanted.TryGetValue(entry.FullName,out spec)) continue;
                if(entry.FullName.StartsWith("/") || entry.FullName.Contains("../") || entry.FullName.Contains("\\")) throw new InvalidDataException("Unsafe archive entry");
                string destination=Path.GetFullPath(Path.Combine(staging,project,entry.FullName.Replace('/',Path.DirectorySeparatorChar)));
                if(!destination.StartsWith(Path.GetFullPath(staging)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Path escapes staging");
                long size=long.Parse(spec[1]); if(entry.Length != size) throw new InvalidDataException("ZIP length mismatch: "+entry.FullName+" expected="+size+" got="+entry.Length);
                Directory.CreateDirectory(Path.GetDirectoryName(destination)); string[] hashes;
                if(File.Exists(destination)) { using(var f=File.OpenRead(destination)) hashes=Hash(f,size,null); }
                else {
                    string temporary=destination+".restoring";
                    using(var input=entry.Open()) using(var output=new FileStream(temporary,FileMode.Create,FileAccess.Write,FileShare.None)) hashes=Hash(input,size,output);
                    if(hashes[0] != spec[0]) throw new InvalidDataException("Git blob mismatch: "+entry.FullName);
                    File.Move(temporary,destination);
                }
                if(hashes[0] != spec[0]) throw new InvalidDataException("Existing staging conflict: "+entry.FullName);
                using(var f=File.OpenRead(destination)) {
                    byte[] first=new byte[50]; int n=f.Read(first,0,first.Length);
                    if(Encoding.ASCII.GetString(first,0,n).StartsWith("version https://git-lfs.github.com/spec/v1")) throw new InvalidDataException("LFS pointer, not payload");
                }
                records.Add(new ReorgRestoreRecord {project=project,commit=commit,path=entry.FullName,oid=spec[0],bytes=size,sha256=hashes[1],staging_path=destination.Substring(repo.Length+1).Replace('\\','/')});
                wanted.Remove(entry.FullName);
            }
        }
        if(wanted.Count != 0) throw new InvalidDataException("Selected files absent from archive: "+wanted.Count);
        return records.ToArray();
    }
}
'@
$taskScopes = @{
    A01=@('Assignment01_Final_5_Models.ipynb','diabetes.csv','vietnam_housing_dataset.csv','artifacts','backend','web','neo4j_scripts','.python-version')
    A02=@('A02_CT_anhtt.053.ipynb','datasets','artifacts','backend','web','neo4j_scripts','.python-version')
    A03=@('pipeline','datasets','A03_CT_anhtt.053.docx','build_a03_report.py','backend','web','artifacts','README.md','neo4j_scripts','PIPELINE_UPGRADE_PLAN.md')
    A04=@('pipeline04','pipeline','datasets','backend','web','artifacts','README.md','neo4j_scripts','PIPELINE_UPGRADE_PLAN.md')
    A05=@('A05')
    A06=@('A06')
    tieuluan1=@('term_paper','backend','web','render.yaml','RENDER_DEPLOY.md','TIEU_LUAN_AI_EXECUTION_PLAN.md','README.md')
}
$taskArchiveDir = Join-Path $taskOut 'staging/.archives'
[IO.Directory]::CreateDirectory($taskArchiveDir) | Out-Null
$taskRecords = [Collections.Generic.List[object]]::new()
$taskGroups = $taskSelection.files | Group-Object { $_.project + '|' + $_.commit }
foreach($taskGroup in $taskGroups) {
    $taskProject = $taskGroup.Group[0].project
    $taskCommit = $taskGroup.Group[0].commit
    $taskArchive = Join-Path $taskArchiveDir ($taskProject + '-' + $taskCommit.Substring(0,9) + '-lf.zip')
    $taskPaths = $taskScopes[$taskProject]
    if ($taskProject -eq 'A01' -and $taskGroup.Group[0].path -ne 'Assignment01_Final_5_Models.ipynb' -and $taskCommit.StartsWith('0c27')) {
        $taskPaths=@('A01_CT_anhtt.053.ipynb','A01_CT_anhtt.053.html','A01_CT_anhtt.053.pdf')
    }
    if (!(Test-Path -LiteralPath $taskArchive)) {
        $taskArgs = @('-c','core.autocrlf=false','-c','core.eol=lf','-C',$taskRoot,'archive','--format=zip',('--output='+$taskArchive),$taskCommit,'--') + $taskPaths
        & git @taskArgs
        if ($LASTEXITCODE -ne 0) { throw "Git archive failed: $taskProject" }
    }
    $taskDefinitions = @($taskGroup.Group | ForEach-Object { $_.oid + "`t" + $_.bytes + "`t" + $_.path })
    $taskResult = [ReorgNativeRestore]::Restore($taskArchive,(Join-Path $taskOut 'staging'),$taskRoot,$taskProject,$taskCommit,$taskDefinitions)
    foreach($taskRecord in $taskResult) { $taskRecords.Add($taskRecord) }
    Write-Output ("{0}/{1}: {2} file(s) restored and Git-blob/SHA256 verified" -f $taskProject,$taskCommit.Substring(0,9),$taskResult.Count)
}
$taskTotal=($taskRecords | Measure-Object -Property bytes -Sum).Sum
$taskManifest = [ordered]@{files=$taskRecords.ToArray();count=$taskRecords.Count;bytes=$taskTotal;git_blob_identity='PASS every file';sha256='computed every file';lfs_pointers=0;historical_code_executed=$false;writer='native Windows .NET ZIP streams; Git read-only archive'}
[IO.File]::WriteAllText((Join-Path $taskOut 'restoration_manifest.json'),($taskManifest | ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
Write-Output "Restoration complete: $($taskRecords.Count) files / $taskTotal bytes."
