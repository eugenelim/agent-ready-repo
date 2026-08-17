# Plan: work-loop in-process guards

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

The guard algorithms already exist exactly once — inside `loop-cohort.py`'s
read-only verbs and `check-spec-status.py`. What does not exist is a way to
*call* them. Every current caller reaches them through `argparse` → verb
function → `stop()`/`print()` → exit code, which is why the engine reaches them
by starting an interpreter.

So the shape is **extract, then rewire** — not reimplement. A new sibling module
`_loop_guards.py` becomes the home of the guard decisions and the helpers they
need. `loop-cohort.py` and `check-spec-status.py` shrink to thin adapters: they
keep their `argparse`, their `stop()` prefixes, and their success messages, but
the *decision* is no longer theirs. The engine calls the same functions directly.

Two rounds of pre-EXECUTE review turned this from a pure move into a
move-plus-hardening, and everything traces to one root cause: **the child-process
boundary was doing work nobody had written down.** It bounded every guard's file
reading with a 20-second subprocess timeout, and it converted every unexpected
exception into an exit code. Delete the child and both properties vanish
silently — a FIFO at `spec.md` hangs the engine past the lock's 300-second stale
threshold and lets a contender reclaim a live lock, and an `OverflowError` from an
`Infinity` retry cap becomes a traceback out of a lock-holding process. So the
guard layer owns bounded, non-blocking, type-checked reads and an
exception-containment boundary as first-class requirements.

Round two's lesson was the opposite shape: the *mitigations* were accreting risk
faster than they closed it. A hand-rolled cache-free module loader, specified to
close a `__pycache__` concern, produced four distinct defects of its own and
needed a `bandit` `exec` suppression — so it is out, and `exec_module` stays with
`sys.dont_write_bytecode` around it. The residual (a pre-existing `.pyc` can
still be read) is exactly today's exposure and is named in AC13 rather than
traded for new code in a privileged position. What survived from that round is
the part that was genuinely load-bearing: `O_NONBLOCK` and the widened `except`
clauses. `sys.modules` registration was itself withdrawn in round 3 — it was only
ever needed to make a frozen dataclass work under future-annotations, and dropping
that import removes the need entirely; and the stream *save/restore* form turned
out to be theatre, replaced by a real swap on the loader that actually execs the
reconfiguring module.

Proof discipline changed too. Two original tests compared moved code against
itself — the digest check and the message-preservation check — the antipattern
this repo already recorded. Both are now golden fixtures captured from the
**pre-change** tree, over a corpus **copied into the pack's own fixtures
directory** because `tools/lint-pack-test-boundary.py` forbids a pack test from
reading above its pack. That is T0, and it comes first.

The riskiest part remains the extraction. `canonical_contract` is 100 lines whose
output is a pinned hash; it moves byte-for-byte, `_STATUS_PLACEHOLDER`'s literal
included.

## Constraints

- **ADR-0074** — stdlib-only helpers a skill needs are authored *in the skill*.
- **ADR-0061** — status recognition has one implementation on this path.
- **The lock-hold budget is one budget**, and after this change it must state
  honestly which half is time-bounded and which is only byte-bounded.
- **The FSM is out of scope.** No transition-table edit, no new event, no state
  schema change, no reordering of `cmd_transition`.
- **`tools/lint-pack-test-boundary.py`** forbids a pack test from reading above
  `packs/core/`. Every fixture this change adds lives inside the pack.
- **`tests/roster/test_work_loop_root_validation.py`** is a source-content anchor
  on `loop-cohort.py`, counting `= _resolved_report(args.report)` occurrences.
  Both sites are outside this change; do not disturb them.
- **No new dependency.** Python 3.11+ stdlib only.

## Construction tests

**Integration tests:**

- `test_loop_guards_parity.py` — one fixture table driven twice, once through the
  callable API and once through the real CLI as a subprocess, with the CLI's
  streams compared against T0's normalized pre-change goldens rather than against
  the API's own output. Spans T0, T1b, T2, T6.
- The existing `test_loop_engine.py`, `test_loop_cohort.py`,
  `test_loop_cohort_schedule.py`, `test_loop_cohort_max_iter_single_source.py`,
  `test_loop_engine_events_jsonl.py`, `test_loop_concurrency.py`,
  `tests/roster/test_work_loop_root_validation.py`, and
  `tools/lint-pack-test-boundary.py` are the regression bar across every task.

**Manual verification:**

- Drive `python loop-engine.py transition` against a real spec directory through
  a full `spec-ready → reviewers-clean → spec-approved → plan-approved →
  plan-locked` walk plus one CODE-state transition; record stdout, stderr, exit.
- Re-run the read-only topology probe over the nine representative paths.
- Perturb one line of the relocated `canonical_contract` and confirm the digest
  test goes red (the mutation check for AC5).

## Design (LLD)

`Shape: service`.

### Design decisions

- **A frozen dataclass result.** `GuardResult(ok, reason, message, data)` with a
  `__post_init__` asserting `ok == (reason is None)`, so the two fields cannot
  disagree and an adapter written `if result.reason:` cannot read a containment
  bug as success. Adapters branch on `ok`. Rejected: raising on refusal; bare
  `str | None` (loses the success message the CLIs must print).
  Traces to: AC6, AC15.
- **`exec_module`, kept, unregistered, and `_loop_guards.py` omits
  `from __future__ import annotations`.** These two go together. A frozen dataclass
  under future-annotations fails at class creation when its module is absent from
  `sys.modules`, which pushed an earlier revision toward registering — but
  `exec_module` does not clean a registered entry when the body raises, so
  registration means hand-rolling the cleanup the standard `import` machinery does
  for free, and it turns the module into a session-global singleton whose memoised
  parser and patched attributes leak across every pack test in a pytest run.
  Dropping the future-annotations import removes the requirement instead of
  patching it: PEP 604 unions evaluate natively above the 3.11 floor, and `ruff`
  does not select `FA`, so nothing is lost. `_loop_guards.py` therefore matches
  `_statelock.py`'s precedent exactly — unregistered, memoised in a module global —
  and carries a one-line comment explaining the deliberate style departure.
  Rejected: registering (cleanup + singleton cost); a `NamedTuple` (loses the
  `__post_init__` invariant); a hand-rolled `compile`/`exec` loader (four defects
  and a `bandit` suppression for a residual unchanged from today).
  Traces to: AC13.
- **A completeness sentinel, because a clean truncation does not raise.** A
  `_loop_guards.py` truncated mid-file at a statement boundary — an interrupted
  `make build-self` or checkout — loads without error and returns a handle missing
  later names. Each loaded module therefore declares `__all__` near the top and
  `_MODULE_COMPLETE = True` as its **last** statement; the loader requires
  `_MODULE_COMPLETE` truthy and `set(mod.__all__) <= set(dir(mod))`. An enumerated
  symbol list was specified first and **rejected**: it is order-blind, it would be
  restated in each of the three loader copies, and the obvious spelling of it
  ("every relocated name plus the six guards") silently omits `GuardResult`,
  `read_managed_text`, `validate_run_id`, and `assert_status_legal` — converted or
  new rather than relocated, and precisely the names whose absence breaks the
  mutation path. A pinning test fixes `__all__`'s contents. Traces to: AC13.
- **Three copies of a ~15-line loader, policed by a defined normalization.** This is
  a decision, not a discovery: the loader cannot live in `_loop_guards.py` (it is
  what loads it), and `check-spec-status.py` importing `loop-cohort.py` to borrow it
  is the 1800-line-CLI import the Design rejects. So `loop-cohort.load_guards()`,
  `loop-engine._guards()`, and `check-spec-status`'s copy are three instances of one
  small function. **The canonical normalization, defined here and nowhere else:**
  `ast.parse` each file, locate the loader `FunctionDef`, and compare
  `ast.dump` of its **body** with (a) the function name and (b) the single
  stop-prefix string literal excluded. A plain `ast.dump` comparison is red on day
  one — the three differ in function name, module-global name, and prefix
  (`loop-cohort:` / `loop-engine:` / `check-spec-status:`) — and a normalization
  loose enough to pass could strip the body, so the test **also asserts the three
  prefix literals differ from each other**, which makes an over-broad exclusion
  detectable. Traces to: AC3, AC13.
- **An exception-containment decorator catching `Exception` only.** `@_contained`
  converts any escaping `Exception` into `GuardResult(ok=False, reason=…)` with an
  `internal-error:` marker. `BaseException` — `KeyboardInterrupt`, `SystemExit` —
  and any `_statelock`-derived exception propagate untouched: `StateLockLost`
  means "the mutation ran and may have been overwritten", and containing it would
  report a comfortable refusal over a real integrity event. Reasons are
  whitespace-collapsed, length-capped, and never carry raw artifact content.
  Rejected: enumerating expected exception types per guard — that is exactly how
  `OverflowError` slipped through the child-process era's implicit containment.
  Traces to: AC10, AC11.
- **`O_NONBLOCK` is the control that makes bounded reads real.** The type
  pre-check is path-based (`lstat` → `S_ISREG`) and therefore racy; `os.open` with
  `O_RDONLY | O_NOFOLLOW` blocks indefinitely on a FIFO swapped in afterwards, so
  the post-open re-check never runs. Adding `O_NONBLOCK` returns immediately and
  is a no-op for regular files, letting the post-open `fstat` do the rejecting.
  Traces to: AC8, AC22.
- **Move the helpers, don't copy them.** The canonical relocation list lives in
  T1a and nowhere else. Rejected: importing `loop-cohort.py` from the engine — an
  1800-line `argparse` CLI to reach a hash function. Traces to: AC3, AC4.
- **`_validate_run_id` and `_assert_status_legal` keep their `stop()`-returning
  signatures in `loop-cohort.py`** as wrappers over reason-returning functions, so
  none of the six mutation verbs' call sites change. Signed off against the
  `Ask first` rail. Their `None`-means-success shape is why AC11 requires a
  contained failure to return a non-empty reason. Traces to: AC3, AC11.
- **Path confinement stays where it is, and the callee validates only what a
  callee can.** The three callers' resolvers are unchanged;
  `check-spec-status.py`'s bare `Path(...).resolve()` is the weakest and stays so
  under AC15's argument freeze. The guard therefore documents the precondition and
  checks `spec_dir` exists and is a directory — a check that can actually fail —
  rather than re-testing "absolute, no `..`", which holds by construction after
  any `resolve()`. `filename` is constrained to a single path component, because
  `O_NOFOLLOW` guards only the final one. Traces to: AC7, AC9.
- **No cross-guard snapshot.** Each guard calls `read_state()` itself; a test
  counts the reads. The residual (engine holds only its own lock while reading the
  cohort's state) is pre-existing and recorded against
  `loop-outbox-cross-spec-rmw`. Traces to: AC19.
- **The engine's duplicate `_read_managed_json` goes away.** Byte-identical to the
  cohort's, and the engine imports the shared module anyway. Traces to: AC3.

### Data & schema

No schema change; `schema_version = 1` and every field unchanged. What is added is
validation: numeric fields guards compare
(`implementation_retry_count`, `review_retry_count`,
`max_implementation_retries`, `max_review_retries`, `current_wave_index`) are
checked as non-negative integers, and the reader rejects non-finite numbers via
`parse_constant`. Coercible inputs whose verdict changes are enumerated in T0's
matrix. Traces to: AC8, AC16.

### Interfaces & contracts

```
GuardResult(ok: bool, reason: str | None, message: str | None, data: dict | None)
    # __post_init__: assert ok == (reason is None)

# spec_dir: caller-confined absolute resolved Path; callee checks S_ISDIR
check_identity(spec_dir, *, expect_run_id: str | None) -> GuardResult
check_plan_current(spec_dir, *, require_schedule: bool) -> GuardResult
check_schedule_current(spec_dir) -> GuardResult
check_phase(spec_dir, *, phase: str) -> GuardResult
check_wave(spec_dir, *, expect: str, wave_index: int | None) -> GuardResult
check_artifact_status(spec_dir, *, filename: str, expect: str) -> GuardResult
```

Traces to: AC6, AC7, AC8, AC9, AC10, AC15.

### Component / module decomposition

```
loop-engine.py transition
    → in-process read-only guard API   (_loop_guards.py)
        → bounded, non-blocking, type-checked state/artifact reads
              ↳ lint-spec-status.py    (canonical status parser)

loop-cohort.py / check-spec-status.py CLI
    → the same read-only guard API     (_loop_guards.py)
        → CLI-specific printing and exit codes
```

New: `_loop_guards.py`. Unchanged: `_statelock.py`, `lint-spec-status.py`
(except four `timeout=` ride-alongs, see T4). Shrunk to adapters:
`loop-cohort.py`'s `cmd_identity`, `cmd_plan_check_current`,
`_schedule_check_current_impl`, `cmd_check`/`_evaluate`, `cmd_wave_check`; all of
`check-spec-status.py`. Rewired: `loop-engine.py`'s `_run_id_preflight`,
`_schedule_check_current`, the ten dispatched `_GUARDS` functions, the two
indirect delegates, `_read_engine_state`. Deleted: `_run`, `LOOP_COHORT`,
`CHECK_SPEC_STATUS`, the engine's duplicate `_read_managed_json`, and the two dead
`_guard_plan_check_current*` functions. Traces to: AC1, AC2, AC3.

### Failure, edge cases & resilience

- **Module load failure is a refusal, not a traceback, and not an import error.**
  The re-binding must be eager (a test reads `mod.DEFAULTS` straight after
  `exec_module`, with no verb invoked), so a raising module-level `load_guards()`
  would traceback during `import loop-cohort` where no CLI handler exists.
  Instead the module-level call is wrapped: on failure it binds a sentinel, and
  every verb entry checks the sentinel and refuses with a message naming the path,
  the failure mode, and the remedy (`make build-self` / restore the file) — the
  style `_statelock.py:326-344` already uses. The loader re-raises any load
  exception as `ImportError` so `SyntaxError` (a direct `Exception` subclass) is
  covered by the existing `except (ImportError, OSError)` clauses.
- **Unloadable canonical parser refuses.** `_read_md_status`'s
  `except ImportError: return None` becomes an `UnreadableArtifact`-class failure.
  Only an absent status *token* is still skipped.
- **Bounded readers.** `read_managed_json` and a new `read_managed_text` both:
  `lstat`, require `S_ISREG`, `os.open(O_RDONLY | O_NOFOLLOW | O_NONBLOCK)`,
  `fstat` re-check type and dev/ino, read up to the cap, re-verify identity.
  **The canonical cap is 8 MiB** (`_MAX_MANAGED_JSON_BYTES`), reused for text:
  `canonical_contract` costs roughly 0.14 s/MiB, so ~1.0 s at the cap — affordable
  against a 300 s stale threshold, and that arithmetic goes in the budget comment.
- **`TEMPLATE_PATH` is read through the bounded reader, and `DEFAULTS` becomes
  lazy** so no file I/O happens at module import — otherwise the first guard call
  inside the critical section triggers an uncapped read of `assets/state.json`.
- **Stream hygiene, on the right loader.** `lint-spec-status.py` calls
  `sys.stdout.reconfigure(...)` at module scope, and the loader that execs it is
  `_lint_spec_status()` **inside `_loop_guards.py`** — lazily, during a guard call,
  not inside `load_guards()`. So that is where the swap belongs. For the duration
  of the exec, `sys.stdout`/`sys.stderr` are swapped to a throwaway
  `io.TextIOWrapper(io.BytesIO())` and restored in a `finally`. Not
  `sys.__stdout__`: those are `None` under pythonw, embedded, and detached-stdio
  contexts, which would convert a working environment into a total-refusal one. A
  `TextIOWrapper` always has `reconfigure`, is never `None`, and swallows writes.
  Snapshot-and-restore of the *references* is explicitly not the mechanism —
  `reconfigure` mutates in place, so restoring a reference restores nothing.
- **Mutation verbs widened.** `_read_md_status`, `cmd_plan_check_current`,
  `_schedule_check_current_impl`, and `_schedule_run_impl` gain `ValueError` in
  their `except` clauses so an unsafe artifact refuses instead of raising —
  `_schedule_run_impl` runs under the cohort state lock.
- **`resolve()` failures** caught as `(OSError, RuntimeError)` — defensive against
  3.11/3.12 symlink-loop behavior, which did not reproduce on 3.13.
- Traces to: AC8, AC10, AC11, AC12, AC13, AC14.

### Quality attributes (NFRs)

- **AC1/AC23** — verified structurally by instrumenting every spawn primitive and
  failing on any Python-shaped argv. Never a latency bar (a `Never do` rail).
- **AC17/AC21/AC22** — critical section unchanged; the budget names what it does
  and does not bound.
- **AC20** — no `sys.path` mutation, no cwd dependence, no install step, loaded
  once per process, no new bytecode cache entry.

### Dependencies & integration

None added. See T1b for the canonical import allowlist.

## Tasks

### T0: Pre-change behavior is captured as golden fixtures, inside the pack, before anything moves

**Depends on:** none

**Touches:** `packs/core/tests/skills/work-loop/fixtures/corpus/`, `packs/core/tests/skills/work-loop/fixtures/golden_digests.json`, `packs/core/tests/skills/work-loop/fixtures/golden_cli_streams.json`, `packs/core/tests/skills/work-loop/golden_support.py`

**Tests:** (the fixtures are the artifact; self-checks guard them — goal-based + TDD)

- `tools/lint-pack-test-boundary.py` passes: every fixture and every path the
  tests read lives under `packs/core/`. Verifies AC25.
- The frozen corpus holds ~30 files and covers the three cases
  `canonical_contract`'s comments call out: a plan with a checkbox, a file with an
  odd fence count, and a spec with a lowercase-`c` `Acceptance criteria` heading.
  The first two are copied from the live tree
  (`m2-frame-situation/plan.md` has 9 fences); the third is **hand-authored**,
  because the live corpus has zero. Verifies AC5.
- The digest fixture covers every corpus file. Verifies AC5.
- The CLI-stream fixture covers every failure branch of all six read-only verbs,
  keyed by `(argv-shape, scenario)`, recording normalized returncode, stdout and
  stderr — including `plan_review_status: pending`, which carries no verb prefix.
  Each row carries a `before` field (the recorded pre-change verdict). The rows
  whose verdict this change intentionally alters — AC16's coercible-numeric inputs
  and AC9's `--file` narrowing — additionally carry an `after` field, and are the
  only rows asserted against `after`; every other row is asserted against `before`.
  A self-check asserts `after` is present **only** on rows named by AC15's two
  exceptions, so a future edit cannot quietly relax a golden by adding one.
  Verifies AC15, AC16.
- A self-check asserts every recorded `stderr` is exactly one line and contains no
  `Traceback`, so the fixture cannot enshrine a pre-existing traceback as expected
  behavior. Verifies AC15.
- A round-trip check asserts `normalize(normalize(s)) == normalize(s)`, so the
  normalizer is idempotent and cannot mask a real difference. Verifies AC15.

**Approach:**

- Copy the corpus into `fixtures/corpus/` as `NNN-<name>.md` files. Hashing
  `docs/specs/*` in place is a **hard gate failure** under
  `case_pack_tests_stay_in_pack`, and would also go stale on any unrelated spec
  edit — one change fixes both.
- **The canonical normalization function** lives in `golden_support.py` and is the
  only definition; capture and comparison both call it. It replaces the resolved
  spec-dir path with `<SPEC_DIR>`, any 64-hex run of `[0-9a-f]` with `<SHA>`, and
  any 36-char UUID with `<RUN_ID>`. Without it a literal captured in one
  `tmp_path` cannot equal a replay in another, and the comparison would silently
  relax to substring matching — the weak assertion AC15 exists to replace.
- Write a one-shot generator (kept in this spec's `notes/`, not shipped) that runs
  against the **current** tree: digests via `loop-cohort.sha256_canonical_contract`
  over `fixtures/corpus/`; streams by invoking each CLI as a subprocess over a
  fixture matrix, normalized.
- Commit the generated JSON. From here the fixtures are the independent
  expectation; the generator is not re-run.
- **Generate before T1a touches anything.**

**Done when:** both fixture files and the corpus are committed, the self-checks
and the idempotence check pass, `tools/lint-pack-test-boundary.py` passes, and
re-running the generator against the frozen corpus reproduces the fixtures
byte-for-byte.

### T1a: The shared module exists, the helpers have moved, reads are bounded, and every existing cohort suite is still green

**Depends on:** T0

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`, `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`

**Tests:**

- `test_loop_guards.py::test_digests_match_golden` — the relocated
  `sha256_canonical_contract` reproduces T0's `golden_digests.json` exactly over
  `fixtures/corpus/`. Verifies AC5.
- `test_loop_cohort.py`, `test_loop_cohort_schedule.py`,
  `test_loop_cohort_max_iter_single_source.py` pass unmodified — the check that no
  mutation verb broke and that the eager re-binding held. Verifies AC3, AC15.
- `tests/roster/test_work_loop_root_validation.py` and
  `bash packs/core/tests/skills/work-loop/test-loop-cohort.sh` both pass unmodified —
  the latter is gated by `tools/test-all.py` and drives exactly the six verbs being
  converted, so it is the closest pre-existing contract test for them. Verifies AC25.
- Loading `_loop_guards.py` and `lint-spec-status.py` writes **no new**
  `__pycache__` entry; `sys.dont_write_bytecode` holds its prior value after both a
  successful and a failed load; and `_loop_guards` is **absent** from `sys.modules`.
  Verifies AC13, AC20.
- A frozen `GuardResult` is constructible and frozen-enforcing after load, in an
  unregistered module — the regression test for the no-future-annotations decision,
  which fails with `AttributeError: 'NoneType' object has no attribute '__dict__'`
  if the import is reintroduced. Verifies AC13.
- Each of the six load-failure modes yields a one-line refusal naming path,
  failure mode, and remedy, with no traceback — including at `import loop-cohort`
  time, where the fallback bindings must keep the module importable. A seventh case
  asserts the loaded parser did not run its `__main__` block. An eighth truncates
  the module mid-body and asserts nothing reusable survives; a ninth truncates it at
  a clean statement boundary (loads without raising, missing later symbols) and
  asserts the required-symbol check turns it into a load failure. Verifies AC13.
- A parametrised case over **every** `loop-cohort.py` verb asserts each refuses with
  the one-line load-failure message when the fallback bindings are active. Verifies
  AC13.
- Stream handling is verified on **values, not identity**: the caller's
  `sys.stdout.encoding` and `.errors` are unchanged across a load, and a case whose
  `sys.stdout` is an `io.StringIO` asserts the guard returns its real verdict rather
  than an `internal-error:` refusal. An object-identity assertion is explicitly not
  used — `reconfigure` mutates in place, so it passes vacuously. Verifies AC13.
- The three loader copies (`loop-cohort.load_guards`, `loop-engine._guards`,
  `check-spec-status`'s) are textually identical after normalization. Verifies AC3.
- A spec directory reached through a **symlinked ancestor** is accepted, not
  refused — the false-refusal surface `pytest`'s `/private/var`-resolving `tmp_path`
  hides. Verifies AC8.
- Bounded reads: an oversized file, a FIFO, a directory, a symlink, and a
  mid-read-replaced file each refuse with a reason — asserted on the **reason**,
  never on elapsed time. Verifies AC8.
- `TEMPLATE_PATH` is read through the bounded reader, and importing
  `_loop_guards` performs no file I/O (`DEFAULTS` is lazy) — asserted by patching
  the reader and confirming zero calls at import. Verifies AC8.
- All **four** `ValueError` conversion sites: `_read_md_status` (widened to
  `(OSError, UnicodeDecodeError, ValueError)`, raising `UnreadableArtifact`, which
  `_assert_status_legal` already catches — the path that protects the six mutation
  verbs), plus `cmd_plan_check_current`, `_schedule_check_current_impl`, and
  `_schedule_run_impl` directly. Each yields a one-line refusal with no traceback,
  and `_schedule_run_impl`'s asserts no state was written while holding the cohort
  lock. Verifies AC12.
- With `lint-spec-status.py` unloadable, `check_plan_current` and
  `check_schedule_current` **refuse** rather than skipping the status-regression
  check; with a status line merely absent, they still skip. Verifies AC14.
- `validate_run_id` and `assert_status_legal` return a non-empty reason (never
  `None`) when contained. Verifies AC11.

**Approach:**

- Create `_loop_guards.py`: docstring naming it the shared read-only guard API,
  stating the no-print/no-parse/no-exit/no-mutate/no-spawn contract and
  `spec_dir`'s precondition. No `sys.stdout.reconfigure` — it is a library.
- **The canonical relocation list** (only copy; Design references it):
  `_MAX_MANAGED_JSON_BYTES`, `_read_managed_json`, `state_path_for`, `read_state`,
  `_lint_module`, `_lint_spec_status`, `_sha256_bytes`, `_STATUS_PLACEHOLDER`,
  `_AC_HEADING_RE`, `_HEADING_RE`, `_BOLD_LEAD_RE`, `_BOLD_DEPTH`, `_BOTH_CAUSES`,
  `canonical_contract`, `sha256_canonical_contract`, `UnreadableArtifact`,
  `_read_md_status`, `_LEGAL_AFTER_APPROVAL`, `TEMPLATE_PATH`,
  `_template_max_implementation_retries`, `_template_max_review_retries`,
  `DEFAULTS`. Moved byte-for-byte apart from the changes named below —
  `_STATUS_PLACEHOLDER` keeps its exact literal because it feeds the digest.
- Add `O_NONBLOCK` to `_read_managed_json`'s open flags and add `read_managed_text`
  with the same shape; point `sha256_canonical_contract` and `_read_md_status` at
  it. Route `TEMPLATE_PATH` through it.
- **`_lint_spec_status()` is a changed-on-move helper, not an unchanged one.** It is
  the second loader — lazy, memoised, executed inside a guard call — and it gets the
  same four controls as `load_guards()`: `lstat` + `S_ISREG` on
  `lint-spec-status.py`; `sys.dont_write_bytecode` saved/set/restored; the
  `io.TextIOWrapper(io.BytesIO())` stream swap (this is the loader that needs it,
  because `lint-spec-status.py` calls `reconfigure` at module scope); and a
  completeness check on `parse_status`, `extract_status_token`, `_STATUS_RE`,
  `_SECTION_HEADING_RE`, `_HTML_COMMENT_RE`, `_AC_DONE_RE`.
- Add `parse_constant` rejection of `NaN`/`Infinity`.
- Convert the two `stop()`-returning helpers to reason-returning:
  `assert_status_legal(verb, *paths) -> str | None`,
  `validate_run_id(state, expect_run_id, verb) -> str | None`. Keep their two
  message sets distinct from `cmd_identity`'s — different decisions.
- Change `_read_md_status`'s `except ImportError: return None` to raise
  `UnreadableArtifact`; re-word `_lint_spec_status`'s `ImportError` text to a
  module-neutral form (the one string that legitimately changes).
- `_loop_guards.py` **omits `from __future__ import annotations`**, with a one-line
  comment saying why (frozen dataclass in an unregistered module). Annotations use
  PEP 604 unions directly.
- Add `load_guards()` to `loop-cohort.py` — the canonical ~15-line loader body the
  other two callers copy verbatim: `lstat` + `S_ISREG` on the module path;
  `prev = sys.dont_write_bytecode` / set `True` / restore `prev` in a `finally`;
  `spec_from_file_location` + `module_from_spec` + `exec_module` with **no**
  `sys.modules` registration; the completeness check (`_MODULE_COMPLETE` truthy and
  `set(mod.__all__) <= set(dir(mod))`) on the result; any exception re-raised as
  `ImportError`; memoised in a module global. **No stream handling here** —
  `_loop_guards.py` calls no `reconfigure` at module scope, so there is nothing to
  contain; the swap belongs to `_lint_spec_status()`, which execs the module that
  does.
- Call it at module level inside a `try`. **On failure, bind `DEFAULTS = {}` and
  every callable to a stub that RAISES a module-local `GuardsUnavailable`** — not a
  stub that *returns* the reason. Two reasons, both learned the hard way:
  a returning stub makes a missed sentinel check **silent** rather than loud —
  `cmd_approve_plan` would write the reason string into `approved_spec_hash` and
  `write_state_atomic` it under the lock, and if both sides of a later drift
  comparison are stub-produced they compare *equal*, so the drift guard passes
  vacuously. And binding `DEFAULTS` to a literal would create a **third** copy of
  the retry-cap value, which `test_loop_cohort_max_iter_single_source.py` exists to
  prevent (it already polices two: `DEFAULTS` against the template, and the
  `_template_max_*` `fallback=` default hand-synced to it). Raising when *called* is
  safe; only *import* must not raise. Eager binding is still required —
  `test_loop_cohort_max_iter_single_source.py:41-52` reads `mod.DEFAULTS` straight
  after `exec_module` with no verb invoked.
- Check the load sentinel **once, at the single dispatch chokepoint** — in
  `main()` after `parse_args` and before `args.func(args)` — not by enumerating
  ~20 verb entries. One chokepoint cannot be missed for a verb; twenty entries can.
  The parametrised per-verb refusal test stays as the positive check.
- `DEFAULTS` must be **lazily populated but eagerly bound**: a plain function or
  `cached_property` satisfies the no-IO-at-import requirement but breaks
  `mod.DEFAULTS["max_implementation_retries"]`. Bind a `Mapping` subclass at module
  scope whose first `__getitem__` performs the bounded template read.
- The template read must **refuse rather than fall back** on an integrity-class
  failure: `_template_max_*` currently catches `ValueError` and returns the
  hard-coded default, so the bounded reader's `ValueError` for an oversized,
  non-regular, or symlinked `assets/state.json` would silently yield 5/5 caps.
  Narrow the catch to `FileNotFoundError` (a genuine adopter tree with no template)
  and let integrity failures raise.
- Keep `_validate_run_id` and `_assert_status_legal` in `loop-cohort.py` as
  wrappers mapping a returned reason to `stop(...)`.
- Widen the `ValueError` handling at the three **tested** sites: `_read_md_status`
  (raising `UnreadableArtifact`), `_schedule_run_impl` (both its raw
  `plan_path.read_text()` and its hash call, under the cohort lock), and
  `cmd_approve_plan` (its already-approved-branch hash, whose current
  `except (OSError, UnicodeDecodeError)` a `ValueError` escapes, **and** its
  currently-unguarded `state["approved_spec_hash"] = sha256_canonical_contract(...)`
  write). Retain the handler in `cmd_plan_check_current` and
  `_schedule_check_current_impl` as labelled-unreachable defence in depth.
- Declare `__all__` near the top of `_loop_guards.py` and `_MODULE_COMPLETE = True`
  as its last statement.

**Done when:** the suites above are green, the digest golden matches, the mutation
check goes red on a perturbed `canonical_contract`, and `make lint-ruff` passes.

### T1b: The six guard decisions are callable, silent, contained, and non-mutating, and the cohort's read-only verbs are adapters over them

**Depends on:** T1a

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`, `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`, `packs/core/tests/skills/work-loop/test_loop_guards.py`

**Tests:**

- Purity: each guard emits zero bytes on stdout and zero on stderr **and returns
  its expected `ok`/`reason` verdict** — the verdict half is what stops the row
  passing on a guard that refused for an unrelated reason. Capture uses a
  `TextIOWrapper`, not an `io.StringIO`: a `StringIO` has no `reconfigure`, so
  capturing through one turns the lazy parser load into a silent
  `internal-error:` refusal that emits nothing. Verifies AC6.
- AST: imports match **the canonical allowlist — `contextlib`, `dataclasses`,
  `functools`, `hashlib`, `importlib.util`, `io`, `json`, `os`, `re`, `stat`,
  `sys`, `pathlib`** (twelve names) — and the module contains no `argparse`, no
  `sys.exit`, no `sys.argv`, no `.reconfigure(` call, no *unrestored* stream
  mutation, no top-level write or command execution, and no reference to
  `subprocess`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`, `os.fork`,
  `multiprocessing`, `socket`, `urllib`, or `http`. Notes on three entries:
  `functools` is required for `@_contained`'s `functools.wraps` — the idiom both
  sibling scripts already use, without which every wrapped guard loses `__name__`
  and `__doc__`; `io` is required for the throwaway
  `io.TextIOWrapper(io.BytesIO())` the parser loader swaps in; and `sys` is on the
  list for `sys.dont_write_bytecode` and the `sys.stdout`/`sys.stderr` swap, with
  the prohibitions attribute-scoped. Verifies AC6, AC21.
- AST: no `Status`-matching pattern is compiled in `_loop_guards.py` — the
  allowlist admits `re`, so this needs its own assertion. Verifies AC4.
- `GuardResult.__post_init__` rejects `ok=True` with a reason and `ok=False`
  without one; a source assertion confirms no adapter branches on `reason`.
  Verifies AC6.
- Non-mutation: the recursive listing of the spec directory and of the repo-root
  `.loop-run/` — names and bytes — is identical before and after all six guard
  calls; the assertion fails if either directory is absent at snapshot time; no
  `.engine-state-*.json.tmp` and no `state.json.lock` appears. Verifies AC18.
- Containment: an injected `Exception` from each guard's read path yields
  `ok=False` with a non-empty `internal-error:`-marked reason, never a raise; an
  injected `BaseException` **propagates**. No `_statelock`-injection row: the
  containment boundary lives wholly inside a layer that never locks, so such an
  exception cannot originate inside a contained call, and naming the class would
  force an import AC6's allowlist forbids. Verifies AC10.
- Reason hygiene: a reason built from a multi-line exception is collapsed to one
  line and truncated, and a field-validation failure names the field and its type
  without echoing the artifact value. Verifies AC10.
- `spec_dir` that is missing or is a file (not a directory) refuses. Verifies AC7.
- `check_artifact_status` refuses a multi-component `filename`, a dot-only
  `filename` (`.`, `..`, `...` — the charset admits all three, the class
  `0cb5c213` fixed a day earlier), an out-of-`spec_dir` target, a non-regular
  target, and a symlink swapped in after the check. It **accepts** a legitimate
  leading-dot name, so the guard is segment equality rather than a narrowed
  charset. Verifies AC9.
- `check_identity`: `ok=True` with `data["run_id"]` on match; `ok=False` on
  mismatch, `schema_version != 1`, absent `state.json`. Verifies AC2, AC8.
- `check_plan_current`: `ok=False` for pending review status, drifted spec hash,
  drifted plan hash, regressed post-approval status, missing `spec.md`, missing
  `plan.md`; with `require_schedule=True` also for `plan_hash !=
  approved_plan_hash`, empty `schedule_waves`, out-of-range `current_wave_index`.
  Verifies AC2, AC8.
- `check_schedule_current`: `ok=False` for drifted `plan_hash`, missing `plan.md`,
  illegal post-approval plan status, **and missing or malformed `state.json`**.
  Verifies AC2.
- `check_phase`: reads state first and refuses on missing or malformed
  `state.json` for *every* phase including `implement` — the refusal `cmd_check`
  performs today before reaching the stub. Then `ok=True` for `implement` on a
  readable state; `ok=False` at each cap; `ok=False` for an unknown phase; and the
  `phase != "implement"` schema-version branch covered. Verifies AC2, AC8.
- `check_wave`: correct at first, middle, last index for both expectations;
  `ok=False` on explicit `wave_index` disagreement, on unknown `expect`, **and on
  missing or malformed `state.json`**. Verifies AC2.
- Numeric validation: `Infinity`, a negative value, a float, and a string-typed
  counter each refuse; the rows whose verdict differs from today's `int()`
  coercion match T0's captured expectations. Verifies AC8, AC16.
- Fresh reads: three guard calls in one process perform three `state.json` reads,
  counted by patching the reader. Verifies AC19.

**Approach:**

- Add `GuardResult` (frozen dataclass, `__post_init__` invariant) and
  `@_contained` (catches `Exception`; re-raises `BaseException` and
  `_statelock`-derived; normalizes the reason).
- Add the six guard functions, each reproducing its verb's decision sequence and
  its exact reason and success strings minus the CLI prefix.
- Reduce `cmd_identity`, `cmd_plan_check_current`, `_schedule_check_current_impl`,
  `cmd_check`/`_evaluate`, and `cmd_wave_check` to: resolve spec-dir → call the
  guard → `stop(result.reason)` or `print(result.message)`, branching on `ok`.
  `cmd_identity` keeps its `--json` branch, fed from `result.data`.

**Done when:** `test_loop_guards.py` is green and the cohort suites plus the
roster anchor stay green.

### T2: `check-spec-status.py` reaches its decision through the shared API and its CLI contract is unchanged

**Depends on:** T1b

**Touches:** `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py`, `tools/semgrep/argv-path-boundary.yml`

**Tests:**

- Every `check-spec-status` case in `test_loop_engine.py` passes unmodified, and
  each is additionally asserted against T0's normalized goldens. Verifies AC15.
- A `--file` outside `spec_dir`, and a multi-component `--file`, each exit
  non-zero with a one-line message. Verifies AC9, AC15.
- Failure paths emit one line and no traceback. Verifies AC15.

**Approach:**

- Add the **third copy of the canonical loader body** from T1a to this file, and
  replace `_load_status_parser` and the inline decision with
  `load_guards().check_artifact_status(spec_dir, filename=args.file, expect=args.expect)`.
  Three copies is the decision recorded in Design, not an accident: the loader
  cannot live in the module it loads, and importing `loop-cohort.py` here to borrow
  it is the 1800-line-CLI import the Design rejects. T1a's normalized-source
  identity test is what keeps the three from drifting.
- Keep `argparse`, the defaults, the `check-spec-status: ` prefix, and the
  `check-spec-status: OK — Status: <expect> at <path>` success line, formatted by
  the adapter from `data["path"]`.
- Delete the now-unused direct `lint-spec-status.py` loader.
- Re-point **all four** live citations of `check-spec-status.py:72-80` as the
  reference "resolve, then `is_relative_to` in the same function" pattern — a
  rename audit must enumerate comment, docstring, and error-message sites, not just
  code:
  **(1)** `tools/semgrep/argv-path-boundary.yml` (the `pattern-not-inside` comment);
  **(2)** `tools/semgrep/fixtures/argv-path-boundary/negative.py:7`;
  **(3)** `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:400`;
  **(4)** `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py:1274`.
  Sites 3 and 4 have projected copies, so `make build-self` must run after.
- Note in the AC9 record that **no semgrep coverage is lost**: the rule's
  `paths.include` never listed `check-spec-status.py`. The real consequence is that
  the file stays ineligible for the rule's expansion ratchet, because it keeps a
  bare `Path(args.spec_dir).resolve()` with no in-function containment.
- Record the CodeQL `py/path-injection` result on `check-spec-status.py` before and
  after — the containment moving behind an importlib boundary may change what the
  interprocedural pass follows. A new finding is a review item, not an automatic
  blocker.

**Done when:** every `check-spec-status` case is green against the goldens and the
semgrep comment names the new location.

### T3: A transition runs every FSM guard in-process, launching no child Python interpreter

**Depends on:** T1b, T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`

**Tests:**

- `test_loop_engine.py` passes, edited only where it asserts an engine message
  that legitimately shed a nested prefix. Verifies AC2, AC17.
- Run-ID-preflight cases still exit non-zero and leave `engine-state.json`
  byte-identical. Verifies AC2, AC18.
- Every guard case refuses and permits exactly as before. Verifies AC2.
- A double-violation case proves the earlier step's refusal wins, driven on the
  concrete pair AC17 names: a `wave-passed` event with **both** a missing
  `--wave-index` and an unreadable `engine-state.json` must refuse on the
  wave-index (step 2), not on the read (step 4). A second pair covers steps 8 and 9
  (drifted schedule plus a failing event guard → schedule refusal). Verifies AC17.
- A source-order assertion over `cmd_transition`'s body confirms the eleven steps
  appear in AC17's order, so the `Never do` reordering rail has an artifact rather
  than only prose. Verifies AC17.
- `test_loop_engine_events_jsonl.py` and `test_loop_concurrency.py` pass
  unmodified. Verifies AC17.
- AST: `loop-engine.py` contains no `sys.executable` reference and no `.py` string
  literal beyond `_statelock.py` and `_loop_guards.py`. Verifies AC1.

**Approach — the canonical shell-out inventory. 16 `sys.executable` sites; the two
`plan-locked` rows carry two sites each, so 14 rows cover 16 sites:**

| Site | Line(s) | Disposition |
| --- | --- | --- |
| `_run_id_preflight` | 966 | → `check_identity` |
| `_schedule_check_current` | 979 | → `check_schedule_current` |
| `_guard_check_phase_implement` | 552 | → `check_phase(phase="implement")` |
| `_guard_check_phase_gates_failed` | 561 | → `check_phase(phase="gates-failed")` |
| `_guard_wave_check_more` | 573 | → `check_wave(expect="more", wave_index=…)` |
| `_guard_wave_check_last` | 584 | → `check_wave(expect="last")` |
| `_guard_check_phase_review` | 593 | → `check_phase(phase="review")` — **indirect delegate** via `_guard_check_phase_review_on_code_review` |
| `_guard_check_spec_status` | 601 | → `check_artifact_status("spec.md", "Shipped")` — **indirect delegate** via `_guard_check_spec_status_on_code_review` |
| `_guard_spec_approved` | 610 | → `check_artifact_status("spec.md", "Approved")` |
| `_guard_plan_approved` | 620 | → `check_artifact_status("plan.md", "Approved")` |
| `_guard_plan_locked_code` | 631 **and** 636 | → `check_artifact_status` then `check_plan_current(require_schedule=True)`, same order — **2 sites** |
| `_guard_plan_locked_spec_plan` | 647 **and** 652 | → `check_artifact_status` then `check_plan_current(require_schedule=False)`, same order — **2 sites** |
| `_guard_plan_check_current_require_schedule` | 533 | **DELETE** — defined, never referenced anywhere in the repository |
| `_guard_plan_check_current` | 542 | **DELETE** — same |

- Add the cached `_guards()` loader beside `_statelock()`, same shape as
  `loop-cohort.load_guards()`, same `ImportError`/`OSError` → refusal contract, so
  one process loads the module once regardless of guard count.
- Rewrite each site to call its guard and return
  `f"<existing prefix>: {result.reason}"`, preserving every engine prefix verbatim
  and shedding both nested markers (`loop-cohort: stop — `,
  `check-spec-status: `).
- Delete `_run`, `LOOP_COHORT`, `CHECK_SPEC_STATUS`, and the engine's duplicate
  `_read_managed_json`; point `_read_engine_state` at the shared reader.
- Keep `subprocess` and `_get_repo_root` — git is still needed and still bounded.
- Leave `cmd_transition`'s body order, `@_locked`, the CODE-state pre-check
  condition, and the `done` exemption untouched.

**Done when:** `pytest packs/core/tests/skills/work-loop/test_loop_engine.py
test_loop_engine_events_jsonl.py test_loop_concurrency.py` is green, ruff reports
no undefined name, and the topology probe reports 0 child Python processes on all
nine representative paths.

### T4: The lock-hold budget describes the real call graph, states what it does not bound, and cannot silently go stale

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`, `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`, `packs/core/tests/skills/work-loop/test_loop_concurrency.py`

**Tests:** (extend `test_lock_hold_budget` — TDD)

- The unbounded-`subprocess` AST scan covers `loop-engine.py` and
  `_loop_guards.py` file-wide, and its matched call set is T5's canonical spawn set
  — not the current narrower `("run", "Popen", "check_output")`, which lets a
  `check_call` or `os.system` under the lock pass today. `lint-spec-status.py` is
  covered by a reachability assertion instead, not a file-scoped timeout scan.
  Verifies AC21.
- `_loop_guards.py` contains no spawn reference at all. Verifies AC21.
- An AST assertion proves the guard call path does not reach
  `lint-spec-status.py`'s `git`-calling functions — the honest form of the claim,
  since that module does import `subprocess`. Verifies AC21.
- `SUBPROCESS_TIMEOUT_S × MAX_SUBPROCESS_CALLS_UNDER_LOCK` sits strictly between
  `_statelock.DEFAULT_TIMEOUT` and `DEFAULT_STALE_AFTER`, read from the modules.
  Verifies AC22.
- The constant equals the number of external subprocess **invocation edges**
  reachable from `cmd_transition`, counted by an AST call-graph walk. Leaving it at
  6 fails; writing 1 (the *site* count) also fails. Verifies AC22.
- Every reachable under-lock subprocess argv starts with `git`. Verifies AC21.

**Approach:**

- Set **`MAX_SUBPROCESS_CALLS_UNDER_LOCK = 2`** — the two invocation edges reaching
  the single `subprocess.run` site in `_get_repo_root`, from `cmd_transition`'s
  `_resolve_spec_dir` and from its own `_get_repo_root()`. Max hold 20 × 2 = 40 s,
  inside 10 < 40 < 300. **This is the one place the value is written.**
- Define the walk's locked region as **`cmd_transition`'s whole body**, explicitly
  excluding `_locked.decorate.wrapper`'s pre-lock `_resolve_spec_dir`. The
  `with sl.exclusive(...)` block itself contains only `return fn(args)`, an
  indirect call AST cannot resolve, so the syntactic region is not the useful one.
- Rewrite the budget comment to state, honestly: the two edges and that they are
  git only; that in-process guard calls are deliberately not counted as
  subprocesses; that **the subprocess half is time-bounded at `TIMEOUT_S × edges`
  while the in-process half is byte-bounded and not time-bounded**; the ~1.0 s
  worst-case `canonical_contract` cost at the 8 MiB cap; that `O_NONBLOCK` closes
  the reachable local FIFO/device case; and that a stalled network mount — plus
  `_recover_pending`'s repo-global reads — remain an unbounded residual whose only
  recovery is the stale-lock reclaim, which is itself the hazard the lock prevents.
- Fix the stale filename `test-loop-concurrency.py` at `loop-engine.py:67` — an
  in-scope ride-along in the comment T4 is rewriting.
- **Do not** add `timeout=` to `lint-spec-status.py`'s four `git` calls. Considered
  and dropped: they are unreachable from the guard path, so it is not a mechanical
  ride-along but an unspecced change to a shipped CLI's failure mode on a slow
  repository, which `CONVENTIONS.md` says needs its own criterion. Recorded in
  `Deferred` instead. Consequently the scan is **not** file-scoped over
  `lint-spec-status.py`; the artifact for that file is the AST reachability
  assertion proving the guard path never reaches those functions.

**Done when:** `pytest packs/core/tests/skills/work-loop/test_loop_concurrency.py`
is green, and each of raising the constant to 6, lowering it to 1, and dropping a
`timeout=` from any scanned file makes it red.

### T5: A future reintroduction of a child-Python guard fails a test

**Depends on:** T3

**Touches:** `packs/core/tests/skills/work-loop/test_loop_engine_no_child_python.py`

**Tests:** (this task *is* the test — TDD)

- Table-driven over **every `(mode, source_state, event)` entry** — every key of
  every *inner* dict of `_TRANSITIONS_BY_MODE`, enumerated from the module rather
  than restated. Note `_TRANSITIONS_BY_MODE`'s own keys are just the two mode names,
  so iterating those would satisfy a looser wording with a two-case test. The test
  asserts the number of entries actually driven equals
  `sum(len(v) for v in _TRANSITIONS_BY_MODE.values())` — exact, not merely "more
  than two". For each entry a fixture satisfying that transition's guards is built
  and the transition driven. Verifies AC1, AC23.
- **The canonical spawn-primitive set** the recorder patches, and which T4's scan
  reuses: `subprocess.run`, `subprocess.Popen`, `subprocess.check_output`,
  `subprocess.check_call`, `os.system`, `os.popen`, `os.posix_spawn`,
  `os.posix_spawnp`, `os.execv`/`execve`/`execvp`/`execvpe`, `os.spawnv`/`spawnve`,
  `os.fork`, and `multiprocessing.Process`. Each is patched on **the module object
  that owns it**, not on an engine-local alias, so a spawn originating in
  `_loop_guards.py` is also seen. Verifies AC23.
- Fails immediately if an argv's program is `sys.executable`, has a basename
  matching `python*`, `py`, or `pyw`, or if any argv element ends in `.py`.
  Permits `git`/`git.exe` and asserts each carries a `timeout` keyword. **The git
  assertion keys on `argv[0]` plus the `timeout` kwarg and must not co-locate the
  string literals `"rev-parse"` and `"--show-toplevel"` in one
  `List`/`Tuple`/`Call` node** — `tools/lint-pack-test-boundary.py` fails any pack
  test that does, so the obvious spelling
  (`assert argv == ["git", "rev-parse", "--show-toplevel"]`) would break the very
  gate AC25 says passes. Verifies AC1, AC21, AC23, AC25.
- **Non-vacuity, three ways:** the recorder must have fired; the exit code must
  equal the expected value; and the resulting `engine-state.json` `state` must
  equal the expected target (or be byte-unchanged for refusal cases). A fixture
  that refuses at spec-dir confinement having fired one `git` call therefore fails
  rather than passing. Verifies AC23.
- The loader ran **once** across a multi-guard transition, asserted by counting
  loads. Verifies AC20.
- The six path shapes are covered by construction as members of the table:
  identity-only (`spec-ready`), identity+schedule (`blocker-applied` from
  `CODE-HUMAN-GATE`), identity+event-guard (`spec-approved`),
  identity+schedule+event-guard (`wave-complete`), composed plan/status
  (`plan-locked`, code mode), and a failing guard (`gates-clean` when the current
  wave is not the last). Verifies AC23.
- A source-absence AST assertion over both `loop-engine.py` and `_loop_guards.py`
  runs alongside as an independent second signal. Verifies AC1, AC23.

**Approach:**

- Reuse `test_loop_engine.py:40-48`'s fixture shape — `git init` into `tmp_path`
  plus `monkeypatch.chdir` — so `_get_repo_root()` resolves inside the throwaway
  repo and confinement passes. Driving `main(argv)` in-process removes the `cwd=`
  the subprocess harness supplied, which is exactly the vacuity trap.
- Build fixtures via a `_spec_fixture` helper computing baseline hashes through
  `_loop_guards.sha256_canonical_contract`, so fixtures satisfy the real guards.
- Drive via `main(argv)` in-process; convert `SystemExit` to a return code at the
  harness boundary only. The real `@_locked` path still runs.

**Done when:** green over the whole transition table, and red when
`_run_id_preflight` is temporarily reverted to its subprocess form.

### T6: The callable API and the CLI cannot drift apart on any guard verdict or message

**Depends on:** T0, T1b, T2

**Touches:** `packs/core/tests/skills/work-loop/test_loop_guards_parity.py`

**Tests:** (this task *is* the test — TDD)

- A fixture table of `(scenario, on-disk state, API call, CLI argv, expected ok)`
  covering: run-ID identity (match, mismatch, absent state); schedule currency
  (current, drifted, missing plan, absent state); plan currency (approved,
  pending, spec drift, plan drift) with `require_schedule` both false and true
  (schedule missing, wave index out of range); phase caps (`implement` with
  readable and with absent state, `gates-failed` under and at cap, `review` under
  and at cap); wave checks (`more` and `last`, satisfied and not, wave-index
  mismatch, absent state); artifact status (`spec.md` Approved/Shipped/Draft,
  `plan.md` Approved, no-status-line). Verifies AC24.
- For every row, `GuardResult.ok == (cli_returncode == 0)`. Verifies AC24.
- For every row, the CLI's normalized returncode, stdout, and stderr equal **T0's
  goldens** — not the API's own output. This is what makes the test able to catch a
  reworded message. Verifies AC15.
- Every failing row's stderr is a single line with no `Traceback`. Verifies AC15.

**Approach:**

- One fixture builder shared by both halves of each row, so the API and the CLI see
  byte-identical on-disk state; run the CLI as a subprocess so the real `argparse`
  and exit-code path is exercised; normalize through `golden_support.py`.
- Scope the table to decisions, not lifecycle walks — the existing suites cover the
  walks.

**Done when:** `pytest
packs/core/tests/skills/work-loop/test_loop_guards_parity.py` is green.

### T7: Canonical source, projections, metadata, docs, and backlog all agree

**Depends on:** T0, T1a, T1b, T2, T3, T4, T5, T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude/skills/work-loop/scripts/*`, `.agents/skills/work-loop/scripts/*`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `workspace.toml`

**Tests:** (goal-based)

- `Done when:` `make build-self` leaves the tree clean and `_loop_guards.py` plus
  the edited scripts are byte-identical across `packs/core/.apm/`, `.claude/`, and
  `.agents/`. Verifies AC26.
- `Done when:` `make build-check` and `make lint-ruff` exit 0 — including
  `catalogue verify`'s CAT-V-005 version-equality check. Verifies AC26, AC27.
- `Done when:` `python3 tools/lint-pack-test-boundary.py` exits 0. Verifies AC25.
- `Done when:` `python3 -c` probes load `_loop_guards.py` by direct path and via the
  projected `.claude/` copy, from a working directory outside the repo, with no
  `PYTHONPATH`, writing no new `__pycache__` entry. Verifies AC13, AC20.
- `Done when:` both deferred slugs resolve in `workspace.toml [backlog].open`.
  Verifies AC27.
- `Done when:` `lint-spec-status.py` passes for this spec directory.

**Approach:**

- **Bump the Core pack to `2.7.1`** — the single authoritative statement of the
  target version — in **both** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json`, because CAT-V-005 hard-errors on a
  mismatch. `core` is absent from `.claude-plugin/marketplace.json`, so those two
  are the complete set.
- Run `make build-self`; do not hand-edit the projections.
- In `references/state-schema.md`, **leave** the "Two tools own this in Phase 1"
  list at two entries: it enumerates state *writers*, and the paragraph after it
  reads "State mutation is owned exclusively by these tools" — `_loop_guards.py`
  writes nothing (AC18), so adding it there would contradict that. Add a separate
  sentence naming `_loop_guards.py` as the shared **read-only** guard reader, and
  record the boundary diagram. No broader rewrite — user-facing commands unchanged.
- Verify `docs/specs/README.md`'s row still matches the spec (27 ACs / 9 tasks, and
  a re-derived budget rather than a replaced one). It was corrected when the counts
  last changed; this is the drift check, not a pending edit.
- Register both `Deferred` slugs in `workspace.toml [backlog].open` with
  cold-start-sufficient comments.
- Add the implementation note to this spec directory.

**Done when:** `make ci` passes and `git status --porcelain` is empty.

## Rollout

Pure-logic internal refactor of a repository-local skill script. No flag, no
canary, no infrastructure, no external system, no data migration. Reversible by
reverting the commit; the only durable artifacts touched are the projected copies,
regenerated deterministically from source.

**Deployment sequencing** — three ordering constraints, all inside the PR:

1. **T0 must precede T1a.** A golden captured after the move is the tautology it
   exists to prevent.
2. **T1a and T1b may need one commit** — the helpers move out of `loop-cohort.py`
   in T1a and a tree with them half-moved does not import. Separate tasks for
   separate gates, not necessarily separate commits.
3. **T7 must be last**, or it captures an intermediate state into the projections.

## Risks

- **The canonical digest moves and in-flight runs break.** Blast radius is not the
  committed repository — `state.json` is gitignored (`.gitignore:14`) — but every
  in-flight local run, **including this PR's own
  `docs/specs/work-loop-in-process-guards/state.json`**, would start failing
  `plan check-current`. Mitigation: byte-for-byte move, `_STATUS_PLACEHOLDER`
  preserved, T0's pre-move golden plus the mutation check.
- **A relocated helper breaks a mutation verb.** Mitigation: eager re-binding of
  every name in T1a's list, the two `stop()`-returning wrappers so no call site
  changes, and the cohort suites plus the roster source-anchor as the check.
- **The bounded reader's `ValueError` reaches an unguarded mutation verb.**
  Mitigation: AC12 widens the three verbs with a test each; `_schedule_run_impl`'s
  case asserts no state is written while holding the cohort lock.
- **A load failure becomes an import traceback instead of a refusal.** The
  re-binding must be eager, so the module-level call cannot be allowed to raise.
  Mitigation: sentinel binding plus a per-verb check, and a load-failure case that
  triggers at import time specifically.
- **The budget test still cannot see all under-lock code.** Mitigation: T4 scans
  three files and asserts the guard path does not reach `lint-spec-status.py`'s
  `git` functions; the honest residual is written into the comment rather than
  claimed away.
- **The no-child-Python test passes vacuously.** Mitigation: T5 asserts exit code
  and resulting engine state per path, not merely that the recorder fired.
- **The version bump breaks the build.** Mitigation: T7 bumps both files.
- **Scope creep into `loop-cohort.py`'s decomposition.** Mitigation: the spec's
  `Never do` list; only the read-only guard surface moves.

## Deferred

- **`_statelock.py`'s two importlib loaders** do not set
  `sys.dont_write_bytecode`, so they still write and read `__pycache__`. Same
  class as AC13's residual, in code this change otherwise never touches. Register
  as `{slug = "statelock-loader-bytecode-cache", source = "spec/work-loop-in-process-guards AC13"}`.
- **`loop-cohort.py`'s `run_git` has no `timeout=`.** Not reachable under the
  engine lock, so outside this change's budget, but the nearest copy-paste hazard
  to the extraction site. Register as
  `{slug = "loop-cohort-run-git-unbounded", source = "spec/work-loop-in-process-guards AC21"}`.
- **`lint-spec-status.py`'s four `git` calls have no `timeout=`** (`:307`, `:316`,
  `:325`, `:427`). Unreachable from the guard path, so bounding them is not a
  mechanical ride-along but an observable change to a shipped CLI's failure mode on
  a slow repository — which needs its own criterion rather than riding along here.
  Register as
  `{slug = "lint-spec-status-git-unbounded", source = "spec/work-loop-in-process-guards AC21"}`.

## Changelog

Newest first.

- 2026-08-17: revised after round 4 (8 blockers across both reviewers, all verified;
  one reviewer **falsified a change the other had prompted**). Substantive changes:
  **(a)** `cmd_approve_plan` is a **fifth** `ValueError` site and a lock holder —
  one hash call sits inside an `except` a `ValueError` escapes and the other is
  entirely unguarded *and writes its result*. AC12 is restated as three tested sites
  plus two labelled unreachable-by-construction, because reducing
  `cmd_plan_check_current` and `_schedule_check_current_impl` to adapters makes their
  handlers unreachable and their tests vacuous.
  **(b)** the completeness check moves from an enumerated symbol list to
  `__all__` + a `_MODULE_COMPLETE` last-statement sentinel: the enumeration was
  order-blind and its obvious spelling omitted the four names whose absence breaks
  the mutation path.
  **(c)** the stream swap moves to the loader that actually execs the reconfiguring
  module (`_lint_spec_status()`, lazily inside a guard call — the earlier "the
  loaders nest" claim was false), and swaps to `io.TextIOWrapper(io.BytesIO())`
  rather than `sys.__stdout__`, which is `None` under pythonw/embedded stdio.
  **(d)** the load-failure fallbacks now **raise** instead of returning: a returning
  stub made a missed sentinel silent, and would have let a reason string be written
  into `approved_spec_hash`; the sentinel check also moves to `main()`'s single
  dispatch chokepoint rather than ~20 verb entries.
  **(e)** AC9's "lost scanner coverage" claim is **withdrawn as wrong** — the
  semgrep rule's `paths.include` never listed `check-spec-status.py`. Restated as
  ineligibility for the rule's expansion ratchet.
  **(f)** the `lint-spec-status.py` timeout ride-along is dropped as an unspecced
  CLI behavior change and deferred; three further dangling citations of the moved
  confinement exemplar are enumerated in T2; `test-loop-cohort.sh` joins the
  regression bar; and AC17's source-order assertion gains a vacuity guard plus a
  mutation check, per the antipattern `e6d4c14a` records.
- 2026-08-17: revised after round 3 (4 blockers, all verified; the human elected to
  proceed to the approval gates rather than run a fourth review round). One
  simplification and three corrections, all of them fixes to *this document's*
  errors rather than to the change's design:
  **(a)** `_loop_guards.py` now **omits `from __future__ import annotations`** and
  is **not** registered in `sys.modules`, matching `_statelock.py` exactly. This
  retires the half-loaded-module hazard (`exec_module` does not clean a registered
  entry when the body raises), the session-global-singleton test leakage, and the
  missing-`__future__` allowlist gap — by deleting a line rather than adding
  machinery. `ruff` does not select `FA` and PEP 604 unions work above the 3.11
  floor, so nothing is lost.
  **(b)** AC17's step order was **wrong** and omitted the `schema_version` check;
  it is now read from source (spec-dir resolve → wave-index → crash recovery →
  state read → schema check → run-ID preflight → …) and carries a source-order
  assertion, since it is the rail the anti-reordering prohibition is measured
  against.
  **(c)** AC15 and AC16 contradicted each other — AC16's rows were captured as
  pre-change goldens and then required to refuse. The fixture now carries `before`
  and `after`, with `after` asserted only on AC15's two named exceptions.
  **(d)** the stream save/restore control was **theatre**: `reconfigure` mutates in
  place, so restoring references restores nothing and an identity assertion cannot
  fail. Replaced by a real swap plus value-based verification, and the actual hazard
  — a caller whose stream lacks `reconfigure` — is now a test case. *(The swap target
  and its owning loader were both corrected again in round 4: it swaps to a
  throwaway `io.TextIOWrapper`, not `sys.__stdout__`, and it lives on
  `_lint_spec_status()`, not `load_guards()`.)*
- 2026-08-17: revised after round 2 (14 blockers, all verified). **Two items in
  this entry were later superseded — see the round-3 and round-4 entries above:
  `sys.modules` registration was withdrawn, and the stream save/restore form was
  replaced.** Four substantive changes at the time:
  **(a)** the hand-rolled cache-free loader is **withdrawn** — it produced four
  defects of its own (a frozen dataclass fails at class creation when its module
  is absent from `sys.modules`, probe-confirmed under `exec_module` too; a
  mis-set `__name__` runs `lint-spec-status.py`'s `__main__` and yields
  `SystemExit(0)` from a lock holder; three drifting copies; a required `bandit`
  `exec` suppression) for a residual unchanged from today. `exec_module` stays,
  with `sys.dont_write_bytecode`, `sys.modules` registration, and stream
  save/restore.
  **(b)** `O_NONBLOCK` added — without it the bounded reader's own `os.open`
  blocks on a raced FIFO and the post-open type check never runs, so the round-1
  mitigation did not close the hang it was written for.
  **(c)** honest restatement of two overclaims: the budget bounds the subprocess
  half in time and the in-process half only in bytes; and the no-spawn invariant
  holds for the guard *call path*, not transitively, because
  `lint-spec-status.py` imports `subprocess` and has four unbounded `git` calls.
  **(d)** T0's corpus is copied into the pack's fixtures directory —
  `tools/lint-pack-test-boundary.py` makes reading `docs/specs/` from a pack test
  a hard gate failure, the live corpus would go stale on unrelated edits, and the
  lowercase-heading edge case does not exist there to capture.
- 2026-08-17: revised after pre-EXECUTE review round 1 (12 blockers across two
  reviewers, all verified against source). Added T0's golden fixtures because two
  tests compared moved code against itself; promoted bounded reads and exception
  containment to first-class requirements; specified a cache-free loader; split T1
  into T1a/T1b; corrected the shell-out inventory, the budget quantity, and the
  version-bump file count.
- 2026-08-17: initial plan. Extract-then-rewire in seven tasks.
