---
id: worktrees-state-locks-and-shared-host-admission
title: Worktrees, state locks, and shared-host admission
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Worktrees, state locks, and shared-host admission

## Scope and routing signals

Use for skill scripts, evaluations, packs, and execution environments that use
separate working directories while sharing machine-local state. It does not
define a general multi-host operations model.

## Decisions and minimum evidence

Name the state owner and the guarantee each layer actually provides. A guarantee
at one layer was mistaken for a stronger guarantee at another. Separate a safe
final write from protection for a read, decide, and write transition.

## Construction method

Give each execution a bounded temporary, cache, port, and state namespace.
Use a lock or serialization mechanism for the full transition it protects, and
release it on every completion path. Treat directory separation as one boundary,
not proof that machine-local resources are independent.

## Evidence and evaluation

Exercise competing read/decide/write operations and concurrent executions that
request the same temporary, cache, port, or state resource. Verify the intended
owner rejects or serializes the conflict.

## Failure modes

An atomic final write can still lose a competing decision. Separate worktrees
can collide through shared temporary storage, caches, ports, or state. A lock
that covers only output publication does not protect earlier decisions.

## Security and authority

Treat shared state as a boundary between executions. Constrain names and paths,
avoid exposing another execution's data through reused state, and grant access
only to the component that owns lifecycle cleanup.

## Related topics

For temporary-path lifetime, consult `python-and-pytest`. For execution-cost
batching, consult `process-and-filesystem-cost`.

## Provenance and lifecycle

**layered guarantees:**
A guarantee at one layer was mistaken for a stronger guarantee at another.
Last verified: 2026-08-30.
Revalidate when another independent state-ownership failure is observed.
