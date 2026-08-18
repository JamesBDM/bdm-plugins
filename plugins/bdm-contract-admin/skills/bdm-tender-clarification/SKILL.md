---
name: bdm-tender-clarification
description: Draft a BDM Tender Clarification (Form 218) for a LIVE tender — extend the tender closing date, respond to Tenderer RFIs/queries, and/or issue supplementary drawings, as Word + signature-ready PDF plus a cover email draft. Trigger on "tender clarification", "TC-XX", "extend the tender close", "tender extension", "respond to the tenderer's RFI", "issue a drawing to tenderers", "Notice to Tenderers", or any mid-tender notice going out to the tendering builders before tender close. Auto-numbers per tender (TC-01, TC-02 … restarting each new tender), clones the project's latest TC and verifies it against the current Form 218 revision, reads cited source drawings/emails for exact references (never invents), files referenced drawings alongside, saves into the project tender RFI folder, and drafts the cover email. NOT for post-contract variations (use bdm-contract-admin-router / Form 343-342), EOTs, payment certificates, or meeting minutes.
type: process
template_revision: R1
issued: 2026-06-02
approved_by: James Gill
revised: 2026-08-18
maintained_by: BDM Standards Agent
parent_skill: bdm-house-style
related_skills: bdm-pdf-export, bdm-house-style
template_source: 218-Tender_Clarification_R{latest}_{YYYY-MM}.docx (Working Copy / 200 Project Management - Pre-Contract)
defaults: { deliverables: [word, pdf, cover_email], signature: author, cc_client: true, numbering: per-tender }
---

# BDM Tender Clarification — Create (Skill)

Company standard for issuing a **Tender Clarification** (Form 218) during a live tender. One TC can do any combination of three things:

1. **Extend the tender closing date.**
2. **Respond to Tenderer RFIs / queries** (consolidated response table).
3. **Issue a supplementary drawing or document** as an addendum that forms part of the tender documentation.

Output is always **Word + signature-ready PDF + a cover email draft** for the PM to send. BDM **drafts only** — the PM reviews and sends; the PM's send is what "issues" the TC.

## 1. When to use

- "Draft a tender clarification for <project>"
- "Extend the tender close to <date>"
- "Respond to <tenderer>'s RFI and add it to a tender clarification"
- "Issue this drawing to the tenderers"
- A tenderer has emailed a query/RFI during the tender period and a formal response is needed.

## 2. When NOT to use (hand off)

- **Post-contract variations** → `bdm-contract-admin-router` (Form 343 / 342, VO-XX).
- **Extensions of Time** (contract programme) → `bdm-contract-admin-router` (Form 344, AS4000 cl.34). A *tender* close extension is a TC; a *contract* EOT is not.
- **Payment / progress certificates** → `progress-certificate-update` (Form 335).
- **Meeting minutes** → `meeting-minutes-update` / `bdm-site-and-adhoc-minutes`.

## 3. Inputs

- **Required:** the project (so the tender, tenderers and current close date can be read from the project summary).
- **For an extension:** the new closing date (date + time).
- **For an RFI response:** the tenderer's query (email/RFI schedule) **and** the source document that answers it (consultant drawing/email). Read the source for exact reference details.
- **For a drawing issue:** the drawing PDF.

## 4. The company standard (locked decisions — do not re-litigate per job)

| Decision | Standard |
|---|---|
| **Numbering** | **Per tender, restart at TC-01.** Each project's tender opens its own TC-01 sequence. The next number = highest existing TC in that project's tender RFI folder + 1. Legacy "Notice to Tenderers No. X" issued before the TC rename still count toward the sequence — never renumber an already-issued document. |
| **Build from** | **Clone the project's latest TC**, carry its particulars forward, **then verify the layout against the current Working Copy Form 218 revision** and flag if the clone is stale (older revision). If the project has no prior TC, start from the current Form 218 template. |
| **Save location** | **Project tender RFI folder, one subfolder per TC:** `12_Tender Documents/Tender/RFI/RFI<NN> - TC<NN>_<Descriptor>/` (RFI folder number tracks the TC number). Keep a working copy in `00_ai_sandbox/TC<NN>_<Descriptor>/`. Follow the project's existing subfolder naming pattern if it differs. |
| **Deliverables** | **Word + PDF + cover email draft**, every time. |
| **Signature** | **The signature of the PM creating the TC** (signature-ready PDF), at **2.25 cm** wide. Cloning your own prior TC carries your signature automatically. For another author, swap to their signature PNG (see §5.8). |
| **cc** | **cc the client / Superintendent by default** — pull the contact from the project summary §2/Key people (e.g. RSL Queensland on 160 Pacific). |
| **References** | **Never invent** a drawing number, revision, date, clause or RFI ref. Read it from the source file. File the referenced drawing alongside the TC. |

## 5. Process

1. **Identify the project & tender.** Match the project folder under `Projects - Documents`. Read the sandbox `Project_Summary_*.md` (per `bdm-house-style` § 11.2 — if missing/stale, flag, don't block). Pull: project name, BDM project number, PM, **tenderer list + contacts**, **client/Superintendent cc**, **current tender close date**, and the most recent prior TC / Notice to Tenderers.
2. **Get the next TC number + subfolder name.**
   `python3 scripts/next_tc.py "<project_root>"` → prints the next TC number and a suggested `RFI<NN> - TC<NN>_<Descriptor>` subfolder name, and the path to the latest TC to clone.
3. **Confirm the content type(s)** with the PM if not obvious: extension / RFI responses / drawing issue (or a combination — TC-04 on 160 Pacific did extension **and** an RFI response in one).
4. **Read every source.** For each RFI item, open the tenderer's query email/schedule **and** the answering document. Extract exact references: drawing number, **version/revision**, issue date, issuing consultant, and the relevant design loads/notes. (On the lift-core RFI: `BE230166`, drawing `LT2-S1.101`, Version 2, Issued for Construction 21 Apr 2026, Burchills — all read off the title block.)
5. **Draft the content** into a config JSON (see `scripts/example_config.json`):
   - **Particulars** — project, project_number, project_manager, **issued_to** (tenderer names + key contacts), clarification_number (`TC-NN`), issue_date.
   - **Subtitle** — one line describing what this TC does.
   - **Clarification (2.0)** — what the TC does, in plain English. If it does two things, say "(a)… and (b)…".
   - **Closing date (3.0)** — always present. Either "remains 12:00 noon, <day date>" or "is extended to 12:00 noon, <day date>. This supersedes the previous closing date of …". **Check the weekday is correct** (`date -d <YYYY-MM-DD> +%A`).
   - **RFI items (4.0)** — optional list, one row each: item, subject, query (paraphrase the tenderer faithfully — keep their drawing refs), response (cite the issued document + what tenderers must allow for), source (the consultant).
   - **Attachments (5.0)** — optional list; each line = the issued drawing with full reference.
   - **Author block** — name, title, email (defaults to the cloning PM).
6. **Build the Word doc.** `python3 scripts/build_tc.py config.json "<out>.docx"` — clones the source TC, fills the particulars table, sets the subtitle/clarification/closing-date text, builds or removes the RFI table (one row per item) and attachments list, **renumbers the Submission/Acknowledgement sections automatically**, and swaps the author block/signature if provided.
7. **Export the PDF** with `bdm-pdf-export` — load the skill and run its inlined preflight, then convert and render-check. Eyeball page 1 (masthead font, particulars) and the RFI table. *(The old pdf_export shim in this skill's scripts folder is deleted: both paths it searched were dead, and one pointed into a single user's folder.)*
8. **Signature.** Default is the cloning PM's signature (carried in the clone). To author as a different PM, set `signature_png` to that PM's signature, resolved at run time per `bdm-house-style` § 9.3 — `<PM home>/<INITIALS>_signature.png`, at **2.25 cm**. `build_tc.py` swaps it. **Never hardcode a person's signature path, and never substitute another PM's signature.** If the acting PM has no signature on file, flag it and ask.
9. **Save the pack.** Word + PDF into `12_Tender Documents/Tender/RFI/RFI<NN> - TC<NN>_<Descriptor>/`, with any referenced drawings filed alongside (clear filenames, e.g. `BE230166_LT2-S1.101_V2_Core-Lift-Pad-Reo.pdf`). Working copy → sandbox. **Writing into the synced folder:** build/convert in `outputs/`, then write with the fsync byte-write in `bdm-house-style` § 8.6 — **not** `cat`+`sync`, which left corrupt files on four projects. Re-open the copies to verify.
10. **Draft the cover email** (§7) as chat text for the PM to paste into Outlook (Cowork can't draft to Outlook directly). To: tenderers; cc: client/Superintendent.
11. **Update the project summary** — add a change-log line (what the TC does, refs, status DRAFT — held for PM to issue). If it extends the close, note to update the close date in §1/§4 **once issued**. Sweep temp files (per `bdm-house-style` § 13.10).

## 6. Document structure (Form 218) — dynamic numbering

Fixed: **1.0 PROJECT** (particulars table) · **2.0 CLARIFICATION** · **3.0 TENDER CLOSING DATE** (always present, even when not extending).

Optional, in order: **CONSOLIDATED RFI RESPONSES** (table) · **ATTACHMENTS**.

Then **SUBMISSION** · **ACKNOWLEDGEMENT** · signature block.

`build_tc.py` numbers the tail dynamically: with both optional sections → 4.0 RFI, 5.0 Attachments, 6.0 Submission, 7.0 Acknowledgement; an extension-only TC drops both → 4.0 Submission, 5.0 Acknowledgement.

## 7. Cover email template

> **To:** <tenderers — names>
> **Cc:** <client / Superintendent>
> **Subject:** <Project> — Tender Clarification No. <NN> — <short summary>
>
> Hi <names>,
>
> Please find attached Tender Clarification No. <NN> for <project>[, which covers the following: …].
>
> [If extension] The tender closing date has been extended to **12:00 noon, <day date>** (previously <prior>). All other tender requirements remain unchanged.
>
> [If RFI/drawing] In response to the query on <subject>, the detail is provided on the attached <consultant> drawing "<title>" (<dwg no> <ver>), which now forms part of the tender documentation. Please allow for <what> as shown.
>
> Tenders are to be submitted by email to {{PM_EMAIL}} in two separate packages clearly labelled: Package 1 — Lot 1 …; Package 2 — Lot 2 …. [adapt to the tender]
>
> Please acknowledge receipt by return email, and let me know if you have any further queries.
>
> Regards,
> <PM name> · Bentley Development Management
>
> **Attachments:** TC-<NN> (PDF); <referenced drawings>

Keep the RFI raiser **neutral** ("the query") in both the TC and the email — it goes to all tenderers. Name a tenderer only if the PM asks.

## 8. House rules baked in (don't relearn these)

- **Never invent** dates, drawing numbers, revisions, costs, clause or RFI refs — read them off the source (`bdm-house-style` § 13.1).
- **BDM drafts only** — never "issue". The PM sends; that's the issue event.
- **Always re-check the weekday** of any quoted date.
- **Signature-ready means two things** — the acting PM's signature embedded at 2.25 cm **and** the literal word "Date" replaced with the actual date (`DD MMM YYYY`, Brisbane time). One without the other is a failed deliverable (`bdm-pdf-export` § 7).
- **`{{PM_EMAIL}}`, `{{PM_NAME}}` and `<PM name>` in the § 7 boilerplate resolve to the acting PM** at run time (`bdm-house-style` § 9). Never leave a hardcoded address in issued text — a tender submission sent to the wrong inbox is not recoverable.
- **Writing into the synced folder** — stage binaries in `outputs/`, then use the fsync byte-write (`bdm-house-style` § 8.6). Never `cat`+`sync`. Re-open to verify. If the target `.docx`/`.pdf` is locked (open in Word/Acrobat), say so and ask the PM to close it.
- **Verify against the current template** — if the cloned TC is an older Form 218 revision than the Working Copy, flag it before issuing.

## 9. Files

- `scripts/next_tc.py` — scan a project's tender RFI folder → next TC number, suggested subfolder name, path to latest TC to clone.
- `scripts/build_tc.py` — config JSON → Form 218 Word doc (clone-and-fill, dynamic section numbering, optional signature/author swap).
- `scripts/example_config.json` — worked example (extension + a structural RFI). Names and emails in it are placeholders; the author block resolves to the acting PM at run time.

PDF export has no script here — load the `bdm-pdf-export` skill, which is self-contained.

## 10. Provenance

Built from 160 Pacific Parade, Bilinga **TC-04** (2 June 2026) — a single clarification that extended the tender close to 12:00 noon Thu 11 Jun 2026 **and** closed out Centro's lift well / stair core reinforcement RFI by issuing Burchills drawing LT2-S1.101 V2. First end-to-end run of the Form 218 → Word + PDF + cover-email standard.
