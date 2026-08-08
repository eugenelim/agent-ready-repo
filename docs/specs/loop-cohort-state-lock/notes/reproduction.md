# Reproduction evidence — loop-cohort-state-lock

Captured before any fix was written. Describes the **pre-fix** tree at
`13be9e0da`. Retained as evidence, not as a contract; the spec is the contract.

## Harness

Real CLI processes, with the synchronising barrier placed **after** interpreter
and module startup: each child loads the target module via
`importlib.util.spec_from_file_location`, spins to a shared wall-clock instant,
then calls `main(argv)`.

The barrier placement is the whole trick. A naive fan-out of 20 subprocesses via
`ThreadPoolExecutor` loses **nothing**, 5 trials out of 5 — ~40 ms of Python
startup per process smears them apart and the microsecond-wide critical section
is never entered concurrently. A concurrency test built that way passes against
the unfixed tree and proves nothing.

## Case A — cohort: lost increment

Two concurrent `record-attempt` calls with distinct `--cycle-id` (distinct is
required; the `last_record_attempt_cycle_id` guard makes a repeat an idempotent
no-op). Each should add 1 to `implementation_retry_count`.

```
trial 0: 2/2 calls exited 0 | implementation_retry_count=1 | LOST=1   <-- LOST UPDATE
trial 1: 2/2 calls exited 0 | implementation_retry_count=1 | LOST=1   <-- LOST UPDATE
...
TOTAL LOST UPDATES across 20 trials: 20
```

**20 of 20 trials lost an update.** At N=8:

```
trial 0: 8/8 calls exited 0 | implementation_retry_count=1 | LOST=7
trial 1: 8/8 calls exited 0 | implementation_retry_count=3 | LOST=5
trial 2: 8/8 calls exited 0 | implementation_retry_count=2 | LOST=6
trial 3: 8/8 calls exited 0 | implementation_retry_count=1 | LOST=7
trial 4: 8/8 calls exited 0 | implementation_retry_count=1 | LOST=7

TOTAL LOST UPDATES across 5 trials: 32
```

Every call exits 0 and prints a success line naming the count it believes it
wrote. Nothing surfaces the loss.

## Case B — engine: illegal transition admitted

Two concurrent `transition <spec> spec-ready` from `SPEC-PLAN-DRAFTING`. Run
sequentially, the second **must** fail
`illegal transition: mode='code' state='SPEC-PLAN-REVIEW' event='spec-ready'`.

```
trial 0: 2/2 transitions exited 0 | state=SPEC-PLAN-REVIEW transition_sequence=1 | reported seqs=['1','1']   <-- BOTH ADMITTED
...
Trials where BOTH concurrent transitions were admitted: 10/10
```

**10 of 10.** Both validated against the same `current_state`, both computed
`new_seq = 1`. The durable audit outbox recorded the collision:

```
total events: 20
duplicate (spec, seq) pairs: 10
   ('docs/specs/.rmw-repro-0', 1) -> 2 records
   ('docs/specs/.rmw-repro-1', 1) -> 2 records
   ...
```

Setup notes learned here and folded into the plan: the engine confines
`spec-dir` to the repo root (so the spec dir must be in-tree), and its `run_id`
preflight reads `state.json` (so a paired `loop-cohort init` is required).

The engine's window is far wider than the cohort's — between its read and its
write sit the FSM table lookup, the mandatory `schedule check-current`
plan-hash guard, and event guards that shell out to `git`.

## Case C — the precedent's own acquire loop hot-spins

Found by the spec-stage `security-reviewer` and confirmed empirically against
the **shipped** `agentbundle/statelock.py` (not a port, not a hypothetical):

```
lock is dangling symlink: True | resolves: False
>>> STILL RUNNING after 6s with timeout=2.0 -> HOT SPIN CONFIRMED
    CPU%: 98.4
```

`statelock.py:74-78` — `open(O_CREAT|O_EXCL)` fails `EEXIST` on a symlink
regardless of target, while `Path.stat()` follows the link and raises
`FileNotFoundError`, whose handler does `continue` with **no deadline check and
no sleep**. `StateLockTimeout` is never raised: the verb neither proceeds nor
exits, at 98% CPU, indefinitely. One planted file wedges every verb for that
spec.

This is why the port hardens rather than copies — see the spec's AC set and the
plan's `## Design (LLD)`. The defect in the upstream package is tracked
separately as `agentbundle-statelock-symlink-spin`.
