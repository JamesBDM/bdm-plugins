---
name: bdm-variation-determination
description: Assess and draft a variation determination and the Contract Sum Adjustment (CSA) that follows, under AS4000 cl.36 — the Superintendent's instrument approving, reducing, rejecting or superseding a contractor's variation claim. Use when the user says "VO-XX", "assess the variation", "variation determination", "contract sum adjustment", "CSA", "price this variation", "reject the variation", "supersede CSA-XX", or hands over a contractor's variation claim. Carries the CSA rules — restated value not a delta, no internal commentary, builder's submission attached. Pairs with bdm-variation-cover.
metadata:
  type: process
  revision: R1
  issued: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-contract-admin-router, bdm-variation-cover, bdm-contract-admin-register, progress-certificate-update
---

# Variation Determination and Contract Sum Adjustment (AS4000 cl.36)

Assesses a contractor's variation claim and drafts the determination and, where the contract sum moves, the **Contract Sum Adjustment (CSA)**. **Draft only** — the Superintendent's Representative signs and issues.

---

## 1. Before anything else — read the contract

**Contract Particulars and General Conditions, both** (`bdm-house-style` § 13.2). Confirm the **edition**, the valuation rules the contract sets for varied work (rates, schedule of rates, cost plus margin), the margin percentage, and the notice requirements. Amended contracts renumber and reprice. Never carry a clause number or a margin from another project.

---

## 2. Assess

1. **Is it a variation at all?** Directed variation, constructive variation, or work already within the contract scope? Scope-in work is not a variation. Say which, and why, citing the clause.
2. **Entitlement.** Was it directed, and by whom? Was notice given as the contract requires?
3. **Valuation.** Apply the contract's valuation rules in the order the contract sets them. Check the rates against the schedule of rates where one exists. Show the build-up — quantities, rates, margin — so the figure can be checked.
4. **Time.** If the variation carries a delay, that is a **separate EOT** (`bdm-eot-determination`), not a line here.
5. **Determination.** Approved / partially approved / rejected / superseded — **the assessor decides, not the skill.** Present the assessed figure and ask.

---

## 3. The CSA rules — these govern every CSA issued

**A superseding CSA states the RESTATED value, not a delta.** Where a later CSA replaces an earlier one, it carries the **full corrected amount** and says so. A full reversal reads **($0.00)** with the words *"reversing the amount previously approved"*. Never issue a CSA showing only the movement — the reader cannot tell a $40k reduction from a $40k variation, and the register and the progress certificate then disagree.

**No internal commentary. Ever.** A CSA goes to the builder **and** the Principal. Never state that a rate is under-claimed, that an item is "in the Principal's favour", that the builder has mis-priced something, or anything else that reads as BDM advising one party against the other. Assess the claim; state the determination; stop. This is the rule most easily broken by a helpful-sounding sentence.

**Attach the builder's submission to every issued CSA.** Merge it behind the CSA as a single PDF, and file a standalone copy in the submission subfolder alongside. A CSA issued without the submission it determines cannot be audited later.

**A rejected variation consumes no CSA number.** It stays on the register at status `Rejected`, determined value **$0**, with the grounds in the Notes column.

---

## 4. Build

1. Resolve the current variation determination and CSA templates from the templates library (`bdm-house-style` § 8) — highest revision, ignore `_Superseded`. Cite forms by **name**; take numbers from `001-Forms Contents Index` at run time rather than copying from another skill.
2. Populate: parties, VO number, claim reference and date, description of the varied work, clause relied on, valuation build-up, **determined value**, time position, and — on a CSA — the **restated contract sum**.
3. Never invent a rate, quantity, drawing reference, clause or register row. Use `[verify clause: __]` where a reference cannot be confirmed.
4. Word + PDF via `bdm-pdf-export`. Signature **and** date (`bdm-pdf-export` § 7).

---

## 5. After

- **Log it** — `bdm-contract-admin-register`, Variations tab: determined value, status, approved date, programme days.
- **Transmit** — `bdm-variation-cover` (Mode B), builder's submission merged behind.
- **Update** the Project Summary change log and the Correspondence Register in the same pass.
- Remember the downstream: `progress-certificate-update` certifies variations **against the register**, not against the builder's claim. A determination that never reaches the register will be certified wrong.
