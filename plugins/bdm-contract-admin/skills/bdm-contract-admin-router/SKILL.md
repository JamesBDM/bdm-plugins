---
name: bdm-contract-admin-router
description: Front door for BDM contract administration under AS4000 — variations (Form 343 determination, Form 342 contract sum adjustment, VO-XX), extensions of time (Form 344, EOT-XX, cl.34), cover letters transmitting either, and the per-project Contract Admin Register (CAR). Use when a contractor's variation or EOT claim needs to be acknowledged, assessed, determined, transmitted or logged, or when the user asks about the register, contract sum adjustments, delay damages, concurrent delay, or "the whole lot" for a claim. Trigger on VO-XX, EOT-XX, Form 342, Form 343, Form 344, "variation determination", "extension of time", "contract sum adjustment", "the register", "CAR", "log this claim", "weather days", "latent condition delay", "acknowledge the claim". Routes to the right sub-skill and walks the lifecycle in order. Not for tender-stage clarifications (use bdm-tender-clarification), progress certificates (use progress-certificate-update) or meeting minutes.
metadata:
  type: router
  revision: R4
  issued: 2026-05-06
  revised: 2026-09-01
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
---

# BDM Contract Admin — router

Routes contract administration work to the correct sub-skill and sequences the multi-step lifecycles. **`bdm-house-style` is always in play** — load it alongside whatever you end up using, so nothing leaves BDM off-brand.

> **Standing filing rule (`bdm-house-style` § 13.12, locked 1/9/26).** Every deliverable below is built and saved **directly in its regular project folder on the first save** — the claim folder, the VO folder, the EOT folder, the tender RFI folder. It is never staged in `00_ai_sandbox` and moved when "finished". Follow the sub-folder naming already in use on that project rather than a convention from a skill, and write into the folder that already exists where the contractor's own documents have landed. Saving there is **not** issuing — the document stays a DRAFT for the Superintendent to sign and send. `00_ai_sandbox` carries the `Project_Summary_*.md`, the `CAR_Sync_Log.md`, ad-hoc work, and documents with no regular home. Scratch and intermediates stay in a temp directory outside the project.

---

## 1. Router table

Match the request to a row, then load that skill. If two rows fit, take the more specific one.

| The user wants … | Load | Produces |
|---|---|---|
| To assess or produce a contractor's variation — "VO-XX", "variation determination", "contract sum adjustment", "CSA", "AS4000 cl.36" | `bdm-variation-determination` | `BDM_VariationDetermination_[Project]_VO[##]_Rev[X].docx` |
| A cover letter wrapping a variation — "acknowledge VO-XX", "transmit the determination", "send the variation back" | `bdm-variation-cover` | `BDM_VariationCoverLetter_[Project]_VO[##]_Rev[X].docx` |
| To determine an EOT — "EOT-XX", "AS4000 cl.34", "extension of time", "weather days", "latent condition delay" | `bdm-eot-determination` | `BDM_EOTDetermination_[Project]_EOT[##]_Rev[X].docx` |
| A cover letter wrapping an EOT — "acknowledge EOT-XX", "transmit the EOT determination" | `bdm-eot-cover` | `BDM_EOTCoverLetter_[Project]_EOT[##]_Rev[X].docx` |
| To log, update or publish from the Contract Admin Register — "the register", "CAR", "log VO-XX", "insurance currency", "approvals status", "register dashboard for the monthly report" | `bdm-contract-admin-register` | `BDM_ContractAdminRegister_[Project]_Rev[X].xlsx` — **xlsx only** |
| A brand or formatting question | `bdm-house-style` | An answer, not a file |
| A **tender-stage** query response or close-date extension, before contract award | `bdm-tender-clarification` | Tender Clarification |
| A **change to the tender documents** during a live tender — revised drawings, scope or terms | `bdm-tender-addendum` | Tender Addendum |
| To certify a progress claim | `progress-certificate-update` | Progress Certificate |

---

## 2. Sub-skills

All five contract admin sub-skills are packaged in this plugin:

- `bdm-variation-determination`
- `bdm-variation-cover`
- `bdm-eot-determination`
- `bdm-eot-cover`
- `bdm-contract-admin-register`

**If one is genuinely unavailable, do not improvise a determination.** A variation or EOT
determination is a contractual instrument issued by the Superintendent — an invented one
carries real risk. Instead: say which skill is missing, resolve the current template from the
templates library (`bdm-house-style` § 8), follow the lifecycle in § 3 and the decision points
in § 4 manually, asking at each one, apply the QA checklist (`bdm-house-style` § 10), and flag
that the skill needs rebuilding.

---

## 3. Lifecycles

### 3a. Variation (cl.36)

1. Contractor submits the claim (their document, not BDM's).
2. **Log it** — register, Variations tab, status `Open`.
3. **Acknowledge** — `bdm-variation-cover` (Mode A), within 48 hours.
4. **Assess** — `bdm-variation-determination` (Form 343).
5. **Transmit** — `bdm-variation-cover` (Mode B), Form 343 attached.
6. **Update the register** — assessed $, programme days, status, approved date.
7. If the contract sum moves, issue a **Contract Sum Adjustment (CSA)**.

**CSA rules — these govern every CSA issued:**

- **A superseding CSA states the RESTATED value, not a delta.** If a later CSA replaces an
  earlier one, it carries the full corrected amount and says so. A full reversal reads
  **($0.00)** with the words *"reversing the amount previously approved"*. Never issue a CSA
  showing only the movement — the reader cannot tell a $40k reduction from a $40k variation.
- **No internal commentary. Ever.** A CSA goes to the builder **and** the Principal. Never
  state that a rate is under-claimed, that an item is "in the Principal's favour", that the
  builder has mis-priced something, or anything else that reads as BDM advising one party
  against the other. Assess the claim; state the determination; stop.
- **Attach the builder's submission to every issued CSA.** Merge it behind the CSA as a
  single PDF, and file a standalone copy in the submission subfolder alongside. A CSA issued
  without the submission it determines cannot be audited later.

### 3b. EOT (cl.34)

1. Qualifying event occurs.
2. Contractor serves notice within 14 days (cl.34.2).
3. **Log it** — register, EOT tab, status `Open`.
4. **Acknowledge** — `bdm-eot-cover` (Mode A). State explicitly whether the notice fell inside the 14-day window.
5. **Run the date preflight (below), then assess** — time analysis (TIA / windows), then
   `bdm-eot-determination`.
6. **Transmit** — `bdm-eot-cover` (Mode B).
7. **Update the register** — assessed days, revised PC date, cost impact.
8. If there is a cost component, raise a related variation (back to 3a).

### 3b-i. EOT date preflight — run before every determination

Calendar-day arithmetic on EOT dates has produced wrong Practical Completion dates on issued
determinations. **Every EOT date calculation runs these six steps, in order.**

1. **Confirm the day basis from the contract**, not from habit. Contract Particulars and
   General Conditions both — amended contracts change the basis. If the contract says
   *business days*, weekends and public holidays are excluded from the count.
2. **Establish the applicable public holiday set** for the **site's** jurisdiction, for every
   year the calculation touches — including the year the revised PC date lands in, which is
   often the following year.
3. **Apply the Queensland show holiday carve-out.** The Ekka public holiday applies to
   **Brisbane only**. It does **not** apply on the Gold Coast or the Sunshine Coast, which
   have their own separate show holidays on different dates. Getting this wrong shifts a PC
   date by a full day.
4. **Count in business days** from the qualifying event, excluding weekends and the holiday
   set from step 2.
5. **Check the resulting date lands on a business day.** A revised PC date falling on a
   Saturday, Sunday or public holiday is a failed calculation, not a rounding question — go
   back and find the error. A calendar-day count once produced a **Sunday** PC date.
6. **Buffer-window check.** Re-run the count with the window shifted one day either side. If
   a one-day shift changes the answer by more than one day, a holiday is being crossed —
   confirm which, and state it in the determination.

Then state the basis explicitly in the determination: day basis, holiday set applied, and any
holiday that fell inside the window. A determination that does not show its working cannot be
checked.

> **Both errors this prevents are real.** One EOT calculated on calendar days produced a
> Sunday PC date. Another missed **Queensland Labour Day (Monday 3 May 2027)** and issued a
> wrong PC date — and the same error was already baked into the preceding EOT on that project,
> so it propagated before anyone caught it.

The full method, including the worked examples, lives in `bdm-eot-determination`. This section
is the preflight the router runs so no EOT reaches assessment without it.

---

### 3c. Monthly publication / lender pack

1. Confirm every Variations / EOT / Insurances / Approvals row on the register is current.
2. **The CAR is xlsx only — do not print or publish it to PDF.** The register is a live
   working document; a PDF of it is stale the moment it is made and gets circulated as though
   it were current. For the lender pack and monthly report appendix, take the dashboard
   figures into the report itself rather than attaching a register snapshot.
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
| R3 | 2026-08-18 | James Gill | All five sub-skills now packaged (§ 2 rewritten). Added § 3b-i EOT date preflight (business days, jurisdiction holiday set, Ekka carve-out, business-day landing check, buffer window). Added the CSA rules to § 3a — restated value not a delta, no internal commentary, builder's submission attached. CAR is xlsx only; removed "print the Cover sheet to PDF" from § 3c. Form numbers removed from the router table pending the form-number decision. |
| R4 | 2026-09-01 | James Gill | Added the standing filing rule at the head of the router so it applies to every route. Filing rule aligned to `bdm-house-style` § 13.12 (locked 1/9/26): the deliverable is built and saved directly in its regular project folder on the first save, following the sub-folder naming already in use on that project; no `00_ai_sandbox` staging; scratch and intermediates stay in a temp directory outside the project; saving is not issuing. |
