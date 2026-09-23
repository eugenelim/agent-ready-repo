# Verification ledger

Execution observations for this delivery. Not contract: the criteria live in
`spec.md` and the plan is pinned.

## Mutation evidence

Every check below was verified falsifiable by editing the source, running the
named tests, requiring failure, then restoring the original bytes and
re-verifying the sha256. No `git checkout`, `reset` or `stash` was used — the
working tree carries uncommitted work and the stash stack is shared across
worktrees.

| Probe | Source edit | Tests required to red | Result |
| --- | --- | --- | --- |
| AC1 capture dominance | move the capture after a cohort read | `capture_precedes` | red |
| AC6 hold contents | drop the state write from the hold | `hold_contains` | red |
| AC22 no spawn in the hold | add `subprocess.run` inside the hold | `no_spawn_and_stays` | red |
| AC3 exemption wiring | compare against a hard-coded event literal | `declared_set` | red |
| AC17 cohort writes held | add an unlocked `write_state_atomic` caller | `inside_a_cohort_hold` | red |
| AC18 one-way lock order | add an `engine-state.json` read to `loop-cohort.py` | `never_reaches_the_engine` | red |
| AC12 the race itself | remove the fingerprint comparison | all 5 interleaving cases | red (5 failed) |
| AC4 mutual exclusion | acquire on `engine-state.json` instead of the cohort path | `peer_holding` | red |

The AC4 probe is the one worth keeping in mind. Every interleaving case forces
the mutator to commit *before* the engine commits, so all five still pass with
the lock taken on the wrong path — their refusal comes from the fingerprint
alone. Only AC4 observes the exclusion itself, and only it reds under that edit.

## Observations

- A re-run `loop-cohort schedule` over an unchanged plan rewrites byte-identical
  cohort state. The first draft of the schedule cases therefore asserted a
  refusal that could not happen and failed for the right reason. The cases now
  repartition the plan first, and `_assert_refused_without_writing` proves the
  cohort state actually moved before asserting the refusal — without that, a
  no-op mutator would report a closed race that never opened.
- `_get_repo_root` is statically reachable under the cohort lock: every
  `@_locked` verb re-calls `_resolve_spec_dir` in its own body, redundantly with
  the decorator. It is harmless because that resolver memoises per working
  directory, so the in-hold call is a cache hit — but "no spawn under the cohort
  lock" is false as a property, and AC16 asserts boundedness instead.
- `test_loop_concurrency.py` runs 25 cases in 70s; `test_loop_engine.py` plus
  `test_contract_amendment_wave4.py` run 204 in 324s.
