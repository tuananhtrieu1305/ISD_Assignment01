$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$python = 'C:\Users\anhca\anaconda3\envs\tf312\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Required Phase 3 Python is missing: $python"
}
Push-Location $workspace
try {
    & $python -m unittest discover -s term_paper/tests -p 'test_ch2_*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'Chapter 2 unit/integration tests failed' }
    & $python -m term_paper.tools.verify_phase3
    if ($LASTEXITCODE -ne 0) { throw 'Phase 3 artifact verification failed' }
} finally {
    Pop-Location
}
