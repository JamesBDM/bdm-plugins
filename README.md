# BDM Plugins

Shared Claude skills for Bentley Development Management. This repository is a **plugin marketplace** — install from it once and you stay on the latest version of every BDM skill.

## What's in here

### BDM Standards
The foundation. Install this first — the contract admin skills assume it.

| Skill | What it does |
|---|---|
| `bdm-house-style` | The always-on rulebook: palette, typography, logo, layout, filename convention, QA checklist, template locations, working rules |
| `bdm-pdf-export` | Word-faithful PDF export (Aptos install, table grid normalisation, row border cleanup) |
| `datum-markup` | Editable markups, measurements and priced BOQ takeoffs written straight into a PDF for Datum |

### BDM Contract Admin
Contract administration under AS4000.

| Skill | What it does |
|---|---|
| `bdm-contract-admin-router` | Front door for variations (Form 343/342), EOTs (Form 344), and the Contract Admin Register |
| `bdm-tender-clarification` | Form 218 tender clarifications — close date extensions, tenderer RFIs, supplementary drawings |
| `progress-certificate-update` | Form 335 progress certificates, certifying builder claims under cl.37.2 |
| `bdm-site-inspection-report` | Form 331 site inspection records from a OneNote export |
| `bdm-site-and-adhoc-minutes` | New minutes for site, workshop, kickoff and ad-hoc meetings (Form 232) |
| `meeting-minutes-update` | Rolls PCG and recurring minutes forward with tracked changes |

## Installing

**In Claude Code or the desktop app's Code tab:**

```
/plugin marketplace add jamesbdm/bdm-plugins
/plugin install bdm-standards@bdm
/plugin install bdm-contract-admin@bdm
```

**In Cowork:** use the plugin menu next to the prompt box → Manage plugins → add the marketplace `jamesbdm/bdm-plugins`, then install both.

## Getting updates

Updates arrive automatically when a new session starts — **provided the version number was bumped**. See "Making a change" below.

To force a refresh:

```
/plugin marketplace update bdm
```

## Making a change

1. Edit the skill.
2. **Bump the `version` in the plugin's `.claude-plugin/plugin.json` AND in the matching entry in `.claude-plugin/marketplace.json`.** Both. If you skip this, nobody gets the change and nothing looks broken.
3. Commit and push.

Version numbers are `MAJOR.MINOR.PATCH`:
- Fixed a typo or a small behaviour tweak → bump the last number (`1.0.0` → `1.0.1`)
- Added a new skill or a meaningful new capability → bump the middle (`1.0.1` → `1.1.0`)
- Changed how something fundamental works → bump the first (`1.1.0` → `2.0.0`)

## Adding a new skill

1. Create `plugins/<plugin-name>/skills/<new-skill-name>/SKILL.md`.
2. Bump the plugin version in both JSON files (see above).
3. Push.

Everyone gets it on their next session. No reinstall.

## Known gaps

These skills are referenced by the packaged ones but have not been recovered yet. Until they are, `bdm-contract-admin-router` falls back to working from the templates directly and asking the user at each decision point (see § 2 of that skill).

- `bdm-brand-standard` — the full brand rulebook (the always-on summary lives in `bdm-house-style`)
- `bdm-variation-determination` — Form 343
- `bdm-variation-cover` — variation cover letters
- `bdm-eot-determination` — Form 344
- `bdm-eot-cover` — EOT cover letters
- `bdm-contract-admin-register` — the CAR
- `bdm-payment-claim-certificate`, `qs-report` — built previously, not in the account

Not packaged by choice: the 39 Britannia Ave monthly report skill (project-specific), `bdm-project-status-report` (being rebuilt), `glazepro-schedule-extraction` (separate business).

## Templates

Templates are **not** in this repository. They stay in the SharePoint `Standard - Documents` library so BDM Standards revises a form once and every skill picks it up. Skills resolve the path from the current user's home directory — see `bdm-house-style` § 7.
