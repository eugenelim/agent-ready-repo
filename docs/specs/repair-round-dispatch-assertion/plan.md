# Plan: repair-round dispatch assertion

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/loop-infrastructure.md` §§ 3, 4, 6 (write authority, the two lock domains, the wave-exit verdict's serialisation residual); `packs/AGENTS.md` (pack export boundary, version bump rule, no internal-governance citations in shipped prose); analogous implementations — `_wave_exit_verdict` and `check_phase` in `_loop_guards.py`, `cmd_wave_advance` and `plan_dispatch_receipt` in `loop-cohort.py`, and `_guard_check_spec_status_on_code_review` in `loop-engine.py` for the source-state discriminator; their tests — `test_loop_guards.py`, `test_loop_cohort.py`, `test_loop_engine.py` under `packs/core/tests/skills/work-loop/`; construction path — `_GUARDS` in `loop-engine.py`, `PHASES` and `_SCHEMA_EXEMPT_PHASES` for the new phase. Named uncertainty: the controller-facing site set is discovered by search in T4, not enumerated here, because a list written now would be the failure it exists to prevent.

## Approach

The round is scoped by **emptiness**, not by a counter. A wave whose record
subtree holds nothing has, by construction, no assertion that could discharge
its exit, so the existing accounting predicate does all the enforcing and gains
no new input. Two pieces make that hold: a skill-invoked verb that empties the
current wave's subtree, and a guard on each re-entry edge that refuses while the
subtree is non-empty. Neither is useful alone — the verb without the guard is
optional, and the guard without the verb is a dead end.

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
| Maintainer procedure | T4 | the site set is a search result, and the search expression is committed with the test |
| Verification evidence | T1, T2, T3 | each task appends its own mutation entries as it lands, rather than one task writing all of them afterwards |
| Interface compatibility | T5 | — |
| Release history | T5 | — |
| Reusable learning | T4 | — |

## Design (LLD)

### Design decisions

**Emptiness over a counter.** A round counter would need a new cohort key, a
round stamp inside every record, and a comparison inside `unaccounted_wave_tasks`
— which moves the wave-exit verdict's accounted and unaccounted rows. Emptiness
needs none of those, and it leaves that verdict's eight rows deciding exactly
what they decide today. What it costs is per-round history, accepted by the
owner on 2026-09-23 and recorded as a follow-on against `loop-parallelism.md` § 1.

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

**Tests:** TDD. Discharges the five criteria under § The repair-round verdict,
all four under § Proof, and the accounting change the § The reopen verb group
depends on.

- The predicate change lands first and alone: `unaccounted_wave_tasks` returns a
  task whose only record is superseded. Both consumers are asserted, the wave
  exit and `wave advance`'s advancing branch, because the predicate is shared
  and a change that reached one consumer only is the defect this repository has
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
- `notes/walk_reopen_partition.py`: domain built from the axis list
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

### T2: reopening a wave empties that wave alone and keeps the container

**Depends on:** T1

**Tests:** TDD. Discharges the five criteria under § The reopen verb.

- The multi-wave, multi-digest fixture proves the survivors; the single-wave,
  single-digest fixture is the one that matters for the container invariant,
  because only there does the container collapse to empty.
- The post-reopen wave-exit case drives `check --phase wave-exit` rather than
  inspecting state, so the assertion is on the refusal the controller sees.
- Each refusal case asserts the file digest before and after, not just the exit
  code.

**Done when:** those cases are green, `loop-cohort wave reopen --help` lists the
verb, and this task's mutation entries are in `notes/verification-ledger.md`.

### T3: the three edges refuse until the wave is reopened, and nothing else does

**Depends on:** T2

**Tests:** TDD, driven through `loop-engine transition` against a real spec
directory rather than the guard function. Discharges the five criteria under
§ The three edges.

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

**Tests:** goal-based check. Discharges the four criteria under § Controller-facing
surfaces.

- The site predicate is **fenced command blocks**, not prose: the check parses
  fenced blocks under the skill tree, selects those invoking `loop-engine.py
  transition` with one of the three edges, and asserts each contains a
  `wave reopen` invocation on an earlier line. Prose that names an edge
  descriptively — `references/capture.md`, `references/state-schema.md`'s
  `last_event` vocabulary — is not a firing site and is correctly excluded,
  which is why the predicate is blocks rather than a grep for the literal.
- A presence assertion pairs with the quantifier, naming `SKILL.md`,
  `references/full-mode-engine.md` and `references/session-resumption.md`, so the
  universal cannot pass at zero blocks.
- `make build-self` reports three-copy parity across `.apm/`, `.claude/` and
  `.agents/`.

**Done when:** `packs/core/tests/pack/` is green and the parity check reports
three matching copies.

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
  assert, and by T4's count check catching an undocumented route.
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
- 2026-09-23 — revised from the round-2 adversarial review: the reopen supersedes
  rather than removes, because a frozen `Never do` names the only three paths
  that may remove a record; the site predicate became fenced command blocks; and
  `wave-passed` moved to a follow-on with the claims narrowed to three edges.
