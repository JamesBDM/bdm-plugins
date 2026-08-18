---
name: bdm-eot-determination
description: Assess and draft an Extension of Time determination under AS4000 cl.34 — the Superintendent's instrument granting, reducing or refusing a contractor's EOT claim, and the revised Date for Practical Completion that follows from it. Use when the user says "EOT-XX", "extension of time", "assess the EOT", "EOT determination", "how many days", "weather days", "wet weather claim", "latent condition delay", "revised PC date", "concurrent delay", or hands over a contractor's delay notice. Carries the mandatory date preflight — business days, jurisdiction public holidays and the Queensland show-holiday carve-out — that calendar-day arithmetic has repeatedly got wrong. Pairs with bdm-eot-cover for the transmitting letter.
metadata:
  type: process
  revision: R1
  issued: 2026-08-18
  approved_by: James Gill
  maintained_by: BDM Standards
  parent_skill: bdm-house-style
  related_skills: bdm-contract-admin-router, bdm-eot-cover, bdm-contract-admin-register
---

# EOT Determination (AS4000 cl.34)

Assesses a contractor's delay claim and drafts the Superintendent's determination. **Draft only** — the Superintendent's Representative signs and issues (`bdm-house-style` § 13.6).

---

## 1. Before anything else — read the contract

**Read the Contract Particulars and the General Conditions.** Both. Amended and modified contracts renumber clauses and change the day basis, the notice window and the delay damages rate. A clause number carried over from another project is not evidence of anything (`bdm-house-style` § 13.2).

Confirm and record: the **contract edition** in use, the **day basis** (business or calendar), the **notice window** (cl.34.2 is 14 days in the unamended form), the **delay damages** rate and basis (cl.35), and the **current Date for Practical Completion** you are working from.

Never assume the edition. Two progress certificates on one project went out citing the wrong AS4000 edition because a default was allowed to stand.

---

## 2. The date preflight — mandatory, every time

Calendar-day arithmetic has produced wrong PC dates on issued determinations. Run these six steps in order, and show the working in the determination.

**Step 1 — Day basis from the contract, not from habit.** If the contract says *business days*, weekends and public holidays are excluded from the count.

**Step 2 — Build the public holiday set** for the **site's** jurisdiction, covering **every year the calculation touches** — including the year the revised PC date lands in, which is often the year after the claim.

**Step 3 — Apply the Queensland show-holiday carve-out.** The Ekka public holiday applies to **Brisbane only**. It does **not** apply on the Gold Coast or the Sunshine Coast, which have their own separate show holidays on different dates. Getting this wrong shifts a PC date by a full day.

**Step 4 — Count in business days** from the qualifying event, excluding weekends and the step 2 holiday set.

**Step 5 — Confirm the result lands on a business day.** A revised PC date falling on a Saturday, Sunday or public holiday is a failed calculation, not a rounding question. Go back and find the error. A calendar-day count once produced a **Sunday** PC date on an issued determination.

**Step 6 — Buffer-window check.** Re-run the count with the window shifted one day either side. If a one-day shift moves the answer by more than one day, a holiday is being crossed — identify which, and name it in the determination.

> **Both failures are real, and one propagated.** One EOT calculated on calendar days produced
> a Sunday PC date. Another missed **Queensland Labour Day, Monday 3 May 2027**, and issued a
> wrong PC date — and the same error was already baked into the preceding EOT on that project,
> so it had to be corrected twice.

**State the basis in the determination**: day basis, holiday set applied, and any holiday that fell inside the window. A determination that does not show its working cannot be checked.

---

## 3. Assess

1. **Notice.** Was the contractor's notice served inside the contractual window? State the answer explicitly either way — it is the first thing a reader looks for. Late notice is a matter for the Superintendent, not an automatic bar; flag it, do not decide it.
2. **Qualifying cause.** Does the event fall within the causes the contract lists as entitling an extension? Quote the clause, having read it (§ 1).
3. **Delay analysis.** Time impact or windows analysis against the accepted programme. Show the critical path affected. An event that does not delay the critical path does not extend the date.
4. **Concurrent delay.** Contractor-caused delay overlapping the qualifying event reduces the assessed days. **Raise it; do not resolve it.** Concurrency is a judgement for the assessor.
5. **Days.** Assessed days, and the revised Date for Practical Completion from the § 2 preflight.
6. **Cost.** Time and cost are separate. If there is a cost component it is a **separate variation** (`bdm-variation-determination`), not a line in this determination. Delay damages under cl.35 are a further separate question — flag whether they arise; do not compute them unasked.

---

## 4. Decisions to ask, never assume

- Granted / partially granted / refused — the assessor decides.
- Whether concurrency reduces the assessed days, and by how much.
- Whether the delay carries a cost claim, delay damages, or is nil.
- Signatory capacity — under AS4000 the signing party is the **Superintendent's Representative**.

Ask **one sharp question** at a time (`bdm-house-style` § 13.5).

---

## 5. Build

1. Resolve the current EOT determination template from the templates library (`bdm-house-style` § 8) — highest revision, ignore `_Superseded`. Cite the form by **name**; take its number from `001-Forms Contents Index` at run time rather than copying a number from another skill.
2. Populate: parties, EOT number, claim reference and date, qualifying event, clause relied on, delay analysis summary, **assessed days**, **revised Date for Practical Completion**, **the day basis and holiday set used**, concurrency position, cost position.
3. Never invent a clause, date, drawing reference or register row. Use `[verify clause: __]` where a reference cannot be confirmed (`bdm-house-style` § 13.1).
4. Word + PDF via `bdm-pdf-export`. Signature-ready means signature **and** date (`bdm-pdf-export` § 7).

---

## 6. After

- **Log it** — `bdm-contract-admin-register`, EOT tab: assessed days, revised PC date, **and the day basis used**.
- **Transmit** — `bdm-eot-cover` (Mode B).
- **Update the Project Summary** change log and the Correspondence Register in the same pass (`bdm-house-style` § 13.9).
- If there is a cost component, raise the related variation.
