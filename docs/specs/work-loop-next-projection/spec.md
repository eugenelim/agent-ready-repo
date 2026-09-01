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

The agent gets one authoritative action per turn instead of reconstructing it from
two state dumps and a fifteen-row prose routing table. The adopter driving these
commands by hand gets a single call in place of that sequence.

The state-to-action mapping is a set of tables in this document — [Preconditions](#preconditions),
[Discriminators](#discriminators), [Routing](#routing), and
[Action attributes](#action-attributes) — not prose. Those tables are the
contract; the acceptance criteria assert properties *of* them (totality,
determinism, closure, and each row's observable), so adding a state or an action
changes a table row rather than a criterion.

Reducing the always-loaded instruction surface is the separate contract this one
enables; no criterion here changes `SKILL.md`'s size.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the record is a machine-read payload | `contracts/jsonschema/work-loop-next.schema.json` with `contract_version` and `x-spec`, plus its row in `contracts/README.md` | Repository maintainer | Conformance suite under `tests/roster/` over live emitter output | Schema validates real output, back-references this spec, and appears in the contract inventory |
| Current architecture | Applicable — the subsystem doc enumerates engine verbs, so a new verb makes it drift on landing | `docs/architecture/loop-infrastructure.md` | Repository maintainer | Entrypoint section names the verb and its read-only status | Doc describes the shipped verb set |
| Current product truth | Applicable — the skill payload is the product, and the shipped resumption reference changes | `packs/core/.apm/skills/work-loop/**` and its regenerated projections | Repository maintainer | `make build-self-dry-run` reports no drift | Source edited, projections regenerated, drift gate clean |
| User-facing promise | Applicable — adopters drive these commands by hand | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | Repository maintainer | Adopter description of resuming through the verb | Guide describes shipped behavior |
| Operations | Applicable — the manual-QA transcripts are the only evidence the assembled route works | `docs/specs/work-loop-next-projection/notes/qa-transcripts.md` | Implementing agent | Two recorded transcripts with actions, states, and exit codes | Both transcripts committed at that path |
| Release history | Applicable — a new public verb changes what a consumer can do, and a `contracts/` change requires a release indicator | `docs/product/changelog.md` free-standing dated entry with a `### Highlights` block | Repository maintainer | Entry at top level, not nested under `[Unreleased]` | Entry present at `##`, highlights projection regenerated |
| Reusable learning | Applicable — the state-versus-judgment split generalises | Routed through `project-knowledge` at the loop's capture gates | Implementing agent | Capture receipt, or a recorded `project-knowledge unavailable` | Receipt recorded or unavailability named |
| Decision rationale | Not applicable — the verb is an internal of one subsystem, which a spec owns | — | — | — | — |
| Maintainer procedure | Not applicable — no maintainer runbook changes | — | — | — | — |

## The contract tables

The four tables below are normative. An implementation carries its own copy of
the routing and attribute data; conformance is checked by comparing that copy
with these tables and by driving the live command into every row.

### Domain

The **key** the projection answers is
`(mode, engine state, last_event, discriminator)`.

`(mode, engine state, last_event)` ranges over the **base keys**: for each mode,
the image of that mode's transition table — every `(event, target_state)` pair it
contains — plus the extra keys below, which the current tables cannot produce but
which reach the verb anyway.

| Mode | `last_event` | Engine state | Origin |
| --- | --- | --- | --- |
| both | `null` | `SPEC-PLAN-DRAFTING` | A freshly initialised run, before its first transition |
| code | `plan-approved` | `CODE-IMPLEMENTATION` | A pre-split persisted run |
| spec-plan | `plan-approved` | `DONE` | A pre-split persisted run |

That yields 19 base keys in `code` mode and 10 in `spec-plan`, 29 in all.

Each base key is crossed with the values of whichever Discriminator applies to
it, giving **32 domain members in `code` mode and 22 in `spec-plan`, 54 in all**.
A base key no Discriminator applies to contributes exactly one member. This
document is the sole home of that figure; the plan references it rather than
restating it.

Wave position is deliberately not a Discriminator: it changes no row's action,
and enters the record only as `cohort.wave-advance`'s `from_index` parameter.

### Discriminators

Each Discriminator's value set is fixed **here**, from a source outside the
Routing table, so that deleting a Routing row shrinks the coverage without
shrinking the domain.

| # | Applies to | Read from | Values | Value source |
| --- | --- | --- | --- | --- |
| D1 | `SPEC-HUMAN-GATE` | `spec.md`'s Status line | `Draft`, `Approved`, `Implementing`, `Shipped`, `Archived`, `unreadable` | The five-token spec Status vocabulary `lint-spec-status.py` enforces, plus one value for no usable status |
| D2 | `PLAN-HUMAN-GATE` | `plan.md`'s Status line | `Drafting`, `Approved`, `Executing`, `Done`, `unreadable` | The four-token plan Status vocabulary `lint-spec-status.py` enforces, plus one value for no usable status |
| D3 | `SPEC-PLAN-APPROVED` | `plan_review_status` and whether `schedule_waves` is empty, in `state.json` | `pending+unscheduled`, `pending+scheduled`, `approved+unscheduled`, `approved+scheduled` | The full cross product of the two fields' domains in `references/state-schema.md` |
| D4 | `CODE-IMPLEMENTATION` with `last_event: findings-remain` | `last_review_record_operation_id` in `state.json`, compared with `<run_id>:<transition_sequence>` | `matches`, `does-not-match` | A boolean comparison |

`unreadable` is **one** value, not two. The canonical reader raises for a file it
cannot read and returns nothing for a file with no recognised Status line; both
outcomes mean the same thing to this projection — no usable status — and both
route identically, so the contract does not distinguish them.

`D3` is the full cross product rather than the reachable subset. Including
`pending+scheduled` costs one row's worth of coverage and removes a reachability
argument the criteria would otherwise depend on.

### Preconditions

Evaluated in order; the first matching row decides, and Routing runs only when
none matches. `P1` through `P4` carry four distinct non-zero exit codes, and the
same condition always yields the same code.

| # | Condition | Exit | Record | stderr names |
| --- | --- | --- | --- | --- |
| P1 | No `engine-state.json`, and `spec.md` carries the light-mode marker defined below | non-zero | none | the legacy light-mode resumption table as the surface that answers instead |
| P2 | No `engine-state.json`, and no light-mode marker | non-zero | none | the ambiguity, without pointing at the light-mode table |
| P3 | `engine-state.json` is unreadable, or its `schema_version` is not `1` | non-zero | none | which of the two it was |
| P4 | `engine-state.json` lacks a well-formed `run_id`, `transition_sequence`, or `mode` | non-zero | none | which field failed, and the offending value under the bound AC14 sets |
| P5 | An unpromoted engine-state temporary file, or an unreplayed pending-events file, is present | zero | `halt` | which artifact was found, and that recovery is a writing verb's job |
| P6 | `state.json` is missing, is unreadable, carries no `run_id`, or carries one differing from `engine-state.json`'s | zero | `halt` | which of the four it was |
| P7 | The `(engine state, last_event)` pair is not a base key for the run's mode | zero | `halt` | the offending pair |

**P4's well-formedness.** `run_id` is a canonical lowercase UUID,
`transition_sequence` a non-negative integer, and `mode` one of `code` or
`spec-plan`. All three fail before any record is built rather than routing to a
`halt`, because the record cannot be constructed without them: `run_id` and
`transition_sequence` are two of its nine keys, and `mode` selects the transition
table `complete_with` is derived from.

**P1's light-mode marker.** With HTML comments removed, a line in `spec.md`
*before its first `##` heading* matching
`^[\s>*_`-]*Mode[\s*_`]*:?[\s*_`]*light\b`, case-insensitively. The zone
restriction is load-bearing: the marker is discussed in the body of specs that
are about it, and those mentions must not route a run to P1.

**P5's scope.** Detection is by presence alone; neither artifact's content is
read, so nothing here parses an attacker-influenceable file. The pending-events
file lives in the repository-shared run directory rather than the spec directory,
so its presence halts every run in the repository, not only this one. That is the
intended behaviour: the artifact records an interrupted write whose replay is a
writing verb's job, and a read-only verb cannot tell whose.

### Routing

`*` in the `last_event` column matches every base key reaching that state. `both`
in the Mode column matches either mode.

| Row | Mode | Engine state | `last_event` | Discriminator | Action |
| --- | --- | --- | --- | --- | --- |
| R1 | both | `SPEC-PLAN-DRAFTING` | `*` | — | `spec.draft` |
| R2 | both | `SPEC-PLAN-REVIEW` | `*` | — | `spec.review` |
| R3 | both | `SPEC-HUMAN-GATE` | `*` | D1 `Draft` | `await-spec-approval` |
| R4 | both | `SPEC-HUMAN-GATE` | `*` | D1 `Approved` | `engine.spec-approved` |
| R5 | both | `SPEC-HUMAN-GATE` | `*` | D1 `Implementing`, `Shipped`, `Archived`, `unreadable` | `halt` |
| R6 | both | `PLAN-HUMAN-GATE` | `*` | D2 `Drafting` | `await-plan-approval` |
| R7 | both | `PLAN-HUMAN-GATE` | `*` | D2 `Approved` | `engine.plan-approved` |
| R8 | both | `PLAN-HUMAN-GATE` | `*` | D2 `Executing`, `Done`, `unreadable` | `halt` |
| R9 | both | `SPEC-PLAN-APPROVED` | `*` | D3 `pending+unscheduled`, `pending+scheduled` | `cohort.approve-plan` |
| R10 | code | `SPEC-PLAN-APPROVED` | `*` | D3 `approved+unscheduled` | `cohort.schedule` |
| R11 | code | `SPEC-PLAN-APPROVED` | `*` | D3 `approved+scheduled` | `engine.plan-locked` |
| R12 | spec-plan | `SPEC-PLAN-APPROVED` | `*` | D3 `approved+unscheduled`, `approved+scheduled` | `engine.plan-locked` |
| R13 | code | `CODE-IMPLEMENTATION` | `plan-locked`, `plan-approved`, `blocker-applied` | — | `implement` |
| R14 | code | `CODE-IMPLEMENTATION` | `wave-passed` | — | `cohort.wave-advance` |
| R15 | code | `CODE-IMPLEMENTATION` | `gates-failed` | — | `cohort.record-attempt` |
| R16 | code | `CODE-IMPLEMENTATION` | `findings-remain` | D4 `matches` | `implement` |
| R17 | code | `CODE-IMPLEMENTATION` | `findings-remain` | D4 `does-not-match` | `halt` |
| R18 | code | `CODE-VERIFICATION` | `wave-complete` | — | `run-gates` |
| R19 | code | `CODE-REVIEW` | `gates-clean` | — | `run-review` |
| R20 | code | `CODE-HUMAN-GATE` | `reviewers-clean` | — | `await-merge-decision` |
| R21 | code | `DONE` | `done` | — | `complete` |
| R22 | spec-plan | `DONE` | `plan-locked`, `plan-approved` | — | `reset-and-reinit` |

### Action attributes

`kind`, the `parameters` key set, `load`, and `human_wait` are functions of
`action` alone, so they are tabled once here rather than repeated per routing row.
`—` in the `parameters` column means the empty object, never an absent key.

| Action | `kind` | `parameters` keys | `load` | `human_wait` |
| --- | --- | --- | --- | --- |
| `spec.draft` | `agent` | — | `ref:pre-execute-review` | false |
| `spec.review` | `agent` | — | `ref:pre-execute-review`, `ref:finding-adjudication` | false |
| `implement` | `agent` | — | `ref:verification-modes` | false |
| `run-gates` | `agent` | — | `ref:pre-flight-failures` | false |
| `run-review` | `agent` | — | `ref:finding-adjudication`, `ref:review-verdict-record` | false |
| `engine.spec-approved` | `command` | — | — | false |
| `engine.plan-approved` | `command` | — | — | false |
| `engine.plan-locked` | `command` | — | — | false |
| `cohort.approve-plan` | `command` | — | — | false |
| `cohort.schedule` | `command` | — | — | false |
| `cohort.wave-advance` | `command` | `from_index` | — | false |
| `cohort.record-attempt` | `command` | `cycle_id` | `ref:pre-flight-failures` | false |
| `await-spec-approval` | `wait` | — | — | true |
| `await-plan-approval` | `wait` | — | — | true |
| `await-merge-decision` | `wait` | — | `ref:session-resumption` | true |
| `complete` | `done` | — | — | false |
| `reset-and-reinit` | `done` | — | `ref:session-resumption` | true |
| `halt` | `stop` | — | — | false |

`human_wait` describes the record, not the engine's `pending_human_wait`. At a
human gate whose approver has already written the decision — R4 and R7 — the
engine still reports `pending_human_wait: true` while the record reports
`human_wait: false`, because nothing is left to wait for: the action is firing the
event the approver's write authorised. `reset-and-reinit` runs the other way: it
is a `done`-kind action reporting `human_wait: true`, because R22's reset is
destructive and the shipped resumption rows require explicit human confirmation
before it.

**What `complete_with` does not carry.** It names *events*, not invocations. Two
of them take required transition arguments the record does not supply:
`wave-passed` needs `--wave-index`, and `contract-amendment` needs
`--owner-authority-ref` and `--reason-ref`. An agent firing either still reads
those values from engine state. Adding them to the record would add a key, which
Boundaries routes to *Ask first*.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit `packs/core/.apm/skills/work-loop/**` as the source and regenerate the
  adapter skill trees with `make build-self`.
- Derive the base keys and `complete_with` from the same transition tables the
  state machine enforces, at runtime, rather than transcribing either.
- Keep each execution wave green and shippable on its own.

### Ask first

- Changing an existing exit code, output line, or flag on any `loop-engine` verb:
  `init`, `transition`, `status`, `reset`.
- Changing an existing exit code, output line, or flag on any `loop-cohort` verb.
- Adding a row, a column, or a key to any of the four tables above.
- Editing any file under `packages/agentbundle/`, which a protected-tree gate
  covers.

### Never do

- Add a third work-loop CLI, a new module boundary, or a new top-level directory.
- Add a runtime dependency to any shipped pack script.
- Let the projection verb write, create, truncate, delete, or lock any file.
- Introduce a reader of `state.json` outside `loop-cohort.py` and
  `_loop_guards.py`, or a reader of `engine-state.json` outside `loop-engine.py`.
- Put a filesystem path, a human-readable sentence, or any value carrying `/` or
  `\` into the record.
- Put a repository-only path, `ADR-NNNN`, or `RFC-NNNN` token into `packs/**` or
  `guides/**` content.
- Hand-edit a generated projection.

## Testing Strategy

- **Table properties — totality, determinism, closure, and each row's observable:
  TDD.** The tables are a compressible invariant over a closed, enumerable domain.
  The property tests parse the tables from this document and compare them with the
  implementation's own copy, so a passing run means two independent expressions of
  the mapping agree rather than one artifact matching itself.
- **Table parsing lives in `tests/roster/`**, not in a pack test:
  `tools/lint-pack-test-boundary.py` forbids a pack test from reading above its
  own pack, and this document is above `packs/core/`.
- **The read-only guarantee: TDD**, because byte-equality of the state files
  across a call is a compressible invariant.
- **Record shape, the stderr bound, and schema conformance: TDD**, the last
  exercised as a **contract** test validating live emitter output rather than a
  sample.
- **Confinement and reader reuse: TDD**, driven by hostile fixtures — a symlink,
  a non-regular file, and an oversized file at each read target.
- **The shipped resumption table's action column, and the consumer's trust
  posture: TDD**, with the expected identifiers parsed from the shipped table
  rather than transcribed into the test.
- **The architecture doc and the adopter guide: goal-based check**, one grep each.
- **The assembled route: visual / manual QA**, covering one full run to `DONE` and
  one crash-and-resume through the recording branch. This skill is an artifact a
  user invokes, and a green unit suite does not establish that the assembled route
  works.
- **Projection drift and release consistency: goal-based check**, one command
  each.

## Acceptance Criteria

**Exit convention.** A record is emitted on a zero exit, including a record whose
`kind` is `stop` — computing "you must stop" is a success. A non-zero exit means
the command could not compute a record at all, and emits none.

### The tables

- [ ] **AC1 — totality.** Every member of the domain matches at least one Routing
  row. The domain is built at runtime from the engine's transition tables plus the
  extra base keys, crossed with the Discriminators table's value sets — never with
  values read out of the Routing table. Deleting any Routing row leaves at least
  one domain member uncovered, and that holds for all 22 rows, not only the ten
  that carry no Discriminator.
- [ ] **AC2 — determinism.** No member of the domain matches more than one Routing
  row. Widening any row's Mode, `last_event`, or Discriminator column so that it
  overlaps another row fails this criterion.
- [ ] **AC3 — each row's observable.** For every Routing row, a run driven into a
  domain member that row matches yields a record whose `action` is that row's
  action. The expected action is parsed from the Routing table's Mode, Engine
  state, `last_event`, and Discriminator columns — never obtained from the
  implementation's own routing data or discriminator resolver. Both a changed row
  action and a swapped discriminator branch fail this criterion; the second is the
  mutation that distinguishes it from AC1 and AC2, so exchanging R3's and R4's
  Discriminator cells in the implementation must redden it.
- [ ] **AC4 — closure.** Every action named in a Routing row has exactly one Action
  attributes row, and every Action attributes row is named by at least one Routing
  row.
- [ ] **AC5 — attribute observable.** For every emitted record, `kind`, the
  `parameters` key set, the `load` list, and `human_wait` equal the Action
  attributes row for that record's `action`. Changing any single cell of that
  table fails this criterion.
- [ ] **AC6 — preconditions.** Each Preconditions row, exercised in isolation and
  against a state that also matches a later row, produces that row's exit and
  record, and its stderr names what the row's last column requires. P1's marker
  match is exercised against every marker spelling the live corpus carries and
  against a body-zone mention that must not match. P1 through P4 return four
  distinct exit codes, asserted as mutually distinct rather than as four literals.

### The record

- [ ] **AC7.** On a zero exit, `loop-engine next <spec-dir> --json` writes exactly
  one JSON object to stdout, whose key set is exactly `schema_version`, `run_id`,
  `sequence`, `kind`, `action`, `parameters`, `complete_with`, `load`,
  `human_wait`. On a non-zero exit it writes nothing to stdout.
- [ ] **AC8.** No diagnostic, refusal reason, or stop reason is written to stdout
  on any exit path; every one of them is written to stderr.
- [ ] **AC9.** `schema_version` is the literal string `work-loop-next.v1`; `run_id`
  equals the `run_id` in `engine-state.json` and matches the canonical lowercase
  UUID form P4 requires; and `sequence` equals its `transition_sequence`. Pinning
  either derived field to a constant fails this criterion, and so does emitting a
  record for state whose `run_id` does not match that form.
- [ ] **AC10.** `complete_with` lists exactly the events legal from the record's
  state in the engine's transition table for the run's mode, read at runtime, and
  is empty exactly when that state has no outgoing transition. Pinning it to a
  constant fails this criterion.
- [ ] **AC11.** Every `parameters` value matches `^[A-Za-z0-9:._-]+$`, or is an
  integer, or is a boolean; and every `load` entry resolves to a file shipped
  under the skill's `references/` tree, with the resolution built by globbing that
  tree rather than transcribed.
- [ ] **AC12.** No record carries a schedule array, amendment history, finding
  fingerprint, or verbatim copy of either state file. A fingerprint is the case
  this criterion uniquely catches: a 64-character hex digest satisfies AC11's
  character class and would occupy a declared `parameters` key without violating
  AC5 or AC7.
- [ ] **AC13.** No record in the domain exceeds 1024 bytes, measured as the UTF-8
  byte length of the JSON object written to stdout, excluding any trailing
  newline. The test also pins the observed maximum, so growth is visible before it
  reaches the bound.
- [ ] **AC14.** Every value the verb interpolates into a stderr reason from a state
  file or from `argv` is length-capped at the bound the shared guard module
  already applies to one external scalar, and is delimited so a reader can see
  where untrusted text starts and ends. A whole reason is capped at that module's
  reason bound. A planted oversized `run_id` therefore reaches stderr truncated
  and quoted, not verbatim; removing either the cap or the delimiters fails this
  criterion.

### Reads

- [ ] **AC15.** Every file the verb opens — both state files, both artifact Status
  files, and both crash artifacts — is resolved through the existing spec-directory
  confinement and read through the shared guard module's readers, with no direct
  `open` or `read_text` anywhere in the verb's path. A symlink, a non-regular file,
  and an oversized file at each read target are each refused rather than followed,
  read, or blocked on.
- [ ] **AC16.** Running `next` leaves `engine-state.json`, `state.json`, and
  `.loop-run/events.jsonl` byte-identical, and creates and deletes no file
  anywhere under the spec directory or the loop run directory. This holds on every
  Preconditions row too, including the two that detect a mid-write crash artifact.

### The published schema

- [ ] **AC17.** `contracts/jsonschema/work-loop-next.schema.json` validates the
  emitter's live output for at least one record per Action attributes row, and
  rejects a record carrying a `parameters` key that table does not declare for
  that record's `action`.
- [ ] **AC18.** That schema carries `contract_version: "work-loop-next.v1"`, names
  this spec directory in `x-spec`, and has a row in `contracts/README.md` whose
  CLI-data column reads `no`.

### The shipped surface

- [ ] **AC19.** The shipped full-mode resumption routing table carries a
  machine-readable action-identifier column, and for every one of its rows the
  identifiers in that column are exactly the **union across both modes** of the
  Routing actions whose `(mode, engine state, last_event)` key matches that row's
  `(last_event, state)` pair, with both sides parsed rather than transcribed.
  Changing one identifier fails this criterion.
- [ ] **AC20.** The shipped instructions state the consumer's trust posture: that
  the record is data rather than instruction, that `action` is matched against the
  closed Action attributes vocabulary and an unrecognised value halts, that a
  `load` entry outside the closed reference vocabulary halts, and that no field of
  the record is executed or interpreted as a command. A grep over the shipped text
  finds each of those four statements.
- [ ] **AC21.** `loop-engine --help` lists `next` alongside `init`, `transition`,
  `status`, and `reset`.
- [ ] **AC22.** The entrypoint section of
  `docs/architecture/loop-infrastructure.md` names `next` in the `loop-engine.py`
  verb set and records it as read-only.
- [ ] **AC23.** `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  describes resuming through `next`.

### Evidence and release

- [ ] **AC24.** Two manual-QA transcripts are committed at the destination the
  Durable Outputs table names: a full-mode `code`-mode loop driven end-to-end
  through the shipped instructions on a throwaway spec directory reaching `DONE`,
  and a session interrupted between firing `findings-remain` and recording the
  round then resumed, reaching a correct next action with no double increment of
  `review_round_count`. Each records the observed action sequence, final engine
  state, and per-command exit codes, and states what it does not exercise.
- [ ] **AC25.** `docs/product/changelog.md` carries a free-standing
  `## [core][<version>] — YYYY-MM-DD` entry at top level rather than nested under
  `[Unreleased]`, containing a `### Highlights` block; and `packs/core/pack.toml`
  and `packs/core/.claude-plugin/plugin.json` read the same version, one minor
  above the value on the base branch at commit time.
- [ ] **AC26.** `make build-self-dry-run` reports no projection drift, and the
  generated highlights projection matches the changelog entry.

## Follow-ons

None. The always-loaded instruction surface and its ceiling are a separate
contract that depends on this one; they are not deferred work from this checklist.

## Assumptions

- Technical: the replayable review recording this projection reads shipped
  separately and is not respecified here — `--operation-id`, its form check,
  replay and conflict behaviour, `last_review_record_operation_id` and
  `last_review_record_payload_digest`, the state-schema reference, and the
  rewritten `reviewers-clean` resumption row are all present (source:
  `docs/specs/review-record-idempotency/spec.md` at `Status: Shipped`, core
  2.18.2, PR #1192; `references/state-schema.md` documents both fields, and all
  seven fenced `review record` invocations in the shipped skill pass the flag)
- Technical: AC19 is purely additive — every shipped resumption row's prescribed
  action already agrees with the Routing table, so no row is rewritten and the two
  tests that pin row prose keep passing. They locate their row by substring and
  assert phrases within the matched line, so an added column does not disturb
  either (source: `test_loop_engine.py:2775-2776` matches the `findings-remain`
  row and requires "stale fingerprint baseline", "under-count", and "do NOT
  auto-reissue", all of which R16 and R17 preserve; `:2846`
  `test_reviewers_clean_skill_prose_obligations` matches the same way)
- Technical: the stderr bound AC14 requires already exists and is already
  calibrated — the shared guard module caps one interpolated external scalar at
  120 characters and a whole reason at 4000, having found that a 100 KB `run_id`
  in `state.json` produced a 100,055-character reason on agent-captured stderr.
  The engine's own `_diag`/`stop()` path escapes control characters and applies
  neither cap, so AC14 is reuse of a calibrated control rather than a new one
  (source: `_loop_guards.py` `_MAX_SCALAR_CHARS` and `_MAX_REASON_CHARS` at
  `:109-123`, the chokepoint comment at `:264-270`; `loop-engine.py:135-137`,
  `:964-966`)
- Technical: `next` runs unlocked by construction. `_statelock` guards a path by
  creating a sibling lock file, which AC16 forbids, so the two state files are
  sampled at different instants and a concurrent writing verb can produce a torn
  pair. P6's `run_id` comparison bounds only cross-*run* confusion, because
  `run_id` is constant within a run; it does not bound a `plan_review_status`,
  `schedule_waves`, or `transition_sequence` value captured mid-write. This is
  accepted: the verb is advisory, the agent re-reads before acting, and every
  writing verb it names re-validates under the lock. P5 covers the one torn state
  that is detectable from disk (source: `_statelock.py:122-124`)
- Technical: the two state files keep their owners, so the projection reads engine
  state through the engine's own reader and cohort state through the shared guard
  API (source: `_loop_guards.py` names `engine-state` only in two comments;
  `loop-cohort.py` in two, at `:94` and `:1920`)
- Technical: the canonical Markdown status reader raises for a file it cannot read
  and returns nothing for a file with no recognised Status line, which is why D1
  and D2 collapse both outcomes into one `unreadable` value (source:
  `_loop_guards.py` `read_md_status` at `:891-923`)
- Technical: the light-mode marker regex P1 names was validated against the live
  corpus before this contract was opened: over `docs/specs/*/spec.md` with HTML
  comments stripped, it matches in the pre-`##` zone for exactly the 37 specs that
  carry a real marker — across all six observed spellings, including
  `**Mode:** light`, `- **Mode:** light`, `> Mode: light`, and a backticked form —
  with no misses and no over-matches, and the zone restriction correctly excludes
  the body-prose mention in `direct-light-execution/spec.md` (source: a corpus
  scan, 2026-09-01)
- Technical: the engine's two crash-recovery routines are reachable only from its
  writing verbs, so a read-only verb must detect the mid-write artifacts and stop
  rather than repair them (source: in
  `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`,
  `_recover_engine_state_tmp` and `_recover_pending` have exactly four call sites
  — `:479` inside `_recover_pending` itself, `:1125` in `cmd_init`, and `:1289`
  and `:1299` in `cmd_transition` — and none in `cmd_status`, the existing
  read-only verb)
- Technical: the engine's transition tables contain 10 states and 15 events, and
  the skill ships 15 reference files, so the state, event, and load vocabularies
  are closed and small (source: `_BOTH_TRANSITIONS`, `_CODE_TRANSITIONS`, and
  `_SPEC_PLAN_TRANSITIONS` at `loop-engine.py:533-566`; a glob over
  `references/`, 2026-09-01)
- Technical: `plan_review_status` and `schedule_waves` make the three commands
  `SPEC-PLAN-APPROVED` requires — `approve-plan`, `schedule`, `plan-locked` —
  distinguishable without an engine transition between them, which is why R9-R12
  discriminate on cohort state rather than returning the same action three times
  (source: `references/state-schema.md` field table)
- Technical: the widest record the tables can produce measures 331 bytes
  serialized compact — `cohort.record-attempt` at `CODE-IMPLEMENTATION`, carrying a
  UUID `cycle_id` and one `load` entry — so the 1024-byte bound leaves 209%
  headroom while still detecting an embedded state dump. The bound is asserted in
  the suite rather than enforced as a runtime refusal, because a refusal would
  leave the loop with no next action (source: a serialization measurement over
  every Routing row, 2026-09-01)
- Technical: `next` cannot observe a human merge decision, so `CODE-HUMAN-GATE`
  carries one row rather than a changes-requested branch. What the agent does on
  changes-requested — replay the recorded clean form under its operation id, then
  fire `blocker-applied` — is already stated in the shipped resumption row that
  R20's `load` points at, and needs no record field (source:
  `references/session-resumption.md` `reviewers-clean`/`CODE-HUMAN-GATE` row)
- Technical: `next` cannot determine a round's warranted reviewer roster, because
  no state field records it and the warrant is a judgment over the diff; so R17
  stops on a non-matching operation id rather than naming a recording action, and
  this contract claims decidability rather than automatic recovery on that row
  (source: the `state.json` field table records no roster)
- Technical: `next` does not answer legacy light-mode resumption, which has no
  engine state to read, and refuses cleanly instead (source: user confirmation
  2026-08-31)
- Technical: new suites under `packs/core/tests/skills/work-loop/` and under
  `tests/roster/` both run in `make test`, which names the first directly and the
  second through `pytest tests/` (source: `Makefile:545`, `Makefile:530`)
- Technical: a JSON payload contract lives at
  `contracts/jsonschema/<name>.schema.json` carrying `contract_version` and
  `x-spec`, validated from `tests/roster/` (source:
  `contracts/jsonschema/semantic-surface-resolution.schema.json`)
- Process: no RFC is owed; every change is additive and the RFC reserved list
  covers charter, authority, security trust model, and withdrawal of a published
  promise (source: `docs/CONVENTIONS.md:342-346`)
- Process: no ADR is owed; the verb is an internal of one subsystem, which a spec
  owns (source: `docs/CONVENTIONS.md:291`, user confirmation 2026-08-31)
- Process: editing any file under `packages/agentbundle/` outside `build/recipes/`
  or a `tests/` path trips a protected-tree gate requiring an engine-scoped RFC
  trailer, so no task here edits that tree (source:
  `tools/lint-catalogue-curation-guard.py`; the gate runs at
  `tools/repo/build_gate_chain.py:306`)
- Process: a `contracts/` change requires a release indicator in the same change,
  which the changelog entry satisfies, because `contracts/` is absent from the
  non-impacting prefix list (source:
  `tools/repo/check_release_impact.py` `NON_IMPACTING_PREFIXES`)
- Process: the core pack bumps minor, because a new CLI verb is a new primitive
  (source: `packs/AGENTS.md:45-47`)
- Process: shipped pack content and adopter guides state rules directly and cite
  no repository-only path (source: `packs/AGENTS.md:49-52`,
  `tools/lint-guides-no-repo-only-refs.py`)
- Process: the changelog entry is free-standing at `##` and never nested under
  `[Unreleased]`, or the highlights projection never sees it (source:
  `docs/product/changelog.md:11-19`)
- Process: `packs/core/.apm/**` is the source and the adapter skill trees are
  regenerated projections, byte-identical to source today (source: the `build-self`
  and `build-self-dry-run` targets at `Makefile:67` and `Makefile:82`; `diff -q`
  between source and the Claude projection)
- Product: this contract delivers the projection only; it makes no claim about the
  size of the always-loaded instruction surface, which a dependent contract owns
  (source: user confirmation 2026-08-31)
- Product: this delivery provides mechanism, not a longitudinal study of
  completion rate or recovery refusals across sessions; those need many real runs
  and are outside this contract (source: user confirmation 2026-08-31)
