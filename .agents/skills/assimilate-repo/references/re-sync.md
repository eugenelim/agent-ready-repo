# Incremental re-sync

Re-pointing `assimilate-repo` at a source you assimilated before is a **diff**,
not a fresh run — the incremental-import pattern (mined from Copybara, no
dependency).

## Classify against the durable marker
The per-source marker `~/.agentbundle/catalogue-curation/sources/<source-hash>/last-synced.toml`
holds the last content baseline (candidate content-hashes) plus dated sync
entries. It is written as **dated append entries** (never overwritten) and is
**exempt from the per-run completion purge** — the run ledger is ephemeral; this
baseline is durable. Each candidate classifies as:

- **unchanged** — content-hash matches the baseline → skip.
- **changed** — hash differs → re-surface for a verdict.
- **new** — not in the baseline → surface.

## Time-of-sync record = the git commit log
Each sync lands as commits, so the commit log *is* the timestamped migration
history. No parallel bespoke log; the marker holds only the baseline + dates.

## Recording the re-sync on the prior source-RFC
Follow RFC-0055's own forms (it governs corrections *within* an RFC; it does not
define whole-RFC supersession):

- Prior RFC **Open** → record the delta **in-place as an Amendment** (correction
  or new candidates alike — the proposal is still being worked).
- Prior RFC **Frozen (Accepted/Rejected) + a genuine correction** (a verdict
  typo, a moved destination) → an **Erratum** entry, additive.
- Prior RFC **Frozen + new candidates or reversed verdicts** (fresh decisions,
  not a correction) → author a **new RFC**, and record it on the prior one as an
  **Erratum entry naming the superseding RFC** (RFC-0055's documented whole-RFC
  form). **Never append new decisions to a Frozen RFC's Errata.**
