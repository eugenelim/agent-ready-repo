# ADR-0007: Ship the doc-drift spec-metadata lint to adopters as a work-loop skill script

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-05-29
- **Deciders:** eugenelim
- **Supersedes:** none (narrows ADR-0006 in part — see Decision)
- **Related:** ADR-0006; RFC-0016 (§ Errata); `docs/specs/lint-work-loop-delivery/`; `docs/specs/doc-drift-prevention/`

## Context

ADR-0006 and RFC-0016 concluded that the mechanical spec-metadata lint
(`lint-spec-status.py`) would live **only** as catalogue governance — in
`tools/`, run from CI — because the lint "cannot reach adopters." A load-bearing
reason given was that "linters don't project: `tools/lint-*.py` have no `packs/`
source."

That projection premise is **false**, and RFC-0016 now carries an Approver-signed
§ Errata saying so. A skill's `scripts/` folder is a first-class projecting
surface that already ships governance Python helpers to all four adapters:
`governance-extras`'s `new-adr` / `new-rfc` `scripts/next-ordinal.py` (with their
bundled tests) and `core`'s `work-loop` `scripts/loop-cohort.py`. A linter given a
`packs/` source under a skill's `scripts/` projects identically. Of RFC-0016's
three "cannot reach adopters" reasons, only the third — there is no PR-open
lifecycle event to fire a *fail-closed* gate in an adopter repo — survives.

ADR-0006 records the same now-corrected sub-claim ("The mechanical gate is
catalogue-only … has no `packs/` source"). ADRs are corrected by a superseding
ADR, not by errata, so this ADR records the narrowing.

## Decision

> We will ship the spec-metadata lint to adopters as a **`work-loop` skill
> script** (`packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`),
> invoked by the agent at the work-loop's finish-time checklist — available and
> agent-invoked, **not** fail-closed. The catalogue additionally runs it as a
> fail-closed CI gate via `make build-check`.

This **narrows ADR-0006 in part**: ADR-0006's core decision — doc-drift
prevention for adopters is delivered by *construction + judgment* — still stands.
What changes is ADR-0006's sub-claim that the mechanical lint is delivered *only*
as catalogue governance: the adopter delivery model is now construction +
judgment **plus an agent-invocable mechanical check on every adapter that has
Python**. ADR-0006 is not superseded wholesale and keeps its `Accepted` status;
this ADR is the authority on the lint's delivery surface.

## Consequences

**Positive:**
- Adopters with a Python runtime get a runnable spec-metadata check, on every
  adapter — not construction + judgment alone.
- The catalogue keeps its fail-closed CI gate; source↔projection stays
  drift-checked by `make build-check`.
- Reuses the proven `loop-cohort.py` skill-script model — no new mechanism.

**Negative:**
- Not fail-closed for adopters (no PR-open hook event; copilot can't fire hooks)
  — it is an *available* check, not enforcement. This is the one RFC-0016 reason
  that survives.
- Still a Python bet: the script no-ops where Python is absent (same bet
  `loop-cohort.py` / `next-ordinal.py` already make).
- One more projected skill script to maintain.

**Neutral / to revisit:**
- Whether to drive the adopter warn-rate down enough to promote any invariant to
  hard remains deferred (RFC-0016 Q3 / `spec-code-ref-lint`).

## Alternatives considered

- **Leave it catalogue-only (status quo, ADR-0006).** Rejected: rests on the
  false projection premise; needlessly withholds a deliverable check from
  adopters.
- **A fail-closed gate in adopter repos.** Rejected: infeasible — no PR-open
  lifecycle event, and copilot can't fire hooks (RFC-0016 reason #3, which
  stands).
- **A new top-level linter package shipped to adopters.** Rejected: heavier than
  needed; the skill-`scripts/` surface already exists and is proven.
