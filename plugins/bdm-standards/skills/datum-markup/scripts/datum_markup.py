#!/usr/bin/env python3
"""
datum_markup.py — write editable Datum markups, measurements, priced BOQ
takeoffs and presentation layouts directly into a PDF, no Datum UI involved.

Datum (BDM PDF Markup Tool) stores its whole editable project as JSON,
base64-encoded, inside the PDF's Info dictionary under the key
/BDMMarkupData. When Datum opens a PDF carrying that key, every markup,
measurement and takeoff item is restored fully live and editable.

    from datum_markup import DatumProject, embed, Grid

    p = DatumProject("Report.pdf", page_w=595.3, page_h=841.9)
    g = p.grid()                                    # 12-column layout helper

    p.banner(*g.band(top=40, height=54), title="Trade Package Status",
             subtitle="PCG 14 — 22 August 2026", preset="banner-brand")
    p.kpi(*g.cell(0, 4, top=110, height=90), value="$4.21M",
          caption="Certified to date", delta="+8.2%", direction="up")
    p.chip(*g.cell(0, 2, top=220, height=20), text="On track", preset="chip-ok")
    embed("source.pdf", p, "Report - MARKED UP.pdf")
    bake("Report - MARKED UP.pdf")   # Datum's own Save → visible in Adobe too

Coordinates: PDF points (1/72 inch) at 1:1, origin at the page's TOP-LEFT,
y increasing DOWNWARD. (This is pdf.js viewport space, NOT PDF-native
bottom-left space. If you computed positions bottom-left, convert with
y_datum = page_height - y_pdf.)

Requires: pypdf  (pip install pypdf). Any 3.x / 4.x / 5.x works.

Targets Datum v3.22 (project payload version 4).
"""
import base64
import json
import sys
import uuid

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0

# ---------------------------------------------------------------------------
# House style. These mirror DATUM_TOKENS / DATUM_PRESETS inside Datum itself,
# so a markup written here looks the same as one styled in the app. Reference a
# role, not a hex code, and a rebrand is one edit in both places.
# ---------------------------------------------------------------------------
TOKENS = {
    "brand": "#E5432E", "ink": "#0F172A", "muted": "#64748B",
    "line": "#E2E8F0", "surface": "#FFFFFF", "surfaceAlt": "#F8FAFC",
    "navy": "#1a1b2e", "ok": "#16A34A", "warn": "#F59E0B",
    "risk": "#DC2626", "info": "#4F8EF7", "accent2": "#9333EA",
}
FONT = '"Segoe UI", Arial, sans-serif'

PRESETS = {
    "card":          {"fillColor": TOKENS["surface"], "fillOpacity": 100, "color": TOKENS["line"],
                      "thickness": 1, "radius": 10, "shadow": True, "shadowBlur": 14,
                      "shadowOffsetY": 3, "shadowColor": "rgba(15,23,42,0.10)"},
    "card-flat":     {"fillColor": TOKENS["surfaceAlt"], "fillOpacity": 100, "thickness": 0, "radius": 10},
    "card-accent":   {"fillColor": TOKENS["surface"], "fillOpacity": 100, "color": TOKENS["brand"],
                      "thickness": 3, "strokeSide": "l", "radius": 8},
    "banner-brand":  {"fillColor": TOKENS["navy"], "fillColor2": "#2b2d52", "gradientAngle": 0,
                      "textColor": "#FFFFFF", "accentColor": TOKENS["brand"], "accentWidth": 5,
                      "radius": 4, "thickness": 0},
    "heading":       {"fontSize": 20, "fontWeight": "700", "textColor": TOKENS["ink"], "fontFamily": FONT},
    "subheading":    {"fontSize": 13, "fontWeight": "600", "textColor": TOKENS["muted"], "fontFamily": FONT},
    "body":          {"fontSize": 10, "fontWeight": "400", "textColor": TOKENS["ink"], "fontFamily": FONT},
    "note":          {"fontSize": 9, "fontWeight": "400", "textColor": TOKENS["muted"],
                      "boxFill": "#FFFFFF", "fillOpacity": 92, "boxPad": 5, "radius": 4},
    "chip-ok":       {"fillColor": TOKENS["ok"], "textColor": "#FFFFFF", "thickness": 0},
    "chip-warn":     {"fillColor": TOKENS["warn"], "textColor": "#111111", "thickness": 0},
    "chip-risk":     {"fillColor": TOKENS["risk"], "textColor": "#FFFFFF", "thickness": 0},
    "chip-info":     {"fillColor": TOKENS["info"], "textColor": "#FFFFFF", "thickness": 0},
    "chip-neutral":  {"fillColor": TOKENS["line"], "textColor": TOKENS["ink"], "thickness": 0},
    "kpi":           {"fillColor": TOKENS["surface"], "color": TOKENS["line"], "thickness": 1,
                      "radius": 8, "accent": TOKENS["brand"], "accentWidth": 4, "boxPad": 10},
    "quote-finding": {"fillColor": TOKENS["surfaceAlt"], "accentColor": TOKENS["brand"],
                      "accentWidth": 4, "radius": 6, "thickness": 0, "boxPad": 10},
    "callout-note":  {"fillColor": "#FFFFFF", "fillOpacity": 96, "color": TOKENS["brand"],
                      "radius": 6, "boxPad": 7, "fontSize": 10},
    "divider-soft":  {"color": TOKENS["line"], "thickness": 1, "textColor": TOKENS["muted"], "fontSize": 9},
}

# Types Datum's renderer accepts. Writing anything else produces a dashed
# placeholder box, so the verifier below treats it as an error.
VALID_TYPES = {
    # original markup set
    "measure", "polyline", "area", "rectangle", "ellipse", "line", "polygon",
    "cloud", "arrow", "text", "callout", "stamp", "tick", "signature", "image",
    "symbol", "pen", "highlight", "count", "dimension", "cutcontent", "legend",
    "table",
    # v3.22 presentation markups
    "chip", "badge", "divider", "banner", "quote", "kpi", "chevron",
    "timeline", "bracket", "progress", "chart",
}
# Types positioned by two opposite corners.
BOX2_TYPES = {"rectangle", "ellipse", "highlight", "cutcontent", "image", "symbol",
              "chip", "kpi", "banner", "quote", "divider", "chevron", "timeline",
              "bracket", "chart", "progress"}


# Every symbol id Datum v3.42 knows, with its default placed size (w, h) in
# PDF points. Not all symbols are square: the artwork is mapped into the
# annotation box, so a box of the wrong proportions draws it stretched.
# symbol_at() uses this table. Generated by gen-skill-symbols.js — do not
# edit by hand.
SYMBOL_SIZES = {
    "g-north": (44, 44),
    "g-section": (40, 40),
    "g-detail": (40, 40),
    "g-elevation": (40, 40),
    "g-level": (44, 44),
    "g-grid": (36, 36),
    "g-rev": (36, 36),
    "g-keynote": (38, 38),
    "g-benchmark": (36, 36),
    "g-scalebar": (60, 60),
    "a-door": (50, 50),
    "a-door2": (56, 56),
    "a-slider": (56, 56),
    "a-bifold": (52, 52),
    "a-cavity": (56, 56),
    "a-window": (56, 56),
    "a-window-s": (56, 56),
    "a-stair": (29, 86.83),
    "a-stair-cut": (29, 86.83),
    "a-stair-l": (88, 76.3),
    "a-stair-u": (65, 100.31),
    "a-stair-spiral": (59, 59),
    "a-ramp": (35, 116.67),
    "a-skylight": (44, 44),
    "a-break": (52, 14.56),
    "a-lift": (44, 44),
    "a-hatch": (34, 34),
    "u-bed-k": (80, 59.52),
    "u-bed-q": (71, 59.29),
    "u-bed-d": (40, 55.48),
    "u-bed-ks": (31, 59.39),
    "u-bed-s": (27, 54.88),
    "u-bunk": (27, 66.67),
    "u-bedside": (25, 22.23),
    "u-drawers": (35, 14.6),
    "u-dresser": (35, 26.25),
    "u-robe": (53, 17.65),
    "u-wir": (70, 17.5),
    "u-desk": (44, 39.34),
    "u-sofa": (62, 26.6),
    "u-sofa2": (44, 26.4),
    "u-sofa-l": (76, 55.56),
    "u-armchair": (26, 24.54),
    "u-coffee": (35, 20.41),
    "u-sidetable": (25, 25),
    "u-tv": (53, 15.11),
    "u-rug": (70, 55.16),
    "u-table": (53, 55.97),
    "u-table-8": (70, 41.16),
    "u-table-r": (65, 65),
    "u-table-r6": (74, 74),
    "u-stool": (25, 27.5),
    "u-bookshelf": (53, 10.28),
    "u-chair": (25, 20.83),
    "k-island": (70, 29.19),
    "p-sink": (28, 17.5),
    "k-sink1": (25, 22.5),
    "u-cooktop": (25, 25),
    "k-cooktop9": (26, 17.34),
    "k-oven": (25, 25),
    "k-rangehood": (26, 17.34),
    "u-fridge": (26, 20.23),
    "u-dw": (25, 25),
    "k-mw": (25, 16.68),
    "k-pantry": (26, 17.34),
    "u-wash": (25, 25),
    "u-dryer": (25, 25),
    "p-tub": (25, 22.73),
    "k-bins": (30, 15),
    "p-wc": (25, 43.78),
    "p-wc-wh": (25, 35.51),
    "p-bidet": (25, 40.32),
    "p-basin": (25, 25),
    "p-basin-o": (25, 20),
    "p-vanity": (30, 16.68),
    "p-vanity-2": (53, 16.22),
    "p-bath": (50, 22.05),
    "p-bath-fs": (50, 23.55),
    "p-shower": (26, 26),
    "p-shower-w": (47, 26.41),
    "p-urinal": (25, 41.67),
    "p-fw": (24, 24),
    "p-hwu": (36, 36),
    "p-dp": (24, 24),
    "p-tap": (34, 15.81),
    "p-valve": (34, 18.7),
    "p-wm": (30, 30),
    "c-tree": (88, 88),
    "l-tree-lg": (90, 90),
    "l-tree-sm": (53, 53),
    "l-palm": (80, 80),
    "l-conifer": (44, 44),
    "c-shrub": (35, 35),
    "l-hedge": (90, 14.4),
    "l-ground": (70, 70),
    "l-planter": (53, 17.65),
    "l-pot": (25, 25),
    "l-turf": (88, 58.7),
    "l-step": (88, 21.12),
    "l-deck": (88, 58.7),
    "l-pergola": (90, 67.5),
    "l-pool": (90, 55.71),
    "l-spa": (59, 59),
    "l-lounger": (26, 74.29),
    "l-outdoor": (70, 70),
    "l-bbq": (35, 17.5),
    "l-firepit": (29, 29),
    "l-fence": (90, 14.4),
    "l-retwall": (90, 18),
    "l-clothesline": (70, 35),
    "l-tank": (59, 59),
    "l-letterbox": (25, 35.71),
    "l-car": (53, 110.42),
    "e-gpo": (28, 28),
    "e-gpo2": (28, 28),
    "e-gpowp": (30, 30),
    "e-switch": (26, 26),
    "e-switch2": (28, 28),
    "e-downlight": (26, 26),
    "e-batten": (28, 28),
    "e-led": (56, 11.2),
    "e-fan": (36, 36),
    "e-smoke": (28, 28),
    "e-exhaust": (32, 32),
    "e-db": (40, 24),
    "e-data": (26, 26),
    "e-tv": (28, 28),
    "e-3p": (30, 30),
    "e-iso": (34, 17),
    "e-pir": (30, 30),
    "e-em": (26, 26),
    "e-exit": (44, 19.36),
    "m-supply": (36, 36),
    "m-return": (36, 36),
    "m-exhaustg": (36, 36),
    "m-duct": (40, 40),
    "m-split": (52, 39.52),
    "m-cond": (44, 30.8),
    "m-thermo": (26, 26),
    "m-damper": (36, 18),
    "m-ef": (32, 32),
    "m-fcu": (44, 23.76),
    "f-ext": (28, 28),
    "f-hr": (32, 32),
    "f-hyd": (28, 28),
    "f-spk": (22, 22),
    "f-sd": (28, 28),
    "f-hd": (28, 28),
    "f-mcp": (30, 30),
    "f-fb": (26, 26),
    "f-wip": (28, 28),
    "f-fip": (40, 22.4),
    "c-park": (44, 44),
    "c-parkdis": (44, 44),
    "c-bollard": (20, 20),
    "c-gate": (48, 48),
    "c-pit": (32, 32),
    "c-mh": (30, 30),
    "c-pole": (26, 26),
    "c-sign": (30, 48),
    "cm-crane-tower": (90, 90),
    "cm-crane-mobile": (80, 80),
    "cm-pump-boom": (70, 49.15),
    "cm-pump-line": (40, 20),
    "cm-agitator": (60, 21.6),
    "cm-excavator": (50, 50),
    "cm-truck": (70, 25.2),
    "cm-ewp": (30, 18),
    "cm-telehandler": (44, 22),
    "cm-hoist": (44, 30.61),
    "cm-gen": (36, 18),
    "cm-lighttower": (30, 30),
    "cm-tpb": (30, 16.8),
    "cm-water": (26, 26),
    "cm-cctv": (28, 28),
    "cm-office": (60, 27.6),
    "cm-crib": (60, 27.6),
    "cm-amenities": (60, 27.6),
    "cm-change": (60, 27.6),
    "cm-portaloo": (25, 25),
    "cm-container": (60, 24),
    "cm-container40": (90, 18),
    "cm-firstaid": (28, 28),
    "cm-muster": (36, 36),
    "cm-signin": (34, 17),
    "cm-entry": (40, 17.6),
    "cm-spill": (28, 28),
    "cm-smoking": (36, 36),
    "cm-laydown": (70, 42),
    "cm-loading": (70, 42),
    "cm-exclusion": (60, 60),
    "cm-hoarding": (90, 18),
    "cm-tempfence": (90, 14.4),
    "cm-gate-slide": (60, 24),
    "cm-scaffold": (80, 24),
    "cm-gantry": (80, 32),
    "cm-shaker": (50, 25),
    "cm-washout": (44, 26.4),
    "cm-skip": (34, 17),
    "cm-hookbin": (56, 20.16),
    "cm-stockpile": (50, 50),
    "cm-siltfence": (90, 14.4),
    "cm-pitprotect": (34, 34),
    "cm-tpz": (70, 70),
    "cm-monitor": (26, 26),
    "tc-route-veh": (70, 21),
    "tc-route-ped": (70, 21),
    "tc-controller": (26, 26),
    "tc-spotter": (26, 26),
    "tc-cone": (25, 25),
    "tc-barrier": (90, 18),
    "tc-barricade": (50, 12),
    "tc-sign-rw": (30, 30),
    "tc-stopslow": (26, 26),
    "tc-speed": (26, 26),
    "tc-footpath": (36, 18),
    "tc-arrowboard": (40, 20),
    "tc-vms": (40, 20),
    "tc-lights": (25, 53.41),
    "cp-schwing-17": (90, 45),
    "cp-putz-20": (90, 49.84),
    "cp-junjin-20": (90, 42.78),
    "cp-hangil-21": (90, 50.93),
    "cp-putz-24": (90, 44.15),
    "cp-sany-25": (90, 54),
    "cp-junjin-25": (90, 54.23),
    "cp-putz-28": (90, 50.14),
    "cp-junjin-30": (90, 53.11),
    "cp-sany-30": (90, 52.17),
    "cp-zoomlion-32": (90, 51.63),
    "cp-putz-33": (90, 57.27),
    "cp-putz-36": (90, 57.27),
    "cp-junjin-38": (90, 69.89),
    "cp-sany-39": (90, 61.78),
    "cp-putz-42": (90, 67.78),
    "cp-sany-45": (90, 69.01),
    "cp-putz-47": (90, 72.29),
    "cp-junjin-47": (90, 73.61),
    "cp-everdigm-48": (90, 63.33),
    "cp-junjin-50": (90, 73.48),
    "cp-everdigm-50": (90, 73.42),
    "cp-everdigm-56": (90, 77.97),
    "cp-junjin-57": (90, 80.2),
    "cp-putz-58": (90, 73.37),
    "tv-b99": (90, 33.58),
    "tv-ute": (90, 32.5),
    "tv-srv": (90, 32.77),
    "tv-mrv": (90, 25.57),
    "tv-crane": (90, 57.6),
    "tv-hrv": (90, 18),
    "tv-tipper": (90, 27.11),
    "tv-tipper8": (90, 23.68),
    "tv-agi-mini": (90, 28.43),
    "tv-agi-6": (90, 23.93),
    "tv-agi-8": (90, 21.23),
    "tv-semi": (90, 11.91),
    "tv-truckdog": (90, 11.84),
    "tv-bdouble": (90, 8.65),
    "cr-tc-flat-50": (40, 40),
    "cr-tc-flat-60": (40, 40),
    "cr-tc-hammer-70": (40, 40),
    "cr-tc-luff-45": (40, 40),
    "cr-tc-luff-60": (40, 40),
    "cr-tc-self-40": (40, 40),
    "cr-franna-at15": (90, 24.31),
    "cr-franna-at20": (90, 22.96),
    "cr-franna-mac25": (90, 20.09),
    "cr-franna-at40": (90, 19.49),
    "cr-mc-25": (90, 66.32),
    "cr-mc-60": (90, 63.16),
    "cr-mc-100": (90, 56.92),
    "cr-mc-220": (90, 55.47),
    "cr-mc-400": (90, 49.59),
    "ac-hoist-single": (40, 53.33),
    "ac-hoist-twin": (40, 36.13),
    "ac-hoist-long": (40, 66.04),
    "ac-hoist-mat": (40, 42.11),
    "ac-sc-19": (30, 8.35),
    "ac-sc-26": (30, 7.28),
    "ac-sc-32": (30, 10.51),
    "ac-sc-40": (30, 9.06),
    "ac-sc-rt33": (30, 9.79),
    "ac-sc-rt43": (30, 10.77),
    "ac-mast-20": (30, 16.64),
    "ac-boom-k34": (30, 11.25),
    "ac-boom-k45": (30, 10),
    "ac-boom-k60": (30, 8.72),
    "ac-boom-t60": (30, 8.33),
    "ac-boom-t80": (30, 6.64),
    "ac-boom-t135": (30, 5.6),
    "ac-spider-17": (30, 30),
    "sf-run-1200": (90, 9),
    "sf-run-700": (90, 5.25),
    "sf-stair": (60, 60),
    "sf-loading": (60, 60),
    "sf-tower-1450": (60, 42.31),
    "sf-tower-850": (60, 38.43),
    "ss-office-6": (60, 30),
    "ss-office-9": (60, 18.75),
    "ss-office-12": (60, 16.5),
    "ss-office-stack": (60, 16.5),
    "ss-crib-6": (60, 30),
    "ss-crib-12": (60, 16.5),
    "ss-toilet-6": (60, 30),
    "ss-change-6": (60, 30),
    "ss-firstaid": (60, 40),
    "ss-portaloo": (60, 60),
    "ss-portaloo-acc": (60, 60),
    "ss-cont-10": (60, 48.96),
    "ss-cont-20": (60, 24.16),
    "ss-cont-40": (60, 12.01),
}

# True-size symbols: real footprint (w, h) in millimetres of the annotation
# box. symbol_true_size() multiplies by the page's pixelsPerMm.
SYMBOL_REAL = {
    "cp-schwing-17": (8600, 4300),
    "cp-putz-20": (9390, 5200),
    "cp-junjin-20": (9047, 4300),
    "cp-hangil-21": (9100, 5150),
    "cp-putz-24": (10600, 5200),
    "cp-sany-25": (10500, 6300),
    "cp-junjin-25": (10455, 6300),
    "cp-putz-28": (10590, 5900),
    "cp-junjin-30": (11100, 6550),
    "cp-sany-30": (11300, 6550),
    "cp-zoomlion-32": (11540, 6620),
    "cp-putz-33": (12100, 7700),
    "cp-putz-36": (12100, 7700),
    "cp-junjin-38": (11203, 8700),
    "cp-sany-39": (11800, 8100),
    "cp-putz-42": (11950, 9000),
    "cp-sany-45": (12520, 9600),
    "cp-putz-47": (12450, 10000),
    "cp-junjin-47": (12470, 10200),
    "cp-everdigm-48": (14069, 9900),
    "cp-junjin-50": (13350, 10900),
    "cp-everdigm-50": (14220, 11600),
    "cp-everdigm-56": (14774, 12800),
    "cp-junjin-57": (14812, 13200),
    "cp-putz-58": (15100, 12310),
    "tv-b99": (5200, 1940),
    "tv-ute": (5400, 1950),
    "tv-srv": (6400, 2330),
    "tv-mrv": (8800, 2500),
    "tv-crane": (10000, 6400),
    "tv-hrv": (12500, 2500),
    "tv-tipper": (8300, 2500),
    "tv-tipper8": (9500, 2500),
    "tv-agi-mini": (7600, 2400),
    "tv-agi-6": (9400, 2500),
    "tv-agi-8": (10600, 2500),
    "tv-semi": (18900, 2500),
    "tv-truckdog": (19000, 2500),
    "tv-bdouble": (26000, 2500),
    "cr-tc-flat-50": (6000, 6000),
    "cr-tc-flat-60": (8000, 8000),
    "cr-tc-hammer-70": (8000, 8000),
    "cr-tc-luff-45": (6000, 6000),
    "cr-tc-luff-60": (10000, 10000),
    "cr-tc-self-40": (4500, 4500),
    "cr-franna-at15": (8700, 2350),
    "cr-franna-at20": (9800, 2500),
    "cr-franna-mac25": (11200, 2500),
    "cr-franna-at40": (12700, 2750),
    "cr-mc-25": (9500, 7000),
    "cr-mc-60": (11400, 8000),
    "cr-mc-100": (13600, 8600),
    "cr-mc-220": (15900, 9800),
    "cr-mc-400": (19600, 10800),
    "ac-hoist-single": (3150, 4200),
    "ac-hoist-twin": (4650, 4200),
    "ac-hoist-long": (3150, 5200),
    "ac-hoist-mat": (2850, 3000),
    "ac-sc-19": (2730, 760),
    "ac-sc-26": (3340, 810),
    "ac-sc-32": (3340, 1170),
    "ac-sc-40": (3940, 1190),
    "ac-sc-rt33": (5360, 1750),
    "ac-sc-rt43": (6380, 2290),
    "ac-mast-20": (1370, 760),
    "ac-boom-k34": (4000, 1500),
    "ac-boom-k45": (6900, 2300),
    "ac-boom-k60": (8600, 2500),
    "ac-boom-t60": (9000, 2500),
    "ac-boom-t80": (11300, 2500),
    "ac-boom-t135": (13400, 2500),
    "ac-spider-17": (4300, 4300),
    "sf-run-1200": (12000, 1200),
    "sf-run-700": (12000, 700),
    "sf-stair": (2400, 2400),
    "sf-loading": (2400, 2400),
    "sf-tower-1450": (3900, 2750),
    "sf-tower-850": (3060, 1960),
    "ss-office-6": (6000, 3000),
    "ss-office-9": (9600, 3000),
    "ss-office-12": (12000, 3300),
    "ss-office-stack": (12000, 3300),
    "ss-crib-6": (6000, 3000),
    "ss-crib-12": (12000, 3300),
    "ss-toilet-6": (6000, 3000),
    "ss-change-6": (6000, 3000),
    "ss-firstaid": (3600, 2400),
    "ss-portaloo": (1200, 1200),
    "ss-portaloo-acc": (2200, 2200),
    "ss-cont-10": (2990, 2440),
    "ss-cont-20": (6060, 2440),
    "ss-cont-40": (12190, 2440),
}

# Which overlays each true-size symbol understands: pump, tower, franna,
# mobile, vehicle, ewp (boom / spider lift), scaffold (editable run) or
# access / site (hoist, scissor, shed — none). See symbol_true_size().
SYMBOL_LIFT = {
    "cp-schwing-17": "pump",
    "cp-putz-20": "pump",
    "cp-junjin-20": "pump",
    "cp-hangil-21": "pump",
    "cp-putz-24": "pump",
    "cp-sany-25": "pump",
    "cp-junjin-25": "pump",
    "cp-putz-28": "pump",
    "cp-junjin-30": "pump",
    "cp-sany-30": "pump",
    "cp-zoomlion-32": "pump",
    "cp-putz-33": "pump",
    "cp-putz-36": "pump",
    "cp-junjin-38": "pump",
    "cp-sany-39": "pump",
    "cp-putz-42": "pump",
    "cp-sany-45": "pump",
    "cp-putz-47": "pump",
    "cp-junjin-47": "pump",
    "cp-everdigm-48": "pump",
    "cp-junjin-50": "pump",
    "cp-everdigm-50": "pump",
    "cp-everdigm-56": "pump",
    "cp-junjin-57": "pump",
    "cp-putz-58": "pump",
    "tv-b99": "vehicle",
    "tv-ute": "vehicle",
    "tv-srv": "vehicle",
    "tv-mrv": "vehicle",
    "tv-crane": "vehicle",
    "tv-hrv": "vehicle",
    "tv-tipper": "vehicle",
    "tv-tipper8": "vehicle",
    "tv-agi-mini": "vehicle",
    "tv-agi-6": "vehicle",
    "tv-agi-8": "vehicle",
    "tv-semi": "vehicle",
    "tv-truckdog": "vehicle",
    "tv-bdouble": "vehicle",
    "cr-tc-flat-50": "tower",
    "cr-tc-flat-60": "tower",
    "cr-tc-hammer-70": "tower",
    "cr-tc-luff-45": "tower",
    "cr-tc-luff-60": "tower",
    "cr-tc-self-40": "tower",
    "cr-franna-at15": "franna",
    "cr-franna-at20": "franna",
    "cr-franna-mac25": "franna",
    "cr-franna-at40": "franna",
    "cr-mc-25": "mobile",
    "cr-mc-60": "mobile",
    "cr-mc-100": "mobile",
    "cr-mc-220": "mobile",
    "cr-mc-400": "mobile",
    "ac-hoist-single": "access",
    "ac-hoist-twin": "access",
    "ac-hoist-long": "access",
    "ac-hoist-mat": "access",
    "ac-sc-19": "access",
    "ac-sc-26": "access",
    "ac-sc-32": "access",
    "ac-sc-40": "access",
    "ac-sc-rt33": "access",
    "ac-sc-rt43": "access",
    "ac-mast-20": "access",
    "ac-boom-k34": "ewp",
    "ac-boom-k45": "ewp",
    "ac-boom-k60": "ewp",
    "ac-boom-t60": "ewp",
    "ac-boom-t80": "ewp",
    "ac-boom-t135": "ewp",
    "ac-spider-17": "ewp",
    "sf-run-1200": "scaffold",
    "sf-run-700": "scaffold",
    "sf-stair": "site",
    "sf-loading": "site",
    "sf-tower-1450": "site",
    "sf-tower-850": "site",
    "ss-office-6": "site",
    "ss-office-9": "site",
    "ss-office-12": "site",
    "ss-office-stack": "site",
    "ss-crib-6": "site",
    "ss-crib-12": "site",
    "ss-toilet-6": "site",
    "ss-change-6": "site",
    "ss-firstaid": "site",
    "ss-portaloo": "site",
    "ss-portaloo-acc": "site",
    "ss-cont-10": "site",
    "ss-cont-20": "site",
    "ss-cont-40": "site",
}

# Scaffold runs: default (bays, bay length m, width m). The box is
# bays × bay length by width, drawn live by Datum from the annotation.
SYMBOL_SCAFFOLD = {
    "sf-run-1200": (5, 2.4, 1.2),
    "sf-run-700": (5, 2.4, 0.7),
}


def pixels_per_mm(scale_denominator):
    """Datum calibration value for a sheet printed at true size at 1:<N>."""
    return (PT_PER_INCH / MM_PER_INCH) / float(scale_denominator)


def _gen_id(prefix="agent"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _apply_preset(ann, preset):
    """Merge a named preset in. Anything already set on the annotation wins."""
    if not preset:
        return ann
    p = PRESETS.get(preset)
    if p is None:
        raise ValueError(f"unknown preset {preset!r}; known: {sorted(PRESETS)}")
    for k, v in p.items():
        ann.setdefault(k, v)
    ann["preset"] = preset
    return ann


class Grid:
    """A 12-column page grid, so layouts line up instead of being eyeballed.

    Every helper returns (x1, y1, x2, y2) ready to splat into a markup call:

        g = p.grid(margin=42, gutter=12)
        p.kpi(*g.cell(0, 4, top=110, height=90), ...)   # cols 0-3
        p.kpi(*g.cell(4, 4, top=110, height=90), ...)   # cols 4-7
        p.banner(*g.band(top=40, height=54), ...)       # full content width
    """

    def __init__(self, page_w, page_h, margin=42.0, gutter=12.0, columns=12):
        self.page_w, self.page_h = float(page_w), float(page_h)
        self.margin, self.gutter, self.columns = float(margin), float(gutter), int(columns)

    @property
    def content_w(self):
        return self.page_w - self.margin * 2

    @property
    def col_w(self):
        return (self.content_w - self.gutter * (self.columns - 1)) / self.columns

    def x(self, col):
        return self.margin + col * (self.col_w + self.gutter)

    def cell(self, col, span, top, height):
        """Box spanning `span` columns starting at `col` (0-based)."""
        if col < 0 or span < 1 or col + span > self.columns:
            raise ValueError(f"cell({col},{span}) falls outside {self.columns} columns")
        x1 = self.x(col)
        x2 = x1 + span * self.col_w + (span - 1) * self.gutter
        return (x1, float(top), x2, float(top) + float(height))

    def band(self, top, height):
        """Full content-width box."""
        return (self.margin, float(top), self.page_w - self.margin, float(top) + float(height))

    def row(self, count, top, height, col=0, span=None):
        """`count` equal boxes side by side. Returns a list of boxes."""
        span = span if span is not None else self.columns
        each = span // count
        if each < 1:
            raise ValueError(f"cannot fit {count} cells into {span} columns")
        return [self.cell(col + i * each, each, top, height) for i in range(count)]


class DatumProject:
    """Builds the JSON payload Datum restores on open (project version 4)."""

    def __init__(self, filename="document.pdf", page_w=595.276, page_h=841.89):
        self.filename = filename
        self.page_w, self.page_h = float(page_w), float(page_h)
        self.annotations = []
        self.takeoff_items = []
        self.takeoff_headings = []
        self.page_calibrations = {}
        self.count_groups = {}

    def grid(self, margin=42.0, gutter=12.0, columns=12):
        return Grid(self.page_w, self.page_h, margin, gutter, columns)

    # ---------- calibration ----------
    def calibrate_page(self, page, scale):
        """Calibrate one page (0-based) as 1:<scale> at true printed size."""
        self.page_calibrations[str(page)] = {
            "pixelsPerMm": pixels_per_mm(scale), "scale": f"1:{scale}"
        }

    def calibrate_all_pages(self, scale, num_pages=1):
        for p in range(num_pages):
            self.calibrate_page(p, scale)

    # ---------- internals ----------
    def _push(self, ann):
        self.annotations.append(ann)
        return ann

    def _box(self, kind, page, x1, y1, x2, y2, preset=None, **kw):
        ann = {"id": _gen_id(), "type": kind, "page": page,
               "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}], "opacity": 100}
        ann.update({k: v for k, v in kw.items() if v is not None})
        return self._push(_apply_preset(ann, preset))

    def group(self, *annotations, group_id=None):
        """Bind annotations into one object — they move, delete and re-order
        together in Datum. Give every composed card its own group; it is the
        difference between dragging one thing and dragging four."""
        gid = group_id or _gen_id("grp")
        for a in annotations:
            if isinstance(a, (list, tuple)):
                self.group(*a, group_id=gid)
            else:
                a["groupId"] = gid
        return gid

    # =====================================================================
    # REVIEW MARKUPS
    # =====================================================================
    def cloud(self, page, x1, y1, x2, y2, color=TOKENS["brand"], thickness=2):
        """Rectangular revision cloud (Datum draws the scallops itself)."""
        return self._push({
            "id": _gen_id(), "type": "cloud", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y1},
                       {"x": x2, "y": y2}, {"x": x1, "y": y2}],
            "color": color, "thickness": thickness, "opacity": 100})

    def text(self, page, x, y, text, color=None, font_size=12, bold=False,
             preset=None, width=None, height=None, align=None, valign=None,
             text_color=None, box_fill=None, box_stroke=None, radius=None,
             pad=None, italic=False, underline=False, rotation=None,
             shadow=None, font_family=None):
        """Free text. Anchored TOP-LEFT at (x, y).

        `align` / `valign` position the text inside the box — they only bite
        when `width` / `height` are given, since otherwise the box hugs
        the text. Both were unusable before Datum v3.22.
        """
        ann = {"id": _gen_id(), "type": "text", "page": page,
               "points": [{"x": x, "y": y}], "text": text,
               "fontSize": font_size, "fontFamily": font_family or FONT,
               "fontWeight": "700" if bold else "400",
               "fontStyle": "italic" if italic else "normal",
               "textDecoration": "underline" if underline else "none",
               "opacity": 100}
        for k, v in (("color", color), ("textColor", text_color),
                     ("boxW", width), ("boxH", height),
                     ("textAlign", align), ("vAlign", valign),
                     ("boxFill", box_fill), ("boxStroke", box_stroke),
                     ("radius", radius), ("boxPad", pad),
                     ("rotation", rotation), ("shadow", shadow)):
            if v is not None:
                ann[k] = v
        return self._push(_apply_preset(ann, preset))

    def rectangle(self, page, x1, y1, x2, y2, color=TOKENS["info"], fill=None,
                  fill_opacity=10, thickness=2, dashed=False, subject="",
                  radius=None, preset=None, hatch=None, hatch_spacing=None,
                  hatch_angle=None, gradient_to=None, gradient_angle=None,
                  shadow=None, stroke_side=None, rotation=None):
        """Box. thickness=0 means no border at all (fill-only card)."""
        return self._box(
            "rectangle", page, x1, y1, x2, y2, preset=preset,
            color=color, fillColor=(fill if fill is not None else color),
            fillOpacity=fill_opacity, thickness=thickness,
            lineStyle="dashed" if dashed else "solid",
            hatch=hatch or "none", subject=subject, radius=radius,
            hatchSpacing=hatch_spacing, hatchAngle=hatch_angle,
            fillColor2=gradient_to, gradientAngle=gradient_angle,
            shadow=shadow, strokeSide=stroke_side, rotation=rotation)

    def ellipse(self, page, x1, y1, x2, y2, color=TOKENS["info"], fill=None,
                fill_opacity=10, thickness=2, hatch=None, preset=None):
        return self._box("ellipse", page, x1, y1, x2, y2, preset=preset,
                         color=color, fillColor=fill, fillOpacity=fill_opacity,
                         thickness=thickness, hatch=hatch or "none")

    def line(self, page, x1, y1, x2, y2, color=TOKENS["brand"], thickness=2,
             dashed=False, cap=None):
        return self._push({
            "id": _gen_id(), "type": "line", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "color": color, "thickness": thickness, "opacity": 100,
            "lineStyle": "dashed" if dashed else "solid",
            **({"lineCap": cap} if cap else {})})

    def polygon(self, page, points, color=TOKENS["info"], fill=None,
                fill_opacity=15, thickness=2, hatch=None):
        return self._push({
            "id": _gen_id(), "type": "polygon", "page": page,
            "points": [{"x": x, "y": y} for x, y in points],
            "color": color, "fillColor": fill or color,
            "fillOpacity": fill_opacity, "thickness": thickness,
            "opacity": 100, "hatch": hatch or "none"})

    def polyline(self, page, points, color=TOKENS["brand"], thickness=2, dashed=False):
        """Connected lines with NO measurement label (a plain shape)."""
        return self._push({
            "id": _gen_id(), "type": "polyline", "page": page,
            "points": [{"x": x, "y": y} for x, y in points],
            "label": "", "measLabel": "", "isShape": True, "hideLabel": True,
            "color": color, "thickness": thickness, "opacity": 100,
            "lineStyle": "dashed" if dashed else "solid"})

    def arrow(self, page, x1, y1, x2, y2, color=TOKENS["brand"], thickness=2.5,
              head="triangle", tail=None, head_scale=None, cap=None):
        """Arrow FROM (x1,y1) TO (x2,y2) — the head lands on the 2nd point.
        head/tail: triangle | open | dot | bar | none."""
        return self._push({
            "id": _gen_id(), "type": "arrow", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "color": color, "fillColor": "transparent",
            "thickness": thickness, "opacity": 100, "lineStyle": "solid",
            "arrowHead": head,
            **({"arrowTail": tail} if tail else {}),
            **({"arrowScale": head_scale} if head_scale else {}),
            **({"lineCap": cap} if cap else {})})

    def highlight(self, page, x1, y1, x2, y2, color="#fbbf24", fill_opacity=40):
        return self._box("highlight", page, x1, y1, x2, y2, color=color,
                         fillColor=color, fillOpacity=fill_opacity,
                         thickness=1, lineStyle="solid", hatch="none", subject="")

    def stamp(self, page, x, y, text, color=TOKENS["brand"], scale=1.2, opacity=85):
        """Stamp is CENTRE-anchored on (x, y)."""
        return self._push({
            "id": _gen_id(), "type": "stamp", "page": page,
            "points": [{"x": x, "y": y}], "text": text,
            "stampColor": color, "color": color,
            "stampScale": scale, "opacity": opacity})

    def callout(self, page, anchor, text_pos, text, knees=None, color=TOKENS["brand"],
                font_size=10, fill="#FFFFFF", width=None, height=None,
                radius=None, pad=None, align=None, preset=None):
        """Leader line + boxed text. `anchor` is the point being pointed AT
        (the arrow head lands there); `text_pos` is the text box's top-left.
        `knees` bends the leader: [(x, y), ...]."""
        ann = {"id": _gen_id(), "type": "callout", "page": page,
               "points": [{"x": anchor[0], "y": anchor[1]}],
               "anchor": {"x": anchor[0], "y": anchor[1]},
               "textPos": {"x": text_pos[0], "y": text_pos[1]},
               "knees": [{"x": x, "y": y} for x, y in (knees or [])],
               "text": text, "color": color, "fillColor": fill,
               "fontSize": font_size, "fontFamily": FONT, "thickness": 1,
               "opacity": 100}
        for k, v in (("boxW", width), ("boxH", height), ("radius", radius),
                     ("boxPad", pad), ("textAlign", align)):
            if v is not None:
                ann[k] = v
        return self._push(_apply_preset(ann, preset))

    def tick(self, page, x, y, color=TOKENS["ok"], size=24, thickness=4):
        return self._push({
            "id": _gen_id(), "type": "tick", "page": page,
            "points": [{"x": x, "y": y}], "color": color,
            "tickSize": size, "thickness": thickness, "opacity": 100})

    def symbol(self, page, x1, y1, x2, y2, symbol_id, color="#111111", thickness=2,
               rotation=None):
        """One of Datum's symbols in an explicit box — see
        references/symbols.md for every id. The box must keep the symbol's
        own proportions (SYMBOL_SIZES) or the artwork draws stretched;
        symbol_at() is the safer call."""
        if symbol_id not in SYMBOL_SIZES:
            raise ValueError(f"Unknown Datum symbol id {symbol_id!r} — "
                             "see references/symbols.md")
        return self._box("symbol", page, x1, y1, x2, y2,
                         symbolId=symbol_id, color=color, thickness=thickness,
                         rotation=rotation)

    def symbol_at(self, page, cx, cy, symbol_id, width=None, color="#111111",
                  thickness=2, rotation=None):
        """Place a symbol centred on (cx, cy) at its true proportions.
        width defaults to Datum's own placement size; the height always
        follows from the symbol's shape, exactly as a click in Datum does."""
        if symbol_id not in SYMBOL_SIZES:
            raise ValueError(f"Unknown Datum symbol id {symbol_id!r} — "
                             "see references/symbols.md")
        dw, dh = SYMBOL_SIZES[symbol_id]
        w = float(width) if width else dw
        h = w * dh / dw
        return self.symbol(page, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2,
                           symbol_id, color=color, thickness=thickness,
                           rotation=rotation)

    def symbol_true_size(self, page, cx, cy, symbol_id, scale=None, rotation=None,
                         color="#111111", thickness=2, show_reach=None, rings=None,
                         jib=None, cj=None, parked=None, tail=None, show_vane=None,
                         show_turn=None, turn_right=None, bays=None, bay_length=None,
                         width=None):
        """Place a true-size symbol — concrete pump (cp-*), truck (tv-*) or
        crane (cr-*), hoist or EWP (ac-*), scaffold (sf-*) or site shed (ss-*) —
        centred on (cx, cy) at its REAL footprint.

        The box comes from SYMBOL_REAL × the page's pixelsPerMm, so call
        calibrate_page() first or pass scale=<N> for 1:N. At rotation 0 the
        cab / boom / jib points to +x; rotation is degrees clockwise. A tower
        crane's box is its base — the jib is drawn out along +x at `jib` m.

        Overlays (each is also editable afterwards in Datum's Properties):
          show_reach, rings=[(radius_m, "label"), ...]  pumps, cranes, boom / spider lifts
          jib, cj (counter-jib / tail), parked (luffer)  tower cranes, metres
          show_vane   tower: weathervane zone · mobile: tail-swing circle
          tail        mobile crane tail-swing radius, metres
          show_turn, turn_right                          trucks
          bays, bay_length (2.4/1.8/1.2/0.7), width (1.2/0.7)  scaffold runs
        Default ring capacities are typical for the class, not a load chart —
        pass the real crane's radii and capacities in `rings` when known.
        """
        if symbol_id not in SYMBOL_REAL:
            raise ValueError(f"{symbol_id!r} is not a true-size symbol — use symbol_at(); "
                             "true-size ids are cp-*, tv-*, cr-*, ac-*, sf-* and ss-* (references/symbols.md)")
        if scale:
            ppm = pixels_per_mm(scale)
        else:
            cal = self.page_calibrations.get(str(page))
            if not cal:
                raise ValueError(f"Page {page} isn't calibrated — call calibrate_page({page}, N) "
                                 "or pass scale=N so the symbol can be placed at true size")
            ppm = cal["pixelsPerMm"]
        kind = SYMBOL_LIFT[symbol_id]
        lift = {"showReach": show_reach, "jib": jib, "cj": cj, "parked": parked,
                "tail": tail, "showVane": show_vane, "showTurn": show_turn,
                "turnRight": turn_right, "bays": bays, "bayL": bay_length,
                "sfW": width}
        allowed = {"pump": {"showReach"},
                   "tower": {"showReach", "jib", "cj", "parked", "showVane"},
                   "franna": {"showReach"},
                   "mobile": {"showReach", "tail", "showVane"},
                   "vehicle": {"showTurn", "turnRight"},
                   "ewp": {"showReach"},
                   "access": set(),
                   "site": set(),
                   "scaffold": {"bays", "bayL", "sfW"}}[kind]
        if rings is not None and kind not in ("pump", "tower", "franna", "mobile", "ewp"):
            raise ValueError(f"{symbol_id!r} has no reach chart")
        bad = [k for k, v in lift.items() if v is not None and k not in allowed]
        if bad:
            raise ValueError(f"{symbol_id!r} ({kind}) doesn't take {', '.join(bad)}")
        rw, rh = SYMBOL_REAL[symbol_id]
        if kind == "scaffold":
            n0, l0, w0 = SYMBOL_SCAFFOLD[symbol_id]
            n = max(1, int(round(bays or n0)))
            rw, rh = n * float(bay_length or l0) * 1000, float(width or w0) * 1000
            if bays is not None:
                lift["bays"] = n
        w, h = rw * ppm, rh * ppm
        ann = self.symbol(page, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2,
                          symbol_id, color=color, thickness=thickness, rotation=rotation)
        for k, v in lift.items():
            if v is not None:
                ann[k] = (bool(v) if k in ("showReach", "showVane", "showTurn", "turnRight")
                          else int(v) if k == "bays" else float(v))
        if rings is not None:
            ann["rings"] = [{"r": float(r), "t": str(t)} for r, t in rings]
            if show_reach is None:
                ann["showReach"] = True
        return ann

    def cutcontent(self, page, x1, y1, x2, y2):
        """White-out a region of the underlying PDF — replace, not just overlay."""
        return self._box("cutcontent", page, x1, y1, x2, y2, color="#ffffff")

    def table(self, page, x, y, columns, rows, title=None, title_bg=None,
              header_bg="#e9edf2", border="#333333", grid="#b8bec8",
              bg="#ffffff", font_size=9, scale=1.0):
        """A real data table.

        columns: [{"label": "Package", "align": "left"},
                  {"label": "Status", "type": "colour", "align": "center"}]
        rows:    [[{"text": "Structure"}, {"color": "#16A34A", "text": "On track"}], ...]

        A cell takes text, fill, bold, textColor; a 'colour' column's cell
        takes color (the swatch) and optional text drawn over it.
        """
        ann = {"id": _gen_id(), "type": "table", "page": page,
               "points": [{"x": x, "y": y}], "cols": columns, "rows": rows,
               "headerBg": header_bg, "borderColor": border, "gridColor": grid,
               "bgColor": bg, "fontSize": font_size, "legendScale": scale,
               "showGrid": True, "opacity": 100}
        if title:
            ann["title"] = title
            ann["titleBg"] = title_bg or TOKENS["navy"]
        return self._push(ann)

    def legend(self, page, x, y, mode="summary", scope="doc", show_rates=True, scale=1.0):
        """Auto-generated takeoff key/BOQ table, live-linked to the items.
        mode: simple | summary | detailed.  scope: doc | page."""
        return self._push({
            "id": _gen_id(), "type": "legend", "page": page,
            "points": [{"x": x, "y": y}], "legendMode": mode,
            "legendScope": scope, "showRates": show_rates,
            "legendScale": scale, "opacity": 100})

    # =====================================================================
    # PRESENTATION MARKUPS (Datum v3.22)
    # =====================================================================
    def chip(self, page, x1, y1, x2, y2, text, preset="chip-neutral",
             fill=None, text_color=None, font_size=None, radius=None):
        """Rounded pill label — status tags, trade tags, "REV C"."""
        return self._box("chip", page, x1, y1, x2, y2, preset=preset,
                         text=text, fillColor=fill, textColor=text_color,
                         fontSize=font_size, radius=radius)

    def badge(self, page, x, y, label, size=22, fill=None, text_color="#FFFFFF",
              border="#FFFFFF", thickness=2):
        """Numbered step circle, CENTRE-anchored. Unlike count(), a badge is
        pure annotation and never touches the workbook."""
        return self._push({
            "id": _gen_id(), "type": "badge", "page": page,
            "points": [{"x": x, "y": y}], "text": str(label),
            "badgeSize": size, "fillColor": fill or TOKENS["brand"],
            "textColor": text_color, "borderColor": border,
            "thickness": thickness, "opacity": 100})

    def divider(self, page, x1, y1, x2, y2, text="", align="center",
                preset="divider-soft", color=None, text_color=None):
        """Horizontal rule, optionally broken by a label."""
        return self._box("divider", page, x1, y1, x2, y2, preset=preset,
                         text=text, labelAlign=align, color=color,
                         textColor=text_color)

    def banner(self, page, x1, y1, x2, y2, title, subtitle="",
               preset="banner-brand", fill=None, gradient_to=None,
               text_color=None, accent=None, accent_width=None,
               align=None, radius=None, font_size=None):
        """Page / section header band."""
        return self._box("banner", page, x1, y1, x2, y2, preset=preset,
                         title=title, subtitle=subtitle, fillColor=fill,
                         fillColor2=gradient_to, textColor=text_color,
                         accentColor=accent, accentWidth=accent_width,
                         textAlign=align, radius=radius, fontSize=font_size)

    def quote(self, page, x1, y1, x2, y2, text, attribution="",
              preset="quote-finding", accent=None, fill=None,
              text_color=None, font_size=None, pad=None):
        """Accent-bar panel for a finding or recommendation. Text wraps."""
        return self._box("quote", page, x1, y1, x2, y2, preset=preset,
                         text=text, attribution=attribution,
                         accentColor=accent, fillColor=fill,
                         textColor=text_color, fontSize=font_size, boxPad=pad)

    def kpi(self, page, x1, y1, x2, y2, value, caption="", delta=None,
            direction="flat", preset="kpi", accent=None, accent_width=None,
            fill=None, text_color=None, value_size=None, caption_size=None,
            caption_top=False, shadow=None):
        """Stat tile: big value, caption, optional delta.
        direction: up | down | flat (drives the arrow glyph and its colour)."""
        return self._box("kpi", page, x1, y1, x2, y2, preset=preset,
                         value=value, caption=caption, delta=delta,
                         deltaDirection=direction, accent=accent,
                         accentWidth=accent_width, fillColor=fill,
                         textColor=text_color, valueSize=value_size,
                         captionSize=caption_size, shadow=shadow,
                         captionPosition="top" if caption_top else None)

    def chevron(self, page, x1, y1, x2, y2, stages, current=-1,
                active=None, base=None, text_color=None, font_size=None):
        """Process / stage band. `stages` is a list of labels (or dicts with
        label / color / active). `current` highlights stages 0..current."""
        segs = [{"label": s} if isinstance(s, str) else dict(s) for s in stages]
        return self._box("chevron", page, x1, y1, x2, y2,
                         segments=segs, current=current, activeColor=active,
                         fillColor=base, textColor=text_color,
                         fontSize=font_size, thickness=0)

    def timeline(self, page, x1, y1, x2, y2, milestones, color=None,
                 done_color=None, current_color=None, font_size=None, thickness=2):
        """Milestone bar. Each milestone is a dict:
        {"label": "PC", "date": "30 Nov 26", "state": "done|current|todo",
         "at": 0.0-1.0}   — `at` is optional; milestones space evenly without it.

        Labels are centred on their dot, so leave a little margin at each end
        or the first/last label will overhang the box.
        """
        ms = []
        for m in milestones:
            d = dict(m)
            d.setdefault("state", "todo")
            ms.append(d)
        return self._box("timeline", page, x1, y1, x2, y2,
                         milestones=ms, color=color, doneColor=done_color,
                         currentColor=current_color, fontSize=font_size,
                         thickness=thickness)

    def bracket(self, page, x1, y1, x2, y2, text="", orientation="top",
                color=None, thickness=1.5, label_background="#FFFFFF"):
        """Span marker. orientation: top | bottom | left | right.
        Pass label_background=False for no backing plate behind the label."""
        return self._box("bracket", page, x1, y1, x2, y2, text=text,
                         orientation=orientation, color=color or TOKENS["muted"],
                         thickness=thickness, labelBackground=label_background)

    def progress(self, page, x1, y1, x2, y2, value, bar_color=None,
                 track=None, show_value=True, value_label=None, radius=None):
        """Percentage bar. value is 0-100 and is clamped."""
        return self._box("progress", page, x1, y1, x2, y2,
                         value=value, barColor=bar_color or TOKENS["ok"],
                         fillColor=track, showValue=show_value,
                         valueLabel=value_label, radius=radius, thickness=0)

    def chart(self, page, x1, y1, x2, y2, data, kind="bar", title=None,
              palette=None, show_values=True, show_labels=True,
              center_label=None, area_fill=False, fill=None, max_value=None):
        """Bar | line | donut | pie from an inline series.

        data: [{"label": "Structure", "value": 1240, "color": "#..."}, ...]
        `color` per point is optional — the palette cycles otherwise.
        """
        pts = []
        for d in data:
            pts.append(dict(d) if isinstance(d, dict)
                       else {"label": str(d[0]), "value": float(d[1])})
        return self._box("chart", page, x1, y1, x2, y2,
                         chartType=kind, data=pts, title=title,
                         palette=palette, showValues=show_values,
                         showLabels=show_labels, centerLabel=center_label,
                         areaFill=area_fill, fillColor=fill,
                         maxValue=max_value, thickness=0)

    # =====================================================================
    # TAKEOFF / BOQ
    # =====================================================================
    def boq_heading(self, name):
        if name and name not in self.takeoff_headings:
            self.takeoff_headings.append(name)

    def boq_item(self, name, result_type, trade="", rate=0, factor=0,
                 color=TOKENS["brand"]):
        """Measured BOQ line. result_type: length | area | count |
        vertical (m² = length x factor-mm height) | volume (m³ = area x factor-mm depth).
        Datum computes qty LIVE from the shapes tagged to this item."""
        item = {"id": _gen_id("item"), "name": name, "resultType": result_type,
                "color": color, "trade": trade, "rate": rate,
                "factor": factor, "markup": 0}
        self.takeoff_items.append(item)
        self.boq_heading(trade)
        return item

    def boq_manual(self, name, qty, unit, rate, trade=""):
        """Un-measured line (prelims, allowances, PC sums)."""
        item = {"id": _gen_id("item"), "name": name, "manual": True,
                "manualQty": qty, "unit": unit, "color": TOKENS["muted"],
                "trade": trade, "rate": rate, "markup": 0}
        self.takeoff_items.append(item)
        self.boq_heading(trade)
        return item

    def measure(self, page, x1, y1, x2, y2, item=None, deduction=False):
        """Measured line — tag to a length/vertical item for the BOQ."""
        return self._push({
            "id": _gen_id(), "type": "measure", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "label": "", "measLabel": "",
            "color": (item or {}).get("color", TOKENS["brand"]),
            "thickness": 2, "opacity": 100, "lineStyle": "solid",
            **({"takeoffItemId": item["id"], "isDeduction": deduction} if item else {})})

    def area(self, page, points, item=None, fill_opacity=18, deduction=False,
             hatch=None):
        """Measured area polygon; points = [(x, y), ...] in order."""
        color = (item or {}).get("color", TOKENS["info"])
        return self._push({
            "id": _gen_id(), "type": "area", "page": page,
            "points": [{"x": x, "y": y} for x, y in points],
            "label": "", "perimLabel": "", "measLabel": "",
            "color": color, "fillColor": color, "fillOpacity": fill_opacity,
            "thickness": 1.5, "opacity": 100, "hatch": hatch or "none",
            **({"takeoffItemId": item["id"], "isDeduction": deduction} if item else {})})

    def count(self, page, x, y, group, item=None):
        """Numbered count marker. Numbers auto-increment within the group."""
        grp = self.count_groups.setdefault(
            group, {"count": 0, "color": (item or {}).get("color", TOKENS["brand"])})
        grp["count"] += 1
        return self._push({
            "id": _gen_id(), "type": "count", "page": page,
            "points": [{"x": x, "y": y}], "group": group,
            "number": grp["count"], "color": grp["color"],
            **({"takeoffItemId": item["id"]} if item else {})})

    # ---------- payload ----------
    def to_payload(self):
        cal_keys = list(self.page_calibrations.keys())
        return {
            "version": 4,
            "filename": self.filename,
            "annotations": self.annotations,
            "pageCalibrations": self.page_calibrations,
            "defaultCalibration": (self.page_calibrations[cal_keys[0]]
                                   if cal_keys else None),
            "countGroups": self.count_groups,
            "measurements": [],
            "takeoffItems": self.takeoff_items,
            "takeoffZones": [],
            "takeoffHeadings": self.takeoff_headings,
            "viewports": [],
            "savedAt": "",
        }

    # ---------- self-verification ----------
    def verify(self, pages=None, strict=True):
        """Check the payload before delivering. Returns a list of problems
        (empty = clean). Run this every time — a markup off the page, or a
        type Datum doesn't know, is invisible rather than obviously wrong.

        pages: {page_index: (width, height)} to bounds-check against. Omit to
        check every page against this project's page_w / page_h.
        """
        problems = []
        seen = set()
        item_ids = {i["id"] for i in self.takeoff_items}
        compatible = {"measure": {"length", "vertical"}, "polyline": {"length", "vertical"},
                      "dimension": {"length", "vertical"}, "area": {"area", "volume"},
                      "count": {"count"}}
        measured_pages = set()

        for a in self.annotations:
            aid = a.get("id")
            if not aid:
                problems.append("annotation with no id")
            elif aid in seen:
                problems.append(f"duplicate id {aid}")
            seen.add(aid)

            t = a.get("type")
            if t not in VALID_TYPES:
                problems.append(f"{aid}: unknown type {t!r} — Datum draws a placeholder box")

            pg = a.get("page")
            if not isinstance(pg, int) or pg < 0:
                problems.append(f"{aid}: page must be a 0-based int, got {pg!r}")
            else:
                w, h = (pages or {}).get(pg, (self.page_w, self.page_h))
                for p in a.get("points", []) + [a.get("anchor"), a.get("textPos")]:
                    if not p:
                        continue
                    if not (-1 <= p["x"] <= w + 1) or not (-1 <= p["y"] <= h + 1):
                        problems.append(
                            f"{aid}: point ({p['x']:.0f},{p['y']:.0f}) is off a "
                            f"{w:.0f}x{h:.0f} page")
                        break

            if t in BOX2_TYPES and len(a.get("points", [])) != 2:
                problems.append(f"{aid}: {t} needs exactly 2 points")

            tid = a.get("takeoffItemId")
            if tid:
                if tid not in item_ids:
                    problems.append(f"{aid}: takeoffItemId {tid} has no matching item")
                else:
                    rt = next(i["resultType"] for i in self.takeoff_items if i["id"] == tid)
                    ok = compatible.get(t, set())
                    if ok and rt not in ok:
                        problems.append(f"{aid}: {t} cannot feed a '{rt}' item")
                if isinstance(pg, int):
                    measured_pages.add(pg)

            if a.get("boxFill") is True or a.get("labelBackground") is True:
                problems.append(f"{aid}: boxFill/labelBackground must be a colour "
                                f"STRING or False, never True")

        for pg in sorted(measured_pages):
            if str(pg) not in self.page_calibrations:
                problems.append(f"page {pg} has measured shapes but no calibration "
                                f"(quantities will read 'Not calibrated')")

        if strict and problems:
            raise ValueError("Datum payload problems:\n  - " + "\n  - ".join(problems))
        return problems


def embed(source_pdf, project, output_pdf=None):
    """Embed the project into the PDF's Info dict. Returns the output bytes.

    source_pdf: path or bytes of the ORIGINAL (clean) PDF.
    project: DatumProject instance or a plain payload dict.
    """
    from pypdf import PdfReader, PdfWriter
    import io

    if isinstance(source_pdf, (bytes, bytearray)):
        reader = PdfReader(io.BytesIO(bytes(source_pdf)))
    else:
        reader = PdfReader(source_pdf)

    payload = project.to_payload() if hasattr(project, "to_payload") else project
    b64 = base64.b64encode(
        json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")

    writer = PdfWriter()
    writer.append(reader)
    # Keep whatever metadata the source had, then add Datum's keys.
    meta = {}
    try:
        if reader.metadata:
            for k, v in reader.metadata.items():
                if isinstance(v, str):
                    meta[k] = v
    except Exception:
        pass
    meta["/BDMMarkupData"] = b64
    meta["/BDMVersion"] = "4"
    meta["/BDMBakedOverlay"] = "0"
    writer.add_metadata(meta)

    buf = io.BytesIO()
    writer.write(buf)
    out = buf.getvalue()
    if output_pdf:
        with open(output_pdf, "wb") as f:
            f.write(out)
    return out


def bake(pdf_path, output_pdf=None, app=None, timeout=600):
    """Run Datum's own Save on an embedded PDF so the markups show in Adobe,
    Chrome and every other viewer — not just in Datum.

    embed() only writes the editable project, so other viewers show the clean
    drawing. This opens the file in the real Datum app (headless Chromium via
    datum-bake.js) and saves it exactly as Ctrl+S would: markups painted onto
    the pages, clean original and live project kept inside, still fully
    editable on reopen.

    Needs node + Playwright (`npm install playwright`, and a browser:
    `npx playwright install chromium`, or an installed Chrome/Edge).
    app: path or URL of BDM-PDF-Markup-Tool.html (default $DATUM_APP, else
    the live site).

    Returns (True, message) when baked and verified, (False, reason) when not
    — the file is then left exactly as embed() wrote it, so tell the reader
    to open it in Datum and Save before sending it on.
    """
    import os
    import shutil
    import subprocess
    node = shutil.which("node")
    if not node:
        return False, "node is not installed"
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datum-bake.js")
    cmd = [node, script, str(pdf_path)]
    if output_pdf:
        cmd += ["-o", str(output_pdf)]
    if app:
        cmd += ["--app", str(app)]
    cmd += ["--timeout", str(timeout)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 60)
    except subprocess.TimeoutExpired:
        return False, "datum-bake timed out"
    msg = (r.stdout + r.stderr).strip()
    return r.returncode == 0, msg


def page_sizes(source_pdf):
    """{page_index: (width_pt, height_pt)} as Datum will see them, i.e. with
    /Rotate 90/270 already swapped. Use this before placing anything."""
    from pypdf import PdfReader
    import io
    reader = (PdfReader(io.BytesIO(bytes(source_pdf)))
              if isinstance(source_pdf, (bytes, bytearray)) else PdfReader(source_pdf))
    out = {}
    for i, pg in enumerate(reader.pages):
        w = float(pg.mediabox.width)
        h = float(pg.mediabox.height)
        rot = (pg.get("/Rotate") or 0) % 360
        out[i] = (h, w) if rot in (90, 270) else (w, h)
    return out


def _main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit("usage: datum_markup.py <source.pdf> <project.json> <output.pdf>")
    with open(sys.argv[2]) as f:
        payload = json.load(f)
    embed(sys.argv[1], payload, sys.argv[3])
    print(f"wrote {sys.argv[3]} with {len(payload.get('annotations', []))} markups "
          f"and {len(payload.get('takeoffItems', []))} BOQ items")


if __name__ == "__main__":
    _main()
