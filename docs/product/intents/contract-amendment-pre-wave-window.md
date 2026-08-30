# Contract amendment reachable before the first wave runs

- **Status:** Draft
- **Level:** feature

## Disposition — shipped 2026-08-29 as a bug fix

The outcome below was achieved. The evidence binding is now conditional on completed
work existing; `begin_contract_amendment`'s `missing_evidence` check
(`loop-cohort.py:768`) remains the sole enforcer. Owner authority, reason reference,
run identity, and the approved-hash pins stay unconditional. Shipped in core 2.15.5.

**The governing authority is RFC-0099 § 7, which this intent did not cite.** That
section (Accepted 2026-08-27) defines the post-seal correction route as "legal from
implementation, verification, or review" and lists only preservation effects, with no
completed-work precondition. The guard landed 2026-08-26 in `be51a9847` — one day
*before* RFC-0099 closed — and nobody re-checked the shipped code when the governing
decision landed. So this was non-conformance with an accepted RFC, not merely a
contract weaker than its implementation.

**Three claims below are wrong. Corrected here rather than in place, so the original
reasoning stays legible:**

1. **"three independent guards" — there are four.** The intent misses
   `parse_completed_task_evidence_entries` (`loop-cohort.py:621` pre-fix), which
   rejected an empty entry tuple independently. Changing only the three named guards
   would not have made the route reachable.
2. **"No existing test asserts the empty-completed refusal is correct, so the change
   turns no passing test red as a false regression" — false.** Two deliberately
   written cases asserted it, in
   `packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py`: `:205`
   (`completed_task_evidence: {}`) and `:207` (`current_wave_index: 0`). Both had to
   be removed. Verifying this assumption before starting would have changed the
   estimate materially.
3. **Line citations had drifted.** Correct pre-fix locations were
   `loop-cohort.py:621`, `:650` (`_normalize_completed_task_evidence_map`), `:669`
   (`begin_contract_amendment`), `:746-747` (the empty-completed refusal), and `:772`
   (`missing_evidence`) — not `:618`, `:714`, and `:740`.

**On the "Before starting this" section below:** `docs/specs/sealed-baseline-replacement`
does **not** exist in this branch, and no spec owns this route. The only specs
mentioning `contract-amendment` are `close-work-extraction-and-immediate-disposition`
(Shipped — the implementation corrected here, left untouched as a frozen artifact) and
`credential-broker-contract` (an unrelated sense of the phrase). The concern was sound
to raise; it did not materialise.

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
