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
contract; the acceptance criteria assert properties *of* them — totality,
determinism, closure, each row's observable, each attribute's observable,
precondition outcome, precondition ordering, and discriminator resolution — so
adding a state or an action changes a table row rather than a criterion.

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
| Operations | Applicable — the manual-QA transcripts are the only evidence the assembled route works | `docs/specs/work-loop-next-projection/notes/qa-transcript-1.md` and `notes/qa-transcript-2.md` | Implementing agent | Two recorded transcripts with actions, states, and exit codes | Both transcripts committed, one per file |
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
budget already spent. **D5 reports what it reads, everywhere**, and suppressing
`cap-reached` there would not make the projection silent — it would make it
answer something else, `spec.review`, while the engine still refuses
`findings-remain`, so the record would name one continuation that could not be
taken. An amended contract
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
argument does not reach, and AC15c is what bounds it. Confinement precedes both
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
explains why no record can be built without one — so a zero-exit `halt` record
here would be unconstructible in exactly the state the row exists to catch.
Refusing keeps every zero-exit row downstream of P6's well-formedness proof, so
AC7's and AC9's "on a zero exit" clauses are total. A
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
value and `cycle_id` is derived from it. It is not the only such lever:
`from_index` is a second state-derived integer, and **AC11a bounds that one**,
at the same magnitude and for the same reason. A Precondition cannot, because
`last_event_context.completed_wave_index` is meaningful only at the one routing
key that reads it, so refusing on it here would refuse runs that never touch it.
Between this row and AC11a every state-derived value reaching the record is
bounded; nothing else in the record varies in
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
*before its first `##` heading* matching this pattern, case-insensitively:

```text
^[\s>*_`-]*Mode[\s*_`]*:[\s*_`]+light(?![\w-])
```

The pattern is fenced rather than held in a code span because it contains
backticks of its own: inside a single-backtick span CommonMark pairs the runs
left to right, which splits the pattern across code and emphasis runs and
swallows the following two sentences. The fence is the only form that renders
byte-identical to the pattern the implementation must carry.

The colon and at least one following separator are both required, and the
trailing guard rejects a hyphen, so neither `Modelight` nor `light-weight`
matches. The
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
  skipping it is recorded in assumption **A5**.
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

- **Table properties — totality, determinism, closure, each row's observable,
  each attribute's observable, precondition outcome, precondition ordering, and
  discriminator resolution: TDD.** The tables are a compressible invariant over a closed, enumerable domain.
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
- [ ] **AC6 — precondition observable.** For every Preconditions row, a state
  matching that row and no earlier one produces that row's exit and record, and
  stderr names what the row's last column requires. Every non-zero row returns
  the distinct code the Preconditions preamble allocates; that preamble is the
  single home of both the row count and the code count.
- [ ] **AC6a — precondition ordering.** For every ordered pair of Preconditions
  rows, a state matching both produces the earlier row's outcome. The pairs that
  make ordering load-bearing rather than incidental are P1 over P2, P3, and P4,
  and P2 over P4; a run that reports a later row's outcome for any such state
  fails this criterion.
- [ ] **AC6b — discriminator observable.** Every Discriminator resolves to the
  value its table's row and catch-all define, for each of that Discriminator's
  values, and a state satisfying two of them resolves to the one the
  Discriminators section orders first. D5 resolves to `malformed` for a
  `state.json` whose `max_review_retries` is absent, and to `cap-reached` only
  for one present and spent — a run that answers `cap-reached` on the absent case
  fails this criterion.

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
  state in the engine's transition table for the run's mode, read at runtime,
  **less any event AC10a omits**, and is empty exactly when that state has no
  outgoing transition. Pinning it to a constant fails this criterion. The
  subtraction is stated here rather than only in AC10a because "exactly" and
  "omits" are otherwise jointly unsatisfiable at the two review states, where a
  test written to either criterion reddens the other.
- [ ] **AC10a — no false clean.** At a review state whose D5 value is **anything
  other than `within-budget`**, `complete_with` omits `reviewers-clean`. The key
  is the complement, so the omission holds at `cap-reached`, `stasis`, and
  `malformed` alike, and at any value D5 gains later until someone decides
  otherwise. Emitting `reviewers-clean` at any of the three fails this criterion —
  three failing observables, one per non-`within-budget` value. Assumption **A3**
  records why this exception is load-bearing on each branch.
- [ ] **AC11.** Every `parameters` value matches `^[A-Za-z0-9:._-]+$` or is an
  integer. No `parameters` value is ever a boolean: the Action attributes table
  declares no boolean key, and permitting one would admit `True`, which Python
  counts as an integer. For a value read from either state file this is a
  **runtime refusal, not a suite assertion** — a value that fails yields the
  `halt` record on a zero exit, as the Exit convention requires of every computed
  stop, rather than being coerced into a record that carries it.
- [ ] **AC11a — `from_index` fidelity.** `from_index` equals the wave index the
  engine recorded as completed. On a resume where the advance already landed, the
  emitted `from_index` is that index and not one higher: a record that would make
  the loop skip a wave fails this criterion. A recorded index that is absent,
  negative, boolean, not an integer, **or at or above the magnitude P6 bounds
  `transition_sequence` at** yields `halt` — never an invented, defaulted, or
  coerced index. The magnitude clause is not decoration: `from_index` is the
  second and last state-derived integer reaching the record, and a positive
  4,000-digit value is none of the other four rejections, so without it a
  P6-admitted state file still produces a record many times AC13's bound on
  stdout. A record carrying an oversized `from_index` fails this criterion.
- [ ] **AC11b — load resolution.** Every `load` entry names a file that exists
  under the skill's `references/` tree. Emitting an identifier with no matching
  file fails this criterion.
- [ ] **AC11c — the bypass mitigation stays stated.** The reference R2 and R3
  name in `load` states, in text a grep finds, that `spec.md` returns to `Draft`
  and `plan.md` to `Drafting` before `spec-ready` is fired. Existence of the file
  is AC11b's subject and is not enough here: assumption **A5** records that
  nothing in the engine enforces this reset and that skipping it lets one
  resumption cross both human gates, so the reset instruction is the whole of the
  mitigation. An edit that removes it from the reference fails this criterion.
- [ ] **AC12.** No record carries a schedule array, amendment history, finding
  fingerprint, or verbatim copy of either state file. A fingerprint is the case
  this criterion uniquely catches: a 64-character hex digest satisfies AC11's
  character class and would occupy a declared `parameters` key without violating
  AC5 or AC7.
- [ ] **AC13.** No record in the domain exceeds 1024 bytes, measured as the UTF-8
  byte length of the JSON object written to stdout, excluding any trailing
  newline. This criterion is the single home of that figure; the Assumptions and
  the plan reference it rather than restating the literal. The observed maximum is
  pinned alongside the bound, so growth is visible before it reaches it.
- [ ] **AC13a — the bound holds against planted state.** No record exceeds AC13's
  bound for **any** `engine-state.json` P6 admits, not only for the domain. The
  domain varies no scalar's magnitude, so a criterion asserted over it alone
  would pass while a planted state file produced a record many times the bound.
- [ ] **AC14 — bounded stderr.** No value the verb interpolates into a stderr
  reason reaches stderr verbatim when it is over-long: a planted oversized
  `run_id` appears truncated and marked, so a reader can see where untrusted
  text ends, and the whole reason is itself bounded. Removing either the
  truncation or the marker fails this criterion. **A second failing observable is
  required at a different interpolating Preconditions row** — P8's stderr names
  the offending `(state, last_event)` pair, both `engine-state.json` values P6
  does not form-check — because a criterion binding every interpolated value
  while naming one is satisfied by an implementation that bounds that one site
  and misses the rest. The bound and the marker form are the ones the shared
  guard module already applies; assumption **A1** records what that control
  actually emits, and **A2** records why the `argv` clause binds this verb's own
  new code and has no instance today.
- [ ] **AC14a — neutralised stderr.** A control sequence planted in a state-file
  value reaches stderr escaped, not verbatim. P7 and P8 exit **zero**, so their
  reasons do not travel the non-zero refusal path whose escaping AC14's bound
  reuses, and both interpolate values P6 does not form-check — `run_id` at P7 and
  the `(state, last_event)` pair at P8. Planting an `ESC [ 2 J` sequence and a
  forged success line in `engine-state.json`'s `last_event`, and observing it
  verbatim on P8's stderr, fails this criterion. Length is AC14's subject and is
  not enough on its own: an implementation that truncates and marks without
  escaping is green on AC14 while forging a tool result into the supervising
  agent's captured transcript, which is the documented reason the shared
  escaping control exists.

### Reads

- [ ] **AC15 — bounded read surface.** From the first statement of the `next`
  subcommand's handler to its return — the counting origin, which excludes
  interpreter startup and the engine's own module imports — the verb opens no
  file outside a declared set: both state files, both artifact Status files, and
  **the two Python modules the handler loads by path** — the shared guard module
  and the canonical status parser — each **in whichever form the loader actually
  opens**, its source or its `__pycache__` bytecode. The guard module belongs in
  the set for the same reason the parser does and is easy to miss for the same
  reason: it is loaded lazily *from inside the handler*, by the identical
  `spec_from_file_location` and `exec_module` mechanism, and so falls inside this
  criterion's counting window rather than before it. Both forms of each are in the
  set because the
  loader consults the cache when one is present and falls back to the source when
  it is not, so a set naming only the source is satisfied on a cold tree and
  violated on a warm one — a criterion whose verdict turns on `__pycache__` state
  rather than on the verb. An open outside the set fails this criterion. **The
  claim is over in-process opens**, which is the class an open-tracer can
  observe; the resolver's `git rev-parse` subprocess is outside the claim and is
  carried as a stated residual rather than left to satisfy the criterion by being
  invisible to its instrument. Assumption **A4** records why each module is in the
  set and what residuals come with them.
- [ ] **AC15a — reads only what it needs.** Each artifact Status file is opened
  only on a run whose state consumes it; a run needing neither opens neither, and
  a run that always opens both fails this criterion. **One carve-out:** with no
  `engine-state.json` there is no such state, and `spec.md` is opened anyway for
  the light-mode marker P2 through P4 test.
- [ ] **AC15b — hostile files are refused, not followed.** At each of the four
  data files, a symlink, a non-regular file, and an oversized file each produce a
  refusal rather than being followed, read, or blocked on.
- [ ] **AC15c — crash artifacts are never opened.** P1's two artifacts are
  detected by presence alone. A symlink, a directory, or a FIFO at either
  location is detected as present and produces P1's refusal, with no read, parse,
  or repair at either.
- [ ] **AC15d — confinement precedes the probes.** An argument resolving outside
  the repository, and one escaping through a symlink, are each refused with no
  record and no filesystem access **strictly beneath** that argument — P1's
  glob being the access this bars. "Strictly beneath" is meant literally and
  excludes the argument itself and its ancestors: canonicalising the argument
  walks those, and that walk is how the symlink escape is detected, so a
  criterion barring it would forbid its own confinement mechanism. A
  run that probes under an out-of-repository argument before refusing fails this
  criterion. The pending-events stat is under a root the argument does not reach,
  so AC15c rather than this criterion is what bounds it.
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
  Changing one identifier fails this criterion. **Exactly one shipped row needs
  more than a column:** the `gates-clean`/`CODE-REVIEW` row, whose prose tells a
  resuming agent to re-run the reviewer fan-out — the instruction R25 exists to
  suppress once the review budget is spent. That row's prose gains the budget
  branch, so no shipped row prescribes an action its own identifier column
  contradicts. The two spec-plan `DONE` rows are **not** in that set: their prose
  describes a conditional reset the projection answers as `complete`, and the
  reset is a human-initiated path the projection cannot observe, so the
  identifier column is the whole of what they owe and their prose stands
  unchanged.
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

  **The header has a mechanical boundary and each transcript is its own file.**
  The header is the run's opening fenced block, and the scan region is
  everything after that fence's close to end of file. Both are needed: without
  the fence there is no edge, so 'below its header' names no region an
  implementer can compute; and with two transcripts in one file the first
  transcript's region would contain the second's header, whose recorded
  literals include `/Users/` and `/home/` — a guaranteed match on the very
  needles the exclusion exists to permit. Each transcript therefore lives in
  its own file under `notes/`. The header is also closed by construction: it
  may contain only this needle list and Half B's outcome line, and nothing
  free-form, because an excluded region that admits prose is where a device
  name or a path lands unscanned.

  **Half B — host-derived, and never written down.** The authoring OS account
  name, the authoring machine hostname, and the organisation domain token are
  read from the authoring environment at check time and are **never written into
  any committed artifact, the header included.** The privacy convention bans
  usernames, account identifiers, device names, and org domains from every git
  artifact, so a needle list carrying them would be the violation the control
  exists to prevent. **Half B scans the entire committed artifact, header
  included** — the exclusion Half A needs is Half A's alone, because Half B's
  needles are not written anywhere and so cannot match themselves. The transcript
  records only the *outcome*: the number of needle classes scanned and the number
  of matches. **The scanned count must equal the three classes named above, and a
  needle that does not resolve on the authoring host fails the check rather than
  reducing it** — a run recording "2 scanned, 0 matched" means one class was
  never searched, which is a privacy control reporting green while silently
  degraded. The GitHub handle used for authorship fields is carved out of both
  halves, because the privacy convention rules it is not personal data.

  Half A's failing observables are a planted `/Users/<name>/` path in the
  transcript body, and a header carrying anything but the needle list and the
  outcome line. Half B's are a non-zero match count, a scanned count below three,
  a missing outcome line, and a planted identifier in the header. No
  repository-wide lint backstops either half.

  **Each half names where it runs and records what it ran.** Half A is a
  script committed beside the transcripts, so "re-runnable by anyone" is a
  property of a file rather than a claim; Half B runs at authoring time only,
  because its needles resolve from the authoring environment. Each transcript's
  outcome line records the command invoked alongside its result, so a reader
  can tell a check that passed from one that was never run — a count with no
  command behind it is indistinguishable from a count someone typed.
- [ ] **AC25.** `docs/product/changelog.md` carries a free-standing
  `## [core][<version>] — YYYY-MM-DD` entry at top level rather than nested under
  `[Unreleased]`, containing a `### Highlights` block; and `packs/core/pack.toml`
  and `packs/core/.claude-plugin/plugin.json` read the same version, one minor
  above **the highest `core` version already released on this branch**, which is
  not necessarily the base branch's. The distinction is load-bearing here: this
  branch carries an unrelated `core` release for the `new-spec` grounding-evidence
  guidance, scoped by the owner as its own commit, so a formula reading from the
  base branch names a version this branch has already consumed. That release is
  not this contract's; the Durable Outputs name only the entry this contract
  writes.
- [ ] **AC26.** `make build-self-dry-run` reports no projection drift, and the
  generated highlights projection matches **this contract's** changelog entry —
  identified by the version AC25 computes, since more than one `core` entry is
  present on the branch.

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
- Technical (**A1**): what that control emits is a truncated `repr`, and the
  delimiters are **not balanced**. `_scalar` computes `repr(value)` and, when it
  exceeds the scalar cap, replaces the tail with a single `…`. An over-long
  string therefore reaches stderr as an opening quote, the capped prefix, and a
  trailing ellipsis — there is no closing quote. The ellipsis is the end marker,
  which is why AC14 says "marked" rather than "delimited": a criterion demanding
  a matched pair of quotes would be satisfiable only by re-implementing the
  control this contract reuses (source: `_loop_guards.py:145-156`)
- Technical (**A2**): AC14's `argv` clause has no instance today, and closing it
  is *Ask first* rather than in scope. The only argv-derived refusal is AC15d's,
  which routes through the pre-existing shared resolver; that resolver
  interpolates the raw argument uncapped and returns through the engine's generic
  `stop()` path, which escapes control characters but applies neither cap.
  Capping it would edit a stderr line `init`, `transition`, `status`, and `reset`
  also emit — a shared-output change this spec's Boundaries route to *Ask first*
  — and no such decision has been taken. The clause is stated so that any argv
  value this verb interpolates *itself* is bounded from the first line written
  (source: `loop-engine.py:943-961` and `:964-966`; the Boundaries *Ask first*
  entry on shared engine output)
- Technical (**A3**): AC10a's omission is the only backstop on all three branches, not
  two — including at the cap, where it is tempting to assume the engine helps.
  It does not: `_GUARDS` maps both modes' `findings-remain` to the
  cap-consulting `_guard_check_phase_review` and maps `("code",
  "reviewers-clean")` only to a spec-Status-token check, with no `("spec-plan",
  "reviewers-clean")` entry at all. At the cap the engine therefore refuses the
  *repair* event and still accepts the *clean* one, which is what the Routing
  prose has said all along. A roster check binds these three facts to the live
  `_GUARDS` table, because this Assumption is what AC10a's rationale rests on. At `stasis` nothing anywhere reads the
  fingerprint pair; at `malformed` the verb could not read the budget and so
  cannot know the review is unspent. On every branch this projection is the only
  thing standing between an unresolved review and a declared clean. Advertising
  the clean event in the field an agent parses to choose its next move is
  the false-clean pressure R5 and R25 exist to remove. The general "the guard
  refuses an illegal choice anyway" argument does not hold here: that guard
  checks the spec's Status token rather than whether the review was clean, and in
  spec-plan mode the edge has no guard at all (source: `_GUARDS` in
  `loop-engine.py:894-909`, which registers no `("spec-plan",
  "reviewers-clean")` entry)
- Technical (**A4**): the handler loads and executes **two** sibling modules by
  path — `scripts/_loop_guards.py`, which supplies every blessed reader, and
  `scripts/lint-spec-status.py`, which the canonical status reader in turn
  executes to parse a Status line. Both are loaded lazily from inside the handler,
  so both sit inside AC15's counting window, and each may be opened as source or
  as `__pycache__` bytecode; that is why AC15's declared set is not just the four
  data files. Two residuals come with the loaders and neither is closed here. Each
  loader `lstat`s
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
- Technical (**A5**): an unreset `Approved` after a rejected plan gate auto-fires
  the spec gate, and this contract mirrors that rather than introducing it. Nothing guards
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
  `loop-cohort.py` in two, at `:96` and `:2061`)
- Technical: the canonical Markdown status reader raises for a file it cannot read
  and returns nothing for a file with no recognised Status line, which is why D1
  and D2 collapse every other outcome into one `other` value (source:
  `_loop_guards.py` `read_md_status` at `:891-923`)
- Technical: the light-mode marker regex P3 defines was validated against the live
  corpus before this contract was opened: over `docs/specs/*/spec.md` with HTML
  comments stripped, it matches in the pre-`##` zone for exactly those specs that
  carry a real marker and no others. The count is deliberately not written here:
  it was 37 when this contract opened and is 38 today, because the corpus grows
  under peers, so a literal decays into a false claim within days. The
  load-bearing half is the no-misses-and-no-over-matches property, which survives
  the corpus changing — across all six observed spellings, including
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
  UUID `cycle_id` and one `load` entry — so the bound AC13 states leaves
  roughly three times that measurement in headroom while still detecting an
  embedded state dump. The percentage is not written out: it is a function of
  AC13's literal, so restating it would give that literal a second home under a
  different name. AC13 declares itself the
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
