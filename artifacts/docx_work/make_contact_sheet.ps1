param(
    [Parameter(Mandatory=$true)][string]$InputDir,
    [Parameter(Mandatory=$true)][string]$OutputDir
)

Add-Type -AssemblyName System.Drawing

$null = New-Item -ItemType Directory -Force -Path $OutputDir
$files = Get-ChildItem -Path $InputDir -Filter "page-*.png" | Sort-Object {
    [int]($_.BaseName -replace "[^\d]", "")
}

$cols = 3
$thumbW = 360
$thumbH = 510
$labelH = 34
$gap = 18
$margin = 24
$perSheet = 9

for ($sheet = 0; $sheet * $perSheet -lt $files.Count; $sheet++) {
    $batch = $files | Select-Object -Skip ($sheet * $perSheet) -First $perSheet
    $rows = [Math]::Ceiling($batch.Count / $cols)
    $width = $margin * 2 + $cols * $thumbW + ($cols - 1) * $gap
    $height = $margin * 2 + $rows * ($thumbH + $labelH) + ($rows - 1) * $gap
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.Clear([System.Drawing.Color]::White)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $font = New-Object System.Drawing.Font "Arial", 16, ([System.Drawing.FontStyle]::Bold)
    $brush = [System.Drawing.Brushes]::Black

    for ($i = 0; $i -lt $batch.Count; $i++) {
        $file = $batch[$i]
        $col = $i % $cols
        $row = [Math]::Floor($i / $cols)
        $x = $margin + $col * ($thumbW + $gap)
        $y = $margin + $row * ($thumbH + $labelH + $gap)
        $pageNo = [int]($file.BaseName -replace "[^\d]", "")
        $graphics.DrawString("Page $pageNo", $font, $brush, $x, $y)
        $image = [System.Drawing.Image]::FromFile($file.FullName)
        $graphics.DrawImage($image, $x, $y + $labelH, $thumbW, $thumbH)
        $image.Dispose()
    }

    $outFile = Join-Path $OutputDir ("sheet-{0}.png" -f ($sheet + 1))
    $bitmap.Save($outFile, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}
