# Contract amendment reachable before the first wave runs

- **Status:** Draft
- **Level:** feature

## Outcome

`contract-amendment` succeeds when the plan baseline is sealed and no wave has
yet run, so a defect found in that window is corrected by amendment rather than
by resetting both state machines and losing run identity.

## Opportunity

The window is reachable on every run: `plan-locked` fires, `schedule` sets
`current_wave_index` to 0, and review then finds a spec or plan defect before
wave 1 executes. The transition table already declares the route legal —
`loop-engine.py:546` maps `("CODE-IMPLEMENTATION", "contract-amendment")` to
`SPEC-PLAN-DRAFTING` — but three independent guards make the input set provably
empty:

- `loop-engine.py:1251` refuses the transition when no `--completed-evidence-ref`
  is supplied.
- `loop-cohort.py:618` (`_normalize_completed_task_evidence_map`) rejects an
  empty mapping with `completed_task_evidence is required`.
- `loop-cohort.py:714` (`begin_contract_amendment`) refuses when the computed
  `completed` set is empty, which it always is at `current_wave_index == 0`
  because `waves[:0]` is an empty slice and `completed_task_ids` is still `[]`.

Any task ID supplied to satisfy the first guard is then rejected at
`loop-cohort.py:605` as `names non-completed task`, because `allowed_task_ids` is
empty. No argument vector reaches the amendment.

The documented contract is weaker than the implementation: the lifecycle
reference requires only that *every completed task* carry an evidence binding,
which is vacuously true when none has completed, and the real invariant is
already enforced independently by the `missing_evidence` check at
`loop-cohort.py:740`. All three guards are preconditions the contract never
asked for.

## Before starting this

Grep `docs/specs/` for `contract-amendment` first. A peer session reports that a
spec named `sealed-baseline-replacement` re-specifies this route — it was not
present in this branch when this intent was written, so it is unmerged or lives
in another worktree. Two things follow.

First, do not author competing work: if that spec already owns the route, tick
its criteria and annotate its plan rather than building from this intent.

Second, the evidence recorded above bears on that spec directly. The route it
proposes is already shipped: `("CODE-IMPLEMENTATION", "contract-amendment") ->
"SPEC-PLAN-DRAFTING"` is a legal transition at `loop-engine.py:546`, and
`amendment_history`, `amendment_pending`, `completed_task_ids` and
`completed_task_section_hashes` are all live fields in `loop-cohort.py`. An
assumption that no return exists from CODE states to spec-plan drafting is
false against this tree. That is that spec owner's call, not this intent's.

## Assumptions

- The fix keeps the invariant and only makes the evidence binding conditional on
  completed work existing; the `missing_evidence` check remains the sole
  enforcer.
- No existing test asserts the empty-completed refusal is correct, so the change
  turns no passing test red as a false regression.
- `loop-cohort.py` is not byte-pinned; the golden-digest test re-derives from
  `canonical_contract` rather than pinning file bytes.
- Mutation proof per guard: with zero tasks completed the amendment succeeds;
  with one completed task and no binding it still refuses.

## Source

- Mode: repo-origin
- Locator: docs/specs/spec-authoring-discipline/spec.md
- Revision: local-2026-08-28
