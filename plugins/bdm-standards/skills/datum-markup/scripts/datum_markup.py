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

    def symbol(self, page, x1, y1, x2, y2, symbol_id, color="#111111", thickness=2):
        """One of Datum's 104 construction symbols. Common ids: g-north,
        g-section, g-detail, g-elevation, g-level, g-grid, g-rev, g-keynote."""
        return self._box("symbol", page, x1, y1, x2, y2,
                         symbolId=symbol_id, color=color, thickness=thickness)

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
