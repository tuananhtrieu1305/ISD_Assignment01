$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$manifestRoot = Join-Path $workspace 'artifacts\manifests\phase20'
$events = [System.Collections.Generic.List[object]]::new()
foreach ($event in Import-Csv -LiteralPath (Join-Path $manifestRoot 'operations.csv')) { $events.Add($event) }

function Remove-FinalTarget {
    param([string]$Relative, [string]$Recovery)
    $target = [IO.Path]::GetFullPath((Join-Path $workspace $Relative))
    if (-not $target.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $target.StartsWith((Join-Path $workspace '.git') + '\', [StringComparison]::OrdinalIgnoreCase) -or
        $target.StartsWith((Join-Path $workspace 'data\raw') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Unsafe final cleanup target: $target"
    }
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
        $events.Add([pscustomobject]@{action='REMOVE'; source=$Relative; destination=''; recovery=$Recovery})
        $events | Export-Csv -LiteralPath (Join-Path $manifestRoot 'operations.csv') -NoTypeInformation -Encoding UTF8
    }
}

# These root API pipeline copies are unused by apps.api.app.
Remove-FinalTarget 'apps/api/models/diabetes_pipeline.joblib' 'Original Git HEAD: backend/models/diabetes_pipeline.joblib'
Remove-FinalTarget 'apps/api/models/house_pipeline.joblib' 'Original Git HEAD: backend/models/house_pipeline.joblib'
Remove-FinalTarget 'src/term_paper/deployment/app/static' 'releases/v2/source_snapshot.zip: term_paper/deployment/app/static'
Remove-FinalTarget 'src/term_paper/deployment/app/server.py' 'releases/v2/source_snapshot.zip: term_paper/deployment/app/server.py'

# Only Ch5 rebuild/verification tooling remains active. Phase 0-10/17-19 tooling is frozen in ZIP.
$toolKeep = @(
    '__init__.py', 'phase11_data.py', 'phase12_preprocessing.py', 'phase13_graph.py', 'phase14_rag.py', 'phase15_kgrag.py',
    'build_phase11_sources.py', 'build_phase12_preprocessing.py', 'build_phase13_graphs.py',
    'build_phase14_baselines.py', 'build_phase15_experiments.py', 'build_phase16_runtime.py',
    'verify_phase11.py', 'verify_phase12.py', 'verify_phase13.py', 'verify_phase14.py', 'verify_phase15.py', 'verify_phase16.py'
)
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $workspace 'src\term_paper\tools') -File) {
    if ($file.Name -notin $toolKeep) {
        Remove-FinalTarget ('src/term_paper/tools/' + $file.Name) ('releases/v2/source_snapshot.zip: term_paper/tools/' + $file.Name)
    }
}

Remove-FinalTarget 'apps/api/.venv' 'Recreate environment using Phase 21 bootstrap; old requirements saved in source snapshot'
Write-Output ('Total logged cleanup operations: ' + $events.Count)
