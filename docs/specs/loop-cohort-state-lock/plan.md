# Plan: loop-cohort-state-lock

- **Status:** Done <!-- Drafting | Approved | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Owner:** eugenelim

## Assumption trio

**Files I will touch**

| File | Why |
|---|---|
| `packages/agentbundle/agentbundle/statelock_core.py` | **new — the one authored lock** |
| `packages/agentbundle/agentbundle/build/skill_libs.py` | new — projection primitive (`apply_projection` + `check_drift`) |
| `packages/agentbundle/agentbundle/build/self_host.py` | wire both halves, mirroring the `user_libs` call sites |
| `packages/agentbundle/tests/unit/test_skill_libs.py` | new — projection + drift-gate suite |
| `packs/core/.apm/skills/work-loop/scripts/_statelock.py` | **generated** — never hand-edited |
| `.../scripts/loop-cohort.py` | wire 7 verbs |
| `.../scripts/loop-engine.py` | wire `transition`/`init`/`reset`; bound under-lock subprocesses |
| `packs/core/tests/skills/work-loop/test-statelock.py` | lock unit suite (written at PLAN, red) |
| `.../test-loop-concurrency.py` | the regressions (written at PLAN, red) |
| `.../test-loop-cohort.sh` | run the two new suites |
| `.gitignore`, `packs/core/seeds/.gitignore` | lockfile + reclaim residue |
| `.github/workflows/docs.yml` | path triggers |
| `docs/adr/0074-*.md` | the projection decision |
| `docs/product/changelog.md`, `pack.toml`, `plugin.json`, `marketplace.json` | ship-side |
| `.claude/**`, `.agents/**` | projected; never hand-edited |
| `workspace.toml` | close one item, four already opened |

**What demonstrates done** — `test-loop-concurrency.py` and `test-statelock.py`
pass on the fixed tree and **fail on the pre-fix tree** (verified via
`git worktree`, never `git stash` — the stash stack is shared across Conductor
workspaces); the six existing suites unchanged; `make ci`.

**What I am not changing** — the state schemas, the FSM table, any guard's logic,
`write_state_atomic`'s mkstemp+replace, either `_resolve_spec_dir`'s confinement
contract, and — deliberately — `statelock.state_lock` and its callers
(ADR-0074; the migration is `agentbundle-statelock-symlink-spin`). Verb flags and
stdout formats are unchanged; verbs gain new non-zero refusal paths (AC15, AC9),
which is why "exit codes" is not on this list.

## Declined patterns

| Tempted to | Declined because |
|---|---|
| Hand-copy the lock into the skill | ADR-0074 — two implementations drift, and a fix to one is not a fix to the other. This was round 1's decision and it was wrong: the repo already had a projection mechanism. |
| Project into `.apm/user-libs/` like credbroker | That target is a lowest-precedence, existence-guarded `sys.path` floor — it degrades to *absent*, and an absent lock fails open. |
| Rewire `persist_state_locked` onto the new core here | Changes installer behaviour and needs an agentbundle release. Separate PR, hard `needs` edge. |
| Generalise `user_libs.py` to take a source/target table | It is credbroker-shaped throughout (`PACKAGE_SUBPATH`, `VENDORED_MODULE`, two fixed roots). A sibling module with one entry is the boring option; generalise when a second entry exists. |
| `fcntl.flock` | Windows CI. |
| Reclaim by `unlink` after an mtime check | Two contenders both unlink and delete a third's fresh lock. Even rename-then-unlink is unsafe without an inode re-check — see LLD. |
| A heartbeat thread to keep a long hold fresh | Adds concurrency to a concurrency fix. A machine-checked hold bound (AC10) gives the same guarantee statically. |
| Retry the verb on a lock failure | Silently re-running a mutation is how a retry counter double-counts. Fail loudly. |
| `--no-lock` escape hatch | No second caller needs to differ. |
| Confine `loop-cohort.py`'s `_resolve_spec_dir` here | Narrows the CLI's accepted inputs — beyond this brief. Neutralised instead (AC12 no mkdir, AC9 no unrecognised delete) and tracked. |

## Resolve-vs-surface disposition record

| Item | Disposition |
|---|---|
| Brief claimed the sibling branch adds `exclusive()` to reuse | **Resolved** — false; no lock of any kind there. `statelock.py` was the only precedent. Reported. |
| Does `engine-state.json` share the shape | **Resolved** — yes, and worse. Reproduced. |
| Precedent hot-spins on a dangling symlink | **Resolved for the new core** (AC8); **surfaced** for the shipped package → user chose a separate PR. |
| Port vs project | **Surfaced** → user chose **project**. ADR-0074 rewritten. |
| Decisions 1 and 2 collide (projecting would auto-fix the shipped bug) | **Resolved** — new `statelock_core.py` alongside the untouched `state_lock`, so the follow-up PR is a de-duplication. Flagged to the user. |
| Reclaimed holder still writes and exits 0 | **Resolved** — AC9's lost-lock report; also makes the residual reclaim race fail-loud instead of fail-silent. |
| Cross-spec `_recover_pending` reach | **Surfaced** — `loop-outbox-cross-spec-rmw`, which now names the engine-state reach, not just the outbox. |
| `append-knowledge.py`, `_resolve_spec_dir` confinement | **Surfaced** — tracked with `needs` edges. |

## Design (LLD)

### Concurrency and locking

`exclusive(path, *, timeout=10.0, stale_after=300.0, poll=0.05)`, yielding once
the sibling `<path>.lock` is held. Exceptions: `StateLockError` base,
`StateLockTimeout` (contended, retry later) and `StateLockUnusable` (will never
be acquirable) as subclasses, plus `StateLockLost` raised at release. None derive
from `OSError` — `loop-cohort.py:585` catches `(OSError, ImportError)` and
`loop-engine.py` has 14 `except Exception: warn; continue` sites, so an
`OSError`-derived lock error is one boundary-drift from a silent fall-through.

Lockfile record: exactly `statelock1 <uuid4-hex> <pid>\n`. Read at most 256
bytes. Anything that does not parse is *not ours* — the reclaim path refuses to
touch it, so the lock never deletes a file it does not recognise. The pid is
rendered into a message only after matching `^[0-9]{1,10}$`, so lockfile bytes
cannot reach a terminal unvalidated.

Acquire, per iteration:

1. `os.open(lock, O_CREAT | O_EXCL | O_WRONLY, 0o600)`. On success: write the
   record — **if that write fails, unlink and fail closed**, because an empty
   lockfile means release can never recognise it and the lock wedges for
   `stale_after`. Capture `(st_dev, st_ino)` from `os.fstat(fd)`, close, yield.
2. On `FileExistsError`: `os.lstat` the path — **`lstat`, never `stat`**. `stat`
   follows a symlink and raises `FileNotFoundError`, whose `continue` in the
   precedent has no deadline check and no sleep; that is the confirmed 98%-CPU
   spin.
   - Not a regular file → `StateLockUnusable` immediately. Waiting cannot help.
   - Older than `stale_after` and parses as ours → reclaim (below).
   - Otherwise → check the deadline, then sleep `poll`. **Every** `continue` in
     this loop passes through that check.
3. Any other `OSError` → wrap in `StateLockError`; the caller renders `stop()`.

Reclaim, race-safely. A bare `unlink` lets two contenders both delete and a
third's fresh lock vanish. Rename alone is not enough either: T2 lstats a stale
lock, T1 reclaims and creates a fresh one, then T2 renames *T1's live lock*
away — two holders. So:

1. `rename` to `<lock>.reclaim.<uuid4>` — unique per attempt, not per pid
   (same-pid threads collide on a pid-keyed name).
2. `os.lstat` the renamed file and compare `(st_dev, st_ino)` **and the record
   bytes** with what step 2 observed. Inode identity alone false-matches after
   inode reuse (routine on ext4/tmpfs), which would delete a foreign file
   created in the window. Match → unlink and retry acquire.
3. Mismatch → we moved a *live* lock, so restore it with `os.link` +
   `unlink(claimed)`, **not** `rename`. `rename` silently replaces its
   destination, so if a third process took the momentarily-free lock path,
   restoring by rename would delete that process's lockfile and leave two
   holders in their bodies. `link` raises `FileExistsError` instead; leaving
   `claimed` in place then makes the *displaced* holder fail closed at release.
4. The residual window is bounded by AC9: a holder whose lockfile was moved
   discovers it at release and reports a lost lock. Fail-loud, not fail-silent.

Release, in `finally`: compare `(st_dev, st_ino)` **and the record bytes** to the
acquire-time capture. Identity, not content — content comparison would reject a
correct inode-based implementation, and a truncate-in-place rewrite keeps the
same inode. Match → unlink. Missing or foreign → leave it (it is the successor's)
and raise `StateLockLost`, which each verb renders as a non-zero
"lost the lock mid-mutation, state may not reflect this run" refusal naming the
state file.

**The linked budget (AC10), machine-checked.** `timeout` (10) < max hold <
`stale_after` (300). Max hold is bounded by giving every subprocess reachable
under lock an explicit `timeout=`. Two sites, not one: `_run`
(`loop-engine.py:305-308`, ~15 guard call sites) **and** `_get_repo_root`
(`loop-engine.py:67-73`), which is called at `:730`, inside the section AC14
opens. `loop-cohort.py:155`'s `run_git` is currently uncalled. A test AST-walks
the locked call graph and fails when a new unbounded call appears, so the budget
cannot rot as guards are added.

### Projection

Source `packages/agentbundle/agentbundle/statelock_core.py` → target
`packs/core/.apm/skills/work-loop/scripts/_statelock.py`, then onward to
`.claude/` and `.agents/` by the existing skill projection.

`build/skill_libs.py` mirrors `user_libs.py`'s contract exactly —
`compute_projections` / `apply_projection` / `check_drift`, resolving **modified
/ missing / orphaned**, deterministic order, each message ending in
`run: make build-self FORCE=1`, and a no-op when the package source is absent
(non-monorepo). Single-file rather than a tree walk, so no `EXCLUDED_DIR_NAMES`
and no orphan scan beyond the one declared target. Wired at the two
`user_libs` call sites in `self_host.py` (`:1214` apply, `:1584` drift).

The generated file carries a header naming its source and forbidding hand-edits.

### Module loading

Both scripts load `_statelock` via `importlib.util.spec_from_file_location`
against their own `SCRIPT_DIR` — the idiom already at `loop-cohort.py:179` and
`append-knowledge.py:91`. A plain `import _statelock` works under file-path
invocation but not under an importlib harness, which is exactly what the
concurrency suites are.

### Critical-section extent

Cohort (7): `cmd_approve_plan`, `_schedule_run_impl`, `cmd_wave_advance`,
`cmd_record_attempt`, `cmd_review_record`, `cmd_init`, `cmd_reset` — open before
`read_state()`, close after `write_state_atomic()`.

Engine (3): `cmd_transition`, `cmd_init`, `cmd_reset`. For `transition`, open
before `_recover_engine_state_tmp` and close **after the outbox finalisation** —
past `_write_engine_state_atomic`, through `_append_events_jsonl` and the pending
unlink. Releasing at the write leaves this reachable: A writes pending, writes
engine-state, releases; B acquires, `_recover_pending` matches on
`to`/`seq`/`run_id` (`loop-engine.py:216-229`) and replays A's event; B refuses
`illegal transition`; A then appends its own record again → duplicate
`(spec, seq)` for the *same* spec, which the cross-spec deferral does not cover.

`_recover_pending` sits inside the section but is **not protected by it** — it
reads the repo-global outbox and calls `_recover_engine_state_tmp` on whatever
spec that record names, so it can reach *another* spec's engine-state while
holding only this spec's lock. A comment at the call site says so, and
`loop-outbox-cross-spec-rmw` owns it. Position is not protection.

## Tasks

### T1 — `statelock_core.py`

**Depends on:** none · **Mode:** TDD · `stub: true`
**Tests:** `packs/core/tests/skills/work-loop/test-statelock.py`, markers
`# STUB: AC<n>`. Cross-process mutual exclusion (AC5, subprocess children, not
threads); no residue on return and on raise (AC6); `StateLockError` not an
`OSError` and one base for every acquisition failure incl. `EACCES` via
`chmod 0o500` (AC7); dangling-symlink / directory / FIFO each fail in
**less than** `timeout` with `time.process_time()` delta under half the elapsed
wall time, so "no hot spin" is asserted rather than implied (AC8); concurrent
same-pid reclaimers yield one holder, reclaim refuses an unparseable file,
release keys on `(st_dev, st_ino)`, and a moved lockfile raises `StateLockLost`
(AC9); mode `0o600`, bounded record, failed token write fails closed, timeout
message names path and a *validated* pid — planted as a distinctive fake pid so
the assertion cannot pass on the caller's own (AC11); no mkdir (AC12).
**Approach:** write it per the LLD. Docstring names ADR-0074 and that it is the
projection source.

### T2 — The regressions

**Depends on:** none · **Mode:** TDD · `stub: true`
**Tests:** `test-loop-concurrency.py`, markers `# STUB: AC<n>`. AC17 asserting
against N; AC18 incl. loser message and no duplicate `(spec, seq)`; AC19 across
both scripts' `init` plus an `init`/`reset` pair; AC20 the arrival-spread check;
AC21 hermeticity from an import-time `{relpath: sha256}` baseline over
`.loop-run/**` and `.gitignore`; AC15/AC16 by planting a fresh lockfile before
invoking each verb and asserting non-zero plus an unchanged digest.
**Approach:** already written and red at PLAN. Remaining: replace the two
placeholder cases with the planted-lockfile stubs, and strengthen AC21's
baseline per above.

### T3 — Projection primitive

**Depends on:** T1 · **Mode:** TDD · `stub: true`
**Tests:** `packages/agentbundle/tests/unit/test_skill_libs.py` — projection
writes the target byte-identically; drift gate reports modified / missing /
orphaned; no-op when the source is absent; idempotent.
**Approach:** `build/skill_libs.py` per the LLD; wire both `self_host.py` sites.

### T4 — Wire `loop-cohort.py`

**Depends on:** T1, T2 · **Mode:** TDD (AC17, AC19 go green)
**Tests:** AC15/AC16 cases from T2. Note `test-loop-cohort.sh:426-436` is the
read-only `status` case and does **not** cover AC16.
**Approach:** load `_statelock` per the LLD; wrap the seven verbs; map every
`StateLockError` and `StateLockLost` onto `stop()`.

### T5 — Wire `loop-engine.py`, bound the under-lock subprocesses

**Depends on:** T1, T2 · **Mode:** TDD (AC18 goes green)
**Tests:** AC18; the AC10 AST budget test; `test_loop_engine_events_jsonl.py`
unchanged.
**Approach:** wrap `transition` through the outbox finalisation, plus
`init`/`reset`. Add `timeout=` at both subprocess sites. Comment the
`_recover_pending` caveat.

### T6 — Ignore lockfiles, here and for adopters

**Depends on:** T4, T5 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `git check-ignore -q` exits 0 for `state.json.lock`,
`engine-state.json.lock` and a `.lock.reclaim.<uuid>` name under
`docs/specs/foo/`; the same patterns are in `packs/core/seeds/.gitignore`;
`git status --short` is empty after a run leaving both residues. Confirm with
`git ls-files` after staging — a gitignore rule can silently fail to apply.

### T7 — Projection + CI wiring

**Depends on:** T6 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `make build-self` leaves `_statelock.py` byte-identical to the
package source across all three trees; `python3 tools/test-all.py`,
`python3 -m pytest packs/core/tests packages/agentbundle/tests -q`, and
`make build-check` pass. (`test-all` does not reach the pytest-collected suites
in AC22 — hence the explicit pytest run.)
**Approach:** register the two new suites in `test-loop-cohort.sh`; add
`docs.yml` triggers for `_statelock.py` under both `.claude/` and
`packs/core/.apm/` (`packs/**` covers only the latter) and the new test files.
Re-check `git status` after `build-self`; it overwrites projection-only edits.

### T8 — Ship-side

**Depends on:** T7 · **Mode:** Goal-based check · `no stub (mode)`
**Done when:** `lint-spec-status.py --root .` exits 0; the three version files
report the *same* bumped version (explicit equality check — `build-self` syncs
none of them); the changelog entry names the stale window and the `rm` recovery;
`grep` confirms `loop-cohort-state-rmw-unlocked` is gone and the four new slugs
present.

## Risks

| Risk | Mitigation |
|---|---|
| A concurrency test that passes against the unfixed tree | AC20's arrival-spread check, which already caught a 1 s guessed lead smearing children 495 ms apart. |
| Flaky timing in CI | Assert invariants, not windows. The rendezvous replaces the guessed lead, which also cut runtime 48 s → 15 s. |
| A slow-but-live holder reclaimed → two writers | AC10's machine-checked budget; AC9 makes the residual window fail-loud. |
| Suite pollutes the live repo | AC21, from an import-time baseline. |
| Hand-edit to the projected copy | AC4's drift gate; header on the generated file. |
| `agentbundle` carries two locks until the follow-up | ADR-0074 Consequences; hard `needs` edge on the backlog item. |
| Added CI wall-clock — measured **~46 s** warm (a cold-cache first run was 2:17), 52 barriered child launches across 17 `git init`s | Recorded here so a trial-count increase is measured against a true baseline. The earlier "~15 s" was the fail-fast path, before the cases passed. |

## Rollout

Ships in `core`. Adopters get `_statelock.py` with the pack on next
install/upgrade — no migration, no state-file change, no flag, and no runtime
dependency on `agentbundle` (the projected copy is committed and self-contained).
In-flight runs are unaffected: no schema key changes, and an older unlocked run
simply has no lockfile to contend for. Version bump is three files.
`agentbundle` is **not** released by this PR; its own migration is
`agentbundle-statelock-symlink-spin`.
