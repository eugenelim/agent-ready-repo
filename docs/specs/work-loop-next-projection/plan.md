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
neither is generated from the other. The pack suite then drives the live command
into every domain member.

The Discriminators table is what keeps totality honest. Because each
discriminator's value set is fixed outside the Routing table, deleting a routing
row shrinks coverage without shrinking the domain, so AC1's mutation reddens for
every row rather than only the ones carrying no discriminator.

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
  - **AC1** — delete any Routing row. This must redden for all 22, which is the
    property the Discriminators table exists to buy; a run where only the ten
    discriminator-free rows redden means the domain is still being sourced from
    the Routing table.
  - **AC2** — widen one row's match so it overlaps another.
  - **AC3** — exchange R3's and R4's Discriminator cells in the implementation's
    resolver. This is the mutation that distinguishes AC3 from AC1 and AC2: it
    changes no row's action and no row's coverage, so only a criterion that drives
    the live command and compares against the spec's Discriminator column catches
    it. Four domain members change action under it.
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
- The record carries identifiers and scalars only. Reasons go to stderr, which is
  why a `stop` needs no message field and no path value — and why AC14 bounds that
  channel, since it reaches the same agent the record does.
- A `stop` is a zero-exit record because computing "you must stop" succeeded; a
  non-zero exit means no record could be computed. P1-P4 are the four conditions
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
  them. R9-R12 discriminate on `plan_review_status` and `schedule_waves` so each
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
table, `run_id` with the canonical-UUID pattern P4 requires, and `parameters` as a
per-action conditional key set with character-class-constrained values.

### Component / module decomposition

No new module: a new `cmd_next` plus two table dictionaries and a per-state
discriminator resolver in `loop-engine.py`.

### State & control flow

The projection never transitions. The agent reads a record, acts, fires an event
from `complete_with`, and calls it again.

### Failure, edge cases & resilience

The spec's Preconditions table is the failure contract: seven ordered rows, the
first four exiting non-zero with four distinct stable codes and no record, the
last three emitting a zero-exit `halt`. Everything below them routes. P7 closes
the off-table pair — a valid state carrying an event that never targets it —
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
- Both state files, both artifact Status files, and both crash artifacts are
  resolved through the existing spec-directory confinement and read through the
  guard module's readers; no direct `open` or `read_text` appears in the verb's
  path (AC15).
- A symlink, a non-regular file, and an oversized file at each read target are
  each refused rather than followed, read, or blocked on.
- Mutation proof: replacing one guard read with `Path.read_text` makes the symlink
  case at that target pass.

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
  at runtime, empty exactly for `DONE` (AC10).
- Mutation proofs: pinning `run_id`, `sequence`, or `complete_with` to a constant
  reddens at least one case; removing the `run_id` form check lets a planted
  malformed id reach a record.

**Done when:** the assertions are green and all four mutations flip.

### T4: the four contract tables, and the five properties that hold of them

**Depends on:** T2

**Tests:** TDD.
- `tests/roster/` — parse the spec's Routing and Action attributes tables and
  assert they equal the implementation's two dictionaries, cell for cell; parse
  the Discriminators and extra-base-key tables and assert the domain builder uses
  them.
- Build the domain at runtime from `_TRANSITIONS_BY_MODE` plus the spec's extra
  base keys, crossed with the spec's discriminator value sets; assert totality
  (AC1) and determinism (AC2).
- Drive the live command into a domain member matching each Routing row and assert
  the row's action, with the expected value parsed from the spec (AC3).
- Assert closure in both directions between the tables (AC4).
- Assert `kind`, the `parameters` key set, `load`, and `human_wait` against the
  Action attributes row for each emitted record's action (AC5), including
  `human_wait: false` at R4 and R7 while the engine reports
  `pending_human_wait: true`, and `human_wait: true` at R22.
- Mutation proofs, one per property, exactly as listed under Construction tests.
  AC1's must redden for all 22 rows.

**Approach:** implement routing as a dictionary keyed on
`(mode, state, last_event)` with a discriminator resolver per state. The resolver
is the part the roster equality test cannot reach — it has no dictionary cell — so
AC3's live-drive case is its only coverage and the R3/R4 exchange is its only
mutation. Neither may source its expectation from the resolver.

**Done when:** all five properties are green over the full domain, and all five
mutations flip including AC1's across every row.

### T5: values, references, and the size bound are constrained

**Depends on:** T3, T4

**Tests:** TDD.
- Every `parameters` value matches the character class or is an integer or boolean
  (AC11, first half).
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
- Each of the seven Preconditions rows, exercised in isolation and against a state
  that also matches a later row, produces that row's exit and record, and its
  stderr names what the row requires (AC6).
- P1's marker match is exercised against every spelling the live corpus carries —
  bare, `**Mode:**`, list-prefixed, blockquoted, backticked, and fully bolded —
  and against a body-zone mention that must not match.
- P1 through P4 return four distinct codes, asserted as mutually distinct rather
  than as four literals in four places.
- Digest `engine-state.json`, `state.json`, and `.loop-run/events.jsonl` before
  and after; assert equality and that no file is created or removed, on every
  Preconditions row as well as every Routing row (AC16).
- Mutation proofs: removing the crash-artifact check, the `run_id` pairing check,
  the `mode` well-formedness check, or the off-table-pair check each make their
  row's case pass.

**Approach:** detect the two crash artifacts by presence alone — an `lstat`, not a
read — because reading them would parse an attacker-influenceable file and repair
is a writing verb's job. Treat a present pending-events file as halting for every
run in the repository, per the spec's P5 scope note.

**Done when:** all seven rows are green and all four mutations flip.

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
- For each of the 15 shipped rows, the identifiers parsed from the new column
  equal the union across both modes of the Routing actions whose key matches that
  row's `(last_event, state)` pair, with both sides parsed (AC19).
- A grep over the shipped text finds all four trust-posture statements: record is
  data, unrecognised `action` halts, unrecognised `load` halts, no field is
  executed (AC20).
- Mutation proofs: changing one row's identifier reddens its generated case;
  deleting any one of the four statements reddens AC20.

**Approach:**
- Add the identifier column only. No row's prose changes: every shipped row's
  prescribed action already agrees with the Routing table, so this task's diff is
  additive and the two prose-pinned tests at `test_loop_engine.py:2775-2776` and
  `:2846` keep passing unchanged. Confirm that rather than assuming it — run both
  before opening the task and after the edit.
- Re-check the peer session's activity in the skill tree before editing.

**Done when:** parity is parsed for all 15 rows, all four trust statements are
present, and both pinned tests still pass untouched.

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

**Tests:** goal-based — `guides/core/how-to/plan-and-execute-non-trivial-work.md`
names the verb in its resumption passage (AC23).

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
- **Totality passes without covering the discriminators.** This is the defect the
  first review round found. The Discriminators table sources every value set
  outside the Routing table, and AC1's mutation is required to redden for all 22
  rows, not the ten that carry no discriminator.
- **The discriminator resolver ships untested.** The roster equality test cannot
  reach it. AC3 drives the live command with expectations parsed from the spec,
  and the R3/R4 exchange is its named mutation.
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

- 2026-08-31 — Split out of a larger contract that also carried an authored-word
  ceiling and a prose cut. Two review rounds on the combined contract produced 30
  then 43 findings, most attributed to the previous round's own repairs, and both
  reviewers independently identified the size as structural. The combined plan's
  dependency graph refuted its own atomicity claim.
- 2026-08-31 — Three fields the loop advances on — `complete_with`, `human_wait`,
  `sequence` — were unconstrained through two review rounds; an emitter returning
  empty values satisfied the whole contract. All now have derivation criteria and
  constant-value mutation proofs.
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
- 2026-09-01 — Restructured after four review rounds (30 → 43 → 19 → 37 findings)
  failed to converge. The diagnosis: the spec was specifying a total
  state-to-action function in prose acceptance criteria, so every round's repair
  of one row's wording opened a gap in another's. The mapping moved into tables in
  `spec.md` and the criteria became properties of those tables, taking the
  contract from 62 ACs and 17 tasks to its current 26 and 12.
- 2026-09-01 — Wave 3 was deleted rather than rewritten. `--operation-id`, its
  form check, replay and conflict behaviour, the two `state.json` fields, the
  state-schema reference, and the shipped invocations all landed in
  `docs/specs/review-record-idempotency/` (core 2.18.2, PR #1192). Ten criteria
  describing that mechanism were removed as already shipped; what remains of the
  recording branch is two Routing rows, R16 and R17.
- 2026-09-01 — The `CODE-HUMAN-GATE` changes-requested criteria were dropped. They
  described a record for a branch `next` cannot observe: the human's merge
  decision is not in either state file, so that state has one row and the replay
  detail stays in the shipped resumption row, which already carries it.
- 2026-09-01 — Wave position stopped being an input dimension. It discriminates no
  row's action; it enters the record only as `cohort.wave-advance`'s `from_index`.
- 2026-09-01 (round 1 repair) — The restructure's own totality criterion was a
  control that could not fail. The domain was crossed with "each row set's
  discriminator values", read out of the same Routing table totality was checked
  against, so deleting a discriminator-bearing row deleted the members that would
  have exposed it: only 10 of 22 rows reddened. A Discriminators table now fixes
  each value set from a source outside Routing — the Status vocabularies
  `lint-spec-status.py` enforces, the `state.json` field domains, and a boolean —
  and the domain is a derivable 54 members with the count stated once. Re-checked
  after the repair: 0 uncovered, 0 ambiguous, and all 22 rows reddening.
- 2026-09-01 (round 1 repair) — Three ways the contract could be satisfied while
  still handing an agent attacker-controlled text. Stderr was unbounded while the
  record was tightly bounded, and the guard module had already been through this:
  a 100 KB `run_id` produced a 100,055-character reason. `run_id` reached the
  record with no form check. Artifact reads were named by filename with no
  confinement or reader. AC14, P4, and AC15 close the three, all by reusing
  controls that already exist rather than inventing bounds.
- 2026-09-01 (round 1 repair) — Two holes the routing tables could not see. An
  off-table `(state, last_event)` pair — a valid state carrying an event that
  never targets it — was excluded from the domain by construction, so no criterion
  reached it; P7 now covers it. `mode` appeared in no precondition while Routing
  keyed on it, and P6's old "differs" test passed vacuously on two absent
  `run_id`s; P4 and the restated P6 close both. The precondition table went from
  six rows and three exit codes to seven and four.
- 2026-09-01 (round 1 repair) — `P1`'s light-mode marker was undecidable. The
  literal appears across `docs/specs/` in six header spellings plus HTML comments,
  acceptance-criterion mentions, and one negated prose occurrence, and no Python
  in the repository parses it. The condition is now a single regex over the
  pre-`##` zone with comments stripped, validated against the corpus: it matches
  exactly the 37 specs carrying a real marker, with no misses and no over-matches.
- 2026-09-01 (round 1 repair) — AC3 could not be distinguished from the roster
  equality test, leaving the discriminator resolver — 12 of 22 rows — with no
  coverage. AC3 now sources its expectation from the spec's Discriminator column
  and names the R3/R4 exchange as its mutation; that mutation changes four domain
  members' actions while changing no row's action or coverage.
- 2026-09-01 (round 1 repair) — Three smaller gaps closed: `complete_with` now
  states that it names events rather than invocations and that `wave-passed` and
  `contract-amendment` take arguments the record does not supply; the unlocked
  two-file read is recorded as an accepted Assumption with what P6 does and does
  not bound; and AC19 states that its comparison set is the union across both
  modes, without which its exactness claim had no quantifier.
- 2026-09-01 (round 1, refuted) — Four findings were tested and not sustained, and
  the artifact is unchanged on each: AC12 is not dominated by AC5/AC7/AC11,
  because a 64-character fingerprint satisfies all three while violating it, so it
  stays and T5 now drives that exact case; the extra base keys are already sourced;
  per-task verification modes were already derivable from the Testing Strategy,
  though they are now stated per task anyway; and T8's test location was already
  fixed by the Constraints section.
