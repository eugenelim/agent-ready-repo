# Implementation log

Notes accumulated during EXECUTE. **Deliberately not in `spec.md` or `plan.md`:**
those are pinned by `approved_spec_hash` / `approved_plan_hash`, and editing them
mid-wave trips the cohort drift guard — which it already did once, in wave 1. These
get folded into the plan at the `CODE-HUMAN-GATE`, where amending the contract and
re-pinning the baseline is expected rather than an interruption.

## W1 · T0

- **`plan.md`'s contract and the cohort baseline disagree.** The plan says it "is
  allowed to change as you learn — while its Status is `Drafting` or `Executing`",
  and `_LEGAL_AFTER_APPROVAL` admits plan status `Executing`. But
  `approved_plan_hash` pins plan *content*, and `canonical_contract` splices out
  only the status *token*. So the tooling forbids exactly the mid-execution
  amendment the contract invites. Worth raising as a work-loop finding, not just a
  local annoyance.
- **`canonical_contract`'s CRLF/CR fold is currently unreachable via file input.**
  `Path.read_text()` decodes with universal newlines. Mutation-confirmed: deleting
  the fold moves no file-derived digest. It becomes load-bearing once
  `read_managed_text` decodes bytes itself.
- **A digest-level assertion about line endings cannot fail**, for two independent
  reasons (universal newlines above, plus `.gitattributes` `eol=lf` preventing a
  CRLF fixture from being committed at all). Test the fold on strings.

## W2 · T1a

- **Sequencing deviation from the plan, and why.** The plan puts `GuardResult` in
  T1b, but AC13 requires `__all__` plus a `_MODULE_COMPLETE` sentinel whose
  completeness check is `set(__all__) <= set(dir(mod))`. If T1a declared the final
  `__all__` — including the six guards — the check would fail for the whole of T1a.
  So T1a declares `__all__` covering exactly what T1a provides (the relocated
  names, `GuardResult`, `read_managed_text`, `validate_run_id`,
  `assert_status_legal`) and T1b extends it with the six guards, moving the
  full-set pinning test to T1b. Same commit boundary either way; the plan already
  allows T1a and T1b to land together when import health requires it.
- **The relocation is done by extraction, not retyping.** A script slices the exact
  source segments out of `loop-cohort.py` by anchor and reassembles them, so
  `canonical_contract` moves byte-for-byte by construction rather than by care.
  T0's `test_recomputed_digests_match_golden` is the proof.

### T1a outcome

- `_loop_guards.py` is 792 lines; `loop-cohort.py` 1826 → 1661. All 18 relocated
  names stay reachable as `loop-cohort` module attributes, so no call site in the
  file changed and the six mutation verbs are untouched.
- **`cmd_approve_plan` was worse than the review reported.** One hash pair sits in
  an `except (OSError, UnicodeDecodeError)` a `ValueError` escapes; the second pair
  was *entirely unguarded and wrote its result*. Both now convert. It holds the
  cohort lock, and neither `with_state_lock` (StateLockError only) nor `main()`
  (KeyboardInterrupt only) would have caught it.
- **`AC11` needed more than documentation.** I first left `validate_run_id` /
  `assert_status_legal` unwrapped and explained why in their docstrings. That is not
  what AC11 asks: an *unexpected* exception would still traceback out of a
  lock-holding verb. Added `contained_reason`, which converts to a **non-empty
  reason** and never to `None` — `None` there means "proceed", so a containment that
  produced it would be `approve-plan` sailing past a check that never ran.
- Two bugs in my own new test file, both caught by running it: the load-failure
  cases invoked the *real* script rather than the sandbox copy (so all eight passed
  for the wrong reason), and the capability scan tripped on its own docstrings —
  which discuss `subprocess` precisely to explain its absence. The scan is now over
  the AST.
