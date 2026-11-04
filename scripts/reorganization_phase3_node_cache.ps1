$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskSource=Join-Path $taskRoot 'apps/web/node_modules'
$taskTarget=Join-Path $taskRoot 'node_modules'
foreach($taskPath in @($taskSource,$taskTarget)){if(-not [IO.Path]::GetFullPath($taskPath).StartsWith($taskRoot+[IO.Path]::DirectorySeparatorChar)){throw 'Cache path outside workspace'}}
Add-Type -TypeDefinition @'
using System;
using System.IO;
public static class ReorgNodeCache {
  public static int Copy(string source,string target) {
    int count=0;
    foreach(string file in Directory.GetFiles(source,"*",SearchOption.AllDirectories)) {
      string destination=Path.Combine(target,file.Substring(source.Length+1));
      Directory.CreateDirectory(Path.GetDirectoryName(destination));
      if(File.Exists(destination)) {
        if(new FileInfo(file).Length!=new FileInfo(destination).Length) throw new InvalidDataException("Conflicting cache file");
        continue;
      }
      File.Copy(file,destination,false);count++;
    }
    return count;
  }
}
'@
$taskCount=[ReorgNodeCache]::Copy($taskSource,$taskTarget)
Write-Output "Shared Node cache copied from existing cache: $taskCount files. No install or source deletion."
