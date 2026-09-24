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
  replaces it with properties measured against the shipped code: a read refusal
  never reaches the verdict; every refusal names a live record read from the
  container; superseding clears every `_repair_round_verdict` refusal; only R7
  moves at the wave exit (to R8), and no other row moves; and both sides of
  the predicate are non-empty in the domain. (`test_wave_exit_row_movement_from_superseding`
  and `test_wave_reopen_check_is_read_only` carry the last two.)
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
was used at any point. `gates-failed`'s own source-state discriminator
(`_guard_gates_failed_repair_round`, mirroring M6) was not separately mutated:
`gates-failed` has exactly one source state in `_CODE_TRANSITIONS` today, the
same non-detection M6 already establishes and explains, so a second run of the
identical result would add no information.

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
makes the guard proceed to the repair-round check, which refuses given the live-record
fixture, turning that test red (confirmed by the T6 mutation run; see § T6 below).

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

Run 2026-09-24 against `_loop_guards.py` and `loop-engine.py`. Two new clauses,
two reds, none survived.

| # | Clause removed | Mutation applied | Suites that turned red | Observed failure |
| --- | --- | --- | --- | --- |
| M1 | `superseded_wave_tasks` categorization in `_wave_exit_verdict` | replaced with flat `"no dispatch receipt: {bounded_id_list(unaccounted)}"` | cli, parity | cli: `test_wave_exit_refusal_distinguishes_superseded_from_absent` — the superseded case rendered identically to the absent case; parity: `test_wave_exit_row_movement_from_superseding` — `_shipped_row` returned `"unknown"` for superseded states because the reason text no longer contained the expected discriminating strings, so `moved == 0` |
| M2 | `_guard_blocker_applied`'s source-state discriminator | `if engine_state.get("state") != "CODE-HUMAN-GATE": return None` deleted | engine | `test_inert_source_state_discriminators_skip_repair_round_when_state_is_wrong`: `_guard_blocker_applied` with `{"state": "CODE-REVIEW"}` returned the repair-round refusal text instead of `None` |

Each mutation was reverted immediately after its red was observed and the file
diffed against its pre-mutation copy (`python3 -m pytest` re-run passing) before
the next mutation began.
