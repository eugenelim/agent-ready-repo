# Spec: loop-cohort-state-lock

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none
- **Constrained by:** ADR-0074

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A person running the work-loop gets state that tells the truth when more than
one thing touches it at once. Today a supervisor and a hand-run verb, or two
agents in one workspace, silently overwrite each other: retry counters
undercount so a retry cap never fires, the state machine admits a transition it
is specified to reject, and the durable audit log records the same sequence
number twice. Every caller exits 0. Nothing surfaces the loss.

The files are written atomically but *decided upon* unguardedly — only the final
write is atomic, and a concurrent verb's write lands inside the decide window
and is lost.

Success looks like: concurrent verbs either both take effect, or the loser is
told plainly why it did not — and a caller that cannot be sure its write landed
is told that too, rather than exiting 0.

Reproduced before this spec was written, at 20/20, 10/10 and 6/6 trials, with
the harness and transcripts in [`notes/reproduction.md`](notes/reproduction.md).
Every number and measurement quoted anywhere in this feature is canonical
**there**; the spec and plan reference it rather than restating it.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off before
proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Make the decision inside the critical section, not just the write. Locking
  only `read → write` leaves every defect in this spec intact.
- Fail closed on *any* inability to hold the lock — contention, permission,
  read-only filesystem, a lock path that is not a regular file, a failed token
  write. Non-zero exit, `stop()`-shaped message, no traceback, no unlocked
  write.
- Bound every wait: every retry path checks the deadline and sleeps.
- Author the lock once, in the package, and let the projection carry it. Never
  hand-edit a projected copy.

### Ask first

- Changing `timeout`, `stale_after`, or the bound on subprocess calls made while
  the lock is held. They are one linked budget (AC8); moving one alone
  reintroduces the double-holder case.
- Locking any verb the engine's guard table invokes while holding its own lock.
  Today that set is `check`, `identity`, `plan check-current`,
  `schedule check-current`, and `wave check` — they are unlocked *by
  construction*, which is what makes the design acyclic.
- Adding a second lock scope (for example over the repo-global outbox).

### Never do

- **Never let a locked verb invoke another locked verb**, in-process or by
  subprocess. The design is deadlock-free only because the engine holds its
  lock while shelling into cohort verbs that take no lock, and no cohort verb
  invokes the engine. Load-bearing, not incidental.
- **Never add a third state file** or a key to either existing schema.
- **Never widen the per-spec critical section to cover a repo-global
  resource.** A per-spec lock does not serialise cross-spec access; putting a
  repo-global operation under it manufactures false confidence.
- **Never delete a file the lock did not create.** The reclaim path must
  recognise a lockfile as its own kind before touching it.
- **Never create a directory in order to take a lock.** `loop-cohort.py`'s
  spec-dir resolver does not confine to the repo root.

## Acceptance criteria

Observable outcomes. Mechanism and technique live in the plan's `## Design (LLD)`
and each task's `Tests:`.

**One authored source (ADR-0074)**

- [ ] **AC1** — The lock is authored once, at
      `packages/agentbundle/agentbundle/statelock_core.py`, and imports only the
      standard library — no `agentbundle` import, so the projected copy is
      importable standalone.
- [ ] **AC2** — It behaves identically on every platform: no platform branch and
      no `fcntl` / `msvcrt` import.
- [ ] **AC3** — `packs/core/.apm/skills/work-loop/scripts/_statelock.py` is a
      byte-identical projection of that source, written by `make build-self`.
- [ ] **AC4** — `make build-check` fails when the projected copy is **modified**,
      **missing**, or **orphaned**, each message naming the source and the
      regeneration command. Projection is a documented no-op outside the
      monorepo; the committed copy is what adopters receive.

**The lock primitive**

- [ ] **AC5** — Mutual exclusion holds **across OS processes**: with N
      contenders, never two holders at once.
- [ ] **AC6** — No lockfile *created by this holder* remains after the body
      returns or after the body raises. (A lockfile that is no longer this
      holder's is deliberately left alone — AC9.)
- [ ] **AC7** — Every failure to acquire raises a `StateLockError`, which does
      **not** derive from `OSError`. One base for all of them — contention,
      `EACCES`, `EROFS`, a non-regular lock path — so no pre-existing broad
      `except OSError` can swallow one into a fall-through, and a caller can
      distinguish "retry later" from "this will never be acquirable".
      Acquisition never leaves a traceback.
- [ ] **AC8** — Bounded wait, no hot spin. With the lock path occupied by a
      **dangling symlink**, a **directory**, and a **FIFO**, acquisition fails
      in **less than `timeout`** in each case — it is unacquirable, not
      contended — and burns no measurable CPU spinning. This is a confirmed live
      defect in the precedent (`notes/reproduction.md` Case C).
- [ ] **AC9** — Reclaim and release cannot admit or mask a second writer:
      - N concurrent reclaimers of one stale lock yield exactly one holder,
        including when they share a pid.
      - Reclaim refuses a file at the lock path that does not parse as a
        lockfile this module wrote, so it deletes nothing it does not recognise.
      - Release identifies its own lockfile by `(st_dev, st_ino)` captured at
        acquire, not by content.
      - **If release finds its lockfile gone or foreign, the verb reports that
        it lost the lock mid-mutation, names the state file, and exits
        non-zero.** Ownership-checked release protects the successor's *file*;
        this criterion is what protects the *state*, and without it a reclaimed
        holder completes its write and exits 0 — the original defect, restored
        through the reclaim path.
- [ ] **AC10** — The linked budget is machine-checked, not asserted in prose:
      every subprocess reachable while the lock is held passes an explicit
      `timeout=`, and `stale_after` exceeds the resulting maximum hold, which in
      turn exceeds `timeout`. A test derives this from the source and fails when
      a new unbounded call is added under lock.
- [ ] **AC11** — The lockfile is mode `0o600`, holds a single bounded
      well-formed record, and the token write must succeed before the body is
      entered — on failure the lockfile is removed and the verb fails closed.
      A timeout message names the lock path and the holder pid, rendering the
      pid only if it parses as a pid, so lockfile bytes can never reach a
      terminal unvalidated.
- [ ] **AC12** — Acquiring the lock creates no directory; a verb given a
      nonexistent spec-dir refuses without creating anything.

**The wiring**

- [ ] **AC13** — Every code path that writes `state.json` or
      `engine-state.json` does so inside a critical section that also contains
      the read it decided from. Ten verbs today; the inventory is in the LLD.
- [ ] **AC14** — For `loop-engine.py`'s `transition`, the critical section
      extends through the outbox finalisation, not merely through the state
      write. Releasing at the write leaves a reachable same-spec
      duplicate-event interleaving.
- [ ] **AC15** — Every locked verb, when the lock cannot be acquired for **any**
      reason, exits non-zero and creates or modifies nothing on disk. Verified
      per verb, not by a module-level timeout test.
- [ ] **AC16** — Locked no-op paths still do not write: `record-attempt` with a
      repeated `--cycle-id`, and `approve-plan` when already approved, leave
      `state.json` byte-identical.

**The regressions** (each recorded failing pre-fix in `notes/reproduction.md`)

- [ ] **AC17** — N concurrent `record-attempt` calls in separate OS processes
      with distinct `--cycle-id` values: **all N exit 0 and
      `implementation_retry_count == N`.** Asserted against N, never against
      the number that happened to succeed. N = 2 over 20 trials, N = 8 over 5.
- [ ] **AC18** — Two concurrent identical `transition` calls: exactly one exits
      0; the loser exits non-zero with `illegal transition`, never a lock
      timeout. Surviving `transition_sequence` is 1, and `events.jsonl` holds
      exactly one record for that spec.
- [ ] **AC19** — N concurrent `init` calls: exactly one exits 0 and the rest
      refuse with `already exists` — a lock timeout does not satisfy this.
      Covers both scripts' `init`, and a concurrent `init`/`reset` pair cannot
      leave a resurrected state file.
- [ ] **AC20** — Every concurrency case proves its children actually raced,
      and fails loudly when they did not. A guessed barrier lead smears them
      apart (measured in `notes/reproduction.md`), which would turn every case
      into a silent false pass.
- [ ] **AC21** — The suite is hermetic: the live repo's `.loop-run/` **contents**
      and `.gitignore` are byte-identical before and after a full run, compared
      against a baseline taken at import — not mid-suite — since
      `loop-engine init` appends to `.gitignore`.

**Not-a-regression, and the ship-side**

- [ ] **AC22** — Existing behavior is unchanged: `test-loop-cohort.py`,
      `test-loop-engine.py`, `test-loop-cohort.sh`, and the pytest-collected
      `test_loop_cohort_schedule.py`, `test_loop_engine_events_jsonl.py`,
      `test_loop_cohort_max_iter_single_source.py` all pass.
- [ ] **AC23** — `.gitignore` and the shipped adopter seed
      `packs/core/seeds/.gitignore` both ignore the lockfile and its reclaim
      residue; `git status` is clean after a run that leaves both behind.
- [ ] **AC24** — The three projected copies of every touched skill script are
      byte-identical after `make build-self`, and `docs.yml` path triggers cover
      the new module and test files.
- [ ] **AC25** — `docs/product/changelog.md` carries a user-facing entry that
      names how to clear a stale lock and how long the stale window is;
      `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` and
      `.claude-plugin/marketplace.json` all carry the same bumped version.
- [ ] **AC26** — `workspace.toml [backlog].open` drops
      `loop-cohort-state-rmw-unlocked` and carries
      `agentbundle-statelock-symlink-spin`, `loop-outbox-cross-spec-rmw`,
      `append-knowledge-rmw-unlocked` and
      `loop-cohort-resolve-spec-dir-confinement`.

## Testing strategy

TDD for the lock and the regressions — a mutual-exclusion protocol is the
compressible-invariant case. Stub coverage is recorded per task in `plan.md`;
goal-based tasks record `no stub (mode)`.

Two properties of the harness are load-bearing, both learned by measurement
(`notes/reproduction.md`):

1. **Separate OS processes, never threads.** Threads share `os.chdir`, the
   module-level `_lint_module` global, and `sys.stdout`, so they cannot
   distinguish an `O_EXCL` lockfile from a process-local mutex and cannot
   support sound per-caller exit-code assertions. This applies to the lock's own
   mutual-exclusion and reclaim cases as much as to the verb-level regressions.
2. **A rendezvous, not a guessed lead.** Children announce readiness after their
   module loads, then wait on a go signal. Each records its post-barrier
   instant, and a case whose children did not arrive together fails (AC20).

Timing-sensitive assertions pin invariants — no lost update, exactly one holder,
CPU not burned — never a timing window or a transient filename.

## Assumptions

1. **`docs/specs/<feature>/` supports `O_CREAT | O_EXCL` create-exclusivity.**
   A genuinely new requirement beyond the atomic `rename` the existing writer
   needs, and exactly the primitive NFSv2/v3 lacks. There the lock degrades
   **silently** to today's behaviour. Accepted: the state directory is a working
   tree, not a network share.
2. **Staleness is judged on wall-clock `st_mtime`**, unlike the monotonic
   timeout, so it is exposed to NTP skew. AC10's margin absorbs normal skew;
   AC9's lost-lock report bounds the damage when it does not.
3. **Contention is rare and short** — one `open` and one `unlink` per verb in the
   uncontended case.
4. **`spec-dir` is operator-supplied, not attacker-supplied.**
   `loop-cohort.py`'s resolver rejects `..` but does not confine to the repo
   root the way `loop-engine.py`'s does. This change declines to *widen* that
   gap — no directory creation (AC12), no deletion of unrecognised files
   (AC9) — but does not close it. Tracked as
   `loop-cohort-resolve-spec-dir-confinement`.
