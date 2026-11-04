[CmdletBinding()]
param([string]$OutputName = 'preservation_before.json')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$locks = @(
 'artifacts/manifests/phase22/spec_lock.json',
 'artifacts/manifests/phase24/data_lock.json',
 'artifacts/manifests/phase25/core_lock.json',
 'artifacts/manifests/phase26/revisions/r2/experiment_lock.json',
 'artifacts/manifests/phase27/experiment_lock.json',
 'artifacts/manifests/phase28/experiment_lock.json',
 'artifacts/manifests/phase29/experiment_lock.json',
 'artifacts/manifests/phase30/experiment_lock.json',
 'artifacts/manifests/phase31/experiment_lock.json'
)
$members = @{}
$lockRefs = @()
foreach ($relative in $locks) {
 $path = Join-Path $repo $relative
 $document = Get-Content -Raw -Encoding UTF8 -LiteralPath $path | ConvertFrom-Json
 $lockRefs += @{path=$relative; sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
 foreach ($record in $document.files) {
  if ($members.ContainsKey($record.path) -and $members[$record.path] -ne $record.sha256) { throw 'Conflicting protected hash' }
  $members[$record.path] = $record.sha256
 }
}
$done = 0
foreach ($relative in $members.Keys) {
 $target = [IO.Path]::GetFullPath((Join-Path $repo $relative))
 if (-not $target.StartsWith($repo + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Protected path escapes workspace' }
 if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $members[$relative]) { throw "Protected hash mismatch: $relative" }
 $done++
 if ($done % 5000 -eq 0) { Write-Output "Verified $done / $($members.Count) protected files" }
}
$destination = Join-Path $repo ('artifacts/manifests/phase32/' + $OutputName)
if ([IO.Path]::GetFileName($OutputName) -ne $OutputName) { throw 'Output must be a filename' }
if (Test-Path -LiteralPath $destination) { throw 'Evidence exists; choose a new evidence name' }
[IO.Directory]::CreateDirectory((Split-Path -Parent $destination)) | Out-Null
$evidence = @{status='PASS'; unique_protected_files=$done; locks=$lockRefs; created_at=[DateTime]::UtcNow.ToString('o'); historical_test_executed=$false}
[IO.File]::WriteAllText($destination, ($evidence | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
Write-Output "PASS: $done protected files; $destination"
