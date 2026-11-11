# ADR-0166: A read-only `frontier` query in `ferryman` finds the next work and keeps `ask` unless an order is configured

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0144 (`dispatch.py` stays pinned); ADR-0164 (the program that hosts it); ADR-0170 (the tracker seam it reads); ADR-0159 (the brief-level runner); ADR-0180 (reconciliation, owns brief-scoped order); ADR-0184 (the verified-identity rule for the `light` label)

## Context

An unattended run must choose its next work, and a silent pick is the risk. `dispatch.py` sees specs only and answers `ask` when several are ready. The relation script sees intents, briefs and specs. Neither is to be edited, and `Priority:` never decides order.

## Decision

We will add one read-only `frontier` query to `ferryman` that composes existing scripts and never starts work.

- **D1:** `frontier` runs `dispatch.py` and the relation script by subprocess, gets tracker candidates through `ferryman`'s own tracker module, and edits none of them.
- **D2:** It returns `frontier.v1` with items of five kinds: `shape-intent`, `author-brief`, `author-spec`, `review`, `run-spec`.
- **D3:** The default policy keeps `ask`. An order applies only when the owner configures `list` or `kind-first` in `ferryman-config`. A model never picks the order.
- **D4:** If the tracker fails, `frontier` returns repository items alone with the finding `tracker-unavailable`. If a script reports an incomplete snapshot, it returns `decision: refuse` and no item.
- **D5:** On one tree and one tracker snapshot, `frontier --json` gives identical bytes.
- **D6:** A ticket counts as light only when a verified identity applied the label named by `[frontier] light_label` (default `light`; see ADR-0184). It appears only in `light_candidates`. It is never an item, and a human starts it.
- **D7:** A `waves` view layers `run-spec` items by `Depends on:` edges and derives them without authoring them.
- **D8:** Brief-scoped order is out of scope here. ADR-0180 owns it.

## Consequences

**Positive:**
- No pinned script changes, and an unattended run never picks silently.
- A partial view cannot start the wrong work.

**Negative:**
- With several ready specs and the default policy, the unattended run stops and waits for the owner.
- The exact `shape-intent` predicate is unverified and is settled at implementation.

**Revisit if:** the owner wants `Priority:` to order work, which needs its own decision.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a determinism test over a 50-tree fixture corpus, a write-absence test, and a policy test for two ready specs. These are designed targets, not yet run.
- **Owner:** eugenelim

## Alternatives considered

- **Frontier inside each supervisor:** each would duplicate the derivation, and the pinned supervisor cannot change.
- **A model-picked order:** a model verdict would replace a human check.
- **Read `Priority:` and amend `lint-priority-field.py`:** the field's contract forbids it from deciding order.
- **Keep `ask` only:** the unattended run could never proceed with two ready specs.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/04-frontier-and-waves.md`
