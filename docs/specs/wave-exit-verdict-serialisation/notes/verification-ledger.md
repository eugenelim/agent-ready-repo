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
| AC20 content class | delete the `ManagedContentError` arm | `discriminates_its_four` | red |
| AC13 reclaim reported | make the lock handler exit zero | `reclaim_at_the_end` | red |
| loader fail-open | drop the try around `_guards()` | `guards_loader_failure` | red |
| AC6 unlink exclusion | move the outbox unlink inside the hold | `hold_contains` | red |
| AC17 shape-3 route | add an unlocked caller of `_schedule_run_impl` | `inside_a_cohort_hold` | red |

The AC4 probe is the one worth keeping in mind. Every interleaving case forces
the mutator to commit *before* the engine commits, so all five still pass with
the lock taken on the wrong path — their refusal comes from the fingerprint
alone. Only AC4 observes the exclusion itself, and only it reds under that edit.

## Post-gates review round 1

Adversarial returned 3 Blockers, 8 Concerns and 3 Nits; security returned 3
Concerns and 1 Nit. The repairs that changed behaviour rather than wording:

| Finding | What was wrong | Repair |
| --- | --- | --- |
| sec C2, adv N12 | `_guards()` was called inside the state-read try and again in an `except` clause, where evaluating it while an exception is in flight can raise and escape the whole try — a later `except Exception` does not catch a raise from clause evaluation. | Resolve the module, the path and the exception class before the try; use the resolved class in the handler. **Correction:** round 1 stated the cause as `FileNotFoundError` landing on the ABSENT arm, and round 2 refuted it — `_guards()` wraps every load failure in `GuardsUnavailable`, a `RuntimeError`, which the catch-all already handled. That fail-open never existed. The clause-evaluation escape is real and is what the restructure closes. The first version of the test drove it with an exception the loader cannot raise. |
| sec C1, adv C4 | AC20's four-way distinctness never produced `content-unusable`: the 4300+ digit input lands on the catch-all, not the `ManagedContentError` arm. Deleting that arm left the test green. | Five observations, with genuinely malformed JSON as a separate case. Probe confirms the arm's removal now reds. |
| adv B1 | AC13 had no artifact at all — the suite covered the three acquisition failures but nothing raised `StateLockLost` on hold exit. | A case that makes the hold's exit raise it and asserts non-zero. |
| adv C7 | AC17's closure marked a helper held as soon as ONE held caller reached it, so a state write reachable from both a held and an unheld verb passed. | Heldness per path: a function counts as held only when it has callers and every one of them is held. |
| sec N4 | AC22's no-spawn set was rooted at three helpers, omitting the two operations the delivery moved INTO the hold. | Rooted at the `with` block's own statements. |
| adv C5 | AC15 recovered the acquisition sets, asserted them non-empty, then used a literal `1`. | The count is derived from the recovered routes. |
| adv C6 | AC6 checked four of the six exclusions its criterion names. | All six, including the FSM lookup and the outbox unlink. |

Two probes in the first round of this batch reported STILL GREEN. One was a
missing test (the loader guard had none) and one was a bad probe — the injected
call sat before the hold rather than inside it. Both were corrected and both
now red. A probe that fails to red is not automatically a weak check; it can be
a weak probe, and the two need telling apart.

## Post-gates review round 2

Security returned `Clean — ready to commit.` Adversarial returned 1 Blocker, 3
Concerns and 1 Nit, all on the round-1 repairs rather than on the mechanism.

The one worth recording is the correction above. Round 1's Nit 12 asserted a
specific exception class, that assertion was adopted without checking it at
source, and it was then restated more confidently in a code comment, a commit
message, this ledger and a test. The repair was right and its reason was not.
Verifying the *shape* of a hazard is not verifying the *class*.

Two others were real holes in checks that had passed:

- AC17 seeded a `with_state_lock` body callable as a held root, which exempted
  it from the every-caller rule. An unlocked second route to
  `_schedule_run_impl`'s write left the case green. The lock site is now
  recorded as one held caller and the target earns heldness like anything else;
  the reviewer's exact probe reds.
- AC15 decided mutator membership with `held`, which after the per-path repair
  means "always called from inside a hold" — the inverse of "reaches a hold".
  It counted a pure argv parser as acquiring. Membership is now downward
  reachability to an acquisition.

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
