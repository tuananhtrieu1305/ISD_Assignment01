[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('A01','A02','A03','A04','A05','A06','tieuluan1','tieuluan2','tieuluan3','agent01','agent02')][string]$Project,[int]$Port=0)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path.Replace('\','/')
$taskLinuxRoot=(& wsl.exe -d Ubuntu --exec wslpath -a $taskRoot).Trim()
if($LASTEXITCODE -ne 0){throw 'Cannot resolve workspace'}
$taskArguments=@('-B',"$taskLinuxRoot/scripts/web_app.py",'--project',$Project)
if($Port){$taskArguments+=@('--port',[string]$Port)}
$env:PYTHONDONTWRITEBYTECODE='1'
& wsl.exe -d Ubuntu --exec env PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python @taskArguments
if($LASTEXITCODE -ne 0){throw "Web runner exited $LASTEXITCODE"}
