---
name: progress-certificate-update
description: >-
  Build a BDM Progress Certificate (Form 335) in response to a builder's progress claim —
  BDM's certifying instrument as Superintendent under AS4000 cl.37.2. Use this skill whenever
  someone asks to "do/produce/draft the progress certificate", "certify claim NN", "Form 335
  for [project]", "progress certificate for [project]", or drags a builder's claim schedule +
  tax invoice + statutory declaration into the session and asks to certify or assess the claim.
  Also trigger on "assess the claim", "roll the certificate forward", "next progress
  certificate", or any mention of certifying a head-contract progress claim. This produces the
  CERTIFICATE (BDM → builder); it is the companion to progress-claim-update, which produces the
  builder's CLAIM. Trigger even if the word "Form 335" isn't used — a council/builder claim plus
  "certify" or "progress payment" is enough.
---

# Progress Certificate (Form 335) — update / roll-forward

## What this does and why

When a builder lodges a progress claim, BDM (as Superintendent) must issue a Progress
Certificate under AS4000 cl.37.2 stating the amount BDM recommends for payment. This skill
rolls the previous certificate forward onto the new claim, populates the BDM Form 335
template, verifies the numbers tie to the builder's tax invoice, and produces the
certificate (Excel + PDF) for the Senior QS or Director to review, sign and issue.

You (Claude) do the judgement — reading the project folder and the claim documents, mapping
trades, deciding the certified position. The bundled `scripts/build_certificate.py` does the
deterministic build, the macro-free cashflow, the verification, and the tabs-01–04 PDF. Keep
that division: think and confirm, then let the script build.

## Authority boundary (read first)

BDM **drafts and recommends**; the Senior QS or Director **certifies and issues**. So:
- Every output is held for sign-off (not issued); the signatory line is left as a placeholder.
  Do **not** write "DRAFT" on the certificate — no DRAFT revision, status, header, footer or
  `_DRAFT` filename suffix (`bdm-house-style` § 13.6).
- Default the certified amounts to the **claimed** amounts, then flag any line where you
  believe the Superintendent should certify less — but never reduce a claim yourself without
  being asked. The reviewer adjusts.
- Never invent figures, dates, retention rates or contract references. If a number isn't in
  the documents or the project folder, ask one sharp question or flag it — don't guess.

## Inputs (usually dragged in from email)

1. Builder's **claim schedule** (.xlsx) — trade breakdown, this-claim and to-date amounts.
2. Builder's **tax invoice** (.pdf) — the payment-claim total; the certificate must tie to it.
3. Signed **statutory declaration** (.pdf) — supporting; filed alongside, not a figure source.

If the prior certificate or Payment Schedule isn't already in the project folder, ask for it.

## Workflow

### 1. Identify the project and claim number
Resolve the project from the request and the claim schedule. Read the claim schedule to get
the claim number, "work completed to" date, contract sum, and the this-claim / to-date totals.
Confirm the claim number and project with the user before building. The folder convention for
the claim is `PC 0NN (Month YYYY)`.

### 2. Reconcile the template
Pull the **latest** `335-Progress_Certificate_R*.xlsm` from
`…\BDM TEMPLATES\Working Copy\300 Project Management - Contract Delivery\` (highest revision
wins; ignore `_Superseded`). **Cloud-only trap:** newly-revised templates often arrive as
OneDrive placeholders that won't open from the sandbox (BadZipFile / wrong size). If that
happens, ask the user to drag the template into the chat — uploaded files read cleanly.

### 3. Gather the project specifics (read the project folder — do NOT hard-code)
Per BDM standing rule, read the project's own folder rather than assuming. Sources:
- `00_ai_sandbox\Project_Summary_*.md` — parties, contract form, contract sum, retention basis,
  prior certified/net figures, programme dates. **Start here.**
- The **prior certificate / Payment Schedule** — previously certified to-date (per trade) and
  the previous net recommendation (drives the roll-forward).
- The executed **contract** — retention rule and contract form (e.g. Amended AS4000-1997 vs
  AS4000-2024). Confirm the clause/timeframe if the contract is amended.

Review what you find with the user, especially the **retention basis** (e.g. 10% of value to
date capped at 5% of the contract sum is common for BDM head contracts — the template default
of flat 5% is often wrong) and the **contract form** wording.

### 4. Assemble the config
Write a JSON config (schema in `references/config_schema.md`) capturing project details, the
trade lines `[desc, original, prev, todate]`, retention rule, certificate number, valuation
and issue dates, the previous net recommendation, contract form, invoice total, and cashflow
params/actuals. This is where the roll-forward lives:

**Roll-forward rule (the heart of it):** each trade's **prev claimed** = the *prior
certificate's certified-to-date*; the new **certified-to-date** comes from the new claim. The
certificate's **previous net recommendation** = the prior certificate's net (ex GST). The
script computes this-claim = to-date − prev automatically.

**First certificate on an existing project (bootstrap):** if there is no prior Form 335 (e.g.
the previous claim was certified via a QS report / Payment Schedule), reconstruct "previously
certified" from the prior builder claim schedule's previous-claim column plus the Payment
Schedule net. Flag that the prior figure is reconstructed.

### 4a. Cross-check every variation line against the CAR (mandatory)

**Do not certify a variation line off the builder's claim.** The builder's claim states the
builder's view of each variation's status; the **Contract Admin Register (CAR)** states BDM's
determination. Where they differ, the CAR governs.

For every variation line in the claim:

1. Open the project's CAR (`bdm-contract-admin-register`) and find the matching VO number.
2. Compare **status** (Approved / Rejected / Pending / Superseded) and **approved value**.
3. Certify the **CAR** position, not the claimed position.
4. List every mismatch in the hand-back, with both figures.

A pending or rejected variation certifies at **$0** regardless of what the claim shows. A
superseding CSA carries the **restated** value, not a delta.

> This is not a theoretical control. On one certificate **5 of 17 variation lines** carried
> the wrong status straight off the builder's claim — including one claimed at **$50,589
> approved** that the register showed as **REJECTED, $0**.

If the project has no CAR, or the CAR is stale, **say so and stop**. Do not certify variations
against an unverified register.

### 5. Build (stage in the project's sandbox)
All working/intermediate files go in the **active project's `00_ai_sandbox`** folder — every
BDM project has one, and it's the standing location for in-progress work (operator-agnostic;
do **not** stage in any personal "working" folder). Create the claim sub-folder there using
the standing convention, `00_ai_sandbox\PC 0NN (Month YYYY)\`, and point the engine at it:
```
python scripts/build_certificate.py \
  --template <latest 335 .xlsm> --config <config.json> \
  --outdir "<project>\00_ai_sandbox\PC 0NN (Month YYYY)" --rev "R4 2026-06"
```
It applies the template guards (idempotent — see below), populates tabs 00–04, ports the
cashflow macro to native formulas, saves a macro-free `.xlsm` (Excel recalculates on open),
verifies the math, and exports a PDF of **tabs 01–04 only**. It prints a JSON report;
require `"PASS": true` (ties to the invoice, zero formula errors). Copy the source claim
schedule, invoice and stat dec into the same sandbox sub-folder.

### 6. Review the rendered PDF
Open the PDF pages and eyeball them. Confirm the certificate summary equals the invoice, the
trade subtotals tie, the cashflow chart plots actuals only for claimed months, and the
contract-form references are right. Never report done before looking (BDM verify-before-done).

### 7. File the final deliverables to the contract admin folder
Once the certificate is finalised and ties out, copy the **final `.xlsm` + PDF** (and the
three source docs) to the project's contract-admin folder for progress claims — e.g.
`13_Contract Admin\01_Main Contract\03_Payment Claims\PC to Builder\PC 0NN (Month YYYY)\`
(use the project's actual numbering).

> The old `13_Contract\04_Progress Claims\` path was **retired in May 2026** when the
> `13_Contract` / `13_Contract Admin` split was collapsed. Filing to the old path puts the
> certificate somewhere nobody looks. **Never overwrite existing source project files**; only add the new claim folder.

### 8. Clean up the skill's own working files
After the build, verification, PDF export and filing are done, delete the **scratch /
intermediate artefacts the skill created** — temp build files, render-preview images, any
recalc/static-ize intermediates — leaving only the final deliverables (the `.xlsm`, the
PDF and the source docs) in the sandbox sub-folder. Only ever delete files **the skill
created**; never touch project documents or the source claim files. (The engine already
removes its own temp dir automatically; this step sweeps anything created outside it.)

### 9. Present
Present the final PDF and `.xlsm` and list every judgement call and flag.

## Template guards (idempotent — kept as a safety net)

The corrected master is `335-Progress_Certificate_R4_2026-06.xlsm`. If an older template is
ever used, the script auto-repairs these known defects (and no-ops on the clean R4):
- Stale print header/footer revision stamps → current rev.
- Cover letter reading the certificate number from the title cell `02!A4` → `02!F6`.
- The `scurve()` VBA cashflow macro → native Excel formulas (helper x/y columns) so the
  workbook is macro-free and prints correctly with no enable-macros prompt.
- "Actual Cumulative" total summing instead of taking the last value.
- The yellow "INPUT DATES" highlight on the cashflow note cells.
- **Prior unfixed materials not added back.** `02 Certificate!F28` shipped wired
  `='03 Trade Breakdown'!G88*-1`, which deducts the *whole* unfixed-materials balance
  including the portion already deducted last certificate. Correct is
  `=-('03 Trade Breakdown'!G88-'03 Trade Breakdown'!G58)`. Left unfixed, this
  **over-certified one draft by $1,533,071.32 ex GST**. The guard rewrites the formula and
  no-ops once correct.

## Figures the roll-forward does NOT handle for you

**Builder's margin (`03 Trade Breakdown!I56`).** The template leaves *last month's* margin in
place. Set `builders_margin` in the config — either `{"rate": 0.06}` to recompute on this
claim's value, or an absolute amount. If neither is supplied the script warns and the stale
figure stands; confirm it before issuing.

## Writing the workbook safely

**Never let openpyxl re-save a branded BDM workbook without checking what survived.** An
openpyxl round-trip silently drops embedded images — seven logos and roughly 19 KB were lost
from one register this way. The script now compares `xl/media/` before and after and **fails
the build** if anything was dropped.

When the check fails, do not re-run and hope. Rebuild by editing the XML directly and
re-zipping, observing OOXML child order:

- `pageSetup` comes **after** `pageMargins`.
- `[Content_Types].xml` is the **first** entry in the archive.
- A LibreOffice round-trip that opens cleanly is the acceptance test.

## Cashflow tab notes

The forecast S-curve is `total · (x − 0.016x² + 0.016x − (1/3.021)(6x³ − 9x² + 3x))`, floored
to $1,000 (x = elapsed fraction of start→finish). Actual monthly/cumulative are populated for
claimed months **only**; unclaimed cells are blanked so the chart plots gaps, not zeros. The
template's month rows span a fixed window (Feb-26 → Feb-27); for a programme outside that
window, extend the month rows (a template enhancement) and flag it.

## Flags to raise every time

Retention basis used; **contract form / edition confirmed against the executed contract**
(mandatory — the script aborts without it); **every CAR mismatch, with both figures**; the
builder's margin basis; any certified-vs-claimed delta; any source that was OneDrive cloud-only and couldn't be read; and
the held-for-signature status. Scope of v1 is **head-contract** progress certificates.

## Reference files
- `references/config_schema.md` — the JSON config schema with a worked example.
- `references/template_map.md` — Form 335 tab/cell map and the roll-forward column logic.
