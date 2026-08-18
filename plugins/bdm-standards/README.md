# BDM Standards — v2.0.0

The foundation plugin. Install this first — the other BDM plugins assume it.

- **`bdm-house-style` (R3)** — the always-on rulebook. Palette, typography, page geometry, logo, layout ("Charcoal · Navy Rule"), table specification, numerical conventions, template resolution, QA checklist and the BDM working rules. A rulebook, not a template: it produces answers and corrections, not files.
- **`bdm-pdf-export` (R2)** — **self-contained.** Produces a PDF from a BDM-templated `.docx` that matches Microsoft Word. Carries the four preflight fixes inline: Aptos→Calibri repack, `tblGrid` normalisation, cloned-row border reset, and content-control placeholder stripping. Plus the signature-ready definition.
- **`datum-markup`** — writes editable markups, measurements and priced BOQ takeoffs directly into a PDF for Datum.

Templates live in SharePoint, not here. See `bdm-house-style` § 8.

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
