# Form 335 template map and roll-forward logic

Tabs (issued PDF = **01, 02, 03, 04 only**; 00 and helpers are excluded):

| Tab | Role |
|---|---|
| 00 Project Details | Single source of truth — every other tab pulls from here. Not issued. |
| 01 Cover Letter | AS4000 cl.37.2 cover; pulls cert no. from `02!F6`, parties from 00. |
| 02 Certificate | The signed Form 335 (recommended payment). |
| 03 Trade Breakdown | The engine — trade analysis, provisional sums, variations, retention. |
| 04 Cashflow Forecast | Forecast S-curve vs certified actuals + chart. |
| SINGLE STAGE (3) / CashflowInput / Data | Helpers. Not issued. |

## 03 Trade Breakdown — column logic (trade rows start at row 14)
```
C Original Budget   D Variance   E Current(=C+D)   F %Prev(=G/E)
G Prev Claimed      H %Done(=I/E)   I Claimed-to-Date
J This Claim (=I-G)   K To Complete (=E-I)
```
Roll-forward: set **G := prior certificate's I**, then update **I** from the new claim →
**J** computes. Subtotal row 46 (`I46`, `G46`, `J46`). Retention `I76`
(`=-(I46+I71)*rate`, or `=-MIN((I46+I71)*rate, contract*cap)` for a capped rate).

## 02 Certificate — chain
```
F22 Contract Works      = 03!I46
F25 Works to date       = F22 + variations
F28 Less Cash Retention = 03!I76
F30 Net Value to Date   = F25 + F27 + F28
F32 Less Previous Net   = -(prior net recommendation)   <- certificate-level roll-forward
F34 Net this claim      = F30 + F32
F47 GST = F46*10%   F49 Net incl GST = F46+F47   (must equal builder invoice)
```
Cert no. `F6`; valuation date `F5`.

## 04 Cashflow / CashflowInput
`scurve(total,first,last,point)` (ported to native formulas by the skill):
```
x = (point-first)/(last-first)
y = x - 0.016x^2 + 0.016x - (1/3.021)(6x^3 - 9x^2 + 3x)
result = total*y ; floored to nearest 1000 unless x = 1
```
Actual monthly (C) / cumulative (E) populated for claimed months only; blank elsewhere so the
chart plots gaps. Total `E33 = MAX(E12:E32)`. Month rows span a fixed window — extend for
longer programmes.
