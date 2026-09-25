# Verification ledger — repair-round dispatch assertion

Execution observations. The spec and plan carry the contract; this file carries
what running the work established, in the order it was established.

## Mutation record

Method: edit the clause out of the source, run the suites, read the failure,
edit the clause back, and assert the file is byte-identical to what it was. No
`git checkout`, `git reset` or `git stash` at any point — the stash stack is
shared across worktrees.

Suites: `guards` = `packs/core/tests/skills/work-loop/test_loop_guards.py`;
`cli` = `packs/core/tests/skills/work-loop/test_loop_cohort.py`;
`engine` = `packs/core/tests/skills/work-loop/test_loop_engine.py`;
`parity` = `tests/roster/test_repair_round_predicate_parity.py`.

### T1 — the accounting clause and the repair-round verdict

Run 2026-09-24 against `_loop_guards.py`. Six clauses, six reds, none survived.

| # | Clause removed | Mutation applied | Suites that turned red |
| --- | --- | --- | --- |
| M1 | `accounts_for_task`'s superseded test | `return is_dispatch_record(value)` | guards, cli, parity |
| M2 | the `is True` strictness in that test | `not value.get(SUPERSEDED_KEY)` | **parity only** |
| M3 | `unaccounted_wave_tasks` calling the helper | reverted to `is_dispatch_record` | guards, cli, parity |
| M4 | the verdict's refusal branch | `if live:` → `if False:` | guards, cli, parity |
| M5 | the verdict's absent-container pass | made it refuse | guards, cli, parity |
| M6 | `wave-reopen` in `_SCHEMA_EXEMPT_PHASES` | removed from the frozenset | **cli only** |

Two of the six are caught by exactly one suite, and each justifies a design
choice that would otherwise look like surplus:

- **M2 is caught only by `parity`.** It needs a record carrying a *truthy
  non-`True`* `superseded` value, which exists only because the parity check's
  domain varies that member by type and value rather than by presence alone. Every
  example-based test in `guards` and `cli` uses `True` or omits the member, so
  all of them stay green while accounting silently turns on truthiness — and a
  record is data another process wrote.
- **M6 is caught only by `cli`.** `check_phase` refuses a non-exempt phase on a
  schema mismatch *before* the phase dispatch, so the verdict's own
  unsupported-schema row becomes unreachable through the verb while every test
  that calls the verdict function directly still passes.

The `oracle` suite alias is retired as of T6: `notes/walk_reopen_partition.py` was
deleted and its properties absorbed into `parity`. Detecting a change to the
shipped predicate is `parity`'s job, and M1, M2, M3, M4 and M5 all turned it red.

## Observations

- **The frozen wave-complete-dispatch-receipts oracle cannot see this change,
  and its criterion says so.**
  `docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py`
  re-implements the accounting predicate locally rather than importing
  `_loop_guards`. Re-run 2026-09-24, unedited, and its report is unchanged:
  35,728 states, 0 overlapping, 0 uncovered, R1 17864 / R2 13398 / R3 3829 /
  R4 49 / R5 384 / R6 108 / R7 4 / R8 92. That establishes this delivery did not
  redefine a record, a wave or a partition. It establishes nothing about the
  shipped guard.
- **The repair-round parity check (`tests/roster/test_repair_round_predicate_parity.py`)
  carries the properties the deleted oracle used to hold.** The oracle compared
  its own inline restatement against itself — a tautology. The parity check
  replaces it with comparisons against the shipped code. What the check actually
  asserts, test by test — an earlier revision of this list credited it with
  properties no test in it carries, so each is now named with its test:

  | Property | Asserted by |
  | --- | --- |
  | the transcribed record rule agrees with shipped `accounts_for_task` | `test_the_accounting_rule_agrees_record_by_record` |
  | the transcribed unaccounted list agrees with shipped `unaccounted_wave_tasks` | `test_the_accounting_predicate_agrees_over_the_whole_domain` |
  | the transcribed verdict agrees with the shipped verdict | `test_the_verdict_agrees_over_the_whole_domain` |
  | superseding moves a state from accounted to unaccounted and moves no other | `test_wave_exit_row_movement_from_superseding` |
  | `check --phase wave-reopen` writes nothing | `test_wave_reopen_check_is_read_only` |
  | both outcomes occur, so no comparison is vacuous | the non-degeneracy asserts inside the three agreement tests |

  Withdrawn from the earlier list because nothing asserts them: "a read refusal
  never reaches the verdict" (those states are skipped by `continue`, which
  asserts nothing) and "every refusal names a live record read from the
  container" (no assertion exists).
- **The parity check's transcription was wrong once, and the check found it.**
  The first version omitted the absent-container exemption that the shipped
  predicate carries inside itself, and 32 states disagreed. Fixed by moving the
  exemption inside the transcribed `_unaccounted`, which is where the frozen
  spec's § Always do requires it to live.

### T2 — the reopen verb

Run 2026-09-24 against `plan_wave_reopen` in `loop-cohort.py`. Seven clauses,
seven reds, none survived.

| # | Clause removed | Mutation applied | Test(s) that turned red | Observed failure |
| --- | --- | --- | --- | --- |
| M1 | the usable-partition refusal | `if False:` in place of the `not isinstance(waves, list) or not waves` guard | `test_wave_reopen_refuses_a_malformed_partition[not-a-list]`, `[empty]` | `not-a-list`: exits 0 (silently reopens nothing, since no wave record keys under a string-keyed digest); `empty`: falls through to the pointer check and refuses with the WRONG reason (`current_wave_index=0 is not an index into schedule_waves (len=0)`) instead of naming `schedule_waves`/`unusable` |
| M2 | the malformed-container refusal | `if False:` in place of the `malformed is not None` guard | `test_wave_reopen_refuses_a_malformed_container` (all four depths) | `AttributeError: 'int' object has no attribute 'get'` — an unhandled crash, not a clean refusal, once the container's own hostile shape reaches the marking code unchecked |
| M3 | the pointer-type refusal | `if False:` in place of the `isinstance(index, str)` guard | `test_wave_reopen_refuses_a_pointer_not_an_index[string]`, `[float]`, `[bool]` | `TypeError: '>=' not supported between instances of 'str' and 'int'` — the reason string `non_negative_int` returns reaches the `>=` comparison unchecked |
| M4 | the pointer-range refusal | `if False:` in place of the `index >= len(waves)` guard | `test_wave_reopen_refuses_a_pointer_not_an_index[past-the-end]` | exits 0 instead of refusing — no wave-records key exists at the out-of-range index, so nothing to mark and no crash either |
| M5 | the marking assignment | `record[SUPERSEDED_KEY] = True` replaced with `pass` | `test_wave_reopen_marks_only_the_live_digest_and_current_wave`, `test_wave_reopen_then_wave_exit_refuses_and_names_tasks`, `test_wave_reopen_then_fresh_receipt_accounts_again` | exits 0 but no record gains `superseded`; a subsequent `check --phase wave-exit` still PASSES, because every record reads as live |
| M6 | the live-digest scoping (`container.get(digest, ...)`) | replaced with a loop over every digest in the container | `test_wave_reopen_marks_only_the_live_digest_and_current_wave` | a record under a stale, non-live partition digest was superseded too: `{'0': {'T1': {'kind': 'receipt', 'superseded': True}}}` where the fixture asserts it untouched |
| M7 | the current-wave-index scoping (`.get(str(index))`) | replaced with a loop over every wave index under the live digest | `test_wave_reopen_marks_only_the_live_digest_and_current_wave` | the sibling wave index's record was superseded too: `{'T3': {'kind': 'receipt', 'superseded': True}}` where the fixture asserts it untouched |

Each mutation was reverted immediately after its red was observed and the file
diffed byte-identical against its pre-mutation copy before the next mutation
began. No `git checkout`, `git reset` or `git stash` was used at any point.

M6 and M7 are the two halves of the criterion the multi-wave, multi-digest
fixture exists to catch: marking by digest alone (M6) or by wave index alone
(M7) instead of the `(digest, wave index)` pair together, per plan.md T2's own
call-out that this is "the only fixture shape that can catch" either defect.

### T3 — the three edges' guard entries in `loop-engine.py`

Run 2026-09-24 against `loop-engine.py`. Six clauses, five reds, one confirmed
non-detection (documented below rather than papered over).

| # | Clause removed | Mutation applied | Suite(s) that turned red | Observed failure |
| --- | --- | --- | --- | --- |
| M1 | `_guard_repair_round`'s check itself | body replaced with `return None` | `engine` — `test_the_three_edges_refuse_then_admit_after_a_reopen[gates-failed]`, `[findings-remain]`, `[blocker-applied]` | all three edges admitted a transition while wave 0 still held a live, unsuperseded dispatch record — the defect this whole task exists to close |
| M2 | `_guard_check_phase_review_repair_round`'s source-state discriminator, replaced with the mode-only check the task explicitly asks for | `if engine_state.get("state") != "CODE-REVIEW": return None` replaced with `if False: return None` (this entry only ever runs for `mode == "code"`, so a mode-only condition degenerates to "always apply") | `engine` — `test_findings_remain_from_fresh_spec_plan_review_is_admitted_with_live_records`, `test_findings_remain_from_spec_plan_review_after_amendment_is_admitted` | `findings-remain` from `SPEC-PLAN-REVIEW` was refused: `"repair round: wave 0 still holds live dispatch records for: 'T1'; supersede them with \`loop-cohort wave reopen\`..."` — the twin-sourced edge the Agent Rules call out by name |
| M3 | `_guard_gates_failed_repair_round`'s composition order (existing guard first) | swapped to run the repair round before the retry-cap check | `engine` — `test_gates_failed_composition_order_retry_cap_reason_wins` | refusal reason became the repair-round text instead of `"implementation retry cap reached (5/5)"` |
| M4 | `_guard_check_phase_review_repair_round`'s composition order (existing guard first) | same swap, for the review cap | `engine` — `test_findings_remain_composition_order_retry_cap_reason_wins` | refusal reason became the repair-round text instead of `"review retry cap reached (5/5)"` |
| M5 | `blocker-applied`'s `_GUARDS` entry — its first guard ever | `("code", "blocker-applied"): _guard_blocker_applied` line removed from `_GUARDS` | `engine` — `test_the_three_edges_refuse_then_admit_after_a_reopen[blocker-applied]` | `blocker-applied` admitted a transition with wave 0's record still live — no guard fired at all |
| M6 | `_guard_blocker_applied`'s source-state discriminator | `if engine_state.get("state") != "CODE-HUMAN-GATE": return None` deleted | none in T3 — the full `engine` suite (214 cases) stayed green; **turned red in T6** — see T6 below | **did not turn red at T3.** `blocker-applied` has exactly one entry in `_CODE_TRANSITIONS` — `("CODE-HUMAN-GATE", "blocker-applied")` — so it is never twin-sourced today and the discriminator is unreachable by any T3 fixture. Recorded rather than hidden: the mutation is real, its non-detection is expected given the shipped FSM. **T6 adds `test_inert_source_state_discriminators_skip_repair_round_when_state_is_wrong`**, a direct unit test that calls `_guard_blocker_applied` with `{"state": "CODE-REVIEW"}` (wrong source state) and asserts `None` — removing the discriminator makes the guard apply, which refuses given the live-record fixture, turning that test red. M6 is no longer a survivor. |

Each mutation was reverted immediately after its result was observed and the
file diffed byte-identical (`sha256sum -c`) against its pre-mutation copy
before the next mutation began. No `git checkout`, `git reset` or `git stash`
was used at any point. `gates-failed`'s own source-state discriminator was not
mutated in the T1-T3 runs; it is mutated in § T6 below as M3, after a review
found this ledger asserting a result for it that no run had produced.

## Observations (T3)

- **The composition-order criterion needs the retry cap AND the live record
  in the same state**, or the "first" guard's refusal is unreachable and the
  test cannot distinguish "runs first" from "is the only one that runs". Both
  M3 and M4 fixtures carry a retry count already at its cap AND a live,
  unsuperseded dispatch record for the current wave.
- **The twin-sourced edge (`findings-remain`) is the only one where the
  source-state discriminator is live code today.** `gates-failed` and
  `blocker-applied` each have exactly one source state in `_CODE_TRANSITIONS`,
  so M6 (and the equivalent mutation on `gates-failed`, not separately run) is
  expected to pass — not a gap, but the flip side of `_guard_check_spec_status_on_code_review`'s
  existing pattern this task's guards were built to match: the read is
  defensive against a transition table that does not exist yet, not against
  one that exists today.
- **`unsupported-schema`, among the seven falsifying conjuncts, is refused for
  a reason that is not the repair-round guard's.** `check_identity`'s schema
  check runs at `cmd_transition`'s Step 0 — before the FSM table, before
  Step 1b, before any `_GUARDS` entry — for every event alike, including
  `blocker-applied`, which carries no guard of its own before this task. The
  falsified-conjunct test for that one case therefore asserts the narrower,
  honest claim: the transition IS refused, but the refusal names neither
  `"wave reopen"` nor `"repair round"` — proving the repair-round guard was
  never reached, rather than asserting an admission the shipped engine does
  not produce.

### T3 addendum — the discriminator's inert half, made into a tripwire

The implementer reported one clause whose removal left the suite green, and the
report was accurate: `_GUARDS` is keyed `(mode, event)`, and in code mode
`gates-failed` and `blocker-applied` each have exactly one source state, so
reading `engine_state["state"]` on those two guards cannot change an outcome
today. Only `findings-remain` is twin-sourced — `CODE-REVIEW` and
`SPEC-PLAN-REVIEW` — and its discriminator is load-bearing, proved by the
implementer's M2.

Verified independently against the parsed tables 2026-09-24:

| Event | Source states, code mode | Discriminator |
| --- | --- | --- |
| `gates-failed` | `CODE-VERIFICATION` | inert today |
| `findings-remain` | `CODE-REVIEW`, `SPEC-PLAN-REVIEW` | load-bearing |
| `blocker-applied` | `CODE-HUMAN-GATE` | inert today |

Disposition: the inert checks stay, because they make the three guards read
alike and fail safe if the table grows. Keeping unfalsifiable code silently is
the part that is not acceptable.

**T3 tripwire:** `test_only_findings_remain_is_twin_sourced_in_code_mode` pins
the table's shape and names, in its failure message, the fact that a new source
state makes that event's discrimination load-bearing.

| # | Clause removed | Mutation applied | Result |
| --- | --- | --- | --- |
| M8 | the table shape the tripwire pins | added `("CODE-REVIEW", "blocker-applied")` to `_CODE_TRANSITIONS` | **RED** — the tripwire fails and names the changed event |

**T6 direct test:** `test_inert_source_state_discriminators_skip_repair_round_when_state_is_wrong`
calls `_guard_gates_failed_repair_round` and `_guard_blocker_applied` directly with
a wrong source state and asserts both return `None`. Removing either discriminator
makes the guard proceed to the repair-round check, which refuses given the
live-record fixture, turning that test red. Both halves are observed, not
inferred: § T6's M2 removes `_guard_blocker_applied`'s read and M3 removes
`_guard_gates_failed_repair_round`'s. An earlier revision of this paragraph
claimed both were "confirmed by the T6 mutation run" when only the first had
been run; the correction is recorded here rather than silently applied.

The inert discriminators now have two independent controls: a tripwire on the
table shape that would make them load-bearing, and a direct unit test that kills
the discriminators if they are removed.

## Manual QA — the guard refused this delivery's own repair round

Observed 2026-09-24 on this spec's live run (`run_id 905c9b25…`), at wave 4 of 5
with `T5` carrying a live receipt. Firing `findings-remain` out of `CODE-REVIEW`
to apply the implementation review's findings — a real repair round, not a
fixture — produced:

```
loop-engine: stop — check --phase wave-reopen failed: repair round: wave 4 still
holds live dispatch records for: 'T5'; supersede them with `loop-cohort wave
reopen` so this round records its own
```

`loop-cohort wave reopen` then admitted the transition. Container afterwards:

| wave | record |
| --- | --- |
| 0 | `{"kind": "decline", "reason": "human-directed"}` |
| 1 | `{"kind": "receipt"}` |
| 2 | `{"kind": "receipt"}` |
| 3 | `{"kind": "receipt"}` |
| 4 | `{"kind": "receipt", "superseded": true}` |

Three properties observed at once, none of them through a test double: the edge
refuses and names the wave, the task and the clearing verb; the reopen preserves
the record rather than removing it; and waves 0 to 3 are untouched, so the
scoping is by `(digest, wave index)` and not by digest or task alone. Before this
change the transition was admitted and wave 4's exit would later have been
discharged a second time by that same first-pass receipt.

It also confirmed a review finding from the operator's seat: the verb at the time
printed `loop-cohort: wave reopen for repair-round-dispatch-assertion` and nothing
about what it had changed. That finding was addressed in T6: the verb now prints
the wave index and record count — e.g. `loop-cohort: wave reopen wave 4: 1 record(s)
superseded for repair-round-dispatch-assertion`.

## Specification errors found by the implementation review

Two acceptance criteria were wrong rather than unmet, and the owner authorised a
controlled amendment on 2026-09-24 rather than an edit.

1. **The coupling's home was impossible.** § Proof required the parity assertion
   to live in `packs/core/tests/skills/work-loop/`. A pack test may not read
   above its own pack — `tools/lint-pack-test-boundary.py` enforces it — and the
   oracle is under `docs/`, so the assertion cannot live there. It landed in
   `tests/roster/test_repair_round_predicate_parity.py` with the named
   `build-check.yml` step above the bulk pytest step, both `lint-ci-parity` axes,
   and a `.workspace-prune-protected.toml` entry. The implementation is right and
   the criterion was wrong.
2. **The oracle criterion required a tautology.** It required the oracle to
   report that the verdict "refuses on exactly those satisfying the conjunction".
   The oracle transcribes that conjunction, so comparing the two restates the
   function's own body and cannot fail. The falsifiable form of that comparison
   is against the *shipped* predicate, which is what the roster parity test does.

A third criterion, the mutation record's "no clause whose removal left the suite
green", is met by T6 adding a direct unit test for the inert discriminators rather
than by amending the criterion — the owner's decision, and the better one: it adds
coverage instead of licensing the exception.

### T6 — refusal text distinction, inert discriminators, parity row movement

Run 2026-09-24 against `_loop_guards.py` and `loop-engine.py`. Three clauses,
three reds, none survived.

| # | Clause removed | Mutation applied | Suites that turned red | Observed failure |
| --- | --- | --- | --- | --- |
| M1 | the `superseded`/`absent` categorisation in `_wave_exit_verdict` | replaced with a flat `no dispatch receipt: {bounded_id_list(unaccounted)}` | cli only | Replayed clause-by-suite 2026-09-24: `cli` **RED** — `test_wave_exit_refusal_distinguishes_superseded_from_absent`, `1 failed, 232 deselected`; `guards` green, `158 passed`; `parity` green, `5 passed`. **Two earlier revisions of this row were wrong and both are corrected here from that run.** The first recorded a parity red with `moved == 0`; the second kept the parity attribution and changed the number to 8 violations. Neither happens: the mutation changes only `GuardResult.reason`, and the parity check asserts on the shipped verdict's `ok` flag and on `unaccounted_wave_tasks` return values, never on refusal text, so it is structurally blind to this clause. The `8` in the second revision was the accounted-state count, not a violation count |
| M2 | `_guard_blocker_applied`'s source-state discriminator | `if engine_state.get("state") != "CODE-HUMAN-GATE": return None` deleted | engine | `test_inert_source_state_discriminators_skip_repair_round_when_state_is_wrong`: `_guard_blocker_applied` with `{"state": "CODE-REVIEW"}` returned the repair-round refusal text instead of `None` |
| M3 | `_guard_gates_failed_repair_round`'s source-state discriminator | `if engine_state.get("state") != "CODE-VERIFICATION": return None` deleted | engine | run 2026-09-24: `test_inert_source_state_discriminators_skip_repair_round_when_state_is_wrong` fails — `1 failed, 215 deselected`. Run because a review found this ledger asserting this result without it having been produced |

Each mutation was reverted immediately after its red was observed and the file
diffed against its pre-mutation copy (`python3 -m pytest` re-run passing) before
the next mutation began.

### T6 addendum — remaining `_repair_round_verdict` pass-clauses

Run 2026-09-24 against `_loop_guards.py`. The absent-container pass-clause (M5 in § T1) already has a row. Five remaining pass-clauses are mutated here. M2 needed a new fixture before it could be killed; the first run of it survived, and both the survival and its closure are recorded below rather than only the final state. Suites: `guards` = `test_loop_guards.py`; `parity` = `tests/roster/test_repair_round_predicate_parity.py`. Method as § T1: edit the clause, run the suite, record the failure, edit back.

| # | Clause removed | Mutation applied | Suites that turned red | Observed failure |
| --- | --- | --- | --- | --- |
| M1 | the unsupported-schema pass (`if state.get("schema_version") != SCHEMA_VERSION:`) | replaced with `if False:` | guards | `test_the_repair_round_verdict_fails_open_on_every_falsified_conjunct[unsupported schema]` — `AssertionError: unsupported schema must pass, got: repair round: wave 0 still holds live dispatch records for: 'T1'; supersede them with \`loop-cohort wave reopen\` so this round records its own` |
| M2 | the malformed-container pass (`if malformed_receipts_position(state.get(RECEIPTS_KEY)) is not None:`) | deleted | guards | **RED after the fixture was added.** The pre-existing fail-open fixture (`{RECEIPTS_KEY: {"d": []}}`) could not kill this clause: its outer key is not the live partition digest, so with the clause removed the accounting walk finds no subtree, every task reads unaccounted, `live` is empty and the verdict passes either way. The first run of this mutation therefore survived, and was recorded here as a non-detection with the fixture shape that would close it. `test_the_malformed_container_pass_clause_is_reachable_and_killable` is that fixture — the live digest holds one accounted task while a sibling digest carries a non-record leaf — and with it the mutation reports `1 failed, 157 deselected`. The clause is now falsifiable and no clause in this delivery survives its mutation |
| M3 | the malformed-schedule_waves pass (`if not isinstance(waves, list) or not waves:`) | replaced with `if False:` | parity | `test_the_verdict_agrees_over_the_whole_domain` — `KeyError: 0` from `wave = waves[index]` when `waves = {"a": 1}` (a dict in the parity domain); `guards` stayed green because its fixture uses `schedule_waves = []` and the removed clause's absence leaves the verdict passing via the pointer-range check (`0 >= len([])` → True). |
| M4 | the invalid-pointer pass (`if isinstance(index, str) or index >= len(waves):`) | replaced with `if False:` | guards | `test_the_repair_round_verdict_fails_open_on_every_falsified_conjunct[pointer past the end]` and `[pointer not an integer]` — both raise `TypeError: list indices must be integers or slices, not str` when `waves[index]` is reached with a non-int or out-of-range index. |
| M5 | the malformed-wave pass (`if not wave_is_well_formed(wave):`) | replaced with `if False:` | parity | `test_the_verdict_agrees_over_the_whole_domain` — `TypeError: 'int' object is not iterable` from `for task in wave` when `wave = 123` (an int in the parity domain's `[123]` schedule_waves entry); `guards` stayed green because its fixture uses `schedule_waves = [[]]` and `unaccounted_wave_tasks`'s own `wave_is_well_formed` check returns `[]` for an empty wave, leaving `live = []` and the verdict passing. |

Each mutation was reverted immediately after its result was observed and the file diffed against its pre-mutation copy (all relevant suites re-run passing) before the next mutation began. No `git checkout`, `git reset` or `git stash` was used at any point.


### T6 addendum 2 — clauses the reviews found unrecorded

Two review passes found three clauses T6 added with no mutation entry. Run
2026-09-24, method as above. Suites: `guards` = `test_loop_guards.py`;
`cli` = `test_loop_cohort.py`.

| # | Clause removed | Mutation applied | Result | Observed |
| --- | --- | --- | --- | --- |
| M6 | the superseded grouping in `unaccounted_breakdown` | the `if superseded:` branch deleted | **RED** | `guards` `1 failed, 160 passed`; `cli` `3 failed, 69 passed, 161 deselected` |
| M7 | `superseded_wave_tasks`' subtree-absent clause | `if not isinstance(held, dict): return []` deleted | **RED** | `guards` `4 failed, 157 passed`; `cli` `2 failed, 70 passed, 161 deselected` |
| M8 | `plan_wave_reopen`'s idempotence clause | `if record.get(SUPERSEDED_KEY) is not True:` → `if True:` | **survived, then RED** | First run: no suite turned red. The clause skips an already-superseded record and counts only what it marks, and the resulting state is identical either way, so the only observable difference is the verb's success line — which every call site discarded into `_` — 9 of them, counted by `grep -c 'run_cohort("wave", "reopen"' packs/core/tests/skills/work-loop/test_loop_cohort.py` at the time. `test_wave_reopen_reports_the_wave_and_the_count_it_superseded` asserts the wave index and the count, including zero on a second reopen; with it the mutation reports `1 failed, 233 deselected` |

M8 is the second clause in this delivery whose first mutation survived, and the
pattern is the same as the malformed-container one: **a clause whose only effect
is on output nothing asserts cannot be killed, however carefully the code is
reviewed.** Both are recorded with their survival rather than only their closure.

### A correction this ledger had to make twice

The M1 row was wrong in two successive revisions — first recording a parity red
with `moved == 0`, then keeping the parity attribution and changing the figure to
8 violations. Neither run produces either. The mutation changes only
`GuardResult.reason`, and the parity check asserts on the shipped verdict's `ok`
flag and on `unaccounted_wave_tasks` return values, so it is structurally blind
to it; the second revision's `8` was the unmutated accounted-state count.

The lesson is about how a wrong claim gets corrected, not about this row: the
first correction fixed the number the reviewer flagged and inherited the suite
attribution unchecked. **Re-derive the whole claim from a run, not the part that
was challenged.**


## A finding refuted, and why two reviewers reached it

Both final-pass reviewers reported that `evals.json` carries unrelated encoding
churn — one counted 35 changed lines, the other 72 — and both asked for it to be
reverted or declared as a ride-along.

It is already reverted. Re-measured after the 2026-09-24 rebase, against the
current merge-base `b59becf264` — the earlier version of this table named the
pre-rebase base `ba76d833c` and labelled a line count as a character count, so
neither side reproduced:

| Measure | command | merge-base | HEAD |
| --- | --- | --- | --- |
| lines changed, all three copies | `git diff --stat $(git merge-base HEAD origin/main)..HEAD -- '*evals/evals.json'` | — | `3 files changed, 36 insertions(+)` |
| literal `—` characters, `.apm/` copy | `grep -o '—' <file> \| wc -l` | 45 | 45 |
| `\u2014` escapes, `.apm/` copy | `grep -o 'u2014' <file> \| wc -l` | 0 | 0 |

Thirty-six insertions is the twelve-line repair-round entry in each of the three
copies, and nothing else. Both reviewers were given `27cff5b78..HEAD` as their
range, and that window *contains* the revert of the re-encoding an earlier task
introduced — so the revert itself appears in the diff as changed lines and reads
as the churn.

Recorded because the mistake is easy to repeat and is not the reviewers': **a
two-SHA range is a window, not a net change.** A finding about what a delivery
ships has to be measured against the merge-base, whatever range the review was
scoped to.

### T6 addendum 3 — the last un-reviewed range

A final pass over the commits no reviewer had seen found three clauses or claims
that could not hold. Run 2026-09-24.

| # | Subject | Disposition |
| --- | --- | --- |
| A | `unaccounted_breakdown`'s `if not unaccounted: return ""` | **Deleted.** It changed no output for any state — an empty list forces `superseded` and `absent` empty and `"; ".join([])` is already `""` — so the clause was unkillable and its test stayed green without it. Removing it is what keeps § Proof's no-survivors criterion true |
| B | `superseded_wave_tasks`' docstring naming the parity check as what catches its walk drifting | **The control now exists.** It did not: the parity file had no reference to that function. `test_superseded_wave_tasks_is_a_subset_of_unaccounted` drives `set(superseded) <= set(unaccounted)` over the whole domain and asserts the superseded list is non-empty somewhere, so the subset claim is not satisfied by a function that always returns nothing |
| C | `test_both_consumers_render_one_state_identically` | **Renamed and split.** It asserted one consumer while its name and comment claimed two. The wave-exit half keeps the guards-level assertion under an honest name; `wave advance`'s half is pinned at the CLI, where that refusal is observable, by comparing its output against `unaccounted_breakdown`'s fragment for the same state |

All three are the delivery's own recurring class — a clause that cannot fail, and
a comment asserting a property its artifact does not have. That class appeared in
the oracle, twice in this ledger, in a guard docstring, and in three test
docstrings. What caught it every time was a reviewer reading the claim against
the artifact, never a green suite.
