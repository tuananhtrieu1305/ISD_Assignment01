[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02')][string]$Project,
    [ValidateSet('auto','torch','scratch','keras')][string]$Framework='auto',
    [switch]$Inspect,
    [switch]$ListDatasets,
    [switch]$Cpu,
    [string]$Notebook,
    [string]$Module,
    [string[]]$ModuleArguments=@()
)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskRootForWsl=$taskRoot.Replace('\','/')
$taskResolvedRoot=& wsl.exe -d Ubuntu --exec wslpath -a $taskRootForWsl
if($LASTEXITCODE -ne 0 -or -not $taskResolvedRoot) {throw 'Cannot resolve workspace in Ubuntu'}
$taskLinuxRoot=($taskResolvedRoot -join '').Trim()
$taskArguments=@('--project',$Project)
if($Inspect){$taskArguments+='--inspect'}
if($ListDatasets){$taskArguments+='--list-datasets'}
if($Cpu){$taskArguments+='--cpu'}
if($Notebook){$taskArguments+=@('--notebook',$Notebook)}
if($Module){$taskArguments+=@('--module',$Module)}
$taskArguments+=$ModuleArguments
& wsl.exe -d Ubuntu --exec bash "$taskLinuxRoot/scripts/run_assignment.sh" $Framework @taskArguments
if($LASTEXITCODE -ne 0) {throw "Assignment runner exited $LASTEXITCODE"}
