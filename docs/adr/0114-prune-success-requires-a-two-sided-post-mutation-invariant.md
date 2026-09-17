# ADR-0114: Prune success requires a two-sided post-mutation invariant

- **Status:** Accepted
- **Date:** 2026-09-13
- **Areas:** workspace, tooling
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0096 § *Wave 7 — Historical migration and pruning* and 2026-09-13
  Errata; `reclassified-lifecycle-result`; `loop-cohort-state-lock`
- **Renumbered:** issued as ADR-0112 and moved to ADR-0114 on 2026-09-13. Another record reached the default branch under 0112 first and keeps the ordinal. Only this record's identifier changed; its decision text is unaltered.

## Decision summary

- **Decision:** Wave 7c satisfies the entry-removal precondition with a
  mandatory, two-sided post-mutation invariant, not an atomic prune. Before
  mutation, the prune fixes an immutable, non-empty selection and records both
  the selected artifacts and their memberships as present. Before reporting
  success, it must establish in one coherent closure observation that every
  selected artifact and every membership that resolves to it are absent.
- **Because:** the repository has no cross-target transaction mechanism that
  commits a directory-tree removal and a shared `workspace.toml` replacement
  together. Existing controls can serialize or detect some writes, but they do
  not turn the removals into one transaction.
- **Applies to:** every Wave 7c prune of a registered Shipped or Archived
  delivery artifact and its `workspace.toml` membership.
- **Tradeoff accepted:** the removals remain sequential, so a half-state is
  observable between them and can survive interruption. The invariant closes
  the operation, not the window.
- **Revisit if:** the repository gains a transaction mechanism that can atomically commit both the directory-tree removal and the shared `workspace.toml` edit, or the register and artifact become one authoritative target whose single atomic mutation establishes both facts.

## Context

RFC-0096 and its 2026-09-13 Errata carry the entry-removal requirement and
assign this route choice to Wave 7c. The `reclassified-lifecycle-result` spec
is only the historical evidence surface: its own notes exclude this item from
its accepted contract and retain the file as history.

Route A, an atomic prune, is unavailable because the repository has no
cross-target transaction mechanism that commits removal of a directory tree
and replacement of shared TOML together. Repository locks and target-local
atomic replacement do not supply that property. The `loop-cohort-state-lock`
reclaim residual is supporting analogy only: it shows a race in one
check-then-rename protocol, not a universal proof about directory-plus-TOML
transactions.

Existing checks do not already establish this decision. `missing_artifact` is
shape-limited finding semantics, not a general membership-to-artifact check.
Legacy and alias memberships also exist: `legacy_entry` and
`unsupported_legacy` are live finding codes, and this checkout contains a
legacy membership.

The global Type 1 reconciliation scan has a different default population.
Wave 7c may reuse it only for the prune's selected pairs; default
reconciliation behavior remains unchanged unless separately decided.

## Decision

Wave 7c must make the invariant part of the prune operation's own completion
contract. A conforming prune:

1. fixes an immutable, non-empty selection before mutation and records both
   sides as present;
2. establishes in one coherent closure observation that each selected
   artifact is absent and that **every membership that resolves to that
   artifact is absent**; and
3. returns failure if either side remains or the coherent observation cannot
   be established.

- **D1:** Prune success is established by a two-sided post-mutation invariant
  inside the prune operation's own completion contract, not by an atomic prune.
- **D2:** The prune fixes an immutable, non-empty selection before mutation and
  records both the selected artifacts and their memberships as present.
- **D3:** Before reporting success the prune establishes, in one coherent closure
  observation, that every selected artifact and every membership resolving to it
  is absent.
- **D4:** The prune returns failure if either side remains or the coherent
  observation cannot be established.
- **D5:** A later status, reconciliation, or audit command never satisfies the
  invariant.
- **D6:** Reuse of the global Type 1 reconciliation scan is limited to the
  prune's selected pairs, and default reconciliation behavior is unchanged.
- **D7:** The closure observation's protocol is left to the Wave 7c spec, which
  must carry the named obligations as acceptance criteria.

A one-sided check does not conform. Neither does a predicate that can pass
when nothing was removed. A later status, reconciliation, or audit command
cannot satisfy the invariant because it cannot un-succeed a prune that already
reported success.

This ADR requires a coherent closure observation but deliberately leaves its
protocol to the Wave 7c spec. As acceptance criteria, that spec must define how
the observation is obtained and which mutation paths participate; the
digest/generation baseline, observation interval, identity binding, absence
representation, and ABA handling; canonical membership identity resolution,
including duplicate and legacy-alias cases; and forced-interleaving
construction tests for each allowed mechanism.

## Consequences

- Successful exit means the operation established both required absences for
  its immutable, non-empty selection in one coherent closure observation.
- The two mutations remain sequential. Peers can observe an intermediate
  half-state, and interruption can leave it behind; recovery remains needed.
- Reuse of the global Type 1 reconciliation scan stays limited to the selected
  pairs. This decision does not change default reconciliation behavior.
- The decision does not select artifacts for deletion, define Wave 7d's
  cleanup set, authorize bulk pruning, or implement the sweep.

**Revisit if:** the repository gains a transaction mechanism that can atomically commit both the directory-tree removal and the shared `workspace.toml` edit, or the register and artifact become one authoritative target whose single atomic mutation establishes both facts.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** The Wave 7c spec carries these obligations as acceptance criteria, and its suite covers no removal, one-sided failure, and surviving duplicate membership for a selected artifact.
- **Owner:** workspace-status maintainers

## Alternatives considered

**Route A — make the prune atomic.** Rejected because no repository mechanism
commits the directory-tree removal and shared-TOML replacement as one
transaction. The `loop-cohort-state-lock` reclaim residual supports the
judgment only by analogy.

**Rely on `missing_artifact`.** Rejected because its semantics are
shape-limited and one-sided.

**Widen the global Type 1 scan.** Rejected because that would change default
reconciliation behavior and report beyond the prune's selected pairs.

**Detect residue later.** Rejected because a later command can diagnose or
support recovery but cannot retract an earlier successful prune result.
