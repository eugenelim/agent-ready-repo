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
| loader raises during clause evaluation | drop the try around `_guards()` | `loader_failure`, `while_handling` | red |
| AC6 unlink exclusion | move the outbox unlink inside the hold | `hold_contains` | red |
| AC17 shape-3 route | add an unlocked caller of `_schedule_run_impl` | `inside_a_cohort_hold` | red |
| AC15 cohort route | add a call to a *different* acquiring cohort mutator | `budget_counts` | red |
| AC15 engine route | add a second cohort `exclusive` in a *new* engine function | `budget_counts` | red |
| AC15 engine route | add a second cohort `exclusive` *inside the same* function | `budget_counts` | red |
| AC15 attribution | acquire via a local variable the classifier cannot attribute | `budget_counts` | red |
| AC15 site count | add a cohort `exclusive` in a new function *reachable from* `cmd_transition` | `budget_counts` | red |
| AC13 reclaim wording | render the reclaim through the acquisition handler | `reclaim_at_the_end` | red |
| AC11 mechanism | refuse from a lock timeout instead of the fingerprint | `commit_window` | red |

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

## Post-gates review round 3

Two Blockers and two Nits, all on the round-2 repairs. Both Blockers were the
same fault, and it is worth naming because it has now recurred.

**A repair's stated reason outrunning its source.** Round 2's C4 caught it once:
the loader fix was correct and its recorded cause was an exception class the
loader cannot raise. Round 3 caught it again: AC15's engine-side membership was
described in a comment and a commit message as "recovered rather than declared"
while the code filtered for one literal function name, so `len(engine_routes)`
was pinned at 1 and a second engine-side acquisition under-derived the bound by
a whole timeout.

The self-probe run before that review did not catch it either, and the reason
is instructive: the probe added a second *cohort-side* route, which the check
did handle, and the passing result was read as covering both halves. A probe
exercises the path it picks, not the claim it is quoted against.

Both halves are recovered structurally — engine-side by finding every
`exclusive(...)` call whose argument locks a cohort path, cohort-side by
downward reachability.

## Post-gates review round 4

One Blocker, and it is the same class a third time — this time inside the two
ledger rows written *about* the class.

Both route sets held function **names** while the bound consumed them as a count
of **acquisitions**. A second `exclusive` added inside a function already in the
set left the count unchanged, so the row "add a second engine-side `exclusive`
on a cohort path" was falsified only for the new-distinct-name instance, not for
the class it names. Counting is per site now, the rows say exactly which
mutation each one falsifies, and a site the classifier cannot attribute fails
the check instead of dropping out — that silent drop was the fail-open
direction, since an acquisition written through a local variable would have left
the bound unchanged.

Three instances is enough to state the rule rather than the cases. **A probe
licenses exactly the sentence that describes the mutation it ran.** Widening
that sentence to the class the probe belongs to is the step that failed here
each time: the loader's exception class, the "recovered rather than declared"
claim, and now these two rows.

## Post-gates review round 5

Two Blockers, one Concern, one Nit — three of them the same class, a fourth
instance. `concurrent` evaluated to 2 while the docstring and AC15 both said the
arithmetic collapses mutually exclusive branches; it over-approximated and
claimed otherwise.

The repair stopped patching the expression. Rounds 4 and 5 wanted two different
things from one number — red when a site is added, and collapse sites that
cannot co-execute — and no single count does both. There are two numbers now:
the site counts are pinned, so any new acquisition forces a human back to the
derivation, and the bound is taken over distinct acquiring functions, which is
the collapse AC15 names. The derived maximum is 50 s again, which is what the
plan has recorded all along.

Two probes in this batch came back green and only one was a weak check. Adding
an acquisition in an *unreachable* function is correctly ignored; re-probed
through a reachable one, it reds. Substituting the bare-name call form tested
whether the matcher sees it, which it does. But ADDING an acquisition through an
alias — `acquire = sl.exclusive` — is genuinely invisible, and no static matcher
resolves that without dataflow. The docstring said "every `exclusive(...)` site";
it now says which form it matches and why the pinned site counts are what covers
the rest.

## Post-gates quality review

Six Concerns and three Nits, no Blockers. One was an operability defect in
shipped code and the rest were in the verification layer.

**The reclaim refusal read like an acquisition refusal, and the two need
opposite responses.** A failed acquisition wrote nothing, so retry is right. A
`StateLockLost` at release means the transition already committed and a pending
record survives, so retry is wrong. Both rendered through the same
`cohort state lock:` prefix. They are separate handlers now — `StateLockLost`
first, since it subclasses the other — and the reclaim message says the
transition DID commit and not to re-run. The AC13 case pins that wording,
including that it must not say "nothing was written".

Two checks were weaker than they read. The five interleaving cases accepted any
non-zero exit, so a lock timeout or a child crash satisfied a case written for
the fingerprint mismatch; they now require the stderr to name it. The cohort-side
budget added the engine's own hold ceiling — a different process on the same
lock — to a sum of spawn edges across mutually exclusive verbs; it takes the
maximum over verbs and drops the engine term.

Two findings are recorded rather than repaired, because repairing them would
mean claiming something untrue:

- The canonicalise catch-all in `_cohort_fingerprint` is **unfalsifiable against
  the current reader**. Deep nesting raises inside `read_state` and is caught
  earlier; a lone surrogate cannot fail `encode` under `ensure_ascii=True`. It
  is kept as a contract guard, not an input guard, and the code says so.
- AC15's inequality is **slack by 25x** and is not its own discriminator; the
  pinned site counts are. The test says so rather than implying the arithmetic
  is load-bearing.

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
