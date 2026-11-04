$ErrorActionPreference = 'Stop'
$python = 'C:\Users\anhca\anaconda3\envs\rnn312\python.exe'
& $python -m unittest discover -s term_paper/tests -p 'test_ch4_*.py' -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m term_paper.tools.verify_phase5
exit $LASTEXITCODE
