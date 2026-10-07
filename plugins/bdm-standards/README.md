# BDM Standards — v2.4.1

The foundation plugin. Install this first — the other BDM plugins assume it.

- **`bdm-house-style` (R3)** — the always-on rulebook. Palette, typography, page geometry, logo, layout ("Charcoal · Navy Rule"), table specification, numerical conventions, template resolution, QA checklist and the BDM working rules. A rulebook, not a template: it produces answers and corrections, not files.
- **`bdm-pdf-export` (R2)** — **self-contained.** Produces a PDF from a BDM-templated `.docx` that matches Microsoft Word. Carries the four preflight fixes inline: Aptos→Calibri repack, `tblGrid` normalisation, cloned-row border reset, and content-control placeholder stripping. Plus the signature-ready definition.
- **`bdm-project-sandbox-setup` (R2)** — creates `00_ai_sandbox`, backfills the 17-section project summary, and builds `AI_Context\` (the project documents except drawings as markdown, scans OCR'd), with a monthly stale-file audit.
- **`datum-markup`** — writes editable markups, measurements and priced BOQ takeoffs directly into a PDF for Datum, then bakes them with Datum's own Save so they show in Adobe, Chrome and Bluebeam too.

Templates live in SharePoint, not here. See `bdm-house-style` § 8.

## What changed in 2.4.0

- **`bdm-project-sandbox-setup` R2: AI_Context.** Implements CLAUDE.md R5 §8. Converts a project's static documents (except drawings) to markdown in `00_ai_sandbox\AI_Context\`, one file per source with a source/modified/size header so stale copies are detectable; excludes drawings, live registers, superseded copies and duplicates; OCRs scanned PDFs with the built-in Windows OCR (rotation-aware); writes `INDEX.md` with the contract, spec and approvals first; adds the §16 pointer to the summary. New `audit_ai_context.mjs` is the AI_Context part of the monthly audit (stale, removed, new; `--refresh` brings projects current). Needs Node 18+ and a one-off per-user install of pdfjs-dist, exceljs and jszip outside the synced library (see `scripts/common.mjs`).

## What changed in 2.3.0

- **`datum-markup` now bakes its output.** Previously its PDFs showed markups only in Datum — Adobe, Chrome and Bluebeam showed a clean drawing until someone opened the file in Datum and pressed Save. New `bake()` (in `datum_markup.py`, driving `scripts/datum-bake.js`) opens the file in the real Datum app in headless Chromium and runs Datum's own Save, then checks the result before replacing the file. Needs Node 18+ and `npm install playwright` (plus `npx playwright install chromium` if no Chrome/Edge). If baking isn't possible the file is left as written and the skill says so on delivery.
- **`datum-markup` brought up to Datum v3.44.** The plugin copy had fallen behind the working copy: full symbol catalogue (`references/symbols.md`, `symbol_at`, `symbol_true_size` for plant at true size), current annotation reference, and the updated workflow.

## What changed in 2.2.0

- **New skill `bdm-project-sandbox-setup`.** Gets projects without a sandbox or summary onto the CLAUDE.md §13 standard so every other skill has a live project state to read. Bundles two read-only PowerShell helpers: `scan_project.ps1` (sandbox status sweep and per-project inventory) and `read_msg.ps1` (reads saved Outlook `.msg` emails).

## What changed in 2.0.0

**Brand Standard R3 (CN-2026-018) is now implemented.** The estate is **Calibri-only** — Aptos and Arial are purged. If a document, template or workflow still specifies Aptos, it is following R2 and is out of date.

Also in this release:

- Page geometry added — A4 portrait, **2.2 cm margins**, body Calibri 10 pt navy, 1.25 line.
- Header rule is **2 pt navy estate-wide**; the 1 pt gold rule on the QS forms is deprecated.
- New table specification — `#F4F4F1` header, navy 9 pt bold caps, 0.5 pt navy top and bottom only, numbers right-aligned.
- `#EAF2EA` and `#1B1B1B` prohibited; Word's default heading blues must be overridden in the style.
- **`bdm-pdf-export` actually runs.** R1 called four scripts that did not exist, and three other skills failed with it. Everything is inline now.
- The OneDrive `cat`+`sync` write method is **removed** — it corrupted files on four projects. Use the fsync byte-write in `bdm-house-style` § 8.6.
- `PROJECT.md` is retired in favour of `Project_Summary_*.md`.
- New § 9 **Resolving the current user** — these skills run for every BDM PM. No personal paths, names, signatures or email addresses in any skill file.

## Known open items

Two things in `bdm-house-style` are **flagged pending a decision** and marked as such in the file:

- **§ 7 filename convention** — the master pattern does not match documented practice.
- **§ 8.2 Working Copy subfolder names** — mixed naming, and three folders are missing.

Until settled, follow the naming already in use on the project folder and flag the inconsistency.

The **form-number map** (which form is 342 / 343 / 344, and whether the progress certificate is 335 or 233) is also unsettled. Form numbers have been **removed** from the skills rather than guessed. Cite forms by name and take the number from `001-Forms Contents Index` at run time.
