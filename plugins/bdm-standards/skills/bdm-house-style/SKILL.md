---
name: bdm-house-style
description: The Bentley Development Management (BDM) house style — the always-on brand and formatting rulebook for every BDM deliverable. Load this any time a BDM-branded document is being created, updated, reviewed or QA'd, in any format (Word, Excel, PowerPoint, PDF, HTML). Trigger on mention of BDM, Bentley Development Management, BDM brand, house style, navy and gold, the Charcoal Navy Rule, BDM template, BDM letterhead, filename convention, "is this on-brand", "what colour is our navy", "which font do we use", or whenever a deliverable is about to be saved or issued to a client, lender or contractor. This skill is the rulebook, not a template — it produces answers and corrections, not files. When in doubt, load it: context is cheap, off-brand output is not.
metadata:
  type: standard
  revision: R2
  issued: 2026-05-06
  revised: 2026-08-17
  approved_by: James Gill
  maintained_by: BDM Standards
---

# BDM House Style — the always-on rulebook

Every BDM document obeys these rules, whatever produced it and whoever it is going to. When a workflow skill (contract admin, reporting, minutes) cites a brand rule, it points back here rather than redefining it. **If a workflow skill contradicts this file, this file wins** — flag the conflict so it gets fixed at source rather than quietly forked.

---

## 1. Palette (locked)

| Role | Hex | Use |
|---|---|---|
| Navy | `#0F1721` | Body text, headings, header rule, table top/total borders |
| Gold | `#9D7B5B` | Accents only — eyebrows, logo mark, sign-off wordmark |
| Grey | `#ECECEB` | Fills, table banding |
| Grey-3 hairline | `#D8D7D3` | Interior table dividers, footer hairline |
| White | `#FFFFFF` | Ground, inverted text on navy bands |

No reds, blues or off-navys. **Gold is never body text.**

## 2. Typography (two faces only)

- **Aptos** — body and headings.
- **Calibri** — numbers, dates and document references.

No third typeface, ever. If Aptos is unavailable on the rendering machine, that is a rendering fault to fix (see `bdm-pdf-export`), not a licence to substitute.

## 3. Logo

Navy wordmark + gold mark. 36–46 px in body headers, 82 px on covers. Inverts to white-on-navy on dark bands. No recolour, no stretch, no shadow, no rotation.

## 4. Layout — the "Charcoal · Navy Rule"

- Logo top-left.
- Gold UPPERCASE eyebrow + document reference top-right.
- Navy 2 px hairline rule beneath the header.
- Footer: grey-3 hairline, filename reference left, page numbers right (`current / total`).
- Section headings: UPPERCASE, navy, navy 1 px underline.
- Eyebrow labels: gold, UPPERCASE, letter-spaced.
- KV tables flat (shaded for minutes only), no rogue borders.
- Data tables: navy 2 px top border; navy 2 px bottom border on the TOTAL row; grey-3 interior dividers.
- Sign-off blocks close with the gold `BENTLEY DEVELOPMENT MANAGEMENT` wordmark line.

## 5. Numerical conventions

- **Currency** — `$#,##0`. Whole dollars. Parentheses for negatives. Em-dash for nil.
- **Dates** — `DD MMMM YYYY` in formal documents; `dd-mmm-yyyy` in tables.
- **Document references** — `BDM-YYYY-####-XX-##`.
- **GST and retention** — always on their own line. Never netted into a sub-total.

## 6. Filename convention

```
BDM_[DocType]_[Project or "TEMPLATE"]_Rev[X].[ext]
```

Hyphens not spaces. Capital `R`. No zero-padding — `Rev1`, never `Rev01`.

---

## 7. Where the templates live

**Never hardcode a user's path.** Template locations differ on every machine. Resolve them like this:

1. **Ask the running environment, don't assume.** The BDM templates live in the SharePoint-synced `Standard - Documents` library. On a synced machine that resolves under the user's home directory:
   - Windows: `%USERPROFILE%\BDM\Standard - Documents\BDM TEMPLATES\Working Copy\`
   - macOS: `~/BDM/Standard - Documents/BDM TEMPLATES/Working Copy/` (or under `~/Library/CloudStorage/` if OneDrive is configured that way)

   Build the path from the home directory at runtime. Do not write a person's name into a skill.

2. **Sub-folders by phase:**
   - `200-PM Pre-Contract` — Form 218 Tender Clarification, Form 232 Meeting Memorandum
   - `300 Project Management - Contract Delivery` — Form 331 Site Inspection, Form 335 Progress Certificate, Form 342/343 Variations, Form 344 EOT
   - `500-Construction` — site meeting forms

3. **Highest revision wins.** Templates are named `NNN-Name_R{n}_{YYYY-MM}.ext`. Take the highest `R` number. **Ignore anything under `_Superseded`.**

4. **The cloud-only trap.** Newly revised templates often sit as OneDrive placeholders that will not open from a sandbox (`BadZipFile`, or a file size far smaller than expected). If that happens, do not guess or fall back to an older revision silently — ask the user to drag the template into the chat. Uploaded files read cleanly.

5. **The OneDrive write quirk.** When writing binaries back into a synced folder, build in a scratch directory first, then copy in with `cat src > dest && sync`, and re-open the result to confirm it is not corrupt. If the target file is locked (open in Word or Acrobat), say so and ask for it to be closed rather than writing a duplicate.

If the templates folder genuinely cannot be found, **say so and ask** — never invent a BDM template from scratch. The templates carry the brand; a reconstruction will not.

---

## 8. QA before locking any BDM document

**Brand**
- Palette restricted to navy / gold / grey / white.
- Logo present, two-colour, correctly sized.
- Navy 2 px header rule and grey-3 footer hairline both present.
- Aptos for text, Calibri for numbers — no other typefaces.

**Layout**
- Section headings UPPERCASE with the navy 1 px underline.
- Eyebrow labels gold, UPPERCASE, tracked.
- KV tables flat, no rogue borders.
- Data tables: navy 2 px top border, navy 2 px bottom on the TOTAL row.
- Sign-off block closes with the gold wordmark line.

**Content**
- Every `[bracketed placeholder]` replaced.
- Document control block populated.
- Currency, dates and references follow § 5.

**File hygiene**
- Filename follows § 6 exactly.
- Word: track changes off (unless the deliverable is deliberately a tracked draft), comments cleared, document properties set.
- Excel: gridlines off in print view, print area set, no formula errors.
- **Re-open the saved file once** to confirm it still renders correctly.

---

## 9. Default deliverable format

New BDM documents go out as **Word + PDF**. Produce the PDF with `bdm-pdf-export`, not a plain LibreOffice conversion — the default converter does not match Word's rendering and the result drifts off-brand.

---

## 10. Adding a new document type

1. Build the locked template in the SharePoint templates library using the § 6 filename pattern.
2. Create a new skill folder in the appropriate plugin with its own `SKILL.md`, plus a worked example.
3. Declare `parent_skill: bdm-house-style` and list `related_skills` for siblings it works with.
4. If it is a contract admin document, add a row to the router table in `bdm-contract-admin-router`.
5. Bump the plugin version so the change reaches everyone.

---

## 11. Working rules

These are the standing BDM rules every workflow skill assumes. They previously lived in a personal `CLAUDE.md`; they live here now so the plugin is self-contained and behaves the same on every BDM machine.

**11.1 Never invent.** Dates, dollar values, drawing numbers, revisions, clause references, RFI references, attendee names and contract references are read off the source document — never inferred, never reconstructed from memory, never filled with a plausible-looking placeholder. If a reference cannot be found, say so and ask. A confidently wrong contract reference in an issued document is worse than a gap.

**11.2 The project sandbox.** Each project folder carries `00_ai_sandbox/PROJECT.md` (or `Project_Summary_*.md`) — the working source of truth for project name and number, key people, meeting history, open actions and the decisions log. Read it before starting. **If it is missing or stale, flag it** — then continue where the task allows, rather than silently re-reading every source file.

**11.3 One sharp question.** When a required input is missing, ask a single specific question and wait. Do not stack three questions, and do not proceed on a guess for something contractual.

**11.4 Draft, don't issue.** Skills produce DRAFTS held for a human to review and issue. Nothing goes to a contractor, client or lender without the responsible person sending it. Where a document is a tracked-changes draft for review, leave track changes on deliberately and say so.

**11.5 Clean up.** Sweep temporary and intermediate files when a job finishes. Update the project sandbox with what changed — new actions, decisions, documents issued — so the next run starts from current facts.

**11.6 Reporting back.** A short "what's in it / what changed" summary plus links to the files. No lengthy restatement of the document's contents — the reader can open it.

---

## 12. Revision control

| Rev | Date | Editor | Change |
|---|---|---|---|
| R1 | 2026-05-06 | James Gill | Initial issue as part of the `bdm-standards` master skill. |
| R2 | 2026-08-17 | James Gill | Split out as a standalone always-on house style skill. Contract admin routing moved to `bdm-contract-admin-router`. Added § 7 template resolution (removes hardcoded user paths) and § 9 default deliverable format. |
