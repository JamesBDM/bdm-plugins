<#
.SYNOPSIS
  Read one or more saved Outlook .msg files as plain text (read-only).

.DESCRIPTION
  Uses Outlook desktop (COM OpenSharedItem) when it is installed: gives From, To, Cc,
  Sent, Subject, attachment names and the body. If Outlook is not available, falls back
  to pulling readable text runs out of the file - rough, but enough to get the gist.
  Never sends, moves, saves or deletes anything. Outlook is left running if it was
  already open.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File read_msg.ps1 -Path "C:\...\file1.msg","C:\...\file2.msg" -MaxBody 3000
#>
param(
  [Parameter(Mandatory = $true)][string[]]$Path,
  [int]$MaxBody = 4000
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Trim-Body([string]$b) {
  if (-not $b) { return '' }
  # drop quoted history below the first reply header to keep the latest message only
  $cut = [regex]::Match($b, '(?m)^\s*(From:|-----Original Message-----|On .+ wrote:)')
  if ($cut.Success -and $cut.Index -gt 200) { $b = $b.Substring(0, $cut.Index) + "`n[...earlier thread trimmed...]" }
  $b = ($b -replace "(`r?`n){3,}", "`n`n").Trim()
  if ($b.Length -gt $MaxBody) { $b = $b.Substring(0, $MaxBody) + "`n[...truncated...]" }
  $b
}

function Read-Fallback([string]$p) {
  $bytes = [System.IO.File]::ReadAllBytes($p)
  $u = [System.Text.Encoding]::Unicode.GetString($bytes)
  $runs = [regex]::Matches($u, '[\u0020-\u007E\u00A0-\u024F\r\n\t]{25,}') | ForEach-Object { $_.Value.Trim() } |
    Where-Object { $_ -match '[a-zA-Z]{4,}' } | Select-Object -Unique
  Trim-Body ($runs -join "`n")
}

$ol = $null
try { $ol = New-Object -ComObject Outlook.Application -ErrorAction Stop } catch { $ol = $null }

foreach ($p in $Path) {
  "=" * 78
  "FILE: $p"
  if (-not (Test-Path -LiteralPath $p)) { "  (not found)"; continue }
  $done = $false
  if ($ol) {
    try {
      $m = $ol.Session.OpenSharedItem($p)
      "From:    $($m.SenderName) <$($m.SenderEmailAddress)>"
      "To:      $($m.To)"
      if ($m.CC) { "Cc:      $($m.CC)" }
      "Sent:    $($m.SentOn)"
      "Subject: $($m.Subject)"
      if ($m.Attachments.Count -gt 0) {
        $names = @(); for ($i = 1; $i -le $m.Attachments.Count; $i++) { $names += $m.Attachments.Item($i).FileName }
        "Attach:  " + ($names -join ' | ')
      }
      ""
      Trim-Body $m.Body
      [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($m)
      $done = $true
    } catch { "  (Outlook could not open it: $($_.Exception.Message) - using text fallback)" }
  }
  if (-not $done) { "(text fallback - headers may be missing)"; ""; Read-Fallback $p }
  ""
}
if ($ol) { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($ol) }
