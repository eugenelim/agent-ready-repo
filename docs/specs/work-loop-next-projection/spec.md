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
| D5 | `SPEC-PLAN-REVIEW` and `CODE-REVIEW` | `review_retry_count`, `max_review_retries`, `finding_fingerprints`, and `previous_finding_fingerprints`, in `state.json` | `within-budget`, `cap-reached`, `stasis`, `malformed` |

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
- **D3 `malformed`** — any of its two fields that is not what it must be, both
  named: `plan_review_status` is a free JSON value, so anything that is not
  `pending` or `approved`, and any `schedule_waves` that is not a list.
- **D5 `malformed`** — any of its four fields that is not what it must be, named
  so the closure is checkable against the Read-from column rather than only
  counted: `review_retry_count` or `max_review_retries` that is not a
  non-negative integer, or `finding_fingerprints` or
  `previous_finding_fingerprints` that is not a list **of strings**. The element type is load-bearing: `[{"a": 1}]` and
  `[1, "a"]` are both lists, and the sorted-unique comparison below raises on
  each, so a catch-all that checked only "is a list" would let a hand-edited
  `state.json` crash the verb where the contract promises a `halt`. Both counters
  are resolved through the shared guard module's **non-negative-integer helper**,
  read directly from `state.json` with no fallback default. That helper is named
  deliberately and the phase check is not: the phase check is an enforcement API
  returning a refusal, and it reaches a defaults table that is eagerly bound and
  lazily populated, so its first lookup — at the phase check, not at import —
  opens the bundled state template, a file outside AC15's declared set. The
  integer helper performs no I/O. Its third argument is a required fallback fed
  straight to `state.get`, so "no fallback default" is expressed by passing a
  sentinel the helper itself rejects — `None`: an absent `max_review_retries` then
  fails the integer check and is `malformed`, where passing `0` would read as
  `cap-reached` and passing the defaults table would open that sixth file. The
  catch-all therefore stays total over what `state.json` actually presents.

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

**Why no amendment carve-out exists.** A contract amendment preserves the review
counters by design, so an amended contract can re-enter `SPEC-PLAN-REVIEW` with a
budget already spent. An earlier revision suppressed `cap-reached` there. That was
wrong, and the reason is worth keeping: suppressing a *report* does not make the
projection silent, it makes it answer something else — `spec.review` — and the
engine still refuses `findings-remain`, so the record named one continuation that
could not be taken. D5 now reports what it reads, everywhere. An amended contract
at a spent budget lands on `await-replan-decision`, which is a stop for a human,
not a dead end.

D3 lists the full cross product of its two recognised fields rather than the
reachable subset. Including `pending+scheduled` costs one row's worth of coverage
and removes a reachability argument the criteria would otherwise depend on.

### Preconditions

**Before any row is evaluated**, `<spec-dir>` is resolved and proved inside the
repository through the engine's existing resolver — the same step every other
engine verb takes first. P1 probes under two roots: a glob under a path derived
from that argument, and a stat in the repository-shared run directory. The
resolver establishes confinement for the first; the second is under a root the
argument does not reach, and AC15a is what bounds it. Confinement precedes both
rather than following them. A rejection returns through the engine's existing
generic refusal at exit 1 and needs no new code.

Evaluated in order; the first matching row decides, and Routing runs only when
none matches. P1 through P6 carry six distinct non-zero exit codes, allocated
from 3 upward so that none collides with the engine's existing exit 1 (its
generic refusal, including an unloadable guard module) or argparse's exit 2.

| # | Condition | Exit | Record | stderr names |
| --- | --- | --- | --- | --- |
| P1 | An unpromoted engine-state temporary file, or an unreplayed pending-events file, is present | non-zero | none | which artifact class was found, and that recovery is a writing verb's job |
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

**Why P1 refuses rather than emitting a record.** P1's own trigger case is an
interrupted `init`, which leaves no `engine-state.json` — and P6's note below
explains why no record can be built without one. An earlier draft had P1 exit
zero with a `halt` record, which was unconstructible in exactly the state the row
exists to catch. Refusing keeps every zero-exit row downstream of P6's
well-formedness proof, so AC7's and AC9's "on a zero exit" clauses are total. A
crash artifact is also not a routed action: the answer is "run a writing verb",
which stderr states and no `next` field could carry.

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
`transition_sequence` a non-negative integer **below 10^9**, and `mode` one of
`code` or `spec-plan`. The magnitude bound is not decoration: `sequence` is that
value and `cycle_id` is derived from it, and nothing else in the record varies in
size with state, so a planted `transition_sequence` is the one lever an attacker
has on record length. Without a bound the only ceiling is the interpreter's
int-to-string limit at 4,300 digits, which yields two ~4.3 KB values and a record
several times AC13's bound, delivered on stdout into the agent's context — the
flood AC14 closes on stderr and nothing closed on stdout. 10^9 is chosen against
the run it has to admit: at one transition per second without pause, it is over
31 years. All three fail before any record is built rather than routing to a
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

**What `complete_with` means on a `wait`.** It lists the events legal from the
record's state in the transition table — not the events fireable this turn.
`kind` carries fireability: on a `wait`, nothing may be fired until the human
decision the row names is taken, and the stderr reason says what that decision
unlocks. At `cap-reached` this matters most. The record lists `findings-remain`
and the engine refuses it, which reads as a contradiction until you see that the
refusal names its own remedy: a human directing the run may pass
`--allow-retry-cap-override` to that transition and to the matching
`review record`. So the single listed event is exactly the one the human decision
unlocks, and the field is honest rather than misleading. Emptying it would delete
the only authorised continuation from the field an agent reads.

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
  `spec-ready` after a `contract-amendment`, where a surviving over-cap counter
  yields `cap-reached` and a surviving equal non-empty fingerprint pair yields
  `stasis` — the same answers as anywhere else, because no carve-out exists; and
  on a state satisfying both `cap-reached` and `malformed`, which must yield
  `malformed`. D5 is additionally exercised on a `state.json` with
  `max_review_retries` **absent entirely**, which must yield `malformed`: that is
  the shape of any legacy or hand-trimmed state file, and it is the case that
  distinguishes the sentinel decision from its two wrong implementations —
  passing `0` reads as `cap-reached` and routes to a replan wait, passing the
  defaults table opens a file outside AC15's set.

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
  state whose D5 value is **anything other than `within-budget`**,
  `reviewers-clean` is omitted. The key is stated as the complement deliberately,
  so the exception covers all three of `cap-reached`, `stasis`, and `malformed`,
  and so any value added to D5 later omits the clean event until someone decides
  otherwise. Stasis needs it more than the cap does: the cap is independently
  refused by the engine's phase guard, while nothing anywhere reads the
  fingerprint pair, so on the stasis branch this projection is the only thing
  between two rounds of identical findings and a declared clean. `malformed`
  needs it for the reason the complement makes obvious — the verb could not read
  the budget at all, so it cannot know the review is unspent, and its record is
  the contracted `halt`. Keying on D5's value is safe now that no carve-out can
  make D5 report `within-budget` at a spent budget. The retained
  `findings-remain` is the only one the
  engine still accepts at the cap, and advertising it in the field an agent parses
  to choose its next move is the false-clean pressure R5 and R25 exist to remove.
  The general "the guard refuses an illegal choice anyway" argument does not hold
  on this edge: its guard checks the spec's Status token, not whether the review
  was actually clean, and in spec-plan mode the edge has no guard at all.
  Emitting `reviewers-clean` in a record whose D5 value is `cap-reached`,
  `stasis`, or `malformed` fails this criterion — three failing observables, one
  per non-`within-budget` value.
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
  Planting a `last_event_context.completed_wave_index` of `true`, `-1`, or a
  string, and observing a record rather than a `halt`, fails this criterion —
  that is the field this criterion names as the source, and planting the field it
  rules out would demand a `halt` from a read no conforming verb performs. **Absence** resolves the same
  way: the engine writes a null `last_event_context` for every event but two, so a
  legacy or hand-edited state at R19's key can carry no `completed_wave_index` at
  all, and with no fallback default that is `halt`, never an invented index.
- [ ] **AC12.** No record carries a schedule array, amendment history, finding
  fingerprint, or verbatim copy of either state file. A fingerprint is the case
  this criterion uniquely catches: a 64-character hex digest satisfies AC11's
  character class and would occupy a declared `parameters` key without violating
  AC5 or AC7.
- [ ] **AC13.** No record in the domain exceeds 1024 bytes, measured as the UTF-8
  byte length of the JSON object written to stdout, excluding any trailing
  newline. This criterion is the single home of that figure; the Assumptions and
  the plan reference it rather than restating the literal. The test also pins the
  observed maximum, so growth is visible before it reaches the bound. The domain
  is a cross product of `(mode, engine state, last_event, discriminator)` and
  varies no scalar's magnitude, so traversing it cannot by itself establish the
  bound against a planted state file; what makes the bound enforceable is P6's
  magnitude check on `transition_sequence`, the only state-derived scalar whose
  length is attacker-influenced. This criterion asserts the bound over the domain;
  P6 asserts it against a hostile input, and the two together are what hold.
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
  criterion. **The `argv` clause binds this verb's own new code and has no
  instance today.** The only argv-derived refusal is AC15b's, and AC15b routes it
  through the pre-existing shared resolver, whose message interpolates the raw
  argument uncapped through the engine's generic stop path — recorded as a
  standing Assumption, not closed here. Changing that message would edit a line
  `init`, `transition`, `status`, and `reset` also emit, which Boundaries puts
  behind *Ask first*, and no such decision has been taken. The clause is stated
  so that any argv value this verb interpolates itself is capped from the first
  line written.

### Reads

- [ ] **AC15.** The verb opens no file outside a declared set of **five**: both
  state files, both artifact Status files, and `scripts/lint-spec-status.py`. The
  fifth is not a data read and not optional — the canonical status reader this
  criterion mandates loads and executes that module to parse a Status line, so any
  conforming implementation opens it on any run that reads one. It is enumerated
  rather than excused: a criterion bounding the verb at four would be false of the
  blessed reader, and an instrument narrowed enough to make four true would stop
  detecting a real extra read. The parser module's own accepted residual — a
  pre-existing poisoned `.pyc`, which its loader documents and suppresses writing
  but cannot un-write — is inherited unchanged and recorded in the Assumptions.
  The verb reads each artifact Status file only at the state whose Discriminator
  consumes it, so a run that needs neither opens neither.
  **One carve-out:** P2 through P4 read `spec.md` for the light-mode marker when
  there is no `engine-state.json`, and therefore at no Discriminator's state. That
  read is mandatory, goes through the same guard readers, and counts against the
  declared set; the per-state clause governs the Status reads only. Each data file is read through the shared guard module's readers,
  with no direct `open` or `read_text` anywhere in the verb's path; a symlink, a
  non-regular file, and an oversized file at each of the four data files is
  refused rather than followed, read, or blocked on. The instrument is an
  open-tracer over the whole invocation with the five paths allow-listed, so a
  sixth open of any kind — including the bundled state template the phase check
  would reach — fails this criterion.
- [ ] **AC15a.** The two crash artifacts are never opened. P1 detects them by
  presence alone, under two different roots: the engine-state temporary by a
  confined glob within the spec directory, the pending-events file by a single
  stat in the repository-shared run directory. A symlink, a directory, or a FIFO
  at either location is detected as present and yields P1's refusal, and no read,
  parse, or repair occurs at either. The run-directory stat is under a root
  `<spec-dir>` does not reach, so AC15b's confinement does not bound it and this
  criterion is what does.
- [ ] **AC15b.** `<spec-dir>` is resolved and proved inside the repository
  through the engine's existing resolver before **any filesystem access under
  that argument**, which is P1's glob and every subsequent read. The claim is
  scoped to accesses under the argument because the resolver itself calls
  `Path.resolve()` and shells to `git rev-parse` to find the repository root: an
  instrument mechanizing "before any filesystem access" without that scope would
  redden on the control it is verifying. An argument resolving outside the
  repository, and one escaping through a symlink, are each refused at the
  engine's existing generic exit with no record and no probe under the argument
  performed. Removing the resolver call, or ordering it after P1, fails this
  criterion.
- [ ] **AC16.** Running `next` leaves `engine-state.json`, `state.json`, and
  `.loop-run/events.jsonl` byte-identical, and creates and deletes no file
  anywhere under the spec directory or the loop run directory. This holds on every
  Preconditions row too, including P1 on each of the two crash-artifact classes it
  detects — the unpromoted engine-state temporary and the unreplayed
  pending-events file — which are one row, not two.

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
- [ ] **AC27.** Five paths, each with its evidence form named. Path 1 is a
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

  **Path 2's evidence asserts the reconciled state, not the absence of one
  phrasing.** Every instruction in the always-loaded body that names the
  adjudication reference must sit under a trigger conditioned on the report's
  classification — the classifier's `findings` result, or the mandatory footer of
  path 4. An artifact that only pins the absence of today's sentence can be
  cleared by inverting the sentence and leaving the unconditional instruction
  intact, which turns the suite green on an unreconciled surface; that is why the
  evidence form is "every mention is under a conditioned trigger" rather than
  "this string is gone." The companion positive check for paths 3 through 5
  passes today alongside the contradiction, so it cannot distinguish the two
  outcomes and is not evidence for path 2.

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
  from every committed artifact. The scan is **split in two, because the needles
  divide into ones that are safe to commit and ones that are the very data being
  excluded.**

  **Half A — recorded, and re-runnable by anyone.** The transcript's header
  records a fixed set of *non-identifying* needles as literals: `/Users/`,
  `/home/`, `~/`, `/var/folders/`, and an email-address *pattern* (a shape, not an
  address). The check scans the transcript **below its header** — the header is
  where the needle list lives, so scanning it would make the check false by
  construction. Recording these as literals rather than deriving them is what
  makes the check reproducible: a needle computed at check time passes vacuously
  on every machine but the one that wrote the transcript.

  **Half B — host-derived, and never written down.** The authoring OS account
  name, the authoring machine hostname, and the organisation domain token are
  read from the authoring environment at check time and are **never written into
  any committed artifact, the header included.** The privacy convention bans
  usernames, account identifiers, device names, and org domains from every git
  artifact, so a needle list carrying them would be the violation the control
  exists to prevent. The transcript records only the *outcome*: the count of
  host-derived needles scanned and the number of matches, which must be zero. The
  GitHub handle used for authorship fields is carved out of both halves, because
  the privacy convention rules it is not personal data.

  Half A's failing observable is a planted `/Users/<name>/` path in the transcript
  body. Half B's is that T11 records a non-zero match count, or records no outcome
  line at all. No repository-wide lint backstops either half.
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
  2.18.2, PR #1192; `references/state-schema.md` documents both fields, and every
  fenced `review record` invocation in the shipped skill passes the flag)
- Technical: AC19 is additive for twelve of the fifteen shipped rows, whose
  prescribed action already agrees with the Routing table. The two spec-plan `DONE`
  rows are the exception: they prescribe a reset conditioned on a later human
  request, so their identifier column carries `complete` — the action `next`
  returns — while their prose keeps describing the conditional reset as a human
  path. Exactly one row's prose is rewritten — the `gates-clean`/`CODE-REVIEW`
  row, which AC19 requires to gain the budget branch; every other row's prose is
  untouched, and the additive-diff argument is made for those. The **three** tests
  that pin row prose keep passing, and this is the site that enumerates them, so
  AC19's task and T8's Done-when refer to this enumeration rather than restating a
  count. They locate their row by substring and
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
- Technical: reading a Status through the canonical reader loads and executes
  `scripts/lint-spec-status.py`, which is why AC15 declares five files rather than
  four. Two residuals come with it and neither is closed here. The loader `lstat`s
  the module path and refuses a non-regular file, saves and restores
  `sys.dont_write_bytecode` so it writes no bytecode of its own, and requires the
  symbols the guard path uses so a truncated module fails to load rather than
  loading half-parsed — but a **pre-existing poisoned `.pyc`** would still be
  executed, which the loader's own docstring records as accepted. Separately, the
  resolver shells to `git rev-parse --show-toplevel`, so the verb is not
  subprocess-free even though it is write-free. Both are inherited from controls
  this contract reuses rather than introduced by it (source:
  `_loop_guards.py:600-686` and `:891-923`; `loop-engine.py:140-157`)
- Technical: `next` runs unlocked by construction. `_statelock` guards a path by
  creating a sibling lock file, which AC16 forbids, so the two state files are
  sampled at different instants and a concurrent writing verb can produce a torn
  pair. P6's `run_id` comparison bounds only cross-*run* confusion, because
  `run_id` is constant within a run; it does not bound a `plan_review_status`,
  `schedule_waves`, or `transition_sequence` value captured mid-write. This is
  accepted: the verb is advisory, the agent re-reads before acting, and every
  writing verb it names re-validates under the lock. Two atomic-write temporaries
  are detectable from disk, and P1 refuses on only one of them: the cohort's
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
- Technical: an amendment made after the review budget is already spent stops on
  its first review call, and that is the design rather than a gap. The stop is
  `await-replan-decision`: a `wait` with `human_wait: true`, carrying
  `ref:delivery-contract-lifecycle` in `load`, whose stderr reason names both
  continuations the engine itself offers — reset and start a new run, or the
  paired human-authorised `--allow-retry-cap-override`. No mechanism is added to
  route around it. Every attempt to do so produced a worse artifact, and the
  information the human needs to choose is already in the record and the reason
  (source: `loop-engine.py`'s cap refusal text, which names both remedies)
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
  serialized compact, comfortably inside the bound AC13 states — `cohort.record-attempt` at `CODE-IMPLEMENTATION`, carrying a
  UUID `cycle_id` and one `load` entry — so the bound AC13 states leaves 209%
  headroom while still detecting an embedded state dump. AC13 declares itself the
  single home of that figure, so the literal is not repeated here. The bound is asserted in
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
