# Datum project payload — full reference

This is the JSON Datum restores when it opens a PDF whose Info dictionary
carries `/BDMMarkupData` (base64 of this JSON), `/BDMVersion` = `"4"` and
`/BDMBakedOverlay` = `"0"`. Verified against Datum v3.10 (Aug 2026).

## Table of contents

- [Top-level payload](#top-level-payload)
- [Coordinate system](#coordinate-system)
- [Calibration](#calibration)
- [Annotation types](#annotation-types)
- [Takeoff items (the BOQ)](#takeoff-items-the-boq)
- [How Datum computes quantities](#how-datum-computes-quantities)
- [Worked example payload](#worked-example-payload)
- [Embedding mechanics](#embedding-mechanics)

## Top-level payload

```json
{
  "version": 4,
  "filename": "display-name.pdf",
  "annotations": [],
  "pageCalibrations": { "0": { "pixelsPerMm": 0.0566929, "scale": "1:50" } },
  "defaultCalibration": { "pixelsPerMm": 0.0566929, "scale": "1:50" },
  "countGroups": { "Doors": { "count": 2, "color": "#9333EA" } },
  "measurements": [],
  "takeoffItems": [],
  "takeoffZones": [],
  "takeoffHeadings": ["Prelims", "Concrete"],
  "viewports": [],
  "savedAt": ""
}
```

All arrays may be empty. `measurements` can safely be left `[]` — Datum
rebuilds it from annotations. `countGroups[group].count` must equal the
highest `number` used by count markers in that group (it seeds the next
number when the user keeps counting).

## Coordinate system

PDF points (1/72"), 1:1 scale, origin TOP-LEFT of each page, y downward.
From PDF-native (bottom-left) coordinates: `y_datum = page_height − y_pdf`.
A4 portrait ≈ 595.3 × 841.9 pt; A3 landscape ≈ 1190.6 × 841.9 pt.
Pages with `/Rotate` 90/180/270: coordinates are in the ROTATED (as-viewed)
space, sized as the viewer shows the page.

## Calibration

`pixelsPerMm` = page-units per real-world millimetre.
True-size sheet at scale 1:N → `pixelsPerMm = (72 / 25.4) / N`.

| Scale | pixelsPerMm |
|-------|-------------|
| 1:1   | 2.8346457   |
| 1:50  | 0.0566929   |
| 1:100 | 0.0283465   |
| 1:200 | 0.0141732   |

If the sheet was printed at a reduced size (e.g. an A1 drawing issued as A3,
i.e. half size), the effective denominator doubles: a "1:100 @ A1" set read
as A3 needs the 1:200 value — keep `scale` label honest ("1:200") or the
user will mis-trust measurements. If the true scale is unknown, either omit
calibration entirely (measurements show "Not calibrated", user calibrates in
Datum) or derive pixelsPerMm from a known dimension on the drawing:
`pixelsPerMm = measured_length_pt / real_length_mm`.

## Annotation types

Every annotation requires: unique `id` (string), `type`, `page` (0-based
int), `points` (array of `{x, y}`), `color` (hex string), `opacity`
(0–100, 100 = solid).

### cloud — revision cloud
`points` = closed polygon in order (4 corners for a rectangular cloud);
Datum draws the scallops. Extra: `thickness`.

### text — free text note
`points` = [anchor], TOP-LEFT of the text. Extra: `text`, `fontSize` (pt),
`fontFamily` ("Arial"), `fontWeight` ("400"|"700"), `fontStyle`
("normal"|"italic"), `textDecoration` ("none"|"underline").
Optional box behind the text: `boxFill` = colour STRING (e.g. "#FFFFFF" —
never a boolean; the value goes straight into canvas fillStyle), plus
`fillOpacity` (0–100).

### rectangle / highlight — box shapes
`points` = [cornerA, cornerB] (any two opposite corners). Extra: `fillColor`,
`fillOpacity` (0–100), `thickness`, `lineStyle` ("solid"|"dashed"|"dotted"),
`hatch` ("none"), `subject` (free text shown in the markups list).
`highlight` is the same shape rendered as a translucent marker — use
`color`/`fillColor` "#fbbf24", `fillOpacity` ~40.

### arrow
`points` = [tail, head] — the arrowhead lands on points[1]. Extra:
`thickness`, `lineStyle`, `fillColor` ("transparent" is fine here).

### stamp
`points` = [CENTRE]. Extra: `text` (e.g. "FOR REVIEW"), `stampColor` (border
+ text colour), `stampScale` (1 = base size, clamp 0.2–12), `opacity`
(default Datum stamps use 85).

### measure — measured line
`points` = [p1, p2]. Extra: `label: ""`, `measLabel: ""` (Datum fills labels
live from calibration), `thickness`, `lineStyle`. For the BOQ add
`takeoffItemId` and `isDeduction: false`. Deductions (`isDeduction: true`)
subtract from the item's total and render dashed.

### area — measured polygon
`points` = polygon in order (≥3, do not repeat the first point). Extra:
`label/perimLabel/measLabel: ""`, `fillColor` (use the item colour),
`fillOpacity` (~18), `thickness`, `hatch: "none"`, `takeoffItemId`,
`isDeduction`.

### count — numbered dot marker
`points` = [centre]. Extra: `group` (string), `number` (1-based within the
group), `takeoffItemId`. Keep `countGroups[group]` consistent (see above).
One marker = qty 1 on the linked count item.

### Types Datum supports but this skill does not write
callout, polyline/polyshape, dimension, ellipse, line, pen, tick, symbol,
signature, image, legend, table, cutcontent. They restore fine if present but
have fiddlier geometry/state. If one is truly needed, inspect Datum's source
(single HTML file in the public repo https://github.com/JamesBDM/bdm-pdf-tool)
for its `draw<Type>` function and creation site before writing it.

## Takeoff items (the BOQ)

Measured item:

```json
{ "id": "item-1", "name": "External walls — 190 blockwork (2.7m high)",
  "resultType": "vertical", "color": "#E5432E", "trade": "Masonry",
  "rate": 285, "factor": 2700, "markup": 0 }
```

- `resultType`: `length` | `area` | `count` | `vertical` | `volume`
- `factor`: millimetres — wall height for `vertical`, depth for `volume`;
  0 otherwise. Compatible shapes: length/vertical ← measure; area/volume ←
  area; count ← count.
- `trade`: the workbook grouping/heading (e.g. "Masonry"). Add each distinct
  trade to `takeoffHeadings` so empty groups still render in order.
- `rate`: $ per unit. `markup`: percent added on top.
- `color`: give each item a distinct colour and reuse it on its shapes —
  Datum colours an item's shapes by the item colour.

Manual (un-measured) item — prelims, PC sums, allowances:

```json
{ "id": "item-2", "name": "Site establishment", "manual": true,
  "manualQty": 1, "unit": "item", "color": "#64748B", "trade": "Prelims",
  "rate": 2500, "markup": 0 }
```

## How Datum computes quantities

Never store quantities — Datum derives them on every redraw:

- length (m) = Σ line lengths(pt) ÷ pixelsPerMm ÷ 1000
- vertical (m²) = length(m) × factor(mm)/1000
- area (m²) = Σ polygon areas(pt²) ÷ pixelsPerMm² ÷ 10⁶
- volume (m³) = area(m²) × factor(mm)/1000
- count (no.) = Σ markers (deductions count −1)
- amount ($) = qty × rate × (1 + markup/100)

The Workbook dock (Workbook button, top bar) shows the BOQ grouped by trade
with live totals and Excel export. Everything stays editable: dragging a
shape endpoint changes the quantity; editing rate/factor reprices the line.

## Worked example payload

A 1:50 A3 plan (1190.6 × 841.9 pt) with one 7 m wall measured and priced:

```json
{
  "version": 4,
  "filename": "Plan - MARKED UP.pdf",
  "annotations": [
    { "id": "a1", "type": "measure", "page": 0,
      "points": [ {"x": 180, "y": 224}, {"x": 576.9, "y": 224} ],
      "label": "", "measLabel": "", "color": "#E5432E", "thickness": 2,
      "opacity": 100, "lineStyle": "solid",
      "takeoffItemId": "item-1", "isDeduction": false }
  ],
  "pageCalibrations": { "0": { "pixelsPerMm": 0.0566929, "scale": "1:50" } },
  "defaultCalibration": { "pixelsPerMm": 0.0566929, "scale": "1:50" },
  "countGroups": {}, "measurements": [],
  "takeoffItems": [
    { "id": "item-1", "name": "External walls — 190 blockwork (2.7m high)",
      "resultType": "vertical", "color": "#E5432E", "trade": "Masonry",
      "rate": 285, "factor": 2700, "markup": 0 }
  ],
  "takeoffZones": [], "takeoffHeadings": ["Masonry"], "viewports": [],
  "savedAt": ""
}
```

Expected in Datum: line labelled "7.00m"; Workbook shows 18.9 m² @ $285 =
$5,386.50 (7.0 × 2.7).

## Embedding mechanics

Three Info-dictionary entries, nothing else changes:

- `/BDMMarkupData` — base64(UTF-8 JSON payload), as a PDF string
- `/BDMVersion` — `"4"`
- `/BDMBakedOverlay` — `"0"` (no baked image → markups render only in
  Datum until the user re-saves there; Datum then embeds a clean source
  copy and bakes an overlay for other viewers)

pypdf: `writer.append(reader)` then `writer.add_metadata({...})` — preserve
the source's existing string metadata keys, then add the three keys.
pdf-lib (Node): `doc.getInfoDict().set(PDFName.of('BDMMarkupData'),
PDFHexString.fromText(b64))` etc. Literal strings and hex strings both work —
Datum's reader handles either. Base64 text is ASCII-safe in both.

Do NOT set `/BDMCleanSource` or `/BDMCleanCompressed` — those are for
Datum's own saves that bake an overlay.
