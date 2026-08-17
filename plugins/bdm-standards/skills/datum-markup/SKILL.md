---
name: datum-markup
description: >
  Write editable markups, measurements and priced BOQ takeoffs directly into a
  PDF for Datum, BDM's PDF markup tool (the Bluebeam replacement). Use this
  skill whenever the task involves marking up a drawing or document for Datum,
  redlining a PDF, adding review clouds/stamps/notes, measuring a drawing,
  doing a quantity takeoff, or producing a bill of quantities (BOQ) / estimate
  on a PDF — even if the user only says "mark this up", "cloud the changes",
  "measure this plan", "do a takeoff", or "price this drawing". The output is a
  normal PDF that opens in Datum with every markup fully live and editable, and
  every measured quantity computed by Datum itself. No access to the Datum app
  is needed to produce the file.
---

# Datum Markup — write editable markups straight into a PDF

Datum is a single-file, in-browser PDF markup and estimating tool
(Bluebeam-style). Live app: https://jamesbdm.github.io/bdm-pdf-tool/BDM-PDF-Markup-Tool.html

The whole trick: Datum stores its editable project as **base64 JSON in the
PDF's Info dictionary** under the key `/BDMMarkupData`. Any agent that can
run Python (or Node) can therefore produce a "Datum-saved" PDF without ever
opening the app. When a person opens the file in Datum, every cloud, note,
measurement and BOQ line is restored fully editable — exactly as if a human
had drawn it.

## Workflow

1. **Inspect the source PDF first.** Get each page's width/height in points
   and its `/Rotate` value (use pypdf). You cannot place markups sensibly
   without knowing the page size. If the drawing has a scale bar or title
   block ("SCALE 1:100 @ A3"), note the scale for calibration.
2. **Plan positions in Datum page space.** Coordinates are PDF points
   (1/72 inch) at 1:1 zoom, **origin at the page's TOP-LEFT, y increasing
   DOWNWARD**. This is the #1 source of errors: PDF-native coordinates are
   bottom-left-up, so convert with `y_datum = page_height − y_pdf`. If you
   render the page to an image to find features, image pixels map linearly:
   `pt = pixel × (page_width_pt / image_width_px)` — and image y is already
   top-down, so no flip is needed from images.
3. **Build the project payload** with `scripts/datum_markup.py` (bundled —
   read its docstring; it has helpers for every markup type, calibration,
   and BOQ items). For property-level detail or types the helpers don't
   cover, read `references/annotation-types.md`.
4. **Embed and save** with `embed(source_pdf, project, output_pdf)`. The
   source must be the clean original PDF; the output is a byte-for-byte
   normal PDF plus three Info-dict keys.
5. **Self-verify before delivering** (see checklist below).

## Quick start

```python
from datum_markup import DatumProject, embed   # scripts/datum_markup.py

p = DatumProject("Site Plan - MARKED UP.pdf")

# Review-style markups
p.cloud(page=0, x1=100, y1=200, x2=400, y2=300)          # revision cloud
p.text(0, 100, 310, "Confirm setback with surveyor", bold=True)
p.arrow(0, 500, 400, 420, 320)                            # head on 2nd point
p.stamp(0, 700, 80, "FOR REVIEW")                         # centre-anchored
p.highlight(0, 90, 780, 560, 800)
p.rectangle(0, 80, 500, 560, 700, dashed=True, subject="Signatures")

# Measured takeoff + priced BOQ (needs calibration)
p.calibrate_all_pages(scale=50, num_pages=1)              # sheet is 1:50 true size
walls = p.boq_item("External walls — 190 blockwork (2.7m)", "vertical",
                   trade="Masonry", rate=285, factor=2700, color="#E5432E")
slab  = p.boq_item("Floor slab — 100 thk", "area", trade="Concrete",
                   rate=118, color="#4F8EF7")
doors = p.boq_item("Doors — flush panel", "count", trade="Openings",
                   rate=620, color="#9333EA")
p.boq_manual("Site establishment", 1, "item", 2500, trade="Prelims")

p.measure(0, 180, 224, 577, 224, item=walls)              # a wall line
p.area(0, [(180, 224), (577, 224), (577, 462), (180, 462)], item=slab)
p.count(0, 300, 350, "Doors", item=doors)                 # auto-numbers 1, 2, …

embed("source.pdf", p, "Site Plan - MARKED UP.pdf")
```

Requires only `pypdf`. A Node.js equivalent using pdf-lib is in
`scripts/datum-markup-node.js` if Python isn't available.

## How quantities work (the important mental model)

Datum computes every measured quantity **live from shape geometry ×
calibration** — quantities are never stored. So the agent's only jobs are
(a) draw shapes whose geometry is truly to scale and (b) set the calibration
correctly. For a sheet printed at true size at 1:N, calibration is
`pixelsPerMm = (72 / 25.4) / N`. A 7 m wall on a 1:50 sheet is therefore a
line of length 7000 × 0.0566929 ≈ 396.9 pt. If the user later drags a line's
endpoint in Datum, the BOQ updates — that's expected and desirable.

Item types: `length` (m), `area` (m²), `count` (no.), `vertical`
(m² = length × factor mm height — walls), `volume` (m³ = area × factor mm
depth — slabs, footings). `factor` is millimetres. Manual lines (prelims,
allowances) carry a typed `manualQty` instead of shapes.

## Self-verification checklist (do this every time)

Without Datum available, verify programmatically before delivering:

- Re-open the output with pypdf: `/BDMMarkupData` present in `reader.metadata`;
  base64-decodes; JSON parses; `version == 4`.
- Every annotation: unique `id`, integer `page` within range, all point
  coordinates inside the page box (0 ≤ x ≤ width, 0 ≤ y ≤ height).
- Every `takeoffItemId` on a shape matches an existing item `id`; shape type
  is compatible with the item (`measure` → length/vertical, `area` →
  area/volume, `count` → count).
- If any measured items exist: `pageCalibrations` covers every page that has
  measured shapes (keys are STRINGS: `"0"`, `"1"`, …).
- Hand-compute one expected quantity (length ÷ pixelsPerMm ÷ 1000 = metres)
  and state it to the user so they can spot-check the BOQ in Datum.
- The page count and page content of the output must equal the source —
  embedding only adds metadata, never alters pages.

## Things that bite

- **Top-left origin.** Repeated because it is the failure mode: flip y when
  converting from PDF-native coordinates.
- Markups are visible **only in Datum** until the user re-saves there
  (`BDMBakedOverlay = '0'`); Acrobat/browsers show the clean document. Say
  this when delivering, so nobody thinks the file is blank.
- `page` is 0-based. `pageCalibrations` keys are strings.
- Stamps anchor at their CENTRE point; text anchors at its TOP-LEFT.
- On text: `boxFill` must be a colour string (e.g. `'#FFFFFF'`), never a
  boolean. On shapes the fill is `fillColor`. Don't cross them.
- `opacity` is 0–100 with 100 = solid (Datum's UI shows "transparency",
  which is the inverse — ignore that, store opacity).
- Password-protected PDFs: decrypt first (pypdf `reader.decrypt(pw)`), embed
  into the decrypted bytes.
- Don't invent an eighth annotation type. The supported set for writing is:
  cloud, text, rectangle, highlight, arrow, stamp, measure, area, count.
  (Datum itself has more — callouts, tables, symbols, polylines — but their
  formats are fiddlier; read `references/annotation-types.md` before
  attempting one.)

## Delivering

Name the output `<original name> - MARKED UP.pdf` (or the user's requested
name), state what was placed where, state the one hand-computed check
quantity, and remind the user: open it in Datum — markups are editable; the
BOQ lives under the **Workbook** button in the top bar; re-saving from Datum
bakes markups in for other PDF viewers.
