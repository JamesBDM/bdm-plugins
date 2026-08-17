# progress-certificate-update

Builds a BDM Progress Certificate (Form 335) from a builder's progress claim — BDM's
certifying instrument as Superintendent under AS4000 cl.37.2. Companion to
`progress-claim-update` (which builds the builder's claim).

## What you get
- A populated, **macro-free** `.xlsm` (Excel recalculates on open).
- A **DRAFT PDF of tabs 01–04 only** (Cover, Certificate, Trade Breakdown, Cashflow).
- A verification that the net-this-claim incl GST equals the builder's tax invoice.

## How it works
`SKILL.md` is the workflow Claude follows: identify project & claim no., reconcile the latest
335 template, read the project folder for specifics (parties, retention basis, contract form,
prior net), assemble a JSON config, then run the engine. The engine is deterministic:

```
python scripts/build_certificate.py \
  --template "<…/Working Copy/300 …/335-Progress_Certificate_R4_2026-06.xlsm>" \
  --config   "<config.json>" \
  --outdir   "<project>\00_ai_sandbox\PC 0NN (Month YYYY)" \
  --rev      "R4 2026-06"
```
Requires `python3`, `openpyxl`, and LibreOffice (`soffice`) on PATH. Output JSON must show
`"PASS": true`.

## Where files go (operator-agnostic)
- **Working / intermediate:** the active project's `00_ai_sandbox\PC 0NN (Month YYYY)\`. Every
  BDM project has a `00_ai_sandbox`; it's the standing location for in-progress work, so the
  skill never depends on any one person's personal folder.
- **Final deliverables:** the `.xlsm` + DRAFT PDF (and the source claim schedule, invoice,
  stat dec) are filed to the project's contract-admin folder, e.g.
  `13_Contract\04_Progress Claims\PC to Builder\PC 0NN (Month YYYY)\`.
- Source project folders are never overwritten — the skill only adds the new claim folder.

## Cleanup
The skill removes its own scratch/intermediate artefacts when it finishes (the engine deletes
its temp dir automatically; the workflow sweeps any render previews or build intermediates),
leaving only the final deliverables. It only ever deletes files it created — never project
documents or source claim files.

## Files
- `SKILL.md` — triggers + workflow + guardrails.
- `scripts/build_certificate.py` — the build/verify/PDF engine (idempotent template guards).
- `references/config_schema.md` — JSON config fields + worked example.
- `references/template_map.md` — tab/cell map + roll-forward column logic.

## Roll-forward in one line
Each trade's **prev certified** := prior certificate's **certified-to-date**; new
**certified-to-date** comes from the new claim; **this-claim = to-date − prev**. The
certificate's **previous net recommendation** = the prior certificate's net (ex GST).

## Per-project config
Read from the project folder each run (Project_Summary in `00_ai_sandbox`, prior certificate,
contract) — not a static file. Review the retention basis and contract form with the user;
the template's flat-5% retention default is often wrong (BDM head contracts commonly use 10%
to a 5% cap).

## Scope / limits (v1)
- Head-contract progress certificates.
- Certificate is **DRAFT** for Senior QS / Director sign-off; never issued by the skill.
- Cashflow month rows span a fixed window; extend for longer programmes.

## Pilot
Willowbrook (202511, 157-163 Caboolture River Rd) PC 02 — ties to Invoice INV-0067 at
$45,045. Test config: `_test_willowbrook_pc02.json`.
