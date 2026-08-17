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

## W3 · T1b

- **I overwrote the pre-change goldens, and nearly shipped it.** Re-ran
  `generate_goldens.py` after the extraction to pick up an unrelated fixture tweak.
  That command *looks* idempotent and is not: it captures whatever the tree
  currently does, so `before` was rewritten with the post-change behaviour. Every
  parity assertion would then have compared the change against itself and passed no
  matter what broke — the exact tautology T0 exists to prevent. Caught only because
  I happened to diff the result. Restored from git, and the generator now **refuses
  to overwrite** unless passed `--force`. The refusal message says why, because the
  mistake is easy and the symptom is silence.
- **Disk exhaustion mid-wave.** `OSError: [Errno 28]` from a test's `mkdir`, not a
  regression — the volume was at 100% (159 MiB free of 460 GiB). My own contribution
  was ~695 MB of pytest temp dirs and 8 MiB oversized-artifact fixtures rewritten on
  every run. Fixed properly: the *test* now sparse-extends with `os.truncate`, which
  trips the reader's `st_size` pre-check for one block instead of 8 MiB. The
  *generator* keeps filling for real, because it must keep reproducing the committed
  capture byte-for-byte and a sparse file changes the artifact's content — and it
  runs once, not every invocation.
- **`_evaluate` kept, narrowed.** It takes an already-read state dict, so it cannot
  simply forward to `check_phase` (which reads). It now delegates the cap arithmetic
  to the shared `_non_negative_int`, so the validation has one implementation even
  though the entry point is duplicated.
- **`check_artifact_status` had a real symlink hole, found by test not by reading.**
  I wrote `target = (spec_dir / filename).resolve()` and then read `target`. But
  `resolve()` dereferences a symlink at the final component, so `O_NOFOLLOW` never
  saw the link and a symlinked `spec.md` was accepted — meaning AC15's
  `artifact-integrity` change would not actually have happened for that row. Now two
  paths: confinement verifies the **resolved** path (canonicalize-then-verify-prefix,
  the CWE-73 depth), and the read uses the **unresolved** one. Audited the other five
  reader call sites; all already pass unresolved paths.

## W4 · T2

- **The goldens caught two of my bugs in one run.** `check_artifact_status`'s reasons
  embedded `check-spec-status: `, so the adapter's own prefix doubled it —
  `check-spec-status: check-spec-status: spec.md Status is …`. A CLI prefix inside
  the guard layer is precisely the CLI concern that layer is supposed to be free of;
  reasons are now prefix-free like every other guard's.
- **Check order turned out to be load-bearing.** Putting the single-component rule
  before the confinement check re-diagnosed `--file ../outside.md` as a component
  problem, changing an existing message with no `change_reason`. Confinement now runs
  first, so that row keeps `--file must be within spec-dir` and the component rule
  catches only the genuinely new case: a multi-component path resolving *inside*
  `spec_dir`.
- **AC9's scanner note was right to be rewritten.** `check-spec-status.py` was never
  in the semgrep rule's `paths.include`, so no coverage is lost; the rule file now
  says so, and names the behavioural test that replaces the exemplar.
- The loader-identity test is no longer skipping — two of three copies exist and
  compare equal after normalization.

## W5 · T3 + T6

- **The headline property, measured.** Re-ran the read-only topology probe over the
  same nine transition paths used for the before-state: **0 child Python processes**
  on every one, exit codes identical (0 for the eight legal transitions, 1 for the
  failing guard). `sys.executable` in `loop-engine.py` went 16 → 0 references; the
  only remaining mention is a comment recording what was removed. One
  `subprocess.run` survives — `git rev-parse`, with its timeout.
- **The engine's duplicate `_read_managed_json` is gone.** It delegates to the shared
  reader now. Worth noting it was the copy *without* `O_NONBLOCK`, so leaving it would
  have left the engine's own `engine-state.json` read able to block on a FIFO.
- **Two bugs in the parity table, both mine.** The argv was inverted — `loop-cohort`
  takes its verb first and the spec dir after, `check-spec-status` the reverse — so
  every cohort row failed with an argparse "invalid choice" that had nothing to do
  with parity. An explicit `SPEC` placeholder in the table replaces the guess. Then
  three rows still failed because their SUCCESS message interpolates
  `spec_dir.name`, which `normalize()` cannot strip (it is a basename, not a path);
  those rows now pin the generator's directory name as table data, rather than
  re-capturing the goldens to match — which is the thing that must never happen.
- **AC17's ordering assertion is mutation-verified.** Swapping the run-ID preflight
  with the transition-table check turns it red; so does removing a single anchor,
  which is the vacuity mode `e6d4c14a` warns about.
