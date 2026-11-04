[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('tieuluan1','tieuluan2','tieuluan3')][string]$Project,[switch]$Install)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskNode=Join-Path $taskRoot '.local/node-v22.23.4-win-x64/node.exe'
if(-not (Test-Path -LiteralPath $taskNode)){$taskNode=(Get-Command node -ErrorAction Stop).Source}
$taskNodeDir=Split-Path $taskNode
$taskPreviousPath=$env:PATH
try{
    $env:PATH=$taskNodeDir+[IO.Path]::PathSeparator+$env:PATH
    Push-Location (Join-Path $taskRoot "$Project/web/frontend")
    try{
        if($Install){& npm.cmd ci --no-fund --no-audit;if($LASTEXITCODE -ne 0){throw 'npm ci failed'}}
        & npm.cmd run build
        if($LASTEXITCODE -ne 0){throw 'Frontend build failed'}
    }finally{Pop-Location}
}finally{$env:PATH=$taskPreviousPath}
