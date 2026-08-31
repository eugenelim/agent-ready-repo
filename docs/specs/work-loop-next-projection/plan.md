# Plan: work-loop-next-projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Ownership source: `docs/architecture/loop-infrastructure.md` §2-3 assigns the
    state machine and write authority to `loop-engine.py` and every cohort
    counter to `loop-cohort.py`. `packs/AGENTS.md` §Version bump rule and
    §Shipped pack content own the release and portability constraints.
  - Analogous implementation 1 — a read-only JSON-emitting engine verb:
    `loop-engine.py:1160-1181` (`cmd_status`); its resolve → read → schema-check →
    `json.dumps` shape, and its stderr-only `stop` at `:947-949`. Tests:
    `packs/core/tests/skills/work-loop/test_loop_engine.py:2350-2360`.
  - Analogous implementation 2 — id-keyed idempotency with form validation:
    `loop-cohort.py:1536-1581` (`cmd_record_attempt`), form check at
    `:1552-1565`. Tests: the crash-window block from `test_loop_engine.py:2232`.
  - Analogous implementation 3 — the schema field shape a JSON payload contract
    follows: `contracts/jsonschema/semantic-surface-resolution.schema.json`,
    validated from `tests/roster/`.
  - Named uncertainty: none material. Every seam is grounded in the anchors
    above and the vocabularies below.

## Approach

The projection is a pure function of engine state, cohort state, and artifact
statuses. Purity is what lets a test enumerate the input set and what makes the
read-only guarantee checkable by digest. It reads engine state through the
engine's own reader and cohort state through the shared guard API, so no new
reader of either file appears.

Four record fields carry the loop rather than describe it, and each is derived
rather than authored: `run_id` and `sequence` from the engine's state,
`complete_with` from the transition table's outgoing edges, and `human_wait` from
the wait-state set plus the destructive-action set. Deriving them is what stops an
emitter from satisfying the contract with constants.

The record carries identifiers and scalars only. Every human-readable reason —
including a stop's reason and the reset a terminal record names — goes to stderr.
That is why the record needs no message key and no path-shaped value, and why the
nine keys are enough.

The operation id makes the recording state decidable. Recorded means the write
happened; absent means it did not, once every shipped invocation passes the flag.
The projection stops on absent rather than recording, because it cannot know the
round's warranted reviewer roster.

The engine repairs its own crash artifacts only inside its writing verbs. A
read-only verb must therefore detect an unpromoted temporary state file or an
unreplayed pending-events file and stop, rather than answer confidently from
state that is mid-write.

## Constraints

- Neither state file changes owner.
- One Python process per invocation; `test_loop_engine_no_child_python.py`
  enforces this for the engine.
- No runtime dependency is added to any shipped pack script.
- No task edits `packages/agentbundle/`. The protected-tree gate at
  `tools/repo/build_gate_chain.py:305` requires an engine-scoped RFC trailer for
  that tree, and nothing here needs it.
- A pack test may not read above its own pack
  (`tools/lint-pack-test-boundary.py`), so anything reading `contracts/` is a
  `tests/roster/` test and anything reading only `packs/core/**` is a pack test.
- `packs/core/tests/skills/work-loop/` (`Makefile:544`) and `tests/roster/` (via
  `pytest tests/` at `Makefile:529`) already run in `make test`; neither needs new
  CI wiring.
- The changelog entry ships in this change, because `contracts/` is
  release-impacting.
- `pytest` and `make build-check` cannot run concurrently in this tree; gate runs
  are serialized.
- `spec.md` and `plan.md` are hashed file-wide once approved. Every enumeration an
  implementer needs is in this plan; no task authors one mid-execution.
- A peer session is active in this repository's skill tree; re-check
  `packs/core/.apm/skills/work-loop/` for landed changes before T7 and T12.

## Vocabularies

These four enumerations are the closed sets the criteria quantify over. They are
here, not in `spec.md`, because they are mechanism the criteria reference.

### Action identifiers

| Identifier | Kind | Meaning |
| --- | --- | --- |
| `spec.draft` | agent | Draft or revise the spec and plan |
| `spec.review` | agent | Run the fired pre-EXECUTE reviewers |
| `engine.spec-ready` | command | Fire `spec-ready` |
| `engine.spec-approved` | command | Fire `spec-approved` |
| `engine.plan-approved` | command | Fire `plan-approved` |
| `engine.plan-locked` | command | Fire `plan-locked` |
| `engine.wave-passed` | command | Fire `wave-passed` |
| `engine.gates-clean` | command | Fire `gates-clean` |
| `engine.done` | command | Fire `done` |
| `cohort.approve-plan` | command | Record the approved baseline |
| `cohort.schedule` | command | Schedule waves |
| `cohort.wave-advance` | command | Advance the wave pointer |
| `cohort.record-attempt` | command | Record a failed implementation cycle |
| `cohort.review-record` | command | Record a review round |
| `implement` | agent | Implement the current wave's tasks |
| `run-gates` | agent | Run lint, typecheck, tests |
| `run-review` | agent | Dispatch the warranted reviewers |
| `await-spec-approval` | wait | Spec approver decides |
| `await-plan-approval` | wait | Plan approver decides |
| `await-merge-decision` | wait | Human merge decision |
| `reset-and-reinit` | done | Terminal; a later implementation request needs a reset |
| `complete` | done | Terminal; the loop finished |
| `halt` | stop | Fail closed; the stderr reason names why |

### Destructive action set

`reset-and-reinit` only. `human_wait` is true for it, and for every `wait`-kind
record. No other identifier in the table above names an operation that deletes or
overwrites durable state.

### Reference-load identifiers

One per shipped reference file: `ref:delivery-contract-lifecycle`,
`ref:finding-adjudication`, `ref:infra-verification`, `ref:pre-execute-review`,
`ref:pre-flight-failures`, `ref:review-verdict-record`, `ref:scale-with-a-tool`,
`ref:self-coverage-protocol`, `ref:self-coverage-resolve-vs-surface`,
`ref:session-resumption`, `ref:state-schema`, `ref:supervisor-mode`,
`ref:tdd-stubs`, `ref:unattended-loops`, `ref:verification-modes`. The identifier
is the reference's path under `references/` with `.md` removed and `/` replaced
by `-`, so the mapping is derivable and the test builds it by globbing.

### Per-action `parameters` keys

| Action | Keys |
| --- | --- |
| `cohort.wave-advance` | `from_index` — the engine's `last_event_context.completed_wave_index` |
| `cohort.record-attempt` | `cycle_id` — `<run_id>:<transition_sequence>` |
| `cohort.review-record` | `operation_id` — the id recorded in `state.json` on the continuation path, otherwise `<run_id>:<transition_sequence>` |
| every other action | none; `parameters` is `{}` |

### Input-set dimension applicability

| Dimension | Applies to | Values |
| --- | --- | --- |
| `spec.md` status | `SPEC-HUMAN-GATE` | `Draft`, `Approved`, `Implementing`, `Shipped`, `Archived` |
| `plan.md` status | `PLAN-HUMAN-GATE` | `Drafting`, `Approved`, `Executing`, `Done` |
| Recorded operation id | `CODE-IMPLEMENTATION`, `CODE-HUMAN-GATE` | present, absent |
| `last_review_clean_source` | `CODE-HUMAN-GATE` | present, absent |
| Wave position | code mode, `CODE-IMPLEMENTATION` and `CODE-VERIFICATION` | before the last wave, at the last wave, unscheduled |

A dimension not listed for a state contributes no cells for that state. The
resulting set is a few hundred cells, not a full cross product.

### Resumption row to action identifier

T7 writes this mapping into the shipped table's new column. Retained rows:
`reviewers-clean`/`SPEC-HUMAN-GATE` → `await-spec-approval`;
`spec-approved`/`PLAN-HUMAN-GATE` → `await-plan-approval`;
`plan-approved`/`SPEC-PLAN-APPROVED` → `cohort.approve-plan`;
`plan-locked`/`CODE-IMPLEMENTATION` → `implement`;
`plan-approved`/`CODE-IMPLEMENTATION` → `implement`;
`done`/`DONE` → `complete`;
`wave-passed`/`CODE-IMPLEMENTATION` → `cohort.wave-advance`;
`gates-failed`/`CODE-IMPLEMENTATION` → `cohort.record-attempt`;
`blocker-applied`/`CODE-IMPLEMENTATION` → `implement`;
`wave-complete`/`CODE-VERIFICATION` → `run-gates`;
`gates-clean`/`CODE-REVIEW` → `run-review`.
Superseded rows: `findings-remain`/`CODE-IMPLEMENTATION` → `cohort.review-record`
or `halt` per the recorded id; `reviewers-clean`/`CODE-HUMAN-GATE` →
`await-merge-decision`; `plan-locked`/`DONE` and `plan-approved`/`DONE` →
`reset-and-reinit`.

## Construction tests

- Every new refusal and guard carries a mutation proof: the invariant, the test
  catching its removal, the exact mutation, the expected failure.
- Enumerations are derived at runtime from shipped source, never copied. The base
  triples come from the transition tables; row parity comes from parsing the
  shipped table's action column; the load vocabulary comes from globbing
  `references/`.
- Each of the four derived fields gets a constant-value mutation: pinning
  `run_id`, `sequence`, `complete_with`, or `human_wait` to a constant must redden
  at least one case.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — the record schema | T6 | `tests/roster/` conformance over live output; `contracts/README.md` row | Schema validates real output, carries `x-spec`, inventoried |
| Current architecture — `loop-infrastructure.md` | T14 | Entrypoint section names the verb as read-only | Doc matches the shipped verb set |
| Current product truth — the skill payload | T7, T11, T12, T17 | `make build-self-dry-run` clean | Source edited, projections regenerated |
| User-facing promise — the core how-to | T15 | Adopter description of the verb and of replay | Guide describes shipped behavior |
| Operations — the QA transcripts | T16 | Two transcripts at `notes/qa-transcripts.md` | Both committed with their scope boundary |
| Release history — the changelog | T17 | Free-standing dated entry with `### Highlights` | Entry at top level; highlights projection regenerated |
| Reusable learning | T17 | `project-knowledge` receipt or recorded unavailability | Receipt recorded or unavailability named |

## Design (LLD)

### Design decisions

- `kind` separates who acts; the controller maps `action` through the closed table
  above, so no string from the record is executed.
- The record carries identifiers and scalars only. Reasons go to stderr, which is
  why a `stop` needs no message field and no path value.
- A `stop` is a zero-exit record because computing "you must stop" succeeded; a
  non-zero exit means no record could be computed.

### Data & schema

`state.json` gains the recorded operation id and a digest of the payload recorded
under it. `record-attempt`'s precedent checks the id alone, sufficient there
because its payload *is* the id; a review round's payload varies, so the digest is
what refuses a conflicting payload. Both fields are absent-tolerant on read.

### Interfaces & contracts

The schema fixes the nine-key set with `additionalProperties: false`, the `kind`
enum, the `schema_version` const, the `action` enum from the table above, and
`parameters` as a per-action conditional key set with character-class-constrained
values.

### Component / module decomposition

No new module: a new `cmd_next` plus a projection table in `loop-engine.py`, and
one new flag plus two state fields in `loop-cohort.py`.

### State & control flow

The projection never transitions. The agent reads a record, acts, fires an event
from `complete_with`, and calls it again.

### Failure, edge cases & resilience

Missing engine state with and without a light-mode marker, a mid-write crash
artifact, schema-version mismatch, run-id mismatch, an unknown state, a malformed
operation id, an absent recorded id, and an absent clean-round source each fail
closed with a distinct stable code.

### Quality attributes (NFRs)

The size bound is asserted over the input set in the suite rather than enforced
at runtime, so a future record that grows reddens CI instead of leaving a live
loop with no next action. The measured headroom is in the spec's Assumptions.

### Dependencies & integration

None added. Both suites already run in `make test`.

## Tasks

### T1: the record has a fixed shape and a clean exit convention

**Depends on:** none

**Tests:**
- Zero exit yields exactly one JSON object with the nine-key set; `kind` and
  `schema_version` are constrained (AC1, AC5, AC6).
- Non-zero exit writes nothing to stdout (AC2); no diagnostic reaches stdout on
  any path (AC3); every diagnostic and stop reason reaches stderr (AC4).
- A `stop`-kind record is emitted on a zero exit, and a command failure emits none
  (the exit convention).
- No schedule array, amendment history, or fingerprint appears (AC16).
- The subparser is registered beside the four existing verbs (AC35).
- Mutation proof: routing one reason to stdout reddens the channel case.
- `stub: true` — one compilable red assertion that the verb exits 0 and prints
  parseable JSON for a freshly initialised `code`-mode run.

**Approach:** follow `cmd_status`'s shape and its stderr-only `stop`.

**Done when:** shape, channel, and exit-convention cases are green and `--help`
lists the verb.

### T2: the four derived fields are computed, not authored

**Depends on:** T1

**Tests:**
- `run_id` equals the engine's (AC7); `sequence` equals `transition_sequence`
  (AC8).
- `complete_with` equals the outgoing event set read from the transition table at
  runtime, empty exactly for a state with no outgoing edge (AC9).
- `human_wait` equals `kind == "wait" or action in {reset-and-reinit}` (AC10).
- Mutation proofs, one per field: pinning each to a constant reddens at least one
  case.

**Done when:** four assertions green and four mutations flip.

### T3: the action vocabulary and per-action parameters are closed

**Depends on:** T1

**Tests:**
- Every emitted `action` is in the vocabulary table (AC11).
- Each action's `parameters` key set matches the per-action table exactly (AC12).
- Every value matches the character class or is an integer or boolean (AC13).
- At least one record carries non-empty `parameters` (AC15, second half).
- Mutation proof: emitting `{}` for an action that declares keys reddens its case.

**Done when:** vocabulary and key-set cases are green and the mutation flips.

### T4: the load vocabulary resolves to shipped references

**Depends on:** T1

**Tests:**
- Every emitted `load` entry is in the vocabulary, and every vocabulary entry
  resolves to a file under `references/`, with the mapping built by globbing
  rather than copied (AC14).
- At least one record carries a non-empty `load` (AC15, first half).
- Mutation proof: emitting an identifier with no matching file reddens the case.

**Done when:** both directions of the mapping are asserted and the mutation flips.

### T5: the input set is traversed and bounded

**Depends on:** T2, T3, T4, T8, T13

**Tests:**
- Build the input set at runtime from the transition tables plus the two extra
  triple sources, crossed only per the applicability table; assert no record
  exceeds 1024 bytes and pin the observed maximum against a constant held in the
  test file (AC17).

**Approach:** depends on T8 and T13 so the traversal runs against real branches
rather than placeholders.

**Done when:** the traversal covers the applicability table and the bound holds.

### T6: the published schema validates live output and is inventoried

**Depends on:** T5

**Tests:**
- `tests/roster/` conformance running the real command for one representative
  member of every `(kind, action)` pair and validating each record (AC18).
- An undeclared `parameters` key is rejected (AC19).
- `contract_version`, `x-spec`, and the `contracts/README.md` row (AC20).

**Done when:** the roster test validates live output and the inventory row exists.

### T7: the resumption table carries action identifiers and its pinned tests move with it

**Depends on:** T3

**Tests:**
- Every retained row's parsed identifier equals the projection's `action` and the
  plan's row-to-action mapping (AC21, AC22).
- The four superseded rows state this spec's behavior (AC23).
- The `reviewers-clean` row no longer asserts non-idempotency or a double
  increment (AC24).
- Mutation proof: changing one row's identifier reddens its generated case.

**Approach:**
- Add the identifier column, then rewrite the four superseded rows.
- Update the two shipped tests that pin those rows' prose,
  `packs/core/tests/skills/work-loop/test_loop_engine.py:2746` and `:2817`, in
  this task. The second's pinned phrases assert the replay is non-idempotent,
  which this spec makes false, so its assertions change rather than move.
- Re-check the peer session's activity in the skill tree before editing.

**Done when:** parity is parsed from the table, all four rows are rewritten, and
both pinned tests assert the new prose.

### T8: terminal rows and artifact-status branches route correctly

**Depends on:** T3

**Tests:**
- The two spec-plan terminal rows yield `done` with `reset-and-reinit`, and the
  stderr reason names the reset and its required confirmation (AC25).
- The code-mode terminal row yields `done` with `complete` (AC26).
- Spec-gate statuses route wait / command / stop across all five values (AC27).
- Plan-gate statuses route wait / command / stop across all four values (AC28).

**Done when:** every enumerated status value has a passing case.

### T9: the projection is read-only and fails closed

**Depends on:** T1

**Tests:**
- Digest the three mutable state files before and after; assert equality, that no
  path appears, and that none is removed (AC29).
- An unpromoted engine-state temporary file, and an unreplayed pending-events
  file, each yield `stop` naming which was found (AC30).
- Missing engine state with a light-mode marker names the legacy table (AC31);
  without one, names the ambiguity (AC32).
- Divergent run ids yield `stop` (AC33); a state neither source nor target yields
  `stop` (AC34).
- Mutation proofs: removing the crash-artifact check, the run-id comparison, and
  the unknown-state branch each make their case pass.

**Approach:** detect the two crash artifacts by a bounded read; never repair them,
because repair is a writing verb's job.

**Done when:** every case is green and all three mutations flip.

### T10: review recording is replayable, conflict-refusing, and form-validated

**Depends on:** none

**Tests:**
- Golden capture, committed before `cmd_review_record` is touched, of the stdout
  line and resulting state for each of the four flagless forms; the post-change
  test asserts against it (AC42).
- The id form is `<run_id>:<transition_sequence>` (AC36); a non-matching id exits
  non-zero changing nothing (AC37).
- A flagged first application produces the same delta as the flagless form except
  for the two new fields, for each of the four forms (AC38).
- Replay with the same payload leaves all six named fields unchanged (AC39).
- A differing payload under the same id exits non-zero leaving `state.json`
  byte-identical (AC40).
- Two rounds separated by a transition get different ids and the second
  increments `review_round_count` (AC41).
- Mutation proofs: removing the digest comparison makes the conflict case pass;
  removing the form check makes the malformed-id case pass.

**Approach:** mirror `cmd_record_attempt`'s early-return idempotency and form
validation, extended with the payload digest; validate against `--expect-run-id`,
which the verb already requires, so no new cross-file read appears. Attach the
flag outside the existing mutually exclusive group.

**Done when:** all seven cases are green and both mutations flip.

### T11: the state surfaces document the new fields

**Depends on:** T10

**Tests:**
- Both fields exist after a recorded round (AC43); the shipped reference documents
  both and the bundled template carries both (AC44).

**Done when:** template, reference, and writer agree on the field set.

### T12: every shipped recording invocation passes the flag

**Depends on:** T10

**Tests:**
- No invocation in `SKILL.md` or `references/` omits `--operation-id`, where an
  invocation is a fenced-code-block line naming the cohort script and the verb
  (AC45).
- A prose mention in a field table is not counted, proved by a fixture containing
  one.
- Mutation proof: removing the flag from one invocation reddens the check.

**Approach:** edit the invocations in `SKILL.md` and in the reference files the
check finds. `evals/evals.json` records expected transcripts and is out of scope;
the check's path list states this.

**Done when:** the check passes over the stated paths and the mutation flips.

### T13: the recording states route on the recorded id

**Depends on:** T3, T10, T12

**Tests:**
- Id recorded → the following action (AC46); id absent → `halt` whose stderr
  reason names the expected id and the artifact (AC47).
- `reviewers-clean` in `CODE-HUMAN-GATE` → `await-merge-decision` (AC48).
- The continuation with a recorded source names the matching form and carries the
  recorded id, not a freshly computed one (AC49); replaying it leaves
  `review_round_count` unchanged (AC50); with no recorded source, `halt` (AC51).
- Mutation proof: computing a fresh id on the continuation path reddens AC50.

**Done when:** all six cases are green and the mutation flips.

### T14: the architecture surface names the new verb

**Depends on:** T9

**Tests:** goal-based — `grep -n "next" docs/architecture/loop-infrastructure.md`
shows it in the verb list marked read-only (AC52).

**Approach:** edit that one owning section; the repository state-ownership table
names writers, so a read-only verb adds no row there.

**Done when:** the doc describes the shipped verb set.

### T15: adopters can drive the new behavior from the guide

**Depends on:** T13

**Tests:** goal-based — the how-to names the verb in its resumption passage
(AC53) and describes what a recorded id makes replayable (AC54).

**Approach:** rewrite the hand-driven resumption passage to the sequence adopters
now run, rather than appending the new one beside the old.

**Done when:** the guide describes shipped behavior.

### T16: the assembled route runs, including a crash and resume

**Depends on:** T7, T8, T13

**Tests:**
- Run 1: a full-mode `code`-mode loop to `DONE`, recording the action sequence,
  final engine state, and per-command exit codes (AC55).
- Run 2: interrupt between firing `findings-remain` and recording the round,
  resume, confirm a correct next action with no double increment (AC56).
- Both transcripts state what the sessions do not exercise (AC57).

**Approach:** write both to `notes/qa-transcripts.md`. Use a throwaway spec
directory, remove it afterwards, and confirm `git status` is clean. Scope
boundary: spec-plan mode, contract amendment, and the supervisor fan-out paths
are covered by unit cases and are not exercised here.

**Done when:** both transcripts are committed with their scope boundary stated.

### T17: the release surface is consistent

**Depends on:** T6, T14, T15, T16

**Tests:**
- A free-standing dated entry at `##` (AC58) with a `### Highlights` block
  (AC59); both version files read the same value, one minor above the base
  branch's (AC60); the drift gate reports no drift (AC61); the highlights
  projection matches the entry (AC62).

**Approach:** diff the version against the base branch before committing;
regenerate both projections rather than editing either; run the gate chain with a
clean build directory.

**Done when:** versions agree, the entry sits at top level, and both projections
are regenerated.

## Rollout

- **Delivery:** dependency-ordered waves, each green and shippable. The verb, the
  flag, and the state fields are additive; the shipped instructions gain the flag
  and the resumption table gains a column, both backward-compatible with existing
  persisted runs. One PR carries the whole spec, so the release indicator the
  `contracts/` change requires is present from the first commit that needs it.
- **Reversibility:** reverting removes additive code and restores the table's
  prior rows and its two pinned tests. Existing `state.json` files without the new
  fields keep working, because both are absent-tolerant on read.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the version bump and changelog land in T17.

## Risks

- **The projection and the state machine drift apart.** Both read the same
  transition tables, and the input set and `complete_with` are derived from them
  at runtime.
- **The emitter satisfies the contract with constants.** Each of the four derived
  fields carries a constant-value mutation proof.
- **Row parity degrades to "a record exists".** T7 adds the identifier column and
  anchors the expected mapping in this plan, outside the PR that writes the
  column.
- **A distinct round is absorbed as a replay.** AC41 requires the second round to
  increment; AC49 requires the continuation to reuse the recorded id rather than
  mint one.
- **The projection answers from mid-write state.** T9 detects both crash artifacts
  and stops.
- **Rewriting the resumption rows reddens two pinned tests.** T7 owns them in the
  same task.
- **A peer worktree takes the version.** Re-checked against the base before
  commit.
- **A peer session is editing the same skill tree.** Re-checked before T7 and T12.
- **Concurrent gate runs void results.** Gates run serialized and never while a
  worker is editing.

## Changelog

- 2026-08-31 — Split out of a larger contract that also carried an authored-word
  ceiling and a prose cut. Two review rounds on the combined contract produced 30
  then 43 findings, most attributed to the previous round's own repairs, and both
  reviewers independently identified the size as structural. The combined plan's
  dependency graph refuted its own atomicity claim.
- 2026-08-31 — Three fields the loop advances on — `complete_with`, `human_wait`,
  `sequence` — were unconstrained through two review rounds; an emitter returning
  empty values satisfied the whole contract. A fourth, `run_id`, and the `load`
  and `action` vocabularies had the same gap. All now have derivation criteria,
  closed vocabularies in this plan, and constant-value mutation proofs.
- 2026-08-31 — The automatic recording branch was cut: the projection cannot know
  a round's warranted reviewer roster, so requiring every warranted reviewer's
  payload was unverifiable by construction. An absent id now stops.
- 2026-08-31 — Review round 3 named the root defect as an unsettled record field
  set: criteria had been added requiring the record to carry a reset description
  and an artifact path, which no key could hold. Resolved by ruling that the
  record carries identifiers and scalars only and every reason goes to stderr, so
  the nine keys stand unchanged and no path-shaped value enters the record.
- 2026-08-31 — The runtime over-length refusal was dropped. A refusal would leave
  a live loop with no next action, and the invariant it guarded is already covered
  by the no-state-dump criterion; the size bound is now a suite assertion.
- 2026-08-31 — Two shipped tests pin the literal prose of the resumption rows this
  spec rewrites, and one asserts a property this spec makes false. T7 owns them.
- 2026-08-31 — The authored-word threshold was briefly planned inside
  `packages/agentbundle/`. A protected-tree gate requires an engine-scoped RFC
  trailer there, so no task touches that tree; the dependent contract places its
  checks in an existing pack test instead.
