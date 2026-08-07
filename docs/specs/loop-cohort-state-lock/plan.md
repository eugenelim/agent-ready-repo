# Plan: loop-cohort-state-lock

- **Status:** Drafting <!-- Drafting | Approved | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Owner:** eugenelim

## Assumption trio

**Files I will touch**

| File | Why |
|---|---|
| `packs/core/.apm/skills/work-loop/scripts/_statelock.py` | new — the hardened lock |
| `.../scripts/loop-cohort.py` | wire 5 verbs + init/reset |
| `.../scripts/loop-engine.py` | wire `cmd_transition` + init/reset; bound the under-lock subprocesses |
| `packs/core/tests/skills/work-loop/test-statelock.py` | new — lock unit suite |
| `packs/core/tests/skills/work-loop/test-loop-concurrency.py` | new — the regressions |
| `packs/core/tests/skills/work-loop/test-loop-cohort.sh` | run the two new suites |
| `.gitignore`, `packs/core/seeds/.gitignore` | ignore lockfiles — ours **and** the shipped adopter seed |
| `.github/workflows/docs.yml` | path triggers |
| `docs/adr/0074-*.md` | new — the port-not-share decision |
| `docs/product/changelog.md` | user-facing entry |
| `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | version bump |
| `.claude/**`, `.agents/**` | projected by `make build-self`, never hand-edited |
| `workspace.toml` | close one backlog item, open four |

**What demonstrates done** — `test-loop-concurrency.py` passes on the fixed tree
and **fails on the pre-fix tree** (verified via `git worktree`, never `git
stash`; the stash stack is shared across Conductor workspaces). Plus
`test-statelock.py`, the six existing suites unchanged, and `make build-check`.

**What I am not changing** — the state schemas, the FSM transition table, any
guard's logic, `write_state_atomic`'s mkstemp+replace mechanics,
`_resolve_spec_dir`'s confinement contract in either script, and
`agentbundle/statelock.py`. Verb flags and stdout formats are unchanged; verbs
do gain one new non-zero refusal path (spec AC13), which is why "exit codes" is
not on this list.

## Declined patterns

| Tempted to | Declined because |
|---|---|
| Import `agentbundle.statelock`, or extract a third shared module | ADR-0074 — incompatible import constraints; a shared home would have to satisfy the stricter one anyway. |
| Vendor `statelock.py` verbatim | It hot-spins forever on a dangling-symlink lock path (confirmed, `notes/reproduction.md` Case C). Porting means hardening. |
| Mirror `persist_state_locked(path, mutate)` | Every call site needs the *decision* inside the lock, not a mutate callback. A bare context manager fits all nine sites; the callback shape would have invited read→write-only locking. |
| `fcntl.flock` | Windows CI. |
| Fix `agentbundle/statelock.py`'s spin in this PR | Different package, published to PyPI, needs its own release. Surfaced as a decision; tracked as `agentbundle-statelock-symlink-spin`. |
| Confine `loop-cohort.py`'s `_resolve_spec_dir` to the repo root while I'm here | A behavior change to the CLI's accepted inputs, beyond this brief. Neutralised instead by adding no directory-creating primitive (AC9). Tracked separately. |
| Lock the repo-global outbox, or the read-only verbs | Second lock scope needs an acquisition order; read-only verbs are the reason the design is acyclic. Both are `Never do` / `Ask first` in the spec. |
| Fix `append-knowledge.py`'s identical RMW | Different file, not named by the backlog item; its temp-then-lint-then-replace flow needs its own thinking. Deferred. |
| A heartbeat thread to keep a long hold fresh | Bounding the subprocesses gives a *provable* max hold with no concurrency added to a concurrency fix. |
| `--no-lock` escape hatch | No second caller needs to differ. |
| Retry the verb on `StateLockTimeout` | Silently re-running a mutation is how a retry counter double-counts. Fail loudly. |

## Resolve-vs-surface disposition record

| Item | Disposition |
|---|---|
| Brief claimed the sibling branch adds `exclusive()` to `append-knowledge.py` to reuse | **Resolved** — false. That branch's copy has no lock; `statelock.py` is the sole precedent. Reported. |
| Does `engine-state.json` share the shape | **Resolved** — yes, and worse (illegal transition admitted). In scope, reproduced. |
| Precedent's dangling-symlink hot spin | **Resolved for the port** (AC5) / **surfaced upstream** — the shipped package is still affected. |
| Lockfile placement, sibling vs `.loop-run/` | **Resolved** — sibling, per precedent; costs two `.gitignore` lines. |
| Cross-spec outbox race | **Surfaced** — `loop-outbox-cross-spec-rmw`; AC12 records that position ≠ protection. |
| `append-knowledge.py`, `_resolve_spec_dir` confinement | **Surfaced** — tracked. |
| Under-lock subprocess bound vs `stale_after` | **Resolved** — linked budget, AC7; measured in T4. |

## Design (LLD)

### Concurrency and locking

`exclusive(path, *, timeout=10.0, stale_after=300.0, poll=0.05)` — a context
manager yielding once the sibling `<path>.lock` is held.

Acquire loop, per iteration:

1. `os.open(lock, O_CREAT | O_EXCL | O_WRONLY, 0o600)` → on success, write a
   token (`uuid4` + pid), close, yield.
2. On `FileExistsError`: `os.lstat` the lock path. **Not `stat`** — `lstat` does
   not follow a symlink, which is what turns the precedent's
   `FileNotFoundError` path into an unbounded spin.
   - Not a regular file (symlink, dir, FIFO) → refuse immediately with a
     `StateLockTimeout` naming the path. Fail closed, do not wait: nothing about
     it will become acquirable.
   - Older than `stale_after` → reclaim by `rename` to
     `<lock>.reclaim.<pid>`, unlink that, retry. Rename is atomic, so exactly
     one of N reclaimers wins; a bare `unlink` would let two win and delete a
     third's fresh lock.
   - Otherwise → **check the deadline, then sleep `poll`**. Every `continue`
     path in the loop passes through this check; that is the invariant AC5
     pins.
3. On any other `OSError` (EACCES, EROFS, ENOSPC, `IsADirectoryError`) → let it
   surface as a lock-acquisition failure the caller renders through `stop()`.

Release, in `finally`: re-read the lockfile's token; unlink **only** if it is
still ours. A holder whose lock was reclaimed must not delete its successor's.

No `mkdir`. The precedent's `mkdir(parents=True, exist_ok=True)` is safe only
because its state path is confined; `loop-cohort.py`'s is not, so inheriting it
would give `loop-cohort reset /tmp/a/b/c` an arbitrary-directory-creation side
effect on a path it then refuses.

`StateLockTimeout(Exception)` — deliberately **not** `OSError`. Both scripts
carry broad `except OSError` handlers (`loop-cohort.py:585`) and 14
`except Exception: warn; continue` sites in `loop-engine.py`; deriving from
`OSError` puts a silent fall-through one boundary-drift away.

**The linked budget (AC7).** `stale_after` must exceed the provable maximum
hold. The engine holds the lock across git-shelling guards whose runner has no
timeout today (`loop-engine.py:305-308`), so T4 adds an explicit `timeout=` to
those calls. Budget: bounded subprocess time × worst-case call count <
`stale_after`. T4 records the measured hold and the resulting margin. Without
this, a merely-slow holder is judged dead and a second writer is admitted —
reinstating the defect.

### Module loading

Both scripts load `_statelock` via `importlib.util.spec_from_file_location`
against their own `SCRIPT_DIR` — the idiom already established in this directory
(`loop-cohort.py:179` for `lint-spec-status.py`; `append-knowledge.py:91` for
`lint-knowledge.py`). A plain `import _statelock` resolves under file-path
invocation but breaks under an importlib-based harness, which does not put the
script's directory on `sys.path` — and the concurrency tests are exactly such a
harness.

### Critical-section extent

Cohort: open before `read_state()`, close after `write_state_atomic()`.

Engine: open before `_recover_engine_state_tmp`, close after the outbox
finalisation — **past** `_write_engine_state_atomic`, through
`_append_events_jsonl` and the pending unlink. Releasing at the write leaves
this reachable: A writes pending, writes engine-state, releases; B acquires,
`_recover_pending` matches on `to`/`seq`/`run_id` (`loop-engine.py:216-229`) and
replays A's event; B refuses `illegal transition`; A then appends its own
`pending_data` again → a duplicate `(spec, seq)` for the *same* spec, which the
cross-spec deferral does not cover.

## Tasks

### T1 — Port and harden the lock module

**Depends on:** none · **Mode:** TDD
**Tests:** `test-statelock.py` — `stub: true`, markers `# STUB: AC1`…`# STUB: AC9`.
`test_stdlib_only_via_ast` (AC1/AC2, `ast.parse` walk of `Import`/`ImportFrom`,
not a grep), `test_mutual_exclusion` (AC3), `test_no_lockfile_after_body_raises`
(AC3), `test_mode_0600_and_pid_recorded` (AC4),
`test_timeout_message_names_path_and_pid` (AC4),
`test_dangling_symlink_terminates` / `_directory_` / `_fifo_` (AC5),
`test_concurrent_reclaimers_yield_one_holder` (AC6),
`test_release_is_ownership_checked` (AC7),
`test_timeout_is_not_oserror` (AC8), `test_no_mkdir` (AC9).
**Approach:** write `_statelock.py` per `## Design (LLD)`. Docstring names
ADR-0074 and the deliberate divergence from the precedent.

### T2 — The regressions, red

**Depends on:** none · **Mode:** TDD
**Tests:** `test-loop-concurrency.py` — `stub: true`, markers
`# STUB: AC15`…`# STUB: AC18`. `_run_barriered(n, module, argv)` spawns
**separate OS processes**, each loading the target module via
`spec_from_file_location`, spinning to a shared wall-clock instant, then calling
`main(argv)`; exit codes are read per child, never from a shared stream.
`test_concurrent_record_attempt_no_lost_update` (AC15, N=2 and N=8, 20 trials),
`test_concurrent_identical_transition` (AC16, incl. no duplicate `(spec, seq)`
and the loser's message being `illegal transition`, not a lock timeout),
`test_concurrent_init` (AC17), `test_harness_is_hermetic` (AC18).
**Approach:** hermetic by construction — reuse the blessed
`_init_git_repo` / `_make_spec_dir` / `_engine_init` helpers at
`test_loop_engine_events_jsonl.py:27-56` so `_get_repo_root()` resolves inside
`tmp_path`. Without this the suite writes the live repo's `.loop-run/` and can
replay or discard the pending event of the very run that owns this PR. Confirm
both cases **fail** on the current tree before T3/T4.

### T3 — Wire `loop-cohort.py`

**Depends on:** T1, T2 · **Mode:** TDD (T2's AC15/AC17 go green)
**Tests:** `stub: true` in T2's file — `test_locked_verbs_refuse_when_held`
(AC13, parametrised over the seven cohort verbs, asserting non-zero **and**
byte-identical state), `test_noop_paths_do_not_write` (AC14: repeated
`--cycle-id`; `approve-plan` when already approved).
*Note:* `test-loop-cohort.sh:426-436` is the `status is read-only` case — it
covers an unlocked read-only verb and does **not** protect AC14. AC14 needs the
new assertions above.
**Approach:** load `_statelock` per the LLD idiom; wrap the five verbs plus
`cmd_init` / `cmd_reset`. Map `StateLockTimeout` and any lock-acquisition
`OSError` onto the existing `stop()` so refusals keep one shape.

### T4 — Wire `loop-engine.py` and bound the under-lock subprocesses

**Depends on:** T1, T2 · **Mode:** TDD (T2's AC16 goes green)
**Tests:** `stub: true` in T2's file — `test_locked_engine_verbs_refuse_when_held`
(AC13 for `transition`/`init`/`reset`), plus
`test_loop_engine_events_jsonl.py` unchanged.
**Approach:** wrap `cmd_transition` from `_recover_engine_state_tmp` through the
outbox finalisation (LLD). Add `timeout=` to the subprocess calls made under
lock. Measure worst-case hold; record it and the `stale_after` margin here and
in the changelog if it moves a default. AC12: comment at the `_recover_pending`
call that it sits inside the section but is not protected by it.

### T5 — Ignore lockfiles, here and for adopters

**Depends on:** T3, T4 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `git check-ignore -q` exits 0 for
`docs/specs/foo/state.json.lock`, `docs/specs/foo/engine-state.json.lock` and
`docs/specs/foo/state.json.lock.reclaim.999`; the same patterns are present in
`packs/core/seeds/.gitignore`; `git status --short` is empty after a run that
leaves both residues. Verify with `git ls-files` after staging — a gitignore
rule can silently fail to apply.

### T6 — Projection + CI wiring

**Depends on:** T5 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `make build-self` leaves the three copies of each touched script
byte-identical (`md5`), `python3 tools/test-all.py` and `make build-check` pass.
**Approach:** register the two new suites in `test-loop-cohort.sh` (which
`test-all` already invokes); add `docs.yml` triggers for `_statelock.py` under
both `.claude/` and `packs/core/.apm/` — `packs/**` covers only the latter — and
for the two test files. Re-check `git status` after `build-self`; it overwrites
projection-only edits.

### T7 — Docs, decision record, version

**Depends on:** T6 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `lint-spec-status.py --root .` exits 0 and the changelog entry is
present.
**Approach:** ADR-0074 (written at PLAN, confirm ordinal still free against
`origin/main` before merge); changelog entry; the three version files.

### T8 — Backlog register

**Depends on:** T7 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `grep` confirms `loop-cohort-state-rmw-unlocked` is gone from
`[backlog].open` and all four new slugs are present (AC23).
**Approach:** `loop-outbox-cross-spec-rmw`, `append-knowledge-rmw-unlocked`,
`agentbundle-statelock-symlink-spin`,
`loop-cohort-resolve-spec-dir-confinement`, each with a cold-start-sufficient
comment naming problem, fix, file, and unblock condition.

## Risks

| Risk | Mitigation |
|---|---|
| A concurrency test that passes against the unfixed tree | T2 requires observing red first; the barrier and separate-process requirements are in the spec's Testing strategy. |
| Flaky timing in CI | Assert invariants, never windows or transient filenames. Generous barrier lead so slow CI startup still lands inside it. |
| A slow-but-live holder is reclaimed → two writers | The linked budget (AC7) plus ownership-checked release. |
| Test suite pollutes the live repo's `.loop-run/` | AC18 hermeticity, using the blessed temp-repo helpers. |
| `make build-self` reverts a hand-edit | Only edit `packs/core/.apm/`; re-check `git status` after. |
| The two lock copies drift | ADR-0074 names it as expected, with each docstring pointing at the other. |

## Rollout

Ships as part of `core`. Adopters receive `_statelock.py` on their next
install/upgrade of the pack; no migration, no state-file change, no flag. The
version bump is three files (`pack.toml`, `plugin.json`, `marketplace.json`) —
`build-self` syncs none of them. Existing in-flight runs are unaffected: no
schema key changes, and an unlocked older run simply has no lockfile to
contend for.
