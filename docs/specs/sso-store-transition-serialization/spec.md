# Spec: sso-store-transition-serialization

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0035](../../rfc/0035-sso-cookie-auth-for-atlassian-pack.md) — owns the `sso-cookie` broker and its per-verb exit-code contract; [RFC-0013](../../rfc/0013-credential-broker-contract.md) — carries the exit-code errata RFC-0035 wrote against; [ADR-0026](../../adr/0026-sso-consumer-resolution-in-credbroker.md) — places consumer resolution in `credbroker`, fixing the engine→library dependency direction this spec must not invert.
- **Architecture:** [`docs/architecture/credentials.md § The `sso-cookie` broker`](../../architecture/credentials.md#the-sso-cookie-broker) — the engine/library split, the exit-code table, and the primary-store / materialisation-surface distinction live there. This spec does not restate them; it serialises the transition between them.
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

Mode: full (risk triggers: **security boundary** — credential material at rest, file I/O; **structural change** — a new concurrency primitive and a new engine-internal boundary; **unfamiliar** — cross-platform interprocess locking)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two engine invocations that touch one SSO profile at the same time never
corrupt, lose, or stale-serve its cookie jar. `sso-broker.py` serialises the
whole per-profile store transition behind one exclusive interprocess lock, and
serialises `get-cookies`' load-and-materialise behind the same lock. Under any
interleaving of concurrent invocations for a single profile, a reader observes
exactly one of: the jar stored before the concurrent writers ran, or the jar one
of them stored whole. Never a mix of two, never a jar assembled from slots
another writer reaped, and never a materialised file older than the last
completed store.

The unambiguously reachable race is **reader against writer** — a `get-cookies`
or `test` resolving a profile while a `refresh` re-captures it. That needs no
coordination to occur: an agent turn resolves cookies while a prior turn's
recapture is still committing. Writer-against-writer for one profile is also
covered, but two concurrent `refresh` calls additionally contend on Chromium's
singleton lock over the shared `browser-state/<profile>` directory, which is a
separate resource tracked as `sso-broker-register-concurrency` and out of scope
here.

Contention is a distinct, recoverable answer rather than a silent wait: a verb
that cannot take the lock inside its budget exits `6`, leaving the jar and the
profile TOML untouched, and `credbroker` raises a typed contended error the
caller can back off on. `register` and `refresh` are the exception to the
untouched-state guarantee, and structurally so: both drive Chromium against
`~/.agentbundle/browser-state/<profile>` before they reach the lock, so that
directory carries the browser's writes whatever the lock then answers. The lock
sits after the browser work deliberately — holding it across a 540 s capture
would starve every reader — and the accepted cost is that a contended capture
discards a sign-in that had already completed.

Every lock wait is bounded strictly below the `credbroker` timeout for the same
verb, so a lock never converts a bounded call into a hang. A holder that is
killed mid-transition releases the lock to the operating system; no profile is
left permanently unusable by a lock, and nothing in the engine breaks, reaps, or
ages out a lock to achieve that.

The guarantee is asserted for a local filesystem. Where the lock primitive
reports that the underlying filesystem cannot support it, the engine fails
loudly rather than proceeding unserialised.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Take the lock on a **dedicated lockfile** under `~/.agentbundle/sso-locks/`,
  never on the jar, the floor file, or the profile TOML. Windows byte-range
  locks are mandatory — they deny other processes read *and* write on the locked
  region — so locking a file the engine also reads turns serialisation into
  `EACCES`.
- Compose the lockfile path through the same two controls as every other
  profile-derived path: `_profile_component` for grammar, `_contained` for
  resolved-path containment.
- Acquire **non-blocking, then retry against a deadline the engine owns**.
  `fcntl.flock(LOCK_EX)` blocks unboundedly and `msvcrt.locking(LK_LOCK)` caps
  itself at ten one-second attempts; neither honours a caller's budget, so only
  a non-blocking acquire inside the engine's own loop is bounded on both.
- Ensure every caller of `_store_cookie_jar` holds the lock across the whole
  call, including its non-Tier-2 and single-credential paths, and across
  `get-cookies`' load and materialisation together. `_store_cookie_jar` itself
  does not acquire — it asserts it is held.
- Release the lock before any operation whose bound is set by something other
  than the store: the Chromium launch in `register` / `refresh`, and the 15 s
  validation request in `test`.
- Keep the engine stdlib-only: `fcntl` on POSIX, `msvcrt` on Windows, both
  imported conditionally.
- Carry `Engine-Change-RFC: RFC-0035` in every commit message touching
  `packs/credential-brokers/**` or `packages/agentbundle/agentbundle/`.
- Regenerate the drift-gated projected copies with
  `agentbundle catalogue self-host --root . --write` after editing the pack
  source, and verify the editable install resolves to this workspace first.

### Ask first

- Widening the lock to cover `register`'s or `refresh`'s browser launch. That
  is `sso-broker-register-concurrency`'s resource on a 540 s timescale; folding
  it in here starves the 30 s `get-cookies` waiter.
- Changing any lock-wait budget, or any `credbroker` verb timeout the budgets
  are derived from.
- Adding a lock to a verb not named in the Acceptance Criteria.
- Introducing a second lockfile per profile, or any lock ordering between two
  locks held at once.

### Never do

- **Never delete, truncate, or recreate a lockfile to recover from contention.**
  Unlinking a locked file lets one process hold a lock on the unlinked inode
  while another creates a fresh file and locks that — two simultaneous holders,
  which is the failure the lock exists to prevent. This holds for `rm` too: the
  lockfile survives profile deletion, which AC19 records as a known artifact.
- **Never implement a stale-lock reaper** — no PID files, no mtime heuristics,
  no lock breaking. Both platforms release on process termination; a reaper adds
  a way to break a lock a live process still holds.
- **Never acquire the lock while the same *thread* already holds one.** Thread,
  not process: `flock` is per-open-file-description, so a second acquisition on a
  new descriptor self-deadlocks until the budget expires — but a *different*
  thread in the same process must be allowed to contend normally, which is what
  makes the threaded reproduction harness exercise the real primitive. A
  process-scoped rule would produce the process-global guard AC15 rejects and
  would disable the test that matters.
- **Never let the engine import `credbroker`.** The dependency runs the other
  way and inverting it breaks the engine's stdlib-only contract.
- **Never add a third-party dependency, a new top-level directory, or a new
  module boundary outside `sso-broker.py` and `credbroker._sso`.**
- **Never let a lock failure become a silent unserialised success — no
  exceptions, `rm` included.** Contention exits `6`; an unusable lock path exits
  `3`. No verb proceeds to the store without the lock.
- **Consumer-side backoff on the contended error is out of scope.** `jira.py`
  is not modified by this spec; the follow-on is tracked as
  `sso-contended-consumer-backoff`.

## Testing Strategy

**Serialisation under forced interleaving: TDD, exercised by an integration
test.** This is the spec's central claim and it is a compressible invariant —
for any interleaving, the reader sees one whole jar. The harness parks a chosen
writer at a chosen write index inside a fake Tier-2 backend, runs writers on
threads, and asserts on what a subsequent reader gets. Threads are the right
surface rather than a shortcut: both `flock` and `msvcrt.locking` conflict
between two descriptors opened by one process, so a thread harness exercises
the real primitive. It is a unit-level driver of an integration-level property,
which is why the negative control below is not optional.

**Negative control on the serialisation tests: goal-based.** A permanent test
runs the same interleavings with the lock stubbed out and asserts corruption
*does* occur. A concurrency test that passes for the wrong reason is the
dominant failure mode here: without the lock, the three-writer case already
produces a clean fail-closed miss, so "the reader got no jar" is a *passing*
assertion against unfixed code. The negative control is what distinguishes the
two, and it stays in the suite rather than being a one-time observation.

**Interprocess reality: TDD, exercised by an integration test.** One test
spawns real `sso-broker.py` subprocesses rather than threads. Its coverage is
bounded by what a subprocess can reach: `_tier2_backend` binds at import time
from a platform sibling module with no injection seam, so on Linux the
subprocess exercises the **file-floor** transition — which is the Linux
production path and the surface AC4's materialisation race lives on. The
chunked-generation Tier-2 transition is thread-verified only; AC7 states that
limit rather than implying coverage it does not have.

**Bounded wait and the contended exit code: TDD.** A held lock plus an expired
budget is a pure input/output pair: exit `6`, a stderr line, and a measured
elapsed time. Asserted on measured elapsed, not on the constant.

**Classifying contention: TDD, and the one behaviour that must be observed on
Windows.** Which exception the acquire raises, and with which errno, decides
whether a verb exits `6` or `3` — and the two platforms disagree. POSIX raises
`BlockingIOError`; Windows raises a plain `OSError` carrying the same `EACCES`
that an unwritable directory produces. Every other claim in this spec is
verifiable on the author's machine; this one is not, which is why AC12 pins it
to a test that runs on the `windows-latest` runner rather than to reasoning
from documentation.

**Bounded hold: manual QA, and the only manual criterion here.** The wait bound
is only meaningful if the hold is short. AC10 measures the longest-held region —
`rm` on a multi-slot profile — against a fixed 2 s bar over twenty iterations.
It is manual because no runner in this repo's CI can execute it: macOS is the
only platform where the cost being bounded (`/usr/bin/security` spawns) exists
at all, and there is no macOS runner. Recorded in `manual-qa.md`, matching the
sibling `jira-check-sso-auto-login` spec's convention.

**Lock release after holder death: TDD, exercised by an integration test.** A
subprocess takes the lock and is killed; a second acquires it. POSIX is asserted
strictly; Windows asserts eventual acquisition within the retry budget, because
`LockFileEx` documents release as resource-dependent rather than immediate.

**Path confinement and error paths: TDD.** Same shape as the existing
`_cookie_floor_path` / `_profile_path` containment tests, plus assertions that
an unusable lock path exits `3` with no traceback on stderr.

**Windows execution coverage: goal-based.** The credbroker suite already runs on
`windows-latest` inside `agentbundle catalogue self-host --check --windows`; the
new concurrency module must be collected by that step rather than skipped.

**Projection drift: goal-based.** `agentbundle catalogue self-host --check
--root .` exits 0 after the pack source changes.

## Acceptance Criteria

### The serialisation property

- [ ] **AC1.** Two writers storing different jars for one profile, forced to
      interleave at every chunk index, leave the store holding exactly one of
      the two jars whole. A reader never observes a jar containing bytes from
      both.
- [ ] **AC2.** Three writers, with the third rotating and reaping a generation
      while the first is still staging under it, leave the store holding one
      writer's jar whole. A reader never observes an absent jar as a result of a
      concurrent transition.
- [ ] **AC3.** A reader running concurrently with a committing writer receives
      either the pre-transition jar or the post-transition jar, never `None`
      from a partially reaped generation.
- [ ] **AC4.** Two concurrent `get-cookies` calls for one profile leave the
      materialised file at `~/.agentbundle/sso-cookies/<profile>.jar` matching
      the jar the later-completing call read. A stale reader never overwrites a
      fresher materialisation. This holds on Linux, where the primary store and
      the materialisation surface are the same file.
- [ ] **AC5.** Every path that mutates a profile's stored jar runs under the
      lock: all three exit paths of `_store_cookie_jar` including the
      non-Tier-2 and single-credential ones, the `_fall_back_to_floor` route,
      `get-cookies`' load-plus-materialisation, `rm`'s existence check, purge,
      and profile-TOML unlink, and `register` / `refresh`'s profile-TOML write. No mutating path
      reaches the store unserialised.
- [ ] **AC6.** A permanent negative-control test runs the AC1, AC2, and AC4
      interleavings with the lock stubbed out and asserts that corruption *does*
      occur, proving the harness can detect the defect it guards against.
- [ ] **AC7.** A test drives two real `sso-broker.py` subprocesses, not threads,
      and shows the same single-whole-jar outcome for the file-floor transition.
      Its docstring names the coverage limit — the Tier-2 chunked-generation path
      is thread-verified only — so a later reader does not mistake the test's
      scope for the property's scope.

### Bounding and failure

- [ ] **AC8.** A verb that cannot take the lock within its budget exits `6`,
      writes a stderr line naming the profile and the budget, and leaves the jar
      and the profile TOML byte-identical to their pre-invocation state.
      `browser-state/<profile>` is explicitly **not** covered: `register` and
      `refresh` mutate it via `launch_persistent_context` before they reach the
      lock, so a test asserting it unchanged could only pass with Chromium
      stubbed inert. That residue is recorded in
      `docs/architecture/credentials.md` instead.
- [ ] **AC9.** Contention is bounded, and the bound is stated once per verb
      class. For `get-cookies`, `test`, and `rm`, which reach the lock
      immediately: measured elapsed from process start to exit `6` is under 15 s,
      strictly below the 30 s `_TIMEOUT_GET_COOKIES_S` bound that is the
      tightest `credbroker` caller timeout. For `refresh` and `register`, whose
      browser work precedes the lock and so cannot be measured from process
      start: measured elapsed from the first acquire attempt to exit `6` is at
      most `_LOCK_WAIT_BUDGET_S` plus 2 s. There is one budget constant; no
      verb gets a longer wait.
- [ ] **AC10.** The uncontended critical section is measured by hand on macOS
      for the verb that holds it longest — `rm` on a profile with at least four
      continuation slots, where `_delete_cookie_jar` runs `_purge_credential`
      per slot and each is up to four `/usr/bin/security` spawns. **Twenty
      consecutive iterations, every one under 2 s.** A single iteration at or
      above 2 s fails this criterion; the remedy is a separate decision, not an
      escape clause inside it. This is the spec's only manual-QA criterion and
      deliberately so: no CI runner can execute it — there is no macOS runner,
      Linux has no Tier-2 backend so `rm` spawns `security` zero times, and
      Windows reaches Credential Manager in-process through `ctypes`, a cost
      model the 2 s bar was not derived from. The run is recorded in
      [`manual-qa.md`](./manual-qa.md) with the machine, the OS version, and the
      twenty timings.
- [ ] **AC11.** A process killed with `SIGKILL` (POSIX) while holding the lock
      leaves the profile usable: a subsequent invocation acquires the lock and
      completes. The Windows `TerminateProcess` equivalent is asserted as
      eventual acquisition within the retry budget, and is `skipif`-guarded
      where the runner cannot drive it, with the skip stated here rather than
      discovered in a log. No lockfile is deleted, recreated, or aged out.
- [ ] **AC12.** Contention is classified by **which call raised and on
      `exc.errno`** — never by exception type. A refusal from the acquire call
      itself is contention and retries toward the budget, then exits `6`:
      `BlockingIOError` on POSIX, and on Windows an `OSError` whose `errno` is
      `EACCES` (or `EDEADLOCK`, which `_LK_NBLCK` cannot actually produce and is
      classified defensively rather than observed). Two traps make the
      type-based reading wrong in opposite directions, and both are pinned by
      test: `BlockingIOError` is a subclass of `OSError`, so a broad
      `except OSError` swallows POSIX contention; and CPython maps `EACCES` to
      `PermissionError`, so production raises that subclass from both
      `msvcrt.locking` and `os.open` while a naive stub raises a bare `OSError`.
      Classification therefore reads `exc.errno` and the raising call, never
      `isinstance`. Test stubs raise `PermissionError`, matching production.
- [ ] **AC13.** Everything that is not a contention refusal from the acquire
      call exits `3` with a one-line stderr message and no traceback: path
      composition failures, `os.open` failures (including its own `EACCES`, which
      is why the raising call and not the errno alone decides), the
      `RuntimeError` `Path.resolve()` raises for symlink loops on Python
      3.11–3.12, and a filesystem that refuses locking with `ENOLCK` /
      `EOPNOTSUPP` / `ENOSYS`. No path reaches the store unserialised — `rm`
      included. **That errno list is POSIX-only**, and the criterion says so:
      `msvcrt` never produces those names, so a Windows `%USERPROFILE%`
      redirected to SMB surfaces unsupported locking as the same `EACCES` that
      means contention. The Windows symptom is therefore a *permanent* exit `6`
      on every verb for every profile rather than a diagnosable exit `3`, which
      AC22 records in `credentials.md` because no engine-side check can
      distinguish it.
- [ ] **AC14.** `rm`'s exit-`3` message names the manual recourse. With no
      unserialised fallback, an operator whose lock environment is permanently
      unusable cannot revoke a stored corporate session through the tool, and
      that stderr line is the only place they learn the keychain service and
      account shape needed to remove it by hand.
- [ ] **AC15.** The held-set is keyed by **(thread identity, profile)**, not by
      thread alone, and backs two distinct queries. A nested acquire — the thread
      already holds a lock, this profile's or any other's, and attempts a second —
      raises a distinct engine-fault error mapping to exit `3`, never the
      contended error mapping to `6`; a deterministic programming defect must not be reported to callers
      as a transient condition they should retry. AC17's held-ness check asks the
      narrower question. Keying by thread alone would let a caller holding
      profile `a`'s lock satisfy the check while mutating profile `b`.
- [ ] **AC16.** Releasing the lock never replaces an in-flight exception, and
      never goes silent either. The unlock and close run in nested `finally`
      blocks that suppress their own *raising*, so `_store_cookie_jar`'s
      `StoreTransitionError` — the message naming which keychain keys still hold
      cookie bytes after a failed reap — reaches the operator intact. But an
      unlock reporting that the region was **not locked** is the one runtime
      signal that the acquire silently did not take and the whole critical
      section ran unserialised, so that case writes a one-line stderr
      diagnostic. Suppressing the raise must not suppress the evidence. The
      signal is **Windows-only** and the criterion says so: POSIX
      `flock(fd, LOCK_UN)` on an unlocked descriptor succeeds and has no way to
      report the condition, while `_locking` returns `EACCES` for "file already
      locked *or unlocked*". A test asserts the line is emitted and that the
      release still does not raise — an untested emit is one refactor from
      vanishing.
- [ ] **AC17.** `_store_cookie_jar` asserts the lock is held rather than
      trusting its callers, and asserts it for **this profile** — it raises
      unless `(current thread, profile)` is in the held-set of AC15. A test
      drives `_store_cookie_jar` unheld and asserts it raises, and a second test
      drives it while holding a *different* profile's lock and asserts it raises
      too. Without the profile in the key, the most likely wiring mistake in a
      four-site design — acquiring for one profile and storing another — passes
      silently, which is precisely what this criterion exists to stop.

### Confinement and platform

- [ ] **AC18.** The lockfile lives at `~/.agentbundle/sso-locks/<profile>.lock`,
      composed through `_profile_component` and `_contained`. A traversal-shaped
      profile raises `ProfileConfinementError` before the lockfile is opened.
- [ ] **AC19.** On POSIX the lock directory is created `0700` **and repaired to
      `0700` on every acquisition**, mirroring `_file_floor_write` — `mkdir` does
      not repair an existing directory, and a `0755` lock directory lists every
      SSO profile the user holds to any local reader. Lockfiles are `0600` and
      survive `rm`; that residue is recorded in
      `docs/architecture/credentials.md` as a known artifact, and on Windows the
      confidentiality of the profile-name list rests on `%USERPROFILE%` ACLs
      rather than on any control this spec adds.
- [ ] **AC20.** The new concurrency test module actually executes on
      `windows-latest`, inside the existing `credbroker suite (process-tree kill
      parity)` step that `agentbundle catalogue self-host --check --windows`
      already runs. "Not skipped" is asserted by a mechanism, not by reading a
      log: the module carries a Windows-path guard that **fails** rather than
      skips when the lock primitive is unavailable, and the contended-acquire
      case of AC12 is among the tests it runs. `self_host_windows.py` judges a
      step by return code alone, so a fully-skipped module would otherwise exit
      0 and read as coverage.
- [ ] **AC21.** `sso-broker.py` imports `fcntl` and `msvcrt` conditionally,
      `threading` and `errno` unconditionally, and adds no third-party import.
      `errno` is named because the engine does not import it today and every
      classification branch depends on it. The existing stdlib-purity assertions
      still pass — all four are in `sys.stdlib_module_names`, which is what
      `test_stdlib_purity.py` asserts against.
- [ ] **AC22.** `docs/architecture/credentials.md` states that `list-profiles`
      is deliberately unserialised and why — it is advisory display, and it sits
      outside `_GRAMMAR_GUARDED_VERBS` — so a later reader does not mistake it
      for a missed wiring site. It also states that the serialisation guarantee
      is asserted for a local filesystem, and it records **both** network-home
      failure shapes, because they are opposites and an operator needs to
      recognise either: on POSIX a lock silently ignored by CIFS or some NFS
      configurations degrades to the pre-lock behaviour undetected, reporting no
      error; on Windows a `%USERPROFILE%` redirected to SMB surfaces unsupported
      locking as the same `EACCES` that means contention, so every verb returns a
      *permanent* exit `6` on that machine forever. Neither is engine-detectable;
      this text is the only operator-facing explanation.

### Contract and governance

- [ ] **AC23.** Exit `6` is documented as *contended — recoverable* in every
      place the exit-code contract is stated: the table and the following
      "only the two recoverable rows" sentence in
      `docs/architecture/credentials.md`, the adopter-facing exception table and
      its matching sentence in
      `guides/credential-brokers/reference/credbroker-sso-api.md`,
      `sso-broker.py`'s module-docstring enumeration, and the `:raises`
      docstrings in `credbroker/_sso.py`.
- [ ] **AC24.** `credbroker._sso` maps exit `6` to a new typed contended error
      exported from `credbroker`, subclassing the base SSO error but neither the
      session-unavailable nor the broker-unavailable type. The mapping covers
      every verb that can reach the lock, `register` included.
      `packages/credbroker/pyproject.toml` is bumped to `0.6.0`, and the PyPI
      README, `packages/credbroker/CHANGELOG.md`, and `docs/product/changelog.md`
      are updated in the same PR.
- [ ] **AC25.** An Approver-signed erratum recording exit `6` lands in
      RFC-0035 § Errata and RFC-0013 § Errata in the implementing PR, matching
      how RFC-0035 recorded exits `4` and `5`.
- [ ] **AC26.** Every commit in the implementing PR that touches
      `packs/credential-brokers/**` carries `Engine-Change-RFC: RFC-0035`, and
      `tools/lint-catalogue-curation-guard.py --base origin/main` exits 0.
- [ ] **AC27.** `agentbundle catalogue self-host --check --root .` exits 0. Both
      projections match their sources: `sso-broker.py` under `.agentbundle/bin/`,
      and `credbroker/_sso.py` against
      `packs/credential-brokers/.apm/user-libs/credbroker/_sso.py`, which
      `packages/AGENTS.local.md` pins byte-identical. The `broker` fixture's
      `projected` parameterisation passes for every new test.
- [ ] **AC28.** `python3 .claude/skills/work-loop/scripts/lint-spec-status.py
      --root .` exits 0, with `sso-contended-consumer-backoff` resolving in
      `workspace.toml [backlog].open`.

## Assumptions

- Technical: the engine imports stdlib only and must stay so for `get-cookies`,
  so locking is `fcntl` / `msvcrt` (source:
  `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py:27-39`;
  `docs/architecture/credentials.md:285-293`)
- Technical: Python floor is 3.11 (source:
  `packages/credbroker/pyproject.toml:9`)
- Technical: POSIX `flock` is released by the kernel when its holder dies, so
  no permanent stale lock is reachable on POSIX (source: probe — a child took
  `LOCK_EX`, the parent got `BlockingIOError` while it lived and acquired
  immediately after `SIGKILL`)
- Technical: Windows releases locks on process termination, but the time to do
  so "depends upon available system resources" — release is eventual, so a
  Windows waiter can see transient contention from a dead holder (source:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex
  § Remarks)
- Technical: `msvcrt.locking(LK_LOCK)` retries at 1 s intervals for 10 attempts
  then raises `OSError`, a non-configurable ceiling; `LK_NBLCK` fails
  immediately. `fcntl.flock(LOCK_EX)` blocks unboundedly. Only a non-blocking
  acquire inside an engine-owned loop is bounded on both platforms (source:
  https://docs.python.org/3/library/msvcrt.html)
- Technical: Windows byte-range locks are mandatory — they deny other processes
  read and write on the locked region — while POSIX `flock` is advisory, so the
  lock must sit on a dedicated lockfile (source:
  https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex
  § Remarks)
- Technical: `flock` is advisory and its cross-host behaviour is
  filesystem-dependent; on SMB/CIFS and some NFS configurations it is emulated
  per-host or refused. A corporate laptop with a network-mounted `$HOME` is
  within this feature's target population, which is why AC13 requires a loud
  failure rather than a silent one (source: security review, 2026-08-07; the
  refusal errnos are asserted by test rather than assumed)
- Technical: wall-clock bounds are enforced library-side, not in the engine —
  `get-cookies` 30 s, `refresh` 180 s, `register` 540 s — and 30 s is the
  binding one. Every other statement of these numbers in this spec and in
  `plan.md` refers back to this entry (source:
  `packages/credbroker/credbroker/_sso.py:211-213`)
- Technical: on Linux `_tier2_backend` is `None` — the platform dispatch binds
  only on `darwin` and `win32` — so every Linux store takes the file-floor path
  above `_continuation_meta`. This is why AC5 covers the whole of
  `_store_cookie_jar` rather than the continuation branch alone (source:
  `sso-broker.py:78-98`)
- Technical: `_capture` writes the profile TOML and seeds the persistent browser
  profile *before* storing the jar, so a contended exit that fired at
  `_store_cookie_jar` alone would leave both mutated. This is why AC5 puts the
  acquisition in `_capture` around both (source: `sso-broker.py:936-971`)
- Technical: `_tier2_backend` binds at import time from a platform sibling with
  no env var, flag, or injection hook, so a subprocess test cannot supply a fake
  backend. AC7's coverage limit follows from this rather than from
  convenience (source: `sso-broker.py:78-98`)
- Technical: `BlockingIOError` is a subclass of `OSError` (probe:
  `python3 -c "print(issubclass(BlockingIOError, OSError))"` → `True`), so a
  broad `except OSError` around the acquire swallows POSIX contention and makes
  exit `6` unreachable. An earlier draft of this spec did exactly that; AC12 now
  classifies by which call raised and with which errno
- Technical: Windows `_locking` sets `EACCES` for "locking violation (file
  already locked or unlocked)" and `EDEADLOCK` only after `_LK_LOCK`/`_LK_RLCK`
  exhaust ten attempts, so a non-blocking Windows contention is an `OSError`
  with `EACCES` — not a `BlockingIOError`, and not distinguishable by errno from
  an unwritable directory's `os.open` failure (source:
  https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/locking
  § Return value)
- Technical: `_profile_component` enforces only `isinstance(profile, str)`; it
  does **not** enforce the profile grammar. An out-of-grammar legacy name
  therefore composes a valid lockfile path exactly as it composes a valid
  profile path, and any name that would fail containment already raises
  `ProfileConfinementError` at `_do_rm`'s `_profile_path` call before any lock
  code runs. An earlier draft granted `rm` an unserialised fallback on the
  premise that a legacy name could make the lockfile uncreatable; that premise
  is false and the fallback — the spec's only exception to fail-closed — was
  removed (source: `sso-broker.py:186-196`, `:700-704`, `:1307-1309`)
- Technical: `_capture` drives `launch_persistent_context` against
  `browser-state/<profile>` on the `persist=True` path — `register`'s default
  and every `refresh` — and `_seed_persistent_profile` does its own persistent
  launch on the `--ephemeral` path, both before the store. The directory is
  therefore already mutated whenever the lock is attempted, which is why AC8
  excludes it rather than promising it untouched (source:
  `sso-broker.py:884-895`, `:1013-1020`)
- Technical: the `_load_cli_module` + `_InMemoryBackend` + sandboxed-`HOME`
  fixture is the harness the parked-writer reproduction extends (source:
  `packages/credbroker/tests/unit/test_sso_broker_verbs.py:32-99`)
- Technical: the credbroker suite **already** runs on `windows-latest`, inside
  `agentbundle catalogue self-host --check --windows` rather than as a visible
  workflow step. An earlier draft of this spec asserted the opposite and
  proposed adding the job; that assumption was wrong and the AC is now scoped
  to the new module being collected there (source:
  `packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py:88-94`,
  reached from `.github/workflows/build-check-windows.yml:93`)
- Process: any changeset touching `packs/credential-brokers/**` must carry the
  literal `Engine-Change-RFC:` in a commit message or
  `tools/lint-catalogue-curation-guard.py --base origin/main` fails CI, even
  for whitespace-only changes (source: `packages/AGENTS.local.md:56`)
- Process: `sso-materialisation-ordering` stays in `workspace.toml
  [backlog].open` even though this spec closes it, because the frozen
  `jira-check-sso-auto-login` spec defers against that slug at `spec.md:368` and
  `lint-spec-status.py` invariant (iv) requires it to resolve. The register has
  no closed-item section; the entry is annotated instead (source:
  `docs/specs/jira-check-sso-auto-login/spec.md:368`; `workspace.toml:544`)
- Product: this spec absorbs the `sso-materialisation-ordering` work;
  `sso-broker-register-concurrency` stays separate because it guards Chromium's
  user-data dir on a 540 s timescale, and one lock spanning both would starve
  the 30 s `get-cookies` waiter (source: user confirmation 2026-08-07)
- Product: lock-budget exhaustion gets a new recoverable exit code `6` rather
  than reusing `3`, because `3` is documented non-recoverable and auto-recovery
  could never back off on it (source: user confirmation 2026-08-07)
- Product: a single exclusive lock, not a shared/exclusive split. Python's docs
  do not establish that `msvcrt`'s `LK_RLCK` is shared in the POSIX sense, and
  concurrent `get-cookies` for one profile is not the reachable case (source:
  user confirmation 2026-08-07)
- Process: the RFC-0035 / RFC-0013 erratum for exit `6` lands Approver-signed in
  the implementing PR rather than ahead of it, matching how RFC-0035 recorded
  exits `4` and `5` (source: user confirmation 2026-08-07)
