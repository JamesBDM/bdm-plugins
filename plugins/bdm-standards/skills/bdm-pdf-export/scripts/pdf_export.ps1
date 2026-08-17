param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$DocxPath,

    [Parameter(Position = 1)]
    [string]$PdfPath
)

$ErrorActionPreference = 'Stop'
$resolvedDocx = (Resolve-Path -LiteralPath $DocxPath).Path

if ([string]::IsNullOrWhiteSpace($PdfPath)) {
    $PdfPath = [System.IO.Path]::ChangeExtension($resolvedDocx, '.pdf')
} elseif (-not [System.IO.Path]::IsPathRooted($PdfPath)) {
    $PdfPath = Join-Path (Get-Location) $PdfPath
}

$resolvedPdf = [System.IO.Path]::GetFullPath($PdfPath)
$pdfDirectory = Split-Path -Parent $resolvedPdf
if (-not (Test-Path -LiteralPath $pdfDirectory)) {
    New-Item -ItemType Directory -Path $pdfDirectory -Force | Out-Null
}

$exported = $false
$lastError = $null
for ($attempt = 1; $attempt -le 3 -and -not $exported; $attempt++) {
    $word = $null
    $document = $null
    $wordIdsBefore = @(Get-Process WINWORD -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
    try {
        $word = New-Object -ComObject Word.Application
        $word.Visible = $false
        $word.DisplayAlerts = 0
        $word.Options.PrintBackground = $false
        $document = $word.Documents.Open($resolvedDocx, $false, $true)
        $document.ExportAsFixedFormat($resolvedPdf, 17)
        $document.Close(0)
        $document = $null
        $exported = $true
    } catch {
        $lastError = $_
    } finally {
        if ($null -ne $document) {
            try { $document.Close(0) } catch {}
        }
        if ($null -ne $word) {
            try { $word.Quit() } catch {}
        }
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
    }

    if (-not $exported) {
        # Remove only invisible Word processes created by this failed attempt.
        Get-Process WINWORD -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Id -notin $wordIdsBefore -and
                [string]::IsNullOrEmpty($_.MainWindowTitle)
            } |
            Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds (500 * $attempt)
    }
}

if (-not $exported) {
    throw "Word PDF export failed after 3 attempts: $($lastError.Exception.Message)"
}

if (-not (Test-Path -LiteralPath $resolvedPdf)) {
    throw "Word did not create the PDF: $resolvedPdf"
}

$pdfInfo = Get-Item -LiteralPath $resolvedPdf
if ($pdfInfo.Length -eq 0) {
    throw "Word created an empty PDF: $resolvedPdf"
}

Write-Output "Saved: $resolvedPdf"
