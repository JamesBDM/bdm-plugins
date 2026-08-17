#!/usr/bin/env python3
"""
next_tc.py — work out the next Tender Clarification number for a project's live tender.

Company standard (bdm-tender-clarification):
  * Numbering restarts at TC-01 per tender (per project).
  * Next number = highest existing TC found in the tender RFI folder (filenames AND
    subfolder names) + 1. Legacy "Notice to Tenderers No. X" counts toward the sequence.
  * Save location: 12_Tender Documents/Tender/RFI/RFI<NN> - TC<NN>_<Descriptor>/

Usage:
    python3 next_tc.py "<project_root>" [Descriptor]

Prints: next TC number, suggested subfolder name, and the path to the latest TC docx
to clone (if any).
"""
import os, re, sys, glob

def find_rfi_dir(project_root):
    # canonical location, with a couple of tolerant fallbacks
    candidates = [
        os.path.join(project_root, "12_Tender Documents", "Tender", "RFI"),
        os.path.join(project_root, "12_Tender Documents", "Tender", "RFIs"),
    ]
    for c in candidates:
        if os.path.isdir(c):
            return c
    # fall back: any dir named RFI under 12_Tender Documents
    base = os.path.join(project_root, "12_Tender Documents")
    for dirpath, dirnames, _ in os.walk(base):
        for d in dirnames:
            if d.upper() == "RFI":
                return os.path.join(dirpath, d)
    return None

TC_RE = re.compile(r'TC[-_ ]?0*(\d+)', re.IGNORECASE)
NTT_RE = re.compile(r'NOTICE\s*TO\s*TENDERERS?\s*(?:NO\.?\s*)?0*(\d+)', re.IGNORECASE)

def scan_max_tc(rfi_dir):
    hi = 0
    found = []
    for root, dirs, files in os.walk(rfi_dir):
        for name in list(dirs) + list(files):
            for rx in (TC_RE, NTT_RE):
                m = rx.search(name)
                if m:
                    n = int(m.group(1))
                    found.append((n, name))
                    hi = max(hi, n)
    return hi, found

def latest_tc_docx(rfi_dir):
    docs = []
    for p in glob.glob(os.path.join(rfi_dir, "**", "*.docx"), recursive=True):
        b = os.path.basename(p)
        if "TenderClarification" in b or TC_RE.search(b):
            m = TC_RE.search(b)
            n = int(m.group(1)) if m else 0
            docs.append((n, os.path.getmtime(p), p))
    if not docs:
        return None
    docs.sort(key=lambda x: (x[0], x[1]))
    return docs[-1][2]

def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    project_root = argv[1].rstrip("/\\")
    descriptor = argv[2] if len(argv) > 2 else "Clarification"
    descriptor = re.sub(r'[^A-Za-z0-9]+', '-', descriptor).strip('-') or "Clarification"

    rfi_dir = find_rfi_dir(project_root)
    if not rfi_dir:
        print("RFI folder not found under 12_Tender Documents/Tender/. "
              "First TC for this tender → TC-01.")
        print("NEXT_TC=TC-01")
        print('SUBFOLDER=RFI01 - TC01_%s' % descriptor)
        print("CLONE_FROM=(none — start from Working Copy Form 218 template)")
        return 0

    hi, found = scan_max_tc(rfi_dir)
    nxt = hi + 1
    print("RFI folder:    %s" % rfi_dir)
    if found:
        print("Existing TCs/Notices found: %s" % ", ".join(sorted({f[1] for f in found})))
    else:
        print("No prior TC found → first clarification for this tender.")
    print("NEXT_TC=TC-%02d" % nxt)
    print("SUBFOLDER=RFI%02d - TC%02d_%s" % (nxt, nxt, descriptor))
    clone = latest_tc_docx(rfi_dir)
    print("CLONE_FROM=%s" % (clone or "(none — start from Working Copy Form 218 template)"))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
