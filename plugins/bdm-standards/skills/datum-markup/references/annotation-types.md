# Datum project payload — full reference

This is the JSON Datum restores when it opens a PDF whose Info dictionary
carries `/BDMMarkupData` (base64 of this JSON), `/BDMVersion` = `"4"` and
`/BDMBakedOverlay` = `"0"`. Verified against **Datum v3.22**.

## Table of contents

- [Top-level payload](#top-level-payload)
- [Coordinate system](#coordinate-system)
- [Calibration](#calibration)
- [Properties every annotation shares](#properties-every-annotation-shares)
- [Review markups](#review-markups)
- [Data + layout markups](#data--layout-markups)
- [Presentation markups (v3.22)](#presentation-markups-v322)
- [Measurement markups](#measurement-markups)
- [Takeoff items (the BOQ)](#takeoff-items-the-boq)
- [Style presets and tokens](#style-presets-and-tokens)
- [Groups](#groups)
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
highest `number` used by count markers in that group.

## Coordinate system

PDF points (1/72"), 1:1 scale, origin **TOP-LEFT** of each page, y downward.
From PDF-native (bottom-left) coordinates: `y_datum = page_height − y_pdf`.
A4 portrait ≈ 595.3 × 841.9 pt; A3 landscape ≈ 1190.6 × 841.9 pt.
Pages with `/Rotate` 90/180/270: coordinates are in the ROTATED (as-viewed)
space. `datum_markup.page_sizes()` returns the swapped sizes for you.

## Calibration

`pixelsPerMm` = page-units per real-world millimetre.
True-size sheet at scale 1:N → `pixelsPerMm = (72 / 25.4) / N`.

| Scale | pixelsPerMm |
|-------|-------------|
| 1:1   | 2.8346457   |
| 1:50  | 0.0566929   |
| 1:100 | 0.0283465   |
| 1:200 | 0.0141732   |

An A1 drawing issued at A3 is half size, so a "1:100 @ A1" set read as A3
needs the 1:200 value — keep the `scale` label honest or the reader will
mis-trust the measurements. `viewports` override the page calibration inside
a rectangle, for a 1:20 detail on a 1:100 sheet.

## Properties every annotation shares

Required: unique `id` (string), `type`, `page` (0-based int), `points`
(array of `{x, y}`), and normally `color` (hex string) and `opacity`
(0–100, 100 = solid).

Widely supported optional properties:

| Property | Applies to | Notes |
|---|---|---|
| `thickness` | all stroked shapes | **`0` = no border at all** (v3.22). Before v3.22 `0` was silently treated as `2`. |
| `lineStyle` | lines, boxes | `solid` \| `dashed` \| `dotted` \| `dash-dot` |
| `lineCap` / `lineJoin` | lines, boxes, pen, cloud | `butt`/`round`/`square`, `miter`/`round`/`bevel` (v3.22) |
| `radius` | rectangle, text, callout, all panel types | Corner radius in points. `0`/absent = square. (v3.22) |
| `fillColor` | filled shapes | Hex string, or `"none"` |
| `fillOpacity` | filled shapes | 0–100 |
| `fillColor2` + `gradientAngle` | filled shapes, panels | Two-stop linear gradient. Angle in degrees clockwise from left→right; default 90 = top→bottom. (v3.22) |
| `shadow` + `shadowColor` / `shadowBlur` / `shadowOffsetX` / `shadowOffsetY` | shapes, text, callout, panels | `shadow` must be `true` for the rest to apply. (v3.22) |
| `strokeSide` | rectangle, panel types | `"all"` (default) or any of `t`/`r`/`b`/`l` joined, e.g. `"l"` for a left accent bar. (v3.22) |
| `hatch` | rectangle, ellipse, polygon, area | `none` \| `diagonal` \| `diagonal-rev` \| `diagonal-cross` \| `cross` \| `horizontal` \| `vertical` \| `dots` \| `solid` |
| `hatchSpacing` / `hatchAngle` / `hatchWeight` / `hatchOpacity` | as above | Gap in points (default 6), degrees, line width, 0–100 (default 30). (v3.22) |
| `rotation` | rectangle, ellipse, highlight, image, signature, stamp, text, symbol, all panel types | Degrees. Points stay unrotated. |
| `groupId` | any | Members move, delete and re-order as one. (v3.22) |
| `preset` | any | Named house style, expanded on load. (v3.22) |
| `subject` | shapes | Free text shown in the markups list |

> **Hatch clipping.** Before v3.22 hatch filled the shape's *bounding box* and
> never clipped, so diagonal hatch overhung a rectangle as a parallelogram and
> ellipses/polygons/areas hatched the box around them. Fixed in v3.22 — hatch
> now clips to the real path everywhere.

## Review markups

### cloud — revision cloud
`points` = closed polygon in order (4 corners for a rectangular cloud);
Datum draws the scallops. Extra: `thickness`.

### text — free text note
`points` = [anchor], TOP-LEFT of the text. Extra: `text`, `fontSize` (pt),
`fontFamily`, `fontWeight` (`"400"`/`"700"`), `fontStyle`, `textDecoration`,
`textColor` (the letters — `color` is the box outline fallback).

Box: `boxW` / `boxH` fix the size and wrap the text; `boxFill` is a colour
**STRING** (never a boolean); `boxStroke` outlines it; `fillOpacity` 0–100;
`boxPad` (v3.22) sets the breathing room, default 3.

**v3.22:** `textAlign` (`left`/`center`/`right`) and `vAlign`
(`top`/`middle`/`bottom`) now actually position the text inside the box.
`textAlign` was written by the properties panel before v3.22 but the renderer
ignored it. Both need `boxW`/`boxH` to have anything to align within.

### rectangle / highlight — box shapes
`points` = [cornerA, cornerB] (any two opposite corners; order does not
matter). `highlight` is the same shape as a translucent marker — use
`color`/`fillColor` `"#fbbf24"`, `fillOpacity` ~40.

### ellipse / line / polygon / polyline
`ellipse` takes two corners of its bounding box. `line` takes two endpoints.
`polygon` takes ≥3 points and closes itself. `polyline` is an open run of
points; set `isShape: true` and `hideLabel: true` for a plain shape with no
measurement label.

### arrow
`points` = [tail, head] — the head lands on `points[1]`.
**v3.22:** `arrowHead` and `arrowTail` take `triangle` (default) \| `open` \|
`dot` \| `bar` \| `none`, so double-headed span arrows are one markup.
`arrowScale` sizes the head (1 = standard).

### callout — leader + boxed text
`anchor` = the point being pointed at (the head lands there), `textPos` = the
text box's top-left, `knees` = `[{x,y}, …]` bends the leader. Extra: `text`,
`fillColor`, `fillOpacity`, `textColor`, `textAlign`, `boxW`, `boxH`,
`fontSize`, plus `radius` and `boxPad` (v3.22). Also set `points: [anchor]`
so generic code that reads `points` still finds it.

### stamp
`points` = [CENTRE]. Extra: `text`, `stampColor`, `stampScale` (1 = base,
clamp 0.2–12), `opacity` (Datum's own stamps use 85).

### tick / pen / signature
`tick`: `points` = [centre], `tickSize`, `thickness`.
`pen`: `points` = freehand run.
`signature`: two-corner box; keeps its aspect ratio on resize.

### symbol — the construction library
`points` = [cornerA, cornerB]. `symbolId` picks from 104 symbols in 8
categories (General/Drafting, Architectural, Plumbing, Electrical,
Mechanical, Fire, Furniture, Civil). Useful General ids: `g-north`,
`g-section`, `g-detail`, `g-elevation`, `g-level`, `g-grid`, `g-rev`,
`g-keynote`.

### image
`points` = [cornerA, cornerB], plus the image data Datum stores on the
annotation. Easiest written from inside Datum.

### cutcontent — white-out
`points` = [cornerA, cornerB], `color: "#ffffff"`. Paints over the underlying
PDF at render time, so an agent can *replace* content rather than only
overlay it.

### dimension
`points` = [p1, p2]. A measured line drawn with witness lines.

## Data + layout markups

### table — a real data table
`points` = [top-left].

```json
{ "id":"t1", "type":"table", "page":0, "points":[{"x":60,"y":120}],
  "title":"Trade Package Status", "titleBg":"#1a1b2e",
  "headerBg":"#e9edf2", "borderColor":"#333333", "gridColor":"#b8bec8",
  "bgColor":"#ffffff", "fontSize":9, "legendScale":1, "showGrid":true,
  "cols":[ {"label":"Package","align":"left"},
           {"label":"Status","type":"colour","align":"center"},
           {"label":"Value","align":"right"} ],
  "rows":[ [ {"text":"Structure"}, {"color":"#16A34A","text":"On track"}, {"text":"$1,240,000"} ],
           [ {"text":"Facade"},    {"color":"#F59E0B","text":"At risk"},  {"text":"$860,000"} ] ],
  "opacity":100 }
```

A normal cell takes `text`, `fill`, `bold`, `textColor`. A `"colour"` column's
cell takes `color` (the swatch) and optional `text` drawn over it. Ink
contrast is chosen automatically against the fill. Drag any corner in Datum
to rescale the whole table (`legendScale`).

### legend — auto-generated takeoff key
`points` = [top-left]. `legendMode` = `simple` \| `summary` \| `detailed`,
`legendScope` = `doc` \| `page`, `showRates`, `legendScale`. Reads live from
`takeoffItems`, so it stays correct as the reader edits quantities.

## Presentation markups (v3.22)

All of these are **two-point boxes** — `points` = [cornerA, cornerB] — except
`badge`, which is a single centre point. All accept `radius`, `fillColor`,
`fillColor2`/`gradientAngle`, `shadow*`, `rotation`, `groupId` and `preset`.

### chip — rounded pill label
`text`, `fillColor`, `textColor`, `fontSize`, `radius` (defaults to a full
pill). Ink contrast is automatic if `textColor` is omitted.

### badge — numbered step circle
`points` = [CENTRE]. `text` (or `number`), `badgeSize` (diameter, default 22),
`fillColor`, `textColor`, `borderColor`, `thickness`.
Distinct from `count`: a badge never touches the workbook.

### divider — rule, optionally broken by a label
`text`, `labelAlign` (`left`/`center`/`right`), `labelGap`, `color`,
`textColor`, `fontSize`, `thickness`. Drawn at the box's vertical centre.

### banner — page / section header band
`title`, `subtitle`, `textColor`, `subColor`, `fontSize`, `subFontSize`,
`textAlign`, `accentColor`, `accentWidth`, `accentSide`
(`left`/`top`/`right`/`bottom`), `boxPad`.

### quote — accent-bar panel for a finding
`text` (wraps to the box), `attribution`, `accentColor`, `accentWidth`,
`accentSide`, `fillColor`, `textColor`, `fontSize`, `boxPad`.

### kpi — stat tile
`value`, `caption`, `delta`, `deltaDirection` (`up`/`down`/`flat` — drives the
glyph and its colour), `deltaColor`, `accent`, `accentWidth`, `accentSide`,
`captionPosition` (`top` to put the caption above the value), `valueSize`,
`captionSize`, `captionColor`, `textColor`, `boxPad`.

### chevron — process / stage band
`segments`: `[{ "label": "Design", "color": "#…", "active": true }, …]`.
`current` (int) highlights segments `0..current` when a segment has no
explicit `active`. `activeColor`, `fillColor` (inactive), `activeTextColor`,
`textColor`, `fontSize`, `gap`, `notch`.

### timeline — milestone bar
`milestones`: `[{ "label": "PC", "date": "30 Nov 26", "state": "todo", "at": 0.8 }, …]`.
`state` = `done` \| `current` \| `todo`. `at` is 0–1 along the box; omit it and
milestones space evenly. `color` (track), `doneColor`, `currentColor`,
`todoColor`, `dotSize`, `axisAt` (0–1, default 0.5), `fontSize`, `dateColor`.
Labels are centred on their dot, so leave margin at each end or the first and
last labels overhang the box.

### bracket — span marker
`text`, `orientation` (`top`/`bottom`/`left`/`right`), `tickSize`, `color`,
`textColor`, `fontSize`, `labelBackground` (a colour string, or `false` for
none — never `true`).

### progress — percentage bar
`value` 0–100 (clamped), `barColor`, `fillColor` (track), `showValue`
(default true), `valueLabel` (overrides the "65%" text), `radius`.

### chart — bar / line / donut / pie
`chartType` = `bar` \| `line` \| `donut` \| `pie`.
`data`: `[{ "label": "Structure", "value": 1240, "color": "#…" }, …]` —
`color` is optional, the palette cycles. Also: `title`, `palette` (array),
`showValues`, `showLabels`, `maxValue`, `minValue`, `barRadius`, `axisColor`,
`textColor`, `boxPad`; `areaFill` and `lineColor` for line; `innerRadius` and
`centerLabel` for donut.

## Measurement markups

### measure — measured line
`points` = [p1, p2]. Extra: `label: ""`, `measLabel: ""` (Datum fills these
live), `thickness`, `lineStyle`. For the BOQ add `takeoffItemId` and
`isDeduction: false`. Deductions subtract and render dashed.

### area — measured polygon
`points` = polygon in order (≥3, do not repeat the first point). Extra:
`label`/`perimLabel`/`measLabel` `= ""`, `fillColor`, `fillOpacity` (~18),
`thickness`, `hatch`, `takeoffItemId`, `isDeduction`, `showPerimeter`.

### count — numbered dot marker
`points` = [centre]. Extra: `group` (string), `number` (1-based within the
group), `takeoffItemId`. Keep `countGroups[group].count` in step.

## Takeoff items (the BOQ)

```json
{ "id": "item-1", "name": "External walls — 190 blockwork (2.7m high)",
  "resultType": "vertical", "color": "#E5432E", "trade": "Masonry",
  "rate": 285, "factor": 2700, "markup": 0 }
```

- `resultType`: `length` | `area` | `count` | `vertical` | `volume`
- `factor`: millimetres — wall height for `vertical`, depth for `volume`.
- Compatible shapes: length/vertical ← `measure`, `polyline`, `dimension`;
  area/volume ← `area`; count ← `count`.
- `trade` groups it in the workbook; add each distinct trade to
  `takeoffHeadings` so empty groups still render in order.
- Give each item a distinct `color` and reuse it on its shapes.

Manual (un-measured) line — prelims, PC sums, allowances:

```json
{ "id": "item-2", "name": "Site establishment", "manual": true,
  "manualQty": 1, "unit": "item", "color": "#64748B", "trade": "Prelims",
  "rate": 2500, "markup": 0 }
```

Quantities are **never stored** — Datum derives them on every redraw:

- length (m) = Σ line lengths(pt) ÷ pixelsPerMm ÷ 1000
- vertical (m²) = length(m) × factor(mm)/1000
- area (m²) = Σ polygon areas(pt²) ÷ pixelsPerMm² ÷ 10⁶
- volume (m³) = area(m²) × factor(mm)/1000
- count (no.) = Σ markers (deductions count −1)
- amount ($) = qty × rate × (1 + markup/100)

## Style presets and tokens

Set `"preset": "<name>"` on an annotation and Datum expands it into real
properties on load. **Anything you set explicitly wins over the preset**, so a
preset is a starting point, not a straitjacket.

Tokens: `brand #E5432E`, `ink #0F172A`, `muted #64748B`, `line #E2E8F0`,
`surface #FFFFFF`, `surfaceAlt #F8FAFC`, `navy #1a1b2e`, `ok #16A34A`,
`warn #F59E0B`, `risk #DC2626`, `info #4F8EF7`, `accent2 #9333EA`.

| Preset | For | Gives you |
|---|---|---|
| `card` | rectangle | White panel, hairline border, radius 10, soft shadow |
| `card-flat` | rectangle | Tinted panel, no border, radius 10 |
| `card-accent` | rectangle | White panel with a brand left accent bar |
| `banner-brand` | banner | Navy gradient band, white text, brand accent |
| `heading` / `subheading` / `body` / `note` | text | The type scale |
| `chip-ok` / `chip-warn` / `chip-risk` / `chip-info` / `chip-neutral` | chip | Status colours with correct ink |
| `kpi` | kpi | White tile, border, radius 8, brand accent |
| `quote-finding` | quote | Tinted panel, brand accent bar |
| `callout-note` | callout | White rounded panel, brand leader |
| `divider-soft` | divider | Hairline rule, muted label |

Prefer a preset to hand-picked hex. It is what keeps eight agents from
inventing eight different ambers, and a rebrand becomes one edit.

## Groups

Give every composed object its own `groupId`:

```json
{ "id":"card-bg",  "type":"rectangle", "groupId":"grp-kpi-1", ... }
{ "id":"card-val", "type":"text",      "groupId":"grp-kpi-1", ... }
```

In Datum the members move, delete and re-order together. Without it the
reader has to drag every piece of a card separately, which is the single
biggest reason agent-built layouts used to be painful to edit. Many composed
looks are now one annotation anyway (`kpi`, `banner`, `quote`) — reach for
those first and use groups for genuinely bespoke compositions.

Drawing order is array order; later annotations paint on top. In Datum the
reader can restack with Arrange → Front / Up / Down / Back.

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
- `/BDMBakedOverlay` — `"0"` (no baked image → markups render only in Datum
  until the reader re-saves there; Datum then embeds a clean source copy and
  bakes an overlay for other viewers)

pypdf: `writer.append(reader)` then `writer.add_metadata({...})` — preserve
the source's existing string metadata keys, then add the three.
pdf-lib (Node): `doc.getInfoDict().set(PDFName.of('BDMMarkupData'),
PDFHexString.fromText(b64))`. Literal and hex strings both work.

Do NOT set `/BDMCleanSource` or `/BDMCleanCompressed` — those belong to
Datum's own saves that bake an overlay.
