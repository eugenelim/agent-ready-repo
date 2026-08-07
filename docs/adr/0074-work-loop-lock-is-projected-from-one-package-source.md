# ADR-0074: The work-loop's state lock is projected from one package source, not copied

- **Status:** Accepted
- **Date:** 2026-08-07
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer, security-reviewer
- **Supersedes:** none
- **Related:** `packages/agentbundle/agentbundle/build/user_libs.py`,
  `packages/agentbundle/agentbundle/statelock.py`

## Decision summary

- **Decision:** the advisory lockfile the work-loop skill needs is authored
  **once**, in `packages/agentbundle/agentbundle/statelock_core.py`, and
  **projected** byte-faithfully into
  `packs/core/.apm/skills/work-loop/scripts/_statelock.py` by a build-pipeline
  primitive with a `make build-check` drift gate. It is not hand-copied, and
  the skill does not import `agentbundle` at runtime.
- **Because:** the repo already solves "a pack needs stdlib-only code that also
  lives in a package" by projection, not duplication — `credbroker` is
  projected from `packages/credbroker` into
  `packs/credential-brokers/.apm/user-libs/credbroker/` and drift-gated. A
  second lock implementation would drift from the first, and the first has a
  confirmed liveness defect.
- **Applies to:** any future stdlib-only helper a skill script needs that also
  belongs to a package.

## Context

`loop-cohort.py` and `loop-engine.py` perform an unguarded read-modify-write on
their state files. Two concurrent verbs silently lose an update; the engine also
admits an FSM transition it is specified to reject, and duplicates a record in
the durable audit outbox. Reproduced at 20/20, 10/10 and 6/6 trials — see
`docs/specs/loop-cohort-state-lock/notes/reproduction.md`.

`agentbundle/statelock.py` already solves this shape for the installer's
`state.toml`: an `O_CREAT | O_EXCL` lockfile with bounded retry and a stale
reclaim via atomic rename. Two facts constrain how the skill reuses it:

1. **Skill scripts are stdlib-only.** They are projected into adopter repos and
   user-scope trees where `agentbundle` is not importable. A skill script that
   imports the installer package works for maintainers and fails for adopters.
2. **The precedent has a liveness defect.** Its acquire loop's
   `except FileNotFoundError: continue` has no deadline check and no sleep. When
   the lock path is a dangling symlink, `open(O_CREAT|O_EXCL)` fails `EEXIST`
   (POSIX refuses to follow the link) while `Path.stat()` follows it and raises
   `FileNotFoundError` — so the loop spins at 98% CPU indefinitely and the
   timeout never fires. Confirmed against the shipped package.

## Options considered

| Option | Verdict |
|---|---|
| Import `agentbundle.statelock` from the skill scripts | **Rejected** — driver 1. Breaks for every adopter. |
| Hand-copy (port) into the skill, hardened | **Rejected** — two implementations of one protocol drift, and a fix to one is not a fix to the other. This was the first-round decision; it was wrong because it treated the duplication as unavoidable when the repo already had a mechanism. |
| Project into `.apm/user-libs/` (the credbroker target) | **Rejected** — that target is `~/.agentbundle/lib`, a `sys.path` floor appended at *lowest* precedence and guarded on the directory existing, so it degrades to *absent*. A lock that can be absent fails open, which is the one failure mode this feature must not have. |
| **Project into the skill's own `scripts/`** | **Accepted.** |

## Decision

One source, one projection, one gate.

- **Source of truth:** `packages/agentbundle/agentbundle/statelock_core.py` —
  stdlib-only, no `agentbundle` imports, so the projected copy is importable
  standalone. It carries the hardening the precedent lacks: a deadline check on
  every retry path, refusal of a lock path that is not a regular file,
  ownership-checked release, no directory creation, and a `StateLockError` base
  that does not derive from `OSError` (both skill scripts carry broad
  `except OSError` handlers that would otherwise swallow it).
- **Projection:** a `skill-libs` build-pipeline primitive mirroring
  `user_libs.py`'s contract — `apply_projection` on `make build-self`,
  `check_drift` on `make build-check`, resolving **modified / missing /
  orphaned**, and a documented no-op outside the monorepo (the committed copy is
  what adopters receive). Target is the skill's `scripts/` dir, so the file
  ships with the skill and cannot be missing at runtime.
- **Not in this change:** `statelock.state_lock` and its callers are left alone.
  The package therefore carries two lock implementations transiently. That is a
  deliberate scope boundary, not an oversight: rewiring
  `persist_state_locked` onto `statelock_core.exclusive` changes the installer's
  behaviour and needs an `agentbundle` release, so it is a separate PR —
  tracked as `agentbundle-statelock-symlink-spin`, which is what finally closes
  the shipped defect in driver 2.

## Consequences

**Good.** One authored implementation. Skill scripts stay stdlib-only and
adopter-portable with no runtime dependency on `agentbundle`. The drift gate
makes a hand-edit to the projected copy a build failure rather than a silent
fork. The hardening is written once and inherited by the follow-up migration.

**Bad.** A change to the lock now requires `make build-self` and a committed
projection — the same tax `credbroker` pays. Editing the projected copy is a
trap; the gate catches it, but only at `build-check`. And until the follow-up PR
lands, `agentbundle` holds two lock implementations and its own install path
still carries the spin.

**Mitigation.** The projected copy's header names its source and says not to edit
it. The backlog item is a hard dependency edge (`needs`) on this spec, so the
migration cannot be lost.
