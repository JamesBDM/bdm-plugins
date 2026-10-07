---
name: bdm-project-sandbox-setup
description: Set up a BDM project's AI sandbox — create the `00_ai_sandbox` folder, backfill a full `Project_Summary_<Project>.md` (all 17 sections of the CLAUDE.md §13 standard) from what is actually in the project folder, its saved emails and ProjectHub, and build the `AI_Context\` folder (the project's documents except drawings, converted to markdown, scanned PDFs OCR'd, each with a source/revision header). Use when a project has no sandbox, no project summary or no AI_Context, when another skill flags "sandbox missing or stale", or when the user says "set up the sandbox", "create the project summary", "backfill the summary", "onboard this project", "build the AI context", "convert the project documents", "OCR the scans", "refresh AI_Context", "is the AI context stale", "run the monthly audit", "get my projects AI-ready", "which projects don't have a sandbox", or "do all my projects". Works on one project or sweeps every live project folder. Read-only on project documents — the only writes are the sandbox folder, the summary file and AI_Context. Never invents a date, cost, reference or contact; gaps become "Confirm …" actions. Not for updating a summary that already exists (other skills keep it live on every touch).
metadata:
  type: process
  revision: R2
  issued: 2026-10-07
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-house-style, bdm-contract-admin-register
  implements: CLAUDE.md §8 (sandbox first; AI_Context rule, R5) and §13 (project summary standard incl. §16 AI_Context pointer and §17 conventions; monthly audit)
---

# BDM Project Sandbox Setup

Every BDM skill starts by reading `<project>\00_ai_sandbox\Project_Summary_*.md`. A project without one makes every skill flag a blocker and work blind. This skill closes that gap: it creates the sandbox and writes a complete, sourced summary from the project folder, so the next skill that runs has something true to stand on.

This is the **only** skill that creates a project summary. CLAUDE.md §8 says skills must never create a stub — this skill doesn't. It writes all 17 sections from a real read of the folder, and marks what it could not find.

Since R2 it also builds `00_ai_sandbox\AI_Context\` (CLAUDE.md §8, R5): the project's static documents, except drawings, converted once to markdown so later skills quote what a document actually says instead of re-reading a PDF under pressure. The summary holds the current position; AI_Context holds the source text.

---

## 1. Rules that don't bend

1. **Read-only on project documents.** The only things this skill writes are the `00_ai_sandbox` folder (if missing), the `Project_Summary_*.md` inside it, and `00_ai_sandbox\AI_Context\`. Never move, rename, copy or delete a project file — flag misfiled things in §16 instead. The AI_Context scripts only ever delete their own generated `.md` copies when the source is gone or out of scope.
2. **No invented facts.** Every date, dollar figure, reference number, firm and person comes from a document or email you opened. Put the source path on the line. Not found → `TBC — not found in folder`, plus a "Confirm …" action in §10.
3. **Don't overwrite.** If a `Project_Summary_*.md` already exists, don't rewrite it: skip the summary steps for that project and report it. Updating an existing summary is the job of every other skill's "on every touch" step. The two exceptions are AI_Context, which is rebuilt idempotently (unchanged sources are skipped), and the §16 AI_Context pointer block between its markers, which the scripts refresh.
4. **One sandbox per project.** Match `00_ai_sandbox` case-insensitively (`00_AI_sandbox` counts). Never create a second one alongside.
5. **No personal paths in the output.** Write paths relative to the project folder. Resolve the user's home at runtime (`%USERPROFILE%` / `$HOME`) — never hard-code a user name (`bdm-house-style` §9).
6. **Internal work.** This is a CLAUDE.md §10 "internal and reversible" task — do it, then report. No approval queue, no sign-off block, no signature, no DRAFT marking.
7. **Live registers never go into AI_Context.** CAR, correspondence register, fee registers, trackers, cash flows: always read from source. Drawings stay out too.
8. **OCR text is machine-read.** Scanned PDFs are filled with Windows OCR and marked so in the header. Never treat an OCR'd figure, date, name or clause number as checked: read the source before relying on it. Handwriting is not read.
9. **Don't touch security settings.** If Office refuses to open a file (file block, protected view), log it as "read the source" and move on. Never change Trust Center or file-block settings to get a conversion through.

---

## 2. Locate the projects

Projects root, in this order:
1. A path the user gives.
2. `%USERPROFILE%\BDM\Projects - Documents` (the synced SharePoint library).
3. In Cowork or another sandboxed session: the mounted `Projects - Documents` folder. If it isn't mounted, ask the user to connect it — one question, then wait.

A project folder starts with a 6-digit BDM job number (`202603_106 Hargreaves Ave, Chelmer`). Skip everything else: personal folders, `_Projects Archived`, `_Project Opportunities`, `_ New Job Folder`.

**Scope.** If the user's own layer (`CLAUDE.local.md` or private memory) lists their active projects or sweep scope, use it. Otherwise "my projects" / "all projects" means every live project folder at the root.

---

## 3. Workflow

### Step 1 — Status sweep

On Windows run the bundled scanner (read-only):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}\skills\bdm-project-sandbox-setup\scripts\scan_project.ps1" -List
```

(Add `-Root "<path>"` if the projects root isn't the default. If `${CLAUDE_PLUGIN_ROOT}` isn't expanded in your session, the scripts are in the `scripts\` folder next to this SKILL.md.) Outside Windows, do the same with `ls`/`find`: for each job folder, is there a `00_ai_sandbox` (any case), and does it hold a `Project_Summary_*.md`?

Show the user the projects that are missing a sandbox or a summary, as a short table. If they named one project, skip straight to it. If they asked for "all", confirm the list once — "Set up these N? (y / pick)" — then go. Don't re-ask per project.

Also report, but don't fix: retired summary names still present (`PROJECT.md`, `Project_Summary.md`, `*_STATE.md`) and duplicate summaries (e.g. a `-LAPTOP-xxxx` sync-conflict copy).

### Step 2 — Create the sandbox

If `00_ai_sandbox` is missing, create exactly that folder at the project root. Nothing else goes in it at this step.

### Step 3 — Inventory the project

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}\skills\bdm-project-sandbox-setup\scripts\scan_project.ps1" -Project "<project folder name>"
```

This gives: spine check against the BDM Project Folder Standard R1, file count and newest files per top-level folder, an email digest parsed from the `.msg` filenames (`YYYY-MM-DD_HHMMSS_Sender_Subject.msg`), key-document candidates by filename, and the suggested summary filename.

**Template carry-overs are not project facts.** Projects copied from `_ New Job Folder` still hold its stubs — e.g. recruitment/hours emails dated Aug 2025, `T218_Meeting Minutes_v2_280125.docx`, `121 Practical Completion Certificate_Rev I_Jan18.docx`, a 2017 `1_Invoice Register.xlsx`. Ignore them as sources; note them in §16.

### Step 4 — Read the sources

Read in this order, newest first within each group. Stop a group once the facts it feeds are settled — don't read every file.

| Order | Where | Feeds |
|---|---|---|
| 1 | `01_Client\`, BDM fee proposal / engagement | §1 client, BDM role, fee status |
| 2 | `13_Contract Admin\00_Contract Documents\` (or legacy `13_Contract`, `Briefing Documents\Contracts`), the live CAR `BDM_ContractAdminRegister_*.xlsx` | §1 contract, §5 cost, §6 variations, §7 EOTs, §8 notices |
| 3 | `05_Consultants\02_ Fee Proposals`, `03_ Consultant Agreements`, insurance certs | §2 team, fees, PI expiry |
| 4 | `03_Applications & Approvals\`, `04_Statutory Authorities\` — decision notices | §1 DA/BA/Energex refs, §10 open DA conditions |
| 5 | `08_Issued Reports\`, `02_Project Control\2.0_Cost Reports`, QS progress reports | §5 cost, §15 reports register, §3 status |
| 6 | `07_Meeting Minutes\` — latest set | §3 status, §10 actions, §11 decisions |
| 7 | `09_Programmes\` — latest | §4 programme |
| 8 | `06_Drawings & Specifications\` — latest rev per discipline (filenames are usually enough) | §13 drawings |
| 9 | `00_Email Communication\` — the most recent ~15–25 relevant emails, plus any whose subject names a contract, claim, approval or appointment | §3, §11, §12 contacts, gaps everywhere |
| 10 | ProjectHub (if the connector is available): `list_projects` → the project's record, contacts, registers | §1, §12 contacts — cross-check, folder documents win on conflict |

Reading `.msg` emails on Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}\skills\bdm-project-sandbox-setup\scripts\read_msg.ps1" -Path "<file1.msg>","<file2.msg>" -MaxBody 3000
```

It uses Outlook desktop if installed (headers, attachments, latest message only) and falls back to raw text extraction if not. Batch 5–10 files per call. PDFs, Word and Excel: use the pdf / docx / xlsx skills or whatever reader the session has.

**Big projects or "all" sweeps:** where the session supports sub-agents, give each project (or, on a very large project, each source group above) to its own agent in parallel, with this skill's rules 1–2 in its brief. Agents return facts with source paths; you write the summary yourself.

### Step 5 — Write the summary

Copy `references/project_summary_template.md` and fill it.

- **Filename:** `Project_Summary_<Project_Name>.md` — the folder name with the job number stripped, punctuation dropped, spaces → underscores (`202603_106 Hargreaves Ave, Chelmer` → `Project_Summary_106_Hargreaves_Ave_Chelmer.md`). The scanner prints it.
- **Title line:** `# Project Summary — <name, suburb>`.
- **Change log** at the top: one entry recording the backfill — date, sources read count, gap count, and "nothing moved or renamed".
- **All 17 sections present**, in order. A section that doesn't apply yet gets one line saying why (e.g. QS-only engagement or pre-contract → §6–§8 "N/A — no head contract administered by BDM"). Keep the heading.
- **Tailor to the engagement.** QS / lender-side projects: §1 lender and drawdown basis, §5 from the latest QS progress report, §15 lists the QS reports. DM / pre-contract: weight §2 team, §4 programme to DA/BA milestones, §9 feasibility risks.
- **§10** gets a "Confirm …" action for every important gap (contract sum, DA ref, PI expiry, client contact …), owner = the PM.
- **§16 folder gap flags:** empty `01_Client\`, services drawings under `05_Consultants\`, deliverables parked in `00_ai_sandbox\` that have a regular home (CLAUDE.md §8), pre-R1 folder names (`13_Contract`, `13a_…`, `08a_…`, `15_Photographs`), template carry-overs. Flag only — no moves.
- **§17 conventions:** record the folder and file naming the project actually uses (claim folder pattern, report naming, VO numbering) so later skills follow it. Add contract quirks only if a document shows them. §17.2 dated notes carry the date.
- Plain English, Australian spelling, short lines. Write UTF-8.

Write the file into `00_ai_sandbox\`. Re-open it once and check: 17 headings present, no `[placeholder]` brackets left, the template's HOW TO FILL comment removed, every $ figure and date has a source.

### Step 6 — Build AI_Context

Runs for every project in scope, including ones whose summary already existed. Needs Node 18+ and three libraries in a per-user folder outside the synced library (see the top of `scripts\common.mjs`; one-off install). Windows is needed for the Word/Excel legacy conversion and for OCR; elsewhere those two steps are skipped and the files are logged.

```powershell
$s = "${CLAUDE_PLUGIN_ROOT}\skills\bdm-project-sandbox-setup\scripts"
node "$s\build_ai_context.mjs" --project "<job folder>" --legacy-only   # old .doc/.xls via Word/Excel, once
node "$s\build_ai_context.mjs" --project "<job folder>"                 # convert, exclude, index
node "$s\ocr_stubs.mjs"        --project "<job folder>"                 # OCR scanned PDFs (Windows OCR)
node "$s\build_ai_context.mjs" --project "<job folder>"                 # refresh indexes with the OCR results
node "$s\summary_pointer.mjs"  --project "<job folder>"                 # §16 pointer in the summary
```

Repeat `--project` for several jobs, or pass `--projects-file <txt>` (one folder per line, e.g. the user's active list) or `--all` (every job folder with a sandbox). For more than a few hundred documents, run the legacy pre-pass first, then one build process per two or three projects in parallel; the scripts share a cache and never drive Office from two processes at once.

What it does, so you can explain it:

- **Converts:** PDF text (pdf.js), Word (document XML, tables kept as markdown tables), Excel (visible sheets, first 400 rows), PowerPoint text, plain text. One `.md` per source in `AI_Context\<top folder>\`, header first: source path, source modified time and size, method, quality, conversion date, rules version.
- **Excludes, with the reason in `_build_log.csv`:** drawings (large-format pages, title-block text, or label-only text on a plan-named file, in any folder), image-only pages, live registers, superseded and archived copies (`ss`, `_SS`, `superseded`, `_ARCHIVE`, `old`), the sandbox itself, Office lock files, and the second of a same-name pair in one folder (the PDF is kept as the issued form unless it has no text).
- **Indexes:** `INDEX.md` lists the contract, specification and approvals first ("read this first", tested on the file name and the contract-documents folder, never on `13_Contract Admin` as a whole), then one `_INDEX.md` per folder, the OCR'd files, the still-unreadable ones and a build summary.
- **OCR:** tries all four rotations when the upright read is noise (sideways-scanned forms are common) and OCRs a short-path temporary copy when the path is over 260 characters.
- **Idempotent:** a source whose modified time and size match its copy's header is skipped; copies whose source has gone are removed.

Check before you report: open `INDEX.md`, read the "read this first" list for anything that is obviously not a contract, spec or approval, and look at `_build_log.csv` for errors. If a whole contract "Part" was excluded as a drawing, look at a page of it before accepting that (they are often the drawing set or photo annexures, but check).

### Step 7 — Report back

One table, one line per project:

| Project | Sandbox | Summary | Sources read | Gaps | AI_Context (converted / OCR'd / unreadable / errors) | Top flag |
|---|---|---|---|---|---|---|

Then a short "What to do next": the two or three gaps the PM should close first (usually contract sum, client contact, consultant PI), and any AI_Context errors that matter (a contract document that could not be converted). Link each summary file and each `INDEX.md`. Keep it short.

If the session has a run log or console the user's layer asks for, log the run there.

---

## 4. Keeping AI_Context current — the monthly audit

CLAUDE.md §13 makes the first-of-month audit a standing trigger. The AI_Context part is one command:

```powershell
node "$s\audit_ai_context.mjs" --projects-file "<active list>" --refresh --report "<user folder>\AI_Context_Audit_<yyyy-mm>.md"
```

It reports, per project, copies that are **stale** (source modified time or size changed), copies whose **source was removed**, and documents **added since the last build**. With `--refresh` it brings each project that needs it current in the same pass (legacy pre-pass, build, OCR, index, §16 pointer) and reports the state after. Without `--refresh` it changes nothing.

Run it on a schedule where the session supports scheduled tasks (first of the month, early morning), and on demand when a contract is amended or a document set is re-issued. Log the run where the user's layer asks for it. A project still showing "needs refresh" after a refresh is a flag for the user, not something to retry in a loop.

---

## 5. Edge cases

- **Sandbox exists, no summary, other files inside** (e.g. an `Initial Report\` folder): create the summary alongside. If those files are deliverables with a regular home, flag in §16 — don't move them.
- **Retired summary file present** (`PROJECT.md` etc.) **but no `Project_Summary_*.md`:** use it as a source, write the standard file, flag the retired one for the PM to remove. Don't delete it.
- **Near-empty project** (only template carry-overs): still create the sandbox and a summary — §1 from the folder name, everything else `TBC`, and §3 says "No project documents filed yet as at <date>."
- **Nera-style multi-contract projects:** one summary; split §5–§7 by contract with a sub-heading each.
- **Conflicting figures** between two documents: record both with sources, put the conflict in §9 and a "Confirm …" in §10. Don't pick one.
- **A project the user says is dormant or archived:** skip it unless they insist.
- **Office refuses an old `.xls` or `.doc`** ("Office has detected a problem with this file"): file-block policy. Logged as "read the source"; the PDF in the same folder usually converts. Don't change security settings (rule 9).
- **Scans with handwriting** (statutory declarations, signed forms): OCR reads the printed form, not the handwritten names and dates. The header says so; read the source for those.
- **Large AI_Context:** a big job can produce tens of MB of markdown, which syncs to everyone who syncs the library. That is expected; the libraries and caches stay outside the synced library by design.

---

## 6. Revision control

| Rev | Date | Editor | Change |
|---|---|---|---|
| R1 | 2026-10-06 | James Gill | Initial issue. Sweep + per-project backfill to the CLAUDE.md §13 standard (17 sections, incl. §17 conventions). Bundled read-only `scan_project.ps1` and `read_msg.ps1`. |
| R2 | 2026-10-07 | James Gill | AI_Context build (CLAUDE.md R5 §8): new Step 6 and scripts `common.mjs`, `build_ai_context.mjs`, `convert_legacy.ps1`, `ocr_batch.ps1`, `ocr_stubs.mjs`, `summary_pointer.mjs`; monthly audit `audit_ai_context.mjs` (new §4); rules 7 to 9 (no live registers, OCR is machine-read, no security-setting changes); §16 pointer line in the summary template. Proven on ten live projects: 5,923 documents converted, 309 scans OCR'd. |
