# Spec: loop-cohort-state-lock

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Source:** `workspace.toml [backlog].open` → `loop-cohort-state-rmw-unlocked`
- **Constrained by:** ADR-0074

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A person running the work-loop gets state that tells the truth when more than
one thing touches it at once. Today a supervisor and a hand-run verb, or two
agents in one workspace, silently overwrite each other: retry counters
undercount so a retry cap never fires, and the state machine admits a
transition it is specified to reject. Both processes exit 0. Nothing surfaces
the loss.

The files are written atomically but *decided upon* unguardedly. Every mutating
verb does `read → decide → mutate → write`, where only the final write is
atomic:

```
read_state()  →  validate / decide  →  mutate  →  write_state_atomic()
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
             unguarded: a concurrent verb's write lands in here and is lost
```

Success looks like: concurrent verbs either both take effect, or the loser is
told plainly why it did not. No silent loss, no state that disagrees with the
run.

Both defects were reproduced before this spec was written — 20/20 trials lost a
cohort increment, 10/10 trials admitted an illegal engine transition, with 10
duplicate `(spec, seq)` pairs in the durable audit log. Evidence and harness:
[`notes/reproduction.md`](notes/reproduction.md).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off before
proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Open the critical section **before** the read and close it **after** the
  write, so the decision is made against state that cannot change underneath
  it. Locking only `read → write` leaves every defect in this spec intact.
- Fail closed. Any failure to acquire the lock — contention, permission,
  read-only filesystem, a lock path that is not a regular file — ends the verb
  with a non-zero exit and the repo's standard `stop()` refusal. Never a
  traceback, never a silent unlocked write.
- Bound every wait. Every retry path in the acquire loop checks the deadline
  and sleeps; no path may loop without both.
- Keep the two projected copies in sync via `make build-self`; only ever edit
  `packs/core/.apm/`.

### Ask first

- Changing the `timeout` or `stale_after` defaults, or the bound on subprocess
  calls made while the lock is held. These three are a linked budget (AC7) —
  moving one without the others silently reintroduces the double-holder case.
- Locking any read-only verb (`status`, `check`, `identity`, `plan
  check-current`, `schedule check-current`). They are deliberately unlocked;
  see *Never do*.
- Adding a second lock scope (for example over the repo-global outbox).

### Never do

- **Never let a locked verb invoke another locked verb**, in-process or by
  subprocess. The design is deadlock-free today only because the engine holds
  its lock while shelling into cohort verbs that take no lock, and no cohort
  verb ever invokes the engine. This is a load-bearing invariant, not an
  accident.
- **Never add a third state file** or a new key to either existing schema.
  This change is about how the existing files are written, not what they hold.
- **Never widen the per-spec critical section to cover a repo-global
  resource.** A per-spec lock does not serialise cross-spec access; putting a
  repo-global operation under it gives false confidence. See the deferred
  `loop-outbox-cross-spec-rmw`.
- **Never reclaim a lock without making release ownership-checked.** A holder
  whose lock was reclaimed must not delete its successor's lockfile.
- **Never create a directory in order to take a lock.** The lock path derives
  from `spec-dir`, which `loop-cohort.py`'s resolver does not confine to the
  repo root.

## Acceptance criteria

Stated as observable outcomes. Mechanism lives in the plan's `## Design (LLD)`.

**The lock primitive**

- [ ] **AC1** — `packs/core/.apm/skills/work-loop/scripts/_statelock.py` exists,
      exports `exclusive(...)` and `StateLockTimeout`, and imports only the
      standard library. Verified by an `ast.parse` walk of `Import`/`ImportFrom`
      nodes — not a substring grep, which the module's own explanatory prose
      would trip.
- [ ] **AC2** — One code path on every platform: the module has no
      platform branch and no `fcntl` / `flock` / `msvcrt` import node.
- [ ] **AC3** — Mutual exclusion: with N contenders and one holder, exactly one
      holds at a time. No lockfile remains after the body returns **or after the
      body raises**.
- [ ] **AC4** — The lockfile is created with mode `0o600` and records the
      holder's pid; a contention timeout names both the lock path and the
      recorded holder pid, so a wedge is attributable.
- [ ] **AC5** — Bounded wait, no hot spin: with the lock path occupied by a
      **dangling symlink**, a **directory**, and a **FIFO**, `exclusive()`
      terminates within a small multiple of `timeout` in each case rather than
      spinning. This case is a confirmed live defect in the precedent
      (`notes/reproduction.md` Case C) and is the reason the port hardens
      rather than copies.
- [ ] **AC6** — Stale reclaim: N concurrent reclaimers of one stale lock yield
      exactly one holder.
- [ ] **AC7** — Reclaim cannot admit two writers. The linked budget holds:
      every subprocess invoked while the lock is held carries an explicit
      timeout, and `stale_after` exceeds the resulting provable maximum hold by
      a margin recorded in the plan. Release is ownership-checked — a holder
      whose lock was reclaimed does not unlink its successor's lockfile.
- [ ] **AC8** — `StateLockTimeout` does not derive from `OSError`, so no
      pre-existing broad `except OSError` handler in either script can swallow
      it into a fall-through.
- [ ] **AC9** — Taking the lock creates no directory. A verb given a
      nonexistent spec-dir refuses without creating anything on disk.

**The wiring**

- [ ] **AC10** — In `loop-cohort.py`, the five mutating verbs
      (`cmd_approve_plan`, `_schedule_run_impl`, `cmd_wave_advance`,
      `cmd_record_attempt`, `cmd_review_record`) plus `cmd_init` and
      `cmd_reset` decide and write inside one critical section.
- [ ] **AC11** — In `loop-engine.py`, `cmd_transition` holds the lock from
      `_recover_engine_state_tmp` through the outbox finalisation
      (`_append_events_jsonl` and the pending unlink) inclusive — not merely
      through `_write_engine_state_atomic`. Releasing at the write leaves a
      reachable same-spec duplicate-event interleaving. `loop-engine.py`'s own
      `cmd_init` and `cmd_reset` are locked on the same terms as AC10.
- [ ] **AC12** — `_recover_pending` runs inside the critical section but is
      **not** protected by it: it operates on the repo-global outbox, which a
      per-spec lock does not serialise. Recorded so the next reader does not
      mistake position for protection. Tracked as `loop-outbox-cross-spec-rmw`.
- [ ] **AC13** — Every one of the nine locked verbs, when the lock is already
      held, exits non-zero **and leaves its state file byte-identical**. A
      module-level timeout test does not satisfy this; the wiring is what is
      being verified.
- [ ] **AC14** — Locked verbs' no-op paths still do not write: `record-attempt`
      with a repeated `--cycle-id`, and `approve-plan` when already approved,
      each leave `state.json`'s digest unchanged.

**The regressions**

- [ ] **AC15** — N concurrent `record-attempt` calls in **separate OS
      processes** with distinct `--cycle-id` values yield
      `implementation_retry_count == N`, for N = 2 and N = 8, over 20 trials.
      Recorded as failing against the pre-fix tree in
      `notes/reproduction.md` Case A.
- [ ] **AC16** — Two concurrent identical `transition` calls in separate OS
      processes yield exactly one exit 0; the loser exits non-zero with
      `illegal transition`, **never** a lock timeout. The surviving
      `transition_sequence` is 1, and `.loop-run/events.jsonl` holds exactly one
      record for that spec — no duplicate `(spec, seq)` pair. Recorded as
      failing against the pre-fix tree in `notes/reproduction.md` Case B.
- [ ] **AC17** — N concurrent `init` calls yield exactly one exit 0 and N−1
      "already exists" refusals; a concurrent `init`/`reset` pair cannot leave a
      resurrected `state.json`.
- [ ] **AC18** — The concurrency tests are hermetic: they resolve their own
      repo root inside a temp tree, and the real repo's `.loop-run/` and
      `.gitignore` are unmodified by a full run.

**Not-a-regression, and the ship-side**

- [ ] **AC19** — Existing behavior is unchanged: `test-loop-cohort.py`,
      `test-loop-engine.py`, `test-loop-cohort.sh`, `test_loop_cohort_schedule.py`,
      `test_loop_engine_events_jsonl.py` and
      `test_loop_cohort_max_iter_single_source.py` all pass.
- [ ] **AC20** — Lockfiles and reclaim residue are ignored in **both** this
      repo's `.gitignore` and the shipped adopter seed
      `packs/core/seeds/.gitignore`, covering `*.json.lock` and
      `*.json.lock.reclaim.*`. `git status` is clean after a run that leaves
      both behind.
- [ ] **AC21** — The three projected copies of every touched script are
      byte-identical after `make build-self`, and `.github/workflows/docs.yml`
      path triggers cover the new module and the new test files.
- [ ] **AC22** — `docs/product/changelog.md` carries a user-facing entry;
      `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` and
      `.claude-plugin/marketplace.json` carry the version bump.
- [ ] **AC23** — `workspace.toml [backlog].open` no longer lists
      `loop-cohort-state-rmw-unlocked`, and lists
      `loop-outbox-cross-spec-rmw`, `append-knowledge-rmw-unlocked`,
      `agentbundle-statelock-symlink-spin` and
      `loop-cohort-resolve-spec-dir-confinement`, each with a
      cold-start-sufficient comment.

## Testing strategy

TDD for the lock module and the concurrency regressions — a mutual-exclusion
protocol is the compressible-invariant case the mode is for. Stub coverage per
task is recorded in the plan's `Tests:` subsections; T5–T8 are goal-based and
record `no stub (mode)`.

The regressions carry a trap worth stating in the contract: **a concurrency
test that spawns subprocesses without a post-startup barrier passes against the
unfixed tree** (measured: 0 lost updates in 5 trials of 20-way fan-out). Both
tests therefore use separate OS processes, load the target module first, spin to
a shared wall-clock instant, and only then call `main(argv)` — asserting exit
codes read from each child, never from a shared stream. Threads do not satisfy
this: they share `os.chdir`, the module-level `_lint_module` global, and
`sys.stdout`, and never exercise the cross-process contract the lock exists for.

Timing-sensitive assertions pin the **invariant** (no lost update; exactly one
holder), never a timing window or a transient filename.

## Assumptions

1. **`docs/specs/<feature>/` supports `O_CREAT | O_EXCL` create-exclusivity.**
   This *is* a new requirement, beyond the atomic `rename` the existing writer
   already needs — and `O_EXCL` is precisely the primitive NFSv2/v3 does not
   provide. On such a filesystem the lock degrades **silently** to today's
   behavior (no mutual exclusion) rather than failing loudly. Accepted: the
   loop's state directory is a working tree, not a network share.
2. **Staleness is judged on wall-clock `st_mtime`**, unlike the monotonic
   timeout, so it is exposed to NTP skew. The `stale_after` margin in AC7
   absorbs normal skew; ownership-checked release bounds the damage if it does
   not.
3. **Contention is rare and short.** The expected case is one holder and no
   contention: one `open` and one `unlink` per verb.
4. **`spec-dir` is operator-supplied, not attacker-supplied.** `loop-cohort.py`'s
   resolver rejects `..` but does not confine to the repo root the way
   `loop-engine.py`'s does. This spec does not close that gap — it declines to
   *widen* it, by adding no directory-creating primitive at that path (AC9).
   Closing it is tracked as `loop-cohort-resolve-spec-dir-confinement`.
