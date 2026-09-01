---
name: bdm-site-inspection-report
description: Build a NEW BDM Site Inspection Record (Form 331) from a site visit captured in ProjectHub on the PM's phone — or, as a fallback, from a OneNote "Export to PDF". Trigger on "site inspection report", "write up the site inspection", "SIR", "inspection record for a project", "yesterday's site walk", or whenever inspection photos and notes are handed over (optionally with a context email). Pulls the inspection, its items and its photos from ProjectHub, populates the latest Form 331 (particulars, attendees, sectioned observations, captioned photo grid), defaults to 4 photos per page with the signature block removed, then pairs with `bdm-pdf-export` for a Word-faithful PDF. Also supports pre-filling a planned-vs-actual walk sheet the day before an inspection. NOT for meeting minutes (use `bdm-site-and-adhoc-minutes` or `meeting-minutes-update`) or progress certificates.
type: process
template_revision: R2
issued: 2026-06-01
revised: 2026-09-01
approved_by: James Gill
maintained_by: BDM Standards
parent_skill: bdm-house-style
related_skills: bdm-pdf-export, bdm-house-style, bdm-site-and-adhoc-minutes
template_source: 331-Site_Inspection_Record_R{latest}_{YYYY-MM}.docx (Working Copy / 300 Project Management - Contract Delivery)
defaults: { photos_per_page: 4, signature_block: removed }
---

# BDM Site Inspection Report — Create (Skill)

Turns a site visit into a finished BDM **Site Inspection Record** (Form 331), Word + PDF.

**Capture moved to ProjectHub in July 2026.** Inspections are recorded on the PM's phone in
ProjectHub during the walk. **Check ProjectHub first** — do not ask for a OneNote export until
you have looked. OneNote remains supported as a fallback for older visits and for PMs who still
capture that way.

## 1. When to use

Trigger when a BDM PM hands over a OneNote/photo PDF from a site visit and wants it written up:

- "Prepare a site inspection report for <project>"
- "Write up this site inspection" / "turn my OneNote into a report"
- "Inspection record for <project> from these photos"
- A OneNote export PDF (photos + notes) is attached, optionally with a context email.

## 2. When NOT to use (hand off)

- **Meeting minutes** (site meeting, workshop, kickoff) -> `bdm-site-and-adhoc-minutes`; recurring/PCG -> `meeting-minutes-update`.
- **Progress / payment certificates** -> `progress-certificate-update` (Form 335).
- **Routine monthly funder report** -> the monthly report workflow (not packaged in this plugin — ask the user).

## 3. Inputs

**Primary — ProjectHub (check here first):**

- `inspections` — the inspection record: project, date, PM, stage, weather, attendees.
- `inspection_items` — one row per observation, in walk order, with section, text and action owner.
- `photos` — the photos, linked to their inspection item.

**Fallback — OneNote:** the "Export to PDF" of the visit (photos + the PM's narrative), for
visits captured before the move or by a PM still using OneNote.

**Optional:** a context email/thread (back-story, parties, dates, technical detail). Use it to
enrich and cross-check — never to override what the PM saw.

## 4. Process — ProjectHub path (default)

1. **Identify the project & folder.** Match the project folder under the Projects library,
   resolved at run time (`bdm-house-style` § 8/§ 9). Read the sandbox `Project_Summary_*.md`
   per § 13.3 — **if missing or stale, flag it and continue**; it does not block the report.

2. **Find the inspection in ProjectHub.** Search `inspections` for the project and date. If
   more than one inspection exists for that day, list them and ask which. Take from the record:
   **inspection date and time, PM, stage of works, weather, attendees.**

   > **The date comes from the ProjectHub record**, not from a file timestamp and never
   > invented. Only fall back to the OneNote page timestamp on the OneNote path.

3. **Pull the items.** Read `inspection_items` for that inspection, in walk order. Each row
   carries its section, observation text and action owner — that is the observations table,
   already sectioned. Do not re-sequence them; the walk order is the narrative.

4. **Pull the photos — in parallel.** Fetch via the agent-drawings endpoint, concurrently:

   ```bash
   printf '%s\n' "${PHOTO_URLS[@]}" | xargs -P 8 -I{} curl -sSfL -O {}
   ```

   **Do not download serially.** A serial pull of 40 photos blew a two-minute timeout and the
   whole run failed. Eight at a time is the tested setting.

   **Skip `stitch_photos.py` entirely on this path.** ProjectHub photos arrive whole. Stitching
   is a OneNote-only repair for OneNote's sliced export.

5. **Number the report.** `SIR-ddmmyy` from the inspection date. For a second or third
   inspection on the same day, suffix `-2`, `-3`.

6. **Draft the content** into a config JSON (see `scripts/example_config.json`):
   - **Particulars** — ProjectName, ProjectNumber, InspectionDate/Time, Weather, StageOfWorks,
     all from the ProjectHub record.
   - **Attendees** — who was actually on site. Don't guess names; use a role label
     (e.g. "Site technician") if unsure.
   - **Observations** — sectioned table from `inspection_items`. Section header rows use
     `is_section=true` (e.g. `1.0 BACKGROUND`). For an **incident**: BACKGROUND / SITE
     OBSERVATIONS / RECTIFICATION OPTIONS / WHS & RESIDENT IMPACT / NEXT STEPS. For a **routine
     progress** visit: GENERAL / WORKS IN PROGRESS / QUALITY & WORKMANSHIP / WHS &
     ENVIRONMENTAL / PROGRAMME. Put an owner in the ACTION column and cross-reference photos in
     the text, e.g. "(Photos 3-6)".
   - **Captions** — one per photo, referencing its observation item, e.g.
     "Photo 4 - Water at the fire-stair drain (ref 2.3)."
   - **Options** — `photos_per_page` default **4**; `signature` default **false**.

7. **Build the Word doc.** `python3 scripts/build_report.py config.json "<out>.docx"` — finds
   the latest Form 331, fills the three tables, deletes blank attendee rows, drops the signature
   block (unless kept), forces the **PHOTOGRAPHS heading onto the photo page**, and lays out the
   captioned photo grid. The builder creates a **separate photo table for each configured page**
   and inserts an ordinary page break between tables — do not rely on Word's automatic table
   pagination.

8. **Export the PDF** with `bdm-pdf-export` — load the skill and run its inlined preflight, then
   convert and render-check. Do not call a script path from another user's folder.

9. **Save and mirror.**
   - Word + PDF into the project's `08_Issued Reports\NNN - <short title>\`.
   - Filename `<ProjectShort>_<ddmmyy> - Site Inspection Record.docx` / `.pdf`.
   - **Mirror the finished PDF back to the ProjectHub `contract` bucket** so it is on the record
     against the inspection. A report that exists only on the file share is invisible to
     everyone working from ProjectHub.
   - **The report is built straight into `08_Issued Reports\NNN - <short title>\`** — not staged in
     `00_ai_sandbox` and moved later (`bdm-house-style` § 13.12). Follow the report-folder numbering
     already in use on that project. Scratch and intermediates (stitched photo temp files, render
     previews, `.bak`) go to a temp directory outside the project and are swept at the end.

## 4a. OneNote fallback path

Only when there is no ProjectHub record for the visit.

1. Read the narrative text from the OneNote PDF (it carries the PM's dictated notes).
2. **Stitch the photos:** `python3 scripts/stitch_photos.py "<onenote.pdf>" <out_dir>`. OneNote
   slices each photo into stacked strips on export; the script regroups by page and rebuilds one
   clean photo per page. Raw `pdfimages` output gives half-photos.
3. **Source the inspection date from the OneNote page timestamp** — never invent it.
4. Rejoin the main path at step 6.

## 4b. Planned-vs-actual pre-fill (the day before)

When an inspection is scheduled, pre-fill the walk sheet the day before so the PM walks with
structure instead of a blank page:

- **One row per level** (or per zone, if the project is zoned rather than stacked).
- Each row carries a **PLANNED** sentence — what is expected to be in progress at that level,
  from the programme — and a **blank ACTUAL**.
- **No carry-over commentary.** Do not pre-populate ACTUAL from the last inspection, and do not
  copy forward last visit's observations as "expected". The PM records what they see; a
  pre-filled ACTUAL biases the walk and, worse, survives into the report if the PM doesn't
  overwrite it.

## 5. House rules baked in (don't relearn these)

- **Photos default 4 per page** (2x2, ~5.2 cm wide, captions **Calibri** 8 pt italic navy — Brand Standard R3 is Calibri-only). `photos_per_page` also supports 1 and 2. The builder enforces this count using separate paginated tables, and PDF QA must confirm **no caption is stranded on a later page**.
- **Signature block removed by default** — site inspection records issue as informational. Set `options.signature=true` to keep the signed line.
- **PHOTOGRAPHS heading sits with the photos** — a page break is forced before it so the heading never strands at the foot of the observations page.
- **Blank attendee rows are deleted**, not left empty.
- **Never invent** dates, costs, contract refs, or attendee names (`bdm-house-style` § 13.1). The inspection date comes from the **ProjectHub record**, or from the OneNote page timestamp on the fallback path.
- **Writing to the synced folder:** build in a temp directory outside the project, then write into `08_Issued Reports\` with the fsync byte-write in `bdm-house-style` § 8.6 — **not** `cat`+`sync`, which corrupts files, and **not** via a sandbox staging copy (§ 13.12). If the target `.docx` is locked (open in Word), say so and ask for it to be closed.
- **Skip `stitch_photos.py` on the ProjectHub path.** It is a OneNote-only repair.

## 6. Files

- `scripts/stitch_photos.py` — OneNote PDF -> clean per-page photos.
- `scripts/build_report.py` — config JSON + photos -> Form 331 Word doc.
- `scripts/example_config.json` — worked example (Greenwich on Chevron, B2 pipe failure, 28 May 2026).

## 7. Provenance

Built from the Greenwich on Chevron Basement 2 drainage-failure inspection, 1 June 2026 — the first end-to-end run of OneNote -> Form 331 -> Word + PDF. Rebuilt ProjectHub-first in August 2026 after phone capture replaced OneNote.

## 8. Revision control

| Rev | Date | Editor | Change |
|---|---|---|---|
| R1 | 2026-06-01 | James Gill | Initial issue. OneNote export as the sole input. |
| R2 | 2026-08-18 | James Gill | Retains the 17 Aug photo-pagination fix. ProjectHub is now the primary source (inspections / inspection_items / photos); OneNote demoted to a documented fallback. Photos pull in parallel (`xargs -P 8`) — serial download of 40 photos blew a two-minute timeout. `stitch_photos.py` skipped on the ProjectHub path. Added `SIR-ddmmyy` numbering with same-day suffixes, the `contract` bucket mirror, and the planned-vs-actual pre-fill (no carry-over commentary). Inspection date now comes from the ProjectHub record. Captions Aptos -> Calibri per Brand Standard R3. OneDrive write method corrected. |
| R3 | 2026-09-01 | James Gill | Save location made explicit — the report is built straight into `08_Issued Reports\NNN - <short title>\`; the "working files stay in the sandbox" line and the sandbox-staging step in the synced-folder write are removed. Filing rule aligned to `bdm-house-style` § 13.12 (locked 1/9/26): the deliverable is built and saved directly in its regular project folder on the first save, following the sub-folder naming already in use on that project; no `00_ai_sandbox` staging; scratch and intermediates stay in a temp directory outside the project; saving is not issuing. |
