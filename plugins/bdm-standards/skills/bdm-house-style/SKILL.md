---
name: bdm-house-style
description: The Bentley Development Management (BDM) house style — the always-on brand and formatting rulebook for every BDM deliverable. Load this any time a BDM-branded document is being created, updated, reviewed or QA'd, in any format (Word, Excel, PowerPoint, PDF, HTML). Trigger on mention of BDM, Bentley Development Management, BDM brand, house style, navy and gold, the Charcoal Navy Rule, BDM template, BDM letterhead, filename convention, page margins, "is this on-brand", "what colour is our navy", "which font do we use", or whenever a deliverable is about to be saved or issued to a client, lender or contractor. This skill is the rulebook, not a template — it produces answers and corrections, not files. When in doubt, load it: context is cheap, off-brand output is not.
metadata:
  type: standard
  revision: R3
  issued: 2026-05-06
  revised: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  implements: Brand Standard R3 (CN-2026-018)
---

# BDM House Style — the always-on rulebook

Every BDM document obeys these rules, whatever produced it and whoever it is going to. When a workflow skill (contract admin, reporting, minutes) cites a brand rule, it points back here rather than redefining it. **If a workflow skill contradicts this file, this file wins** — flag the conflict so it gets fixed at source rather than quietly forked.

This revision implements **Brand Standard R3 (CN-2026-018)**. Where a document, template or skill still follows R2, R3 supersedes it.

---

## 1. Palette (locked)

| Role | Hex | Use |
|---|---|---|
| Navy | `#0F1721` | Body text, headings, header rule, table top/total borders |
| Gold | `#9D7B5B` | Accents only — eyebrows, logo mark, sign-off wordmark, unresolved placeholders |
| Grey | `#ECECEB` | Fills, table banding |
| Table header shade | `#F4F4F1` | Table header row fill (§ 5) |
| Grey-3 hairline | `#D8D7D3` | Interior table dividers, footer hairline |
| White | `#FFFFFF` | Ground, inverted text on navy bands |

No reds, blues or off-navys. **Gold is never body text.**

**Prohibited outright (R3):**

- `#EAF2EA` — the pale green fill. Remove wherever found; use `#ECECEB` or `#F4F4F1`.
- `#1B1B1B` — the near-black. Existing `#1B1B1B` label text **refits to navy `#0F1721`**.
- Word's default heading blues — `#365F91`, `#4F81BD`, `#17365D`. These arrive with Word's built-in Heading styles and must be overridden in the style definition, not just on the visible text. Check the style, not the paragraph.

## 2. Typography — Calibri only

**Calibri.** Body, headings, numbers, dates and document references. One face, estate-wide.

R2 specified Aptos for body and headings. **R3 replaces this.** Aptos is no longer a BDM face — where a template or an existing document carries Aptos, it is repacked to Calibri on export (see `bdm-pdf-export`). Arial is purged wherever it appears.

- Body — Calibri 10 pt, navy `#0F1721`, 1.25 line spacing, 4 pt space after.
- Body headings — Calibri, navy, **12 pt maximum**.
- Covers are exempt from the heading cap: display sizes 17–26 pt are permitted on cover pages only.
- Carlito is the metric-compatible substitute used by the Linux converter. That is a rendering substitution, not a third BDM face — never specify Carlito in a document.

No third typeface, ever.

## 3. Logo

Navy wordmark + gold mark. 36–46 px in body headers, 82 px on covers. Inverts to white-on-navy on dark bands. No recolour, no stretch, no shadow, no rotation.

## 4. Page geometry and layout — the "Charcoal · Navy Rule"

**Page geometry (R3):**

- A4 portrait.
- **2.2 cm margins, all four sides.**
- Body Calibri 10 pt navy, 1.25 line, 4 pt after.

**Layout:**

- Logo top-left.
- Gold UPPERCASE eyebrow + document reference top-right.
- **Navy 2 pt rule beneath the header — estate-wide.** The 1 pt gold rule previously used on QS Forms 424 and 425 is **deprecated**; those forms move to the 2 pt navy rule at their next revision.
- Footer: grey-3 hairline, filename reference left, page numbers right (`current / total`).
- Section headings: UPPERCASE, navy, navy 1 px underline, 12 pt cap per § 2.
- Eyebrow labels: gold, UPPERCASE, letter-spaced.
- KV tables flat (shaded for minutes only), no rogue borders.
- Sign-off blocks close with the gold `BENTLEY DEVELOPMENT MANAGEMENT` wordmark line.
- **Unresolved placeholders render in gold `#9D7B5B`** — both `{{Token}}` and `[bracketed]` forms. Gold makes an unfilled placeholder obvious on screen and in print, so nothing ships half-populated. Every one must be resolved before issue (§ 10).

## 5. Table specification (R3)

Applies to every data table in every BDM deliverable.

- Header row fill `#F4F4F1`.
- Header text navy, **9 pt, bold, UPPERCASE**.
- **0.5 pt navy frame on the top and bottom edges only. No side borders.**
- Interior dividers grey-3 `#D8D7D3` hairline.
- Numeric columns right-aligned. Text columns left-aligned.
- TOTAL row carries the navy bottom border.

**One sanctioned exception:** navy-fill / white-text header rows are permitted on **Form 101 commercial schedules only**. Nowhere else.

## 6. Numerical conventions

- **Currency** — `$#,##0`. Whole dollars. Parentheses for negatives. Em-dash for nil.
- **Dates** — `DD MMMM YYYY` in formal documents; `dd-mmm-yyyy` in tables.
- **Document references** — `BDM-YYYY-####-XX-##`.
- **GST and retention** — always on their own line. Never netted into a sub-total.
- **Timezone** — all date stamps are **Brisbane time**. Take the date from the environment (`TZ=Australia/Brisbane date`), never from a container default.

## 7. Filename convention

```
BDM_[DocType]_[Project or "TEMPLATE"]_Rev[X].[ext]
```

Capital `R`. No zero-padding — `Rev1`, never `Rev01`.

> **[PENDING DECISION 0.2 — do not treat this section as settled.]** This master pattern
> does not match documented practice, which is per-document-type (`CSA[NN] - [theme].docx`,
> `BDM_TenderClarification_[Project]_TC-XX.docx`, `SM004_[Project].docx`,
> `[PROJECT] - PCG Meeting NNN - DDMMYYYY.docx`,
> `[ProjectShort]_[ddmmyy] - Site Inspection Record.docx`). Until BDM Standards settles
> whether the estate runs one master pattern or a documented per-type table, **follow the
> naming already in use on the project folder** and flag the inconsistency. Do not rename
> existing documents to fit this pattern.

---

## 8. Where the templates live

**Never hardcode a user's path.** Template locations differ on every machine, and these skills run for more than one person. Resolve at runtime per § 9.

1. **Ask the running environment, don't assume.** BDM templates live in the SharePoint-synced `Standard - Documents` library, which resolves under the signed-in user's home directory:
   - Windows: `%USERPROFILE%\BDM\Standard - Documents\BDM TEMPLATES\Working Copy\`
   - macOS: `~/BDM/Standard - Documents/BDM TEMPLATES/Working Copy/` (or under `~/Library/CloudStorage/` if OneDrive is configured that way)

   Build the path from the home directory at runtime. **Never write a person's name, initials or personal folder into a skill.**

2. **Sub-folders by phase:**
   - `200-PM Pre-Contract` — Tender Clarification, Meeting Memorandum
   - `300 Project Management - Contract Delivery` — Site Inspection, Progress Certificate, Variations, EOT
   - `500-Construction` — site meeting forms

   > **[PENDING DECISION 0.3.]** This list uses mixed hyphen/space naming and omits the
   > `000`, `100` and `400` folders. Skills glob on these exact strings, so a wrong string
   > silently finds nothing. **Until the real list is confirmed, list the Working Copy
   > directory at runtime and match case-insensitively on the leading number** rather than
   > relying on the strings above.

3. **Highest revision wins.** Templates are named `NNN-Name_R{n}_{YYYY-MM}.ext`. Take the highest `R` number. **Ignore anything under `_Superseded`.**

4. **Non-templated documents start from Form 040 Letterhead.** Never start a BDM document from a blank page. If no Form template covers the document type, clone **Form 040 Letterhead** and build on it.

5. **The cloud-only trap.** Newly revised templates often sit as OneDrive placeholders that will not open from a sandbox (`BadZipFile`, or a file size far smaller than expected). Do not guess or fall back to an older revision silently — ask the user to drag the template into the chat. Uploaded files read cleanly.

6. **Writing binaries into a synced folder — the correct method.**

   > **`cat src > dest && sync` is NOT reliable and must not be used.** It produced corrupt
   > registers on four separate projects. Any skill still specifying it is following R2 and
   > is wrong.

   Build in a scratch directory, then write with an explicit byte-write and fsync:

   ```python
   with open(src, 'rb') as f:
       data = f.read()
   with open(dest, 'wb') as f:
       f.write(data)
       f.flush()
       os.fsync(f.fileno())
   ```

   Then re-open the written file to confirm it is not corrupt. If the target is locked (open in Word or Acrobat), say so and ask for it to be closed — never write a duplicate.

7. **Reading Office files off the mount is flaky.** Copy the file to a local scratch path (`/tmp`) **before** any integrity check. **An md5 comparison against the source is not a valid test** — the sync mount legitimately repacks the zip, so a differing hash does not mean corruption. Test by opening the copy. Two false "corrupt" calls and about half an hour were lost to this on one job.

If the templates folder genuinely cannot be found, **say so and ask** — never invent a BDM template from scratch. The templates carry the brand; a reconstruction will not.

---

## 9. Resolving the current user

These skills run for every BDM PM, not one person. Nothing that identifies an individual is ever written into a skill file.

Resolve at runtime, in this order:

1. **Home directory** — from the environment (`$HOME` / `%USERPROFILE%`). All SharePoint-synced library paths hang off it.
2. **PM name and initials** — from the signed-in account, or from the project's `Project_Summary_*.md` where the document is being authored on someone's behalf.
3. **Signature** — `<PM home>/<INITIALS>_signature.png`, placed at **2.25 cm** wide. If the acting PM has no signature on file, **flag it and ask** — do not substitute another person's signature.
4. **Sibling skills and scripts** — resolve relative to the plugin root (`${CLAUDE_PLUGIN_ROOT}`). Never an absolute path, never a session ID, never another user's folder.
5. **Tracked-change author, document author, sign-off block** — the acting PM. Never a hardcoded name, and never `Claude`.

**Banned in skill files:** personal folder names, `%USERPROFILE%` expanded to a real user, session paths (`/sessions/<id>/…`), individual email addresses in body text, and any real person's name outside a revision-history table or `approved_by`.

Worked examples in `example_config.json` files use neutral placeholders (`[PM Name]`, `[XX]`, `[pm]@bdmanagement.com.au`), never a real person.

---

## 10. QA before locking any BDM document

**Brand**
- Palette restricted to navy / gold / grey / white. No `#EAF2EA`, no `#1B1B1B`, no Word heading blues.
- Logo present, two-colour, correctly sized.
- Navy **2 pt** header rule and grey-3 footer hairline both present.
- **Calibri throughout** — no Aptos, no Arial, no third face.
- A4 portrait, 2.2 cm margins.

**Layout**
- Section headings UPPERCASE, navy 1 px underline, ≤ 12 pt.
- Eyebrow labels gold, UPPERCASE, tracked.
- KV tables flat, no rogue borders.
- Data tables follow § 5 — `#F4F4F1` header, navy 9 pt bold caps, 0.5 pt navy top and bottom only, numbers right-aligned.
- Sign-off block closes with the gold wordmark line.

**Content**
- Every `{{Token}}` and `[bracketed placeholder]` replaced. Any gold text remaining on the page is an unresolved placeholder.
- Document control block populated.
- Currency, dates and references follow § 6.

**File hygiene**
- Word: track changes off (unless the deliverable is deliberately a tracked draft), comments cleared, document properties set.
- Excel: gridlines off in print view, print area set, no formula errors.
- **Re-open the saved file once** to confirm it still renders correctly.

Run the full pre-issue check against **004-QA_Audit_Checklist** before anything is issued.

---

## 11. Default deliverable format

New BDM documents go out as **Word + PDF**. Produce the PDF with `bdm-pdf-export`, not a plain LibreOffice conversion — the default converter does not match Word's rendering and the result drifts off-brand.

---

## 12. Adding a new document type

1. Build the locked template in the SharePoint templates library.
2. Create a new skill folder in the appropriate plugin with its own `SKILL.md`, plus a worked example.
3. Declare `parent_skill: bdm-house-style` and list `related_skills` for siblings it works with.
4. If it is a contract admin document, add a row to the router table in `bdm-contract-admin-router`.
5. Bump the plugin version so the change reaches everyone.

---

## 13. Working rules

These are the standing BDM rules every workflow skill assumes. They live here so the plugin is self-contained and behaves the same on every BDM machine.

**13.1 Never invent.** Dates, dollar values, drawing numbers, revisions, clause references, RFI references, site instruction references, register rows, attendee names and contract references are read off the source document — never inferred, never reconstructed from memory, never filled with a plausible-looking placeholder. Where a reference cannot be confirmed, write `[verify clause: __]` (or the equivalent for the missing item) and flag it. A confidently wrong contract reference in an issued document is worse than a gap.

**13.2 Read the contract before citing any clause.** Read both the **Contract Particulars** and the **General Conditions**. Modified and amended contracts renumber clauses — a clause number carried over from another project, or from the standard form, is not evidence of anything. Confirm the edition in use before quoting it.

**13.3 The project sandbox.** Each project folder carries `00_ai_sandbox/Project_Summary_[Project_Name].md` — the working source of truth for project name and number, key people, meeting history, open actions and the decisions log. Read it before starting.

- Match with the wildcard `Project_Summary_*.md`. There is exactly **one per sandbox**.
- Handle `00_ai_sandbox` and `00_AI_sandbox` **case-insensitively**.
- **Never create a stub.** If it is missing, say so.
- `PROJECT.md` is the retired name. Do not read it, do not write it, do not create it.
- **If the summary is missing or stale, flag it and continue** where the task allows. It is not a blocker. Apply this severity consistently — no skill treats a missing sandbox as a hard stop.

**13.4 Verify the live file before editing.** List the folder and confirm the file that is actually there. Do not trust a path recorded in the Project Summary — pointers go stale, files get renamed, and editing the wrong copy is silent.

**13.5 One sharp question.** When a required input is missing, ask a single specific question and wait. Do not stack three questions, and do not proceed on a guess for something contractual.

**13.6 Draft, don't issue.** Skills produce DRAFTS held for a human to review and issue. Nothing goes to a contractor, client or lender without the responsible person sending it. Where a document is a tracked-changes draft for review, leave track changes on deliberately and say so.

**13.7 File the deliverable in the same pass.** Producing a document and filing it are one job, not two. In the same pass: deliver the file to the user **and** write it to its project folder. A file that exists only in the session is not a deliverable.

**13.8 Link every file.** Every file created, edited or referenced is cited with a `computer://` link using the **Windows path**, not the mount path.

**13.9 Filing a final document updates the registers.** In the same pass as filing: update the Project Summary change log **and** `Correspondence_Register.csv`. The **CSV is the source of truth**; the old `.xlsx` register is retired. The next correspondence reference is `max(COR-nnn) + 1` — **never a row count**, which silently reuses a number as soon as a row is deleted.

**13.10 Clean up.** Sweep temporary and intermediate files when a job finishes. Update the project sandbox with what changed — new actions, decisions, documents issued — so the next run starts from current facts.

**13.11 Reporting back.** A short "what's in it / what changed" summary plus links to the files. No lengthy restatement of the document's contents — the reader can open it.

---

## 14. Revision control

| Rev | Date | Editor | Change |
|---|---|---|---|
| R1 | 2026-05-06 | James Gill | Initial issue as part of the `bdm-standards` master skill. |
| R2 | 2026-08-17 | James Gill | Split out as a standalone always-on house style skill. Contract admin routing moved to `bdm-contract-admin-router`. Added § 7 template resolution and § 9 default deliverable format. |
| R3 | 2026-08-18 | James Gill | Implements Brand Standard R3 (CN-2026-018). Typography to Calibri-only (Aptos and Arial purged). Added page geometry (A4, 2.2 cm), 2 pt navy header rule estate-wide, 12 pt heading cap, § 5 table specification, prohibited colours, Word heading-style overrides, gold placeholder rendering, Form 040 letterhead start. Replaced the OneDrive `cat`+`sync` write method with an fsync byte-write and added the mount read caveat. `PROJECT.md` retired in favour of `Project_Summary_*.md`. Added § 9 resolving the current user (multi-user) and seven standing rules to § 13. Filename convention (§ 7) and Working Copy subfolder list (§ 8.2) flagged pending decision. |
