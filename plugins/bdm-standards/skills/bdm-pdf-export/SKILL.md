---
name: bdm-pdf-export
description: Produces a print-faithful PDF from a BDM-templated Word document (.docx) — one that matches what Microsoft Word renders. Use whenever a BDM deliverable (Meeting Memorandum, Variation Form, EOT Determination, Payment Claim Certificate, Monthly Report, Tender Addendum, QS Report, or any document built on a BDM Form template) needs a PDF copy. Trigger on requests like "save as PDF", "export PDF", "PDF the doc", "print to PDF", "send a PDF copy", "PDF version please", or any time the workflow output is Word + PDF (BDM default for new documents). This skill bundles the three preflight fixes that make LibreOffice-generated PDFs match Word's output: font install (Aptos + Carlito), table grid normalisation (tblGrid → cell widths), and row-border cleanup after cloning rows. Without this skill, PDFs drift from Word — wrong fonts, equal-width columns, mid-word email wrapping, inconsistent row dividers.
type: process
template_revision: R1
issued: 2026-05-18
approved_by: James Gill
maintained_by: BDM Standards Agent
parent_skill: bdm-house-style
related_skills: bdm-house-style, bdm-contract-admin-router
---

# BDM PDF Export — Skill

Produces a PDF from a BDM-templated `.docx` that matches Microsoft Word's rendering. The default LibreOffice converter in the sandbox does not match Word out of the box. This skill applies three preflight fixes that close that gap.

## 1. When to use

- Any time the deliverable rule is "Word + PDF" (BDM default for new documents — see `bdm-house-style` § 9)
- Whenever the user says "save as PDF", "export PDF", "PDF copy", "print to PDF", "PDF version"
- After finalising any BDM Form: 232 (Meeting Memorandum), 233 (PC Certificate), 342 (EOT), 343 (Variation), QS Report, Monthly Report, Tender Addendum
- After any project work where rows have been added to a template's tables (action register, attendee list, variation line items, EOT day breakdown)

**Don't use for:**

- Non-BDM documents (generic reports, ad-hoc Word docs that don't use a BDM template) — the default LibreOffice converter is fine
- Documents the user has already exported to PDF themselves via Word

## 2. What the skill does (the three fixes)

Each fix corrects metadata that **Microsoft Word silently overrides** but **LibreOffice respects literally**. The `.docx` itself is unchanged from Word's perspective — the fixes only correct the parts of the file that LibreOffice interprets differently.

### Fix 1 — Install Microsoft fonts (one-time per session)

The sandbox resets between sessions. Carlito (Calibri-compatible) is pre-installed; **Aptos must be downloaded**. BDM templates use Aptos as their primary face — without it, LibreOffice falls back to a serif and the PDF looks completely off-brand.

Run once at the start of any session that will produce a PDF:

```bash
bash scripts/install_fonts.sh
```

The script pulls the Aptos family (regular, bold, italic, display, narrow, black, extrabold) from the `ironveil/ttf-aptos` GitHub mirror, drops them in `~/.local/share/fonts/aptos/`, and refreshes the font cache. Idempotent — safe to re-run.

### Fix 2 — Normalise table grid widths

BDM templates ship with an "auto-equal" `<w:tblGrid>` while the actual cells are proportional. Word uses the cells; LibreOffice uses the grid. Result: equal-width columns in the PDF where Word shows narrow / wide / narrow.

The preflight script rewrites each table's `<w:tblGrid>` to match the first row's cell widths.

### Fix 3 — Reset interior row borders after cloning

When extra rows are inserted into a template table by deep-copying the last existing row, those new rows inherit the table's **closing-edge bottom border** (thick navy, sz=16 colour=0F1721). Original interior rows have a thin grey divider (sz=4 colour=D8D7D3). Result: a visible "darker line" jump partway down the table.

The preflight script sets every data row except the actual last one to the interior border style.

## 3. How to run

**Inputs:**
- Path to the `.docx` file
- Output folder for the `.pdf` (typically same folder as the `.docx`)

### Windows (preferred on BDM workstations)

Use Microsoft Word directly. This is the most faithful renderer and does not need the LibreOffice preflight fixes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pdf_export.ps1 "C:\path\report.docx"
```

The script writes the PDF beside the Word document unless a second output path is supplied. It opens the source read-only, disables background printing, retries transient Word automation rejections up to three times, and cleans up only invisible Word processes created by a failed attempt. It fails if the PDF is missing or empty. If a visible Word session has the document locked, stop and report the lock.

### Linux / headless environments

**Steps:**

```bash
# 1. Install fonts (skip if already done this session)
bash scripts/install_fonts.sh

# 2. Run the three-step preflight in-place on the .docx
python3 scripts/preflight.py "/path/to/document.docx"

# 3. Convert to PDF via LibreOffice
python3 /sessions/<session-id>/mnt/.claude/skills/docx/scripts/office/soffice.py \
    --headless --convert-to pdf "/path/to/document.docx" \
    --outdir "/path/to/output/folder"
```

The preflight script edits the `.docx` in place (the grid normalisation and border reset are non-destructive — Word renders identically before and after). The file is then ready for LibreOffice conversion.

**One-command wrapper:**
```bash
bash scripts/pdf_export.sh "/path/to/document.docx"
```
Runs all three steps in sequence and writes the PDF next to the `.docx`.

## 4. Verification (always do this)

After conversion, eyeball the PDF before delivering:

- Page 1 — does the masthead font look right? (Aptos has a distinctive `g` and `R`.)
- Largest table — are the column proportions correct? (Compare to the Word version.)
- Any cloned-row tables — are all interior dividers the same colour? Only the very last row should have the thick closing edge.
- Page numbers and headers/footers — should match Word.

If anything looks wrong, re-run preflight and report — the script logs which tables and rows it changed.

## 5. Source of these fixes

All three issues were discovered in real BDM work. PCG006 on 160 Pacific Parade (18 May 2026) was the first deliverable where all three were applied end-to-end against Form 232 R2 (Meeting Memorandum).

## 6. Maintenance

When BDM Standards issues a new template revision (e.g. Form 232 R3, Form 343 R2), spot-check the template's metadata using:

```bash
python3 scripts/inspect_template.py "/path/to/Form-XXX_RX.docx"
```

The inspector reports tblGrid vs cell-width mismatches and any other quirks. If a new template fixes the underlying issue at source, this skill's preflight becomes a no-op (safe) rather than necessary.
