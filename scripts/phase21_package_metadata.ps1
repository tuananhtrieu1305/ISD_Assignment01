$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$output = Join-Path $workspace 'artifacts\manifests\phase21'
New-Item -ItemType Directory -Force -Path $output | Out-Null
$records = @()
foreach ($name in @('torch','tensorflow','keras','numpy','pandas','scikit-learn','uv')) {
    $url = 'https://pypi.org/pypi/' + $name + '/json'
    $metadata = Invoke-RestMethod -Uri $url
    $linuxWheels = @($metadata.urls | Where-Object { $_.filename -match 'cp311.*(manylinux|linux_x86_64)' })
    $records += [pscustomobject]@{
        package=$name
        version=$metadata.info.version
        requires_python=$metadata.info.requires_python
        requires_dist=$metadata.info.requires_dist
        source=$url
        python311_linux_wheels=@($linuxWheels | ForEach-Object {
            [pscustomobject]@{filename=$_.filename; bytes=$_.size; sha256=$_.digests.sha256; url=$_.url}
        })
    }
    Write-Output ($name + '==' + $metadata.info.version + ' Python: ' + $metadata.info.requires_python)
}
$records | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $output 'package-metadata.json') -Encoding UTF8
