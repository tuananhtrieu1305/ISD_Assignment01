$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$records = @()
foreach ($relative in @('scripts/bootstrap_web_v3.ps1','scripts/run_web_v3.ps1','scripts/check_phase33.ps1','scripts/check_phase33_entrypoints.ps1','scripts/seal_phase33_visual.ps1')) {
 $tokens=$null; $errors=$null
 [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo $relative),[ref]$tokens,[ref]$errors) | Out-Null
 if ($errors.Count -gt 0) { throw "PowerShell parser failed: $relative" }
 $records += @{path=$relative; sha256=(Get-FileHash -LiteralPath (Join-Path $repo $relative) -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$destination = Join-Path $repo 'artifacts/manifests/phase33/entrypoint_verification.json'
if (Test-Path -LiteralPath $destination) { throw 'Evidence exists' }
[IO.File]::WriteAllText($destination,(@{status='PASS';source=$records;parser='PowerShell AST';inference_executed=$false} | ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
Write-Output 'PASS:5 PowerShell entrypoints'
