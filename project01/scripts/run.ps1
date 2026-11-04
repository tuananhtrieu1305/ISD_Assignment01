[CmdletBinding()]
param([switch]$Inspect,[switch]$Probe,[string]$Notebook)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$taskLinuxRoot=(& wsl.exe -d Ubuntu --exec wslpath -a $taskRoot.Replace('\','/')).Trim()
if($LASTEXITCODE -ne 0){throw 'Cannot resolve workspace in WSL Ubuntu'}
$taskArguments=@()
if($Inspect){$taskArguments+='--inspect'}
if($Probe){$taskArguments+='--probe'}
if($Notebook){$taskArguments+=@('--notebook',$Notebook)}
& wsl.exe -d Ubuntu --exec /home/tuananh/.local/share/ai-term-paper-v3/.venv-torch/bin/python -B "$taskLinuxRoot/project01/scripts/run.py" @taskArguments
if($LASTEXITCODE -ne 0){throw "project01 runner failed: $LASTEXITCODE"}
