# BDM Standards

The foundation plugin. Install this first — the other BDM plugins assume it.

- **`bdm-house-style`** — the always-on rulebook. Palette, typography, logo, layout ("Charcoal · Navy Rule"), numerical conventions, filename convention, template locations, QA checklist and BDM working rules. This is a rulebook, not a template: it produces answers and corrections, not files.
- **`bdm-pdf-export`** — produces a PDF from a BDM-templated `.docx` that matches Microsoft Word. Applies the three preflight fixes (Aptos font install, tblGrid normalisation, row border cleanup) that the default converter misses.
- **`datum-markup`** — writes editable markups, measurements and priced BOQ takeoffs directly into a PDF for Datum.

Templates live in SharePoint, not here. See `bdm-house-style` § 7.
