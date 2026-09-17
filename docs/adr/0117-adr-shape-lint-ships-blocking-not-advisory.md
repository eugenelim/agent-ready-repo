# ADR-0117: The ADR shape lint ships blocking over the whole corpus, not advisory

- **Status:** Accepted
- **Date:** 2026-09-17
- **Areas:** governance, tooling
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0102 (the proposal this discharges); ADR-0027 (the deferred
  lint this ships, discharged on its record via that ADR's Errata)

## Decision summary

- **Decision:** We will ship `lint-adr-shape.py` (`check-adr-shape` in the pull-request gate) blocking over the entire `docs/adr` corpus, not advisory over a tolerated residual.
- **Because:** an advisory check over a corpus that already passes is a control that can never fail, and RFC-0102 § 6's original advisory-then-blocking phase existed only to cover an untriaged corpus.
- **Applies to:** the `check-adr-shape` pull-request step over `docs/adr`. It does not change the tool set, the fifteen check classes, or any other gate.
- **Tradeoff accepted:** there is no grace period — any record that a probe class misses now reds the merge gate the moment it is found, rather than surfacing as advisory noise first.
- **Revisit if:** a corpus regression needs bulk remediation before a pull request can merge again, or the fifteen classes prove too strict against a legitimate record shape they do not yet cover.

## Context

RFC-0102 accepted a metadata block a program can check, plus one shape lint over
every ADR. Its own reviewer brief and § 6 stated the rollout as two phases:
"one portable shape lint over every ADR, warn-only until the corpus is migrated,
then enforced." That phasing existed because the corpus, at the RFC's
acceptance, was expected to hold many pre-existing findings against the new
checks — an advisory phase gives a maintainer time to triage before a merge
gate can block on them.

Ahead of this delivery's lint work, a separate migration commit
(`4b2714112`) brought the whole `docs/adr` corpus to a state a probe measured
at four findings across two records, later re-measured at six findings across
four records once the probe covered all fifteen classes and both mirror rules.
Both residuals were record-shaped, not lint-shaped, and both were fixed as
record edits rather than criteria changes. That left the corpus one gate run
away from a clean pass — the precondition RFC-0102 § 6's own advisory phase was
protecting against was already met before the lint shipped.

Shipping an advisory phase against a corpus that already passes would ship a
check that never fires: nothing exercises its finding path, and nothing proves
the check would actually stop a bad merge if one arrived. That is the same
control-that-cannot-fail failure mode this repository's own review discipline
already names elsewhere.

## Decision

We will ship the lint blocking, and only once the corpus is verified clean
against every check class the lint implements — not as a two-phase rollout.

- **D1:** The gate blocks. `lint-adr-shape.py` exits 1 on any finding, and
  `check-adr-shape` is a required pull-request step; there is no separate
  warn-only mode and no flag that downgrades a finding to advisory.
- **D2:** Blocking takes effect only once the corpus is verified to pass every
  one of the fifteen check classes, including both mirror rules
  (`ADR-S009`, `ADR-S010`). The corpus fix is a precondition of this decision,
  not a follow-on phase after it ships.
- **D3:** The gate runs over the whole `docs/adr` directory on every pull
  request, not a sampled or changed-files-only scan — a partial scan would let
  a pre-existing defect in an untouched record escape the gate indefinitely.

## Decision drivers

- **A guarantee has to be enforced, not merely asserted.** An advisory finding
  a maintainer can ignore is not a guarantee; this repository's own review
  discipline treats an unenforced check as equivalent to no check.
- **The corpus was already clean.** Once the precondition an advisory phase
  exists to protect against no longer holds, keeping the phase adds a step with
  no observable effect.
- **No reduction in scope.** Blocking had to cover the whole corpus and every
  check class, not a subset chosen for an easier initial pass.

## Consequences

**Positive:**

- The lint is a real gate from the moment it ships: a record that fails any of
  the fifteen checks blocks its own pull request, rather than accumulating as
  advisory noise a reviewer learns to skip past.
- No temporary tolerance list or suppression mechanism was needed, so there is
  no separate follow-on task to later flip a flag from warn to block.

**Negative:**

- There is no grace period. If a sixteenth defect exists in a record that no
  probe class covers, it surfaces as a blocked merge rather than an advisory
  note, and the remedy is a record fix under time pressure rather than a
  scheduled cleanup.
- The decision assumes the corpus measurement was exhaustive across every
  check class. A probe that implements fewer classes than the shipped lint
  would understate the residual, which is exactly the gap a re-measurement
  against all fifteen classes closed before this decision was made.

**Revisit if:** a corpus regression needs bulk remediation before merging
becomes possible again, or the fifteen check classes prove too strict against
a legitimate record shape they do not yet cover.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `.github/workflows/build-check.yml`'s `check-adr-shape` step
  invokes `lint-adr-shape.py docs/adr`, and the aggregator's `Require every
  gate` step fails the run unless that step succeeds — so blocking cannot be
  dropped by an omitted step.
- **Owner:** eugenelim

## Alternatives considered

- **Ship RFC-0102 § 6's original advisory-then-blocking rollout** — rejected
  against *the corpus was already clean*: the migration that phase exists to
  protect against had already landed, so shipping it would add a phase with
  nothing to be advisory about, an unenforced check masquerading as a safety
  net.
- **Scan only files touched by a pull request** — rejected against *no
  reduction in scope*: a record nobody touches again would never be checked,
  which contradicts the whole-corpus guarantee this delivery ships.

## References

- [RFC-0102](../rfc/0102-mechanically-checkable-adrs.md) § 6 — the original
  advisory-then-blocking rollout this decision narrows to blocking-only.
- [ADR-0027](0027-adr-format-is-madr-aligned-but-lean.md) — deferred "There is
  **no mechanical ADR-status lint** today … adding one is a separate,
  RFC-gated convention"; this is that convention, discharged.
