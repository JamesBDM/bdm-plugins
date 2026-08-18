---
name: bdm-contract-admin-register
description: Read, update and audit a project's Contract Admin Register (CAR) — the live xlsx that holds every variation, EOT, insurance and approval on a project, and the register the Progress Certificate is checked against. Use when the user says "the register", "CAR", "log this variation", "log VO-XX", "log EOT-XX", "update the register", "register status", "what's outstanding on variations", "insurance currency", "approvals status", "is the register current", or when any contract admin document is issued and its register row needs writing. Also use for the nightly sweep and the monthly register audit. Produces xlsx only — never a PDF.
metadata:
  type: process
  revision: R1
  issued: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-contract-admin-router, progress-certificate-update, bdm-variation-determination, bdm-eot-determination
---

# BDM Contract Admin Register (CAR)

The CAR is the project's single source of truth for variations, EOTs, insurances and approvals. Every contract admin document that gets issued has a row here. The Progress Certificate is certified **against** it (`progress-certificate-update` § 4a), so a stale register produces a wrong certificate.

**The register is xlsx. It is never published as a PDF.** A PDF of a live register is stale the moment it is made and then circulates as though it were current. When a lender pack or monthly report needs the numbers, take the figures into the report.

---

## 1. Find the register

Under the project's contract admin folder, resolved at run time (`bdm-house-style` § 8 and § 9). Filename `BDM_ContractAdminRegister_[Project]_Rev[X].xlsx`.

**List the folder and confirm the live file.** Do not trust a path recorded in the Project Summary — pointers go stale and editing the wrong copy is silent (`bdm-house-style` § 13.4).

Tabs: `Variations`, `EOT`, `Insurances`, `Approvals`, `Cover`.

**Column names are not uniform across projects.** Read the header row before writing. Never assume a column index.

---

## 2. Keeping it current — three layers

The register only works if it is current. Three layers, each with a different job:

**Layer 1 — on every touch.** Any time a contract admin document is drafted, issued or determined, its register row is written **in the same pass**. Not "later", not at the end of the week. A document issued without its row is the failure mode this whole skill exists to prevent.

**Layer 2 — nightly sweep.** Walk the contract admin folders for documents issued that day and confirm each has a row. Report anything found without one. The sweep **reports**; it does not invent rows for documents it does not understand.

**Layer 3 — monthly audit.** Cross-check every row against the underlying documents — determinations, covers and CSAs actually issued in the period. The register is the source of truth *only* if it agrees with the documents. Report every disagreement; resolve none of them silently.

---

## 3. What automation may and may not write

**Automation writes `Open` and `DRAFT` rows only.**

It may: create a row when a claim is received; set status `Open`; attach references, dates and the claimed amount; mark a drafted determination `DRAFT`.

It may **not** write `Approved`, `Rejected`, `Partially approved`, `Superseded` or any determined value. **A determination is a human act.** The assessor decides and the register records it afterwards. If a status change is needed, say what you would write and ask.

---

## 4. Writing to the register safely

**Never let openpyxl re-save a branded BDM workbook.** An openpyxl round-trip silently drops embedded images — seven logos and roughly 19 KB were lost from one register this way, and nobody noticed until it was issued.

The safe route:

1. Copy the file off the sync mount to local scratch first (`bdm-house-style` § 8.7). **An md5 comparison against the source is not a valid integrity test** — the mount legitimately repacks the zip.
2. Edit the sheet XML directly and re-zip. Observe OOXML child order:
   - `pageSetup` comes **after** `pageMargins`.
   - `[Content_Types].xml` is the **first** entry in the archive.
3. **Acceptance test:** the rebuilt file opens cleanly in a LibreOffice round-trip, and the `xl/media/` part list is unchanged.
4. Write back with the fsync byte-write (`bdm-house-style` § 8.6). Never `cat`+`sync`.
5. Re-open the written file to confirm it is not corrupt.

If the register is locked (open in Excel), say so and ask for it to be closed. **Never write a duplicate** — two registers is worse than none.

---

## 5. When the write fails — the retry rule

Sync mounts drop out. A failed register write is not a reason to move on quietly.

- Retry every **30 minutes**.
- Cap at **4 attempts or 2 hours**, whichever comes first.
- Then **escalate** — tell the user plainly which row could not be written and what it should say, so it can be entered by hand.
- **Never silently skip a register write.** A missing row is invisible; a reported failure gets fixed.

---

## 6. Row conventions

- **Variations** — one row per VO. A rejected variation keeps its row at status `Rejected` with the determined value **$0**; the grounds go in the **Notes** column. A superseding determination shows the **restated** value, not a delta.
- **EOT** — one row per EOT. Record assessed days, the revised PC date **and the day basis used** (business or calendar, and the holiday set applied — see `bdm-eot-determination`).
- **Insurances** — currency dates. Flag anything expiring inside 30 days.
- **Approvals** — condition references and status.
- **Next reference number** is `max(existing) + 1`, **never a row count** — a row count silently reuses a number as soon as a row is deleted.

---

## 7. Hand back

State: which rows changed, which are still `Open`, anything found in the sweep without a row, and any status change you did not make because it needs a human. Cite the register with a `computer://` link (`bdm-house-style` § 13.8).
