#!/usr/bin/env python3
"""
datum_markup.py — write editable Datum markups / measurements / priced BOQ
takeoffs directly into a PDF, no Datum UI involved.

Datum (BDM PDF Markup Tool) stores its whole editable project as JSON,
base64-encoded, inside the PDF's Info dictionary under the key
/BDMMarkupData. When Datum opens a PDF carrying that key, every markup,
measurement and takeoff item is restored fully live and editable.

Usage as a library:

    from datum_markup import DatumProject, embed

    p = DatumProject("My Drawing.pdf")
    p.calibrate_all_pages(scale=100)                      # sheet is 1:100 true size
    p.cloud(page=0, x1=50, y1=100, x2=300, y2=160)
    p.text(page=0, x=50, y=170, text="Check this detail")
    item = p.boq_item("External walls 190 blk", "vertical", trade="Masonry",
                      rate=285, factor=2700)
    p.measure(page=0, x1=100, y1=200, x2=400, y2=200, item=item)
    out_bytes = embed("source.pdf", p)
    open("marked-up.pdf", "wb").write(out_bytes)

Or from the command line with a JSON project file:

    python3 datum_markup.py source.pdf project.json output.pdf

Coordinates: PDF points (1/72 inch) at 1:1, origin at the page's TOP-LEFT,
y increasing DOWNWARD. (This is pdf.js viewport space, NOT the PDF-native
bottom-left space. If you computed positions bottom-left, convert with
y_datum = page_height - y_pdf.)

Requires: pypdf  (pip install pypdf). Any 3.x / 4.x / 5.x works.
"""
import base64
import json
import sys
import uuid

MM_PER_INCH = 25.4
PT_PER_INCH = 72.0


def pixels_per_mm(scale_denominator):
    """Datum calibration value for a sheet printed at true size at 1:<N>."""
    return (PT_PER_INCH / MM_PER_INCH) / float(scale_denominator)


def _gen_id(prefix="agent"):
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


class DatumProject:
    """Builds the JSON payload Datum restores on open (project version 4)."""

    def __init__(self, filename="document.pdf"):
        self.filename = filename
        self.annotations = []
        self.takeoff_items = []
        self.takeoff_headings = []
        self.page_calibrations = {}
        self.count_groups = {}

    # ---------- calibration ----------
    def calibrate_page(self, page, scale):
        """Calibrate one page (0-based) as 1:<scale> at true printed size."""
        self.page_calibrations[str(page)] = {
            "pixelsPerMm": pixels_per_mm(scale), "scale": f"1:{scale}"
        }

    def calibrate_all_pages(self, scale, num_pages=1):
        for p in range(num_pages):
            self.calibrate_page(p, scale)

    # ---------- plain markups ----------
    def _push(self, ann):
        self.annotations.append(ann)
        return ann

    def cloud(self, page, x1, y1, x2, y2, color="#E5432E", thickness=2):
        """Rectangular revision cloud (Datum draws the scallops itself)."""
        return self._push({
            "id": _gen_id(), "type": "cloud", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y1},
                       {"x": x2, "y": y2}, {"x": x1, "y": y2}],
            "color": color, "thickness": thickness, "opacity": 100})

    def text(self, page, x, y, text, color="#E5432E", font_size=12, bold=False):
        return self._push({
            "id": _gen_id(), "type": "text", "page": page,
            "points": [{"x": x, "y": y}], "text": text,
            "color": color, "fontSize": font_size, "fontFamily": "Arial",
            "fontWeight": "700" if bold else "400", "fontStyle": "normal",
            "textDecoration": "none", "opacity": 100})

    def rectangle(self, page, x1, y1, x2, y2, color="#4F8EF7", fill_opacity=10,
                  thickness=2, dashed=False, subject=""):
        return self._push({
            "id": _gen_id(), "type": "rectangle", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "color": color, "fillColor": color, "fillOpacity": fill_opacity,
            "thickness": thickness, "opacity": 100,
            "lineStyle": "dashed" if dashed else "solid",
            "hatch": "none", "subject": subject})

    def arrow(self, page, x1, y1, x2, y2, color="#28a745", thickness=2.5):
        """Arrow FROM (x1,y1) TO (x2,y2) — the head lands on the 2nd point."""
        return self._push({
            "id": _gen_id(), "type": "arrow", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "color": color, "fillColor": "transparent", "fillOpacity": 20,
            "thickness": thickness, "opacity": 100, "lineStyle": "solid",
            "hatch": "none", "subject": ""})

    def highlight(self, page, x1, y1, x2, y2, color="#fbbf24", fill_opacity=40):
        return self._push({
            "id": _gen_id(), "type": "highlight", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "color": color, "fillColor": color, "fillOpacity": fill_opacity,
            "thickness": 1, "opacity": 100, "lineStyle": "solid",
            "hatch": "none", "subject": ""})

    def stamp(self, page, x, y, text, color="#E5432E", scale=1.2, opacity=85):
        """Stamp is CENTRE-anchored on (x, y)."""
        return self._push({
            "id": _gen_id(), "type": "stamp", "page": page,
            "points": [{"x": x, "y": y}], "text": text,
            "stampColor": color, "color": color,
            "stampScale": scale, "opacity": opacity})

    # ---------- takeoff / BOQ ----------
    def boq_heading(self, name):
        if name not in self.takeoff_headings:
            self.takeoff_headings.append(name)

    def boq_item(self, name, result_type, trade="", rate=0, factor=0,
                 color="#E5432E"):
        """Measured BOQ line. result_type: length | area | count |
        vertical (m² = length x factor-mm height) | volume (m³ = area x factor-mm depth).
        Datum computes qty LIVE from the shapes tagged to this item."""
        item = {"id": _gen_id("item"), "name": name, "resultType": result_type,
                "color": color, "trade": trade, "rate": rate,
                "factor": factor, "markup": 0}
        self.takeoff_items.append(item)
        self.boq_heading(trade) if trade else None
        return item

    def boq_manual(self, name, qty, unit, rate, trade=""):
        """Un-measured line (prelims, allowances, PC sums)."""
        item = {"id": _gen_id("item"), "name": name, "manual": True,
                "manualQty": qty, "unit": unit, "color": "#64748B",
                "trade": trade, "rate": rate, "markup": 0}
        self.takeoff_items.append(item)
        self.boq_heading(trade) if trade else None
        return item

    def measure(self, page, x1, y1, x2, y2, item=None, deduction=False):
        """Measured line — tag to a length/vertical item for the BOQ."""
        return self._push({
            "id": _gen_id(), "type": "measure", "page": page,
            "points": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            "label": "", "measLabel": "",
            "color": (item or {}).get("color", "#E5432E"),
            "thickness": 2, "opacity": 100, "lineStyle": "solid",
            **({"takeoffItemId": item["id"], "isDeduction": deduction} if item else {})})

    def area(self, page, points, item=None, fill_opacity=18, deduction=False):
        """Measured area polygon; points = [(x, y), ...] in order."""
        color = (item or {}).get("color", "#4F8EF7")
        return self._push({
            "id": _gen_id(), "type": "area", "page": page,
            "points": [{"x": x, "y": y} for x, y in points],
            "label": "", "perimLabel": "", "measLabel": "",
            "color": color, "fillColor": color, "fillOpacity": fill_opacity,
            "thickness": 1.5, "opacity": 100, "hatch": "none",
            **({"takeoffItemId": item["id"], "isDeduction": deduction} if item else {})})

    def count(self, page, x, y, group, item=None):
        """Numbered count marker. Numbers auto-increment within the group."""
        grp = self.count_groups.setdefault(
            group, {"count": 0, "color": (item or {}).get("color", "#E5432E")})
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
