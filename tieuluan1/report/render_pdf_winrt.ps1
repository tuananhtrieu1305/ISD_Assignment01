param(
    [Parameter(Mandatory = $true)]
    [string]$PdfPath,
    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[void][Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
[void][Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
[void][Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
[void][Windows.Storage.Streams.DataReader, Windows.Storage.Streams, ContentType = WindowsRuntime]

$genericAsTask = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq "AsTask" -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 } |
    Select-Object -First 1
$actionAsTask = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq "AsTask" -and -not $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 } |
    Select-Object -First 1

function Await-Operation($Operation, [Type]$ResultType) {
    $method = $genericAsTask.MakeGenericMethod($ResultType)
    $task = $method.Invoke($null, @($Operation))
    $task.Wait()
    return $task.Result
}

function Await-Action($Action) {
    $task = $actionAsTask.Invoke($null, @($Action))
    $task.Wait()
}

$pdfFullPath = [System.IO.Path]::GetFullPath($PdfPath)
$outputFullPath = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $outputFullPath -Force | Out-Null

$storageFile = Await-Operation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfFullPath)) ([Windows.Storage.StorageFile])
$pdf = Await-Operation ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($storageFile)) ([Windows.Data.Pdf.PdfDocument])

for ($index = 0; $index -lt $pdf.PageCount; $index++) {
    $page = $pdf.GetPage($index)
    $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    try {
        Await-Action ($page.RenderToStreamAsync($stream))
        $stream.Seek(0)
        $reader = New-Object Windows.Storage.Streams.DataReader($stream.GetInputStreamAt(0))
        try {
            $length = [uint32]$stream.Size
            [void](Await-Operation ($reader.LoadAsync($length)) ([uint32]))
            $bytes = New-Object byte[] $length
            $reader.ReadBytes($bytes)
            $target = Join-Path $outputFullPath ("page-{0:D3}.png" -f ($index + 1))
            [System.IO.File]::WriteAllBytes($target, $bytes)
        }
        finally {
            $reader.Dispose()
        }
    }
    finally {
        $stream.Dispose()
        $page.Dispose()
    }
}

Write-Output "Rendered $($pdf.PageCount) PDF pages to $outputFullPath"
