---
name: bdm-contract-admin-router
description: Front door for BDM contract administration under AS4000 — variations (Form 343 determination, Form 342 contract sum adjustment, VO-XX), extensions of time (Form 344, EOT-XX, cl.34), cover letters transmitting either, and the per-project Contract Admin Register (CAR). Use when a contractor's variation or EOT claim needs to be acknowledged, assessed, determined, transmitted or logged, or when the user asks about the register, contract sum adjustments, delay damages, concurrent delay, or "the whole lot" for a claim. Trigger on VO-XX, EOT-XX, Form 342, Form 343, Form 344, "variation determination", "extension of time", "contract sum adjustment", "the register", "CAR", "log this claim", "weather days", "latent condition delay", "acknowledge the claim". Routes to the right sub-skill and walks the lifecycle in order. Not for tender-stage clarifications (use bdm-tender-clarification), progress certificates (use progress-certificate-update) or meeting minutes.
metadata:
  type: router
  revision: R2
  issued: 2026-05-06
  revised: 2026-08-17
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
---

# BDM Contract Admin — router

Routes contract administration work to the correct sub-skill and sequences the multi-step lifecycles. **`bdm-house-style` is always in play** — load it alongside whatever you end up using, so nothing leaves BDM off-brand.

---

## 1. Router table

Match the request to a row, then load that skill. If two rows fit, take the more specific one.

| The user wants … | Load | Produces |
|---|---|---|
| To assess or produce a contractor's variation — "VO-XX", "Form 343", "variation determination", "contract sum adjustment" (Form 342), "AS4000 cl.36" | `bdm-variation-determination` | `BDM_VariationDetermination_[Project]_VO[##]_Rev[X].docx` |
| A cover letter wrapping a variation — "acknowledge VO-XX", "transmit Form 343", "send the variation back" | `bdm-variation-cover` | `BDM_VariationCoverLetter_[Project]_VO[##]_Rev[X].docx` |
| To determine an EOT — "EOT-XX", "AS4000 cl.34", "extension of time", "weather days", "latent condition delay" | `bdm-eot-determination` | `BDM_EOTDetermination_[Project]_EOT[##]_Rev[X].docx` |
| A cover letter wrapping an EOT — "acknowledge EOT-XX", "transmit the EOT determination" | `bdm-eot-cover` | `BDM_EOTCoverLetter_[Project]_EOT[##]_Rev[X].docx` |
| To log, update or publish from the Contract Admin Register — "the register", "CAR", "log VO-XX", "insurance currency", "approvals status", "register dashboard for the monthly report" | `bdm-contract-admin-register` | `BDM_ContractAdminRegister_[Project]_Rev[X].xlsx` (Cover sheet publishes to PDF for client/lender packs) |
| A brand or formatting question | `bdm-house-style` | An answer, not a file |
| A **tender-stage** notice, before contract award | `bdm-tender-clarification` | Form 218 |
| To certify a progress claim | `progress-certificate-update` | Form 335 |

---

## 2. ⚠ Sub-skills not yet packaged

**`bdm-variation-determination`, `bdm-variation-cover`, `bdm-eot-determination`, `bdm-eot-cover` and `bdm-contract-admin-register` are referenced above but are not yet included in this plugin.** They were built outside the account and have not been recovered.

**If one of them is not available when this router points at it, do not improvise a determination.** A variation or EOT determination is a contractual instrument issued by the Superintendent — an invented one carries real risk. Instead:

1. Say plainly which skill is missing.
2. Resolve the current template from the SharePoint templates library (see `bdm-house-style` § 7) — Form 343/342 for variations, Form 344 for EOTs — and work from the template itself.
3. Follow the lifecycle in § 3 and the decision points in § 4 manually, asking the user at each one.
4. Apply the QA checklist from `bdm-house-style` § 8 before anything is locked.
5. Flag that the skill should be rebuilt and added to this plugin.

---

## 3. Lifecycles

### 3a. Variation (cl.36)

1. Contractor submits the claim (their document, not BDM's).
2. **Log it** — register, Variations tab, status `Open`.
3. **Acknowledge** — `bdm-variation-cover` (Mode A), within 48 hours.
4. **Assess** — `bdm-variation-determination` (Form 343).
5. **Transmit** — `bdm-variation-cover` (Mode B), Form 343 attached.
6. **Update the register** — assessed $, programme days, status, approved date.
7. If the contract sum moves, issue a **Form 342 Contract Sum Adjustment**.

### 3b. EOT (cl.34)

1. Qualifying event occurs.
2. Contractor serves notice within 14 days (cl.34.2).
3. **Log it** — register, EOT tab, status `Open`.
4. **Acknowledge** — `bdm-eot-cover` (Mode A). State explicitly whether the notice fell inside the 14-day window.
5. **Assess** — time analysis (TIA / windows), then `bdm-eot-determination`.
6. **Transmit** — `bdm-eot-cover` (Mode B).
7. **Update the register** — assessed days, revised PC date, cost impact.
8. If there is a cost component, raise a related variation (back to 3a).

### 3c. Monthly publication / lender pack

1. Confirm every Variations / EOT / Insurances / Approvals row on the register is current.
2. Print the register Cover sheet to PDF (A4 landscape, fit to page) — that is the dashboard for the lender pack and monthly report appendix.
3. Cross-check the register against the determinations and covers actually issued in the period. The register is the single source of truth only if it agrees with the underlying documents.

---

## 4. Decisions the router cannot make

Ask the user. Never assume:

- **Mode A vs Mode B** on a cover letter — has the determination been issued yet?
- **Approved / Rejected / Partially approved / Withdrawn** — only the assessor decides.
- **Cost vs time vs both** on an EOT — does the delay carry delay damages (cl.35), is the cost a separate variation, or is it nil?
- **Concurrent delay** — contractor-caused delay overlapping the qualifying event reduces assessed days. Raise it; do not resolve it.
- **Signatory capacity** — under AS4000 the signing party must be the Superintendent's Representative. Confirm before locking.

---

## 5. Revision control

| Rev | Date | Editor | Change |
|---|---|---|---|
| R1 | 2026-05-06 | James Gill | Initial issue as the `bdm-standards` master skill (router + house style combined). |
| R2 | 2026-08-17 | James Gill | Split from `bdm-standards`; house style moved to `bdm-house-style`. Added § 2 fallback behaviour for sub-skills not yet packaged. |
