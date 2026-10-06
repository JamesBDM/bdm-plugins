<#
.SYNOPSIS
  Read-only inventory for bdm-project-sandbox-setup.

.DESCRIPTION
  -List            One row per project folder: sandbox present? summary present?
  -Project <name>  Inventory of one project: spine check, newest files per folder,
                   email digest (parsed from the .msg filenames), key-document candidates
                   and the suggested Project_Summary filename.

  Never writes, moves or renames anything. Output is Markdown on stdout.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scan_project.ps1 -List
  powershell -ExecutionPolicy Bypass -File scan_project.ps1 -Project "202603_106 Hargreaves Ave, Chelmer"
#>
param(
  [string]$Root = (Join-Path $env:USERPROFILE 'BDM\Projects - Documents'),
  [string]$Project,
  [switch]$List,
  [int]$NewestPerFolder = 8,
  [int]$EmailRows = 40
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

if (-not (Test-Path -LiteralPath $Root)) { throw "Projects root not found: $Root  (pass -Root)" }

$JobFolder = '^\d{6}_'          # project folders start with the BDM job number, e.g. 202603_
$Spine = @('00_Email Communication','00_ai_sandbox','01_Client','02_Project Control',
  '03_Applications & Approvals','04_Statutory Authorities','05_Consultants',
  '06_Drawings & Specifications','07_Meeting Minutes','08_Issued Reports','09_Programmes',
  '10_Cost Plans','10a_Feasibility','11_Sales & Marketing','12_Tender Documents',
  '13_Contract Admin','14_Project Completion Docs','15_Site Inspections')
$Retired = @('PROJECT.md','Project_Summary.md')

function Get-Sandbox([string]$projPath) {
  # case-insensitive: 00_ai_sandbox, 00_AI_sandbox, 00_AI_Sandbox all count
  Get-ChildItem -LiteralPath $projPath -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ieq '00_ai_sandbox' } | Select-Object -First 1
}

function Get-SummaryName([string]$folderName) {
  $n = $folderName -replace $JobFolder, ''
  $n = $n -replace '[,&()\.''`]', ' '
  $n = ($n.Trim() -replace '\s+', '_') -replace '_+', '_'
  "Project_Summary_$n.md"
}

function Fmt-Date($d) { $d.ToString('yyyy-MM-dd') }

# ---------------------------------------------------------------- list mode
if ($List -or -not $Project) {
  "# Sandbox status - $Root"
  ""
  "| Project folder | Sandbox | Summary | Retired variants | Newest file |"
  "|---|---|---|---|---|"
  Get-ChildItem -LiteralPath $Root -Directory | Where-Object { $_.Name -match $JobFolder } | Sort-Object Name | ForEach-Object {
    $sb = Get-Sandbox $_.FullName
    $sum = ''; $ret = ''
    if ($sb) {
      $s = Get-ChildItem -LiteralPath $sb.FullName -File -Filter 'Project_Summary_*.md' -ErrorAction SilentlyContinue
      if ($s) { $sum = ($s | ForEach-Object Name) -join '<br>' }
      $r = Get-ChildItem -LiteralPath $sb.FullName -File -ErrorAction SilentlyContinue |
        Where-Object { $Retired -contains $_.Name -or $_.Name -like '*_STATE.md' }
      if ($r) { $ret = ($r | ForEach-Object Name) -join ', ' }
    }
    $newest = Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $nd = if ($newest) { Fmt-Date $newest.LastWriteTime } else { '(empty)' }
    $sbTxt = if ($sb) { $sb.Name } else { '**MISSING**' }
    $sumTxt = if ($sum) { $sum } else { '**MISSING**' }
    "| $($_.Name) | $sbTxt | $sumTxt | $ret | $nd |"
  }
  ""
  "Skipped: folders not starting with a 6-digit job number (personal folders, _Projects Archived, _Project Opportunities, _ New Job Folder)."
  return
}

# ---------------------------------------------------------------- project mode
$projPath = if (Test-Path -LiteralPath $Project) { (Resolve-Path -LiteralPath $Project).Path } else { Join-Path $Root $Project }
if (-not (Test-Path -LiteralPath $projPath)) { throw "Project folder not found: $projPath" }
$proj = Get-Item -LiteralPath $projPath
$all = @(Get-ChildItem -LiteralPath $projPath -File -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -notlike '~$*' -and $_.Name -ne 'Thumbs.db' -and $_.Name -ne 'desktop.ini' })

function Rel($f) { $f.FullName.Substring($projPath.Length).TrimStart('\') }

"# Inventory - $($proj.Name)"
""
"- Path: ``$projPath``"
"- Files: $($all.Count)   |   Scanned: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
$sb = Get-Sandbox $projPath
if ($sb) {
  "- Sandbox: ``$($sb.Name)`` present"
  $sbFiles = Get-ChildItem -LiteralPath $sb.FullName -Force -ErrorAction SilentlyContinue
  if ($sbFiles) { "  - Contents: " + (($sbFiles | ForEach-Object { if ($_.PSIsContainer) { "$($_.Name)\" } else { $_.Name } }) -join ' | ') }
  else { "  - Contents: (empty)" }
} else { "- Sandbox: **MISSING** - create ``00_ai_sandbox``" }
"- Suggested summary filename: ``$(Get-SummaryName $proj.Name)``"
""

# spine check
$top = @(Get-ChildItem -LiteralPath $projPath -Directory -Force | ForEach-Object Name)
$missing = $Spine | Where-Object { $n = $_; -not ($top | Where-Object { $_ -ieq $n }) }
$extra = $top | Where-Object { $n = $_; -not ($Spine | Where-Object { $_ -ieq $n }) }
"## Spine check (BDM Project Folder Standard R1)"
""
"- Missing: " + $(if ($missing) { ($missing -join ' | ') } else { 'none' })
"- Project-specific / non-standard: " + $(if ($extra) { ($extra -join ' | ') } else { 'none' })
""

# per top-level folder
"## Folders - file count, newest date, newest files"
""
foreach ($d in ($top | Sort-Object)) {
  $files = @($all | Where-Object { $_.FullName.StartsWith((Join-Path $projPath $d) + '\', [System.StringComparison]::OrdinalIgnoreCase) })
  if ($files.Count -eq 0) { "### $d - EMPTY"; ""; continue }
  $newest = $files | Sort-Object LastWriteTime -Descending
  "### $d - $($files.Count) files, newest $(Fmt-Date $newest[0].LastWriteTime)"
  if ($d -ieq '00_Email Communication') { "(see email digest below)"; ""; continue }
  $newest | Select-Object -First $NewestPerFolder | ForEach-Object {
    "- $(Fmt-Date $_.LastWriteTime) | $([math]::Round($_.Length/1KB))KB | ``$(Rel $_)``"
  }
  ""
}

# email digest from filenames: YYYY-MM-DD_HHMMSS_Sender_Subject.msg
$mail = @($all | Where-Object { $_.Extension -ieq '.msg' })
"## Email digest - $($mail.Count) .msg files"
""
if ($mail.Count) {
  $parsed = $mail | ForEach-Object {
    if ($_.BaseName -match '^(\d{4}-\d{2}-\d{2})_(\d{6})_(.+?)_(.*)$') {
      [pscustomobject]@{ Date = $Matches[1]; Sender = $Matches[3].Trim(); Subject = $Matches[4].Trim(); Rel = (Rel $_) }
    } else {
      [pscustomobject]@{ Date = (Fmt-Date $_.LastWriteTime); Sender = '?'; Subject = $_.BaseName; Rel = (Rel $_) }
    }
  } | Sort-Object Date -Descending
  "- Range: $($parsed[-1].Date) to $($parsed[0].Date)"
  "- Top senders: " + (($parsed | Group-Object Sender | Sort-Object Count -Descending | Select-Object -First 10 | ForEach-Object { "$($_.Name) ($($_.Count))" }) -join ' | ')
  ""
  "| Date | Sender | Subject | File |"
  "|---|---|---|---|"
  $parsed | Select-Object -First $EmailRows | ForEach-Object { "| $($_.Date) | $($_.Sender) | $($_.Subject) | ``$($_.Rel)`` |" }
  ""
}

# key-document candidates
$keys = [ordered]@{
  'Engagement / client'      = 'engagement|letter of offer|brief|consultancy agreement|BDM.*(fee|proposal)'
  'Contract / insurances'    = 'contract|as ?4000|as ?2124|abic|insurance|currency|bank guarantee|security'
  'Consultant appointments'  = 'agreement|appointment|fee proposal|proposal|engagement'
  'Approvals'                = 'decision notice|approval|DA[ _-]|development permit|building approval|BA[ _-]|conditions'
  'Programme'                = 'programme|program|gantt|schedule'
  'Cost / claims'            = 'cost report|cost plan|feasib|claim|certificate|valuation|budget|estimate|QS'
  'Variations / EOTs / notices' = 'variation|VO[ _-]?\d|CSA|EOT|extension of time|notice|SI[ _-]?\d|instruction'
  'Registers'                = 'register|CAR'
  'Minutes / reports'        = 'minutes|PCG|meeting|report'
}
"## Key-document candidates (filename match - newest first, max 10 each)"
""
$docs = $all | Where-Object { $_.Extension -match '^\.(pdf|docx?|xlsx?|xlsm|msg|md|csv)$' -and $_.FullName -notmatch '\\00_Email Communication\\' }
foreach ($k in $keys.Keys) {
  $hits = @($docs | Where-Object { $_.Name -match $keys[$k] } | Sort-Object LastWriteTime -Descending | Select-Object -First 10)
  "### $k ($($hits.Count))"
  $hits | ForEach-Object { "- $(Fmt-Date $_.LastWriteTime) | ``$(Rel $_)``" }
  ""
}
