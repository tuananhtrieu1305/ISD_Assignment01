$ErrorActionPreference = 'Stop'
$preferredPython = 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe'
if (Test-Path -LiteralPath $preferredPython) {
    $python = $preferredPython
} elseif (Test-Path -LiteralPath '.\backend\.venv\Scripts\python.exe') {
    $python = (Resolve-Path '.\backend\.venv\Scripts\python.exe').Path
} else {
    throw 'Không tìm thấy Python environment có dependency deployment.'
}
& $python -m unittest discover -s term_paper/deployment/tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m term_paper.tools.verify_phase6
exit $LASTEXITCODE
