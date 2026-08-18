# BDM Contract Admin — v2.0.0

Contract administration under AS4000. Requires **BDM Standards** — the house style and PDF export live there.

| Skill | What it does |
|---|---|
| `bdm-contract-admin-router` (R3) | Front door for variations, EOTs and the register. Carries the EOT date preflight and the CSA rules. |
| `bdm-variation-determination` **(new)** | Assess a variation under cl.36 and draft the determination + CSA. |
| `bdm-variation-cover` **(new)** | Acknowledge (Mode A) or transmit (Mode B) a variation. |
| `bdm-eot-determination` **(new)** | Assess an EOT under cl.34. Carries the mandatory date preflight. |
| `bdm-eot-cover` **(new)** | Acknowledge (Mode A) or transmit (Mode B) an EOT. |
| `bdm-contract-admin-register` **(new)** | Read, update and audit the CAR. xlsx only. |
| `bdm-tender-clarification` | Live tender — query responses, close-date extensions, supplementary drawings. |
| `bdm-tender-addendum` **(new)** | Live tender — formal changes to the tender documents. |
| `progress-certificate-update` | Certify a builder's progress claim under cl.37.2. |
| `bdm-site-inspection-report` (R2) | Site Inspection Record — **ProjectHub-first**, OneNote as fallback. |
| `bdm-site-and-adhoc-minutes` (R3) | New minutes for site, workshop, kickoff and ad-hoc meetings. |
| `meeting-minutes-update` (R3) | Rolls PCG and recurring minutes forward with tracked changes. |

## What changed in 2.0.0

**Six new skills.** The five sub-skills the router had been pointing at without them existing — so nothing in the estate could write the CAR, and no EOT or variation determination had a skill behind it — plus the Tender Addendum.

**Three fixes that were producing wrong documents:**

- **Progress certificates** now cross-check every variation line against the **CAR**, not the builder's claim. On one certificate 5 of 17 lines carried the wrong status, including one claimed at $50,589 approved that the register showed rejected at $0.
- **Prior unfixed materials** are added back. The template deducted the whole balance including the portion already deducted last month — over-certifying one draft by **$1.53M ex GST**. Guarded, and the build now fails if the branding is stripped or the figures don't tie.
- **`contract_form` is mandatory.** The silent `AS4000-2024` default put the wrong contract edition on two issued certificates. The script now aborts without it.

**EOT dates.** A six-step preflight is now mandatory: business days, the jurisdiction's holiday set for every year touched, the **Ekka carve-out** (Brisbane only — not Gold Coast, not Sunshine Coast), a business-day landing check and a buffer-window check. Calendar-day arithmetic had produced a **Sunday** PC date, and a missed Queensland Labour Day propagated a wrong date across two EOTs on one project.

**CSA rules, now written down:** a superseding CSA states the **restated** value, not a delta; **no internal commentary** in anything that goes to both the builder and the Principal; the builder's submission is attached to every issued CSA.

**Minutes.** `bdm-site-and-adhoc-minutes` was **truncated mid-sentence** — the tail is recovered. Both minutes skills move to `Project_Summary_*.md`, the drop-closed-items rule, the attendee sourcing priority, the spacer-bullet trap and untracked header/footer edits. Tracked changes are authored by the **acting PM**, not `Claude`.

**Site inspections** are ProjectHub-first: parallel photo pull (a serial pull of 40 photos blew a two-minute timeout), `SIR-ddmmyy` numbering, `contract` bucket mirror, planned-vs-actual pre-fill, and `stitch_photos.py` skipped.

**Multi-user.** Every personal path, name, signature reference and email address is out. See `bdm-house-style` § 9.

## Not included

Deliberately out of scope this release, and still open:

- `bdm-pc-inspection-to-pcc`
- The monthly portfolio audit
- `monthly-report-update` and `qs-report` — CLAUDE.md § 11 lists these as "already covered, don't re-build", but neither is installed. § 11 needs correcting or the skills need building.
- The register **retry rule** lives in `bdm-contract-admin-register` § 5 but was not added to the router.
- Nil determinations by email rather than CSA — the rule is stated in `bdm-variation-determination` § 3 but not in the router lifecycle.
