#!/usr/bin/env bash
# pdf_export.sh — thin shim to the bdm-pdf-export skill (fonts + Form-218 preflight + PDF).
# Usage: bash pdf_export.sh "/path/to/TenderClarification.docx"
set -euo pipefail
DOC="${1:?usage: pdf_export.sh <docx>}"

SELF_DIR="$(cd "$(dirname "$0")" && pwd)"
# 1) sibling skill folder (George/bdm-pdf-export) relative to this skill
REL="$SELF_DIR/../../bdm-pdf-export/scripts/pdf_export.sh"
if [ -f "$REL" ]; then exec bash "$REL" "$DOC"; fi

# 2) known mount locations (glob expands; quoted segments keep spaces intact)
for c in /sessions/*/mnt/"Projects - Documents"/George/bdm-pdf-export/scripts/pdf_export.sh \
         /sessions/*/mnt/.claude/skills/bdm-pdf-export/scripts/pdf_export.sh ; do
  [ -f "$c" ] && exec bash "$c" "$DOC"
done

echo "ERROR: bdm-pdf-export/scripts/pdf_export.sh not found. Install/locate bdm-pdf-export." >&2
exit 1
