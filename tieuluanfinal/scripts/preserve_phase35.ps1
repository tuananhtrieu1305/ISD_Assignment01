[CmdletBinding()]
param([string]$Receipt='artifacts/manifests/phase35/preserve_after.json')
$ErrorActionPreference='Stop'
$p35Repo=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$p35Destination=[IO.Path]::GetFullPath((Join-Path $p35Repo $Receipt))
if (-not $p35Destination.StartsWith($p35Repo+'\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path -LiteralPath $p35Destination)) { throw 'Output guard' }
$p35Frozen=Get-Content -Raw -Encoding UTF8 (Join-Path $p35Repo 'artifacts/manifests/phase34/preserve_after.json') | ConvertFrom-Json
$p35Locks=@($p35Frozen.locks)+@([pscustomobject]@{path='artifacts/manifests/phase34/experiment_lock.json';sha256='e4ba90714b4cd42a46eca8702f3c6b3dc2e0ddf1a11141e1df3944c56af8ebbc'})
$p35Files=@{}
foreach($p35Lock in $p35Locks) {
    $p35LockPath=Join-Path $p35Repo $p35Lock.path
    if((Get-FileHash -LiteralPath $p35LockPath).Hash.ToLowerInvariant() -ne $p35Lock.sha256) { throw ('Lock changed: '+$p35Lock.path) }
    $p35Content=Get-Content -Raw -Encoding UTF8 $p35LockPath | ConvertFrom-Json
    foreach($p35Row in $p35Content.files) {
        $p35Path=[IO.Path]::GetFullPath((Join-Path $p35Repo $p35Row.path))
        if(-not $p35Path.StartsWith($p35Repo+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Frozen member escapes workspace' }
        if($p35Files.ContainsKey($p35Path) -and $p35Files[$p35Path] -ne $p35Row.sha256) { throw 'Conflicting frozen hash' }
        $p35Files[$p35Path]=$p35Row.sha256
    }
}
if($p35Files.Count -ne 31848 -or $p35Locks.Count -ne 12) { throw 'Unexpected preservation scope' }
$p35Counter=0
$p35Sha=[Security.Cryptography.SHA256]::Create()
try {
    foreach($p35Pair in $p35Files.GetEnumerator()) {
        if(([IO.File]::GetAttributes($p35Pair.Key) -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Reparse member' }
        $p35Stream=[IO.File]::OpenRead($p35Pair.Key)
        try { $p35Actual=[BitConverter]::ToString($p35Sha.ComputeHash($p35Stream)).Replace('-','').ToLowerInvariant() }
        finally { $p35Stream.Dispose() }
        if($p35Actual -ne $p35Pair.Value) { throw ('Frozen file changed: '+$p35Pair.Key) }
        $p35Counter++
        if($p35Counter % 5000 -eq 0) { Write-Output ('Verified '+$p35Counter+' protected files') }
    }
} finally { $p35Sha.Dispose() }
$p35Result=[ordered]@{status='PASS';unique_protected_files=$p35Counter;parent_locks=12;locks=$p35Locks;mode='read_only_no_inference';models_retrained=0;historical_test_evaluation_executed=$false}
$p35Json=$p35Result | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($p35Destination,$p35Json+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$p35Json
