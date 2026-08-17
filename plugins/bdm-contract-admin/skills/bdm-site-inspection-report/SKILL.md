---
name: bdm-site-inspection-report
description: Build a NEW BDM Site Inspection Record (Form 331) from a OneNote "Export to PDF" of an on-site visit — the photos + dictated/typed notes a BDM PM brings back from site. Trigger on "site inspection report", "write up the site inspection", "turn my OneNote into a site inspection report", "inspection record for a project", or whenever a OneNote/photo PDF of a site visit is handed over (optionally with a context email). Extracts and re-stitches the OneNote photos, populates the latest Form 331 (particulars, attendees, sectioned observations, captioned photo grid), defaults to 4 photos per page with the signature block removed, then pairs with `bdm-pdf-export` for a Word-faithful PDF. NOT for meeting minutes (use `bdm-site-and-adhoc-minutes` or `meeting-minutes-update`) or progress certificates.
type: process
template_revision: R1
issued: 2026-06-01
approved_by: James Gill
maintained_by: BDM Standards Agent
parent_skill: bdm-house-style
related_skills: bdm-pdf-export, bdm-house-style, bdm-site-and-adhoc-minutes
template_source: 331-Site_Inspection_Record_R{latest}_{YYYY-MM}.docx (Working Copy / 300 Project Management - Contract Delivery)
defaults: { photos_per_page: 4, signature_block: removed }
---

# BDM Site Inspection Report — Create (Skill)

Turns a site visit captured in **OneNote -> Export to PDF** into a finished BDM **Site Inspection Record** (Form 331), Word + PDF.

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

- **Required:** the OneNote "Export to PDF" of the visit (photos + the PM's narrative).
- **Optional:** a context email/thread (back-story, parties, dates, technical detail). Use it to enrich and cross-check — never to override what the PM saw.

## 4. Process

1. **Identify the project & folder.** Match the project folder under `Projects - Documents`. Check `00_ai_sandbox` per `bdm-house-style` § 11.2 — if missing/stale, **flag it** (don't block the report).
2. **Read the source.** Pull the narrative text from the OneNote PDF (it carries the PM's dictated notes) and read the context email if supplied.
3. **Stitch the photos.** `python3 scripts/stitch_photos.py "<onenote.pdf>" <out_dir>`.
   - OneNote slices each photo into stacked strips on export — the script regroups by page and rebuilds one clean photo per page. Don't use raw `pdfimages` output; you'll get half-photos.
4. **Draft the content** into a config JSON (see `scripts/example_config.json`):
   - **Particulars** — ProjectName, ProjectNumber (BDM job code), InspectionDate/Time (**source the date from the OneNote page timestamp — never invent it**), Weather (describe from Photo 1 if not stated), StageOfWorks.
   - **Attendees** — who was actually on site. Don't guess names; use a role label (e.g. "Site technician") if unsure.
   - **Observations** — a sectioned table. Use section header rows (`is_section=true`, e.g. `1.0 BACKGROUND`). Adapt the section set to the visit: for an **incident** use BACKGROUND / SITE OBSERVATIONS / RECTIFICATION OPTIONS / WHS & RESIDENT IMPACT / NEXT STEPS; for a **routine progress** visit use the form's standard GENERAL / WORKS IN PROGRESS / QUALITY & WORKMANSHIP / WHS & ENVIRONMENTAL / PROGRAMME. Put an owner in the ACTION column. Cross-reference photos in the text, e.g. "(Photos 3-6)".
   - **Captions** — one per stitched photo, each referencing the observation item, e.g. "Photo 4 - Water at the fire-stair drain (ref 2.3)."
   - **Options** — `photos_per_page` default **4**; `signature` default **false** (block removed). Override per job.
5. **Build the Word doc.** `python3 scripts/build_report.py config.json "<out>.docx"` — auto-finds the latest Form 331, fills the three tables, deletes blank attendee rows, drops the signature block (unless kept), forces the **PHOTOGRAPHS heading onto the photo page**, and lays out the captioned photo grid.
6. **Export the PDF** with `bdm-pdf-export` (`scripts/pdf_export.sh "<out>.docx"`). Eyeball it.
7. **Save.** Word + PDF into the project's `08_Issued Reports\NNN - <short title>\`. Filename: `<ProjectShort>_<ddmmyy> - Site Inspection Record.docx` / `.pdf`. Final docs to the issued-reports folder; working files in the sandbox.

## 5. House rules baked in (don't relearn these)

- **Photos default 4 per page** (2x2, ~5.2 cm wide, captions Aptos 8pt italic navy). `photos_per_page` also supports 1 and 2.
- **Signature block removed by default** — site inspection records issue as informational. Set `options.signature=true` to keep the signed line.
- **PHOTOGRAPHS heading sits with the photos** — a page break is forced before it so the heading never strands at the foot of the observations page.
- **Blank attendee rows are deleted**, not left empty.
- **Never invent** dates, costs, contract refs, or attendee names (`bdm-house-style` § 11.1). Inspection date comes from the OneNote timestamp.
- **OneDrive write quirk:** binary writes to the mounted project folder can fail/lock. Stage in the sandbox, then copy in; if the target `.docx` is locked (open in Word), say so and ask the user to close it.

## 6. Files

- `scripts/stitch_photos.py` — OneNote PDF -> clean per-page photos.
- `scripts/build_report.py` — config JSON + photos -> Form 331 Word doc.
- `scripts/example_config.json` — worked example (Greenwich on Chevron, B2 pipe failure, 28 May 2026).

## 7. Provenance

Built from the Greenwich on Chevron Basement 2 drainage-failure inspection, 1 June 2026 — the first end-to-end run of OneNote -> Form 331 -> Word + PDF.
