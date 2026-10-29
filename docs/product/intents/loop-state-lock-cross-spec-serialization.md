# Serialize supervisor state across specs

- **Slug:** `loop-state-lock-cross-spec-serialization`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [the state-lock spec, AC11](../../specs/loop-cohort-state-lock/spec.md), the contract of the lock the supervisor's run lock reuses

## Outcome

Supervisor runs on different specs and their repo-global event log can operate concurrently without one spec's step mutating another spec's in-flight state, with the lock failure and reclaim cases proved by deterministic evidence.

## Opportunity

The supervisor's run lock, under each spec's `.supervisor/` directory, protects only the spec being stepped, while every run appends to the one repo-global `.loop-run/events.jsonl` and the remaining failure observations have not been conclusively classified.

## What this absorbs

### loop-outbox-cross-spec-rmw

Each supervisor verb takes its spec's run lock (`run_lock` in `_supervisor_admission.py`, built on `_statelock.py`) and then projects its steps into the repo-global `.loop-run/events.jsonl` through `reconcile_events` in `_supervisor_journal.py`. Two runs on different specs hold different run locks and append to the same file, so the run lock cannot serialize them. The supervisor treats that log as advisory: a failed read or write prints a warning and never changes a verb's outcome, each run's step records live in its own spec and Git history, and a run that missed a line catches up on its next verb. Recovery no longer reaches into another spec's state: the pending-record replay that could promote or delete another spec's in-flight state file left with the old engine. What remains is whether concurrent appends from two specs can interleave or truncate a line. The recorded fix options are an append that is atomic for one line, or a repo-scoped lock with a documented acquisition order relative to the run lock. A second lock scope risks deadlock without an ordering rule.

Unblocks when: a design establishes the append behavior for concurrent specs, or the second lock scope and its acquisition order.

### statelock-token-write-failure-test

The state-lock contract (`docs/specs/loop-cohort-state-lock`) says that the token write must succeed before the body is entered, that failure removes the lockfile, and the verb fails closed. It records this as deferred because injecting an `os.write` failure needs a seam the module deliberately lacks. The missing test must demonstrate that token-write failure prevents body entry, removes the lockfile, and fails closed.

Unblocks when: a test mechanism can control the token-write failure without weakening the lock module's deliberate no-seam design.

### statelock-concurrent-reclaimers-test-flake

Ubuntu Python 3.12 once reported two entrants while one raised `StateLockLost`; a same-commit rerun, Python 3.11, and 3/3 local runs passed. The case is unverified. A deterministic trace must distinguish a real double-holder race from the intended loss-detection path, then the lock or assertion must be corrected accordingly.

Unblocks when: the deterministic trace establishes which path occurred.

### statelock-reclaim-race-flake

The concurrent-reclaimers case failed once in CI on 2026-08-17, passed the same-commit rerun, and passed 3/3 locally. Do not quarantine it before measuring its probability and trace. The evidence must be repeated loaded runs in both the former warm-runner and current first-job shapes.

Unblocks when: those runs provide a measured probability and trace.

## Assumptions

- Concurrent cross-spec event appends need a design that proves a deadlock-free acquisition order or proves that an advisory, catch-up-on-next-verb log is safe.
- `statelock-token-write-failure-test` needs controlled token-write-failure evidence that preserves the deliberately seam-free lock implementation.
- The two reclaim observations need the deterministic or loaded-run evidence named above before their lock behavior or assertions can be changed.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
