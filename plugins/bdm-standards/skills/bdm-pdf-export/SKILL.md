---
name: bdm-pdf-export
description: Produces a print-faithful PDF from a BDM-templated Word document (.docx) — one that matches what Microsoft Word renders. Use whenever a BDM deliverable (Meeting Memorandum, Variation Form, EOT Determination, Progress Certificate, Monthly Report, Tender Addendum, QS Report, Site Inspection Record, or any document built on a BDM Form template) needs a PDF copy. Trigger on requests like "save as PDF", "export PDF", "PDF the doc", "print to PDF", "send a PDF copy", "PDF version please", "signature-ready PDF", or any time the workflow output is Word + PDF (BDM default for new documents). This skill is self-contained — it carries the four preflight fixes that make Linux-generated PDFs match Word's output: Aptos-to-Calibri repack, table grid normalisation, row-border cleanup, and content-control placeholder stripping. Without it, PDFs drift from Word — wrong fonts, equal-width columns, inconsistent row dividers, and "Click or tap here to enter text" printed into issued documents.
metadata:
  type: process
  revision: R2
  issued: 2026-05-18
  revised: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-house-style, bdm-contract-admin-router
  implements: Brand Standard R3 (CN-2026-018)
---

# BDM PDF Export

Produces a PDF from a BDM-templated `.docx` that matches Microsoft Word's rendering. The default Linux converter does not match Word out of the box. This skill applies four preflight fixes that close the gap.

**The preflight is self-contained.** It is inlined in this file — there is nothing to locate, install or keep in sync. R1 referenced four scripts that did not exist, and every workflow that chained into it failed.

The one script this skill does ship is `scripts/pdf_export.ps1`, the Windows/Word path (§ 4). That one is real, and it is the preferred route on a BDM workstation.

## 1. When to use

- Any time the deliverable rule is "Word + PDF" (BDM default for new documents — see `bdm-house-style` § 11)
- Whenever the user says "save as PDF", "export PDF", "PDF copy", "print to PDF", "PDF version"
- After finalising any BDM Form deliverable
- After any project work where rows have been added to a template's tables (action register, attendee list, variation line items, EOT day breakdown)

**Don't use for:**

- Non-BDM documents (generic reports, ad-hoc Word docs that don't use a BDM template)
- Documents the user has already exported to PDF themselves via Word

> **Form numbers are deliberately not listed here.** R1 listed them and disagreed with
> `bdm-contract-admin-router`, `bdm-house-style` and the Forms Contents Index. Until the
> form-number map is settled (pending decision), cite the form by **name**, and take the
> number from `001-Forms Contents Index` at run time. Do not copy a form number from
> another skill.

## 2. The four fixes

Each corrects metadata that **Microsoft Word silently overrides** but the Linux converter respects literally. Word's rendering of the `.docx` is unchanged by any of them.

### Fix 1 — Repack Aptos to Calibri

Brand Standard R3 makes the estate **Calibri-only**. Older templates and any document authored under R2 still carry `w:ascii="Aptos"`. The preflight rewrites every Aptos font reference — in the document body, styles, theme, headers and footers — to Calibri.

> R1 instead **downloaded** the Aptos family from a public GitHub mirror. That step is
> removed: the mirror 404s on every filename, and it existed to satisfy a brand rule R3 has
> since replaced. **Do not reinstate a font download.** Carlito (metric-compatible with
> Calibri) is already present on the converter and is what actually renders.

### Fix 2 — Normalise table grid widths

BDM templates ship with an "auto-equal" `<w:tblGrid>` while the actual cells are proportional. Word uses the cells; the converter uses the grid. Result: equal-width columns where Word shows narrow / wide / narrow. The preflight rewrites each table's `<w:tblGrid>` to match the first row's cell widths.

### Fix 3 — Reset interior row borders after cloning

Rows inserted by deep-copying the last existing row inherit the table's **closing-edge bottom border** (navy, `sz=16`, `#0F1721`). Interior rows should carry the grey-3 hairline (`sz=4`, `#D8D7D3`). Result: a visible "darker line" jump partway down the table. The preflight sets every data row except the genuine last one to the interior style.

### Fix 4 — Strip Word content-control placeholders

Unfilled Word content controls print their prompt text. **110 instances of "Click or tap here to enter text" printed into a live execution pack.** The preflight deletes the whole `<w:sdt>` element.

Three rules, all load-bearing:

- **Detect by the accepted text, never by `showingPlcHdr`.** The flag is unreliable — controls that have been clicked into and left empty no longer carry it but still print the prompt.
- **Leave checkbox content controls alone.** They are legitimate form furniture.
- **Leave `[insert …]` text in Annexure Parts C–H alone.** Those are intentional completion prompts in the execution version, not stray placeholders.

## 3. Before you convert — the Word-side step

If the document has tracked changes, set **Review → Display for Review → No Markup** before exporting. Otherwise the markup prints. This is a display setting, not an accept-all: it does not alter the document, and the tracked changes survive for the reviewer.

If the deliverable is deliberately a tracked draft (see `bdm-house-style` § 13.6), skip this and say so.

## 4. Windows — use Word (preferred on BDM workstations)

Microsoft Word is the most faithful renderer of a BDM template. On a Windows workstation, use it:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/pdf_export.ps1 "C:\path\report.docx"
```

The script writes the PDF beside the Word document unless a second output path is supplied. It opens the source read-only, disables background printing, retries transient Word automation rejections up to three times, and cleans up only invisible Word processes created by a failed attempt. It fails if the PDF is missing or empty. If a visible Word session has the document locked, stop and report the lock.

**Which fixes still apply on the Windows path?**

| Fix | Needed on Windows? |
|---|---|
| 1 — Aptos → Calibri | **Yes.** This is a *brand* fix, not a rendering fix. Word will happily render Aptos; Brand Standard R3 says it must not. |
| 2 — table grid widths | No. Word uses the cell widths already. |
| 3 — cloned row borders | No. Word resolves these correctly. |
| 4 — content-control placeholders | **Yes.** Word prints unfilled control prompts. This is where the 110 "Click or tap here to enter text" came from — on Word, not on the converter. |

So on Windows: run the preflight (§ 5) for fixes 1 and 4, set **No Markup** (§ 3), then export with the PowerShell script. Fixes 2 and 3 are no-ops there and cost nothing.

---

## 5. Run the preflight

Save as `bdm_preflight.py` in a scratch directory and run it against the `.docx`. It edits in place.

```python
#!/usr/bin/env python3
"""BDM PDF preflight — four fixes. Edits a .docx in place."""
import re, shutil, sys, zipfile
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
def q(t): return "{%s}%s" % (W, t)

PLACEHOLDER_TEXT = re.compile(
    r"^\s*(click or tap here to enter text|click here to enter text|"
    r"choose an item|click or tap to enter a date|enter text)\.?\s*$", re.I)

INTERIOR = {"val": "single", "sz": "4",  "space": "0", "color": "D8D7D3"}
CLOSING  = {"val": "single", "sz": "16", "space": "0", "color": "0F1721"}

def fix_fonts(root):
    """Fix 1 — every Aptos reference becomes Calibri."""
    n = 0
    for el in root.iter():
        for a, v in list(el.attrib.items()):
            if isinstance(v, str) and "aptos" in v.lower():
                el.set(a, re.sub(r"Aptos[\w ]*", "Calibri", v))
                n += 1
    return n

def fix_grids(root):
    """Fix 2 — tblGrid follows the first row's actual cell widths."""
    n = 0
    for tbl in root.iter(q("tbl")):
        grid = tbl.find(q("tblGrid"))
        row = tbl.find(q("tr"))
        if grid is None or row is None:
            continue
        widths = []
        for tc in row.findall(q("tc")):
            tcW = tc.find(q("tcPr") + "/" + q("tcW"))
            if tcW is None or tcW.get(q("w")) is None:
                widths = []
                break
            widths.append(tcW.get(q("w")))
        if not widths:
            continue
        cols = grid.findall(q("gridCol"))
        if len(cols) != len(widths):
            continue
        for col, wdt in zip(cols, widths):
            if col.get(q("w")) != wdt:
                col.set(q("w"), wdt)
                n += 1
    return n

def fix_borders(root):
    """Fix 3 — only the genuine last row keeps the closing edge."""
    n = 0
    for tbl in root.iter(q("tbl")):
        rows = tbl.findall(q("tr"))
        for i, tr in enumerate(rows):
            style = CLOSING if i == len(rows) - 1 else INTERIOR
            for tc in tr.findall(q("tc")):
                tcPr = tc.find(q("tcPr"))
                if tcPr is None:
                    continue
                borders = tcPr.find(q("tcBorders"))
                if borders is None:
                    continue
                bottom = borders.find(q("bottom"))
                if bottom is None:
                    continue
                if any(bottom.get(q(k)) != v for k, v in style.items()):
                    for k, v in style.items():
                        bottom.set(q(k), v)
                    n += 1
    return n

def fix_placeholders(root):
    """Fix 4 — delete unfilled content controls. Detect by text, not showingPlcHdr."""
    n = 0
    for sdt in list(root.iter(q("sdt"))):
        pr = sdt.find(q("sdtPr"))
        # leave checkbox controls alone
        if pr is not None and any("checkbox" in etree.QName(c).localname.lower()
                                  for c in pr.iter() if isinstance(c.tag, str)):
            continue
        content = sdt.find(q("sdtContent"))
        if content is None:
            continue
        text = "".join(t.text or "" for t in content.iter(q("t")))
        # leave deliberate completion prompts alone (Annexure Parts C-H)
        if text.strip().lower().startswith("[insert"):
            continue
        if not PLACEHOLDER_TEXT.match(text):
            continue
        parent = sdt.getparent()
        if parent is not None:
            parent.remove(sdt)
            n += 1
    return n

PARTS = re.compile(r"^word/(document|styles|theme/theme\d+|(header|footer)\d+)\.xml$")

def main(path):
    shutil.copy2(path, path + ".preflight.bak")
    zin = zipfile.ZipFile(path)
    items = zin.infolist()
    blobs = {i.filename: zin.read(i.filename) for i in items}
    zin.close()
    tally = {"fonts": 0, "grids": 0, "borders": 0, "placeholders": 0}
    for name in list(blobs):
        if not PARTS.match(name):
            continue
        root = etree.fromstring(blobs[name])
        tally["fonts"] += fix_fonts(root)
        if name == "word/document.xml":
            tally["grids"] += fix_grids(root)
            tally["borders"] += fix_borders(root)
            tally["placeholders"] += fix_placeholders(root)
        blobs[name] = etree.tostring(root, xml_declaration=True,
                                     encoding="UTF-8", standalone=True)
    # [Content_Types].xml must be first in the archive
    order = ["[Content_Types].xml"] + [i.filename for i in items
                                       if i.filename != "[Content_Types].xml"]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in order:
            zout.writestr(name, blobs[name])
    print("preflight:", ", ".join("%s=%d" % kv for kv in tally.items()))
    return tally

if __name__ == "__main__":
    main(sys.argv[1])
```

Requires `lxml` (`pip install lxml --break-system-packages` if absent). A `.preflight.bak` is written next to the file before anything is changed.

## 6. Convert — Linux / headless

Resolve the converter at run time — **never hardcode a session path.** R1 hardcoded `/sessions/<session-id>/…`, which is different on every run and every machine.

```bash
SOFFICE=$(find / -path "*/skills/docx/scripts/office/soffice.py" 2>/dev/null | head -1)
[ -z "$SOFFICE" ] && SOFFICE=$(command -v soffice || command -v libreoffice)

python3 "$SOFFICE" --headless --convert-to pdf "/path/to/document.docx" \
    --outdir "/path/to/output/folder"
```

If neither resolves, say so and stop. Do not fall back to a different converter without saying which one produced the file.

## 7. Verify — always

Render the pages to images and actually look at them:

```bash
pdftoppm -png -r 70 "/path/to/document.pdf" /tmp/check
```

Then check:

- **Fonts** — Calibri (or Carlito) throughout. No serif fallback, no Aptos.
- **Tables** — column proportions match the Word version.
- **Cloned rows** — every interior divider the same grey. Only the very last row carries the thick navy closing edge.
- **Placeholders** — no "Click or tap here to enter text" anywhere. Search the extracted text, don't just eyeball it.
- **Headers, footers, page numbers** — match Word.
- **Margins** — 2.2 cm all round per `bdm-house-style` § 4.

If anything is wrong, re-run the preflight from the `.bak` and report which fix did not take.

## 8. Signature-ready output

A PDF is **not** signature-ready until **both** of these are true:

1. The acting PM's signature image is embedded, **2.25 cm** wide, resolved per `bdm-house-style` § 9.3 — `<PM home>/<INITIALS>_signature.png`. If the acting PM has no signature on file, flag it and ask. Never substitute another person's signature.
2. The literal word **"Date"** in the sign-off block is **replaced** with the actual date in `DD MMM YYYY` form, Brisbane time.

One without the other is a failed deliverable. A signed document still reading "Date" goes back for rework, and it has happened.

## 9. Maintenance

When BDM Standards issues a new template revision, run the preflight against it and read the tally. A template that reports `grids=0, borders=0, placeholders=0` has fixed the underlying issues at source, and the preflight is a safe no-op for it. `fonts=0` means the template is already on R3 Calibri.

## 10. Revision control

| Rev | Date | Editor | Change |
|---|---|---|---|
| R1 | 2026-05-18 | James Gill | Initial issue. Three fixes via four companion scripts. |
| R2 | 2026-08-18 | James Gill | Rewritten self-contained — the four referenced scripts never existed and every dependent skill failed with them. Preflight inlined. Aptos download removed (dead mirror, superseded by Brand Standard R3); Fix 1 is now an Aptos-to-Calibri repack. Added Fix 4 (content-control placeholder stripping) and the No Markup step. Converter path resolved at run time instead of a hardcoded session path. Added `pdftoppm` render verification and the signature-ready definition. Retained the Windows/Word export path added 17 Aug and mapped which fixes apply to it. Form numbers removed pending the form-number decision. |
