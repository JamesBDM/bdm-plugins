---
name: meeting-minutes-update
description: >-
  Updates an existing Meeting Minutes Word document (.docx) for construction and
  development projects by reviewing a meeting transcript or notes, then applying all
  changes with Track Changes visible. Also builds the FIRST set of minutes for a new
  meeting series from the current BDM template. Use whenever a user asks to update,
  roll forward, refresh, or draft meeting minutes from a transcript, meeting notes,
  audio transcription, or discussion summary. Also trigger when the user mentions:
  track changes on minutes, comparing previous minutes to new notes, adding new
  action items, closing out old actions, updating attendee/apology lists, or pulling
  attendees from the calendar invite. Covers design coordination, site, consultant
  and PCG meetings. Even if the user doesn't say "meeting minutes" explicitly,
  trigger if they ask to update or draft a .docx with tracked changes from a
  transcript or meeting discussion notes.
---

# Meeting Minutes Update Skill

**Revision: R2 · 2026-06** (check this against the latest package in
`Alfred\_Skills\meeting-minutes-update\` — filename carries the revision, e.g.
`meeting-minutes-update_R2_2026-06.skill`. If your installed copy shows an older
revision, reinstall the latest.)

Updates an existing Meeting Minutes Word document to reflect the latest meeting
discussion by reviewing a transcript or notes, applying tracked changes, updating
action items, and maintaining the document's existing structure and formatting. Also
covers building the FIRST set of minutes for a new series from the current BDM
template.

## Why this skill exists

Construction and development projects run on meeting minutes. Design coordination
meetings, PCG meetings, and site meetings generate action items across multiple
disciplines (Architecture, Structural, Mechanical, Hydraulic, etc.) that must be
tracked from meeting to meeting. Updating minutes manually is slow and error-prone
-- items get missed, actions aren't closed out, and attendee lists go stale. This
skill automates the full workflow: read the transcript, identify what changed, and
produce an updated Word document with Track Changes so reviewers can see exactly
what was added, removed, or modified.

---

## Prerequisites

This skill depends on the **docx** skill for all Word document manipulation. Before
starting any work, read the docx SKILL.md to understand the unpack -> edit XML ->
repack workflow, tracked changes XML patterns, and validation mechanics.

---

## Inputs

The user will provide:

1. **Existing meeting minutes** (.docx) -- the document to update. If this is the
   FIRST meeting of a series and no prior minutes exist, build a fresh set from the
   current BDM template (see "Template currency" below).
2. **Meeting transcript or notes** -- the source of new information.
3. **The Outlook calendar event** for the meeting -- the authoritative source of
   attendee/invitee NAMES and EMAIL ADDRESSES (see Phase 1). Do not hand-key
   attendees from a garbled auto-transcript when the calendar invite is available.

The transcript/notes can come in various formats:
- A .docx file containing a typed or auto-transcribed meeting record
- A .txt or .md file with discussion notes
- Text pasted directly into the conversation
- An email thread summarising what was discussed
- Previous meeting minutes (for cross-referencing what's changed)

If the format isn't immediately clear, extract the text using pandoc or the
appropriate skill (PDF skill for .pdf, etc.) and work from the extracted content.

### Template currency (BDM)

Before drafting or rolling forward, confirm the current template revision in the
BDM Working Copy templates folder:
the BDM `Standard - Documents\BDM TEMPLATES\Working Copy` library, resolved from the
current user's home directory (see `bdm-house-style` § 7 — never hardcode a username).

- **Design coordination meetings** -> `230-Design_Meeting_Minutes` (use the highest
  Rn in `200 Project Management - Pre-Contract\`; ignore anything under `_Superseded`).
- Pull the latest revision and reconcile against it. Do NOT use the generic
  `T218_Meeting Minutes` skeleton in the New Job Folder for a design meeting -- it is
  the old generic form and has been superseded by Form 230 for design meetings.

---

## Workflow Overview

The process has four phases:

1. **Analyse** -- Pull attendees from the calendar, read the existing minutes and
   transcript, map discussions to sections
2. **Plan changes** -- Build a change list before touching any XML
3. **Apply with Track Changes** -- Edit the document XML with proper tracked change markup
4. **Validate and deliver** -- Repack, validate, and verify the output

---

## Phase 1: Analyse

### Pull attendees and apologies from the Outlook calendar (do this FIRST)

Auto-transcription mangles names and never carries email addresses or initials, so
the meeting's Outlook calendar event is the source of truth for the attendee block.

1. Find the event with `outlook_calendar_search` -- query on the meeting subject
   (e.g. "New Earth - Design Development Meeting") with `afterDateTime` /
   `beforeDateTime` bracketing the meeting date. If the exact subject returns
   nothing, broaden the query (project short name, or "Design Development").
2. From the returned event take: `organizer`, the full `attendees` email list, the
   `start`/`end` (convert from UTC to local AEST for the TIME field), and `location`.
3. Resolve each email to a Name / Initials / Company:
   - Derive the company from the email domain (e.g. `@jhaengineers.com.au` -> JHA
     Engineering Services, `@studioworkshop.com.au` -> Studio Workshop,
     `@edgece.com` -> Edge, `@axiscertifiers.com.au` -> Axis Certifiers,
     `@spectrafire.com.au` -> Spectra Fire, `@bdmanagement.com.au` -> BDM).
   - Derive the display name from the email and confirm against the transcript
     speakers; carry initials (first + surname).
4. **Split attendees vs apologies using the transcript.** The calendar lists
   *invitees*, not who actually attended. Anyone who spoke / joined in the transcript
   is an Attendee; an invitee who did not appear (or was explicitly noted as an
   apology) goes in Apologies. If attendance is genuinely unclear, flag for the user
   rather than guessing.
5. If the calendar tool is unavailable, fall back to the meeting invite email in the
   project's email folder, then to the transcript -- and flag any name/email left
   unconfirmed.

### Read the existing minutes

Unpack and extract the full text of the existing minutes:

```bash
python scripts/office/unpack.py minutes.docx unpacked/
pandoc --track-changes=all minutes.docx -o minutes.md
```

Identify the document's structure:
- Header section (project name, meeting number, date, time, location)
- Attendee and apology tables
- Discipline/topic sections (e.g. General, Approvals, Architecture, Structural, Civil, Electrical, Mechanical, Hydraulic, Landscaping, Fire Engineering, Program)
- Action item tables within each section (typically: Item Number, Description, Action/Responsibility, Date)
- Any existing strikethroughs or tracked changes from previous updates

### Read the transcript

Extract the full transcript text. For construction design meetings, the transcript
typically flows through disciplines in order, with discussion jumping between topics.
Key things to extract:

- **Who attended** (and who was absent compared to previous meetings) -- reconcile
  against the calendar attendee list from the step above
- **Items discussed** -- map each discussion point to the relevant section in the minutes
- **Decisions made** -- these become updates to existing items or new items
- **New action items** -- with responsible party and any target dates mentioned
- **Closed items** -- actions confirmed as complete or no longer relevant
- **Status updates** -- items that are ongoing but have new information

### Build a change map

Before touching any XML, create a structured summary:

```
HEADER CHANGES:
- Date: [old] -> [new]
- Attendees to add: [names, roles, companies, emails -- from calendar]
- Attendees to remove to apologies: [names]
- Apologies to move to attendees: [names]

SECTION CHANGES:
[Section Name]:
  - Item X.Y: [Close/Update/No change] -- [summary of what changed]
  - New item X.Z: [description] -- [responsible party]
  ...
```

This prevents missed updates and gives you a clear checklist to work through.

---

## Phase 2: Plan Changes

### Action item status logic

For each existing action item in the minutes, determine its status based on the
transcript discussion:

- **Close** -- Item confirmed complete or no longer relevant. Apply strikethrough
  to the entire row's text content using tracked deletion, or mark with a status
  indicator depending on the document's existing convention.
- **Update** -- Item discussed with new information. Add the new information as a
  tracked insertion, either appending to the existing description or adding a new
  sub-item row.
- **No change** -- Item not discussed or confirmed as ongoing with no new info.
  Leave untouched.
- **New** -- Discussion raised a topic not covered by any existing item. Add a new
  row with the next sequential item number.

### Numbering convention

Follow the existing document's numbering scheme. Typically:
- Major sections: 1.0, 2.0, 3.0, etc.
- Items within sections: 1.1, 1.2, 1.3, etc.
- Sub-items: 1.1a, 1.1b or indented rows under the parent

When adding new items, use the next available number in that section. When adding
sub-items to an existing item, follow whatever pattern the document already uses.

---

## Phase 3: Apply with Track Changes

The docx skill covers the basic unpack -> edit XML -> repack workflow and the
paragraph-level tracked-change patterns. The patterns below are the ones specific to
meeting minutes (especially action-item TABLE ROWS) that came up repeatedly during
development and are NOT fully covered by the docx skill -- keep them here.

**Fresh (first-meeting) build:** there are no prior items to track, so a clean issue
is appropriate -- no tracked changes required. Populate the current Form 230 template,
mark the document DRAFT FOR REVIEW, and follow the BDM filename convention. The XML
patterns below apply when you are rolling an existing set forward.

### The unpack -> edit XML -> repack workflow

```bash
# 1. Unpack (already done in Phase 1)
python scripts/office/unpack.py minutes.docx unpacked/

# 2. Edit word/document.xml (the bulk of the work -- see below)

# 3. Repack
python scripts/office/pack.py unpacked/ updated_minutes.docx --original minutes.docx
```

### Track Changes XML -- critical patterns

Every change must use proper OOXML tracked change markup.

#### Replacing text within a paragraph

The `<w:del>` and `<w:ins>` elements must be **direct children of `<w:p>`** (siblings
of `<w:r>`), never nested inside a `<w:r>` element. This is the single most common
mistake.

```xml
<!-- CORRECT: del and ins are siblings of w:r at the paragraph level -->
<w:del w:id="100" w:author="Claude" w:date="2026-06-07T00:00:00Z">
  <w:r>
    <w:rPr><!-- copy original formatting --></w:rPr>
    <w:delText>old text</w:delText>
  </w:r>
</w:del>
<w:ins w:id="101" w:author="Claude" w:date="2026-06-07T00:00:00Z">
  <w:r>
    <w:rPr><!-- copy original formatting --></w:rPr>
    <w:t>new text</w:t>
  </w:r>
</w:ins>

<!-- WRONG: del/ins nested inside a w:r -- produces corrupt document -->
<w:r>
  <w:rPr>...</w:rPr>
  <w:del w:id="100" ...><w:r>...</w:r></w:del>  <!-- INVALID -->
</w:r>
```

#### Inside `<w:del>`, always use `<w:delText>` not `<w:t>`

This is easy to forget. If you use `<w:t>` inside a deletion block, the text won't
render as struck-through and the document may fail validation.

#### Adding new table rows (inserted rows)

To mark a new table row as an insertion, place the `<w:ins>` element **inside
`<w:trPr>`**, not wrapping the `<w:tr>`. And critically, `<w:ins>` must come
**after** `<w:trHeight>` and other table row properties -- the OOXML schema enforces
a specific element order within `<w:trPr>`.

```xml
<!-- CORRECT: w:ins inside w:trPr, AFTER w:trHeight -->
<w:tr w:rsidR="00000000" w14:paraId="1AAABBBB" w14:textId="77777777">
  <w:trPr>
    <w:trHeight w:val="283"/>
    <w:ins w:id="105" w:author="Claude" w:date="2026-06-07T00:00:00Z"/>
  </w:trPr>
  <w:tc>...</w:tc>
  <w:tc>...</w:tc>
</w:tr>

<!-- WRONG: w:ins wrapping the w:tr -->
<w:ins w:id="105" ...>
  <w:tr>...</w:tr>
</w:ins>

<!-- WRONG: w:ins before w:trHeight in w:trPr -->
<w:trPr>
  <w:ins w:id="105" .../>
  <w:trHeight w:val="283"/>   <!-- Schema violation: trHeight after ins -->
</w:trPr>
```

The same rules apply to `<w:del>` for marking deleted rows.

#### Element ordering within `<w:trPr>`

The OOXML schema requires elements in `<w:trPr>` in a specific order. The most
relevant ordering for meeting minutes work:

1. `<w:gridAfter>`, `<w:wAfter>` (grid properties)
2. `<w:trHeight>` (row height)
3. `<w:ins>` or `<w:del>` (tracked changes -- must come after trHeight)
4. `<w:trPrChange>` (property change tracking -- must be last)

If you have a `<w:trPr>` with only `<w:ins>` and no other properties, that's fine --
the ordering constraint only matters when multiple elements are present.

#### Unique IDs and paraIds

- Every `w:id` attribute on `<w:ins>` and `<w:del>` elements must be **unique** across
  the entire document. Start at 100 and increment.
- Every `w14:paraId` on new paragraphs must be a unique 8-digit hex value **less than
  0x80000000** (i.e. the first hex digit must be 0-7). Use a pattern like
  `1AAA0001`, `1AAA0002`, etc.
- Every `w14:textId` on new elements can be set to `77777777` (the "no specific ID" value).

#### Preserving formatting

When creating tracked change runs, copy the `<w:rPr>` (run properties) from the
original text you're replacing. This preserves font, size, bold, colour, etc. For
new rows, copy the `<w:rPr>` from an adjacent row in the same table to match the
document's style.

The standard text formatting in most meeting minutes templates looks like:
```xml
<w:rPr>
  <w:rFonts w:asciiTheme="minorHAnsi" w:eastAsia="Times New Roman"
            w:hAnsiTheme="minorHAnsi" w:cstheme="minorHAnsi"/>
  <w:sz w:val="21"/>
  <w:szCs w:val="21"/>
</w:rPr>
```

But always check the actual document -- don't assume. Copy from existing rows.

### Specific meeting minutes edits

#### Updating the date

Find the date in the header table. It's typically in a `<w:r>` containing text like
"12th March 2026". Replace it with a del/ins pair at the paragraph level. Be surgical
-- only change the parts of the date that differ (e.g. the day number), and leave
shared text (like "th March 2026") in an untouched `<w:r>`.

#### Updating attendees and apologies

Attendee/apology tables typically have columns: Name, Initials, Company, Email.

- **Moving someone from Apologies to Attendees**: Delete their row from the Apologies
  table (mark with `<w:del>` in `<w:trPr>`, use `<w:delText>` in all cells) and insert
  a new row in the Attendees table (mark with `<w:ins>` in `<w:trPr>`).
- **Adding a new attendee**: Insert a new row with `<w:ins>` in `<w:trPr>`. Populate
  Name, Initials, Company AND Email from the calendar (Phase 1).
- **Removing an attendee**: Mark the row with `<w:del>` in `<w:trPr>`.

#### Adding new action items

Copy the XML structure of an existing row in the same table. A typical 4-column
action item row has cells for: Item number (e.g. "3.5"), Description,
Action/Responsibility (initials), and Date (usually empty for new items). Copy
`<w:tcPr>`, `<w:pPr>` and `<w:rPr>` from an adjacent row so the new row matches the
document's style, and mark the row as inserted with `<w:ins>` inside `<w:trPr>` (after
`<w:trHeight>`).

#### Closing/striking through items

If the document convention is to strikethrough closed items, wrap the text content
of each cell in `<w:del>` blocks. If the convention is to add a "CLOSED" status,
add that as a tracked insertion instead.

#### Inserting new text into existing items

To append information to an existing description cell, add an `<w:ins>` block after
the existing paragraph content:

```xml
<!-- Existing text stays untouched -->
<w:r><w:rPr>...</w:rPr><w:t>Original description text.</w:t></w:r>
<!-- New text added as tracked insertion -->
<w:ins w:id="108" w:author="Claude" w:date="...">
  <w:r>
    <w:rPr>...</w:rPr>
    <w:t xml:space="preserve"> Updated: new information from latest meeting.</w:t>
  </w:r>
</w:ins>
```

---

## Phase 4: Validate and Deliver

### Repack with validation

```bash
python scripts/office/pack.py unpacked/ updated_minutes.docx --original minutes.docx
```

The pack script runs OOXML schema validation. If it reports errors, the most common
causes are:

| Error | Cause | Fix |
|-------|-------|-----|
| "Element 'w:del': This element is not expected" | `<w:del>` or `<w:ins>` nested inside `<w:r>` instead of being a sibling at `<w:p>` level | Move del/ins out of the run to be direct children of the paragraph |
| "Element 'w:trHeight': This element is not expected" | `<w:ins>`/`<w:del>` placed before `<w:trHeight>` in `<w:trPr>` | Swap ordering so trHeight comes before ins/del |
| "Element 'w:ins': This element is not expected" | `<w:ins>` wrapping a `<w:tr>` instead of being inside `<w:trPr>` | Move ins inside the row's trPr block |
| Duplicate w:id values | Two tracked change elements share the same ID | Ensure every w:id is unique across the document |
| paraId >= 0x80000000 | Hex paraId value too large | Use values starting with 0-7 (e.g. 1AAA0001) |
| `<w:t>` inside `<w:del>` | Used w:t instead of w:delText in a deletion | Change to w:delText |
| Unreferenced file | Leftover file in the unpacked directory | Delete it |

### Content diff check

The pack script also checks that removing Claude's tracked changes produces the
original text. If you see "Document text doesn't match after removing Claude's
tracked changes", it means either:

1. You modified text outside of tracked change markup
2. The validator can't account for row-level insertions (rows with `<w:ins>` in
   `<w:trPr>` are new content that won't exist in the original)

For case 2, if the schema validation passed but only the content diff fails because
of new inserted rows, you can safely pack with `--validate false`:

```bash
python scripts/office/pack.py unpacked/ updated_minutes.docx --original minutes.docx --validate false
```

Then verify the schema separately:
```bash
python scripts/office/validate.py updated_minutes.docx
```

### Visual verification

Convert to PDF and check the output looks correct:

```bash
python scripts/office/soffice.py --headless --convert-to pdf updated_minutes.docx
pdftoppm -jpeg -r 150 updated_minutes.pdf /tmp/page
```

Review each page to confirm:
- Track changes are visible (strikethroughs for deletions, coloured text for insertions)
- Table formatting is intact
- New rows appear in the correct sections
- Attendee/apology changes are correct, with names AND emails populated from the calendar
- No formatting corruption

---

## Tone and Language

Write as the project Superintendent or meeting chair -- professional, concise, and
factual. Meeting minutes record decisions and actions, not opinions or discussion
summaries.

Good: "Timber ceiling/glazing head detail -- review when glazing contractor on board.
Option to drop glazing 30-40mm with aluminium head for cladding junction."

Bad: "The team had a long discussion about the timber ceiling detail and there were
various opinions shared about how to handle the glazing head."

Use the same level of technical detail as the existing minutes. If the existing items
are terse bullet points, keep new items terse. If they're detailed paragraphs, match
that style.

---

## Consistency Checks (Final Pass)

Before delivering, verify:

- Meeting number and date in the header match the new meeting
- **Every attendee and apology has a NAME, INITIALS, COMPANY and EMAIL populated
  from the Outlook calendar** -- no blank email cells, no [placeholder] text
- All attendees who spoke in the transcript are in the Attendees table; invitees who
  did not attend are in Apologies (or removed if no longer on the project)
- New item numbers follow the existing sequence without gaps or duplicates
- Responsibility initials match names in the attendee list
- Items confirmed as closed are properly marked
- No stale references to the previous meeting's date remain
- For updates: Track Changes are NOT accepted -- leave them visible for review
- Document is visibly marked DRAFT until the user signs it off (BDM drafting rule)

---

## Output

Deliver the updated .docx file with:

1. **Track Changes visible** (for updates) -- do NOT accept changes; leave them for
   reviewer approval. (Fresh first-meeting builds are a clean issue, no tracked changes.)
2. **Clean schema validation** -- all OOXML validation passes
3. **Visual verification** -- convert to PDF/images to confirm rendering

The file should be ready to open in Word, review the tracked changes, and distribute
to the project team.

---

## Cover email (BDM standing rule)

When finalising any project meeting minutes, also draft a concise cover email for the
meeting distribution list (the attendees, plus any standing recipients on the project):

- **Subject**: project name, meeting type and number, and the meeting date
  (e.g. "New Earth — Design Coordination Meeting #4 — Minutes for Review").
- **Body**: one or two lines noting the draft minutes are attached for review, a
  request that recipients confirm any corrections by a stated date, and a reminder
  that actions are due as listed against each item.
- **Attachments**: the DRAFT minutes (Word with tracked changes, and/or the PDF
  export via the bdm-pdf-export skill).
- **Do NOT send the email** -- leave it as a draft for the user to review and send,
  consistent with the BDM rule that client- and contractor-facing communications are
  user-approved before they go out.
