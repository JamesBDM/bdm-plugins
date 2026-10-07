---
name: datum-markup
description: >
  Write editable markups, measurements, priced BOQ takeoffs and full
  presentation layouts directly into a PDF for Datum, BDM's PDF markup tool
  (the Bluebeam replacement). Use this skill whenever the task involves
  marking up a drawing or document for Datum, redlining a PDF, adding review
  clouds/stamps/notes, measuring a drawing, doing a quantity takeoff,
  producing a bill of quantities (BOQ) / estimate on a PDF, or laying out a
  report, summary sheet or presentation page, or placing symbols on a plan —
  including a construction management plan / site establishment / traffic
  management layout (tower / mobile / Franna cranes and concrete pumps at
  true size with reach charts and weathervane zones, delivery and concrete
  trucks with turning circles, builder's hoists, scissor and boom lift EWPs, scaffold runs and true-size site sheds / containers, bins, hoarding, traffic
  control) — even if the user only says
  "mark this up", "cloud the changes", "measure this plan", "do a takeoff",
  "price this drawing", "do a CMP layout", or "make this look presentable". The output is a
  normal PDF that opens in Datum with every markup fully live and editable,
  and every measured quantity computed by Datum itself, then baked by
  Datum's own Save so the markups also show in Adobe, Chrome and Bluebeam.
  No access to the Datum app UI is needed to produce the file.
---

# Datum Markup — write editable markups straight into a PDF

Datum is a single-file, in-browser PDF markup and estimating tool
(Bluebeam-style). Live app: https://jamesbdm.github.io/bdm-pdf-tool/BDM-PDF-Markup-Tool.html

The whole trick: Datum stores its editable project as **base64 JSON in the
PDF's Info dictionary** under the key `/BDMMarkupData`. Any agent that can
run Python (or Node) can therefore produce a "Datum-saved" PDF without ever
opening the app. When a person opens the file in Datum, every cloud, note,
measurement, table and card is restored fully editable — exactly as if a
human had drawn it.

**Targets Datum v3.22.** If the reader is on an older build, the
presentation markups render as dashed placeholder boxes — check with them
before using this skill's presentation half on an unknown install.

## Workflow

1. **Inspect the source PDF first.** Get each page's width/height and
   `/Rotate` — `datum_markup.page_sizes(path)` returns the as-viewed sizes
   with rotation already applied. You cannot place markups sensibly without
   them. If the drawing has a scale bar or title block ("SCALE 1:100 @ A3"),
   note the scale for calibration.
2. **Plan positions in Datum page space.** PDF points (1/72 inch) at 1:1,
   **origin at the page's TOP-LEFT, y increasing DOWNWARD**. This is the #1
   source of errors: PDF-native coordinates are bottom-left-up, so convert
   with `y_datum = page_height − y_pdf`. Rendered-image pixels are already
   top-down: `pt = pixel × (page_width_pt / image_width_px)`.
3. **Use the grid for anything laid out rather than pointed at.** `p.grid()`
   gives a 12-column page grid; `g.cell(col, span, top, height)` and
   `g.band(top, height)` return boxes that line up. Eyeballed coordinates are
   the main reason generated pages look amateur.
4. **Build the payload** with `scripts/datum_markup.py`. For property-level
   detail or anything the helpers don't cover, read
   `references/annotation-types.md`.
5. **Verify, then embed.** Call `p.verify(pages=page_sizes(src))` — it raises
   on off-page coordinates, unknown types, orphaned takeoff links and missing
   calibration. Then `embed(source_pdf, p, output_pdf)`.
6. **Bake, so the markups show outside Datum.** `embed()` only writes the
   editable project — Adobe, Chrome and Bluebeam show the clean drawing.
   `ok, msg = bake(output_pdf)` opens the file in the real Datum app
   (headless Chromium) and runs Datum's own Save, exactly as if someone had
   pressed Ctrl+S: markups painted onto every page for every viewer, and the
   file still reopens fully editable in Datum. Do this every time the file is
   going to anyone. See **Baking** below for setup and what to do if it fails.

## Quick start — review markup

```python
from datum_markup import DatumProject, embed, bake, page_sizes

sizes = page_sizes("source.pdf")
w, h = sizes[0]
p = DatumProject("Site Plan - MARKED UP.pdf", page_w=w, page_h=h)

p.cloud(page=0, x1=100, y1=200, x2=400, y2=300)
p.callout(0, anchor=(250, 250), text_pos=(430, 210),
          text="Confirm setback with surveyor", preset="callout-note")
p.stamp(0, 700, 80, "FOR REVIEW")
p.symbol_at(0, 80, 80, "g-north")          # true proportions, default size
p.rectangle(0, 80, 500, 560, 700, dashed=True, subject="Signatures")

p.verify(pages=sizes)
embed("source.pdf", p, "Site Plan - MARKED UP.pdf")
ok, msg = bake("Site Plan - MARKED UP.pdf")   # visible in Adobe too
print(msg)
```

## Quick start — presentation page

```python
from datum_markup import DatumProject, embed, page_sizes

sizes = page_sizes("blank-a4.pdf"); w, h = sizes[0]
p = DatumProject("PCG Summary.pdf", page_w=w, page_h=h)
g = p.grid()                       # 12 columns, 42pt margins

p.banner(*g.band(top=40, height=54), title="Trade Package Status",
         subtitle="PCG 14 — 22 August 2026")

for box, (val, cap, d, dir_) in zip(
        g.row(3, top=112, height=86),
        [("$4.21M", "Certified to date", "+8.2%", "up"),
         ("12",     "Open variations",   "-3",    "down"),
         ("41 d",   "Float remaining",   None,    "flat")]):
    p.kpi(*box, value=val, caption=cap, delta=d, direction=dir_, shadow=True)

p.chevron(*g.band(top=214, height=32),
          stages=["Design", "Tender", "Construction", "DLP"], current=2)

p.timeline(*g.band(top=262, height=52), milestones=[
    {"label": "Award",   "date": "12 Mar 26", "state": "done"},
    {"label": "Lock-up", "date": "19 Sep 26", "state": "current"},
    {"label": "PC",      "date": "30 Nov 26", "state": "todo"}])

p.divider(*g.band(top=326, height=18), text="Findings")

p.quote(*g.cell(0, 7, top=352, height=76),
        text="Facade procurement is on the critical path and needs a "
             "decision this week to hold the lock-up date.",
        attribution="Superintendent")
p.progress(*g.cell(7, 5, top=352, height=18), value=65)
p.chip(*g.cell(7, 2, top=382, height=20), text="On track", preset="chip-ok")

p.table(page=0, x=g.margin, y=450,
        columns=[{"label": "Package", "align": "left"},
                 {"label": "Status", "type": "colour", "align": "center"},
                 {"label": "Value", "align": "right"}],
        rows=[[{"text": "Structure"}, {"color": "#16A34A", "text": "On track"}, {"text": "$1,240,000"}],
              [{"text": "Facade"},    {"color": "#F59E0B", "text": "At risk"},  {"text": "$860,000"}]],
        title="Package summary")

p.verify(pages=sizes)
embed("blank-a4.pdf", p, "PCG Summary.pdf")
```

## Quick start — measured takeoff + priced BOQ

```python
p.calibrate_all_pages(scale=50, num_pages=1)          # sheet is 1:50 true size
walls = p.boq_item("External walls — 190 blockwork (2.7m)", "vertical",
                   trade="Masonry", rate=285, factor=2700, color="#E5432E")
slab  = p.boq_item("Floor slab — 100 thk", "area", trade="Concrete", rate=118)
doors = p.boq_item("Doors — flush panel", "count", trade="Openings", rate=620)
p.boq_manual("Site establishment", 1, "item", 2500, trade="Prelims")

p.measure(0, 180, 224, 577, 224, item=walls)
p.area(0, [(180, 224), (577, 224), (577, 462), (180, 462)], item=slab)
p.count(0, 300, 350, "Doors", item=doors)
p.legend(0, x=700, y=520, mode="summary")             # live BOQ table on the sheet
```

## What you can write

**Review:** cloud, text, rectangle, ellipse, line, polygon, polyline, arrow,
highlight, callout, stamp, tick, symbol, image, cutcontent (white-out),
dimension, pen, signature.

**Symbols:** 311 in 19 categories — drafting markers, doors/windows/stairs,
furniture, kitchen, sanitary, landscape, electrical, mechanical, fire, civil,
and a full **construction management plan** set (schematic cranes, pumps,
hoists, site sheds, bins, hoarding and fencing, erosion and sediment control,
traffic control devices and signs). Read `references/symbols.md` for the ids
before placing any, and place with `symbol_at()` so each lands at its true
proportions.

**True-size plant and site establishment (v3.37–v3.42):** concrete boom pumps (`cp-*`), trucks and
vehicles (`tv-*` — agitators, rigid trucks, tippers, semi, truck & dog,
B-double) and cranes (`cr-*` — flat-top, hammerhead, luffing and
self-erecting tower cranes, Frannas, all-terrain mobiles) and access
(`ac-*` — builder's hoists, scissor lifts, vertical mast, knuckle and
telescopic boom lifts, spider lift), scaffold (`sf-*` — runs with editable
bays, stair tower, loading bay, mobile towers) and site sheds (`ss-*` —
portable offices, crib, toilets, change rooms, portaloos, containers) carry a real
footprint. Calibrate the page, then place with `symbol_true_size()` so the
machine occupies its real size on the drawing, and add the overlays a CMP
needs:

```python
p.calibrate_page(0, 200)
p.symbol_true_size(0, 300, 260, "cr-tc-luff-45", rotation=-30, jib=40,
                   show_vane=True,                        # weathervane zone
                   rings=[(15, "18 t"), (25, "11 t"), (40, "5.6 t")])
p.symbol_true_size(0, 520, 300, "cr-mc-100", show_reach=True, show_vane=True)
p.symbol_true_size(0, 420, 420, "cp-putz-36", show_reach=True)
p.symbol_true_size(0, 470, 480, "tv-agi-8", rotation=90, show_turn=True)
p.symbol_true_size(0, 200, 400, "ac-hoist-twin")                # base enclosure + cages
p.symbol_true_size(0, 240, 470, "ac-boom-t60", show_reach=True) # outreach ring
p.symbol_true_size(0, 400, 120, "sf-run-1200", bays=12, bay_length=2.4)  # 28.8 m run
p.symbol_true_size(0, 650, 520, "ss-office-12")                 # 12 × 3.3 m portable
```

At rotation 0 the cab / boom / jib points to +x (rotation is degrees
clockwise); a tower crane's box is its base and the jib is drawn out along
+x, so rotate it to slew. Default crane and pump rings are typical for the
class, not a load chart — pass the actual crane's radii and capacities in
`rings` when the job has them. The full option table is in
`references/symbols.md`.

**Data + layout:** table (title bar, header row, per-cell fill, colour-swatch
columns), legend (auto-generated BOQ key).

**Presentation (v3.22):** chip, badge, divider, banner, quote, kpi, chevron,
timeline, bracket, progress, chart (bar / line / donut / pie).

**Measured:** measure, area, count — plus `boq_item` / `boq_manual`.

Full property lists are in `references/annotation-types.md`; every symbol id
and its default size is in `references/symbols.md`.

## Making it look designed, not just populated

- **Use presets, not hex codes.** `preset="chip-risk"`, `preset="card"`,
  `preset="heading"`. They carry BDM's palette, radius and shadow, and one
  edit restyles everything. Explicit properties still override them.
- **Use the grid.** `g.cell()` / `g.band()` / `g.row()`. Consistent margins
  and gutters do more for how a page reads than any single shape.
- **Prefer one composed type to four primitives.** A `kpi` beats
  rectangle + text + text + rectangle: it lays itself out, and the reader
  edits one object.
- **Group anything you do compose.** `p.group(bg, label, value)` — without a
  group the reader drags four things to move one card.
- **Round the corners and lift the cards.** `radius=10`, `shadow=True`.
  `thickness=0` gives a borderless fill-only panel; `strokeSide="l"` gives an
  accent-bar card.
- **Let text breathe.** `pad=8` and `align`/`valign` on text boxes. Cramped,
  top-left-jammed text is the main tell of a generated page.
- **Leave margin at timeline ends** — milestone labels centre on their dot
  and will overhang the box otherwise.

## How quantities work (the important mental model)

Datum computes every measured quantity **live from shape geometry ×
calibration** — quantities are never stored. So your only jobs are (a) draw
shapes whose geometry is truly to scale and (b) set the calibration
correctly. For a sheet printed at true size at 1:N, calibration is
`pixelsPerMm = (72 / 25.4) / N`. A 7 m wall on a 1:50 sheet is therefore a
line of length 7000 × 0.0566929 ≈ 396.9 pt. If the reader later drags a
line's endpoint in Datum, the BOQ updates — that's expected and desirable.

Item types: `length` (m), `area` (m²), `count` (no.), `vertical`
(m² = length × factor mm height — walls), `volume` (m³ = area × factor mm
depth — slabs, footings). `factor` is millimetres. Manual lines (prelims,
allowances) carry a typed `manualQty` instead of shapes.

## Self-verification (do this every time)

`p.verify(pages=page_sizes(src))` raises on the failures that are invisible
rather than obviously wrong: off-page coordinates, unknown annotation types,
duplicate ids, box types without exactly two points, `takeoffItemId` with no
matching item, shape/item type mismatches, measured shapes on an uncalibrated
page, and `boxFill: true` (must be a colour string).

Then, after embedding:

- Re-open the output with pypdf: `/BDMMarkupData` present in
  `reader.metadata`; base64-decodes; JSON parses; `version == 4`.
- Page count and page content equal the source — embedding only adds
  metadata, never alters pages.
- Hand-compute one expected quantity (length ÷ pixelsPerMm ÷ 1000 = metres)
  and state it to the user so they can spot-check the BOQ in Datum.

## Baking

`bake()` drives `scripts/datum-bake.js`, which loads Datum, opens the PDF,
calls Datum's `saveProject()`, and checks the result with Datum's own reader
(markups painted in, clean original embedded, same markup count) before it
replaces the file. Same renderer as the app, so nothing drifts when Datum
changes.

Setup, once per machine or sandbox (Node 18+):

```bash
npm install playwright
npx playwright install chromium   # skip if Chrome or Edge is installed
```

Run `npm install` in the `scripts/` folder or the working directory —
either is found. CLI form: `node scripts/datum-bake.js file.pdf [-o out.pdf]`.

- **The app** comes from the live site by default
  (`https://jamesbdm.github.io/bdm-pdf-tool/BDM-PDF-Markup-Tool.html`), so it
  needs internet. Offline, pass `app="path/to/BDM-PDF-Markup-Tool.html"` (or
  set `$DATUM_APP`) and `npm install pdf-lib@1.17.1 pdfjs-dist@3.11.174` so
  the libraries are served locally too.
- **Browser**, first that works: `$CHROMIUM_PATH`, Playwright's Chromium,
  installed Chrome, installed Edge.
- **Already baked** (it was saved from Datum) → reports so and changes
  nothing. Re-baking is always safe; Datum renders from the clean copy.
- **If it fails** (no node, no browser, no internet, or a set too large for
  the browser to hold twice — roughly 200MB+), the file is left exactly as
  `embed()` wrote it and `msg` says why. Don't hand the file over as if it
  were finished: tell the reader the markups are only visible in Datum until
  they open it there and press Save.
- Verify a bake independently if you can: render a page with PyMuPDF or
  pdftoppm and look — the markups should be on the page.

## Things that bite

- **Top-left origin.** Repeated because it is the failure mode: flip y when
  converting from PDF-native coordinates.
- Straight out of `embed()`, markups are visible **only in Datum**
  (`BDMBakedOverlay = '0'`); Acrobat, Bluebeam and browsers show the clean
  document. `bake()` fixes that. If baking wasn't possible, say so when
  delivering, so nobody thinks the file is blank.
- `page` is 0-based. `pageCalibrations` keys are STRINGS (`"0"`, `"1"`).
- Stamps and badges anchor at their CENTRE; text and tables anchor TOP-LEFT.
- On text the fill is `boxFill`; on shapes it is `fillColor`. Don't cross
  them. Both must be colour **strings** — a boolean silently renders
  invisible text.
- `opacity` is 0–100 with 100 = solid (Datum's UI shows "transparency", the
  inverse — ignore that, store opacity).
- `thickness: 0` means no border (v3.22 and later only).
- `textAlign` / `vAlign` on text need `boxW` / `boxH` to align within.
- Drawing order is array order — write backgrounds before the things that sit
  on them.
- Password-protected PDFs: decrypt first (pypdf `reader.decrypt(pw)`), embed
  into the decrypted bytes.

## Delivering

Name the output `<original name> - MARKED UP.pdf` (or the user's requested
name), state what was placed where, state the one hand-computed check
quantity if anything was measured, and remind the reader: open it in Datum —
markups are editable; the BOQ lives under the **Workbook** button in the top
bar. State whether the file was baked: if yes, it is ready to send and shows
in Adobe/Chrome/Bluebeam; if `bake()` failed, say the markups only show in
Datum until someone opens it there and presses Save.
