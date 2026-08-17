#!/usr/bin/env python3
"""next_number.py - find the next meeting number in a folder.

Scans a folder for filenames like `<PREFIX>###_*.docx` (case-insensitive on
prefix) and returns the next sequential number as a zero-padded 3-digit
string.

Usage:
    python3 next_number.py "<folder>" "<prefix>"

Example:
    python3 next_number.py "07_Meeting Minutes/Site Meetings" "SM"
    # Folder contains SM001..., SM002..., SM003... -> prints "004"
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def next_number(folder: Path, prefix: str) -> str:
    if not folder.exists():
        return "001"
    # Match prefix + digits, followed by anything that's not another digit
    # (underscore, space, dash, dot, end-of-string).
    pat = re.compile(
        rf"^{re.escape(prefix)}(\d{{1,4}})(?:\D|$)", re.IGNORECASE
    )
    highest = 0
    for p in folder.iterdir():
        if not p.is_file():
            continue
        if p.suffix.lower() != ".docx":
            continue
        m = pat.match(p.name)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        if n > highest:
            highest = n
    return f"{highest + 1:03d}"


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    folder = Path(argv[1])
    prefix = argv[2]
    print(next_number(folder, prefix))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
