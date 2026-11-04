[CmdletBinding(DefaultParameterSetName='Module', PositionalBinding=$false)]
param(
    [Parameter(Mandatory=$true, ParameterSetName='Module')]
    [ValidatePattern('^[A-Za-z_][A-Za-z0-9_.]*$')][string]$Module,
    [Parameter(Mandatory=$true, ParameterSetName='File')][string]$Script,
    [string]$Distribution = 'Ubuntu',
    [string[]]$Arguments = @()
)
$ErrorActionPreference = 'Stop'
$phase35Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$phase35LinuxRepo = (& wsl.exe --distribution $Distribution --exec wslpath -a $phase35Repo).Trim()
if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve document workspace' }
if ($PSCmdlet.ParameterSetName -eq 'File') {
    $phase35ScriptPath = (Resolve-Path -LiteralPath $Script).Path
    $phase35Target = (& wsl.exe --distribution $Distribution --exec wslpath -a $phase35ScriptPath).Trim()
    $phase35Mode = 'file'
} else {
    $phase35Target = $Module
    $phase35Mode = 'module'
}
& wsl.exe --distribution $Distribution --exec bash "$phase35LinuxRepo/scripts/run_docs_v3.sh" $phase35Mode $phase35Target @Arguments
if ($LASTEXITCODE -ne 0) { throw "Document command exited with code $LASTEXITCODE" }
