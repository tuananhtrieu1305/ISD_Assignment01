[CmdletBinding()]
param([ValidateSet('relocate','views')][string]$Stage='relocate')
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskP2=Join-Path $taskRoot 'docs/reorganization/phase2'
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Collections.Generic;
public static class ReorgPhase2IO {
    [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateHardLink(string file,string existing,IntPtr reserved);
    public static string Hash(string p) { using(var f=File.OpenRead(p)) using(var s=SHA256.Create()) return BitConverter.ToString(s.ComputeHash(f)).Replace("-","").ToLowerInvariant(); }
    public static string Safe(string root,string rel) {
        if(Path.IsPathRooted(rel)) throw new InvalidDataException("Relative path required");
        string p=Path.GetFullPath(Path.Combine(root,rel));
        if(!p.StartsWith(Path.GetFullPath(root)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase) || p.Equals(Path.Combine(root,".git"),StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Outside authorized workspace");
        return p;
    }
    public static string Transfer(string root,string source,string target,string operation,string sha,long bytes) {
        string s=Safe(root,source),t=Safe(root,target);
        if(File.Exists(t)) {
            if(new FileInfo(t).Length!=bytes || Hash(t)!=sha) throw new InvalidDataException("Existing destination conflict: "+target);
            return s==t?"in_place_verified":"existing_verified";
        }
        if(!File.Exists(s) || new FileInfo(s).Length!=bytes || Hash(s)!=sha) throw new InvalidDataException("Source changed/missing: "+source);
        Directory.CreateDirectory(Path.GetDirectoryName(t));
        if(operation=="move") { File.Move(s,t); return "moved"; }
        if(operation=="link_or_copy" && CreateHardLink(t,s,IntPtr.Zero)) return "hardlinked";
        File.Copy(s,t,false); return "copied";
    }
    static void MergeMove(string source,string target) {
        Directory.CreateDirectory(target);
        foreach(string f in Directory.EnumerateFiles(source)) {
            string t=Path.Combine(target,Path.GetFileName(f));
            if(File.Exists(t)) { if(Hash(f)!=Hash(t)) throw new InvalidDataException("Merge conflict: "+t); continue; }
            try { File.Move(f,t); } catch(IOException) { File.Copy(f,t,false); } catch(UnauthorizedAccessException) { File.Copy(f,t,false); }
        }
        foreach(string d in Directory.EnumerateDirectories(source)) {
            string name=Path.GetFileName(d);
            if(name=="node_modules" || name=="dist" || name=="__pycache__" || name==".git" || name==".openai") continue;
            MergeMove(d,Path.Combine(target,name));
        }
    }
    public static string MoveDirectory(string root,string source,string target) {
        string s=Safe(root,source),t=Safe(root,target);
        if(!Directory.Exists(s)) { if(Directory.Exists(t)) return "already_present"; throw new DirectoryNotFoundException(source); }
        if(Directory.Exists(t)) {
            if(Directory.GetFileSystemEntries(t).Length!=0) { MergeMove(s,t); return "merged_source_files_generated_cache_retained"; }
            Directory.Delete(t,false);
        }
        Directory.CreateDirectory(Path.GetDirectoryName(t));
        try { Directory.Move(s,t); return "moved"; }
        catch(IOException) { MergeMove(s,t); return "file_moves_with_locked_parent_or_cache_retained"; }
        catch(UnauthorizedAccessException) { MergeMove(s,t); return "file_copies_with_locked_parent_or_cache_retained"; }
    }
    public static int BuildViews(string root,string tsv,string journal) {
        var verified=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);
        int count=0; int links=0; int copies=0;
        using(var writer=new StreamWriter(journal,true,new System.Text.UTF8Encoding(false))) {
            foreach(var line in File.ReadLines(tsv)) {
                var fields=line.Split('\t'); if(fields.Length!=4) throw new InvalidDataException("Bad view row");
                string s=Safe(root,fields[0]),t=Safe(root,fields[1]),expected=fields[2]; long size=long.Parse(fields[3]);
                string actual;
                if(!verified.TryGetValue(s,out actual)) {
                    if(!File.Exists(s) || new FileInfo(s).Length!=size) throw new InvalidDataException("Missing view source: "+fields[0]);
                    actual=Hash(s); if(actual!=expected) throw new InvalidDataException("Changed view source: "+fields[0]);
                    verified.Add(s,actual);
                }
                if(actual!=expected) throw new InvalidDataException("Conflicting view source");
                string status="existing_verified";
                if(File.Exists(t)) { if(new FileInfo(t).Length!=size || Hash(t)!=expected) throw new InvalidDataException("View target collision: "+fields[1]); }
                else {
                    Directory.CreateDirectory(Path.GetDirectoryName(t));
                    if(CreateHardLink(t,s,IntPtr.Zero)) {status="hardlinked";links++;}
                    else {File.Copy(s,t,false);status="copied";copies++;}
                }
                writer.WriteLine(fields[0]+"\t"+fields[1]+"\t"+status); count++;
                if(count%20000==0) {writer.Flush();Console.WriteLine("Runtime aliases "+count+"; hardlinks="+links+", copies="+copies);}
            }
        }
        return count;
    }
}
'@
$taskJournal=Join-Path $taskP2 ($Stage+'-journal.jsonl')
$taskWriter=[IO.StreamWriter]::new($taskJournal,$true,[Text.UTF8Encoding]::new($false))
try {
    if($Stage -eq 'relocate') {
        $taskMap=Get-Content (Join-Path $taskP2 'relocation_map_r2.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach($taskMove in $taskMap.bulk_directory_moves) {
            $taskMoveResult=[ReorgPhase2IO]::MoveDirectory($taskRoot,$taskMove.source,$taskMove.target)
            $taskWriter.WriteLine((@{kind='directory';source=$taskMove.source;target=$taskMove.target;status=$taskMoveResult} | ConvertTo-Json -Compress))
            $taskWriter.Flush()
            Write-Output "Directory relocated: $($taskMove.source) -> $($taskMove.target)"
        }
        $taskCount=0
        foreach($taskRow in $taskMap.files) {
            $taskResult=[ReorgPhase2IO]::Transfer($taskRoot,$taskRow.source_after_bulk,$taskRow.target,$taskRow.operation,$taskRow.sha256,[long]$taskRow.bytes)
            $taskWriter.WriteLine((@{source=$taskRow.source_after_bulk;target=$taskRow.target;status=$taskResult;sha256=$taskRow.sha256} | ConvertTo-Json -Compress))
            $taskCount++
            if($taskCount%10000 -eq 0) {$taskWriter.Flush();Write-Output "Relocated/verified $taskCount/$($taskMap.files.Count)"}
        }
        foreach($taskName in @('A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02')) {
            foreach($taskSub in @('datasets','notebooks','web','provenance')) {[IO.Directory]::CreateDirectory((Join-Path $taskRoot "$taskName/$taskSub")) | Out-Null}
        }
        # Move only the known nested web-project metadata, never root .git.
        foreach($taskName in @('.git','.openai')) {
            $taskFrom="agent01/web-demo/$taskName"
            if(Test-Path -LiteralPath (Join-Path $taskRoot $taskFrom)) {[ReorgPhase2IO]::MoveDirectory($taskRoot,$taskFrom,"agent01/provenance/nested_web_metadata/$taskName")}
        }
        [IO.File]::WriteAllText((Join-Path $taskP2 'relocation_native_complete.json'),(@{status='COMPLETE';files=$taskCount;phase1_sources_preserved=$true;source_models_executed=$false} | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    } else {
        $taskCount=[ReorgPhase2IO]::BuildViews($taskRoot,(Join-Path $taskP2 'runtime_views.tsv'),(Join-Path $taskP2 'views-files.tsv'))
        [IO.File]::WriteAllText((Join-Path $taskP2 'runtime_views_complete.json'),(@{status='COMPLETE';aliases=$taskCount;symlinks_required=$false;copy_fallback=$true} | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    }
} finally {$taskWriter.Dispose()}
