# Spec: work-loop in-process guards

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061, ADR-0074
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

One `python loop-engine.py transition <spec-dir> <event>` invocation is one
Python interpreter process. Every read-only work-loop guard the FSM requires —
engine/cohort run-ID pairing, scheduled-plan currency, approved spec and plan
baselines, implementation and review retry caps, current-wave and
more-waves/last-wave checks, and `Approved`/`Shipped` artifact status — runs
inside that same process by calling a shared, callable guard API. No transition
starts a second Python interpreter.

The user is an agent (or a human) driving the work-loop: a transition costs one
interpreter startup instead of up to four, and a guard refusal reads the same as
it always did. The standalone `loop-cohort.py` and `check-spec-status.py` CLIs
keep working for direct callers, and the engine, those CLIs, and the tests all
reach the same single implementation of each guard decision — so a CLI and the
engine cannot drift into disagreeing about whether a transition is legal.

Removing the child processes removes a containment boundary as well as a cost.
A child interpreter bounded every guard's file reading with a subprocess timeout
and converted every unexpected exception into an exit code. In-process, the guard
layer carries those properties itself: every file it reads is size-capped, type-
checked, and opened non-blockingly so an unsafe path refuses instead of hanging,
and the guard-call boundary turns any unexpected exception into a one-line
refusal rather than a traceback out of a process that holds the state lock. A
guard that cannot decide refuses; it never skips.

Guards that are intrinsically external stay external: `git rev-parse` still
resolves the repository root, bounded by an explicit timeout, and the engine
still holds the state lock across the whole read-decide-write critical section.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Route every guard decision through exactly one implementation, called by the
  engine, by the corresponding CLI adapter, and by unit tests alike.
- Keep the callable guard layer free of CLI concerns: explicit typed arguments
  in, a structured result out; no `argparse`, no `sys.argv`, no `sys.exit`, no
  printing to stdout or stderr, no state mutation.
- Bound every file the guard layer reads — state JSON, Markdown artifact, and the
  bundled `assets/state.json` template alike — by size, reject anything that is
  not a regular file, and open non-blockingly so a FIFO or device refuses
  immediately rather than blocking.
- Contain every unexpected `Exception` at the guard-call boundary and turn it
  into a refusal. A guard that cannot complete its check must never report
  success and must never silently skip.
- Read the current `state.json`, `spec.md`, and `plan.md` afresh on each logical
  guard call, exactly as the separately-invoked child processes did.
- Bound every remaining external subprocess reachable while `cmd_transition`
  holds the engine-state lock with an explicit `timeout=`.
- Keep the shared module Python 3.11+ stdlib-only, importable without
  installation, packaging, `PYTHONPATH` setup, or a specific working directory.
- Regenerate the `.claude/` and `.agents/` projections from the Core pack source
  with the repository's own build tooling.

### Ask first

- Any change to the FSM transition table, the state schema, the set of
  work-loop events, or the order of steps inside `cmd_transition`.
- Any change to a `loop-cohort.py` mutation verb's **body or accepted
  arguments** (`init`, `approve-plan`, `schedule`, `record-attempt`,
  `wave advance`, `review record`, `reset`). Refactoring a helper those verbs
  *share*, without changing any of their call sites, is outside this rail —
  signed off 2026-08-17 for `_validate_run_id` and `_assert_status_legal`.
  Widening three mutation verbs' `except` clauses so an unsafe artifact refuses
  instead of raising is a change to their **failure behavior**, signed off
  separately on 2026-08-17.
- Any widening of the accepted-argument surface, defaults, or exit-code contract
  of a `loop-cohort.py` or `check-spec-status.py` verb.
- Replacing `importlib`'s `exec_module` with a hand-rolled loader anywhere in the
  work-loop scripts. Considered and **declined** 2026-08-17; see AC7's residual.
- Converting `_statelock.py`'s two importlib loaders, or adding `timeout=` to
  `loop-cohort.py`'s `run_git`. Deferred; see `Deferred` in `plan.md`.

### Never do

- **Never introduce a new module boundary outside the work-loop skill's own
  `scripts/` directory, a new top-level directory, or a new runtime dependency**
  — the shared guard module is a sibling of the scripts that use it, stdlib-only,
  and requires no MCP server, daemon, package install, or `uv`.
- Never satisfy the in-process requirement by calling a CLI `main()`, building a
  synthetic `argparse.Namespace` for the engine, redirecting stdout/stderr, or
  catching `SystemExit`.
- Never add a second Markdown status parser or status regular expression;
  `lint-spec-status.py` stays the only one on the work-loop guard path.
- Never mutate `state.json`, `engine-state.json`, `events.pending`,
  `events.jsonl`, `spec.md`, or `plan.md` from the shared guard API, and never
  create a file anywhere under the spec directory or `.loop-run/` from it.
- Never acquire the cohort mutation lock from a read-only guard, and never
  shorten, split, or reorder `cmd_transition`'s critical section.
- Never introduce a cross-guard cached cohort snapshot.
- Never weaken or delete the lock-hold budget test to accommodate the new call
  graph.
- Never gate acceptance on a wall-clock timing threshold; no test asserts that a
  transition, or any guard, completes within a fixed elapsed time.
- Never let the guard layer's own module reach a process-spawning or network
  capability — no `subprocess`, `os.system`, `os.popen`, `os.exec*`, `os.spawn*`,
  `os.fork`, `multiprocessing`, `socket`, `urllib`, or `http`. (The module it
  loads, `lint-spec-status.py`, does import `subprocess`; AC16 states that
  boundary honestly rather than claiming a transitive invariant that is false.)
- Never rename `_STATUS_PLACEHOLDER`'s literal value; it feeds the canonical
  digest and a rename silently re-pins every baseline.
- Never interpolate raw artifact content into a refusal reason.

## Testing Strategy

| Behavior | Mode | Why |
| --- | --- | --- |
| No child Python process is launched for any guard, on any FSM path | **TDD** — process-boundary instrumentation | A compressible invariant over the one process-launch seam. The engine module is loaded in-process, every spawn primitive is replaced on the module object that owns it (so a spawn from the guard module is also seen), and the recorder fails on any Python-shaped argv. Driven table-wise over every key in `_TRANSITIONS_BY_MODE`, not a sampled subset. This is the normative performance regression test. |
| Each guard decision has one implementation shared by engine, CLI, and tests | **TDD** — parity tests, integration surface | A fixture table asserts the callable API and the standalone CLI reach the same verdict for the same on-disk state. Drift between two surfaces is what a parity table catches and a unit test on either side alone does not. |
| CLI messages are unchanged | **TDD** — golden-literal comparison | A test comparing new code against new code proves nothing (the antipattern in `docs/knowledge/topics/a-test-that-moves-with-the-code-cannot-catch-the-code-being-wrong.json`). Literals are captured from the **pre-change** CLIs, normalized through one canonical function (absolute paths and 64-hex digests are variable), checked in, and asserted against. |
| The canonical digest did not move | **TDD** — golden fixture over a frozen corpus, plus a mutation check | Same reason. The corpus is **copied into the pack's own fixtures directory** — both because a fixture over live `docs/specs/` goes stale on unrelated edits and because `tools/lint-pack-test-boundary.py` forbids a pack test from reading above its own pack. |
| The callable layer prints nothing, parses nothing, exits nothing, mutates nothing, spawns nothing | **TDD** — unit plus AST | Capture stdout/stderr around every call and assert both empty; assert the recursive listing of the spec directory and the loop-run directory is identical before and after; AST-scan the module against an import **allowlist** so an added capability fails the gate rather than needing a reviewer to notice. |
| Every guard semantic the FSM requires still holds | **TDD** — existing suites, integration surface | `test_loop_engine.py`, `test_loop_cohort.py`, `test_loop_cohort_schedule.py`, and `test_loop_engine_events_jsonl.py` already encode these decisions end-to-end through the real CLIs. They are the regression bar. |
| Locking, transition ordering, safe-file handling, no-write-on-refusal | **TDD** — existing suite, cross-process surface | `test_loop_concurrency.py` drives separate OS processes against a real lock; only a multi-process harness proves the critical section. |
| The bounded set of under-lock work is what the budget claims | **TDD** — unit over source | The budget test's AST scan covers `loop-engine.py`, `_loop_guards.py`, and `lint-spec-status.py`, and derives the inequality from the modules rather than restating it. The counted quantity is **invocation edges on the reachable call graph**, not call sites. |
| Load failures fail closed | **TDD** — unit, one case per failure mode | Six enumerable modes each get a fixture; each must produce a one-line, remedy-naming refusal — never a traceback, never a skipped check. |
| Unsafe artifacts refuse rather than hang | **TDD** — unit, deterministic | With `O_NONBLOCK` the FIFO case returns an error immediately, so the assertion is on the **refusal reason**, not on elapsed time. No wall-clock ceiling is used anywhere. |
| The module imports cleanly under every supported route | **Goal-based check** | `Done when:` it loads by direct file path, through the tests' importlib harness, and from the projected copies, with no `sys.path` mutation and no cwd dependence — and writes no new `__pycache__` entry. |
| Canonical source and projected copies agree | **Goal-based check** | `Done when:` `make build-self` is a no-op and `make build-check` passes; a byte comparison across the three copies is the check. |
| The real engine CLI still drives a full transition | **Visual / manual QA** | The engine is a CLI a user invokes directly, so the built artifact is exercised end-to-end through a real spec directory and the observed stdout, stderr, and exit code recorded. |

## Acceptance Criteria

Numbered in group order. Each criterion names the task that carries its
verifying artifact; where a fact is stated canonically elsewhere, the criterion
references that place rather than repeating the value.

### Process topology

- [ ] AC1 — A transition launches zero child Python processes for run-ID,
      schedule, cohort, wave, phase, plan, or artifact-status guards. Verified
      table-wise over **every `(mode, source_state, event)` entry** — that is,
      every key of every inner dict of `_TRANSITIONS_BY_MODE`, not its two
      top-level mode keys — with the entry list read from the module rather than
      restated here. *(T5)*
- [ ] AC2 — The engine still evaluates every guard the FSM requires: the run-ID
      preflight on all transitions, the schedule pre-check on CODE states except
      the `done` exemption, and every dispatched guard **including the two
      delegates reached indirectly**. Every `sys.executable` site in
      `loop-engine.py` is accounted for by the disposition table in `plan.md`'s
      T3 — the single canonical inventory — with each live site rewired and each
      unreferenced one deleted as dead code orphaned by `_run`'s removal. *(T3)*

### One implementation

- [ ] AC3 — A shared callable guard module exists at
      `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`, is Python
      3.11+ stdlib-only, and is the single implementation of each guard decision
      and of the bounded safe-file readers. `loop-engine.py`, `loop-cohort.py`,
      `check-spec-status.py`, and the tests all call into it; the engine's own
      duplicate `_read_managed_json` is deleted and `_read_engine_state` routes
      through the shared reader, so no guard algorithm and no safe-reader
      implementation exists in a second file. *(T1a, T3)*
- [ ] AC4 — Every status read on the work-loop guard path resolves through
      `lint-spec-status.py`, and an AST assertion confirms `_loop_guards.py`
      compiles no `Status`-matching pattern of its own. (Scoped to the guard
      path: other status matchers exist elsewhere in the repository — see
      Assumptions — and are out of scope.) *(T1b)*
- [ ] AC5 — The canonical contract digest is unchanged by the relocation. A
      checked-in fixture of digests, generated from the **pre-move**
      `loop-cohort.py` over a frozen corpus committed inside the pack's own
      fixtures directory, is reproduced exactly by the moved implementation, and
      perturbing a single line of the relocated `canonical_contract` makes that
      test fail. *(T0, T1a)*

### The callable contract

- [ ] AC6 — Every public function in `_loop_guards.py` takes explicit typed
      arguments (`Path`, expected run ID, phase, wave expectation, wave index,
      filename, expected status) and returns a structured result whose `ok` and
      `reason` fields cannot disagree — `GuardResult.__post_init__` **raises
      `ValueError`** (not `assert`, which `-O` / `PYTHONOPTIMIZE` strips, and this
      is the control that stops an adapter written `if result.reason:` reading a
      containment bug as success) unless `ok == (reason is None)`. Every adapter
      branches on `ok`, never on `reason`; that source assertion is scoped to the
      six `GuardResult`-returning guards. **Two named public functions are carved
      out** of the structured-result rule: `validate_run_id` and
      `assert_status_legal` return `str | None` by design (AC11), because their
      six mutation-verb callers consume a reason directly and rewriting those call
      sites is out of scope.
      Calling any guard produces zero bytes on stdout and zero on stderr. An AST
      scan enforces an **import allowlist**, stated canonically in `plan.md`'s T1b,
      and confirms the module contains no `argparse`, no `sys.exit`, no `sys.argv`,
      no `.reconfigure(` call, no *unrestored* stream mutation (the one sanctioned
      exception is `_lint_spec_status()`'s swap-and-restore under AC13), no
      top-level file write or command execution, and no reference to any spawning
      or network capability named in the `Never do` rail. The purity rows are not
      vacuous: each asserts the guard's expected `ok`/`reason` verdict **alongside**
      the empty-stream assertion, and captures through a `TextIOWrapper` rather
      than an `io.StringIO` — a `StringIO` has no `reconfigure`, so capturing
      through one turns the lazy parser load into an `internal-error:` refusal that
      emits nothing and would satisfy an empty-stream-only assertion while hiding a
      wrong verdict. *(T1b)*
- [ ] AC7 — `spec_dir` is documented as a caller-confined absolute resolved
      `Path`; the module names which helper each of its three callers uses to
      satisfy that precondition, and validates at the boundary what a callee can
      actually validate — that `spec_dir` exists and is a directory
      (`lstat` + `S_ISDIR`). The former "absolute, no `..`" re-check is dropped
      as unfalsifiable: all three callers `resolve()` first, after which the
      property holds by construction. *(T1b)*
- [ ] AC8 — An expected validation failure returns an ordinary failure result
      carrying a one-line reason, never a raised exception: run-ID mismatch;
      unsupported schema; baseline drift; cap reached; wrong wave; wrong status;
      and a state or artifact file that is missing, malformed, oversized,
      non-regular (a FIFO, device, or directory), symlinked, replaced mid-read,
      resolves outside `spec_dir`, or whose resolution raises `OSError` or
      `RuntimeError`. Every file the guard layer reads — state JSON, Markdown
      artifact, and the bundled `assets/state.json` template — goes through a
      bounded reader that `lstat`s, requires `S_ISREG`, opens with
      `O_RDONLY | O_NOFOLLOW | O_NONBLOCK`, re-checks type and dev/ino on the
      returned descriptor, and enforces the byte cap stated canonically in
      `plan.md`'s T1a. `O_NONBLOCK` is what makes an unsafe path refuse rather
      than block: the type pre-check is path-based and racy, so without it a FIFO
      swapped in after the `lstat` blocks the open indefinitely. Numeric state
      fields a guard compares are validated as non-negative integers, and
      non-finite JSON numbers (`NaN`, `Infinity`) are rejected rather than
      coerced. Integrity-class reasons carry a stable greppable marker distinct
      from routine policy refusals. **Platform scope:** `O_NOFOLLOW` is absent on
      Windows, where the existing `getattr(os, "O_NOFOLLOW", 0)` degrades to `0`;
      the symlink guarantee is therefore POSIX-only and the racy path pre-check
      is all that remains there. This inherits an existing gap rather than adding
      one, and is stated rather than left silent. *(T1a, T1b)*
- [ ] AC9 — `check_artifact_status`'s `filename` must be a single path component
      matching `^[A-Za-z0-9._-]+$`, **and is additionally rejected when it consists
      only of dots** (`.`, `..`, `...`). The charset alone admits every dot segment,
      which is the exact class `0cb5c213` ("reject dot path segments in
      capture-evidence `--repo`") fixed a day earlier; the repo's blessed form for
      it is segment equality rather than a narrower charset, because a leading dot
      is legitimate in real filenames. The single-component rule is what makes the
      confinement honest: `O_NOFOLLOW` rejects a symlink only at the **final**
      component, so `sub/spec.md` with `sub` swapped after the confinement check
      would otherwise escape. The dot cases are also caught downstream — `..` by
      the resolves-outside-`spec_dir` check and `.` by `S_ISREG` — so the explicit
      rejection is defence in depth, not the only guard. The descriptor re-check
      proves type and inode identity, **not** confinement, and this criterion
      claims only that.
      **Scanner-coverage note.** No semgrep coverage is lost: the rule's
      `paths.include` lists `lint-traceability.py`, `lint-spec-status.py`,
      `loop-cohort.py`, and its fixtures — **not** `check-spec-status.py`, which
      appears only in a comment explaining why the rule's `pattern-not-inside`
      clause exists. The real consequence runs the other way: after the move
      `check-spec-status.py` retains a bare `Path(args.spec_dir).resolve()` with no
      in-function containment, which makes it permanently ineligible for the rule's
      own expansion ratchet. T1b's confinement cases are the compensating control
      for the pattern's new home, and the CodeQL `py/path-injection` before/after
      comparison is an acceptance artifact, not plan prose. *(T1b, T2)*
- [ ] AC10 — The guard-call boundary contains every unexpected `Exception` and
      turns it into a refusal: for each guard, an injected arbitrary exception
      produces a one-line refusal and a non-zero exit from the engine and from
      the CLI, never a traceback and never a reported success. Containment
      catches `Exception` **only**, so `BaseException` — `KeyboardInterrupt`,
      `SystemExit` — propagates untouched. Lock-integrity exceptions are handled
      **structurally, not by naming the class**: the containment boundary sits
      wholly inside the read-only guard layer, which never acquires a lock, so a
      `_statelock`-derived exception cannot originate inside a contained call —
      `StateLockLost` is raised by `with sl.exclusive(...)` in
      `loop-cohort.with_state_lock`, outside every guard frame, and
      `with_state_lock`'s own `except sl.StateLockError` remains its only handler.
      (Requiring `@_contained` to re-raise the class by name would force the
      read-only layer to import the lock module, which AC6's allowlist forbids.)
      A contained failure resolves to a **non-empty**
      reason, never `None`, carrying an `internal-error:` marker so an operator
      can tell a crash-refusal from a policy refusal. Every reason is
      whitespace-collapsed and length-capped, and never interpolates raw artifact
      content — only a field name and its type. *(T1b)*
- [ ] AC11 — The two reason-returning helpers on the mutation path
      (`validate_run_id`, `assert_status_legal`), whose `None` means "legal,
      proceed", are covered by containment in a form that cannot turn a failure
      into `None`. A contained failure returns a non-empty reason string, so no
      mutation verb proceeds past a check that did not complete. *(T1a)*
- [ ] AC12 — Routing `spec.md` / `plan.md` reads through the bounded reader
      introduces a `ValueError` class the mutation path did not previously handle.
      **Three sites are tested; two more keep the handler as
      unreachable-by-construction defence in depth.** Tested:
      **(i)** `_read_md_status` widens its `except (OSError, UnicodeDecodeError)` to
      include `ValueError` and raises `UnreadableArtifact`, which
      `_assert_status_legal`'s existing handler already catches — the path that
      protects the six mutation verbs calling it.
      **(ii)** `_schedule_run_impl`, under the **cohort state lock**, with two
      exposures: its raw `plan_path.read_text()` and its
      `sha256_canonical_contract` call.
      **(iii)** `cmd_approve_plan`, also `@_locked`, whose already-approved branch
      hashes inside an `except (OSError, UnicodeDecodeError)` that a `ValueError`
      escapes, and whose later `state["approved_spec_hash"] =
      sha256_canonical_contract(...)` is **entirely unguarded and writes the
      result**. `with_state_lock` catches only `StateLockError` and `main()` only
      `KeyboardInterrupt`, so unhandled this is a traceback out of a lock holder.
      Each tested site asserts a one-line refusal, and the two lock holders assert
      no state was written while the lock was held.
      Defence in depth, no test claim: `cmd_plan_check_current` and
      `_schedule_check_current_impl` become thin adapters whose only remaining calls
      are `_resolve_spec_dir` and a `@_contained` guard, so no `ValueError` can reach
      them; the handler is retained against future re-expansion but is labelled
      unreachable rather than asserted.
      No traceback escapes a lock-holding process. *(T1a)*
- [ ] AC13 — Two modules load by path, through **two** loaders: `_loop_guards.py`
      via `load_guards()` (three copies — the cohort CLI, the engine, and
      `check-spec-status.py`), and `lint-spec-status.py` via `_lint_spec_status()`
      **inside `_loop_guards.py`**, lazily and memoised, first executed during a
      guard call. Both loaders carry the same four controls, and the stream swap
      belongs to the **second** one, because that is the exec that triggers a
      module-scope `reconfigure`. (An earlier revision claimed the loaders nest;
      they do not — the parser load happens inside a guard call, well after
      `load_guards()` has returned.)
      Both follow `_statelock.py`'s precedent for *registration and memoisation* —
      unregistered, cached in a module global — **plus four controls that precedent
      lacks**: the module path is `lstat`-verified as a regular non-symlinked file
      before load; `sys.dont_write_bytecode` is saved, set, and restored to its
      **prior value** in a `finally`; streams are swapped as described below; and
      completeness is verified as described below. `_loop_guards.py` therefore
      **omits
      `from __future__ import annotations`** — a deliberate, documented departure
      from the sibling scripts' style, because a frozen dataclass under
      future-annotations fails at class creation when its module is absent from
      `sys.modules`, and PEP 604 unions evaluate natively on the 3.11 floor so the
      import buys nothing here. Not registering is what keeps a failed
      `exec_module` from leaving a half-executed module behind: `exec_module` does
      not remove a registered entry when the body raises, so registration would
      require hand-rolled cleanup that the standard `import` machinery does for
      free. `sys.dont_write_bytecode` is saved, set, and restored to its **prior
      value** in a `finally`, so no new `__pycache__` entry is written and a host
      interpreter's `-B` setting is never silently cleared.
      **Completeness by sentinel, not by enumeration.** A module truncated at a
      clean statement boundary loads *without* raising, so each loaded module
      declares `__all__` near the top — where a truncation cannot remove it — and
      `_MODULE_COMPLETE = True` as its **last** statement. The loader requires both:
      `_MODULE_COMPLETE` truthy, and `set(mod.__all__) <= set(dir(mod))`. An
      enumerated required-symbol list is explicitly rejected: it is order-blind, it
      would be restated in each of the three loader copies, and the obvious spelling
      of it ("every relocated name plus the six guards") silently omits
      `GuardResult`, `read_managed_text`, `validate_run_id`, and
      `assert_status_legal`, which are converted or new rather than relocated. A
      pinning test asserts `__all__` equals the relocation list plus those four plus
      the six guards. This detects accidental truncation only, **not** tampering;
      tampering is the accepted write-access residual below.
      **Stream handling, on the loader that needs it.** `lint-spec-status.py` calls
      `sys.stdout.reconfigure(...)` at module scope. That mutates the stream **in
      place** and never rebinds `sys.stdout`/`sys.stderr`, so snapshotting the
      *references* would restore nothing and an identity assertion cannot fail; the
      real hazard is the reverse — a caller whose `sys.stdout` has no `reconfigure`
      (an `io.StringIO`, the established in-suite capture pattern) makes that line
      raise. `_lint_spec_status()` — not `load_guards()` — therefore **swaps**
      `sys.stdout` / `sys.stderr` to a throwaway `io.TextIOWrapper(io.BytesIO())`
      for the duration of the exec and restores them in a `finally`. Not
      `sys.__stdout__`/`sys.__stderr__`: those are `None` under pythonw, embedded,
      and detached-stdio contexts, so swapping to them would convert an environment
      where the caller's own valid stream worked into a total-refusal one.
      Verification is (a) the caller's stream's `encoding` and `errors` unchanged
      across a load, and (b) a case whose `sys.stdout` is an `io.StringIO`,
      asserting the guard returns its real verdict rather than an `internal-error:`
      refusal. An object-identity assertion is explicitly **not** the check. This
      swap is the one sanctioned exception to AC6's no-stream-mutation rule, which
      is scoped accordingly.
      All six load-failure modes — missing, permission-denied, non-regular,
      symlinked, syntactically invalid, partially written — produce a one-line
      refusal with a non-zero exit and no traceback, and the refusal names the
      module path, the failure mode, and the remedy. A seventh case asserts the
      loaded parser did not execute its `__main__` block; an eighth asserts a module
      truncated mid-body leaves nothing reusable behind; and a ninth truncates at a
      clean statement boundary — loading without raising — and asserts the
      completeness sentinel turns it into a load failure. Every case runs against
      **both** loaders, since both now carry the four controls.
      **Residual, accepted:** a `.pyc` that already exists in the gitignored
      `__pycache__` can still be read. The **set of actors** who can plant one is
      unchanged — write access to the scripts directory already implies arbitrary
      code execution via the `.py` itself — but the **blast radius grows**: the
      process that would execute it moves from a short-lived, print-and-exit child
      to the lock-holding engine with write authority over `engine-state.json`,
      `events.pending`, and `events.jsonl`. The deferred
      `statelock-loader-bytecode-cache` item carries that weight. A hand-rolled
      cache-free loader was considered and declined: it replaces a battle-tested
      import path with new code in a privileged position, and in specification it
      produced four defects of its own. *(T1a)*
- [ ] AC14 — An unloadable or unparseable canonical status parser is a refusal,
      not a skipped check. `_read_md_status`'s former `except ImportError:
      return None` no longer lets `_assert_status_legal` treat a broken parser as
      "no status line", so the post-approval status-regression guard cannot
      silently pass. Only an absent status *token* is still skipped; a missing,
      non-regular, symlinked, or unreadable artifact is a refusal.
      **The same fail-open shape must not be reintroduced on the bundled template.**
      `_template_max_implementation_retries` and `_template_max_review_retries`
      currently catch `(FileNotFoundError, OSError, KeyError, TypeError,
      ValueError)` and return a hard-coded fallback — so once `TEMPLATE_PATH` reads
      through the bounded reader, an oversized, non-regular, or symlinked
      `assets/state.json` would silently yield the default 5/5 retry caps instead of
      refusing. An integrity-class reader failure on the template is therefore a
      **refusal**, carrying the integrity marker; the fallback is retained only for a
      genuine `FileNotFoundError` (an adopter tree with no bundled template). *(T1a)*

### CLI compatibility

- [ ] AC15 — `loop-cohort.py identity`, `plan check-current`,
      `schedule check-current`, `check`, `wave check`, and `check-spec-status.py`
      keep their accepted arguments and defaults, their exit-zero versus
      non-zero behavior, their one-line stderr failure form, their success stdout
      messages, and their no-traceback failure behavior. Proven against golden
      stdout and stderr literals captured from the **pre-change** CLIs for every
      failure branch of all six verbs — including `plan_review_status: pending`
      and `_evaluate`'s three refusals, none of which carry a verb prefix. Because those messages embed
      absolute paths and live 64-hex digests, capture and comparison both run
      through one normalization function defined canonically in `plan.md`'s T0.
      **Three named exception classes, each asserted against an explicit `after`
      value rather than the recorded `before`:** **(1)** the AC16 numeric-coercion
      rows; **(2)** `check-spec-status.py`'s `--file`, which AC9 narrows from any
      `is_relative_to`-passing value to a single dot-free path component;
      **(3)** the **artifact-integrity class** — routing `spec.md` / `plan.md`
      through the bounded reader adds `O_NOFOLLOW`, `O_NONBLOCK`, `S_ISREG`, and an
      8 MiB cap to reads that are plain `path.read_text()` today, so a symlinked,
      non-regular, or over-cap artifact newly refuses. That class reaches
      `cmd_approve_plan` and `_schedule_run_impl` as well as the read-only verbs, so
      it changes the accepted-input surface of four cohort verbs, not just the six
      read-only ones — enumerated and ratified rather than left to be discovered.
      Every other row is asserted against `before`. Each row carries a closed
      `change_reason` enum (`numeric-coercion` | `file-narrowing` |
      `artifact-integrity`); the self-check asserts `after` is present **iff**
      `change_reason` is set, and that the observed enum set equals the declared
      one — so the exception list is machine-readable rather than restated a third
      time. *(T0, T2, T6)*
- [ ] AC16 — Where AC8's numeric validation changes a verdict that today's
      coercion accepts — a string-typed or float-typed counter that `int()`
      currently absorbs — the affected inputs are enumerated and recorded so the
      change is deliberate rather than discovered. The fixture carries **two
      fields** for these rows: `before`, the pre-change verdict, recorded for the
      audit trail and never asserted as expected; and `after`, the intended new
      verdict, which is what the parity test asserts. A single-valued fixture would
      make every such row fail by construction, and editing the golden to match
      would destroy exactly the property AC15 exists to provide. *(T0, T1b, T6)*

### Locking and state safety

- [ ] AC17 — `cmd_transition` holds the engine-state lock across the following
      steps, in exactly this order — read from the source, since this criterion is
      the rail the `Never do` reordering prohibition is measured against:
      **(1)** spec-dir re-resolution; **(2)** `--wave-index` validation;
      **(3)** crash recovery (`_recover_engine_state_tmp`, then `_get_repo_root`
      plus `_recover_pending`); **(4)** engine-state read; **(5)** the
      `schema_version` check; **(6)** run-ID preflight; **(7)** transition-table
      validation; **(8)** the CODE schedule pre-check; **(9)** the event-specific
      guard; **(10)** the state decision; **(11)** outbox plus state finalization.
      A double-violation case proves the earlier step's refusal wins: a
      `wave-passed` event with **both** a missing `--wave-index` and an unreadable
      `engine-state.json` refuses on the wave-index (step 2), not on the read
      (step 4); a second pair covers steps 8 vs 9.
      The source-order assertion backing the other nine boundaries carries a
      **vacuity guard and a mutation check**, because four of the eleven steps have
      no callee to anchor on (`--wave-index` validation, the `schema_version` check,
      transition-table validation, and the state decision) and must key on literals
      — an anchor that silently stops matching would drop out of a sorted list that
      then always passes. The assertion fails unless **all eleven** anchors resolve,
      and `Done when:` requires that swapping any adjacent pair of the eleven makes
      it red. This is the antipattern `e6d4c14a` records: *"a gate whose scanned file
      set can collapse to zero while still exiting 0 is silent when it works and
      silent when it is broken… an unmutated assertion is an unverified one."*
      *(T3)*
- [ ] AC18 — No `_loop_guards.py` function acquires the cohort mutation lock, and
      the **recursive listing** of the spec directory and of the repo-root
      `.loop-run/` directory — names and bytes — is identical before and after any
      sequence of guard-API calls. The assertion fails if either directory is
      absent when the snapshot is taken, so it cannot pass by comparing empty to
      empty. No file is created, including any path matching
      `_recover_engine_state_tmp`'s `.engine-state-*.json.tmp` glob or a
      `state.json.lock`. File timestamps are deliberately excluded: nothing in the
      loop keys off artifact mtime. *(T1b)*
- [ ] AC19 — Each logical guard reads the files it needs at call time; no cohort
      snapshot is shared or cached across guards. A test counts `state.json` reads
      across a three-guard transition and asserts three. *(T1b)*
- [ ] AC20 — `_loop_guards.py` loads under direct file-path invocation, under the
      tests' importlib harness, and from a projected adopter-shaped copy, without
      adding the repository root to `sys.path`, without depending on the working
      directory, and without installing `agentbundle`. A test asserts the engine
      loads it **once** across a multi-guard transition, not once per guard.
      *(T5, T7)*

### The lock-hold budget

- [ ] AC21 — Every `subprocess` call reachable from a guard while
      `cmd_transition` holds the lock passes an explicit `timeout=`, and the only
      such calls are `git`. The claim is scoped to the **guard call path**, not to
      transitive capability. `loop-engine.py` and `_loop_guards.py` are scanned
      file-wide (the latter must contain no spawn reference at all).
      `lint-spec-status.py` is **not** scanned file-wide: it imports `subprocess`
      and has four unbounded `git` calls in functions the guard path never invokes,
      and the artifact is an AST **reachability** assertion proving the guard path
      does not reach them — not a file-scoped timeout scan. Adding `timeout=` to
      those four calls was considered and **dropped**: they are unreachable from the
      lock, so it is not a mechanical ride-along but an unspecced change to a shipped
      CLI's failure mode on a slow repository, which would need its own criterion.
      It is recorded in `Deferred` instead. The matched call set is the canonical
      spawn set AC23 names. *(T4)*
- [ ] AC22 — The lock-hold budget is stated honestly rather than overclaimed.
      `MAX_SUBPROCESS_CALLS_UNDER_LOCK` equals the number of external subprocess
      **invocation edges** on the reachable call graph — distinct from call sites,
      of which there is one — and its value is written in exactly one place,
      `plan.md`'s T4. `test_lock_hold_budget` still proves
      `statelock timeout < TIMEOUT_S × MAX_CALLS < stale_after`, still fails when
      an under-lock subprocess call omits `timeout=`, and additionally fails when
      the constant disagrees with the invocation-edge count derived from source.
      The explanatory comment states the split explicitly: **the subprocess half
      is time-bounded at `TIMEOUT_S × edges`; the in-process half is byte-bounded
      and not time-bounded.** A byte cap bounds bytes, not seconds — a stalled
      network mount can still block `os.read`, and `_recover_pending` reads
      repo-global state under the same lock. `O_NONBLOCK` closes the reachable
      local case (FIFO, device); the hung-mount residual is named and accepted,
      its only recovery being the stale-lock reclaim, which is itself the
      integrity hazard the lock exists to prevent. *(T4)*

### Tests and gates

- [ ] AC23 — A deterministic test fails if a transition executes
      `sys.executable`, any other Python interpreter (including the Windows
      `py`/`pyw` launchers), `loop-cohort.py`, `check-spec-status.py`, or any
      other `.py` script, via any spawn primitive in the canonical set defined in
      `plan.md`'s T5 — which covers `subprocess.run`/`Popen`/`check_output`/
      `check_call`, `os.system`, `os.posix_spawn`, `os.exec*`, `os.spawn*`,
      `os.fork`, and `multiprocessing`. It permits `git` and asserts each `git`
      call is bounded. It cannot pass vacuously: it asserts the recorder fired,
      that a guard actually executed, and the expected exit code and resulting
      engine state for each path. A source-absence AST assertion over both
      `loop-engine.py` and `_loop_guards.py` runs alongside as an independent
      second signal. *(T5)*
- [ ] AC24 — Parity tests assert the callable API and the CLI adapter reach the
      same success-or-failure verdict for shared fixtures covering run-ID
      identity, schedule currency, plan currency with and without a required
      schedule, phase retry caps, wave checks, and spec and plan status checks —
      each including the missing-or-malformed-`state.json` refusal the CLI
      performs today. *(T6)*
- [ ] AC25 — `pytest packs/core/tests/skills/work-loop/` passes, including
      `test_loop_engine.py`, `test_loop_cohort.py`,
      `test_loop_cohort_schedule.py`, `test_loop_cohort_max_iter_single_source.py`,
      `test_loop_engine_events_jsonl.py`, and `test_loop_concurrency.py`;
      `bash packs/core/tests/skills/work-loop/test-loop-cohort.sh` passes — gated by
      `tools/test-all.py` and driving **exactly** the six verbs this change converts
      to adapters (`identity`, `plan check-current`, `schedule check-current`,
      `check --phase {implement,review,gates-failed,stub}`, `wave check`), so it is
      the closest pre-existing contract test for them and must pass unmodified;
      `pytest tests/roster/test_work_loop_root_validation.py` passes, whose
      `test_report_sites_route_through_resolver` counts source occurrences in
      `loop-cohort.py` and must not be disturbed; and
      `python3 tools/lint-pack-test-boundary.py` passes, which forbids a pack test
      from reading above its own pack **and** fails any pack test whose single
      `List`/`Tuple`/`Call` node contains both `"rev-parse"` and
      `"--show-toplevel"` — so AC23's `git`-argv assertion must key on `argv[0]`
      plus the `timeout` kwarg without co-locating those two literals. *(T0, T5, T7)*
- [ ] AC26 — `make build-check` and `make lint-ruff` pass, and the Core pack
      source and its `.claude/` and `.agents/` projections are byte-identical.
      *(T7)*
- [ ] AC27 — No new runtime dependency, MCP requirement, daemon, package
      installation, or `uv` requirement is introduced. The Core pack version is
      bumped in **both** files that carry it — `packs/core/pack.toml` and
      `packs/core/.claude-plugin/plugin.json` — because `catalogue verify`'s
      CAT-V-005 is a hard error on a mismatch. (`core` is absent from
      `.claude-plugin/marketplace.json`, so those two files are the complete set.)
      The target version is stated once, in `plan.md`'s T7. Both deferred items
      named in `plan.md`'s `Deferred` section resolve as slugs in
      `workspace.toml [backlog].open`. *(T7)*

## Assumptions

Facts settled by a probe or a direct read. Where a fact is also load-bearing for
a criterion, the criterion references this section rather than restating it.

### Repository layout and versions

- Technical: the canonical Core pack source is
  `packs/core/.apm/skills/work-loop/scripts/` (nine `.py` files);
  `.claude/skills/work-loop/scripts/` and `.agents/skills/work-loop/scripts/`
  are byte-identical tracked projections synced by `make build-self` (source:
  `md5` comparison across `loop-engine.py`, `loop-cohort.py`,
  `check-spec-status.py`, `lint-spec-status.py`, and `_statelock.py`, plus
  `git check-ignore` returning exit 1 for both projected paths).
- Technical: the supported Python floor is 3.11 (source: `pyproject.toml`
  `python_version = "3.11"`, ruff `target-version = "py311"`).
- Technical: `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  both carry `version = "2.7.0"`, and `catalogue verify`'s CAT-V-005 is a hard
  error on a mismatch; `core` is absent from `.claude-plugin/marketplace.json`,
  so the repository-wide knowledge topic's "three files" reduces to two for this
  pack (source: `verify.py:203-217`, `marketplace.json` plugin list, grep for
  `2.7.0`).

### The before-state

- Technical: a transition launched up to three child Python guard processes —
  `loop-cohort.py identity`, `loop-cohort.py schedule check-current`, and one
  event guard, with `plan-locked` reaching three through a two-call composed
  guard — plus three `git rev-parse` calls, one in the `_locked` wrapper outside
  the lock and two inside `cmd_transition` (source: read-only instrumentation
  probe over nine representative transition paths, 2026-08-17).
- Technical: `loop-engine.py` contains 16 `sys.executable` occurrences; 14 are
  live guard shell-outs and 2 sit in `_guard_plan_check_current` and
  `_guard_plan_check_current_require_schedule`, which are defined and never
  referenced anywhere in the repository — the similarly-named
  `test_guard_plan_check_current*` cases are test function names, not call sites
  (source: repository-wide grep, 2026-08-17).
- Technical: exactly one `subprocess` call **site** is reachable under the lock —
  `subprocess.run` inside `_get_repo_root` — reached along two invocation edges,
  from `cmd_transition`'s `_resolve_spec_dir` and from its own `_get_repo_root()`
  call. `MAX_SUBPROCESS_CALLS_UNDER_LOCK = 6` was therefore a conservative bound
  over a measured maximum of five calls. The `_locked` decorator's own
  `_resolve_spec_dir` runs *before* `sl.exclusive()` and is not counted (source:
  probe plus call-graph read).
- Technical: `_statelock.py` declares `DEFAULT_TIMEOUT = 10.0` and
  `DEFAULT_STALE_AFTER = 300.0` (source: `_statelock.py:94-95`). The derived
  product and its inequality are stated once, in `plan.md`'s T4.

### What the child process was silently providing

- Technical: `path.read_text()` on a FIFO blocks indefinitely, and the child
  process's `timeout=SUBPROCESS_TIMEOUT_S` was the only bound on the guards'
  Markdown reads — `_read_managed_json`'s 8 MiB cap covers JSON only (source:
  probe: `read_text` on a `mkfifo` path blocked until `SIGALRM`, 2026-08-17).
- Technical: `os.open` with `O_RDONLY | O_NOFOLLOW` also blocks indefinitely on a
  FIFO, so the existing reader's post-open `S_ISREG` re-check never runs when a
  regular file is swapped for a FIFO after the `lstat`. Adding `O_NONBLOCK`
  returns immediately and is a no-op for regular files, letting the post-open
  type check do the rejecting (source: probe comparing all four combinations,
  2026-08-17).
- Technical: `json.loads` accepts the non-standard `Infinity` literal and
  `int(float('inf'))` raises `OverflowError`, which is outside every exception set
  the guards convert — so an `Infinity` retry cap became a traceback rather than
  a refusal (source: probe, 2026-08-17).
- Technical: `SyntaxError` derives directly from `Exception` — its MRO is
  `(SyntaxError, Exception, BaseException, object)` and it is **not** a
  `ValueError` subclass — so it escapes `except (ImportError, OSError)` and would
  surface as a traceback (source: probe, 2026-08-17; corrects a mis-stated
  parentage in review that reached the right conclusion).
- Technical: `Path.resolve()` on a symlink loop did **not** raise on Python
  3.13.13 — non-strict resolution returned normally. The `RuntimeError` claim
  (CPython #109187) is plausible on the 3.11/3.12 floor but unconfirmed here;
  catching `(OSError, RuntimeError)` is retained as cheap defence rather than as a
  reproduced defect (source: probe, 2026-08-17).
- Technical: `DEFAULTS` is computed at module scope from two helpers that each do
  an unbounded, unchecked `TEMPLATE_PATH.read_text()` on
  `assets/state.json`; `_evaluate` needs `DEFAULTS`, so `check_phase` does, so the
  first guard call inside the critical section would trigger that read — which is
  why AC8 covers the bundled template and the plan makes `DEFAULTS` lazy (source:
  `loop-cohort.py:83-110`, `:1165`, `:1174`).

### Module loading

- Technical: a `@dataclass(frozen=True)` under `from __future__ import
  annotations` raises `AttributeError: 'NoneType' object has no attribute
  '__dict__'` at class creation when its module is absent from `sys.modules` —
  `dataclasses` resolves the module via `sys.modules.get(cls.__module__)` with no
  `None` guard. This reproduces identically under `exec_module` and under a
  hand-rolled `compile`/`exec` loader. **Omitting the future-annotations import
  avoids it entirely** — probe-verified: a frozen dataclass with `str | None`
  fields constructs correctly, and enforces frozenness, in an unregistered
  `exec_module`'d module. `ruff` does not select the `FA` ruleset, so
  future-annotations is not linter-enforced here, and PEP 604 unions evaluate
  natively from 3.10 — above the 3.11 floor (source: probe over all combinations
  plus `pyproject.toml` ruff `select`, 2026-08-17).
- Technical: `exec_module` does **not** remove a `sys.modules` entry when the
  module body raises — probe-confirmed a truncated module survives with early
  names bound and later ones absent, whereas a real `import` cleans up
  (`_bootstrap.py` does `del sys.modules[spec.name]`). This is why the design does
  not register: registration would require hand-rolling the cleanup the standard
  machinery provides. A module truncated at a clean statement boundary can also
  load *without* raising, which is why a required-symbol check is needed regardless
  (source: probe, 2026-08-17).
- Technical: `sys.stdout.reconfigure(...)` mutates the `TextIOWrapper` in place and
  preserves object identity — probe-confirmed — so snapshotting and restoring the
  *references* restores nothing and an identity assertion cannot fail. The real
  failure is a caller whose stream lacks `reconfigure`: `io.StringIO` has no such
  attribute, and `contextlib.redirect_stdout(io.StringIO())` is used in this pack's
  own suites, so a lazily-loaded parser under a redirected stdout would raise
  `AttributeError` and be contained as a refusal (source: probes, 2026-08-17).
- Technical: `exec_module` reads and writes `__pycache__`, validated by source
  mtime and size rather than by hash; `__pycache__/` is gitignored
  (`.gitignore:75`) and `.claude/skills/work-loop/scripts/__pycache__/` already
  contains `_statelock.cpython-313.pyc`. Setting `sys.dont_write_bytecode = True`
  suppresses the write; it does not suppress a read of an existing entry (source:
  probe, 2026-08-17).
- Technical: a module executed with `__name__ == "__main__"` runs
  `lint-spec-status.py`'s `if __name__ == "__main__": sys.exit(main())`, producing
  `SystemExit(code=0)` — a `BaseException` that `except Exception` does not catch,
  with a success code. `exec_module` sets `__name__` from the spec, which is one
  reason to keep it rather than hand-roll (source: probe, 2026-08-17).
- Technical: `lint-spec-status.py` imports `argparse` and `subprocess` and calls
  `sys.stdout.reconfigure` / `sys.stderr.reconfigure` at module scope, and has
  four `subprocess.run` calls with no `timeout=` (`:307`, `:316`, `:325`, `:427`)
  in functions the guard path does not invoke. So an absolute "the guard layer
  reaches no spawn capability" claim is transitively false, and loading it mutates
  the caller's streams — both stated rather than papered over (source: direct
  read, 2026-08-17).
- Technical: a cached importlib-by-path load of an underscore-named sibling module
  is the established in-repo pattern, used for `_statelock.py` by both
  `loop-engine._statelock()` and `loop-cohort._statelock()` (source: both call
  sites).

### Test surface

- Technical: `lint-spec-status.py` is the canonical status parser on the
  work-loop guard path. It is **not** the repository's only `**Status:**` matcher
  — `lint-spec-status.py`, `receive-brief/scripts/lint-brief-coverage.py`, and two
  copies of `workspace_status_engine.py` each compile their own, which is why AC4
  is scoped to the guard path rather than repository-wide (source: grep for
  `_STATUS_RE` / `_STATUS_FIELD_RE`, 2026-08-17).
- Technical: `tools/lint-pack-test-boundary.py`'s `case_pack_tests_stay_in_pack`
  ("pack tests may inspect only their owning pack and temporary fixtures") is
  wired into `tools/test-all.py:120`, so a pack test that reads
  `docs/specs/*/spec.md` is a hard gate failure — the reason AC5's corpus is
  copied into the pack's fixtures directory rather than referenced in place
  (source: `lint-pack-test-boundary.py:749`, `test-all.py:120`).
- Technical: the live corpus is 645 files (348 `spec.md`, 297 `plan.md`), all of
  which hash cleanly in 0.74 s. Exactly one carries an odd fence count
  (`m2-frame-situation/plan.md`, 9 fences), several plans carry checkboxes, and
  **zero** specs use a lowercase-`c` `Acceptance criteria` heading — so that
  edge case must be a hand-authored fixture rather than a captured one (source:
  probe over the whole corpus, 2026-08-17).
- Technical: existing engine guard tests assert exit code and
  `engine-state.json` non-mutation rather than exact guard stderr text, and the
  existing CLI cases assert only non-zero or a single substring — so message
  preservation needs the pre-change golden literals AC15 requires (source:
  `test_loop_engine.py` preflight, guard, and `check-spec-status` cases).
- Technical: `loop-cohort.py`'s guard messages interpolate absolute paths and live
  64-hex digests (`:970`, `:972`, `:983-984`, `:992-993`, `:1038`), and
  `check-spec-status.py`'s interpolate the resolved absolute target
  (`:84`, `:94`, `:100`, `:112`), so a golden literal captured in one `tmp_path`
  cannot equal a replay in another without normalization (source: direct read).
- Technical: `cmd_check` calls `read_state` — and therefore refuses on a missing
  or malformed `state.json` — *before* reaching the `implement` phase's
  unconditional-zero stub, so `check --phase implement` is not a total no-op and
  `check_phase` must preserve that refusal. `cmd_wave_check` and
  `_schedule_check_current_impl` refuse there too (source:
  `loop-cohort.py:1138-1153`, `:1195-1197`, `:1022-1024`).
- Technical: `_read_md_status` catches only `(OSError, UnicodeDecodeError)`, and
  `cmd_plan_check_current`, `_schedule_check_current_impl`, and
  `_schedule_run_impl` catch nothing around their artifact reads — the last of
  which runs under the cohort state lock — so introducing a `ValueError`-raising
  bounded reader without widening them would put a traceback inside a
  lock-holding mutation verb (source: `loop-cohort.py:823`, `:978`, `:987`,
  `:1032`, `:1097`).
- Technical: tests reach into `loop-cohort` module attributes
  `canonical_contract`, `sha256_canonical_contract`, `DEFAULTS`,
  `_validate_run_id`, and `_template_max_implementation_retries.__defaults__[0]`,
  and `test_loop_cohort_max_iter_single_source.py:41-52` reads `mod.DEFAULTS`
  immediately after `exec_module` with no verb invoked — so the re-binding must be
  eager, which is why load failure needs a sentinel rather than a raising import
  (source: grep across the pack test directory).
- Technical: the lock-budget test AST-scans only `loop-engine.py` today, matches
  only `("run", "Popen", "check_output")`, and cites a stale filename
  `test-loop-concurrency.py` at `loop-engine.py:67`; `loop-cohort.py`'s `run_git`
  is an existing unbounded `subprocess.run` in the file the guards are extracted
  from (source: `test_loop_concurrency.py:686-705`, `loop-cohort.py:304-311`).
- Technical: `_recover_engine_state_tmp` globs `.engine-state-*.json.tmp` in the
  spec directory and promotes the first valid match over `engine-state.json`, so
  a stray file matching that glob would become engine state — which a
  six-named-file byte comparison cannot detect, hence AC18's directory-level form
  (source: `loop-engine.py:314-337`).
- Technical: `tests/roster/test_work_loop_root_validation.py::test_report_sites_route_through_resolver`
  counts `= _resolved_report(args.report)` occurrences in `loop-cohort.py`
  source. Both sites are in `review inspect` / `review record`, outside this
  change, so it stays green — but it is a source-content anchor on a file this
  change edits (source: anchor-test sweep, 2026-08-17).
- Technical: two run-ID checks with different message sets coexist and must not
  be merged — `cmd_identity`'s (`identity: run_id mismatch (stored=…,
  expected=…)`) and `_validate_run_id`'s (`{verb}: --expect-run-id mismatch
  (stored=…, supplied=…)`) (source: `loop-cohort.py:733-741`, `:501-513`).
- Technical: the plan's task graph parses and schedules — nine tasks, no cycles,
  no forward references, seven waves — and `TASK_HEADING_RE`'s `T\d+[a-z]?`
  accepts the lettered `T1a` / `T1b` IDs (source: `parse_plan` /
  `topological_waves` run against `plan.md`, 2026-08-17).

### Process and product

- Process: authoring a stdlib-only helper as a work-loop script, rather than
  sharing one from `agentbundle`, is the sanctioned pattern (source: ADR-0074
  Decision summary — "stdlib-only helpers a skill needs. Default to authoring
  them in the skill").
- Process: status and acceptance-criterion recognition must have exactly one
  implementation on this path (source: ADR-0061, cited at `loop-cohort.py`'s
  `_lint_module` comment).
- Product: the Core pack version bumps for this Core runtime change, even though
  no gate was found to enforce a bump and recent history is mixed (source: user
  confirmation 2026-08-17).
- Product: the engine's own stderr sheds both nested interior markers it
  previously inherited from capturing a child's stderr — `loop-cohort: stop — `
  and `check-spec-status: `. Every engine prefix and the guard reason itself are
  preserved, and both CLIs' own stderr is unchanged (source: user confirmation
  2026-08-17, extended to the second marker after review).
- Product: the pre-existing status-guard fail-open — an unloadable canonical
  parser silently skipping the post-approval status-regression check — is fixed
  here rather than deferred, because this change makes that loader load-bearing
  for the engine's in-process path (source: user confirmation 2026-08-17).
- Product: the engine's duplicate `_read_managed_json` is routed through the
  shared reader rather than left as a third copy (source: user confirmation
  2026-08-17).
- Product: refactoring `_validate_run_id` and `_assert_status_legal` without
  changing any mutation-verb call site is signed off, and the `Ask first` rail is
  worded to cover a mutation verb's body or accepted arguments (source: user
  confirmation 2026-08-17).
- Product: widening three mutation verbs' `except` clauses so an unsafe artifact
  refuses instead of raising is signed off as a separate change to their failure
  behavior (source: user confirmation 2026-08-17).
- Product: `importlib`'s `exec_module` is retained with `sys.dont_write_bytecode`
  rather than replaced by a hand-rolled cache-free loader. The hand-rolled option
  was specified in an earlier revision and declined after it generated four
  distinct defects — the dataclass/`sys.modules` failure, the
  `__name__` → `SystemExit(0)` hazard, three drifting copies, and a required
  `bandit` `exec` suppression — for a residual (reading a pre-existing `.pyc`)
  that is unchanged from today (source: user confirmation 2026-08-17).
- Product: `_loop_guards.py` omits `from __future__ import annotations` and is not
  registered in `sys.modules`, matching `_statelock.py`'s precedent. This retires
  the half-loaded-module hazard, the session-global-singleton test leakage that
  registration would have introduced across a pytest session, and the
  `__future__`-in-the-allowlist gap — by removing code rather than adding it
  (source: user confirmation 2026-08-17, after round-3 review).
- Product: `check-spec-status.py --file` narrows from any value passing
  `is_relative_to` to a single dot-free path component, and a symlinked `spec.md`
  that `read_text()` follows today is refused by the bounded reader. Both are
  narrowings of a shipped CLI's accepted inputs, recorded as named exceptions in
  AC15 rather than left to be discovered (source: user confirmation 2026-08-17).
- Technical: `pytest`'s `tmp_path` resolves through `/private/var` on macOS, so no
  existing test crosses a symlinked ancestor — the trap recorded in
  `docs/knowledge/topics/pytest-tmp-path-hides-symlinked-ancestor-path-bugs.json`.
  The leaf-scoped symlink guard is correct because all three callers `resolve()`
  first, which is exactly why the untested half is the **false-refusal** surface:
  T1a carries an accept-case for a spec directory reached through a symlinked
  ancestor (source: knowledge topic plus design reasoning, 2026-08-17).
- Product: the residual inconsistency AC19 preserves — the engine holds only its
  own `engine-state.json` lock while reading the cohort's `state.json`, so a
  transition can in principle be admitted against a mix of two `state.json`
  generations — is pre-existing, deliberately unchanged, and tracked by the
  existing `loop-outbox-cross-spec-rmw` backlog item (source:
  `loop-engine.py` `cmd_transition` comment).
