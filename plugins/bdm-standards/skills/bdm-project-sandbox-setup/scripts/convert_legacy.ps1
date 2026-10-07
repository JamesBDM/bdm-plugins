# convert_legacy.ps1 - converts legacy .doc -> .docx and .xls -> .xlsx through Word / Excel COM.
# Input: a JSON array of {src, dst}. Sources are opened read-only; outputs go to the cache outside the library.
param([string]$Jobs)
# NB: PowerShell variable names ignore case. Never reuse $jobs here: it is the [string] -Jobs parameter
# and anything assigned to it is coerced to a string. In 5.1, ConvertFrom-Json emits an array as one
# object, so assign to a variable first and let the pipeline unroll it.
$ErrorActionPreference = 'Continue'
$jobList = Get-Content -LiteralPath $Jobs -Raw -Encoding UTF8 | ConvertFrom-Json
# Office COM throws RPC_E_CALL_REJECTED when it is busy: retry a few times before giving up.
function Invoke-Retry([scriptblock]$Do) {
  for ($i = 1; $i -le 6; $i++) {
    try { & $Do; return $true } catch {
      if ($_.Exception.Message -match '0x80010001|RPC_E_CALL_REJECTED|null-valued' -and $i -lt 6) { Start-Sleep -Milliseconds (800 * $i) } else { throw }
    }
  }
}
$docJobs = @($jobList | Where-Object { $_.src -match '\.doc$' })
$xlsJobs = @($jobList | Where-Object { $_.src -match '\.xls$' })
if ($docJobs.Count) {
  $w = New-Object -ComObject Word.Application; $w.Visible = $false; $w.DisplayAlerts = 0
  foreach ($j in $docJobs) {
    try { Invoke-Retry { $d = $w.Documents.Open($j.src, $false, $true, $false); $d.SaveAs2($j.dst, 16); $d.Close($false) } | Out-Null } catch { Write-Host "doc failed: $($j.src) $_" }
  }
  $w.Quit()
}
if ($xlsJobs.Count) {
  $x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false; $x.AutomationSecurity = 3
  foreach ($j in $xlsJobs) {
    try { Invoke-Retry { $b = $x.Workbooks.Open($j.src, 0, $true); $b.SaveAs($j.dst, 51); $b.Close($false) } | Out-Null } catch { Write-Host "xls failed: $($j.src) $_" }
  }
  $x.Quit()
}
"legacy done: $($docJobs.Count) doc, $($xlsJobs.Count) xls"
