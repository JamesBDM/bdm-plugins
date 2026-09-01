---
name: bdm-tender-addendum
description: Draft a BDM Tender Addendum — the formal one-page notice that changes the tender documents during a live tender, as Word + signature-ready PDF. Use when the user says "tender addendum", "addendum", "issue an addendum", "Addendum No. X", "change the tender documents", "revised drawings to tenderers", "amend the scope during tender", or needs a numbered change to an issued tender package. Auto-numbers per tender and restarts at 1 for each new tender. NOT for answering a tenderer's question or extending the close date — that is bdm-tender-clarification. NOT for post-contract variations — that is bdm-variation-determination.
metadata:
  type: process
  revision: R1
  issued: 2026-08-18
  revised: 2026-09-01
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-tender-clarification, bdm-house-style, bdm-pdf-export
---

# BDM Tender Addendum

A Tender Addendum **changes the tender documents**. That is what separates it from a Tender Clarification, which answers a query or moves a date without altering the documents.

**Use an Addendum when:** the scope changes, drawings or specifications are revised or superseded, a document is added to or withdrawn from the tender package, or a commercial term changes.

**Use `bdm-tender-clarification` when:** a tenderer's question is being answered, the closing date is being extended, or supplementary information is being issued that does not change the documents.

If both are needed, issue both. Do not fold a document change into a clarification — tenderers price from the documents, and a change buried in a Q&A response gets missed.

---

## 1. Format — the BDM R2 one-page format

An Addendum is **one page**. If it will not fit on one page, the attachments carry the detail and the page carries the schedule of what changed.

- Form 040 Letterhead basis, house style throughout (`bdm-house-style`).
- Header block: project, BDM project number, tender name, **Addendum No.**, issue date.
- One sentence stating that the Addendum forms part of the tender documents and is to be read with the Tender Brief and all previously issued Addenda and Clarifications.
- **The schedule of changes** — a table, one row per change: item number, document affected (title, number, revision **from** → revision **to**), and what changed in one line.
- Attachments list, matching the schedule exactly.
- Acknowledgement line: tenderers acknowledge receipt in their tender return.
- Signature block — acting PM, signature **and** date (`bdm-pdf-export` § 7).

Calibri throughout, A4, 2.2 cm margins, 2 pt navy header rule (`bdm-house-style` § 2 and § 4).

---

## 2. Numbering

`Addendum No. 1`, `No. 2`, … sequential **per tender**, restarting at 1 for each new tender.

Take the next number by listing the tender's addenda folder and using `max(existing) + 1` — **never a row count or a file count**, which silently reuses a number as soon as something is deleted or filed elsewhere.

---

## 3. Build

1. **Identify the project and tender.** Resolve the project folder at run time (`bdm-house-style` § 8, § 9). Read the sandbox `Project_Summary_*.md` — if missing or stale, flag and continue.
2. **Establish what actually changed.** Read the superseded and the superseding documents. **Read the title blocks** — take drawing numbers, revisions and dates off the documents themselves, never from an email describing them and never from memory (`bdm-house-style` § 13.1).
3. **Clone the tender's most recent Addendum** where one exists, then verify it against the current template revision in the templates library. Flag any drift.
4. **Write the schedule.** One row per change. Every row names the document, the revision it replaces and the revision that replaces it. "Various drawings updated" is not a schedule.
5. **File the referenced documents alongside** the Addendum, with clear filenames.
   **Save location:** the Addendum is built and saved directly in the project's tender folder —
   `12_Tender Documents/Tender/Addenda/Addendum <NN>/`, or whatever subfolder pattern that tender
   already uses. List the tender folder and follow it; never impose a convention (`bdm-house-style`
   § 13.12). **Do not stage in `00_ai_sandbox`** — the sandbox is for the Project Summary, logs and
   documents with no regular home. Scratch and intermediates go to a temp directory outside the
   project.
6. **Word + PDF** via `bdm-pdf-export`. Render-check page 1.
7. **Draft the cover email** for the PM to send — to all tenderers, cc the client/Superintendent, asking for acknowledgement of receipt.

---

## 4. Gotchas

- **Every tenderer gets every Addendum.** An Addendum issued to some tenderers and not others compromises the tender. If the distribution list is unclear, ask before drafting.
- **Check the close date still works.** A material change late in a tender usually needs an extension — raise it. The extension itself goes out as a Clarification.
- **Never invent** a drawing number, revision or date. Where one cannot be confirmed, write `[verify: __]` and flag it.
- **Draft only.** The PM issues (`bdm-house-style` § 13.6).
- **File and log in the same pass** — the tender folder, the Project Summary change log and the Correspondence Register (`bdm-house-style` § 13.7, § 13.9).
