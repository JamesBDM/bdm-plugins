---
name: bdm-site-and-adhoc-minutes
description: Draft NEW meeting minutes for SITE MEETINGS and AD-HOC / WORKSHOP / KICKOFF meetings only. NOT for PCG or any recurring meeting series — those use `meeting-minutes-update` to roll a master document forward each cycle. Trigger on "site meeting minutes", "SM###", "write up today's site walk", "workshop minutes", "WS###", "ad-hoc meeting", "kickoff minutes", or a transcript / notes from a one-off meeting. Auto-increments the meeting number from the project folder, rolls forward and auto-closes actions from the prior meeting based on the transcript, and updates the project sandbox PROJECT.md with new actions / decisions / meeting history. Pairs with `bdm-pdf-export` for a Word-faithful PDF. If the user mentions PCG, monthly client meetings, fortnightly status, or design coordination, hand off to `meeting-minutes-update` instead.
type: process
template_revision: R2
issued: 2026-05-20
approved_by: James Gill
maintained_by: BDM Standards Agent
parent_skill: bdm-house-style
related_skills: bdm-pdf-export, meeting-minutes-update, bdm-house-style
template_source: 232-Meeting_Memorandum_R<latest>_<YYYY-MM>.docx (Working Copy)
scope: site_meetings, ad_hoc, workshops, kickoffs
not_for: pcg, recurring_meetings, design_coordination, monthly_status
---

# BDM Site & Ad-hoc Meeting Minutes — Create (Skill)

Drafts a fresh set of meeting minutes against the latest BDM Form 232 Meeting Memorandum template, scoped to **site meetings** and **ad-hoc / workshop / kickoff** meetings only. Recurring meeting series (PCG, fortnightly status, design coordination) already have an established workflow that rolls a master document forward each cycle — use `meeting-minutes-update` for those instead.

## 1. When to use

Trigger on **one-off or site-based** meetings where there's no existing rolling master document to update:

- **Site Meetings (SM###)** — on-site construction phase walkthroughs with contractor + consultants.
- **Workshops (WS###)** — design workshops, value-management workshops, risk workshops.
- **Ad-hoc / one-off meetings** — kickoffs, scope reviews, supplier presentations, ad-hoc client catch-ups that aren't part of a numbered recurring series.

Typical user phrases:

- "Draft site meeting minutes for <project> from this transcript"
- "Write up today's site walk with Centro"
- "SM004 from these notes"
- "Workshop minutes for the VM session"
- "Kickoff meeting writeup"
- "I just got out of an ad-hoc with the structural engineer, here are my notes"

## 2. When NOT to use (hand off)

- **PCG meetings (PCG###)** → use `meeting-minutes-update`. James maintains a rolling PCG master document and updates it each cycle with tracked changes — do not start from scratch.
- **Any recurring meeting series** (fortnightly status, monthly client, design coordination, programme reviews) → also `meeting-minutes-update`, same reason.
- **Updating an existing `.docx`** of minutes (site or otherwise) → `meeting-minutes-update`.
- **Pre-meeting agendas** — this skill only handles post-meeting write-ups.
- **Monthly funder/lender reports** → the monthly report workflow (not packaged in this plugin — ask the user).

If the user's request is ambiguous (e.g. "draft the minutes" with no series named), ask one sharp clarifying question: *"Site meeting or recurring (PCG / monthly) — different workflow."* Then route accordingly.

## 2. Inputs the user may provide

- **Transcript file** (`.docx` / `.txt`) — auto-transcribed or typed record.
- **Pasted bullet notes** — quick brain-dump in chat.
- **Email thread** — forwarded summary.
- **Prior minutes + delta** — "here's PCG005 plus what changed today, roll it forward".

If any are missing, ask one sharp clarifying question and wait (per `bdm-house-style` § 11.3).

## 3. Default opening clarifications (only if not in the request)

If the user just says "draft the minutes" with no context, ask in one line: *"Site meeting, workshop or ad-hoc — and which project? If it's a PCG or recurring meeting, I'll hand off to meeting-minutes-update."*

If the project / series is obvious, just proceed.

## 4. Workflow

### Step 1 — Locate the project + meeting folder

- Identify the project folder from the user's request. Project folders live in the SharePoint-synced `Projects - Documents` library under the current user's home directory (`~/BDM/Projects - Documents/<ProjectFolder>/`) — resolve it at runtime, never hardcode a username. See `bdm-house-style` § 7.
- Read the project sandbox: `<project>/00_ai_sandbox/PROJECT.md`. This is the source of truth for project name, key people, existing meeting history, open actions, decisions log.
- **If the sandbox is missing or stale, flag as a blocker** — do not re-read source files blind (per `bdm-house-style` § 11.2).
- Identify the meeting subfolder under `<project>/07_Meeting Minutes/`. The PCG pattern (`PCG Meetings/`) is the canonical layout; mirror it for other series:
  - Site Meetings → `07_Meeting Minutes/Site Meetings/`
  - Workshops → `07_Meeting Minutes/Workshops/`
  - Design Coord → `07_Meeting Minutes/Design Coordination/`
  - Ad-hoc — pick or create a sensibly named subfolder.
- If the subfolder doesn't exist yet, create it and tell the user.

### Step 2 — Determine the meeting number

Run `scripts/next_number.py` against the meeting subfolder:

```bash
python3 scripts/next_number.py "<meeting subfolder>" "<prefix>"
```

It scans for filenames like `<prefix>###_*.docx` (case-insensitive on the prefix), finds the highest existing number, and returns the next one. Example: in a folder with `SM001.docx`, `SM002.docx`, `SM003.docx`, calling it with prefix `SM` returns `004`.

If the folder is empty for that series, it returns `001`. Confirm the prefix with the user if not obvious (PCG, SM, WS, DC, etc.).

### Step 3 — Read the latest template

Templates live in the BDM Working Copy templates library under `200-PM Pre-Contract` (or `500-Construction` for site meetings — both use Form 232). Resolve the path from the current user's home directory as set out in `bdm-house-style` § 7; do not hardcode a username.

- Pick the most recent revision of `232-Meeting_Memorandum_R*_<YYYY-MM>.docx` by sorting on the revision/date in the filename.
- **Do not use the Control Copy** — that's locked reference only.
- **Do not use the legacy `Sally Standards` folder** — superseded.

### Step 4 — Read the previous minutes for roll-forward

If a prior meeting exists in the folder (highest existing `<prefix>###_*.docx`), read it to extract:

- **Open actions** from the Action Register.
- **Last-meeting attendee list** (good default, edit per today's attendance).
- **Tone and section structure** from the topics (carry over the section headings so the project's minutes feel consistent over time).

Use the `docx` skill's `extract-text` or `pandoc` to read the prior .docx as markdown.

### Step 5 — Read the transcript and build the change map

Read the user's transcript / notes and build a structured plan **before touching the template**:

```
META:
  Project: <from PROJECT.md>
  Meeting no: <from Step 2>
  Date/time: <from transcript or user>
  Location: <Teams / Site / Office>

ATTENDEES / APOLOGIES:
  <list with name, initials, company, email — pull from PROJECT.md key-people table; ask if any new face attended>

SUMMARY (3–6 sentences, plain prose):
  Headline outcomes, decisions, where the project sits.

TOPICS (numbered 01, 02, 03… by section):
  <heading>:
    - <bullet — single complete thought>
    ...

ACTION REGISTER:
  Roll forward from prior minutes:
    - <existing action> → CLOSE if transcript confirms done
    - <existing action> → CARRY if still open and no update
    - <existing action> → UPDATE if discussion changed scope/owner/date
  Add new actions raised in this meeting.

NEXT MEETING:
  <date / location / TBC>
```

### Step 6 — Populate the template

Use `scripts/build_minutes.py` with the JSON config:

```bash
python3 scripts/build_minutes.py \
    --template "<path to latest Form 232>" \
    --config /tmp/minutes_config.json \
    --output "<meeting folder>/<prefix>###_<project short name>.docx"
```

The script handles:
- Meta table (project / meeting no / location / date·time).
- Attendees + apologies tables (auto-removes unused placeholder rows).
- Distribution line.
- Summary paragraph (preserves run colours — tan prefix + dark body where applicable).
- Topic sections with proper 2-run formatting (`NN ` in tan, heading in navy bold; bullet `•\t` in tan, body in dark navy).
- Action register table (auto-grows rows beyond the template's default 4 placeholder rows).
- Next meeting line.

Filename convention: `<prefix>###_<project short name>.docx` — e.g. `SM004_160 Pacific Parade.docx`, `WS002_167 Hedges.docx`.

### Step 7 — Preflight + PDF (calls `bdm-pdf-export` skill)

The output `.docx` is built from a BDM template, so all three preflight fixes from `bdm-pdf-export` apply:

```bash
bash <George>/bdm-pdf-export/scripts/pdf_export.sh "<path to new .docx>"
```

This:
1. Installs Aptos fonts in the sandbox if missing.
2. Normalises `<w:tblGrid>` in every table.
3. Resets cloned-row interior borders.
4. Generates the matching `.pdf` next to the `.docx`.

**Never ship a PDF without preflight.** See `bdm-pdf-export/SKILL.md` for why.

### Step 8 — Update the project sandbox

Update `<project>/00_ai_sandbox/PROJECT.md`:

- **Section: Meeting history** — append a row for the new meeting (number, date, file path).
- **Section: Open actions register (live)** — move the previous meeting's open actions into a "Closed at <new meeting>" subsection with their outcomes, and create a new "From <new meeting>" table with the rolled-forward + new actions.
- **Section: Decisions log** — append any new decisions captured in the minutes with the date.

### Step 9 — Deliver

Reply with a short "what's in it / what changed" summary plus computer:// links to both the .docx and .pdf. Per `bdm-house-style` § 11.6 — succinct, no excessive postamble.

```
[<prefix>### — Word](computer://<full path>.docx)
[<prefix>### — PDF](computer://<full path>.pdf)
```

## 5. Tone of the minutes

Write as the project Superintendent / meeting chair (per `bdm-house-style` § 11.4):

- Direct. Plain English. Short sentences. Australian spelling.
- Practical, calm construction tone. No corporate jargon.
- Match the technical detail of the prior meetings' minutes — terse if they're terse, full sentences if they are.

Record **decisions and actions**, not opinions or back-and-forth discussion.

## 6. Gotchas

- **Don't invent dates, costs, durations, or contract references.** If the transcript is ambiguous (e.g. "next Tuesday"), either leave it as a relative phrase or flag for the user to confirm — don't pick a specif