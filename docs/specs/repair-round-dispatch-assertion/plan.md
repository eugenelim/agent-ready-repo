# Plan: repair-round dispatch assertion

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/loop-infrastructure.md` §§ 3, 4, 6 (write authority, the two lock domains, the wave-exit verdict's serialisation residual); `packs/AGENTS.md` (pack export boundary, version bump rule, no internal-governance citations in shipped prose); analogous implementations — `_wave_exit_verdict` and `check_phase` in `_loop_guards.py`, `cmd_wave_advance` and `plan_dispatch_receipt` in `loop-cohort.py`, and `_guard_check_spec_status_on_code_review` in `loop-engine.py` for the source-state discriminator; their tests — `test_loop_guards.py`, `test_loop_cohort.py`, `test_loop_engine.py` under `packs/core/tests/skills/work-loop/`; construction path — `_GUARDS` in `loop-engine.py`, `PHASES` and `_SCHEMA_EXEMPT_PHASES` for the new phase. Named uncertainty: none outstanding. The controller-facing site set was surveyed on 2026-09-23 and is enumerated in T4; the obligation it carries is demoted working material rather than contract, and § Design (LLD) records why.

## Approach

The round is scoped by **supersession**, not by a counter and not by deletion. A
record marked superseded stays on disk and stays a valid record, and stops
accounting for its task. Three pieces make that hold: one clause in the shared
accounting predicate, a skill-invoked verb that marks the current wave's records,
and a guard on each of the three named edges that refuses while any record there
is still live. None is useful alone — the clause without the verb marks nothing,
the verb without the guard is optional, and the guard without the verb is a dead
end.

## Constraints

- ADR-0061 Option A: a transition permits a change and never causes one. The
  reopen is therefore a `loop-cohort` verb the controller runs *before* firing
  the edge, and the guard reads the state that verb left behind.
- `SCHEMA_VERSION` does not move, and no key is added to cohort `state.json`
  (owner decision, 2026-09-23).
- `wave-complete-dispatch-receipts` § Ask first requires sign-off for scoping a
  record to a repair round and for any change to the review-phase guards. The
  owner granted both on 2026-09-23. That spec's § Never do is not reachable by
  sign-off, and two of its rules bind here: `check --phase implement` is not
  approached, and no record is removed — the reopen supersedes.
- `packs/` prose carries no citation of this repository's internal records, so
  the skill text states the obligation directly and never names this spec.
- The stash stack is shared across worktrees: every mutation proof restores by
  editing the source back, never by `git checkout`, `reset`, or `stash`.

## Construction tests

Every suite already exists; this change extends them rather than adding a
directory. T1 → `test_loop_guards.py` plus the new oracle in this spec's
`notes/`; T2 → `test_loop_cohort.py`; T3 → `test_loop_engine.py`; T4 →
`packs/core/tests/pack/`. Paths under `packs/core/tests/skills/work-loop/`
except the last.

## Durable-output map

| Spec durable output | Task | Construction detail the spec does not carry |
| --- | --- | --- |
| Current architecture | T5 | the edge list goes in § 4 beside the allowed-edges table, not § 6 |
| Interface documentation | T4, sole owner | the `dispatch_receipts` row is edited in the same task as the prose it has to agree with; T1 changes the predicate but writes no documentation |
| Maintainer procedure | T4 | demoted working material: T4 writes the prose and the pack suite pins it, and no criterion reads it |
| Verification evidence | T1, T2, T3 | each task appends its own mutation entries as it lands, rather than one task writing all of them afterwards |
| Interface compatibility | T5 | — |
| Release history | T5 | — |
| Reusable learning | T4 | — |

## Design (LLD)

### Design decisions

**A boolean over a counter.** Both designs put a comparison inside
`unaccounted_wave_tasks`, so neither leaves the wave-exit verdict's accounted and
unaccounted rows deciding what they decide today: a wave whose records are all
superseded now reaches the unaccounted row, and that movement is a criterion
rather than a side effect. What separates them is cost. A counter needs a new
cohort key on a triplicated `SCHEMA_VERSION`, a round stamp written by the
recording verb, and a comparison against a second field the guard must also
validate; supersession needs one member with an absence rule and one clause. The
rows move either way, so the reason to prefer the boolean is that it moves them
with the smallest reachable surface. What it costs is per-round history, accepted
by the owner on 2026-09-23 and recorded as a follow-on against
`loop-parallelism.md` § 1.

**The reopen supersedes; it never removes.** `wave-complete-dispatch-receipts`
§ Never do names the only three paths that may remove a record — a `schedule`
run under a different partition, a contract amendment, and `loop-cohort reset`
— and that rule is not reachable by sign-off, so a deleting reopen would be a
fourth. Marking instead keeps every record present and `is_dispatch_record`-valid,
and moves the round scoping into the shared accounting predicate, which is where
`wave-complete-dispatch-receipts` § Always do already requires this class of
exemption to live.

Deletion was also the shape most likely to be built into a bypass. Probed
against the shipped predicates on 2026-09-23: removing a wave's subtree leaves
the sibling wave's records intact and turns the wave-exit verdict from passing
to refusing by name, but removing the `dispatch_receipts` key itself leaves that
verdict *passing*, because `unaccounted_wave_tasks` returns no tasks for an
absent container. An implementer pruning now-empty parents would have disabled
enforcement while appearing to demand it. Superseding cannot reach that state at
all.

**One clause, inside the shared predicate.** `unaccounted_wave_tasks` is the
declared accounting predicate for both the wave exit and `wave advance`'s
advancing branch, so adding the superseded clause there is what keeps the two
consumers agreeing. It also means a reopen correctly blocks a `wave advance`
until the round re-records.

**The guard is decided by the engine's source state, never by the run mode.**
`_GUARDS` is keyed `(mode, event)` and dispatched at `loop-engine.py:1759`, and
`_CODE_TRANSITIONS` splats in `_BOTH_TRANSITIONS`, so a code-mode run sitting in
`SPEC-PLAN-REVIEW` dispatches `findings-remain` through `("code",
"findings-remain")` — the same entry `CODE-REVIEW` uses. That state is reached
at the start of every code run and again after `contract-amendment`, where
`begin_contract_amendment` writes `schedule_waves: []`. The guard therefore
reads `engine_state["state"]` and applies the repair-round check only at
`CODE-VERIFICATION`, `CODE-REVIEW` and `CODE-HUMAN-GATE`, the way
`_guard_check_spec_status_on_code_review` already discriminates the twin-sourced
`reviewers-clean` edge.

**The verdict fails open.** It refuses only when it can positively establish
that a record remains for the current wave; every state it cannot read that far
passes. Mirroring the wave-exit verdict's refusals instead would make a
malformed partition refuse at both the edge and the verb, stranding a run that
re-enters implementation today and leaving only the destructive reset pair. The
wave-exit verdict stays the fail-closed gate; this one only demands a reopen
where a stale record could actually discharge something.

**Composition order is existing guard first.** `gates-failed` and
`findings-remain` already carry a retry-cap guard. The repair-round check runs
second, so a state failing both is refused with the reason it is refused with
today and no caller-visible message changes.

**The new phase joins `_SCHEMA_EXEMPT_PHASES`.** `check_phase` refuses any
non-exempt phase on a schema mismatch at `_loop_guards.py:1514`, before the
phase dispatch below it. Without membership, the verdict's own pass-on-
unsupported-schema behaviour is unreachable through the CLI while every test
that drives the verdict function directly stays green — the divergence the
criterion exercising the exemption through `check --phase wave-reopen` exists
to catch.

**The documented procedure is demoted, not dropped.** Three criterion forms
failed to mechanise "this prose instructs a reader to fire this edge", so on
2026-09-23 the owner removed the obligation from the contract. It lives here
instead, and T4 produces it against the survey table below; a content test in
`packs/core/tests/pack/` pins the resulting prose so its removal reds a suite.
What is given up is stated plainly: no completion gate reads it, so a future
edit that drops the reopen from one block fails a pack test rather than a
delivery criterion.

### Data & schema

No key is added, renamed, or removed, and no record is deleted. The only write
adds a `superseded` member to records already present, under the cohort lock,
through the existing atomic write. A record without that member reads as live,
so every `state.json` on disk today means exactly what it means now.

### Interfaces & contracts

Three surfaces gain a value: a `reopen` verb under the existing `wave`
subparser, `wave-reopen` in `PHASES`, and `wave-reopen` in
`_SCHEMA_EXEMPT_PHASES`. All three are additive — no existing verb, phase, flag,
or message changes.

### Failure, edge cases & resilience

The verb is idempotent and destroys nothing, so re-running it always closes the
window between "reopen landed" and "transition fired". What the window costs
depends on which forward exit the resuming session takes instead, and all three
source states have more than one:

| Source state | Other forward exits | Cost of an orphaned reopen |
| --- | --- | --- |
| `CODE-VERIFICATION` | `wave-passed`, `gates-clean` | `wave advance` refuses the now-superseded wave until it is re-recorded; `gates-clean` reaches review with the wave superseded, and the next wave exit refuses |
| `CODE-REVIEW` | `reviewers-clean` | reaches the human gate with the wave superseded; the next exit refuses |
| `CODE-HUMAN-GATE` | `done` | the run ends; the superseded records survive but no exit re-examines them |

Every cell is a refusal or a re-record, never a silent pass — which is the
property that matters, and it holds because superseding is monotone: it can only
make an exit stricter. That is the concrete gain over the deleting design, where
the `done` row lost the records outright.

### Dependencies & integration

None added. The verb reuses `_locked`, `read_state`, `write_state_atomic`,
`_validate_run_id`, `partition_digest`, `non_negative_int`,
`malformed_receipts_position`, and `wave_is_well_formed`.

## Tasks

### T1: a superseded record accounts for nothing, and the verdict refuses on exactly the live ones

**Depends on:** none

**Tests:** TDD. Discharges § The repair-round verdict entire; the `wave advance`,
refusal-wording and absence-rule criteria of § The accounting predicate; and the
three oracle criteria of § Proof. The `references/state-schema.md` criterion
belongs to T4, the task that writes documentation, and § Proof's mutation-record
criterion is closed jointly by T1, T2 and T3, each appending its own entries.

- The predicate change lands first and alone: `unaccounted_wave_tasks` returns a
  task whose only record is superseded, and does not return one whose record
  carries no `superseded` member — the backward-compatibility half, driven from a
  fixture written in the pre-change shape. Both consumers are asserted, the wave
  exit and `wave advance`'s advancing branch, because the predicate is shared and
  a change that reached one consumer only is the defect this repository has
  already paid for once.
- One case per conjunct of the verdict's refusal condition, each falsifying that
  conjunct alone and asserting a pass; plus the all-conjuncts-true case
  asserting the refusal and its text.
- The read-refusal case asserts the verdict is never reached, by driving an
  unreadable `state.json` through `cmd_check` and comparing the reason against
  the one `--phase wave-exit` gives for the same file.
- The CLI-level exemption case drives `check --phase wave-reopen` through
  `cmd_check` against an unsupported `schema_version`, not the verdict function,
  because that is the only surface where `_SCHEMA_EXEMPT_PHASES` is observable.
- `notes/walk_reopen_partition.py` imports `_loop_guards` and calls the shipped
  `unaccounted_wave_tasks` and verdict functions, so the walk moves when the code
  moves. The frozen walk is read, run and compared — never edited; it transcribes
  another spec's words and this spec has no standing over it.
- That oracle's domain is built from the axis list
  `wave-complete-dispatch-receipts` § Acceptance Criteria declares canonical
  plus a superseded axis over each record, container values generated from
  `RECEIPT_KEY_PATH` rather than hand-built, asserting refusal ⟺ the conjunction,
  byte-identical `state.json` across every invocation, and the `_wave_exit_verdict`
  row each state reaches.
- The frozen wave-exit oracle's report is compared field by field against the
  baseline in § Proof. Its domain carries no superseded axis, so it cannot see
  this change — which is why the new oracle reports wave-exit rows too, and why
  an unchanged frozen report is evidence of no regression rather than evidence
  of coverage.

Red contract-surface assertion (`stub: true`):

```python
def test_repair_round_verdict_refuses_while_a_record_remains():
    guards = _load_guards()
    state = _cohort_state(waves=[["T1"]], receipts={"T1": {"kind": "receipt"}})
    result = guards._repair_round_verdict(state)
    assert result.ok is False
    assert "wave reopen" in result.reason
```

**Approach:**
- The verdict lands before the verb and the guard entries, because both consume
  it and neither can be written against a predicate that does not exist.

**Done when:** the conjunct cases, the CLI exemption case and both oracles are
green, `wave-reopen` is in `PHASES` and in `_SCHEMA_EXEMPT_PHASES`, and this
task's mutation entries are in `notes/verification-ledger.md`.

### T2: reopening a wave supersedes that wave's records and touches nothing else

**Depends on:** T1

**Tests:** TDD. Discharges § The reopen verb entire.

- The multi-wave, multi-digest fixture proves the survivors: a record under
  another wave index or another digest is untouched, and so is every other key.
  It is the only fixture shape that can catch a verb that marks by digest or by
  task id instead of by the (digest, wave index) pair.
- The post-reopen wave-exit case drives `check --phase wave-exit` rather than
  inspecting state, so the assertion is on the refusal the controller sees.
- Each refusal case asserts the file digest before and after, not just the exit
  code.

**Done when:** those cases are green, `loop-cohort wave reopen --help` lists the
verb, and this task's mutation entries are in `notes/verification-ledger.md`.

### T3: the three edges refuse until the wave is reopened, and nothing else does

**Depends on:** T2

**Tests:** TDD, driven through `loop-engine transition` against a real spec
directory rather than the guard function. Discharges § The three edges entire.

- Three separate cases drive a real repair round to `CODE-IMPLEMENTATION`, one
  per edge, each asserting the refusal text before the reopen and the
  transition after it.
- `wave-passed` and `gates-clean` are driven from the same `CODE-VERIFICATION`
  state that refuses `gates-failed`, asserting both are admitted with their
  reasons unchanged — the case that pins the source-state-plus-event
  discrimination rather than source state alone.
- The code-mode `SPEC-PLAN-REVIEW` case is driven twice: on a fresh run, and
  after a `contract-amendment` has written `schedule_waves: []`.
- The conjunct-admission case reuses T1's falsifying states, driven through the
  engine so the source-state discriminator is exercised rather than assumed.
- The composition-order case asserts the retry-cap reason, and the override case
  asserts that `--allow-retry-cap-override` does not reach the repair-round
  check.

**Done when:** those cases are green, `make lint-ruff lint-mypy` passes, and
this task's mutation entries are in `notes/verification-ledger.md`.

### T4: every documented route to the three edges runs the reopen first

**Depends on:** T3

**Tests:** goal-based check. Discharges the `references/state-schema.md`
criterion of § The accounting predicate, and produces the demoted maintainer
procedure and its content pin.

- The site set is an enumeration, not a search result. The survey that produced
  it, run 2026-09-23 over the shipped tree, found seven fenced blocks invoking
  `loop-engine.py transition` with one of the three edge names, in three files:

  | Block | Edge | Fires from | Reopen |
  | --- | --- | --- | --- |
  | `full-mode-engine.md` § PLAN pre-EXECUTE | `findings-remain` | `SPEC-PLAN-REVIEW` | no |
  | `full-mode-engine.md` § GATES wave routing | `gates-failed` | `CODE-VERIFICATION` | yes |
  | `full-mode-engine.md` § REVIEW, changes requested | `blocker-applied` | `CODE-HUMAN-GATE` | yes |
  | `full-mode-engine.md` § REVIEW, specialist findings | `findings-remain` | `CODE-REVIEW` | yes |
  | `finding-adjudication.md`, two blocks | `findings-remain` | either review phase | conditional |
  | `pre-execute-review.md` | `findings-remain` | `SPEC-PLAN-REVIEW` | no |

- The content pin asserts each row's expected outcome by locating the block, and
  counts `loop-engine.py transition` *invocations* naming one of the three edges
  rather than blocks — two blocks already name a second edge in comment lines, so
  a block count can stay at seven while an unguarded firing line is added.
- Prose that names an edge without firing it — `references/capture.md`'s routing
  sentence, `references/state-schema.md`'s `last_event` vocabulary — is not a
  firing site and is outside the count, which is why the predicate is fenced
  blocks and not a grep for the literal.
- `SKILL.md` and `references/session-resumption.md` hold no fenced transition
  block. `session-resumption.md`'s row that instructs a controller to fire one of
  the three edges is the `wave-complete` / `CODE-VERIFICATION` row, which says
  "fire `wave-passed` or `gates-clean` or `gates-failed`"; the `gates-failed` and
  `findings-remain` rows are keyed on the event already fired and re-issue a
  cohort record, so they are not firing sites.
- `references/state-schema.md`'s `dispatch_receipts` row is edited here, because
  the row and the procedure prose have to agree and a reader meets them together.
- `make build-self` reports three-copy parity across `.apm/`, `.claude/` and
  `.agents/`.

- The `evals/evals.json` entry covering the repair-round obligation is written
  here, because `packs/AGENTS.md` requires a non-cosmetic pack update to update
  that pack's eval harness. Nothing runs it; it is a contract record and is never
  counted as verification.

**Done when:** `packs/core/tests/pack/` is green, `references/state-schema.md`'s
`dispatch_receipts` row describes the `superseded` member and its absence rule,
the eval entry exists, and the parity check reports three matching copies.

### T5: the release surface and the architecture record agree with the code

**Depends on:** T4

**Tests:** goal-based check.

- `pack.toml` and `.claude-plugin/plugin.json` carry the same version, one patch
  above the merge-base computed from a fresh `git fetch origin`.
- `docs/product/changelog.md` carries one `## [core][x.y.z]` heading for this
  branch, topmost beneath `[Unreleased]`, one blank line above and below.
- `docs/architecture/loop-infrastructure.md` § 4 names the reopen obligation and
  the three edges carrying it.

**Done when:** `lint-spec-status.py --root .` is clean and the three version
surfaces agree.

## Rollout

Big bang, reversible by reverting the branch. No infrastructure, no external
system, no deployment sequencing: the change ships inside a pack whose consumers
re-read the scripts on next invocation. An in-flight run on disk keeps working —
it meets the new refusal only at its next repair round, and clears it by running
one verb.

## Risks

- **A controller that has not read the new prose meets an unexplained refusal.**
  Mitigated by the refusal naming the verb that clears it, which T1 and T3
  assert, and by T4's invocation count, which fails when a firing line is added
  without being classified.
- **The shared accounting predicate has two consumers**, and a change tested
  through one only would leave `wave advance` disagreeing with the wave exit.
  Mitigated by T1 asserting both consumers in the same task that changes the
  predicate.
- **The projections are rebuilt without the source edit**, deleting the change.
  Mitigated by T4's parity check; the skill has no seed under
  `packs/core/seeds/`, so `.apm/` is the only source.
- **`wave-passed` has this defect's shape and is out of scope.** It fires before
  its cohort advance, so a controller that skips the advance re-enters at the
  same wave with live records. Not mitigated here; § Follow-ons carries it for
  its own register entry, and the criteria are scoped to three named edges so
  the contract does not claim otherwise.

## Changelog

- 2026-09-23 — drafted.
- 2026-09-23 — revised from the spec-stage shaping and adversarial reviews: the
  guard is discriminated by source state rather than run mode, the verdict fails
  open, and the oracle's domain is sourced from the frozen spec's declared axes.
- 2026-09-23 — round-5 repairs: the frozen oracle is read and never edited, task
  ownership was made one-to-one, and the eval entry regained a producing step.
- 2026-09-23 — the owner demoted the controller-facing-surfaces obligation from
  contract to working material after three criterion forms failed to mechanise
  it; the remaining round-4 findings were repaired.
- 2026-09-23 — revised from the round-3 adversarial review: the prose left
  describing the removal mechanism was brought to the superseding one, the
  controller-facing site set became an enumeration with a count tripwire, and
  `wave advance` and `references/state-schema.md` gained the criteria the
  predicate change owes them.
- 2026-09-23 — revised from the round-2 adversarial review: the reopen supersedes
  rather than removes, because a frozen `Never do` names the only three paths
  that may remove a record; the site predicate became fenced command blocks; and
  `wave-passed` moved to a follow-on with the claims narrowed to three edges.
