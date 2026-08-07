# ADR-0074: The work-loop owns its state lock; agentbundle's stays separate

- **Status:** Accepted
- **Date:** 2026-08-07
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer, security-reviewer
- **Supersedes:** none
- **Related:** `packages/agentbundle/agentbundle/statelock.py`

## Decision summary

- **Decision:** the advisory lockfile the work-loop needs is an ordinary
  **work-loop script**, authored and owned at
  `packs/core/.apm/skills/work-loop/scripts/_statelock.py`. It is not shared
  with, projected from, or imported from `agentbundle`. `agentbundle` keeps its
  own lock for the installer's `state.toml`; the two implementations coexist
  deliberately.
- **Because:** they guard different files for different consumers, and the
  work-loop's lock is a work-loop concern. Sourcing it from the installer
  inverted ownership and bought a coupling that cost more than the duplication.
- **Applies to:** stdlib-only helpers a skill needs. Default to authoring them in
  the skill.

## Context

`loop-cohort.py` and `loop-engine.py` performed an unguarded read-modify-write on
their state files. Two concurrent verbs silently lost an update; the engine also
admitted an FSM transition it is specified to reject and duplicated a record in
the durable audit outbox. Reproduced at 20/20, 10/10 and 6/6 trials — see
`docs/specs/loop-cohort-state-lock/notes/reproduction.md`.

`agentbundle/statelock.py` already solved this shape for the installer's
`state.toml`, which made sharing it look obvious. It is not, for two reasons —
one hard, one about ownership.

## Decision drivers

1. **Skill scripts are stdlib-only, and must stay so.** They are projected into
   adopter repos and user-scope trees where `agentbundle` is not importable. Any
   solution that ends with the work-loop importing the installer is wrong at
   runtime, not just aesthetically.
2. **Ownership.** The work-loop's state files are the work-loop's. Making its
   lock a derivative of an installer-internal module puts a work-loop concern
   inside the installer and points the dependency arrow the wrong way.
3. **The engine tree is RFC-gated.** `packages/agentbundle/**` is protected by
   RFC-0059's path gate. Any build-time projection mechanism has to live in the
   build pipeline, so *any* sharing scheme is an engine change requiring its own
   RFC — a real cost, paid for a benefit driver 2 says we do not want.
4. **The older implementation is not the one to inherit.** Its acquire loop's
   `except FileNotFoundError: continue` has no deadline check and no sleep, and
   `Path.stat()` follows a symlink — so a dangling symlink at the lock path spins
   at 98% CPU indefinitely and the timeout never fires. Confirmed against the
   shipped package.

## Options considered

| Option | Verdict |
|---|---|
| Import `agentbundle.statelock` from the skill | **Rejected** — driver 1. Breaks for every adopter. |
| Project it from `packages/agentbundle/` into the skill, drift-gated | **Rejected** — drivers 2 and 3. This was the previous decision here; it inverted ownership and tripped the RFC gate for a single-source benefit that is not worth an engine change. |
| Move the source to its own `packages/statelock/` and project that | **Rejected** — fixes ownership but still needs the projection primitive in the gated build pipeline, so it keeps driver 3's cost. |
| **Author it in the skill** | **Accepted.** |

## Decision

`_statelock.py` is a work-loop script like `lint-spec-status.py` beside it:
committed, stdlib-only, loaded by path, and carried into `.claude/` and
`.agents/` by the ordinary skill projection that already handles every other
script in that directory. No new build primitive, no drift gate, no engine
change, no runtime dependency on `agentbundle`.

It carries the hardening driver 4 names: a deadline check on every retry path,
refusal of a non-regular lock path, inode-plus-token ownership on reclaim and
release, a link-based reclaim restore so a bystander's lockfile is never
clobbered, reclaim of a torn zero-byte create, no directory creation, and a
`StateLockError` hierarchy that does not derive from `OSError`.

## Consequences

**Good.** The work-loop owns its lock outright and has no dependency on the
installer at runtime *or* build time. Adopters get a self-contained file. No RFC
is needed, because no engine code changes. The skill's copy is free to be
stricter than the installer's without coordinating a release.

**Bad.** Two implementations of one protocol now exist, and a fix to one is not
a fix to the other. Concretely, the defect in driver 4 remains in the shipped
`agentbundle` package and must be fixed there on its own terms — tracked as
`agentbundle-statelock-symlink-spin`. Anyone reading both should not assume they
are in sync.

**Mitigation.** This module's docstring names `agentbundle/statelock.py`, says
the separation is deliberate, and points here. The backlog item carries a hard
`needs` edge so the other half is not lost.
