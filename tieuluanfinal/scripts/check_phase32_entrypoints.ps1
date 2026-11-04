[CmdletBinding()]
param([string]$Distribution = 'Ubuntu')
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$records = @()
foreach ($name in @('scripts/run_api_v3.ps1','scripts/phase32_preserve.ps1','scripts/check_phase32.ps1','scripts/check_phase32_entrypoints.ps1')) {
 $path = Join-Path $repo $name
 $parseTokens = $null
 $parseErrors = $null
 [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$parseTokens, [ref]$parseErrors) | Out-Null
 if ($parseErrors.Count -ne 0) { throw "PowerShell parse failure: $name" }
 $records += @{path=$name;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$linuxRepo = (& wsl.exe --distribution $Distribution --exec wslpath -a $repo).Trim()
& wsl.exe --distribution $Distribution --exec bash -n "$linuxRepo/scripts/run_api_v3.sh"
if ($LASTEXITCODE -ne 0) { throw 'Bash parse failure' }
$destination = Join-Path $repo 'artifacts/manifests/phase32/entrypoint_verification.json'
if (Test-Path -LiteralPath $destination) { throw 'Entrypoint evidence already exists' }
$evidence = @{status='PASS';powershell=$records;bash='scripts/run_api_v3.sh';inference_executed=$false}
[IO.File]::WriteAllText($destination, ($evidence | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
Write-Output 'PowerShell and Bash entrypoints PASS'
