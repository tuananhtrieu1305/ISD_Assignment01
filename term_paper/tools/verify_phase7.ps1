$ErrorActionPreference = 'Stop'

$WorkspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Python = 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe'

Push-Location $WorkspaceRoot
try {
    & $Python -m term_paper.tools.build_phase7_manuscript
    if ($LASTEXITCODE -ne 0) { throw 'Phase 7 manuscript build failed.' }
    & $Python -m term_paper.tools.verify_phase7
    if ($LASTEXITCODE -ne 0) { throw 'Phase 7 verification failed.' }
}
finally {
    Pop-Location
}
