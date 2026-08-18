# BDM plugins — how these are maintained

Three people now depend on these skills. That changes what "just fix it" costs.

## The library of record

**The plugin repo is the single source of truth.** Settled 18 August 2026.

Skills previously existed in four places — a local `.claude/skills/` folder, the `2.0_Skills` library, the Cowork plugin set, and archived dev copies. Only the plugin set is what the team actually runs.

**Action required:** the other three copies should be retired or clearly marked superseded, so nobody edits a copy that never reaches anyone. An edit to a non-plugin copy is invisible to the rest of the team and will be silently overwritten at the next install.

## Editing rules

1. **Edit the plugin, not an installed copy.** An installed copy is a read-only cache.
2. **Bump the version.** Every change that reaches other people gets a version bump and a line in the plugin README. Unversioned changes cannot be diagnosed later.
3. **One reviewer.** Any change to a skill that produces a contractual instrument — determinations, CSAs, progress certificates, EOTs — is reviewed by someone other than the author before release.
4. **No personal paths, ever.** Home directories, user folders, session IDs, individual signatures and email addresses resolve at run time. See `bdm-house-style` § 9. The acceptance test is a grep: no personal identifiers outside a revision-history table or `approved_by`.
5. **Flag, don't guess.** Where a standard is genuinely unsettled, mark it pending in the file rather than picking an answer. Two such flags are live right now (filename convention, Working Copy folder names), plus the form-number map.

## Memory has forked — resolve before the next round

As at 9 August 2026 the two memory stores had diverged: one held 143 notes, the other 96 frozen at 30 July, with roughly 50 notes in one and not the other.

**This matters for the team.** If Andrew and Rama sync from the stale side, their sessions will behave differently from the same skills — the skills are shared, the memory behind them is not. Reconcile the two stores before the next round of skill edits.

## After this release

Re-run the memory-gap audit once these changes have been in use for a cycle, and confirm the gaps actually closed. The audit that produced this release found nine skills, all of which had drifted from what the estate had already decided — the drift is the normal state, not an exception, so the audit is worth repeating on a schedule.
