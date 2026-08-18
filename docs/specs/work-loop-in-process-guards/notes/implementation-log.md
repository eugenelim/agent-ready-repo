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

## W6 · T4 + T5

- **The budget test caught a flaw in my own edge counter, on its first run.** It
  computed 3 edges against a constant of 2, because `ast.walk` on a `FunctionDef`
  includes the **decorator expression** — so the walk descended into
  `@_locked("transition")`, found its `_resolve_spec_dir`, and counted the one edge
  that runs BEFORE `sl.exclusive()` and must be excluded. Scoped to `fn.body`.
- **The budget comment now states both halves.** The old one implied a single number
  bounded everything, which stopped being true the moment the guards moved
  in-process: the subprocess half is time-bounded at `TIMEOUT_S × edges`, the
  in-process half is byte-bounded at 8 MiB (~1.0 s for `canonical_contract`) and NOT
  time-bounded. The hung-mount residual is named and accepted, because there is no
  stdlib way to bound a blocking read without threads or signals and adding either
  under the lock is a worse trade.
- **Mutation-verified five ways.** Raising the constant to 6, lowering it to 1,
  dropping a `timeout=`, and swapping git for another program all turn the budget
  test red. The fifth — a bare `import subprocess` in the guard layer — is caught by
  T1a's import allowlist instead, and an actual *use* is caught by the budget test.
  The two cover each other exactly; neither alone is sufficient.
- **The no-child-Python recorder double-counted until fixed.** `subprocess.run` is
  implemented on top of `Popen`, so patching both made one logical spawn arrive
  twice — and the inner `Popen` legitimately carries no `timeout=`, because `run`
  consumes it for `communicate()`. Every bounded `git rev-parse` was therefore
  flagged as unbounded. A re-entrancy depth guard makes one logical spawn one record.
- **The recorder proves it detects.** Two self-checks: spawn a real child Python and
  assert it is flagged; spawn bounded git and assert it is not. Without those, a
  recorder that silently failed to patch would keep the whole file green forever.

## W7 · T2 (metadata) — a core version bump is THREE files, and the third is not marketplace.json

Round-4 review established that `pack.toml` and `.claude-plugin/plugin.json` must
agree (CAT-V-005), and that `core` is absent from `.claude-plugin/marketplace.json`
— so the repo-wide "three files" knowledge topic looked like it reduced to two here.
It does not. `make ci` found the third:

    tests/roster/test_workspace_status_projection.py
      asserts _product_release_heading_version(changelog, "core") == pack_version

`docs/product/changelog.md` must carry a `### [core][<version>]` heading at the
bumped version. Neither `make build-check` nor the pack suite covers this — only the
repo-wide roster suite under `make ci` does, which is a good argument for running the
real gate rather than the fast subset.

Worth folding back into the knowledge topic: for a pack absent from
marketplace.json, the three files are pack.toml, the pack's plugin.json, and the
product changelog.

## Environment, not the change

`make ci` first reported 12 failed / 27 errors. Every one was
`OSError: No space left on device` from a volume at 100% (3 GiB free of 460 GiB) —
including three in the roster source-anchor test that passes standalone. After
reclaiming space the same suite ran 303 passed / 1 failed, and that one failure was
the real changelog gap above. Reporting the first number as a regression would have
been wrong; reporting it as "just the disk" without re-running would have been
wrong too.

## W8 · diff-review repair — contract amendments pending the human gate

Three edits belong in the pinned contract and are held here instead, because
`plan.md` and `spec.md` are pinned by `approved_plan_hash` / `approved_spec_hash`
and every CODE-state transition re-checks them. Applying them now makes
`reviewers-clean` refuse; the documented recovery is a `loop-cohort reset` pair,
which is destructive and needs human authorization. So they land at
`CODE-HUMAN-GATE`, where amending and re-pinning is the expected move.

1. **`plan.md` T1b — the canonical import allowlist says twelve names and the
   module imports thirteen.** `collections.abc.Mapping` is the thirteenth. The
   review found the duplicated value had already drifted: the test restated a
   locally-widened list rather than reading the canonical one. Applied once, then
   reverted to restore hash currency; re-apply at the gate.
2. **`spec.md` AC17 — renumber to twelve steps.** AC17 lists eleven, but the
   source has twelve: it folds crash recovery into one step (the code has
   `_recover_engine_state_tmp` then `_recover_pending`) and merges the state
   decision with the outbox/state finalization. The test's anchor list is already
   one-for-one with the twelve, and its double-violation pairs are now cited as
   2 vs 5 and 9 vs 10 against that numbering.
3. **The finish checklist** — tick or defer every AC, `Status: Shipped` on the
   spec, `Status: Done` on the plan, and re-sync the `docs/specs/README.md` row,
   which still reads `Draft`.

**Worth folding back into the work-loop itself.** This is the second time the
same friction bit this run, and it is a design finding, not an accident: the plan
contract says it "is allowed to change as you learn — while its Status is
`Drafting` or `Executing`", `_LEGAL_AFTER_APPROVAL` admits plan status
`Executing`, and yet `approved_plan_hash` pins plan *content* while
`canonical_contract` splices out only the status *token*. So the tooling forbids
exactly the mid-execution amendment the contract invites, and the only sanctioned
escape is a destructive reset that clears the retry counters. A correction found
during review — a wrong count, a stale citation — is the ordinary case, not an
exceptional one.

## W9 · manual-QA results (spec.md's Visual/manual QA row, plan.md T-manual 1–3)

Recorded because a docstring claiming a perturbation goes red is not a record of a
run. Item 2 was already recorded in W5; items 1 and 3 are below.

### Item 1 — the documented walk, end to end

`spec-ready → reviewers-clean → spec-approved → plan-approved → plan-locked →
wave-complete`, plus the two cohort mutations, against a throwaway git repo. Every
observed line, in order, with its exit code:

    loop-engine init … --mode code --json
      {"run_id": "beb565ab-…", "feature": "walk", "mode": "code"}                  exit=0
    loop-cohort init … --run-id beb565ab-…
      loop-cohort: initialised …/state.json (feature=walk run_id=beb565ab-…)       exit=0
    loop-engine transition … spec-ready
      transition 'SPEC-PLAN-DRAFTING' → 'spec-ready' → 'SPEC-PLAN-REVIEW' (seq=1)  exit=0
    loop-cohort plan check-current …
      loop-cohort: stop — plan_review_status: pending                              exit=1
    loop-engine transition … reviewers-clean
      transition 'SPEC-PLAN-REVIEW' → … → 'SPEC-HUMAN-GATE' (seq=2)                exit=0
    loop-engine transition … spec-approved
      transition 'SPEC-HUMAN-GATE' → … → 'PLAN-HUMAN-GATE' (seq=3)                 exit=0
    loop-engine transition … plan-approved
      transition 'PLAN-HUMAN-GATE' → … → 'SPEC-PLAN-APPROVED' (seq=4)              exit=0
    loop-cohort approve-plan … --expect-run-id beb565ab-…
      approve-plan for walk (approved_spec_hash=ceb42c3412ec… plan=494916697601…)  exit=0
    loop-cohort schedule … --expect-run-id beb565ab-…
      topological order: wave 1: T1 / wave 2: T2; schedule persisted (2 wave(s))   exit=0
    loop-engine transition … plan-locked
      transition 'SPEC-PLAN-APPROVED' → … → 'CODE-IMPLEMENTATION' (seq=5)          exit=0
    loop-engine transition … wave-complete
      transition 'CODE-IMPLEMENTATION' → … → 'CODE-VERIFICATION' (seq=6)           exit=0
    loop-engine status … --json
      state=CODE-VERIFICATION last_event=wave-complete transition_sequence=6       exit=0

The `exit=1` on `plan check-current` is the expected pre-approval signal the skill
documents, not a failure. Six transitions, no traceback anywhere, and the final state
matches the transition table.

### Item 3 — the `canonical_contract` perturbations go red

Two independent perturbations, each reverted after measuring:

    removed the CRLF/CR fold  → test_canonical_contract_folds_line_endings FAILED
    changed _STATUS_PLACEHOLDER → test_recomputed_digests_match_golden      FAILED

Baseline for both: `test_recomputed_digests_match_golden` passes over all 48 pinned
digests. The second is the more valuable of the pair — the placeholder is the literal
`spec.md` forbids renaming, because a rename silently re-pins every baseline, and this
shows the golden ledger catches exactly that.

## W9 · four more contract statements to amend at the human gate

Adding to the W8 list. All four are statements the code no longer supports, so one
gate pass should re-pin a correct contract rather than a partly-corrected one.

4. **`spec.md` AC13's `__all__` description.** It says a pinning test asserts `__all__`
   equals "the relocation list plus those four plus the six guards". The module exports
   21 names; the relocation list in `plan.md` T1a has 22 mostly-private names, ten of
   which are deliberately NOT exported, and `__all__` adds `contained` /
   `contained_reason`. The test pins the real surface; the prose describes a different
   set. (`non_negative_int` was also dropped from `__all__` in this round — it had no
   caller outside the module.)
5. **`spec.md` and `plan.md` still cite `_evaluate`** (four places), which this change
   deleted for having no caller. The W3 log note "‑ `_evaluate` kept, narrowed" is
   likewise superseded and is retired by this entry.
6. **AC15's "four cohort verbs"** is now six: `init` and `review record` also had reads
   newly routed through the bounded reader. `init`'s template is a repo-shipped file, so
   no user-facing input surface changed; `review record`'s report is user-supplied, and
   its symlink case was deliberately preserved by resolving the path first, so only
   genuinely unbounded shapes (FIFO, over-cap) are refused — with the reason now printed
   rather than discarded.
7. **`plan.md` T1a names `_read_managed_json` / `_read_md_status`** as relocated
   symbols; the shipped names have no leading underscore.

**Also for the gate, and a genuine single-source problem rather than a typo:** AC6
declares the import allowlist "canonically in `plan.md`'s T1b", but
`tools/lint-pack-test-boundary.py` forbids the test from reading `plan.md`, so the two
copies cannot be joined and the prose cannot be enforced. This is the drift that
already fired once this round. The fix is to name the TEST as the canonical location
and have `plan.md` reference it, so there is one statement of the fact instead of two.

## W9 · AC20's projected-copy load route, recorded

The third of AC20's three load routes (direct file-path invocation, the tests'
importlib harness, and the projected copies) had no recorded probe. Run against both
projections after `make build-self`:

    $ python3 -c "importlib load .claude/skills/work-loop/scripts/_loop_guards.py"
      loaded: __all__=21 names, _MODULE_COMPLETE=True
    $ python3 -c "importlib load .agents/skills/work-loop/scripts/_loop_guards.py"
      loaded: __all__=21 names, _MODULE_COMPLETE=True
    $ python3 .claude/skills/work-loop/scripts/check-spec-status.py \
          docs/specs/work-loop-in-process-guards --expect Implementing
      check-spec-status: OK — Status: Implementing at …/spec.md          exit=0

The last line is the load-bearing one: a projected CLI resolves its sibling guard
module by `Path(__file__).resolve().parent`, so it exercises the projected copy rather
than the pack source. All three routes work, and the projections are byte-identical to
`packs/core/` (AC26).

AC19's read-count assertion was also mutation-checked while confirming it: caching a
state snapshot across guards drops the count from 3 to 0 and turns it red, so the
"no shared snapshot" claim has a real artifact rather than a mock-shape one.
