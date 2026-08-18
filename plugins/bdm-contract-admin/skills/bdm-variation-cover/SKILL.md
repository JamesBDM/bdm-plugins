---
name: bdm-variation-cover
description: Draft the BDM cover letter that transmits a variation — either acknowledging receipt of a contractor's variation claim (Mode A) or transmitting the Superintendent's determination and Contract Sum Adjustment (Mode B). Use when the user says "acknowledge VO-XX", "acknowledge the variation claim", "transmit the determination", "cover letter for the variation", "send the variation back", or asks for "the whole lot" on a variation claim. Pairs with bdm-variation-determination.
metadata:
  type: process
  revision: R1
  issued: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-variation-determination, bdm-contract-admin-router, bdm-contract-admin-register
---

# Variation Cover Letter

Two modes. **Ask which one** if the request does not make it obvious.

## Mode A — Acknowledge the claim

Sent within **48 hours** of receiving a contractor's variation claim.

Contents:

- Receipt of the claim, its reference, and the **date received**.
- That it is under assessment. **No indication of the likely outcome** — no view on entitlement, no comment on the rates, no "this looks high".
- Anything further required from the contractor to complete the assessment.

## Mode B — Transmit the determination

Sent with the signed determination, and the CSA where the contract sum moves.

Contents:

- The determination reference and what it determines.
- The **determined value**, and on a CSA the **restated contract sum** — never a delta.
- The contractual basis — clause relied on and the valuation rule applied.
- Where the variation carries a delay, that time is being dealt with separately as an EOT.
- **The builder's submission merged behind** the determination as a single PDF.

## Both modes

- **No internal commentary.** These letters go to the contractor **and** the Principal. Never state that a rate is under-claimed, generous, or "in the Principal's favour". State the position; stop.
- **A nil or rejected determination is still transmitted** — the contractor is told, in writing, with the grounds. It simply consumes no CSA number.
- **Never invent** dates, references, rates or clause numbers (`bdm-house-style` § 13.1).
- **Draft only** — the PM or Superintendent's Representative sends (`bdm-house-style` § 13.6).
- Word + PDF via `bdm-pdf-export`; signature **and** date both required.
- Log it on the register and update the Correspondence Register in the same pass.
