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
enables. This contract makes no *reduction* claim about that surface; AC20 adds
five statements to it.

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
| both | `null` | `SPEC-PLAN-DRAFTING` | A freshly initialised run, after the init pair has completed |
| code | `plan-approved` | `CODE-IMPLEMENTATION` | A pre-split persisted run |
| spec-plan | `plan-approved` | `DONE` | A pre-split persisted run |

That yields 19 base keys in `code` mode and 10 in `spec-plan`, 29 in all.

Each base key is crossed with the values of whichever Discriminator applies to
it, giving **34 domain members in `code` mode and 21 in `spec-plan`, 55 in all**.
A base key no Discriminator applies to contributes exactly one member. This
document is the sole home of that figure; the plan references it rather than
restating it.

Wave position is deliberately not a Discriminator: it changes no row's action,
and enters the record only as `cohort.wave-advance`'s `from_index` parameter.

### Discriminators

Each Discriminator's value set is fixed **here**, and each is **total over what
its source can actually produce**. That totality — not a citation to some other
document — is what makes the domain independent of the Routing table: deleting a
Routing row removes coverage without removing a domain member.

| # | Applies to | Read from | Values |
| --- | --- | --- | --- |
| D1 | `SPEC-HUMAN-GATE` | `spec.md`'s Status line, via the canonical reader | `Draft`, `Approved`, `other` |
| D2 | `PLAN-HUMAN-GATE` | `plan.md`'s Status line, via the canonical reader | `Drafting`, `Approved`, `other` |
| D3 | `SPEC-PLAN-APPROVED` | `plan_review_status` and whether `schedule_waves` is empty, in `state.json` | `pending+unscheduled`, `pending+scheduled`, `approved+unscheduled`, `approved+scheduled`, `malformed` |
| D4 | `CODE-IMPLEMENTATION` with `last_event: findings-remain` | `last_review_record_operation_id` in `state.json`, compared with `<run_id>:<transition_sequence>` | `matches`, `does-not-match` |
| D5 | `SPEC-PLAN-REVIEW` and `CODE-REVIEW` | `review_retry_count`, `max_review_retries`, `finding_fingerprints`, `previous_finding_fingerprints`, and `amendment_pending`, all in `state.json` | `within-budget`, `cap-reached`, `stasis`, `malformed` |

**Every value set ends in a catch-all, and that is what makes it closed.**
`state.json` and the Status files are read without schema validation and no
Precondition form-checks any of these fields, so each Discriminator names its
recognised values and folds everything else into one terminal value that routes
to `halt`:

- **D1 / D2 `other`** — the canonical reader applies no vocabulary check. It
  returns whatever leading token the Status line carries, an empty string for a
  comment-only value, nothing at all for a file with no Status line, and raises
  for a file it cannot read. `other` is every one of those except the two named
  values, including a differently-cased token.
- **D3 `malformed`** — `plan_review_status` is a free JSON value; anything that is
  not `pending` or `approved`, and any `schedule_waves` that is not a list.
- **D5 `malformed`** — any of its four fields that is not what it must be: a
  counter that is not a non-negative integer, or a fingerprint field that is not a
  list **of strings**. The element type is load-bearing: `[{"a": 1}]` and
  `[1, "a"]` are both lists, and the sorted-unique comparison below raises on
  each, so a catch-all that checked only "is a list" would let a hand-edited
  `state.json` crash the verb where the contract promises a `halt`. This mirrors the shared guard module, whose integer helper refuses a
  boolean, a negative, and a non-integer by name, and whose phase check returns a
  refusal rather than an under-cap or at-cap answer when a counter is malformed.
  The cap must be derived through that helper, not through raw arithmetic.

**D5's two spent values are distinct because their legal continuations differ.**
`cap-reached` is `review_retry_count >= max_review_retries`. `stasis` is
`finding_fingerprints` **non-empty and equal to** `previous_finding_fingerprints`,
compared in the same sorted-unique canonical form the shipped detector uses — the
non-empty qualifier is load-bearing, because both fields are empty on a fresh run
and after two consecutive clean or all-skipped rounds, and comparing them raw
would classify a brand-new loop as spent on its very first call. The three
spent-or-broken values are evaluated in a fixed order: **`malformed` first, then
`cap-reached`, then `stasis`.** A state satisfying more than one is reported as
the earliest, so two conforming implementations cannot disagree.

**A review state ignores a *cap* written in a different review phase — and only
the cap.** A contract amendment resets the plan-approval cycle but deliberately
preserves the review counters and fingerprints, so an amended contract would
otherwise re-enter `SPEC-PLAN-REVIEW` already reading spent. The signal is
`amendment_pending`: the amendment sets it and only the re-approval of the
amended plan clears it. While it is non-null, D5 at a review state does not
report `cap-reached`.

**`stasis` is never suppressed, and the asymmetry is the whole point.** The cap is
independently enforced — the engine refuses `findings-remain` at it regardless of
what this projection says — so suppressing the projection's report of it removes
mis-advice without removing enforcement. Stasis has no such backstop: no
transition guard reads the fingerprint pair, and the classifier that computes it
returns success on every content outcome. Suppressing stasis would therefore
remove the only signal, and an amended contract could review the same findings
indefinitely. Leaving it live fails safe onto R5's human gate instead.

Two residuals follow, and are accepted rather than closed:

- An amended contract whose surviving fingerprint pair is non-empty and equal
  halts on its first review call, and no verb short of a cohort reset clears the
  pair. That is over-conservative: it stops rather than proceeds, and an
  amendment following a stasis round is a case a human should look at.
- The window is wider than the counters' provenance. `amendment_pending` clears
  only at re-approval, which is after the whole post-amendment review cycle, so a
  cap genuinely reached *inside* that window also goes unreported. The engine
  still refuses the transition, so the enforcement holds and only the advice is
  lost.

D3 lists the full cross product of its two recognised fields rather than the
reachable subset. Including `pending+scheduled` costs one row's worth of coverage
and removes a reachability argument the criteria would otherwise depend on.

### Preconditions

**Before any row is evaluated**, `<spec-dir>` is resolved and proved inside the
repository through the engine's existing resolver — the same step every other
engine verb takes first. P1 globs and stats a path derived from that argument, so
confinement precedes it rather than following it. A rejection returns through the
engine's existing generic refusal at exit 1 and needs no new code.

Evaluated in order; the first matching row decides, and Routing runs only when
none matches. P2 through P6 carry five distinct non-zero exit codes, allocated
from 3 upward so that none collides with the engine's existing exit 1 (its
generic refusal, including an unloadable guard module) or argparse's exit 2.

| # | Condition | Exit | Record | stderr names |
| --- | --- | --- | --- | --- |
| P1 | An unpromoted engine-state temporary file, or an unreplayed pending-events file, is present | zero | `halt` | which artifact class was found, and that recovery is a writing verb's job |
| P2 | No `engine-state.json`, and `spec.md` cannot be read | non-zero | none | that the light-mode marker could not be read, and why the read failed |
| P3 | No `engine-state.json`, and `spec.md` carries the light-mode marker defined below | non-zero | none | the legacy light-mode resumption table as the surface that answers instead |
| P4 | No `engine-state.json`, `spec.md` readable, and no light-mode marker | non-zero | none | the ambiguity, without pointing at the light-mode table |
| P5 | `engine-state.json` is unreadable, or its `schema_version` is not `1` | non-zero | none | which of the two it was |
| P6 | `engine-state.json` lacks a well-formed `run_id`, `transition_sequence`, or `mode` | non-zero | none | which field failed, and the offending value under the bound AC14 sets |
| P7 | `state.json` is missing, is unreadable, carries no `run_id`, or carries one differing from `engine-state.json`'s | zero | `halt` | which of the four it was |
| P8 | The `(engine state, last_event)` pair is not a base key for the run's mode | zero | `halt` | the offending pair |

**Why P1 is first.** The engine writes state by creating a temporary file and
then renaming it, so an interrupted `init` leaves a temporary behind with *no*
`engine-state.json` at all — and an interrupted `transition` can leave one beside
a stale or unreadable file. Ordered any lower, P1 would be shadowed by P2 through
P5 in exactly the cases it exists to catch, and the run would be told "no engine
state, this is ambiguous" when the truth is "a write was interrupted and a writing
verb must finish it."

**Why P2 precedes P3 and P4.** The marker test is a file read, and that read can
fail — a symlink, a non-regular file, an oversized file. Without P2 such a failure
would fall through to P4 and be reported as an ambiguous mode, which is the wrong
diagnosis and contradicts AC15's requirement that the same file be refused rather
than followed or read.

**P1's detection.** Presence only, of either artifact class: a confined glob for
the engine-state temporary, whose name is random, and a single stat for the
pending-events file. Neither artifact is opened and neither is parsed, so nothing
here reads attacker-influenceable content. The pending-events file lives in the
repository-shared run directory rather than the spec directory, so its presence
halts every run in the repository, not only this one — the artifact records an
interrupted write whose replay is a writing verb's job, and a read-only verb
cannot tell whose.

**P6's well-formedness.** `run_id` is a canonical lowercase UUID,
`transition_sequence` a non-negative integer, and `mode` one of `code` or
`spec-plan`. All three fail before any record is built rather than routing to a
`halt`, because the record cannot be constructed without them: `run_id` and
`transition_sequence` are two of its nine keys, and `mode` selects the transition
table `complete_with` is derived from.

**P3's light-mode marker.** With HTML comments removed, a line in `spec.md`
*before its first `##` heading* matching
`^[\s>*_`-]*Mode[\s*_`]*:[\s*_`]+light(?![\w-])`, case-insensitively. The
colon and at least one following separator are both required, and the trailing
guard rejects a hyphen, so neither `Modelight` nor `light-weight` matches. The
zone restriction is load-bearing: the marker is discussed in the body of specs
that are about it, and those mentions must not route a run to P3. A spelling
outside this form is not a marker; P4 then surfaces the ambiguity rather than
guessing, which is the shipped fail-safe.

### Routing

`*` in the `last_event` column matches every base key reaching that state. `both`
in the Mode column matches either mode.

| Row | Mode | Engine state | `last_event` | Discriminator | Action |
| --- | --- | --- | --- | --- | --- |
| R1 | both | `SPEC-PLAN-DRAFTING` | `null`, `findings-remain` | — | `spec.draft` |
| R2 | both | `SPEC-PLAN-DRAFTING` | `spec-rejected`, `plan-rejected` | — | `spec.reset-and-revise` |
| R3 | code | `SPEC-PLAN-DRAFTING` | `contract-amendment` | — | `spec.amend` |
| R4 | both | `SPEC-PLAN-REVIEW` | `*` | D5 `within-budget` | `spec.review` |
| R5 | both | `SPEC-PLAN-REVIEW` | `*` | D5 `cap-reached`, `stasis` | `await-replan-decision` |
| R6 | both | `SPEC-PLAN-REVIEW` | `*` | D5 `malformed` | `halt` |
| R7 | both | `SPEC-HUMAN-GATE` | `*` | D1 `Draft` | `await-spec-approval` |
| R8 | both | `SPEC-HUMAN-GATE` | `*` | D1 `Approved` | `engine.spec-approved` |
| R9 | both | `SPEC-HUMAN-GATE` | `*` | D1 `other` | `halt` |
| R10 | both | `PLAN-HUMAN-GATE` | `*` | D2 `Drafting` | `await-plan-approval` |
| R11 | both | `PLAN-HUMAN-GATE` | `*` | D2 `Approved` | `engine.plan-approved` |
| R12 | both | `PLAN-HUMAN-GATE` | `*` | D2 `other` | `halt` |
| R13 | both | `SPEC-PLAN-APPROVED` | `*` | D3 `pending+unscheduled`, `pending+scheduled` | `cohort.approve-plan` |
| R14 | code | `SPEC-PLAN-APPROVED` | `*` | D3 `approved+unscheduled` | `cohort.schedule` |
| R15 | code | `SPEC-PLAN-APPROVED` | `*` | D3 `approved+scheduled` | `engine.plan-locked` |
| R16 | spec-plan | `SPEC-PLAN-APPROVED` | `*` | D3 `approved+unscheduled`, `approved+scheduled` | `engine.plan-locked` |
| R17 | both | `SPEC-PLAN-APPROVED` | `*` | D3 `malformed` | `halt` |
| R18 | code | `CODE-IMPLEMENTATION` | `plan-locked`, `plan-approved`, `blocker-applied` | — | `implement` |
| R19 | code | `CODE-IMPLEMENTATION` | `wave-passed` | — | `cohort.wave-advance` |
| R20 | code | `CODE-IMPLEMENTATION` | `gates-failed` | — | `cohort.record-attempt` |
| R21 | code | `CODE-IMPLEMENTATION` | `findings-remain` | D4 `matches` | `implement` |
| R22 | code | `CODE-IMPLEMENTATION` | `findings-remain` | D4 `does-not-match` | `halt` |
| R23 | code | `CODE-VERIFICATION` | `wave-complete` | — | `run-gates` |
| R24 | code | `CODE-REVIEW` | `*` | D5 `within-budget` | `run-review` |
| R25 | code | `CODE-REVIEW` | `*` | D5 `cap-reached`, `stasis` | `await-replan-decision` |
| R26 | code | `CODE-REVIEW` | `*` | D5 `malformed` | `halt` |
| R27 | code | `CODE-HUMAN-GATE` | `reviewers-clean` | — | `await-merge-decision` |
| R28 | code | `DONE` | `done` | — | `complete` |
| R29 | spec-plan | `DONE` | `plan-locked`, `plan-approved` | — | `complete` |

**The three ways back are not the same act, which is why R1-R3 are separate
rows.** All three land in `SPEC-PLAN-DRAFTING`, and an agent told only "draft the
spec" would drop an obligation in two of them.

- **R2, a rejected gate.** Reset `spec.md` to `Draft` and `plan.md` to `Drafting`,
  then revise and fire `spec-ready`. Nothing in the engine enforces this — there
  is no `spec-ready` guard — so it is an agent obligation, and the consequence of
  skipping it is recorded in the Assumptions.
- **R3, a contract amendment.** Authority and the completed-task pins are already
  discharged by the transition that produced this state, so they are not owed
  here. What is owed is the same `Draft`/`Drafting` reset, an amendment confined
  to the bounded outcome and the unfinished tasks, and leaving every completed
  task section untouched.
- **R1** is the plain drafting act: a new run, or an ordinary findings round.

**Why R5 and R25 — the two `await-replan-decision` rows — exist.** When the review budget is spent or two rounds return
identical fingerprints, the loop must not review again — and at the cap the engine
will not let it, because the `findings-remain` guard refuses. Without these rows
the projection would answer `spec.review` or `run-review` at exactly the moment
another round is the wrong move, and at the cap the only event the engine still
accepts is `reviewers-clean`, so a caller following the record would be pushed
toward declaring a contract clean in order to escape.

**What the wait's reason may name, and what it may not.** The two spent
conditions have different legal continuations, so the stderr reason differs:

- **`cap-reached`** — the only continuations are the two the engine's own refusal
  names: reset and start a new run, or, if a human directing the run authorises
  it, pass `--allow-retry-cap-override` to both the `findings-remain` transition
  and the matching `review record`, since either half alone desynchronises the
  engine and the cohort.
- **`stasis`** — the loop stops for human replanning. The lifecycle reference this
  row loads is explicit that a repeated finding fingerprint "stops immediately for
  human replanning; it is not another review round", so the engine still accepting
  `findings-remain` below the cap is legality, not permission. The reason names no
  continuation of its own.

Neither reason may offer narrowing the accepted intent or splitting the contract
into separate specs. The lifecycle reference this row loads forbids both on this
trigger: it states that an outcome is not narrowed because a retry budget or
review round ended, and that a retry cap or stasis never invokes the amendment
transition or creates a follow-on. Splitting a contract remains a scope-owner
decision taken outside this loop, not a replanning option a spent review budget
authorises.

### Action attributes

`kind`, the `parameters` key set, `load`, and `human_wait` are functions of
`action` alone, so they are tabled once here rather than repeated per routing row.
`—` in the `parameters` column means the empty object, never an absent key.

| Action | `kind` | `parameters` keys | `load` | `human_wait` |
| --- | --- | --- | --- | --- |
| `spec.draft` | `agent` | — | `ref:pre-execute-review` | false |
| `spec.reset-and-revise` | `agent` | — | `ref:delivery-contract-lifecycle` | false |
| `spec.amend` | `agent` | — | `ref:delivery-contract-lifecycle` | false |
| `spec.review` | `agent` | — | `ref:pre-execute-review` | false |
| `implement` | `agent` | — | `ref:verification-modes` | false |
| `run-gates` | `agent` | — | `ref:pre-flight-failures` | false |
| `run-review` | `agent` | — | — | false |
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
| `await-replan-decision` | `wait` | — | `ref:delivery-contract-lifecycle` | true |
| `complete` | `done` | — | — | false |
| `halt` | `stop` | — | — | false |

`human_wait` is true exactly for the four `wait`-kind actions. No action in this
table is destructive, so there is no second source of it.

`human_wait` describes the record, not the engine's `pending_human_wait`. At a
human gate whose approver has already written the decision — R8 and R11 — the
engine still reports `pending_human_wait: true` while the record reports
`human_wait: false`, because nothing is left to wait for: the action is firing the
event the approver's write authorised.

**Why the two review references are absent from `load`.** A reviewer-dispatch
action needs neither of them *at dispatch*. The adjudication reference is needed
only once a persisted raw report has been classified and that classification
requires adjudication; the verdict reference only when the verdict record for the
unit is emitted or validated. Both conditions are decided after the report exists,
which is after the record was handed over — so naming them in `load` would load
roughly 3,000 words on every dispatch, most of them on turns that never adjudicate
and never aggregate.

Keeping them out costs the contract nothing, because the shipped surface already
owns this routing: its conditional-reference table already predicates the
adjudication reference on a `finding-adjudicator` dispatch and the verdict
reference on emitting or validating the record. `load` was contradicting a
control that already existed. The projection therefore adds no field, action,
state, or discriminator for conditional loading, and — critically — never
inspects a raw report, never derives a discriminator from report prose, and never
infers a reviewer roster. Post-report routing stays with the work-loop, after
classification. AC27 fixes the four paths.

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
- **The conditional-load paths: TDD.** Path 1 is asserted against this document's
  Action attributes table; paths 2 through 5 are greps over the shipped surface,
  in the same form as the trust-posture statements, with the reconciling edit to
  the always-loaded body owned by the task that edits it.
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
  one domain member uncovered, and that holds for every row without exception,
  not only those carrying no Discriminator.
- [ ] **AC2 — determinism.** No member of the domain matches more than one Routing
  row. Widening any row's Mode, `last_event`, or Discriminator column so that it
  overlaps another row fails this criterion.
- [ ] **AC3 — each row's observable.** For every Routing row, a run driven into a
  domain member that row matches yields a record whose `action` is that row's
  action. The expected action is parsed from the Routing table's Mode, Engine
  state, `last_event`, and Discriminator columns — never obtained from the
  implementation's own routing data or discriminator resolver. Both a changed row
  action and a swapped discriminator branch fail this criterion; the second is the
  mutation that distinguishes it from AC1 and AC2, so exchanging R7's and R8's
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
  record, and its stderr names what the row's last column requires. P1 is
  exercised in the state that makes ordering load-bearing — a temporary file with
  no `engine-state.json` beside it — and must win over P2, P3, and P4. P2 is
  exercised with an unreadable `spec.md` and must win over P4. **P3's** marker
  match is exercised against every spelling in the plan's fixture set, against a
  body-zone mention, and against `Modelight` and `light-weight`, none of which may
  match. Every non-zero row returns the distinct code the Preconditions preamble
  allocates, each distinct from the others and from 1 and 2, which the engine's
  generic refusal and argparse already occupy — that preamble is the single home
  of both the row count and the code count, and this criterion asserts against it
  rather than restating either. D5's spent branch is exercised on a fresh run,
  after two consecutive clean rounds, and at `SPEC-PLAN-REVIEW` re-entered by
  `spec-ready` inside an amendment window (not at `SPEC-PLAN-DRAFTING`, where no
  Discriminator applies), where a surviving over-cap counter must yield
  `within-budget` while a surviving equal non-empty fingerprint pair must still
  yield `stasis`; and on a state satisfying both
  `cap-reached` and `malformed`, which must yield `malformed`.

### The record

- [ ] **AC7.** On a zero exit, `loop-engine next <spec-dir> --json` writes exactly
  one JSON object to stdout, whose key set is exactly `schema_version`, `run_id`,
  `sequence`, `kind`, `action`, `parameters`, `complete_with`, `load`,
  `human_wait`. On a non-zero exit it writes nothing to stdout. `--json` is
  required: `next` invoked without it exits non-zero and writes nothing to stdout,
  so there is no second, uncontracted output form.
- [ ] **AC8.** No diagnostic, refusal reason, or stop reason is written to stdout
  on any exit path; every one of them is written to stderr.
- [ ] **AC9.** `schema_version` is the literal string `work-loop-next.v1`; `run_id`
  equals the `run_id` in `engine-state.json` and matches the canonical lowercase
  UUID form P6 requires; and `sequence` equals its `transition_sequence`. Pinning
  either derived field to a constant fails this criterion, and so does emitting a
  record for state whose `run_id` does not match that form.
- [ ] **AC10.** `complete_with` lists exactly the events legal from the record's
  state in the engine's transition table for the run's mode, read at runtime, and
  is empty exactly when that state has no outgoing transition. Pinning it to a
  constant fails this criterion. It carries **one declared exception**: at a review
  state where `review_retry_count >= max_review_retries`, `reviewers-clean` is
  omitted. The exception is keyed on that raw condition rather than on D5's routed
  value, because the amendment carve-out can make D5 report `within-budget` at a
  genuine cap — and the omission has to survive that. That event is the only one the
  engine still accepts at the cap, and advertising it in the field an agent parses
  to choose its next move is the false-clean pressure R5 and R25 exist to remove.
  The general "the guard refuses an illegal choice anyway" argument does not hold
  on this edge: its guard checks the spec's Status token, not whether the review
  was actually clean, and in spec-plan mode the edge has no guard at all. Emitting `reviewers-clean` in a `cap-reached`
  record fails this criterion.
- [ ] **AC11.** Every `parameters` value matches `^[A-Za-z0-9:._-]+$` or is an
  integer. No `parameters` value is ever a boolean: the Action attributes table
  declares no boolean key, and permitting one would admit `True`, which Python
  counts as an integer. For a value read from either state file this is a
  **runtime refusal, not a suite assertion** — a value that fails yields `halt`
  rather than a record, and an integer is resolved through the shared guard
  module's non-negative-integer helper, so a boolean, a negative, or a
  non-integer is refused rather than silently coerced. `from_index` is the case
  that requires it: it is the only `parameters` value taken from a field no
  Precondition form-checks, and it reaches a command line. Its source is
  `engine-state.json`'s `last_event_context.completed_wave_index`, which the
  shipped instruction for the same act already uses — **not** `state.json`'s
  `current_wave_index`, which the advance itself increments, so a record built
  from that field on a resume where the advance already landed would pass an index
  one too high and silently skip a wave. `cycle_id` is derived
  from two fields P6 already checks.
  Every `load` entry resolves to a file shipped under the skill's `references/`
  tree, with the resolution built by globbing that tree rather than transcribed.
  Planting a `current_wave_index` of `true`, `-1`, or a string, and observing a
  record rather than a `halt`, fails this criterion.
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
  where untrusted text starts and ends. The observable is what that helper
  actually emits, not a hand-rolled equivalent: it truncates the *repr*, so an
  over-long value reaches stderr as an opening quote, the capped prefix, and a
  trailing ellipsis that is the end marker — there is no closing quote, and a
  criterion demanding one would be satisfiable only by re-implementing the
  control. A whole reason is capped at that module's
  reason bound. A planted oversized `run_id` therefore reaches stderr truncated
  and quoted, not verbatim; removing either the cap or the delimiters fails this
  criterion.

### Reads

- [ ] **AC15.** The verb opens no file outside a set of four — both state files
  and both artifact Status files — and reads each artifact Status file only at the
  state whose Discriminator consumes it, so a run that needs neither opens
  neither. Each is read through the shared guard module's readers,
  with no direct `open` or `read_text` anywhere in the verb's path; a symlink, a
  non-regular file, and an oversized file at each of the four is refused rather
  than followed, read, or blocked on.
- [ ] **AC15a.** The two crash artifacts are never opened. P1 detects them by
  presence alone, under two different roots: the engine-state temporary by a
  confined glob within the spec directory, the pending-events file by a single
  stat in the repository-shared run directory. A symlink, a directory, or a FIFO
  at either location is detected as present and yields P1's `halt`, and no read,
  parse, or repair occurs at either.
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
  Changing one identifier fails this criterion. Three shipped rows need more than
  a column: the two spec-plan `DONE` rows, whose prose describes a conditional
  reset the projection answers as `complete`, and the `gates-clean`/`CODE-REVIEW`
  row, whose prose tells a resuming agent to re-run the reviewer fan-out — the
  instruction R25 exists to suppress once the review budget is spent. That row's
  prose gains the budget branch, so no shipped row prescribes an action its own
  identifier column contradicts.
- [ ] **AC20.** The consumer's trust posture is stated on the surface an agent has
  loaded **whenever it consumes a record**, not in a reference only one row's
  `load` names — only `await-merge-decision` loads the resumption reference, so
  placing the control there would leave it absent on the `run-review`,
  `spec.amend`, and `halt` turns. It therefore ships in the always-loaded skill
  body, and the resumption reference may repeat it. Five statements, each found by
  grep: the record is data rather than instruction; `action` is matched against
  the closed Action attributes vocabulary and an unrecognised value halts; a
  `load` entry outside the closed reference vocabulary halts; no field of the
  record is executed or interpreted as a command; and a stderr reason is a
  diagnostic and never authority — a `wait`-kind record authorises no act this
  turn, and the continuations its reason names are choices to put to the human,
  not steps to take. Deleting any one of the five fails this criterion.
- [ ] **AC27.** Five paths, each with its evidence form named. Paths 1 is a
  property of this document's Action attributes table; paths 2 through 5 are
  statements a grep finds in the shipped work-loop surface.
  1. **At dispatch, neither reference loads.** `run-review` and `spec.review` name
     neither review reference in `load`. *Evidence: the Action attributes table.*
  2. **A raw report classified `clean` with no `## Not checked` footer loads
     neither.** *Evidence: shipped surface.*
  3. **A finding-bearing report loads the adjudication reference.** *Evidence:
     shipped surface.*
  4. **A report that is otherwise clean but carries the mandatory `## Not checked`
     footer also loads it**, because the footer is prose and prose is what the
     adjudicator reads, so that report is never fast-pathed. *Evidence: shipped
     surface.* This is a control and is not weakened here: footer content stays
     adjudicated unless some later change moves it into a genuinely
     machine-separated contract.
  5. **The verdict reference loads only when the review unit's verdict record is
     emitted or validated** — never at dispatch, never on a repair-verification
     pass. *Evidence: shipped surface.*

  Path 2 is **false on the shipped surface today**: the always-loaded body
  instructs an unconditional read of the adjudication reference before a review
  unit's first report, which contradicts the same file's conditional-reference
  table. Reconciling those two is this contract's work, not a pre-existing
  control it inherits, and the task that edits that surface owns it.

- [ ] **AC21.** `loop-engine --help` lists `next` alongside `init`, `transition`,
  `status`, and `reset`.
- [ ] **AC22.** The entrypoint section of
  `docs/architecture/loop-infrastructure.md` names `next` in the `loop-engine.py`
  verb set and records it as read-only.
- [ ] **AC23.** `guides/core/how-to/plan-and-execute-non-trivial-work.md`
  describes resuming through `next`, checked by grepping for the literal
  `loop-engine next` rather than the bare word — that file already contains "the
  next phase" and "the next review unit", so a bare-word check is green before the
  edit.

### Evidence and release

- [ ] **AC24.** Two manual-QA transcripts are committed at the destination the
  Durable Outputs table names: a full-mode `code`-mode loop driven end-to-end
  through the shipped instructions on a throwaway spec directory reaching `DONE`,
  and a session interrupted between firing `findings-remain` and recording the
  round then resumed, reaching a correct next action with no double increment of
  `review_round_count`. Each records the observed action sequence, final engine
  state, and per-command exit codes, and states what it does not exercise. Both
  carry repository-relative paths only: the verb's own stderr interpolates
  absolute ones, and the privacy convention bans a user-specific filesystem path
  from every committed artifact. The check searches for `/Users/`, `/home/`,
  `~/`, the committing account's username, the machine hostname, an
  email-address pattern, and the employer or organisation domain token, and
  passes only when none is present — a transcript carries the worktree path, the prompt
  hostname, and the account name, and no repository-wide lint backstops this.
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
- Technical: AC19 is additive for twelve of the fifteen shipped rows, whose
  prescribed action already agrees with the Routing table. The two spec-plan `DONE`
  rows are the exception: they prescribe a reset conditioned on a later human
  request, so their identifier column carries `complete` — the action `next`
  returns — while their prose keeps describing the conditional reset as a human
  path. No row's prose is rewritten, and the two tests that pin row prose keep
  passing. They locate their row by substring and
  assert phrases within the matched line, so an added column does not disturb
  either (source: `test_loop_engine.py:2775-2776` matches the `findings-remain`
  row and requires "stale fingerprint baseline", "under-count", and "do NOT
  auto-reissue", all of which R21 and R22 preserve; `:2846`
  `test_reviewers_clean_skill_prose_obligations` matches the same way; and
  `test_loop_cohort.py:1843-1867` pins the same `reviewers-clean` row, requiring
  exactly one matching line and three command-form substrings inside it, which an
  appended column also survives)
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
  writing verb it names re-validates under the lock. Two atomic-write temporaries
  are detectable from disk, and P1 halts on only one of them: the cohort's
  `.state-*.json.tmp` is deliberately not a halting condition, because no recovery
  routine exists for it and halting would wedge the loop permanently (source:
  `_statelock.py:122-124`; `loop-cohort.py:177`)
- Technical: an unreset `Approved` after a rejected plan gate auto-fires the spec
  gate, and this contract mirrors that rather than introducing it. Nothing guards
  `spec-ready`, so if R2's status reset is skipped after `plan-rejected`,
  `spec.md` still reads `Approved` when the run re-reaches `SPEC-HUMAN-GATE`; D1
  returns `Approved`, R8 answers `engine.spec-approved` with `human_wait: false`,
  and the engine's spec-approved guard passes on the status token alone with no
  hash comparison, so the human never re-reviews the revised spec. The plan gate
  has the identical shape — its guard is also a lone status-token check — so an
  unreset `plan.md` makes R11 auto-fire `plan-approved` too, and a single
  resumption can skip both human gates. The shipped
  resumption row prescribes exactly this today, so the projection is faithful; the
  residual is recorded rather than closed, because closing it needs a freshness
  signal the state files do not carry (source: `references/session-resumption.md`
  step 4's `SPEC-HUMAN-GATE` rule; `loop-engine.py` `_guard_spec_approved`)
- Technical: the two state files keep their owners, so the projection reads engine
  state through the engine's own reader and cohort state through the shared guard
  API (source: `_loop_guards.py` names `engine-state` only in two comments;
  `loop-cohort.py` in two, at `:94` and `:1920`)
- Technical: the canonical Markdown status reader raises for a file it cannot read
  and returns nothing for a file with no recognised Status line, which is why D1
  and D2 collapse every other outcome into one `other` value (source:
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
  distinguishable without an engine transition between them, which is why R13-R17
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
  R27's `load` points at, and needs no record field (source:
  `references/session-resumption.md` `reviewers-clean`/`CODE-HUMAN-GATE` row)
- Technical: `next` cannot determine a round's warranted reviewer roster, because
  no state field records it and the warrant is a judgment over the diff; so R22
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
