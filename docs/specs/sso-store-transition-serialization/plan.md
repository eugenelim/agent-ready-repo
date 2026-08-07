# Plan: sso-store-transition-serialization

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

One new engine-internal primitive, four acquisition sites plus one assumes-held
function, then the contract, docs, and projection work around them.

The primitive is a `_profile_lock(profile)` context manager in `sso-broker.py`:
a dedicated `0600` lockfile under `~/.agentbundle/sso-locks/`, a non-blocking
acquire (`fcntl.flock(LOCK_EX | LOCK_NB)` / `msvcrt.locking(LK_NBLCK)`), and a
retry loop against a `time.monotonic()` deadline the engine owns. It is built
and tested standalone in T1 before anything calls it, because every later task
depends on its bounding and failure behaviour being right.

The four acquisition sites are `_capture` (spanning `_write_profile` and the
store), `_do_get_cookies` (load plus materialisation), `_do_rm` (existence check,
purge, and TOML unlink), and `_do_test` (jar load only). `list-profiles` is
deliberately excluded. `_store_cookie_jar` is assumes-held and covered whole —
not just its continuation branch — as are `_fall_back_to_floor`,
`_load_cookie_jar`, and `_delete_cookie_jar`.

Two things make the wiring harder than it looks, and both were found by review
rather than by reading the happy path:

- **On Linux `_tier2_backend` is `None`**, so every store takes the file-floor
  path *above* `_continuation_meta`. Scoping the lock to the continuation branch
  would leave the entire Linux production path — and the CI platform —
  unserialised. The lock therefore covers `_store_cookie_jar` whole, from its
  caller.
- **`_capture` writes the profile TOML and seeds the browser profile before it
  stores the jar.** A lock taken only inside `_store_cookie_jar` would let a
  contended `refresh` return "failed" after already overwriting the
  destination-pinning anchor and writing a replayable session to disk. So
  `_capture` takes the lock once, after the browser work, and holds it across
  both the TOML write and the store.

Rather than wrapping `_store_cookie_jar` in an acquiring outer function, the
acquisition moves **up** into the four verb-level sites and `_store_cookie_jar`
becomes assumes-held like its helpers. An outer wrapper would have had exactly
one production caller before this change and *zero* after — `_capture` is its
only call site in the engine, and `_capture` now takes the lock itself — leaving
a wrapper that only the test suite executes and against which the whole
serialisation property would be asserted. Held-ness is then enforced rather than
conventional: `_store_cookie_jar` asserts against T1's `(thread, profile)`-keyed
held-set and raises unless its caller acquired *this profile's* lock, so a
forgotten wrap — or a wrap taken for the wrong profile — fails loudly instead of
silently working.

That still leaves the self-deadlock risk: `flock` is per-open-file-description,
so a second acquisition inside a held region blocks until the budget expires and
would surface as an intermittent stall rather than a test failure. T1 ships a
thread-local re-entrancy guard that raises a *distinct* fault type — mapped to
exit `3`, never the recoverable `6`, so a code defect is never reported to a
caller as something to retry.

The exception taxonomy is the subtlest part and the part most likely to be got
wrong twice. Contention is **not** an exception class: `BlockingIOError` is a
subclass of `OSError`, so catching `OSError` around the acquire swallows POSIX
contention entirely, and Windows signals contention with a plain `OSError`
carrying the same `EACCES` an unwritable directory yields from `os.open`.
Classification is therefore by *which call raised and with which errno* — the
acquire call raising `BlockingIOError` (POSIX) or `OSError(EACCES|EDEADLOCK)`
(Windows) is contention; everything else is a fault.

The testing story is the reproduction harness in T2: the existing
`_InMemoryBackend` grows a thread-safe store and a *park* hook that blocks a
nominated writer at a nominated write index until released. Writers run as
threads against one loaded module, which exercises the real primitive because
both platforms' locks conflict between two descriptors opened by one process.
Because the pre-lock code already fails *closed* in the three-writer case,
"the reader got no jar" is a passing assertion against unfixed code — so T2 also
ships the permanent negative control that stubs the lock out and asserts
corruption does occur.

## Constraints

- **[RFC-0035](../../rfc/0035-sso-cookie-auth-for-atlassian-pack.md)** owns the
  `sso-cookie` broker and its per-verb exit codes. Exit `6` is new, so the
  erratum is Approver-signed (T8) in the same PR — the pattern RFC-0035 used for
  exits `4` and `5`.
- **[RFC-0013](../../rfc/0013-credential-broker-contract.md)** carries the
  broker-contract errata RFC-0035 wrote against; the same entry lands there.
- **[ADR-0026](../../adr/0026-sso-consumer-resolution-in-credbroker.md)** fixes
  the dependency direction: `credbroker` subprocesses the engine, never the
  reverse. The lock lives entirely in the engine; `credbroker` only *maps* the
  new exit code.
- **`packages/AGENTS.local.md`** — the `Engine-Change-RFC:` commit marker, and
  the byte-identity pin between `packages/credbroker/credbroker/_sso.py` and
  `packs/credential-brokers/.apm/user-libs/credbroker/_sso.py`.
- **`docs/architecture/credentials.md`** — `get-cookies` is stdlib-only.
  `fcntl`, `msvcrt`, and `threading` are stdlib; nothing else is added.
- **Caller timeouts** are as recorded in the spec's Assumptions
  (`_sso.py:211-213`); this plan does not restate the numbers.

### On TDD stubs

`docs/CONVENTIONS.md`'s *Stub → EXECUTE handoff* requires each TDD task's
construction test to exist as a compiling red stub at PLAN. That rule belongs to
a **`--mode code`** run: this is a `--mode spec-plan` run whose terminal state is
`plan-locked`, so committing red stubs now would land failing tests on `main`
with no EXECUTE to green them. `new-spec` states the same carve-out directly —
stubs are generated later, in `work-loop` PLAN. Materialising the T1–T6 stubs is
therefore the **first obligation of the implementing run**, recorded here so it
is not rediscovered.

## Construction tests

**Integration tests:**
- `test_sso_store_concurrency.py::test_two_subprocess_writers_leave_one_whole_jar`
  — real `sso-broker.py` subprocesses, file-floor path (AC7).
- `test_sso_store_concurrency.py::test_killed_holder_releases_lock` — subprocess
  takes the lock, is killed, a second acquires (AC11).

**Manual verification:** one, and only one — AC10's critical-section timing,
run by hand on macOS and recorded in [`manual-qa.md`](./manual-qa.md) with the
machine, OS version, and twenty timings. No CI runner can execute it: there is
no macOS runner, Linux has no Tier-2 backend so `rm` spawns `security` zero
times, and Windows reaches Credential Manager in-process via `ctypes`. The
live-SSO path is unchanged by this spec and needs no manual pass.

## Design (LLD)

Shape is `service`, so the sub-sections below are interfaces & contracts, data &
schema, failure & resilience, and quality attributes, plus the load-bearing
decisions. `docs/architecture/reference.md` is absent, so the stack is taken
from the repo: CPython ≥ 3.11 stdlib, `pytest` for gates.

### Design decisions

- **Dedicated lockfile directory `~/.agentbundle/sso-locks/`, not the cookie
  floor.** Rejected: locking the jar or floor file — Windows byte-range locks
  are mandatory, so that converts serialisation into `EACCES` for readers.
  Rejected: lockfiles in `~/.agentbundle/sso-cookies/` — that directory is
  scanned for stale `.tmp` files. Traces to: AC18, AC19.
- **Non-blocking acquire plus an engine-owned deadline.** Rejected:
  `flock(LOCK_EX)` — unbounded. Rejected: `msvcrt.locking(LK_LOCK)` — caps at
  ten one-second attempts, neither configurable nor matched to a caller timeout.
  Traces to: AC9.
- **The lock covers the whole of `_store_cookie_jar`, not just its continuation
  branch.** Forced by the Linux `_tier2_backend is None` path, which routes every
  Linux store through the file-floor path above `_continuation_meta`. The
  acquisition itself sits in the caller. Traces to: AC5.
- **`_capture` holds one lock across `_write_profile` and the store.**
  `_store_cookie_jar` becomes assumes-held rather than gaining an acquiring
  wrapper — the wrapper would have had no production caller. Rejected: an
  `already_held: bool` parameter — a caller can pass it wrongly. Traces to:
  AC5, AC8.
- **Contention is classified by call site and errno, not by exception class.**
  `BlockingIOError` from the POSIX acquire, or `OSError(EACCES|EDEADLOCK)` from
  `msvcrt.locking` — those being the Windows C constant names; in Python reach
  the second via `_EDEADLK = getattr(errno, "EDEADLOCK", errno.EDEADLK)`, since
  `errno.EDEADLOCK` is absent on macOS — is `StoreContendedError` → exit `6`. Everything else —
  path composition, `os.open`, `ENOLCK`/`EOPNOTSUPP`/`ENOSYS`, a nested acquire —
  is `LockUnavailableError` → exit `3`. Rejected: catching `OSError` around the
  acquire, which an earlier draft specified — `BlockingIOError` subclasses
  `OSError`, so it would have made exit `6` unreachable on both platforms.
  Traces to: AC12, AC13, AC15.
- **`rm` fails closed like every other verb.** An earlier draft gave it an
  unserialised fallback so a grammar-exempt legacy profile stayed revocable;
  `_profile_component` turns out not to enforce the grammar at all, so the
  premise was false and the fallback would have opened an unserialised write
  path for transient `os.open` failures. Traces to: AC13.
- **A `(thread, profile)`-keyed held-set backing two distinct queries.** The
  thread component keeps the T2 harness contending on the real primitive across
  threads; the profile component is what makes AC17 a real check. AC15 asks *does
  this thread hold any lock* — if so a second acquire is a nested-acquire fault.
  AC17 asks *does this thread hold this profile's lock* — if not,
  `_store_cookie_jar` raises. Rejected: keying by `threading.get_ident()` alone,
  which an earlier draft specified — it satisfies AC17 for a caller holding
  profile `a` while storing profile `b`, the likeliest mistake in a four-site
  design. Rejected: a process-global guard — it would make the T2 harness raise
  instead of contend, disabling the test that matters. Traces to: AC15, AC17.
- **No stale-lock handling of any kind.** Both platforms release on process
  termination, so the retry loop absorbs Windows' eventual release. Rejected:
  PID files and mtime-based breaking — each adds a path to break a lock a live
  process still holds. Traces to: AC11.
- **A single exclusive lock, no shared mode.** Rejected: `LOCK_SH` for readers —
  Python's `msvcrt` docs do not establish `LK_RLCK` as shared in the POSIX
  sense. Recorded as an out-of-scope upgrade, not a gap.

### Interfaces & contracts

- **Engine, new exit code.** `6` = *contended*, recoverable, reachable from
  `get-cookies`, `test`, `rm`, `refresh`, and `register` — `register` included
  because `_capture` serves both capture verbs. Codes `0`/`2`/`3`/`4`/`5` keep
  their meanings. Traces to: AC8, AC23.
- **Library, new typed error.** `credbroker.SsoStoreContendedError`, subclassing
  `SsoError` directly so a bare `except SsoError` catches it but neither
  `SsoSessionUnavailableError` nor `SsoBrokerUnavailableError` does. Mapped in
  `load_sso_cookies`, `refresh_sso_session`, **and** `register_sso_session`.
  Additive: no existing signature changes. Traces to: AC24.
- **Internal.** `_profile_lock(profile, budget_s=_LOCK_WAIT_BUDGET_S)` — a
  `contextlib.contextmanager`. Not exported; the engine has no importable
  surface.

### Data & schema

One new artifact: `~/.agentbundle/sso-locks/<profile>.lock`, an empty file whose
content is never read or written — only its byte range `[0, 1)` is locked, so
there is no format to version. Directory `0700`, created and **repaired** on
every acquisition; file `0600` on POSIX. Files are created on demand and never
removed, including by `rm`: unlinking a locked file allows two simultaneous
holders. The residue is a per-profile empty file that outlives the profile,
documented in `credentials.md` (T8). Traces to: AC18, AC19.

### Failure, edge cases & resilience

| Condition | Response | AC |
|---|---|---|
| Lock held past budget | exit `6`, stderr names profile + budget; jar and TOML untouched (`browser-state/` is already written by the browser — AC8 excludes it) | AC8 |
| Second acquire while this thread holds any lock | `LockUnavailableError` → exit `3`, immediate | AC15 |
| Lock dir unwritable, path uncomposable, symlink loop | `(OSError, RuntimeError)` → exit `3`, one line, no traceback | AC13 |
| Filesystem refuses locking (`ENOLCK`/`EOPNOTSUPP`/`ENOSYS`) | exit `3` — never a silent unserialised success | AC13 |
| `rm` genuinely contended | exit `6` | AC8, AC12 |
| Holder killed, POSIX | kernel releases; next acquire succeeds immediately | AC11 |
| Holder killed, Windows | release is resource-dependent; the retry loop absorbs it, worst case exit `6` and the caller retries | AC11 |
| Backend refuses mid-transition | unchanged — `_fall_back_to_floor` runs inside the held lock | AC5 |
| Windows `%USERPROFILE%` on SMB | unsupported locking is indistinguishable from contention (`EACCES`), so the symptom is a *permanent* exit `6`; documented, not detected | AC13, AC22 |
| Unlock reports region was not locked | suppress the raise, but write a stderr diagnostic — it is the only sign the acquire never took | AC16 |
| `_store_cookie_jar` called unheld, or held for a different profile | engine-fault error, immediate | AC17 |

### Quality attributes (NFRs)

- **Bounded wait.** `_LOCK_WAIT_BUDGET_S = 10.0`, uniform across verbs because
  the critical section is uniformly short. It leaves headroom under the tightest
  caller timeout recorded in the spec's Assumptions. Tests assert on measured
  elapsed, not on the constant, so raising the constant past the bound fails the
  gate.
- **Bounded hold — measured against a bar that can fail.** The macOS Tier-2
  backend shells out to `/usr/bin/security` with no `timeout=`, and `rm`'s
  `_delete_cookie_jar` runs `_purge_credential` per slot at up to four spawns
  each — the longest held region in the change, longer than the store's one
  write per slot. AC10 measures exactly that, on a profile with at least four
  slots — twenty consecutive iterations, each under 2 s. One iteration at or
  above 2 s **fails**;
  it does not silently divert into a remedy. Adding `timeout=` to the `security`
  calls is a real behaviour change to a projected file
  (`_sso_keychain_macos.py`) that would turn "the operator is typing their
  keychain password" into a store failure — so it is **out of scope here** and
  recorded as `sso-keychain-call-timeouts` if the bar is missed.
- **No contention cost.** Retry backoff starts at 25 ms and doubles to a 100 ms
  ceiling, jittered via `secrets.randbelow`. This is not a bandit-driven choice
  — B311 is issue-severity LOW and the repo's gate runs at
  `--severity-level medium`, so `random` would not be flagged. `secrets` is
  simply already imported and a jittered lock backoff is not security-sensitive
  either way.
- **Security posture.** The lockfile carries no credential material and is never
  read, so it adds no at-rest surface. It adds one predictable path per profile
  under the user's home; a same-principal process could hold it to deny service,
  which the accepted threat profile concedes for every artifact in
  `~/.agentbundle/`.

### Dependencies & integration

No new external dependency. Four stdlib additions: `fcntl` (POSIX) and `msvcrt`
(Windows), imported conditionally at module scope guarded by `os.name`, plus
`threading` and **`errno`** unconditionally. `errno` is easy to miss —
`sso-broker.py` does not import it today, and the classifier and every stub
reference `errno.EACCES` / `_EDEADLK` / `errno.ENOLCK` / `errno.EOPNOTSUPP` /
`errno.ENOSYS`, so omitting it is a `NameError` on the first contended acquire.
All four are in `sys.stdlib_module_names`, which is what `test_stdlib_purity.py`
asserts against, so AC21 is unaffected. The `credbroker` → engine subprocess
direction is unchanged.

## Tasks

### T1: The lock primitive is bounded, confined, and fails loudly

**Depends on:** none

**Touches:** packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/credbroker/tests/unit/test_sso_broker_verbs.py

**Tests:** (TDD; stubs materialised at the implementing run's PLAN, per *On TDD stubs*)

Exception *types* are asserted here; the *exit codes* they map to are asserted
in T5, which adds the `main` handlers. Splitting them this way keeps T1
buildable in its own wave.

- `_sso_lock_path("../etc/passwd")` raises `ProfileConfinementError` before the
  lockfile is opened — AC18.
- The lock directory is created `0700`; pre-created `0755`, it is narrowed on
  the next acquisition; the lockfile is `0600` — AC19.
- With the lock held by another thread, `_profile_lock(p, budget_s=0.5)` raises
  `StoreContendedError`, and measured elapsed is at least the budget — AC9.
- A POSIX acquire refused with `BlockingIOError` raises `StoreContendedError`,
  **not** `LockUnavailableError` — the regression test for the
  `BlockingIOError`-subclasses-`OSError` trap — AC12.
- An acquire stubbed to raise `PermissionError(errno.EACCES, ...)` and
  `OSError(_EDEADLK, ...)` from `msvcrt.locking` raises `StoreContendedError`;
  the same errno from `os.open` raises `LockUnavailableError`.
  **Two things are load-bearing here, both probed on this machine.** The
  two-argument form: `OSError(13).errno` is `None`, so a single-argument stub
  routes a *correct* `exc.errno` classifier to the fault branch and invites an
  `isinstance` "fix" that diverges from production. And the constant name:
  `errno.EDEADLOCK` **does not exist on macOS** — BSD headers omit it, glibc
  aliases it, MSVC defines it — so referencing it raises `AttributeError` on the
  platform this task's Done-when requires. Define
  `_EDEADLK = getattr(errno, "EDEADLOCK", errno.EDEADLK)` once and use it in both
  the stub and the classifier. CPython auto-promotes
  `OSError(errno.EACCES, ...)` to `PermissionError`, which is what production
  raises; the deadlock errno stays a bare `OSError` because PEP 3151 leaves
  `EDEADLK` unmapped. The assertion reads `exc.errno`, never the class — AC12,
  AC13.
- A lock call stubbed to raise `OSError(errno.ENOLCK, "no locks available")`,
  `OSError(errno.EOPNOTSUPP, ...)`, and `OSError(errno.ENOSYS, ...)` — all three
  errnos AC13 names, not just the first — and a `Path.resolve()` stubbed to
  raise `RuntimeError`, each raise `LockUnavailableError`. Two-argument form for
  the same reason as above: `OSError(errno.ENOLCK).errno` is `None`, so a
  single-argument stub passes by falling through to the fault default and stays
  green against an implementation that wrongly classified `ENOLCK` as
  contention — AC13.
- A same-thread nested acquire raises `LockUnavailableError` in under 100 ms —
  both for the *same* profile and for a *different* one, since AC15's rule is
  any-lock-held; a different-thread acquire contends normally, proving the guard
  does not neuter the T2 harness — AC15.
- An unlock stubbed to raise does not replace an in-flight
  `StoreTransitionError` — AC16.
- A `LK_UNLCK` stubbed to report the region was already unlocked writes the
  one-line stderr diagnostic and does **not** raise. Windows-only: POSIX
  `flock(fd, LOCK_UN)` on an unlocked descriptor succeeds and cannot report the
  condition, so there is no POSIX arm to assert — AC16.
- Source assertions: no `fcntl.flock` call omits `LOCK_NB`; no `msvcrt.locking`
  call uses `LK_LOCK`/`LK_RLCK`; the only descriptor passed to either originates
  from `_sso_lock_path` — AC5, AC21.
- The existing stdlib-purity assertions still pass — AC21.

**Approach:**
- Add the imports first: `errno` and `threading` unconditionally, `fcntl` /
  `msvcrt` guarded by `os.name`. `errno` is not currently imported by
  `sso-broker.py` and every classifier branch needs it.
- Add `_SSO_LOCK_DIR` beside the existing store-directory constants at
  `sso-broker.py:114-116`, and `_sso_lock_path` mirroring `_cookie_floor_path`
  (`:630`).
- Add `StoreContendedError` and `LockUnavailableError` beside
  `StoreTransitionError` (`:312`).
- Add `_profile_lock`: `mkdir(0700)` plus POSIX `chmod(0700)` repair, open
  `O_CREAT|O_RDWR` mode `0600`, non-blocking acquire looped against a
  `time.monotonic()` deadline with `secrets.randbelow` jitter.
- **Classify at the acquire call, not around the block.** Wrap only the acquire
  in its own `try`: `BlockingIOError` → contention; `OSError` whose `errno` is
  `EACCES` or `_EDEADLK` on Windows → contention; every other `OSError` there, and
  everything raised by path composition or `os.open`, → `LockUnavailableError`.
  Do **not** wrap the whole body in `except (OSError, RuntimeError)` —
  `BlockingIOError` subclasses `OSError` and would be swallowed.
- Open the lockfile inside a `try` whose `finally` closes the descriptor, so an
  acquire that fails after a successful `os.open` does not leak an fd.
- The descriptor is at offset 0 when `msvcrt.locking` is called — it locks from
  the *current file position*, and `O_CREAT|O_RDWR` happens to leave it there.
  The invariant is load-bearing, so assert it rather than relying on the default.
- Release in nested `finally` blocks that suppress their own *raising*, so the
  unlock cannot replace an in-flight exception — but write a one-line stderr
  diagnostic when the unlock reports the region was not locked.
- Add the held-set keyed by `(threading.get_ident(), profile)`, exposing the two
  queries AC15 and AC17 ask separately — any-lock-held, and this-profile-held.
- Extend the `broker` fixture to point `_SSO_LOCK_DIR` under the sandboxed home.

**Done when:** T1 tests green on macOS and Linux; `make lint-ruff` clean.

### T2: Concurrent writers to one profile leave exactly one whole jar

**Depends on:** T1

**Touches:** packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/credbroker/tests/unit/test_sso_store_concurrency.py

**Tests:** (TDD)
- Two writers storing distinct jars, parked to interleave at every chunk index
  in turn, leave exactly one jar whole, byte-for-byte, with no bytes of the
  other — AC1.
- Three writers, the third forced to commit and reap while the first is still
  staging, leave one jar whole; the reader never gets `None` — AC2.
- The same two interleavings **with `_tier2_backend` set to `None`**, exercising
  the file-floor path that is the whole of Linux production — AC5.
- Permanent negative control for the AC1 and AC2 interleavings, with
  `_profile_lock` stubbed to `contextlib.nullcontext`, asserting corruption
  *does* result — AC6. (The AC4 negative control lives in T3, which owns the
  `get-cookies` lock it stubs out.)
- A backend refusal mid-transition routes through `_fall_back_to_floor` with the
  lock held; a concurrent writer observes the completed fallback — AC5.
- **At least one writer case drives `_capture`**, not `_store_cookie_jar`
  directly, so the harness and production share an entry point and a later
  change to `_capture`'s lock scope cannot leave these tests green — AC5.
- `_store_cookie_jar` called without the lock raises, **and** called while
  holding a *different* profile's lock raises. Without the second arm a
  thread-only held-set passes every listed test — AC17.

**Approach:**
- Add `test_sso_store_concurrency.py` reusing `_load_cli_module` and the
  `broker` fixture shape (`test_sso_broker_verbs.py:32-99`).
- Extend the in-memory backend: a `threading.Lock` around `self.store`, and
  `park_at(thread_ident, write_index, event)`.
- Make `_store_cookie_jar` (`:432`) **assumes-held** — no acquiring wrapper; the
  four verb-level sites acquire. It asserts held-ness against T1's
  `(thread, profile)`-keyed held-set and raises `LockUnavailableError` unless its
  caller holds *this profile's* lock, so a forgotten wrap — or one taken for the
  wrong profile — fails loudly rather than silently working. Add assumes-held
  docstring lines to it and to `_fall_back_to_floor`, `_load_cookie_jar`, and
  `_delete_cookie_jar`.
- Update the ~39 existing `_store_cookie_jar` call sites in
  `test_sso_broker_verbs.py` to acquire around the call.

**Done when:** AC1, AC2, AC5, AC6, AC17 tests green; the negative control observes
corruption without the lock; the red output of AC1/AC2 against a lock-stubbed
build is captured for the PR description.

### T3: Concurrent readers never see a torn jar or a stale materialisation

**Depends on:** T1

**Touches:** packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/credbroker/tests/unit/test_sso_store_concurrency.py

**Tests:** (TDD)
- A reader parked mid-reassembly while a writer commits and reaps returns the
  pre- or post-transition jar, never `None` — AC3.
- Two `get-cookies` calls parked to interleave leave the materialised file
  matching the later-completing call's jar; a stale reader never wins the
  `os.replace` — AC4.
- Permanent negative control: the AC4 interleaving with `_profile_lock` stubbed
  to `contextlib.nullcontext` asserts the stale reader *does* win — AC6.

**Approach:**
- Wrap `_do_get_cookies` from the `_load_cookie_jar` call (`:1081`) through
  `_file_floor_write` (`:1100`) in one `with _profile_lock(profile):`. The
  profile-TOML read above stays outside.
- Update `_file_floor_write`'s docstring (`:648-658`), which currently states
  that ordering between concurrent materialisers is deliberately unspecified —
  it is now specified.

**Done when:** AC3, AC4 tests green; the AC4 negative control observes the stale
overwrite without the lock.

### T4: Capture, rm, and test serialise without holding across slow regions

**Depends on:** T1, T2

**Touches:** packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/credbroker/tests/unit/test_sso_store_concurrency.py

**Tests:** (TDD)
- A contended `refresh` leaves `sso-profiles/<profile>.toml` byte-identical and
  the jar untouched — AC8. `browser-state/<profile>` is **not** asserted:
  `launch_persistent_context` has already written it before the lock is
  attempted, so an "unchanged" assertion could only pass with Chromium stubbed
  inert. The test comment says so, and the residue is documented by T8.
- `rm` concurrent with a writer leaves the store either fully purged or holding
  the writer's whole jar, never a header without slots, and never a jar whose
  profile TOML has been unlinked — AC5.
- `rm` racing a first `register` does not report "not registered" and exit `0`
  while the capture then stores a jar — the check-then-act gap the existence
  check moving inside the lock closes — AC5.
- `rm` that cannot take the lock exits `6` on contention and `3` on any other
  lock failure. There is no unserialised fallback — AC13.
- Structural: no `_profile_lock` scope encloses `_capture`'s
  `with sync_playwright()` block or `_do_test`'s `urlopen` — AC5.
- A second process acquires the lock while a `test` is inside its validation
  request — AC5.

**Approach:**
- In `_capture` (`:936-971`), take `_profile_lock` after
  `_seed_persistent_profile` returns, spanning `_write_profile` (`:959`) and the
  `_store_cookie_jar` call (`:971`). This crosses no browser launch.
- In `_do_rm`, take the lock **after** `_profile_path` composes at `:1308` and
  **before** `path.exists()` at `:1309` — not just around `_delete_cookie_jar`
  and the unlink at `:1314-1315`. Checking `path.exists()` outside the lock is
  check-then-act: an `rm` racing a first `register` reads "not registered",
  prints that, and exits `0` while the capture then stores a jar. The ordering
  is deliberate: composing first preserves the property the retired-fallback
  Assumption rests on — a containment failure raises `ProfileConfinementError`
  before any lock code runs.
- In `_do_test`, wrap the `_load_cookie_jar` call (`:1141`) only; the `urlopen`
  (`:1171`) stays outside.

**Done when:** AC5, AC8, AC13 tests green.

### T5: A contended verb exits 6 within its budget, and the hold is bounded

**Depends on:** T1, T2, T3, T4

**Touches:** packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/credbroker/tests/unit/test_sso_broker_verbs.py, packages/credbroker/tests/unit/test_sso_store_concurrency.py

**Tests:** (TDD + goal-based, plus AC10's manual-QA record)

This task owns every *exit-code* assertion; T1 owns the exception types that
feed them.

- With the lock held, each of `get-cookies`, `refresh`, `test`, `rm`, `register`
  exits `6` with a stderr line naming the profile and the budget — AC8.
- **A contended acquire yields `6`, not `3`** — the end-to-end form of T1's
  `BlockingIOError` regression test, and the case that must run on
  `windows-latest` where `EACCES` rather than `BlockingIOError` signals
  contention. This case lives in `test_sso_store_concurrency.py`, not
  `test_sso_broker_verbs.py`, so it sits behind the same module-level Windows
  fail-not-skip guard AC20 requires — AC12, AC20.
- A read-only lock directory, and a lock stubbed to raise
  `OSError(errno.ENOLCK, "no locks available")`, each exit `3` with no
  `Traceback` on stderr. Two-argument form — a single-argument stub carries no
  `errno` and would pass by the fault default rather than by classification —
  AC13.
- `get-cookies`, `test`, and `rm`: elapsed from process start to exit `6` is
  under 15 s. `refresh` and `register`: elapsed from first acquire attempt is at
  most `_LOCK_WAIT_BUDGET_S` plus 2 s — AC9.
- AC10 is **manual QA, not a test in this block**: run `rm` by hand on macOS
  against a profile with at least four continuation slots, twenty consecutive
  times, and record every timing plus the machine and OS version in
  `manual-qa.md`. Each iteration must come in under 2 s. Do not write it as an
  automated test — on Linux `rm` spawns `security` zero times and on Windows
  Credential Manager is in-process, so an automated run passes green without
  ever exercising the cost the bar was derived from.

**Approach:**
- Add `except StoreContendedError` → `6` and `except LockUnavailableError` → `3`
  to `main`'s verb-dispatch `try` (`:1399-1421`), beside the existing
  `ProfileConfinementError` and `StoreTransitionError` handlers.
- Emit the stderr wording from the handlers so it is single-sourced. `rm`'s
  `LockUnavailableError` message additionally names the keychain service and
  account shape, so an operator with a permanently unusable lock environment can
  still remove a stored session by hand — AC14.
- Write the hand-run timing recipe into `manual-qa.md` alongside the readings —
  a recipe a second person can repeat, not a harness. If the 2 s bar is missed, that is a
  **failure to surface**, not a licence to add timeouts to
  `_sso_keychain_macos.py` — record `sso-keychain-call-timeouts` in
  `[backlog].open` and raise it as a decision.

**Done when:** AC8, AC9, AC12, AC13, AC14 tests green; AC10's twenty-iteration
macOS timing recorded in `manual-qa.md`.

### T6: `credbroker` raises a typed contended error on exit 6

**Depends on:** T5

**Touches:** packages/credbroker/credbroker/_sso.py, packs/credential-brokers/.apm/user-libs/credbroker/_sso.py, packages/credbroker/credbroker/__init__.py, packages/credbroker/pyproject.toml, packages/credbroker/CHANGELOG.md, docs/product/changelog.md, packages/credbroker/tests/unit/test_sso_recapture.py

**Tests:** (TDD)
- A stubbed engine exiting `6` makes `load_sso_cookies`, `refresh_sso_session`,
  and `register_sso_session` each raise `SsoStoreContendedError` — AC24.
- The new type is caught by `except SsoError` but by neither
  `SsoSessionUnavailableError` nor `SsoBrokerUnavailableError` — AC24.
- `credbroker.__all__` exports it; existing exports unchanged — AC24.

**Approach:**
- Add the class in `_sso.py` beside the error hierarchy (`:75-138`), subclassing
  `SsoError`. Export from `_sso.__all__` (`:48`) and `credbroker.__all__`
  (`__init__.py:80`).
- Map exit `6` in all three call sites, including `register_sso_session`
  (`:568-577`), which currently collapses every non-zero code to
  `SsoRecaptureFailedError`.
- Bump to `0.6.0`; update the PyPI README, both changelogs.
- Apply the identical edit to the byte-identical user-lib copy.

**Done when:** AC24 tests green; `python3 -m pytest packages/credbroker -q` clean.

### T7: The lock holds across a real process boundary

**Depends on:** T2, T3

**Touches:** packages/credbroker/tests/unit/test_sso_store_concurrency.py

**Tests:** (integration)
- Two real `sso-broker.py` subprocesses storing distinct jars leave one whole
  jar on the file-floor path — AC7.
- A subprocess killed while holding the lock leaves the profile usable — AC11.
  POSIX asserts immediate reacquisition after `SIGKILL`; Windows asserts
  eventual reacquisition within the retry budget.

**Approach:**
- Drive `subprocess.Popen` against the pack-source engine with a sandboxed
  `HOME`. Coordinate the park via a sentinel file the child polls.
- Assert the file-floor path only. `_tier2_backend` binds at import from a
  platform sibling with no injection seam, so a subprocess cannot be given a
  fake backend; the test docstring records that the Tier-2 chunked path is
  thread-verified in T2, not process-verified here.
- This module is collected by the Windows credbroker step, so the kill case
  needs a Windows arm or an explicit `skipif` — not an incidental skip. Use
  `TerminateProcess` semantics via `Popen.kill()` there; if the runner cannot
  drive it, `skipif` with a reason string, which AC11 already states.

**Done when:** AC7 and AC11 green on macOS and Linux, and on `windows-latest`
either green or explicitly `skipif`-ed with the reason recorded in AC11.

### T8: The exit-code contract is swept and its errata recorded

**Depends on:** T5, T6

**Touches:** docs/architecture/credentials.md, guides/credential-brokers/reference/credbroker-sso-api.md, packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py, packages/credbroker/credbroker/_sso.py, docs/rfc/0035-sso-cookie-auth-for-atlassian-pack.md, docs/rfc/0013-credential-broker-contract.md

**Tests:** (goal-based)
- Every stated location of the exit-code contract carries `6`: the table and the
  "only the two recoverable rows" sentence in `credentials.md:305-313`; the
  adopter-facing table and matching sentence in `credbroker-sso-api.md:105-117`;
  `sso-broker.py:14-16`'s docstring enumeration; the `:raises` docstrings at
  `_sso.py:490-492` and `:545-547` — AC23.
- `credentials.md` records the `list-profiles` exemption, the surviving
  lockfile artifact, and **both** network-home failure shapes side by side —
  POSIX degrading silently with no error, and a Windows SMB-redirected
  `%USERPROFILE%` returning a permanent exit `6` on every verb. Neither is
  engine-detectable, so this text is the only operator-facing explanation —
  AC19, AC22.
- Both RFC § Errata sections carry a dated, Approver-signed entry for `6` — AC25.

**Approach:**
- Sweep the six locations; the "only the two recoverable rows" sentences become
  three in both files.
- Draft both errata entries in the frozen-RFC erratum form and request the
  Approver signature before merge.

**Done when:** AC19, AC22, AC23, AC25 met; the errata are signed.

### T9: The backlog register and spec lint are consistent

**Depends on:** none

**Touches:** workspace.toml

**Tests:** (goal-based)
- `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .`
  exits 0, read unfiltered — AC28.

**Approach — already applied in the spec-authoring PR, recorded here so the
implementing run does not re-derive it:**
- `{slug = "sso-contended-consumer-backoff", source = "spec/sso-store-transition-serialization AC24"}`
  is in `[backlog].open` with a cold-start-sufficient comment.
- The existing `sso-materialisation-ordering` entry is annotated as closed by
  this spec and **left in place**: the frozen `jira-check-sso-auto-login` spec
  defers against that slug at `spec.md:368` and lint invariant (iv) requires it
  to resolve. The register has no closed-item section.
- Remaining for the implementing run: nothing. The conditional
  `sso-keychain-call-timeouts` entry belongs to T5, which is where the bar is
  measured; T9 does not wait on it.

**Done when:** the lint exits 0 unfiltered.

### T10: Projections match their sources and the curation guard passes

**Depends on:** T2, T3, T4, T5, T6, T8

**Touches:** .agentbundle/bin/sso-broker.py, packs/credential-brokers/

**Tests:** (goal-based)
- `.venv/bin/python -c "import agentbundle, credbroker; print(agentbundle.__file__, credbroker.__file__)"`
  names this workspace before any generation step runs.
- `agentbundle catalogue self-host --check --root .` exits 0 — AC27.
- `packages/credbroker/credbroker/_sso.py` is byte-identical to the user-lib
  copy — AC27.
- The `broker` fixture's `projected` parameterisation passes for every test
  added in T1–T7 — AC27.
- The new concurrency module **executes** on the Windows credbroker step,
  proven by a module-level Windows guard that fails rather than skips when the
  lock primitive is unavailable — `self_host_windows.py`'s `_step` judges by
  return code alone, so a wholly-skipped module would exit 0 and read as
  coverage — AC20.
- `tools/lint-catalogue-curation-guard.py --base origin/main` exits 0 with all
  commits carrying `Engine-Change-RFC: RFC-0035` — AC26.

**Approach:**
- Drive every step through the workspace venv (`.venv/bin/agentbundle`,
  `.venv/bin/python`), never the global interpreter. A global editable install
  resolves to whichever workspace installed it last and silently produced wrong
  generated output during PR #882; the global interpreter is kept on PyPI builds.
  See `packages/AGENTS.local.md` § *Local installs go in a per-workspace venv*.
- Run `agentbundle catalogue self-host --root . --write`, commit the projection
  separately, then run the curation guard against committed state.

**Done when:** AC20, AC26, AC27 met; `make build-check` green.

## Rollout

- **Delivery:** big bang, no flag. The lock is unconditional; a flag would mean
  shipping a documented-unserialised mode, which is the defect.
- **Reversibility:** fully reversible by revert. The only new on-disk artifact is
  a directory of empty lockfiles, which a reverted build ignores.
- **Infrastructure:** none beyond one new user-scope directory created on demand.
- **External-system integration:** none. `credbroker` 0.6.0 is additive and
  consuming skills pin `>=0.5.0`, which 0.6.0 satisfies — so unlike PR #882
  there is **no publish-before-merge ordering constraint**. The PyPI release
  follows the merge.
- **Deployment sequencing:** encoded in `Depends on:` rather than asserted here.
  T1 and T9 are the only roots; T10 sits downstream of every code and doc task.

## Risks

- **A wiring site is missed and a path stays unserialised.** Review already
  found two (the Linux file-floor path, and `_capture`'s pre-store TOML write).
  Mitigation: AC5 enumerates the four acquisition sites and the assumes-held
  function they cover, T1's source assertions pin the
  descriptor origin, and T4 asserts the structural exclusions.
- **The thread harness proves less than it appears to.** If a refactor moved the
  lock to a per-process singleton, the thread harness would pass while
  interprocess serialisation was gone. T7 is the test that pins the property —
  but only for the file-floor path. The Tier-2 chunked path has no
  process-level test and that gap is stated in AC7 rather than papered over.
- **`jira.py` reports a transient contention as an operator action.** Its bare
  `except credbroker.SsoError` (`jira.py:709`) routes any SSO error to
  `EXIT_USER_ACTION`, so until `sso-contended-consumer-backoff` ships, a
  sub-second contention tells the operator to re-register. This is a real
  consumer-visible regression in remediation quality, accepted here because
  the alternative is widening scope into the consumer.
- **A contended capture throws away a sign-in that already succeeded.** The
  acquisition sits after the browser work, so a `refresh` that completed a
  headless IdP flow — or a `register` that consumed an operator's MFA — can exit
  `6` at the final step and lose the capture. The retry pays for another
  Chromium launch (up to `_REFRESH_SILENT_WINDOW_S = 20` plus launch time), and
  via `jira.py:709` the operator may see a re-register prompt for a sign-in that
  worked. Acquiring *before* the browser work would avoid it and is the
  *Ask first* alternative; it is not taken here because a 540 s hold would
  starve every reader. Accepted, and stated in the Objective rather than buried.
- **`rm` still reports success over a keychain that ignored the delete.**
  `_delete_cookie_jar` discards `_purge_credential`'s return value
  (`sso-broker.py:610`, `:619`) and `_do_rm` unlinks the profile TOML
  unconditionally (`:1315`), so a backend that accepts writes and ignores
  deletes leaves cookie bytes at rest while `rm` prints "removed" — and once the
  TOML is gone, `_do_rm` short-circuits on "not registered" and nothing can
  reach those slots again. This is **pre-existing** and not introduced here;
  AC5 pulls the unlink inside the lock without changing its ordering. Fixing it
  means a verified purge before the unlink, mirroring `_store_cookie_jar`'s
  verified reap — out of scope, and worth its own item if the reviewer of the
  implementing PR agrees.
- **The 10 s budget interacts badly with Windows' resource-dependent release.**
  A killed holder on a loaded box could exceed it, producing a spurious exit
  `6`. Accepted: `6` is recoverable. If common, the budget is an *Ask first*
  change, not a silent bump.
- **The macOS critical section is longer than assumed.** `/usr/bin/security`
  calls carry no timeout and a locked login keychain blocks indefinitely.
  AC10 measures rather than assumes; a missed bar surfaces
  `sso-keychain-call-timeouts` as a decision rather than silently adding
  timeouts to a projected file.
- **Windows behaviour is inferred from documentation, not observation.** The
  `msvcrt` retry ceiling and mandatory-lock semantics come from Microsoft and
  Python docs. AC20 puts the new module in front of a real `windows-latest`
  runner, which is the first observation this repo will have of either.

## Changelog

- 2026-08-07: initial plan.
- 2026-08-07: revised against the pre-EXECUTE adversarial and security reviews.
  Substantive changes, not reordering: the lock moved from
  `_store_cookie_jar`'s continuation branch to the whole function (the Linux
  `_tier2_backend is None` path was otherwise unserialised, which broke AC4 on
  the CI platform); `_capture` gained the acquisition so a contended `refresh`
  cannot leave a rewritten profile TOML and a seeded browser session behind;
  the single fault type split into contended-`6` and unavailable-`3` so a
  nested acquire or an unlockable network home is never reported as retryable;
  `rm` gained a documented unserialised fallback so a grammar-exempt legacy
  profile stays revocable; the proposed Windows CI job was **deleted** — the
  credbroker suite already runs there via `self_host_windows.py`, and the
  original assumption was simply wrong; T7's scope narrowed to the file-floor
  path after confirming no backend-injection seam exists; the doc sweep grew
  from one table to six locations.
- 2026-08-07: revised again against review round 2. Substantive changes: the
  exception taxonomy was rebuilt — classification is now by *which call raised
  and with which errno*, because `BlockingIOError` subclasses `OSError` and the
  round-1 catch would have made exit `6` unreachable on POSIX while Windows
  signals contention with the same `EACCES` an unwritable directory yields;
  the `rm` unserialised fallback was **deleted** after confirming
  `_profile_component` does not enforce the grammar, which made its premise
  false and left the spec's only fail-closed exception unjustified; AC8 stopped
  promising `browser-state/<profile>` untouched, which was structurally
  impossible and whose test could only have passed with Chromium stubbed;
  the acquiring `_store_cookie_jar` wrapper was dropped in favour of
  verb-level acquisition, since the wrapper would have had zero production
  callers and the whole property would have been asserted against it; AC10
  gained a fixed 2 s bar and lost its escape clause; two inverted `Depends on:`
  edges were corrected by moving exit-code assertions from T1 to T5 and the
  AC4 negative control from T2 to T3.
- 2026-08-07: rounds 4 and 5 applied. The held-set is keyed by
  `(thread, profile)` rather than thread alone — keying by thread let a caller
  holding profile `a`'s lock satisfy AC17 while mutating profile `b`, the
  likeliest mistake in a four-site design — and AC15/AC17 now ask two separate
  questions of it, each with its own test arm. AC10 became manual QA after
  confirming no CI runner can execute it, and reads as twenty consecutive
  iterations rather than an undefined p99 over twenty samples. Classification
  reads `exc.errno`, not exception class, and stubs raise
  `PermissionError(errno.EACCES, ...)` — `OSError(13).errno` is `None`, so the
  earlier stub would have failed a correct implementation. AC16's diagnostic is
  Windows-only: `flock(fd, LOCK_UN)` on an unlocked descriptor succeeds
  silently, verified by probe. AC22 carries both network-home failure shapes in
  its own text. `_do_rm` locks after `_profile_path` composes and before
  `path.exists()`, closing a check-then-act gap without invalidating the
  retired-fallback Assumption.
- 2026-08-07: round-6 findings applied. `errno.EDEADLOCK` **does not exist on
  macOS** (probed: `hasattr(errno,'EDEADLOCK')` is `False`, `EDEADLK` is 11) —
  BSD omits it, glibc aliases it, MSVC defines it — so both the stub and the
  classifier now go through `getattr(errno, "EDEADLOCK", errno.EDEADLK)`; as
  written it would have raised `AttributeError` on the one platform T1's
  Done-when requires. The `ENOLCK` stubs moved to the two-argument form and
  gained the `EOPNOTSUPP` and `ENOSYS` arms AC13 names: `OSError(errno.ENOLCK).errno`
  is `None`, so the single-argument stubs passed by the fault *default* rather
  than by classification and would have stayed green against an implementation
  that wrongly called `ENOLCK` contention. The *Never do* rail moved from
  process-scoped to thread-scoped — read literally it prescribed the
  process-global guard AC15 rejects, which would disable the threaded harness.
- 2026-08-07: round-3 findings applied. AC10 reclassified from goal-based to
  **manual QA** after confirming no CI runner can execute it — there is no macOS
  runner, Linux has no Tier-2 backend, and Windows uses a different cost model;
  twenty hand-run iterations recorded in `manual-qa.md`. Classification now reads
  `exc.errno` rather than exception type, because CPython maps `EACCES` to
  `PermissionError` and a stub raising bare `OSError` would let a wrong
  implementation pass. Added AC14 (`rm`'s exit-`3` names the manual recourse,
  since deleting the fallback removed the operator's in-tool escape), AC17
  (`_store_cookie_jar` asserts held-ness, so the four wiring sites are enforced
  rather than conventional), and a release-path stderr diagnostic in AC16 (an
  unlock reporting "not locked" is the only sign the acquire never took —
  suppressing the raise must not suppress the evidence). AC13 now states its
  errno list is POSIX-only and that a Windows SMB home surfaces unsupported
  locking as a permanent exit `6`. `_do_rm` takes the lock before its existence
  check, closing a check-then-act gap against a first `register`. Superseded
  round-2 text was purged from the design-decision list, the failure table, and
  Risks — an implementer reading top-to-bottom would have hit the rejected
  design first.
