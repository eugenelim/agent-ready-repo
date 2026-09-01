# Plan: work-loop-next-projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Ownership source: `docs/architecture/loop-infrastructure.md` §2-3 assigns the
    state machine and write authority to `loop-engine.py` and every cohort
    counter to `loop-cohort.py`. `packs/AGENTS.md` §Version bump rule and
    §Shipped pack content own the release and portability constraints.
  - Analogous implementation 1 — a read-only JSON-emitting engine verb:
    `loop-engine.py:1177-1198` (`cmd_status`); its resolve → read →
    schema-check → `json.dumps` shape, and the stderr-only `stop()` it returns
    through at `:964-966`. Tests: `test_loop_engine.py:1037`
    (`test_status_json_after_init`).
  - Analogous implementation 2 — id-keyed idempotency with form validation:
    `loop-cohort.py:1540` (`cmd_record_attempt`), form check at `:1557-1558`.
    This is the shipped precedent for the `run_id` and `cycle_id` form checks,
    not code this plan changes.
  - Analogous implementation 3 — bounded, confined artifact reading and reason
    hygiene: `_loop_guards.py` `read_md_status` (`:891-923`),
    `check_artifact_status` (`:1315-1382`), `read_managed_json`/`read_managed_text`
    (`:430-503`), and the scalar and reason caps at `:109-123` applied at the
    refusal chokepoint (`:264-270`).
  - Analogous implementation 4 — the schema field shape a JSON payload contract
    follows: `contracts/jsonschema/semantic-surface-resolution.schema.json`,
    validated from `tests/roster/`.
  - Named uncertainty: none material. Every seam is grounded in the anchors
    above and in the spec's four contract tables.

## Approach

The projection is a pure function of engine state, cohort state, and artifact
statuses. Purity is what lets a test traverse the whole domain and what makes the
read-only guarantee checkable by digest. It reads engine state through the
engine's own reader and both artifact statuses through the guard module's
`read_md_status`, so no new reader of either surface appears and the confinement,
symlink, non-regular-file, and size bounds those readers already enforce apply
unchanged.

The spec's four tables are the contract, and the spec is the sole home of the
domain's size. The implementation carries the routing and attribute data as
module-level dictionaries in `loop-engine.py`, and a `tests/roster/` test parses
the spec's Markdown and asserts the two agree. That is a comparison between two
independent expressions of the mapping, not an artifact checked against itself:
neither is generated from the other. That same `tests/roster/` suite builds the
domain and drives the live command into every member, because both the domain and
AC3's expected action are parsed from `spec.md`, which a pack test may not read.
The pack suite carries only what needs no file above `packs/core/`.

The Discriminators table is what keeps totality honest, and it does that by being
total over what each source can actually return rather than by citing a vocabulary
elsewhere. The canonical status reader has no vocabulary check — it returns
`draft`, `Frobnicate`, an empty string, or nothing at all — so D1 and D2 name two
values and fold every other outcome into `other`. Because the value sets no longer
come from the Routing table, deleting a routing row shrinks coverage without
shrinking the domain, and AC1's mutation reddens for every Routing row in the spec's table.

Four record fields carry the loop rather than describe it, and each is derived
rather than authored: `run_id` and `sequence` from the engine's state,
`complete_with` from the transition table's outgoing edges, and `human_wait` from
the Action attributes table. Deriving them is what stops an emitter from
satisfying the contract with constants.

The record carries identifiers and scalars only, and every human-readable reason
goes to stderr. That channel is the one an agent also reads, so it gets the same
treatment the guard module already gives its own refusals: each interpolated
external scalar capped and delimited, the whole reason capped. Reuse those bounds;
do not invent new numbers.

The engine repairs its own crash artifacts only inside its writing verbs. A
read-only verb must therefore detect an unpromoted temporary state file or an
unreplayed pending-events file — by presence alone, reading neither — and stop,
rather than answer from state that is mid-write.

## Constraints

- Neither state file changes owner.
- One Python process per invocation; `test_loop_engine_no_child_python.py`
  enforces this for the engine.
- No runtime dependency is added to any shipped pack script.
- No task edits `packages/agentbundle/`. The protected-tree gate at
  `tools/repo/build_gate_chain.py:306` requires an engine-scoped RFC trailer for
  that tree, and nothing here needs it.
- A pack test may not read above its own pack
  (`tools/lint-pack-test-boundary.py`), so every test that parses `spec.md` or
  reads `contracts/` is a `tests/roster/` test, and anything reading only
  `packs/core/**` is a pack test.
- `packs/core/tests/skills/work-loop/` (`Makefile:545`) and `tests/roster/` (via
  `pytest tests/` at `Makefile:530`) already run in `make test`; neither needs new
  CI wiring.
- The changelog entry ships in this change, because `contracts/` is
  release-impacting.
- `pytest` and `make build-check` cannot run concurrently in this tree; gate runs
  are serialized.
- `spec.md` and `plan.md` are hashed file-wide once approved. Every enumeration an
  implementer needs is in the spec's tables; no task authors one mid-execution.
- A peer session may be active in this repository's skill tree; re-check
  `packs/core/.apm/skills/work-loop/` for landed changes before T8.

## Construction tests

- Every new refusal and guard carries a mutation proof: the invariant, the test
  catching its removal, the exact mutation, the expected failure.
- The base keys and `complete_with` are derived at runtime from
  `_TRANSITIONS_BY_MODE`; the extra base keys and the discriminator value sets are
  parsed from the spec's own tables. The load vocabulary comes from globbing
  `references/`. Resumption-row parity comes from parsing the shipped table's
  action column.
- Each of the four derived fields gets a constant-value mutation: pinning
  `run_id`, `sequence`, `complete_with`, or `human_wait` to a constant must redden
  at least one case.
- The five table properties each get a mutation that must redden them:
  - **AC1** — delete any Routing row; at least one domain member must go
    uncovered. This must redden for every Routing row in the spec's table, without exception. A run in which
    the discriminator-bearing rows survive deletion means the domain is still
    being sourced from the Routing table, which is the round-1 defect.
  - **AC2** — widen one row's match so it overlaps another.
  - **AC3** — exchange R7's and R8's Discriminator cells in the implementation's
    resolver. This is the mutation that distinguishes AC3 from AC1 and AC2: it
    changes no row's action and no row's coverage, so only a criterion that drives
    the live command and compares against the spec's Discriminator column catches
    it. Four domain members change action under it.
  - **D5's two rows** get their own mutation: forcing `within-budget` at the cap
    makes R5 and R25 unreachable and must redden AC3, because it is the one that
    drives the live command into a state whose review budget is spent.
  - **AC4** — remove an Action attributes row.
  - **AC5** — change one attribute cell.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — the record schema | T7 | `tests/roster/` conformance over live output; `contracts/README.md` row | Schema validates real output, carries `x-spec`, inventoried |
| Current architecture — `loop-infrastructure.md` | T9 | Entrypoint section names the verb as read-only | Doc matches the shipped verb set |
| Current product truth — the skill payload | T1, T4, T8, T12 | `make build-self-dry-run` clean | Source edited, projections regenerated |
| User-facing promise — the core how-to | T10 | Adopter description of resuming through the verb | Guide describes shipped behavior |
| Operations — the QA transcripts | T11 | Two transcripts at `notes/qa-transcripts.md` | Both committed with their scope boundary |
| Release history — the changelog | T12 | Free-standing dated entry with `### Highlights` | Entry at top level; highlights projection regenerated |
| Reusable learning | T12 | `project-knowledge` receipt or recorded unavailability | Receipt recorded or unavailability named |

## Design (LLD)

### Design decisions

- `kind` separates who acts; the controller maps `action` through the closed
  Action attributes table, so no string from the record is executed. AC20 makes
  that consumer obligation a shipped, grep-assertable statement rather than a
  design note — the producer-side closed vocabulary is only a control if the
  consumer refuses what is outside it.
- `load` names only what an action needs *when the record is handed over*. The
  two review references are needed after a raw report exists and has been
  classified, which is later, so they are absent from `run-review` and
  `spec.review` and stay owned by the shipped conditional-reference table. This is
  the one place where the smallest correct change was to delete two table cells
  rather than add a mechanism: the projection gains no field, action, state, or
  discriminator, reads no report prose, and infers no roster.
- The record carries identifiers and scalars only. Reasons go to stderr, which is
  why a `stop` needs no message field and no path value — and why AC14 bounds that
  channel, since it reaches the same agent the record does.
- A `stop` is a zero-exit record because computing "you must stop" succeeded; a
  non-zero exit means no record could be computed. P2-P6 are the conditions
  under which no record can be built, which is why they exit non-zero: three of
  them cannot produce `run_id`, `sequence`, or `complete_with` at all.
- `complete_with` is the *unguarded* outgoing-edge set. Filtering it by the
  cohort's wave guard would make the record answer "which event" at
  `CODE-VERIFICATION`, but it would also couple the projection to a guard's
  runtime result and make `complete_with` no longer derivable from one table.
  The guard refuses an illegal choice anyway. The spec records the consequence:
  `complete_with` names events, not invocations, and two of them take required
  transition arguments the record does not supply.
- `SPEC-PLAN-APPROVED` needs three commands with no engine transition between
  them. R13-R17 discriminate on `plan_review_status` and `schedule_waves` so each
  call advances, rather than returning `cohort.approve-plan` three times.

### Data & schema

No new state field. The two fields D4 reads —
`last_review_record_operation_id` and `last_review_record_payload_digest` —
shipped with `docs/specs/review-record-idempotency/`, are documented in
`references/state-schema.md`, and are absent-tolerant on read, which is why D4 is
a boolean over "matches" rather than a three-way over absent, differing, and
equal.

### Interfaces & contracts

The schema fixes the nine-key set with `additionalProperties: false`, the `kind`
enum, the `schema_version` const, the `action` enum from the Action attributes
table, `run_id` with the canonical-UUID pattern P6 requires, and `parameters` as a
per-action conditional key set with character-class-constrained values.

### Component / module decomposition

No new module: a new `cmd_next` plus two table dictionaries and a per-state
discriminator resolver in `loop-engine.py`.

### State & control flow

The projection never transitions. The agent reads a record, acts, fires an event
from `complete_with`, and calls it again.

### Failure, edge cases & resilience

The spec's Preconditions table is the failure contract, and its preamble is the
single home of the row count, the non-zero code allocation, and which rows exit
which way — this plan asserts against that preamble and restates none of it.
Everything below the table routes. Its off-table row closes the off-table pair — a valid state carrying an event that never targets it —
which the transition-table-derived domain cannot reach by construction.

### Quality attributes (NFRs)

The size bound is asserted over the domain in the suite rather than enforced at
runtime, so a future record that grows reddens CI instead of leaving a live loop
with no next action. The stderr bound is different in kind and is enforced at
runtime, because its failure mode is a context flood into the supervising agent
rather than a CI signal.

### Dependencies & integration

None added. Both suites already run in `make test`.

## Tasks

### T1: the verb exists, with a fixed shape, a clean exit convention, and a bounded reason channel

**Depends on:** none

**Tests:** TDD.
- Zero exit yields exactly one JSON object with the nine-key set; non-zero exit
  writes nothing to stdout (AC7).
- No diagnostic reaches stdout on any path; every diagnostic and stop reason
  reaches stderr (AC8).
- A `stop`-kind record is emitted on a zero exit, and a command failure emits none
  (the exit convention).
- Every interpolated external scalar is capped and delimited, and the whole reason
  is capped, at the guard module's existing bounds; a planted oversized `run_id`
  reaches stderr truncated and quoted (AC14).
- `--json` is required: the verb invoked without it exits non-zero and writes
  nothing to stdout, so no second output form exists (AC7, second half).
- The subparser is registered beside the four existing verbs (AC21).
- Mutation proofs: routing one reason to stdout reddens the channel case; removing
  the cap, and removing the delimiters, each redden an AC14 case.
- `stub: true` — one compilable red assertion that the verb exits 0 and prints
  parseable JSON for a freshly initialised `code`-mode run.

**Approach:** follow `cmd_status`'s shape and return through the existing `stop()`.
Reuse `_MAX_SCALAR_CHARS` and `_MAX_REASON_CHARS`; do not introduce new numbers.

**Done when:** shape, channel, exit-convention, and reason-bound cases are green
and `--help` lists the verb.

### T2: every read goes through the confinement and the guard readers

**Depends on:** T1

**Tests:** TDD.
- The verb opens exactly four files — both state files, both artifact Status
  files — each through the guard module's readers, with no direct `open` or
  `read_text` in the verb's path (AC15).
- A symlink, a non-regular file, and an oversized file at each of those four are
  each refused rather than followed, read, or blocked on.
- The two crash artifacts are never opened: a symlink, a directory, and a FIFO at
  either location are each detected as present and yield P1's `halt`, with no
  read, parse, or repair (AC15a).
- Mutation proof: replacing one guard read with `Path.read_text` makes the symlink
  case at that target pass; adding any `open` of a crash artifact reddens AC15a.

**Approach:** artifact statuses go through `read_md_status`; state files through
their owners' existing readers. The FIFO that once hung `init` while holding the
state lock is the precedent for why the non-blocking open matters here too.

**Done when:** every read target has a passing hostile-fixture case and the
mutation flips.

### T3: the derived fields are computed, not authored

**Depends on:** T2

**Tests:** TDD.
- `schema_version` is the literal const; `run_id` equals the engine's and matches
  the canonical UUID form; `sequence` equals `transition_sequence` (AC9).
- `complete_with` equals the outgoing event set read from `_TRANSITIONS_BY_MODE`
  at runtime, empty exactly for `DONE`, except AC10's one declared exception that
  T6 covers: a `cap-reached` record omits `reviewers-clean` (AC10).
- Mutation proofs: pinning `run_id`, `sequence`, or `complete_with` to a constant
  reddens at least one case; removing the `run_id` form check lets a planted
  malformed id reach a record.

**Done when:** the assertions are green and all four mutations flip.

### T4: the four contract tables, and the five properties that hold of them

**Depends on:** T2

**Tests:** TDD.
- `tests/roster/test_work_loop_next_projection_contract.py` **already exists and
  already parses all four normative tables**, asserting totality, determinism,
  the deletion mutation, closure, `human_wait`, the stated domain size,
  cross-document reference resolution, AC coverage parity, and AC27's path 1. T4
  **extends that module rather than adding a second parser** of the same tables —
  two parsers of one normative table is the drift hazard this whole contract is
  written against. What T4 adds is the half the module cannot have until the verb
  exists: comparing the parsed tables against the implementation's own routing and
  attribute dictionaries, cell for cell.
- Build the domain at runtime from `_TRANSITIONS_BY_MODE` plus the spec's extra
  base keys, crossed with the spec's discriminator value sets; assert totality
  (AC1) and determinism (AC2).
- `tests/roster/` — drive the live command into a domain member matching each
  Routing row and assert the row's action, with the expected value parsed from the
  spec's Routing table including its Discriminator column, never from the
  implementation's resolver (AC3). Every bullet in this task is a roster test for
  the same reason as the first: each reads `spec.md`.
- Assert closure in both directions between the tables (AC4).
- Assert `kind`, the `parameters` key set, `load`, and `human_wait` against the
  Action attributes row for each emitted record's action (AC5), including
  `human_wait: false` at R8 and R11 while the engine reports
  `pending_human_wait: true`, and `human_wait: true` at R5 and R25, the two `await-replan-decision` rows, which are `wait`-kind.
- Mutation proofs, one per property, exactly as listed under Construction tests.
  AC1's must redden for every Routing row in the spec's table.

**Approach:** implement routing as a dictionary keyed on
`(mode, state, last_event)` with a discriminator resolver per state. The resolver
is the part the roster equality test cannot reach — it has no dictionary cell — so
AC3's live-drive case is its only coverage and the R7/R8 exchange is its only
mutation. Neither may source its expectation from the resolver.

**Done when:** all five properties are green over the full domain, and all five
mutations flip including AC1's across every row.

### T5: values, references, and the size bound are constrained

**Depends on:** T3, T4

**Tests:** TDD.
- Every `parameters` value matches the character class or is an integer resolved
  through the guard module's non-negative-integer helper, which refuses a boolean,
  a negative, and a non-integer by name,
  enforced at runtime for state-derived values: a planted non-integer
  `completed_wave_index` yields `halt`, not a record carrying it (AC11, first
  half). `from_index` is sourced from `engine-state.json`'s
  `last_event_context.completed_wave_index`, never from `state.json`'s
  `current_wave_index`, which the advance itself increments.
  This is the one place a `parameters` value is not derived from a P5-checked
  field.
- Every `load` entry resolves to a file under `references/`, with the mapping
  built by globbing rather than copied (AC11, second half).
- No record carries a schedule array, amendment history, fingerprint, or verbatim
  state copy (AC12), with the fingerprint case driven explicitly — a 64-character
  hex digest placed in a declared `parameters` key satisfies AC5, AC7, and AC11,
  so it is the case that proves AC12 is not dominated.
- Traverse the domain, assert no record exceeds 1024 bytes, and pin the observed
  maximum against a constant held in the test file (AC13).
- Mutation proofs: emitting an identifier with no matching file reddens AC11;
  placing a fingerprint in `cycle_id` reddens AC12 alone.

**Done when:** the traversal covers the domain and both bounds hold.

### T6: the preconditions fire in order, and nothing is written

**Depends on:** T2

**Tests:** TDD.
- Each Preconditions row, exercised in isolation and against a state
  that also matches a later row, produces that row's exit and record, and its
  stderr names what the row requires (AC6).
- P1's ordering is exercised in the state that makes it load-bearing: an
  engine-state temporary with no `engine-state.json` beside it must yield P1's
  `halt`, not P2's or P3's non-zero refusal.
- The review-budget branch is exercised from both review states across all four
  D5 values. `cap-reached` and `stasis` each yield `await-replan-decision`, with
  the stderr reason naming which condition fired and only the continuations legal
  under it — reset or the paired human-directed `--allow-retry-cap-override` at
  the cap, and under stasis a stop for human replanning, which is what the
  lifecycle reference requires — naming neither a repaired round, nor narrowing,
  nor splitting, all of which that reference forbids on this trigger. `malformed`
  yields `halt`.
- The empty-fingerprint baseline is exercised explicitly: a fresh run, and a run
  after two consecutive clean or all-skipped rounds, both yield `within-budget` at
  both review states.
  Without the non-empty qualifier both lists are equal on a fresh run, so every
  first call would read as stasis; these are the cases that prove the qualifier
  is present.
- An amended contract re-entering `SPEC-PLAN-REVIEW` with a surviving over-cap
  counter yields `cap-reached` and routes to `await-replan-decision`, like any
  other spent budget. No carve-out is exercised because none exists: D5 reports
  what it reads at every state. Mutation proof: adding any suppression of
  `cap-reached` reddens this case.
- A `cap-reached` record omits `reviewers-clean` from `complete_with`; a
  `within-budget` record at the same state includes it (AC10's declared
  exception).
- Mutation proof: dropping the non-empty qualifier from the stasis comparison
  reddens the fresh-run case; dropping the `complete_with` exception reddens the
  cap-reached case.
- P3's marker match is exercised against the six spellings in the fixture set
  below, against a body-zone mention, and against `Modelight` and
  `Mode: light-weight` — none of the last three may match.
- Every non-zero row returns the distinct code the spec's Preconditions preamble
  allocates, each distinct from the others and from 1 and 2. The preamble is the
  single home of the row and code counts; assert against it, never against a
  literal restated here.
- Digest `engine-state.json`, `state.json`, and `.loop-run/events.jsonl` before
  and after; assert equality and that no file is created or removed, on every
  Preconditions row as well as every Routing row (AC16).
- Mutation proofs: removing the crash-artifact check, the `run_id` pairing check,
  the `mode` well-formedness check, or the off-table-pair check each make their
  row's case pass.

**Approach:** detect the two crash artifacts by presence alone, never by reading:
the engine-state temporary has a random `mkstemp` name, so it needs a confined
glob of `.engine-state-*.json.tmp` within the spec directory — the same
enumeration the engine's own recovery uses — while the pending-events file takes a
single stat in the repository-shared run directory. Reading either would parse an
attacker-influenceable file, and repair is a writing verb's job. Treat a present
pending-events file as halting for every run in the repository, per the spec's P1
scope note. The marker fixture set is the six spellings observed in the corpus:
bare, `**Mode:**`, list-prefixed, blockquoted, backticked, and fully bolded.

**Done when:** every Preconditions row in the spec's table is green and all four
mutations flip.

### T7: the published schema validates live output and is inventoried

**Depends on:** T5

**Tests:** TDD, as a contract test.
- `tests/roster/` conformance running the real command for at least one record per
  Action attributes row and validating each (AC17, first half).
- An undeclared `parameters` key for that record's action is rejected (AC17,
  second half).
- `contract_version`, `x-spec`, and the `contracts/README.md` row with CLI data
  `no` (AC18).

**Done when:** the roster test validates live output and the inventory row exists.

### T8: the resumption table carries action identifiers, and the consumer's trust posture is shipped

**Depends on:** T4

**Tests:** TDD.
- For every row of the shipped table, its count parsed rather than restated, the identifiers parsed from the new column
  equal the union across both modes of the Routing actions whose key matches that
  row's `(last_event, state)` pair, with both sides parsed (AC19).
- All five trust-posture statements appear in
  `packs/core/.apm/skills/work-loop/SKILL.md`, the always-loaded body, so the
  control is present on every turn a record is consumed rather than only on the
  one action that loads the resumption reference: record is data, unrecognised
  `action` halts, unrecognised `load` halts, no field is executed, and a stderr
  reason is a diagnostic while a `wait`-kind record authorises no act (AC20). The
  resumption reference may repeat them.
- The `gates-clean`/`CODE-REVIEW` shipped row's prose carries the review-budget
  branch, grepped for explicitly; deleting the branch reddens this case (AC19's
  prose clause, which column parity alone does not cover).
- AC27's five paths, each asserted in the evidence form the criterion names:
  path 1 against the spec's Action attributes table, paths 2-5 as greps over the
  shipped surface. The shipped surface currently carries **two conflicting
  controls** — the conditional-reference table predicates the adjudication
  reference on a `finding-adjudicator` dispatch, while the always-loaded body
  instructs an unconditional read before a review unit's first report. This task
  reconciles them, which makes path 2 true; it is not a pre-existing control this
  contract inherits, and the earlier claim that three of four predicates already
  shipped was wrong.
- Mutation proof for AC27: restoring either reference to a review action's `load`
  cell reddens the dispatch-time case.
- Mutation proofs: changing one row's identifier reddens its generated case;
  deleting any one of the five statements reddens AC20; deleting the budget branch
  from the amended row reddens the AC19 prose case.

**Approach:**
- Add the identifier column, and amend exactly one row's prose. Twelve rows'
  prescribed actions already agree with the Routing table. The
  `gates-clean`/`CODE-REVIEW` row does not: its prose tells a resuming agent to
  re-run the reviewer fan-out, which is what R25 suppresses once the budget is
  spent, so that row gains the budget branch. Leaving it as-is would satisfy
  AC19's column parity while the shipped surface still pushed a capped agent
  toward another round. The two spec-plan
  `DONE` rows carry `complete` in the identifier column while their prose keeps
  describing the conditional reset, because that reset is a human-initiated path
  the projection cannot observe. The diff stays additive and all three
  prose-pinned tests keep passing unchanged — `test_loop_engine.py:2775-2776`,
  `:2846`, and `test_loop_cohort.py:1843-1867`, which pins the same
  `reviewers-clean` row and requires exactly one matching line. Confirm rather
  than assume: run all three before and after.
- Re-check the peer session's activity in the skill tree before editing.

**Done when:** parity is parsed for every shipped row, all five trust statements are
present in `SKILL.md`, the amended row carries the budget branch, and both pinned
tests still pass untouched.

### T9: the architecture surface names the new verb

**Depends on:** T6

**Tests:** goal-based — the entrypoint section of
`docs/architecture/loop-infrastructure.md` lists `next` in the `loop-engine.py`
verb set and marks it read-only (AC22).

**Approach:** edit that one owning section; the repository state-ownership table
names writers, so a read-only verb adds no row there.

**Done when:** the doc describes the shipped verb set.

### T10: adopters can drive the new behavior from the guide

**Depends on:** T8

**Tests:** goal-based — grep
`guides/core/how-to/plan-and-execute-non-trivial-work.md` for the literal
`loop-engine next`, not the bare word: that file already carries "the next phase"
and "the next review unit", so a bare-word check is green before the edit (AC23).

**Approach:** rewrite the hand-driven resumption passage to the sequence adopters
now run, rather than appending the new one beside the old.

**Done when:** the guide describes shipped behavior.

### T11: the assembled route runs, including a crash and resume

**Depends on:** T4, T6, T8

**Tests:** visual / manual QA.
- Run 1: a full-mode `code`-mode loop to `DONE`, recording the action sequence,
  final engine state, and per-command exit codes.
- Run 2: interrupt between firing `findings-remain` and recording the round,
  resume, confirm a correct next action with no double increment.
- Both transcripts state what the sessions do not exercise (AC24).

**Approach:** write both to `notes/qa-transcripts.md`. Use a throwaway spec
directory, remove it afterwards, and confirm `git status` is clean. Write
repository-relative paths only; the privacy convention forbids committing
user-specific filesystem paths, and the verb's own stderr interpolates absolute
ones. Scope boundary: spec-plan mode, contract amendment, and the supervisor
fan-out paths are covered by unit cases and are not exercised here.

**Done when:** both transcripts are committed with their scope boundary stated.

### T12: the release surface is consistent

**Depends on:** T7, T9, T10, T11

**Tests:** goal-based.
- A free-standing dated entry at `##` with a `### Highlights` block, and both
  version files reading the same value one minor above the base branch's (AC25).
- The drift gate reports no drift and the highlights projection matches the entry
  (AC26).

**Approach:** diff the version against the base branch before committing;
regenerate both projections rather than editing either; run the gate chain with a
clean build directory.

**Done when:** versions agree, the entry sits at top level, and both projections
are regenerated.

## Rollout

- **Delivery:** dependency-ordered waves, each green and shippable. The verb and
  the resumption table's new column are additive and backward-compatible with
  existing persisted runs. One PR carries the whole spec, so the release indicator
  the `contracts/` change requires is present from the first commit that needs it.
- **Reversibility:** reverting removes additive code and one table column. No
  state field is added, so no persisted `state.json` is affected either way.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** the version bump and changelog land in T12.

## Risks

- **The projection and the state machine drift apart.** The base keys and
  `complete_with` are both derived from `_TRANSITIONS_BY_MODE` at runtime, and
  AC1 fails the moment the engine gains a transition the tables do not cover.
- **The tables and the code drift apart.** The roster test compares the spec's
  Markdown with the implementation's dictionaries; neither is generated from the
  other, so agreement is evidence.
- **The projection pushes a caller toward a false clean.** At the review cap the
  engine refuses `findings-remain`, so `reviewers-clean` is the only event it
  still accepts; a projection that answered `run-review` there would leave
  declaring the contract clean as the sole escape. R5 and R25 answer
  `await-replan-decision` instead, and D5 reads the cap and the stasis
  fingerprints straight from `state.json`.
- **A way back loses its obligation.** All three return paths land in
  `SPEC-PLAN-DRAFTING`, and two carry duties a plain redraft skips — status reset
  after a rejected gate, and authority plus pin preservation plus reapproval and
  rescheduling after a contract amendment. R2 and R3 separate them and each carries
  `ref:delivery-contract-lifecycle` where the duty is written down.
- **Totality passes over a domain narrower than the live input.** Rounds 1 and 2
  each found a version of this. The fix is not a citation but closure: each
  discriminator's value set is total over what its source can return, with `other`
  absorbing every unrecognised, empty, absent, and unreadable outcome, and AC1's
  mutation must redden for every Routing row in the spec's table.
- **The discriminator resolver ships untested.** The roster equality test cannot
  reach it. AC3 drives the live command with expectations parsed from the spec,
  and the R7/R8 exchange is its named mutation.
- **The emitter satisfies the contract with constants.** Each of the four derived
  fields and each of the five table properties carries a mutation proof.
- **A planted state file floods the agent's context.** AC14 caps and delimits
  every interpolated scalar on stderr; P4 refuses a malformed `run_id` before a
  record exists; AC15 keeps every read inside the bounded guard readers.
- **Row parity degrades to "a record exists".** T8 parses both sides.
- **The projection answers from mid-write state.** T6 detects both crash artifacts
  by presence and stops. The residual torn two-file read is accepted and recorded
  in the spec's Assumptions.
- **A peer worktree takes the version.** Re-checked against the base before
  commit.
- **A peer session is editing the same skill tree.** Re-checked before T8.
- **Concurrent gate runs void results.** Gates run serialized and never while a
  worker is editing.

## Changelog

The contract reached its present shape through four pre-EXECUTE review rounds
that sustained 78 findings across the adversarial and secure-design lanes. Three
decisions explain most of what it looks like now:

- **The state-to-action mapping is a set of tables, not prose criteria.** Prose
  acceptance criteria could not specify a total function: four earlier rounds
  produced 30 → 43 → 19 → 37 findings without converging, because repairing one
  row's wording opened a gap in another's. Criteria now assert properties *of*
  the tables — totality, determinism, closure, each row's observable — so new
  behaviour arrives as new rows and leaves the criteria alone.
- **Every discriminator is closed by a catch-all, not by citing a vocabulary
  elsewhere.** Two rounds were lost to value sets that looked closed and were
  not: a cited status vocabulary that excluded the file it was cited for, and a
  stasis comparison that read as true on the empty state every run starts in.
  Closure over what a source can actually return is the property that holds.
- **No action in the contract is destructive, and none is routed from an
  unobservable decision.** A finished spec-plan run answers `complete`; a spent
  review budget waits for a human; splitting a contract is a scope-owner decision
  the projection surfaces rather than names.

Round-by-round repairs, the reasoning each replaced, and the refuted findings are
in [`notes/review-history.md`](notes/review-history.md).
