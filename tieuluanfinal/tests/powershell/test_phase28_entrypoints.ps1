param([ValidateSet('red','green')][string]$Evidence = 'green')
$ErrorActionPreference = 'Stop'
$taskRepo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$taskRows = @()
$taskFailures = 0
foreach ($taskName in @('finish_phase28.ps1','check_phase28.ps1')) {
    $taskError = $null
    try {
        $taskPath = Join-Path $taskRepo ('scripts/' + $taskName)
        $taskTokens = $null
        $taskParseErrors = $null
        $taskAst = [Management.Automation.Language.Parser]::ParseFile($taskPath, [ref]$taskTokens, [ref]$taskParseErrors)
        if ($taskParseErrors.Count) { throw 'PowerShell syntax error' }
        $taskAssignment = $taskAst.Find({ param($taskNode)
            $taskNode -is [Management.Automation.Language.AssignmentStatementAst] -and
            $taskNode.Left -is [Management.Automation.Language.VariableExpressionAst] -and
            $taskNode.Left.VariablePath.UserPath -eq 'taskRoot'
        }, $true)
        if ($null -eq $taskAssignment) { throw 'Missing explicit taskRoot assignment' }
        $taskScripts = (Join-Path $taskRepo 'scripts').Replace("'", "''")
        $taskExpression = $taskAssignment.Right.Extent.Text.Replace('$PSScriptRoot', ("'" + $taskScripts + "'"))
        # Execute only the extracted root expression: never invoke the pipeline or a model.
        $taskResult = & ([ScriptBlock]::Create($taskExpression))
        if ($taskResult -isnot [string] -or [IO.Path]::GetFullPath($taskResult) -ne $taskRepo) {
            throw 'Entrypoint did not resolve the exact repository root as a string'
        }
        Write-Output ($taskName + ': PASS')
    }
    catch {
        $taskFailures += 1
        $taskError = [Security.SecurityElement]::Escape($_.Exception.Message)
        Write-Output ($taskName + ': FAIL: ' + $_.Exception.Message)
    }
    $taskRows += '<testcase classname="powershell.phase28" name="' + $taskName + '">' + $(if ($null -ne $taskError) {'<failure message="' + $taskError + '"/>'}) + '</testcase>'
}
$taskXml = '<testsuites><testsuite name="phase28_entrypoints" tests="2" failures="' + $taskFailures + '" errors="0" skipped="0">' + ($taskRows -join '') + '</testsuite></testsuites>'
$taskOutput = Join-Path $taskRepo ('artifacts/manifests/phase28/powershell-entrypoint-' + $Evidence + '-tests.xml')
[IO.File]::WriteAllText($taskOutput, $taskXml, [Text.UTF8Encoding]::new($false))
if ($taskFailures) { throw ('Entrypoint regression tests failed: ' + $taskFailures) }
