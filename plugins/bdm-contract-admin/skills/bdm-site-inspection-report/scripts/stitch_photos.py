#!/usr/bin/env python3
"""
Stitch photos out of a OneNote 'Export to PDF' site-inspection file.

WHY THIS EXISTS
---------------
When a OneNote page is exported to PDF, each embedded photo is sliced into
2 (sometimes more) horizontal strips stacked down the page. pdfimages pulls
out the strips, not the whole photo. This script regroups the strips by page
and stacks them back into one image per page.

USAGE
-----
    python3 stitch_photos.py "/path/to/onenote_export.pdf" /path/to/out_dir
Produces out_dir/photo1.jpg, photo2.jpg, ... (one per PDF page that has images),
resized to max 1100px wide, JPEG q85.
"""
import sys, os, subprocess, re
from collections import defaultdict
from PIL import Image

def main(pdf, outdir):
    os.makedirs(outdir, exist_ok=True)
    raw = os.path.join(outdir, "_raw")
    os.makedirs(raw, exist_ok=True)

    # 1. which page does each image object belong to?
    listing = subprocess.check_output(["pdfimages", "-list", pdf], text=True)
    page_of = []   # index = image number, value = page number
    for line in listing.splitlines()[2:]:
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            page_of.append(int(parts[0]))

    # 2. extract every image as png
    subprocess.check_call(["pdfimages", "-png", pdf, os.path.join(raw, "img")])
    imgs = sorted(f for f in os.listdir(raw) if f.endswith(".png"))

    # 3. group by page (in document order)
    by_page = defaultdict(list)
    for i, fname in enumerate(imgs):
        pg = page_of[i] if i < len(page_of) else i
        by_page[pg].append(os.path.join(raw, fname))

    # 4. stack each page's strips into one photo
    n = 0
    for pg in sorted(by_page):
        strips = [Image.open(p).convert("RGB") for p in by_page[pg]]
        if not strips:
            continue
        w = max(s.width for s in strips)
        h = sum(s.height for s in strips)
        canvas = Image.new("RGB", (w, h), "white")
        y = 0
        for s in strips:
            canvas.paste(s, (0, y)); y += s.height
        if canvas.width > 1100:
            nh = int(canvas.height * 1100 / canvas.width)
            canvas = canvas.resize((1100, nh))
        n += 1
        canvas.save(os.path.join(outdir, f"photo{n}.jpg"), quality=85)
        print(f"photo{n}.jpg  (page {pg}, {len(strips)} strip(s), {canvas.size})")
    print(f"\n{n} photo(s) written to {outdir}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
