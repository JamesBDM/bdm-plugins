---
name: bdm-eot-cover
description: Draft the BDM cover letter that transmits an extension of time — either acknowledging receipt of a contractor's EOT claim (Mode A) or transmitting the Superintendent's determination (Mode B). Use when the user says "acknowledge EOT-XX", "acknowledge the delay notice", "transmit the EOT determination", "cover letter for the EOT", "send the EOT back", or asks for "the whole lot" on an EOT claim. Pairs with bdm-eot-determination.
metadata:
  type: process
  revision: R1
  issued: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-eot-determination, bdm-contract-admin-router, bdm-contract-admin-register
---

# EOT Cover Letter

Two modes. **Ask which one** if the request does not make it obvious — the difference is whether the determination has been made yet (`bdm-contract-admin-router` § 4).

## Mode A — Acknowledge the claim

Sent within **48 hours** of receiving a contractor's delay notice. It acknowledges receipt and nothing more.

Contents:

- Receipt of the notice, with its reference and the **date received**.
- **Whether the notice fell inside the contractual notice window** — state this explicitly, either way. It is the first thing the reader looks for, and silence on it reads as acceptance.
- That the claim is under assessment. **No indication of the likely outcome**, no view on entitlement, no estimate of days.
- Anything further required from the contractor to complete the assessment.

An acknowledgement that hints at the outcome prejudices the determination. Acknowledge; assess separately.

## Mode B — Transmit the determination

Sent with the signed determination attached.

Contents:

- The determination reference and what it determines.
- **Assessed days** and the **revised Date for Practical Completion**.
- The contractual basis — clause relied on, and the **day basis and holiday set used** (`bdm-eot-determination` § 2).
- Where a cost component exists, that it is being dealt with as a separate variation.
- The determination attached, merged behind the letter as a single PDF.

## Both modes

- **Addressee** — the contractor, as named in the contract. Copy the Principal per the project's distribution rule.
- **No internal commentary.** These letters go to the contractor **and** the Principal. Never state that a claim is weak, generous, under-claimed or "in the Principal's favour". State the position; stop.
- **Never invent** dates, references or clause numbers (`bdm-house-style` § 13.1).
- **Draft only** — the PM or Superintendent's Representative sends. That is the issue event (`bdm-house-style` § 13.6).
- Word + PDF via `bdm-pdf-export`; signature **and** date both required.
- Log it on the register and update the Correspondence Register in the same pass.
