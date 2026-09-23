# Plan: agentbundle-statelock-hardening

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files I'll touch**
- `packages/agentbundle/agentbundle/statelock.py`.
- `packages/agentbundle/tests/unit/test_statelock_hardening.py` (new).
- Version + both changelogs; `workspace.toml`.

**What demonstrates done**
- The reproduction, before and after; 14 tests; mutation revert; `make ci`.

**What I am NOT changing**
- The work-loop skill's `_statelock.py` — the source of the port, untouched.
- `persist_state_locked`'s signature or the merge semantics.
- The 60s `stale_after` default (an NTP-skew margin, not part of this defect).

## Security reasoning (inline — `security-reviewer` is a named skip)

- **Availability / CWE-835 (infinite loop).** The primitive is an unkillable
  busy-wait reachable by anyone who can create a name next to the state file.
  It is a denial of service on *every* state-mutating verb at once, and the
  timeout that should have bounded it was itself bypassed — the worst shape,
  because the caller believes it is protected.
- **`path-and-file` / CWE-59 (link following).** `Path.stat()` follows; the
  planted symlink is what turned a normal contention path into an unbounded one.
  `os.lstat` plus an S_ISREG refusal removes the class, not just the instance.
- **Concurrency (TOCTOU).** AC5 and AC6 are two different ways the lock could
  admit two holders — one at release, one during reclaim. Both are real races
  rather than theoretical: the reclaim window is exactly when a third contender
  is most likely to be trying the path.
- **Failure mode chosen.** Refusing immediately on a non-regular lock path is
  louder than waiting. That is deliberate: a timeout message would send the
  operator to retry, which cannot succeed.
- **Not in scope.** This does not authenticate the lock's *creator*; a local
  attacker can still hold the lock legitimately and block progress for
  `stale_after`. Bounded, visible, and a different problem.

## Declined patterns

- **Tempted:** import the work-loop skill's `_statelock.py` directly instead of
  porting. **Declined:** ADR-0074 keeps them separate on purpose, and the skill
  script is not importable from the installed package anyway.
- **Tempted:** make `StateLockUnusable` subclass `StateLockTimeout` so every
  existing `except StateLockTimeout` catches it. **Declined:** it is not a
  timeout, and mistyping it to buy compatibility would make the taxonomy lie.
  Checked the two real consumers instead — both handle the OSError family.
- **Tempted:** also port the reference's `StateLockLost` (raised when a hold
  discovers its lock was reclaimed mid-body). **Declined:** it is a new
  observable failure for callers that today see silent success; worth doing, but
  as its own decision rather than inside a DoS fix.

## Anchor-test sweep

- `tests/unit/test_statelock.py` — five existing tests over acquire, contention
  and the merge; all still pass unchanged.
- `tests/integration/test_local_scope_install.py` patches
  `persist_state_locked`; signature untouched.
- Release-surface pins under `tests/roster/` — re-run after the bump (pass).

## Verification log

- **AC1** reproduced against the shipped code: still spinning after 5s with
  `timeout=2.0`.
- **AC2/AC3** after the fix: `StateLockUnusable` in 0.000s.
- **AC7** mutation: reverting lstat+refusal and the bounded retry re-fails the
  spin test with the "it is spinning" assertion; restoring passes.
- **Suites** 14 tests across the new and existing statelock files; roster pass.
- **REVIEW** `adversarial-reviewer` and `security-reviewer` = named skips
  (session instruction prohibits subagent dispatch). Reasoning inline above.
