# ocr_batch.ps1 - OCRs scanned PDFs with the built-in Windows OCR engine (Windows.Media.Ocr). No downloads.
# Input: JSON array of {src, txt}. Each source PDF is rendered page by page in memory and recognised;
# the text is written to <txt> (UTF-8) with a form feed (\f) between pages. Sources are only read.
# NB: variable names are case-insensitive in PowerShell; nothing here reuses the -JobFile parameter name.
param([string]$JobFile)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$asTaskOp = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
$asTaskAct = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function Await($op, [type]$t) { $task = $asTaskOp.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(); $task.Result }
function AwaitAct($act) { $task = $asTaskAct.Invoke($null, @($act)); $task.Wait() }

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $engine) { throw 'No Windows OCR engine for the user profile language' }
$jobList = Get-Content -LiteralPath $JobFile -Raw -Encoding UTF8 | ConvertFrom-Json
$n = 0
foreach ($j in $jobList) {
  $n++
  try {
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($j.src)) ([Windows.Storage.StorageFile])
    $pdf = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
    $pages = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $pdf.PageCount; $i++) {
      $page = $pdf.GetPage($i)
      # render so the long side is about 2800 px: enough for 8 to 10 pt scanned text, under the engine's limit
      $scale = 2800 / [math]::Max($page.Size.Width, $page.Size.Height)
      $opts = New-Object Windows.Data.Pdf.PdfPageRenderOptions
      $opts.DestinationWidth = [uint32]([math]::Round($page.Size.Width * $scale))
      $opts.DestinationHeight = [uint32]([math]::Round($page.Size.Height * $scale))
      $mem = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
      AwaitAct ($page.RenderToStreamAsync($mem, $opts))
      $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($mem)) ([Windows.Graphics.Imaging.BitmapDecoder])
      # Scans are often fed sideways or upside down. Read upright first; if that yields few real words,
      # try the other three rotations and keep the reading with the most real words.
      $best = $null; $bestScore = -1
      foreach ($rot in 'None', 'Clockwise90Degrees', 'Clockwise270Degrees', 'Clockwise180Degrees') {
        $tf = New-Object Windows.Graphics.Imaging.BitmapTransform
        $tf.Rotation = [Windows.Graphics.Imaging.BitmapRotation]::$rot
        $bmp = Await ($dec.GetSoftwareBitmapAsync([Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8, [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied, $tf, [Windows.Graphics.Imaging.ExifOrientationMode]::IgnoreExifOrientation, [Windows.Graphics.Imaging.ColorManagementMode]::DoNotColorManage)) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $res = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
        $bmp.Dispose()
        $text = ($res.Lines | ForEach-Object { $_.Text }) -join "`n"
        $score = @([regex]::Matches($text, '\b[A-Za-z]{3,}\b')).Count
        if ($score -gt $bestScore) { $best = $text; $bestScore = $score }
        if ($rot -eq 'None' -and $score -ge 25) { break }   # upright reading is clearly fine
      }
      $pages.Add($best)
      $mem.Dispose(); $page.Dispose()
    }
    [System.IO.File]::WriteAllText($j.txt, ($pages -join "`f"), (New-Object System.Text.UTF8Encoding $false))
    Write-Host "ok $n/$($jobList.Count) $($pdf.PageCount)pp $($j.src)"
  } catch { Write-Host "fail $n/$($jobList.Count) $($j.src) :: $($_.Exception.Message)" }
}
