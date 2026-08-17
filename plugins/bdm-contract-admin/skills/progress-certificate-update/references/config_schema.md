# Config schema — build_certificate.py

A single JSON object. Claude assembles this after reading the project folder and the claim
documents, then passes it to `scripts/build_certificate.py --config`.

## Fields

| Field | Type | Notes |
|---|---|---|
| `output_basename` | string | Filename stem (no extension). Carry `_DRAFT_vX.Y`. |
| `project.name` | string | Appears as the certificate "Re:" / project name. |
| `project.address` | string | Full site address. |
| `project.principal` | string | Principal / superintendent's client. |
| `project.contractor` | string | Builder's legal entity (and trading name). |
| `project.client` | string | Defaults to principal if omitted. |
| `project.development_type` | string | e.g. "Residential — 48 townhouses". |
| `project.stage` | string | Defaults "Construction". |
| `project.project_code` | int | BDM job no. (folder code). |
| `project.builder_contact` / `builder_address` / `builder_email` | string | Cover-letter addressee. |
| `contract_sum` | number | Adjusted contract sum ex GST. |
| `cert_no` | int | This certificate number (e.g. 2). |
| `valuation_date` | "YYYY-MM-DD" | "Work completed to" date from the claim. |
| `issue_date` | "YYYY-MM-DD" | Date BDM issues the certificate. |
| `previous_net` | number | Prior certificate's NET recommendation ex GST (positive; script negates). |
| `contract_form` | string | e.g. "Amended AS4000-1997". Drives cl.37.2 wording. |
| `revision` | string | Shown in 00 Project Details (e.g. "R4 DRAFT"). |
| `retention.rate` | number | Fraction, e.g. 0.10. |
| `retention.cap_pct` | number | Optional. Fraction of contract sum, e.g. 0.05 → "10% to a 5% cap". Omit for flat rate. |
| `invoice_total` | number | Builder invoice total incl GST. Build PASSES only if the certificate ties to this. |
| `signatory` | string | Leave the default placeholder unless told otherwise. |
| `cashflow.total` | number | S-curve total (usually the contract sum). |
| `cashflow.start` / `finish` | "YYYY-MM-DD" | S-curve endpoints. Keep `finish` = the last template month row. |
| `cashflow.actuals` | list | `[{"month":"YYYY-MM","monthly":amount}, …]` certified per month. Cumulative is derived. |
| `trades` | list | `[{"desc","original","prev","todate"}, …]` one per trade line. |

## Trade lines and the roll-forward
- `original` = trade's original budget (claim schedule contract value).
- `prev` = **prior certificate's certified-to-date** for that trade (the roll-forward input).
- `todate` = **new certified-to-date** for that trade (this claim's cumulative).
- The script computes this-claim = `todate − prev`; subtotal across trades drives the
  certificate. Sum of `todate` must equal the claim's total claimed-to-date ex GST.

## Worked example (Willowbrook PC 02 — ties to invoice $45,045)
See `_test_willowbrook_pc02.json` in the skill build folder: 18 trade lines (only Preliminaries
and Earthworks claimed), `retention {rate:0.10, cap_pct:0.05}`, `previous_net 650700`,
`contract_form "Amended AS4000-1997"`, two cashflow actuals (Apr 723000, May 45500).
