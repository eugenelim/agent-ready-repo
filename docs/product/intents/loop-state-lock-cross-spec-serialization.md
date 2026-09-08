# Serialize loop state recovery across specs

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/loop-cohort-state-lock AC11](../../specs/loop-cohort-state-lock/spec.md)

## Outcome

Work-loop state recovery and its repo-global event outbox can be operated concurrently without one spec's transition mutating another spec's in-flight state, with the lock failure and reclaim cases proved by deterministic evidence.

## Opportunity

The current per-spec lock protects only the spec being transitioned, while recovery and both outbox writers use repo-global paths and the remaining failure observations have not been conclusively classified.

## What this absorbs

### loop-outbox-cross-spec-rmw

`loop-engine`'s `_recover_pending` reads the repo-global `.loop-run/events.pending` and calls `_recover_engine_state_tmp(pending_spec_dir)` for whichever spec the record names. A transition on spec A, while holding only A's per-spec lock, can therefore promote or delete spec B's in-flight engine-state temporary file while B holds B's own lock. The two outbox writers, `_write_events_pending` and `_append_events_jsonl`, likewise touch single repo-global paths on the same terms. A per-spec lock cannot serialize these operations. The recorded fix options are to skip a pending record naming another spec and leave it for that spec's next transition, or add a repo-scoped lock with a documented acquisition order relative to the per-spec lock. A second lock scope risks deadlock without an ordering rule.

Unblocks when: a design establishes the second lock scope and its acquisition order, or establishes the safe other-spec pending-record behavior.

### statelock-token-write-failure-test

The `loop-cohort-state-lock` contract says that the token write must succeed before the body is entered, that failure removes the lockfile, and the verb fails closed. It records this as deferred because injecting an `os.write` failure needs a seam the module deliberately lacks. The missing test must demonstrate that token-write failure prevents body entry, removes the lockfile, and fails closed.

Unblocks when: a test mechanism can control the token-write failure without weakening the lock module's deliberate no-seam design.

### statelock-concurrent-reclaimers-test-flake

Ubuntu Python 3.12 once reported two entrants while one raised `StateLockLost`; a same-commit rerun, Python 3.11, and 3/3 local runs passed. The case is unverified. A deterministic trace must distinguish a real double-holder race from the intended loss-detection path, then the lock or assertion must be corrected accordingly.

Unblocks when: the deterministic trace establishes which path occurred.

### statelock-reclaim-race-flake

The concurrent-reclaimers case failed once in CI on 2026-08-17, passed the same-commit rerun, and passed 3/3 locally. Do not quarantine it before measuring its probability and trace. The evidence must be repeated loaded runs in both the former warm-runner and current first-job shapes.

Unblocks when: those runs provide a measured probability and trace.

## Assumptions

- Cross-spec recovery needs a design that proves a deadlock-free acquisition order or proves that deferring another spec's pending record is safe.
- `statelock-token-write-failure-test` needs controlled token-write-failure evidence that preserves the deliberately seam-free lock implementation.
- The two reclaim observations need the deterministic or loaded-run evidence named above before their lock behavior or assertions can be changed.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
