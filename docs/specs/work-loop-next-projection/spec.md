# Spec: work-loop-next-projection

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/jsonschema/work-loop-next.schema.json`
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent advancing or resuming a full-mode work-loop asks the loop CLI what to do
next and receives one bounded record naming a single action, the arguments that
action needs, the events that complete it, and whether a human gate is open.
`loop-engine next <spec-dir> --json` answers from state and writes nothing.

Recording a review round is replayable, so a crashed session can tell whether the
round was written instead of guessing. Where the answer is knowable from state,
the agent proceeds; where it is not, the record says stop and the reason names
what to supply.

The agent gets one authoritative action per turn instead of reconstructing it
from two state dumps and a prose routing table. The adopter driving these
commands by hand gets a single call in place of that sequence.

Reducing the always-loaded instruction surface is the separate contract this one
enables; no criterion here changes `SKILL.md`'s size.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the record is a machine-read payload | `contracts/jsonschema/work-loop-next.schema.json` with `contract_version` and `x-spec`, plus its row in `contracts/README.md` | Repository maintainer | Conformance suite under `tests/roster/` over live emitter output | Schema validates real output, back-references this spec, and appears in the contract inventory |
| Current architecture | Applicable — the subsystem doc enumerates engine verbs, so a new verb makes it drift on landing | `docs/architecture/loop-infrastructure.md` | Repository maintainer | Entrypoint section names the verb and its read-only status | Doc describes the shipped verb set |
| Current product truth | Applicable — the skill payload is the product, and the shipped instructions and resumption reference change | `packs/core/.apm/skills/work-loop/**` and its regenerated projections | Repository maintainer | `make build-self-dry-run` reports no drift | Source edited, projections regenerated, drift gate clean |
| User-facing promise | Applicable — adopters drive these commands by hand | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | Repository maintainer | Adopter description of resuming through the verb and of what a recorded id makes replayable | Guide describes shipped behavior |
| Operations | Applicable — the manual-QA transcripts are the only evidence the assembled route works | `docs/specs/work-loop-next-projection/notes/qa-transcripts.md` | Implementing agent | Two recorded transcripts with actions, states, and exit codes | Both transcripts committed at that path |
| Release history | Applicable — a new public verb changes what a consumer can do, and a `contracts/` change requires a release indicator | `docs/product/changelog.md` free-standing dated entry with a `### Highlights` block | Repository maintainer | Entry at top level, not nested under `[Unreleased]` | Entry present at `##`, highlights projection regenerated |
| Reusable learning | Applicable — the state-versus-judgment split generalises | Routed through `project-knowledge` at the loop's capture gates | Implementing agent | Capture receipt, or a recorded `project-knowledge unavailable` | Receipt recorded or unavailability named |
| Decision rationale | Not applicable — the verb and the recording flag are internals of one subsystem, which a spec owns | — | — | — | — |
| Maintainer procedure | Not applicable — no maintainer runbook changes | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/core/.apm/skills/work-loop/**` as the source and regenerate the
  adapter skill trees with `make build-self`.
- Derive the projection's answer and every enumeration in its tests from the same
  transition tables the state machine enforces.
- Keep each execution wave green and shippable on its own.

### Ask first

- Changing an existing exit code, output line, or flag on any `loop-engine` verb:
  `init`, `transition`, `status`, `reset`.
- Changing an existing exit code, output line, or flag on any `loop-cohort` verb:
  `approve-plan`, `plan check-current`, `schedule`, `check`, `wave check`,
  `wave advance`, `record-attempt`, `review classify`, `review inspect`, and the
  four existing `review record` forms.
- Adding a field to `state.json` beyond the two this spec names.
- Adding a key to the record beyond the nine this spec names.
- Editing any file under `packages/agentbundle/`, which a protected-tree gate
  covers.

### Never do

- Add a third work-loop CLI, a new module boundary, or a new top-level directory.
- Add a runtime dependency to any shipped pack script.
- Let the projection verb write, create, truncate, delete, or lock any file.
- Introduce a reader of `state.json` outside `loop-cohort.py` and
  `_loop_guards.py`, or a reader of `engine-state.json` outside
  `loop-engine.py`.
- Put a filesystem path, a human-readable sentence, or any value carrying `/` or
  `\` into the record.
- Put a repository-only path, `ADR-NNNN`, or `RFC-NNNN` token into `packs/**` or
  `guides/**` content.
- Hand-edit a generated projection.

## Testing Strategy

- **The state-to-action projection: TDD**, because the mapping from state to one
  action is a compressible invariant over a closed, enumerable input set.
- **The read-only guarantee: TDD**, because byte-equality of the state files
  across a call is a compressible invariant.
- **Record shape and schema conformance: TDD**, exercised as a **contract** test
  validating live emitter output rather than a sample.
- **Recording replay, conflict refusal, and id-form refusal: TDD**, each an exact
  before-and-after state assertion.
- **Backward compatibility of the four existing recording forms: goal-based
  check** against a golden capture committed before the writer is touched,
  because the comparison value must exist independently of the change.
- **The architecture doc and the adopter guide: goal-based check**, one grep each
  for the shipped verb name and the replay description.
- **The assembled route: visual / manual QA**, covering one full run to `DONE`
  and one crash-and-resume through the recording branch. This skill is an
  artifact a user invokes, and a green unit suite does not establish that the
  assembled route works.
- **Projection drift and release consistency: goal-based check**, one command
  each.

## Acceptance Criteria

**Exit convention.** A record is emitted on a zero exit, including a record whose
`kind` is `stop` — computing "you must stop" is a success. A non-zero exit means
the command could not compute a record at all, and emits none.

**Input set.** Base triples are the image of the engine's transition tables, plus
one `last_event: null` triple per mode for a freshly initialised run, plus the two
legacy pairs `(plan-approved, CODE-IMPLEMENTATION)` and `(plan-approved, DONE)`
that the tables can no longer produce but persisted runs still carry. Each base
triple is crossed only with the dimensions that apply to it, per the plan's
applicability table: `spec.md` status and `plan.md` status apply at the two
spec-plan gates; recorded operation id and `last_review_clean_source` apply only
in `CODE-IMPLEMENTATION` and `CODE-HUMAN-GATE`; wave position applies only in
code mode after scheduling, and takes the three values *before the last wave*,
*at the last wave*, and *unscheduled*. A dimension that does not apply to a
triple contributes no cells. "The input set" below means this set.

### Wave 1 — the record

- [ ] **AC1.** On a zero exit, `loop-engine next <spec-dir> --json` writes exactly
  one JSON object to stdout, whose key set is exactly `schema_version`, `run_id`,
  `sequence`, `kind`, `action`, `parameters`, `complete_with`, `load`,
  `human_wait`.
- [ ] **AC2.** On a non-zero exit, `next` writes nothing to stdout.
- [ ] **AC3.** No diagnostic, refusal reason, or warning is written to stdout on
  any exit path.
- [ ] **AC4.** Every diagnostic, refusal reason, and stop reason is written to
  stderr.
- [ ] **AC5.** `kind` is one of exactly `agent`, `command`, `wait`, `stop`,
  `done`.
- [ ] **AC6.** `schema_version` is the literal string `work-loop-next.v1`.
- [ ] **AC7.** `run_id` equals the `run_id` in `engine-state.json`.
- [ ] **AC8.** `sequence` equals `transition_sequence` in `engine-state.json`.
- [ ] **AC9.** `complete_with` lists exactly the events legal from the record's
  state in the engine's transition table for the run's mode, and is empty exactly
  when that state has no outgoing transition.
- [ ] **AC10.** `human_wait` is true exactly when `kind` is `wait` or `action` is
  a member of the destructive-action set the plan enumerates.
- [ ] **AC11.** `action` is a member of the closed action vocabulary the plan
  enumerates.
- [ ] **AC12.** For each `action`, `parameters` carries exactly the key set the
  plan's per-action table declares for it, and no other key.
- [ ] **AC13.** Every `parameters` value matches `^[A-Za-z0-9:._-]+$`, or is an
  integer, or is a boolean.
- [ ] **AC14.** Every `load` entry is a member of the closed reference-identifier
  vocabulary the plan enumerates, and each identifier in that vocabulary resolves
  to a file shipped under the skill's `references/` tree.
- [ ] **AC15.** At least one record in the input set carries a non-empty `load`,
  and at least one carries a non-empty `parameters`.
- [ ] **AC16.** The record carries no schedule array, amendment history, finding
  fingerprint, or verbatim copy of either state file.
- [ ] **AC17.** No record in the input set exceeds 1024 bytes, measured as the
  UTF-8 byte length of the JSON object written to stdout, excluding any trailing
  newline.
- [ ] **AC18.** `contracts/jsonschema/work-loop-next.schema.json` validates the
  emitter's live output for at least one representative member of every
  `(kind, action)` pair the input set produces.
- [ ] **AC19.** That schema rejects a record carrying a `parameters` key the
  per-action table does not declare for that record's `action`.
- [ ] **AC20.** That schema carries `contract_version: "work-loop-next.v1"`,
  names this spec directory in `x-spec`, and has a row in `contracts/README.md`.

### Wave 2 — routing

- [ ] **AC21.** The shipped full-mode resumption routing table carries a
  machine-readable action-identifier column, so a row's prescribed action is
  parsed rather than transcribed.
- [ ] **AC22.** For every row of that table except the four rows this spec
  supersedes, the identifier in the row's action column equals the `action`
  `next` returns for that row's state, and equals the identifier the plan's
  row-to-action table records for it.
- [ ] **AC23.** The four superseded rows — `findings-remain` in
  `CODE-IMPLEMENTATION`, `reviewers-clean` in `CODE-HUMAN-GATE`, `plan-locked` in
  `DONE`, and `plan-approved` in `DONE` — each state the behavior this spec
  defines, so no row prescribes an action `next` contradicts.
- [ ] **AC24.** The `reviewers-clean` row no longer asserts that a clean-round
  replay is non-idempotent or that it double-increments the round count, because
  a recorded operation id makes that replay a no-op.
- [ ] **AC25.** For the two spec-plan terminal rows, `next` returns
  `kind: "done"`, and the stderr reason names both the destructive reset a later
  implementation request requires and the human confirmation that reset needs.
- [ ] **AC26.** For the code-mode terminal row, `last_event: done` in `DONE`,
  `next` returns `kind: "done"`.
- [ ] **AC27.** At the spec gate, a `spec.md` status of `Draft` yields
  `kind: "wait"`; `Approved` yields a `command` action firing the approval event;
  `Implementing`, `Shipped`, or `Archived` yields `kind: "stop"`.
- [ ] **AC28.** At the plan gate, a `plan.md` status of `Drafting` yields
  `kind: "wait"`; `Approved` yields a `command` action firing the approval event;
  `Executing` or `Done` yields `kind: "stop"`.
- [ ] **AC29.** Running `next` leaves `engine-state.json`, `state.json`, and
  `.loop-run/events.jsonl` byte-identical, and creates and deletes no file
  anywhere under the spec directory or the loop run directory.
- [ ] **AC30.** When an unpromoted engine-state temporary file or an unreplayed
  pending-events file is present, `next` returns `kind: "stop"` and the stderr
  reason names which artifact was found, because the state on disk is mid-write
  and the recovery that resolves it is a writing verb.
- [ ] **AC31.** With no `engine-state.json` and a spec carrying a light-mode
  marker line, `next` exits non-zero and names the legacy light-mode resumption
  table as the surface that answers instead.
- [ ] **AC32.** With no `engine-state.json` and no light-mode marker line, `next`
  exits non-zero with a stable code and names the ambiguity, without pointing at
  the light-mode table.
- [ ] **AC33.** When `engine-state.json` and `state.json` carry different
  `run_id` values, `next` returns `kind: "stop"`.
- [ ] **AC34.** When `engine-state.json` names a state that is neither a source
  nor a target in the transition table for its mode, `next` returns
  `kind: "stop"`.
- [ ] **AC35.** `loop-engine --help` lists `next` alongside `init`, `transition`,
  `status`, and `reset`.

### Wave 3 — replayable review recording

- [ ] **AC36.** A review round's operation id is `<run_id>:<transition_sequence>`
  read from `engine-state.json` at the time of the round, matching the form the
  shipped instructions already use for a recorded implementation attempt.
- [ ] **AC37.** `loop-cohort review record --operation-id <id>` exits non-zero
  and changes no field of `state.json` when `<id>` does not match
  `<expect-run-id>:<decimal-sequence>`.
- [ ] **AC38.** For each of the four recording forms, a first application carrying
  `--operation-id` produces the same `state.json` delta as the same form without
  the flag, except for the two fields this spec adds.
- [ ] **AC39.** `review record --operation-id <id>` replayed with the same payload
  exits 0 and leaves `review_round_count`, `review_retry_count`,
  `finding_fingerprints`, `previous_finding_fingerprints`,
  `last_review_clean_source`, and `last_review_clean_digest` unchanged from the
  first application.
- [ ] **AC40.** `review record --operation-id <id>` presented with a payload
  differing from the one recorded under that id exits non-zero and changes no
  field of `state.json`.
- [ ] **AC41.** Two review rounds separated by an engine transition receive
  different operation ids, and the second increments `review_round_count`.
- [ ] **AC42.** `review record` invoked without `--operation-id` produces the
  state transition and the stdout line recorded in the committed golden capture,
  for each of the four existing forms: `--fingerprint`, `--direct-clean-file`,
  `--report --adjudication`, and `--all-skipped`.
- [ ] **AC43.** `state.json` carries the recorded review-record operation id and a
  digest of the payload recorded under it.
- [ ] **AC44.** The shipped state-schema reference documents both fields, and the
  bundled `assets/state.json` template carries both.
- [ ] **AC45.** Every `review record` invocation in `SKILL.md` and in the skill's
  `references/` tree passes `--operation-id`, where an invocation is a line
  inside a fenced code block that names the cohort script and the `review record`
  verb. A prose mention outside a fenced code block is not an invocation.
- [ ] **AC46.** For `findings-remain` in `CODE-IMPLEMENTATION` with the current
  round's operation id recorded in `state.json`, `next` returns the action
  following the recording rather than a recording action.
- [ ] **AC47.** For `findings-remain` in `CODE-IMPLEMENTATION` with the current
  round's operation id absent, `next` returns `kind: "stop"` and the stderr
  reason names the round's expected operation id and the persisted adjudication
  artifact whose findings the recording needs.
- [ ] **AC48.** For `reviewers-clean` in `CODE-HUMAN-GATE`, `next` returns
  `kind: "wait"`.
- [ ] **AC49.** On the changes-requested continuation from `CODE-HUMAN-GATE` with
  a recorded `last_review_clean_source`, `next` names the matching recording form
  and carries in `parameters` the operation id recorded in `state.json`, not a
  freshly computed one.
- [ ] **AC50.** Replaying that continuation's recording command leaves
  `review_round_count` unchanged.
- [ ] **AC51.** On that continuation with no recorded `last_review_clean_source`,
  `next` returns `kind: "stop"`.

### Wave 4 — the shipped surface

- [ ] **AC52.** The entrypoint section of
  `docs/architecture/loop-infrastructure.md` names `next` in the
  `loop-engine.py` verb set and records it as read-only.
- [ ] **AC53.** `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  describes resuming through `next`.
- [ ] **AC54.** That guide describes what a recorded operation id makes
  replayable.
- [ ] **AC55.** A full-mode `code`-mode loop driven end-to-end through the shipped
  instructions on a throwaway spec directory reaches `DONE`, with the observed
  action sequence, final engine state, and per-command exit codes recorded at the
  destination the Durable Outputs table names.
- [ ] **AC56.** A session interrupted between firing `findings-remain` and
  recording the round, then resumed, reaches a correct next action with no double
  increment of `review_round_count`, recorded at that same destination.
- [ ] **AC57.** The recorded transcripts state what the two sessions do not
  exercise.
- [ ] **AC58.** `docs/product/changelog.md` carries a free-standing
  `## [core][<version>] — YYYY-MM-DD` entry at top level rather than nested under
  `[Unreleased]`.
- [ ] **AC59.** That entry contains a `### Highlights` block.
- [ ] **AC60.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` read the same version, one minor above
  the value on the base branch at commit time.
- [ ] **AC61.** `make build-self-dry-run` reports no projection drift.
- [ ] **AC62.** The generated highlights projection matches the changelog entry.

## Follow-ons

None. The always-loaded instruction surface and its ceiling are a separate
contract that depends on this one; they are not deferred work from this
checklist.

## Assumptions

- Technical: `engine-state.json` is read only by `loop-engine.py`, and
  `state.json` by `loop-cohort.py` and `_loop_guards.py`; the shared guard module
  has no engine-state reader, so the projection reads engine state through the
  engine's own reader (source: `_loop_guards.py` contains `engine-state` only in
  two comments; `loop-cohort.py` only in one)
- Technical: the engine's two crash-recovery routines are reachable only from its
  writing verbs, so a read-only verb must detect the mid-write artifacts and stop
  rather than repair them (source:
  `packs/core/.apm/skills/work-loop/scripts/loop-engine.py` calls
  `_recover_engine_state_tmp` and `_recover_pending` at `:1108`, `:1269`, and
  `:1279`, all inside `cmd_transition` and `cmd_reset`, and never from
  `cmd_status`)
- Technical: two shipped tests pin the literal prose of the two resumption rows
  this spec rewrites, and the `reviewers-clean` row's pinned phrases become false
  once a recorded operation id makes the replay idempotent (source:
  `packs/core/tests/skills/work-loop/test_loop_engine.py:2746` and `:2817`)
- Technical: the engine's transition tables contain 10 states and 15 events, and
  the skill ships 15 reference files, so the action, event, and load vocabularies
  are all closed and small enough to enumerate in the plan (source: enumeration
  over `loop-engine.py:525-560` and the `references/` tree, 2026-08-31)
- Technical: id-keyed idempotency already works in the cohort writer —
  `record-attempt` no-ops on a repeated cycle id and validates its
  `<run_id>:<digits>` form against `--expect-run-id` (source:
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:1552-1575`)
- Technical: `--operation-id` composes with all four existing recording forms
  because it attaches outside the mutually exclusive group, and `review record`
  already requires `--expect-run-id`, so validating the id's form needs no new
  cross-file read (source:
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:2224-2257`)
- Technical: refusal messages already go to stderr in the engine (source:
  `loop-engine.py:947-949`)
- Technical: a widest padded record measures 425 bytes serialized compact, so the
  1024-byte bound has headroom for ordinary growth while still detecting an
  embedded state dump; the bound is asserted in the suite rather than enforced as
  a runtime refusal, because a refusal would leave the loop with no next action
  (source: a serialization measurement over a deliberately padded record,
  2026-08-31)
- Technical: `review record` appears 44 times across the shipped skill, of which
  many are prose descriptions in field tables rather than commands, which is why
  an invocation is defined by its fenced code block (source: a grep over
  `packs/core/.apm/skills/work-loop/`, 2026-08-31)
- Technical: new suites under `packs/core/tests/skills/work-loop/` and under
  `tests/roster/` both run in `make test`, which names the first directly and the
  second through `pytest tests/` (source: `Makefile:544`, `Makefile:529`)
- Technical: a JSON payload contract lives at
  `contracts/jsonschema/<name>.schema.json` carrying `contract_version` and
  `x-spec`, validated from `tests/roster/` (source:
  `contracts/jsonschema/semantic-surface-resolution.schema.json`)
- Technical: `next` cannot determine a round's warranted reviewer roster, because
  no state field records it and the warrant is a judgment over the diff; so an
  absent operation id yields a stop rather than a recording action, and this
  contract claims decidability rather than automatic recovery on that row
  (source: the `state.json` field table records no roster;
  `references/pre-execute-review.md:91` names artifacts per reviewer role)
- Technical: `next` does not answer legacy light-mode resumption, which has no
  engine state to read, and refuses cleanly instead (source: user confirmation
  2026-08-31)
- Process: no RFC is owed; every change is additive and the RFC reserved list
  covers charter, authority, security trust model, and withdrawal of a published
  promise (source: `docs/CONVENTIONS.md:338-349`)
- Process: no ADR is owed; the verb and the recording flag are internals of one
  subsystem, which a spec owns (source: `docs/CONVENTIONS.md:291`, user
  confirmation 2026-08-31)
- Process: editing any file under `packages/agentbundle/` outside `build/recipes/`
  or a `tests/` path trips a protected-tree gate requiring an engine-scoped RFC
  trailer, so no task here edits that tree (source:
  `tools/lint-catalogue-curation-guard.py` classifies
  `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py` as a
  hit and `tools/lint-*.py` as no hit; the gate runs at
  `tools/repo/build_gate_chain.py:305`)
- Process: a `contracts/` change requires a release indicator in the same change,
  which the changelog entry satisfies, because `contracts/` is absent from the
  non-impacting prefix list (source:
  `tools/repo/check_release_impact.py` `NON_IMPACTING_PREFIXES`)
- Process: the core pack bumps minor, because a new CLI verb is a new primitive
  (source: `packs/AGENTS.md:44-46`)
- Process: shipped pack content and adopter guides state rules directly and cite
  no repository-only path (source: `packs/AGENTS.md:49-52`,
  `tools/lint-guides-no-repo-only-refs.py`)
- Process: the changelog entry is free-standing at `##` and never nested under
  `[Unreleased]`, or the highlights projection never sees it (source:
  `docs/product/changelog.md:11-19`)
- Process: `packs/core/.apm/**` is the source and the adapter skill trees are
  regenerated projections, byte-identical to source today (source:
  `Makefile:67-78`, `diff -q` between source and the Claude projection)
- Product: this contract delivers the projection and replayable recording; it
  makes no claim about the size of the always-loaded instruction surface, which a
  dependent contract owns (source: user confirmation 2026-08-31)
- Product: this delivery provides mechanism, not a longitudinal study of
  completion rate or recovery refusals across sessions; those need many real runs
  and are outside this contract (source: user confirmation 2026-08-31)
