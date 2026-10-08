$ErrorActionPreference = 'Stop'

$python = 'C:\Users\anhca\anaconda3\envs\tf312\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw "Required Python environment not found: $python"
}

& $python -m unittest discover -s term_paper/tests -p 'test_ch3_*.py' -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m term_paper.tools.verify_phase4
exit $LASTEXITCODE
