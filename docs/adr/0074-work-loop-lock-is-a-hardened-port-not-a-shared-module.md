# ADR-0074: The work-loop's state lock is a hardened port of `statelock`, not a shared module

- **Status:** Accepted
- **Date:** 2026-08-07
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer, security-reviewer
- **Supersedes:** none
- **Related:** `packages/agentbundle/agentbundle/statelock.py`,
  `docs/specs/loop-cohort-state-lock/spec.md`

## Decision summary

- **Decision:** the work-loop skill's state lock is a **deliberate second
  implementation** at
  `packs/core/.apm/skills/work-loop/scripts/_statelock.py`, ported from
  `agentbundle/statelock.py` and **hardened past it**, rather than a shared
  module either package imports. The two copies are expected to diverge, and
  the skill copy is the stricter one.
- **Because:** the two consumers have incompatible import constraints, and the
  precedent carries a confirmed liveness defect that the port must not inherit.
- **Applies to:** any future lock or state-persistence helper needed by a skill
  script under `packs/*/.apm/skills/*/scripts/`.

## Context

`loop-cohort.py` and `loop-engine.py` perform an unguarded read-modify-write on
their state files. Two concurrent verbs silently lose one update; the engine
additionally admits a transition its FSM is specified to reject. Reproduced at
20/20 and 10/10 trials respectively — see
`docs/specs/loop-cohort-state-lock/notes/reproduction.md`.

`agentbundle/statelock.py` already solves this exact problem for the installer's
`state.toml`, and is the repo's blessed precedent: an `O_CREAT | O_EXCL`
lockfile with bounded retry and a race-safe stale reclaim via atomic rename.

The obvious move — import it — does not work, and the second-obvious move —
copy it — is not safe either.

## Decision drivers

1. **Skill scripts are stdlib-only.** They are projected into adopter repos and
   into user-scope trees where `agentbundle` is not importable. A skill script
   that imports the installer package works on the maintainer's machine and
   fails for every adopter.
2. **`persist_state_locked` is the wrong shape here anyway.** It takes a
   `mutate(state)` callback and is coupled to agentbundle's `config` and
   `safety` modules. The work-loop's call sites need the *decision* inside the
   critical section — the engine validates its FSM and runs git-shelling guards
   in there — so a mutate-callback would have forced each verb into an awkward
   closure and invited exactly the read→write-only locking that leaves the
   defect intact.
3. **Windows CI.** `fcntl.flock` is unavailable. Both implementations must be
   lockfile-based regardless.
4. **The precedent has a liveness defect.** Its acquire loop's
   `except FileNotFoundError: continue` has no deadline check and no sleep. When
   the lock path is a dangling symlink, `open(O_CREAT|O_EXCL)` fails `EEXIST`
   (POSIX refuses to follow the link) while `Path.stat()` follows it and raises
   `FileNotFoundError` — so the loop spins at 98% CPU forever and the timeout
   never fires. Confirmed empirically against the shipped package.

## Options considered

| Option | Verdict |
|---|---|
| Import `agentbundle.statelock` from the skill scripts | **Rejected** — driver 1. Breaks for every adopter. |
| Extract a third shared module both packages import | **Rejected** — the shared location would have to satisfy the stricter constraint (stdlib-only, no package context) anyway, so it buys nothing over a port while adding a cross-package coupling and a release-ordering dependency between the skill pack and the PyPI package. |
| Vendor `statelock.py` verbatim into the skill | **Rejected** — driver 4. Inherits a confirmed denial-of-service. |
| **Port and harden** | **Accepted.** |

## Decision

Port, and harden past the original. The skill copy adds, relative to the
precedent: a deadline check on every retry path; refusal of a lock path that is
not a regular file; ownership-checked release so a reclaimed holder cannot
delete its successor's lockfile; no directory creation; and a
`StateLockTimeout` that does not derive from `OSError` (both scripts carry
broad `except OSError` handlers that would otherwise swallow it).

The duplication is ~60 lines of stable, well-tested protocol code against a real
and permanent constraint. That is the cheaper side of the trade.

## Consequences

**Good.** Skill scripts stay stdlib-only and adopter-portable. The skill copy is
free to be stricter than the installer's without a coordinated release. The
hardening is covered by its own suite.

**Bad.** Two implementations of one protocol will drift. A fix in one is not a
fix in the other — and the reverse direction is live right now: the upstream
defect in driver 4 remains in the shipped `agentbundle` package, tracked as
`agentbundle-statelock-symlink-spin`. This ADR is the pointer that keeps that
visible.

**Mitigation.** Each copy's module docstring names the other and states that
they are deliberately separate. Neither is presented as the canonical one.
