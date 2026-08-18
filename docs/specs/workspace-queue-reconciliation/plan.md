# Plan: workspace-queue-reconciliation

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `workspace.toml` — three `[work]` moves by tool, one by hand, one appended comment.
- `docs/specs/workspace-queue-reconciliation/{spec.md,plan.md}` — this contract.

**What demonstrates done**
- Goal-based throughout. No code changes, so no test earns its place; the engine's
  own reconciliation output is the assertion.
- `repair-apply` reports `operations_applied: 3`, all three `applied: true` (AC1).
- `repair-plan` lists the fourth under `manual_findings` with
  `reason: "type2-queue-canonical-blocked"` (AC2).
- `reconcile` reports `type2=0`, `type3=0`, `complete: true` (AC3).
- `tomllib` parses `workspace.toml` and confirms each moved path's new collection.
- `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .` clean.
- `make ci` green before the PR opens.

**What I am NOT changing**
- No code, no lint, no CI, no dependency.
- Not the Type 1 finding — dispositioned in AC4, deliberately not registered.
- Not `tracker-refresh-writeback`'s spec, plan, or `needs`. It becomes ready as a
  consequence; reanchoring it is separate tracked work.
- Not the reanchor entries, `[backlog].open` membership, or any `needs` edge.

## Declined patterns

- **Tempted:** hand-edit all four entries in one pass — it is the same edit and the
  script was already written. **Declined:** `repair-apply` re-reads each spec's
  `Status` at apply time and revalidates canonical eligibility immediately before an
  atomic, comment-preserving write. A hand move skips all three protections to save
  nothing. The tool is used where it applies and bypassed only where it refuses.
- **Tempted:** register `rfc0088-round10-measurement` to drive Type 1 to zero, since a
  clean report is satisfying and I had approval to do it. **Declined:** the evidence
  says registration is selective (121 of 372) and RFC-0088 tracks its own rounds, so
  the entry would be invented rather than restored. A zero I manufactured is worse
  than a finding I explained. Recorded as AC4 and re-confirmed with the owner.
- **Tempted:** add a `needs` edge or a marker on `tracker-refresh-writeback` so the
  reanchor is enforced rather than merely documented. **Declined:** that is the
  `ini-008-anchor-staleness-check` design, which needs a real mechanism (`needs`
  carries no timestamp) and an engine change. Faking it with a dependency edge would
  encode a false claim about what depends on what.
- **Tempted:** leave the fourth entry alone, since the tool refused it and refusals
  are usually right to respect. **Declined:** the refusal is about needing *review*,
  not about the move being wrong. Respecting it means measuring the consequence and
  deciding, which is what § Consequence records — not declining to act.
- **Tempted:** while reconciliation is open, also clear the five `missing_plan` and
  three `missing_artifact` canonical findings. **Declined:** each needs a plan
  authored or a spec directory created. That is real work, not reconciliation.

## Tasks

### T1 — Read the findings; confirm no duplicate-membership trap (no writes)
- **Mode:** goal-based. `Done when:` every one of the four target paths is confirmed
  present in exactly one collection before any move.
- **Tests:** no stub (goal-based).
- **Status:** done. All four were queue-only; a `tomllib` parse ruled out the
  duplicate-membership hazard a queue→shipped move would otherwise create.

### T2 — AC1: apply the three auto-eligible moves
- **Mode:** goal-based. `Done when:` `repair-apply` reports three applied.
- **Tests:** no stub (goal-based).
- **Touches:** `workspace.toml` (via tool).

### T3 — Measure the consequence of AC2 before making it
- **Mode:** goal-based. `Done when:` the `canonical.ready` delta from the fourth move
  is known and recorded in the spec.
- **Tests:** no stub (goal-based).
- **Status:** done. Simulated on a scratch copy; `tracker-refresh-writeback` is the
  single addition. Surfaced to the owner with the alternative before proceeding.

### T4 — AC2: move the fourth entry by hand
- **Mode:** goal-based. `Done when:` `tomllib` finds it in `ini-008.work.shipped` and
  in no queue, with its Group 5 comment lines intact.
- **Tests:** no stub (goal-based).
- **Touches:** `workspace.toml`.

### T5 — AC3 + AC4: verify and disposition
- **Mode:** goal-based. `Done when:` `reconcile` reports `type2=0`/`type3=0`, the
  Type 1 disposition is written into the spec, and the live instance is appended to
  `ini-008-anchor-staleness-check`.
- **Tests:** no stub (goal-based).
- **Touches:** `workspace.toml` (comment only), `spec.md`.
