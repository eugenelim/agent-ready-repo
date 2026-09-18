# Spec: wave-complete dispatch receipts

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md) (Option A: `loop-engine` owns read-only guard enforcement, `loop-cohort` owns skill-invoked mutations); `loop-infrastructure-phase-1` (Shipped and frozen — its plan declares `check --phase implement` a Phase-1 compatibility stub, whose semantics this spec preserves); `work-loop-in-process-guards` (Shipped and frozen — it owns the in-process guard surface this spec extends)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Objective

A maintainer running the work loop in full mode is made to assert, once per plan
task, who implemented it, and the exit from code implementation refuses any task
in the current wave carrying no assertion and names it. Today that exit accepts
any readable state, so a wave in which the controller quietly did all the work
itself looks identical to one that dispatched an implementer per task. That
asymmetry is why the sequential-dispatch rule has little force: the review phase
will not advance without persisted reports and adjudication, while the
implementation phase asks for nothing. Running without an `implementer` subagent
installed stays legitimate — the controller records a decline instead, and the
exit accepts it — so an adopter without the agent sees a loop that still
completes, with the degradation written down rather than inferred.

The check has its own phase, `wave-exit`. `--phase implement` keeps the
semantics it has today, because local `make pre-pr` and the always-run
`build-check` pull-request gate run that phase for every spec directory with no
state-machine gate. Moving the accounting into it would turn a wave-exit guard
into a repository-wide pre-PR and pull-request gate for this repository and
every adopter of the packaged hook.

What the exit guarantees is narrow and positive: a durable, per-task record of
who the controller says implemented each task, and a refusal when a task in the
wave has none. It does not prove dispatch happened. The exceptions group by
consequence rather than by count, so finding another does not falsify a number:
some let a record be written by a party or for a reason the guard cannot check
(any actor that can read `run_id` can write one, including a dispatched
`implementer`; and `human-directed` records a human instruction with no testable
precondition); some let an exit pass without a fresh assertion (a repair round
re-enters implementation without moving the wave pointer); and some leave no
trace
that enforcement was off (removing the container disables enforcement for as
long as the key is absent, and the contents can be restored afterwards, so the
window leaves no durable trace; and an enforcement-off exit writes nothing an
after-the-fact reader can find). The
plan's Risks section carries each, and the register holds the ones with owners.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable — the loop gains a refusal an adopter can hit | `docs/product/changelog.md`, `[core]` entry with a `Highlights` block | work-loop release step | Topmost `## [core][<version>]` entry agreeing with both pack manifests | Entry names the new refusal and the declines that avoid it, at the strength the Objective states |
| Maintainer procedure | Applicable — the controller gains a required call per plan task and a required check before the exit | `packs/core/.apm/skills/work-loop/SKILL.md` § Step 2. EXECUTE and its `wave-complete` firing sites; `references/supervisor-mode.md` § Single-agent fallback and its firing site; and the firing sites in `references/session-resumption.md` and `references/finding-adjudication.md` | this spec | Section-scoped checks find the record call, its authorship, the pre-exit check, and both decline reason codes | Projections regenerated and byte-identical across the three copies |
| Interface compatibility | Applicable — durable cohort state gains an additive field an older version ignores | `packs/core/.apm/skills/work-loop/references/state-schema.md` | this spec | The field documented with its absence rule | State-schema reference names the field and what an absent field means |
| Decision rationale | Not applicable — ADR-0061 already decides the Option A split this change sits inside; no new decision is taken | — | — | — | — |
| Reusable learning | Applicable — the measurement that motivated this change, and the proof the guard bites | `docs/specs/wave-complete-dispatch-receipts/notes/verification-ledger.md` | this spec | The ledger is the single home for the dispatch-rate measurement and the mutation table | Ledger records both, each required by a task's `Done when` |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the record write an explicit `loop-cohort` mutation and the wave-exit
  check a read-only `loop-engine`-consulted guard, per the ADR-0061 Option A
  split.
- Authorize the record write exactly as every other cohort mutation is
  authorized: by a matching `--expect-run-id`. Treat that as what it is — a
  staleness and run-pairing check that excludes a caller from another run. It is
  not an authenticator, and it does not establish which party called. Any actor
  that can read the spec directory can read `run_id` from `state.json` and
  invoke the verb, and that includes a dispatched `implementer` subagent, which
  ships with filesystem and shell access. A record is therefore an assertion,
  not a proof of who made it, and nothing scopes a record to the task its writer
  was dispatched for.
- Treat the partition digest the same way. It is an unkeyed function of
  `schedule_waves` held in the same file as the records it partitions, so anyone
  who can write a record can compute the current digest. It discriminates a
  stale partition from the live one; it is not evidence of who wrote a record.
- Disclose the schema toggle at the same strength. The verdict table passes
  silently on a state whose `schema_version` is not the supported value, by
  design, so an actor who can write `state.json` sets an unsupported value,
  fires the transition, and restores the supported value afterwards. Nothing
  durable records that the exit passed unchecked. While the mismatch stands the
  run is not free — `loop-cohort status` refuses, and every run-scoped mutation
  that reads existing cohort state refuses — but those refusals constrain only
  the window, not what happened inside it. Of the four routes this is the
  cheapest in effort and the quietest in evidence — one field set and reset, no
  durable trace — and it exists because
  preserving `check --phase implement`'s verdict for old state was chosen over
  closing it. Disclosed rather than closed.
- Disclose the forward pointer at the same strength. Every accounting statement
  here is scoped to the *current* wave, so an actor who can write `state.json`
  and sets `current_wave_index` from `n` to `n+1` in one field edit skips wave
  `n`'s exit entirely, and `wave advance --from-index n` then exits zero on the
  already-applied branch. It is quieter than forgery and than container
  deletion, and louder only than the schema toggle above: a forged record still
  leaves a per-task record to read, a
  deleted container flips `status` to not-enforced and triggers the exit's
  notice — though only while it is absent: an actor who removes the key, fires
  the exit and the advance, then restores the saved contents leaves `status`
  reporting enforced and nothing but an ephemeral stdout notice behind — and a
  forward pointer leaves a populated container, an enforced `status`, and a
  silent exit. Nothing in this spec detects it, because
  detecting a wave below the pointer needs a per-wave completion record that
  ADR-0061 Option A cannot write. It is disclosed rather than closed.
- Give every guard verdict a precondition that no other verdict's precondition
  can also satisfy, and make the verdicts jointly cover every cohort state. The
  verdict table below is the contract; branch order in the implementation is
  then an optimisation rather than the thing that decides behaviour.
- Reuse the guard layer's existing non-negative-integer validation for
  `current_wave_index` rather than introducing a second integer predicate. The
  existing one rejects `bool` and owns its message shape, and two predicates on
  one field is how they drift.
- Let the guard pass when the receipts container is absent, which is cohort
  state written before receipts existed, so a run already in flight when this
  ships still completes. That is the only such exemption. An absent or empty
  `schedule_waves` is *not* one, **on a state whose schema is supported**: the
  two are indistinguishable to a reader that supplies `[]` as the default, and
  the well-formedness rule below classifies that state malformed. The scope
  matters and is not a hedge — the unsupported-schema row passes before any
  shape is read, deliberately, so that the transition's verdict is preserved
  for the oldest state class. An unsupported-schema state with an empty
  partition therefore passes, and that is the compatibility guarantee rather
  than a second verdict for one state.

  The reason to refuse rather than exempt is not that the state is unreachable
  — it is reachable, through the amendment crash window described under the
  well-formedness rule. It is that the pass direction is silent: an empty
  current wave satisfies "every task in the current wave is accounted for"
  vacuously over zero tasks. Refusing costs a resuming controller one read of
  `amendment_pending`; passing costs the guarantee.
- Carry the absent-container exemption inside the shared accounting predicate,
  not beside it, so every consumer of that predicate inherits it rather than
  restating it.
- Name every task the guard could not account for in its refusal, not a count.

### Ask first

- Adding a decline reason code. The accepted set is closed, and a third code
  changes what the exit will excuse.
- Making the guard enforce anything beyond per-task accountability — the
  content of a report, or the identity of the party that recorded a record.
  Establishing caller identity is a new trust mechanism and needs sign-off.
- Changing `loop-engine.py`'s guard adapter. `_guard_reason` returns `None` for
  any passing result, so a design needing the engine to surface a passing
  guard's text is a change to a contract every guard shares.
- Scoping a record to a repair round. That changes an existing verb's refusal
  set in a way this spec does not attempt.
- Any change to the `wave-passed` guard or the review-phase guards.

### Never do

- Change what `check --phase implement` returns for any state. Local
  `make pre-pr` and the always-run `build-check` pull-request gate run that
  phase for every spec directory with no state-machine gate, so a refusal there
  is a pre-PR and pull-request gate, not a wave gate.
- Give the record durable side-effect semantics: no `pending_transition` entry,
  no idempotency key, no crash-safe replay. Those are ADR-0061 Option B, they
  need a schema that does not exist, and building them here would require
  superseding a Frozen ADR.
- Let the read-only guard write, migrate, or repair cohort state — including
  creating an empty receipts container on first contact.
- Regenerate or hand-author a row in the golden CLI stream fixture. It is
  generated once, before the guard extraction, and deliberately never
  regenerated; a hand-written capture is a comparison value this change supplies
  for itself.
- Remove a record by any path other than the three this spec names: a
  `schedule` run whose partition differs from the one a record was written
  under, a contract amendment, and `loop-cohort reset`, which unlinks
  `state.json` and so removes every record with it.
- Accept a record for a task the named wave does not contain, or for a wave the
  run has not yet reached.

## Testing Strategy

- **The verb's accept and refuse behaviour: TDD.** A receipt write, a decline
  write, a rejected reason code, a rejected unknown task, a rejected wave index
  at each bound, a rejected run identifier, an unusable partition, and a
  replaced duplicate are compressible invariants over pure state, exercised by
  unit tests against the loaded module.
- **The guard's verdict: TDD.** Whether `check --phase wave-exit` passes or
  refuses is a pure function of cohort state. Each row of the verdict table gets
  its own case asserting the exit code and both streams.
- **The verdict table partitions the state space: TDD.** One case constructs
  cohort states by varying the fields the rows read — including the type of
  `schedule_waves`, the type of its current element, the presence and type of
  the container, and the type and range of the pointer — and asserts that every
  constructed state satisfies exactly one row and that every row is satisfied by
  some state. Four review rounds produced criteria that overlapped or left gaps,
  and a per-row example cannot find either, because its states come from the
  rows. The domain must be able to exhibit a counterexample in both directions.
- **`--phase implement` is unchanged: goal-based check.** `Done when:` the
  golden parity replay of `check --phase implement` passes untouched, and the
  pre-PR hook's verdict for a state with an unaccounted task is unchanged.
- **The guard reaching the live transition: goal-based check.** `Done when:` the
  `wave-complete` transition out of `CODE-IMPLEMENTATION` exits non-zero on a
  wave with an unaccounted task. A guard that refuses only when called directly
  would leave the real exit open.
- **The record lifecycle: TDD.** That a partition-changing re-schedule removes
  stale records, that a partition-preserving re-schedule keeps them, and that a
  contract amendment clears them, are three assertions over `schedule` and the
  amendment path.
- **The verb and the guard agree: TDD.** A record written by the verb is counted
  by the guard in the same run, asserted as a round trip. A test that the two
  name the same container key cannot be written when the key is single-sourced,
  which is the natural implementation; the round trip reddens under either
  divergence and under removal of either half.
- **The controller-facing surface: goal-based check.** `Done when:` a check
  scoped to each named section — not a whole-file grep — finds the literal
  calls, the authorship sentence, and both decline reason codes, and the three
  projected copies of each edited file are byte-identical.
- **The refusal's bounding and truncation disclosure: TDD.** One case drives a
  wave whose unaccounted-task list exceeds the interpolation bound and asserts
  the refusal states the list is partial and cuts at an identifier boundary; one
  case drives a state-derived value longer than the bound and asserts the
  refusal does not carry it whole. Both cases run against **every** refusal
  this change adds, including `wave advance`'s new unaccounted-task refusal,
  which emits through `loop-cohort`'s own diagnostic helper — a channel the
  ledger measures as applying no length bound at all. Naming the verb here
  because a criterion that says "the guard or the verb" and cases that drive
  only the guard is the exact shape this repository has already paid for.
- **Mutation proof: manual QA.** Each guard and verb clause is removed in turn,
  the suite is re-run, and the observed red is recorded. A clause whose removal
  leaves the suite green is not yet verified, whatever its tests are named.

## Acceptance Criteria

### What accounts for a task

A wave partition is the value of `schedule_waves`, with an absent key read as
the empty list, matching every existing guard that reads it. Its digest is a
stable function of that value alone, so it changes exactly when the partition
changes. Each record is held under the partition digest, wave index, and task
identifier current when it was written.

- [x] A record accounts for its task when it is held under the digest of the
      current wave partition. A decline's reason is not re-checked here: a
      reason outside the closed set makes the value not a record at all, so the
      state is not well-formed and the malformed row decides it. Stating it in
      both places would leave the second clause dominated — unable to decide
      any state, and unable to redden when removed.
- [x] A record held under any other partition digest accounts for no task.
- [x] A record written to `state.json`, serialized, and read back still
      accounts for its task.
- [x] Editing `plan.md` in a way that leaves `schedule_waves` unchanged, then
      re-scheduling, leaves every existing record still accounting for its task.

### The record lifecycle

- [x] `loop-cohort init` leaves the receipts container present in cohort state.
- [x] `loop-cohort schedule` leaves the receipts container present in cohort
      state.
- [x] A `loop-cohort schedule` run whose resulting partition equals the one a
      record was written under leaves that record present and unchanged.
- [x] A `loop-cohort schedule` run whose resulting partition differs from the
      one a record was written under leaves no record under the superseded
      digest.
- [x] A contract amendment leaves the receipts container empty, so no record
      written before the amendment accounts for a task after it — including when
      the amendment is raised at wave index zero with no completed tasks, where
      the re-scheduled partition is identical and its digest therefore unchanged.

### The `dispatch-receipt` verb

- [x] Recording a receipt for a task in the named wave, with a matching run
      identifier, exits zero and leaves that task accounted for.
- [x] Recording a decline for a task in the named wave, with a matching run
      identifier and a reason from the closed set, exits zero and leaves that
      task accounted for.
- [x] Recording against the current wave index, and against any lower wave index
      the current schedule contains, exits zero.
- [x] Recording against a wave index above the current wave index exits
      non-zero, so a wave the run has not yet reached cannot be recorded
      against.
- [x] Recording against a wave index that is not a non-negative integer, by the
      guard layer's existing validation, exits non-zero.
- [x] Recording when the current partition is empty, or when the current wave
      index is not a valid index into it, exits non-zero and names the unusable
      partition rather than raising.
- [x] Whenever `schedule_waves`, the wave element at the named index, or the
      receipts container holds a value outside the declared well-formed shape,
      the verb refuses by name rather than raising. The container is included
      because the verb reads and writes it, so it is a position the verb can
      raise on and one the guard's predicate is already total over. The hostile
      values are derived from the same key-path and well-formedness declarations
      that generate the guard's predicate, so neither side's coverage can be
      generated without the other's.
- [x] Requesting a receipt and a decline in one invocation exits non-zero.
- [x] A decline reason outside the closed set exits non-zero and names the
      accepted set.
- [x] A task identifier the named wave does not contain exits non-zero and names
      the task identifiers that wave does contain.
- [x] A run identifier that does not match cohort state exits non-zero.
- [x] On every invocation of the verb that exits non-zero, for any reason,
      `state.json` is byte-identical to its content before the invocation.
- [x] Recording the same partition digest, wave index, and task identifier twice
      exits zero both times and leaves exactly one record for that triple.

### Leaving a wave

A wave exit that refuses an unaccounted wave is worth little while a sibling
verb can step past the same wave unchecked, so `loop-cohort wave advance` is
coupled to the same accounting predicate. The coupling is on the branch that
*moves* the pointer, not on the branch that recognises the move as already
applied: the skill documents the verb as idempotent and re-issues it on a
`wave-passed` resume, so refusing on the already-applied branch would turn a
crash-recovery replay into a dead end.

- [x] `loop-cohort wave advance --from-index n`, on the branch where
      `current_wave_index` equals `n` and the pointer therefore moves, exits
      non-zero when any task in wave `n` is not accounted for, and names every
      such task.
- [x] That refusal leaves `state.json` byte-identical to its content before the
      invocation, so the pointer does not move.
- [x] On the branch where `current_wave_index` already equals `n + 1`, the verb
      exits zero regardless of whether wave `n` is accounted for, because the
      documented crash-resume replay re-issues it after the pointer has moved
      and a refusal there would strand the run.
- [x] The accounting predicate `wave advance` applies is the same one
      `check --phase wave-exit` applies, from one declaration, so the two
      cannot disagree about whether a wave is accounted for. The absent-
      container exemption is part of that declaration, not a separate guard-
      side rule. This criterion rests on single-sourcing and is not
      independently falsifiable by a test: two copies of a predicate agree on
      the day they are written. What is falsifiable is the absence of a second
      copy, so the mutation record carries the removal of the shared
      declaration and names the cases in both consumers that redden together.
- [x] `loop-cohort wave advance --from-index n`, on the branch where the pointer
      moves and the receipts container is absent, exits zero and advances, so a
      run whose cohort state predates receipts is not stranded mid-schedule.
      Without this the coupling would refuse every in-flight run at its next
      wave boundary, which no migration step exists to repair.
- [x] The branch selector and the accounting predicate read
      `current_wave_index` through one declared reading: the guard layer's
      existing non-negative-integer validation. `cmd_wave_advance` today reads
      it as `int(state.get("current_wave_index", 0))`, which accepts `"1"`,
      `1.9` and `True` and raises on `None`, while the predicate's validation
      rejects all four — so which branch runs and whether the wave can be
      accounted for are currently decided by different readings of one field.
- [x] When that reading rejects the stored `current_wave_index`, the verb exits
      non-zero and names the field, and the pointer does not move. Denying
      rather than advancing is required because the alternative launders: the
      exit refuses on the pointer row, one advance rewrites the pointer to a
      clean integer, and the skipped wave is then permanently unaccounted with
      the container intact, so `status` still reports the guard enforced.
- [x] Every position the advancing branch reads — `schedule_waves`, the wave
      element at the index, `current_wave_index`, and the receipts container —
      refuses by name rather than raising, and the refusal names `reset` as the
      recovery when the unusable value is in cohort state the verbs cannot
      rewrite. The container is included because the advancing branch now reads
      it to apply the accounting predicate, which makes it a position the verb
      can raise on.
- [x] The verb's existing refusals — a non-matching run identifier, an empty
      partition, a negative `--from-index`, a `--from-index` at or past the end
      of the partition, the final wave, and a `current_wave_index` matching
      neither `n` nor `n + 1` — keep their current verdicts and are decided
      before the accounting check, so no state that refuses today refuses with
      a different reason after this change. The last of these is a third
      branch: the verb has an advancing branch, an already-applied branch, and
      a mismatch refusal, and only the first gains the accounting check.

### The verb and the unsupported-schema class

The exit tolerates a state whose `schema_version` is not the supported value, so
what the verb does for that same class is a criterion rather than an inherited
detail: leaving it unstated would let the exit ask for a record the controller
cannot write.

- [x] `loop-cohort dispatch-receipt` refuses a state whose `schema_version` is
      not the supported value, as every other cohort mutation does, and names
      the schema as the reason.
- [x] That asymmetry is stated in `references/state-schema.md`, on the
      `schema_version` field row, and in `references/supervisor-mode.md`
      § Single-agent fallback beside the decline codes: the exit
      tolerates the class and the verb refuses it, so on the oldest state the
      exit passes without a record and no controller action is owed at the
      exit. State the end-to-end outcome too: `_validate_run_id` refuses an
      unsupported `schema_version` for every run-scoped mutation that reads
      existing cohort state — `reset` and `init` do not call it, so the claim is
      about the run-scoped verbs and not about every verb — so that same
      state's next `wave advance` refuses on schema regardless, and the run
      cannot progress past the wave boundary without a schema migration. The
      exit's tolerance buys the transition, not the run.

### The `check --phase wave-exit` verdict

Exactly one row applies to any cohort state, and the rows together cover every
cohort state.

A **record** is a mapping whose `kind` is `receipt` or `decline`, and which, when
its `kind` is `decline`, carries a `reason` from the closed set
`no-implementer-installed` and `human-directed`. Nothing else is a record.

The container's **key path** is declared once, here: a record is held under the
partition digest, then the wave index, then the task identifier — three keys,
then a record. On disk, all three are JSON object-member names: the partition
digest text, the wave index in decimal string form, and the task identifier
text. Every statement about the container's shape derives from this declaration
rather than restating a nesting depth, because a restated depth is how the
previous version of this section came to require two keys while the data model
declared three, which classified every correctly shaped container as malformed
and would have refused every valid wave exit.

A state is **well-formed** when `schedule_waves` read with its default is a
**non-empty** list, and the receipts container is either absent or a mapping
nested to exactly the declared key-path depth whose every leaf is a record. The
parse is not a conjunct here: every row that reads well-formedness also requires
readability, and a readable state has parsed, so a parse clause could decide no
state.

On a state whose schema is supported, an empty partition is malformed rather
than a passing state, and so is an empty current wave. The scope is load-bearing
and matches the rail in Boundaries: the unsupported-schema row decides before
any shape is read, so an unsupported-schema state with an empty partition passes
on that row and never reaches this rule. Within the supported-schema case this
is the single verdict for the state Boundaries calls "no schedule persisted":
an absent `schedule_waves` reads as `[]` through the default, so the two are one
state and get one answer.

It is reachable, and a claim that it is not would be wrong. `topological_waves`
never emits an empty wave, but `begin_contract_amendment` writes
`schedule_waves: []` directly, and the engine applies that cohort mutation
before its own state write — so a crash between the two leaves cohort state
holding an empty partition while engine state still names
`CODE-IMPLEMENTATION`. A session resuming there and firing the pre-transition
check gets a hard refusal.

The refusal is the correct signal in that window rather than a dead end: the
same state carries `amendment_pending`, `loop-cohort status` reports that field,
and `approve-plan` consumes it by completing the amendment's re-approval — after
which `schedule` repopulates the partition. `references/session-resumption.md`
carries no row for this field, so the route exists in the verbs but is not
written down; naming it is the recovery this design owes, not a new mechanism.
Passing instead would be worse in exactly the
way the exceptions below disclose — an empty current wave satisfies "every task
in the current wave is accounted for" vacuously over zero tasks and would exit
silent. A refusal that points a resuming controller at the amendment it is
already in the middle of costs one read; a silent pass costs the guarantee. Away
from that window, either state can only come from a write to `state.json`. An
empty mapping at any level is well-formed: it holds no records, which is not a
defect. The predicate is total over every value any position can hold, so
accounting never meets a shape it cannot classify.

A state is **readable** when the guard's state acquisition returns a state
rather than refusing — the spec-directory resolution and the state read
together, since the guard invokes them as one step. Readability is not the same
as the file parsing: a non-object JSON
root parses and the read still refuses it, so a row worded around parsing would
fire alongside the read-refusal row. Every row below the read-refusal row
requires readability.

A schema is **supported** when `schema_version` has the supported value.

A **current wave** is well-formed when it is a **non-empty** list whose every
element is a string. A pointer is **valid** when `current_wave_index`, read as zero when the
key is absent, is a non-negative integer by the guard layer's existing
validation, which rejects `bool`, and is less than the number of waves in the
partition. Naming the shared preconditions once is deliberate: an earlier draft
asserted that each row negated the rows above it without writing those
negations, and two rows then covered the same state with opposite verdicts.

- [x] The guard's state acquisition refuses, for any reason in the refusal
      vocabulary of the surface the guard actually invokes: exits non-zero and
      names that reason on stderr. That surface is wider than the state read it
      wraps — it first resolves the spec directory, which refuses when the
      directory cannot be examined or is not a directory, before any read
      happens. The read then refuses for more than absence and unparseability:
      a non-object JSON root, a non-regular file, a file that changed while
      being opened or read, a document over the size bound, and a non-finite
      number are each refusals. A non-object root in particular *parses*, and a
      spec-directory refusal precedes parsing entirely, so a row worded around
      either parsing or the read alone leaves states satisfying no row at all.
- [x] The state is readable and its `schema_version` is not the supported
      value:
      exits zero and prints nothing to stdout or stderr. This row exists so the
      transition's verdict is *preserved* for that state class, not merely
      decided. Sharing `check --phase implement`'s exemption from schema
      validation only guarantees the state reaches the table; `implement`
      returns ok for any readable state, so a state it passes today could
      otherwise land on a refusing row below, on the shape of a field an
      unsupported schema leaves unspecified — which is the breakage this design
      exists to prevent.
- [x] The state is readable, the schema is supported but the state is not
      well-formed: exits non-zero and names the malformed field on stderr,
      rather than surfacing an exception type.
- [x] The state is readable, the schema is supported, the state is well-formed,
      and the receipts container is absent: exits zero and names the absent
      container on stdout.
- [x] The state is readable, the schema is supported, the state is well-formed,
      the container is present, and the pointer is not valid: exits non-zero
      and names the invalid pointer on stderr.
- [x] The state is readable, the schema is supported, the state is well-formed,
      the container is present, the pointer is valid, and the current wave is
      not well-formed: exits non-zero and names the malformed wave on stderr.
- [x] The state is readable, the schema is supported, the state is well-formed,
      the container is present, the pointer is valid, the current wave is
      well-formed, and every task in the current wave is accounted for: exits
      zero and prints nothing to stdout or stderr.
- [x] The state is readable, the schema is supported, the state is well-formed,
      the container is present, the pointer is valid, the current wave is
      well-formed, and at least one task in the current wave is not accounted
      for: exits non-zero and names on stderr every such task, and no accounted
      task, subject to the identifier-list property below.
- [x] Any state-derived list of identifiers in a refusal, from either the guard
      or the verb, names identifiers up to the guard layer's per-value
      interpolation bound — the tighter of the two bounds in play, and
      therefore the one that truncates. Where it truncates, the refusal states
      that the list is partial and cuts only at an identifier boundary, so no
      fragment of an identifier is presented as a task name.
- [x] Every value the guard or the verb interpolates into a refusal — whether
      read from `state.json` or supplied as an argument — passes through the
      guard layer's existing length-bounding helper, so no refusal carries an
      unbounded value. `loop-cohort`'s own diagnostic helper neutralises control
      characters but applies no length bound.
- [x] No cohort state satisfies the preconditions of two of the verdict rows
      above.
- [x] No cohort state satisfies the preconditions of none of the verdict rows
      above.
- [x] Every verdict row above is satisfied by some cohort state.
- [x] The states the three preceding criteria are checked over are constructed by
      varying the outcome of the cohort state read across **whether it returned
      a state or refused**, and the presence, type, and value of
      `schedule_waves`, of its
      element at the pointer, of the receipts container, of a record's `kind`
      and `reason`, of `schema_version`, and of `current_wave_index`. This list
      is the single canonical enumeration of the axes; a task's `Tests` field
      cites it rather than restating a subset. The read axis is two-valued on
      purpose: no verdict row discriminates among the reader's refusal kinds,
      so enumerating them multiplies the domain without adding a distinction
      any predicate makes. The instrument asserts that every kind it lists
      classifies to the read-refusal row and nowhere else, which is what
      licenses the collapse. It does not establish that the list is the
      reader's whole vocabulary — that list is maintained by hand, so
      completeness is the survey's obligation, not the walk's, and the
      instrument states the bound where the assertion lives.
- [x] The container values in that domain are generated from the declared key
      path — a correctly nested instance built from the declaration, then
      mutated at each depth with each hostile value — rather than hand-built at
      a literal depth. A hand-built container makes the walk's oracle ratify the
      shape its author constructed instead of the shape the declaration states,
      which is how a green walk coexisted with a predicate that rejected every
      valid container.
- [x] For every row above whose state has a `state.json`, that file is
      byte-identical before and after a `check --phase wave-exit` invocation.
- [x] The `wave-complete` transition out of `CODE-IMPLEMENTATION` is refused
      when the guard refuses.
- [x] `check --phase wave-exit` reaches the verdict table for a state whose
      `schema_version` is not the supported value, rather than refusing before
      the table, by sharing the exemption `check --phase implement` already has.
- [x] No state whose `schema_version` is not the supported value and for which
      `check --phase implement` exits zero today causes the `wave-complete`
      transition to exit non-zero after this change.
- [x] `check --phase review` and `check --phase gates-failed` still refuse a
      state whose `schema_version` is not the supported value.
- [x] `check --phase implement` returns the same exit code and the same streams
      as it does before this change, for the golden parity replay of that phase
      and for one state per row of the table above — the states the new rows
      distinguish being the only ones whose verdict could have moved.

### Reporting and reaching the check

- [x] Every *site* that instructs firing the `wave-complete` transition also
      instructs running `loop-cohort check --phase wave-exit` immediately
      before it, counted per site rather than per file. Some of these files
      carry more than one firing site, so a file-level check would let an
      uninstrumented site be absorbed by a covered sibling in the same file.
      The count is not stored here: the criterion below compares two counts
      both measured from the tree, which is what survives a site being added.
- [x] The count of instrumented sites equals the count of firing sites, so
      adding a firing site later without its check fails rather than passing
      silently.
- [x] GATES carries no such instruction: GATES fires `wave-passed`,
      `gates-clean` and `gates-failed`, and runs after the `wave-complete`
      transition rather than before it.
<!-- Why the criterion above exists, rather than a criterion itself: the
engine's guard adapter discards a passing guard's text, so the transition alone
cannot surface the absent-container notice and the pre-transition run is its
only caller. Nothing can red for a rationale, so it is not a checkbox. -->
- [x] The verdict that pre-transition run reports is about the wave the run is
      leaving — the wave `current_wave_index` names at the moment the check
      runs. A controller that advances the pointer first therefore does not
      satisfy this against the next wave's empty denominator.
- [x] `loop-cohort status` reports whether dispatch receipts are enforced for
      the run, in both its default output and its `--json` output.
- [x] A record written by `loop-cohort dispatch-receipt` is counted by
      `check --phase wave-exit` in the same run, with no intervening
      re-schedule.

### Controller-facing surfaces

- [x] `SKILL.md` § Step 2. EXECUTE names the literal
      `loop-cohort dispatch-receipt` as required once per plan task.
- [x] `SKILL.md` § Step 2. EXECUTE states that the controller records it and
      that an `implementer` subagent does not record its own.
- [x] `references/supervisor-mode.md` § Single-agent fallback names
      `no-implementer-installed` as the decline the controller records when no
      `implementer` subagent is installed.
- [x] `references/supervisor-mode.md` § Single-agent fallback names
      `human-directed` as recording a human instruction with no testable
      precondition.
- [x] `references/state-schema.md` names the receipts container and states that
      an absent container means the guard does not enforce.
- [x] Every controller-facing surface that instructs `loop-cohort wave advance`
      states the accounting precondition: the advance refuses a wave whose
      tasks are not accounted for. Required because `evals/evals.json` answers
      that the call "is idempotent and safe to replay" and
      `references/session-resumption.md` re-issues it marked "(idempotent)" —
      both true of the already-applied branch and both misleading about the
      advancing branch after this change. The eval answers that describe the
      call are updated in the same task.
- [x] `references/session-resumption.md` carries a row for a resume that finds
      `amendment_pending` set, routing to `approve-plan` and then `schedule`.
      Required because the wave-exit check hard-refuses an empty partition and
      that field is the only state distinguishing the amendment crash window
      from a hand-written one; without the row the refusal names a recovery
      no document describes.

### Proof

- [x] A mutation record names each removed guard and verb clause, the test that
      turned red, and the observed failure, with no clause whose removal left
      the suite green.

## Follow-ons

- eugenelim: `workspace.toml` `[backlog].open`, entry on
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` — refuse or
  disambiguate a duplicate plan task heading. Registered 2026-09-17; independent
  of this spec.
- eugenelim: `workspace.toml` `[backlog].open`, the entry on
  `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py` whose summary opens
  "Require a repair round to carry its own dispatch assertion" — require a
  repair round to
  carry its own assertion. `gates-failed`, `findings-remain`, and
  `blocker-applied` all re-enter `CODE-IMPLEMENTATION` without moving
  `current_wave_index`. Scoping a record to a round needs a counter that
  advances on all three edges; `implementation_retry_count` advances on one, so
  building on it would look like a control without being one.
- eugenelim: `workspace.toml` `[backlog].open`, the entry on
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` whose summary opens
  "Leave a durable trace when a wave exit passes" — a wave exit that
  passes with no container, or with every task declined, leaves no record an
  after-the-fact reader can find, because the read-only guard cannot write and a
  durable side effect on a transition is ADR-0061 Option B. `loop-cohort status`
  also refuses when `schema_version` is unsupported, so for the oldest state
  class the guard tolerates, neither status nor the stdout notice survives; no
  reporting channel remains.

## Assumptions

- Technical: the guard on the `wave-complete` transition out of
  `CODE-IMPLEMENTATION` is `check --phase implement`, an explicit Phase-1
  compatibility stub returning ok for any readable state. This spec retargets
  that transition's guard-table entry at a new `wave-exit` phase and leaves the
  `implement` phase alone (source: `check_phase` in
  `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py` and the
  `("code", "wave-complete")` entry in `loop-engine.py`'s guard table, probe
  2026-09-17)
- Technical: `tools/hooks/pre-pr.py` and its packaged copy
  `packs/core/.apm/hooks/pre-pr.py` glob every `docs/specs/*/state.json` and run
  `loop-cohort check <spec-dir> --phase <phase>` for both `implement` and
  `review`, gating only `review` on the engine state and exiting non-zero on any
  failure. Local `make pre-pr` reaches that hook through
  `tools/catalogue/pre_pr_catalogue.py`; `tools/repo/build_gate_chain.py`
  reaches the same helper as part of `build-check`, whose workflow runs on pull
  requests to `main` and pushes to `main`. A refusal added to the `implement`
  phase therefore gates local pre-PR checks and the always-run pull-request
  build check for every spec directory. This is the reason for a separate
  phase, and it is a caller no grep for `--phase implement` finds, because the
  phase name reaches the argument list through a loop variable (source:
  `tools/hooks/pre-pr.py`, `tools/catalogue/pre_pr_catalogue.py`,
  `tools/repo/build_gate_chain.py`, and the `build-check` workflow, probe
  2026-09-17)
- Technical: `PHASES` is a three-element tuple in `loop-cohort.py` supplying
  `--phase`'s argparse choices, and no test pins it, so a fourth phase is
  additive (source: `PHASES` in `loop-cohort.py` and a search of the pack and
  roster suites, probe 2026-09-17)
- Technical: the golden parity table's guard-family assertion keys on the verb,
  and its expected set of six families includes `check`. A new phase under the
  existing `check` verb adds no family and owes no golden row, which matters
  because the fixture is generated once and deliberately never regenerated
  (source: `test_the_table_covers_every_guard` in
  `packs/core/tests/skills/work-loop/test_loop_guards_parity.py` and the
  fixture-loading failure message in `test_golden_fixtures.py`, probe
  2026-09-17)
- Technical: `cmd_check` calls `_emit(result.message)` on a passing result, so a
  passing guard can print to stdout. What a passing guard cannot do is carry a
  `reason` — `GuardResult.__post_init__` raises unless `ok` is true exactly when
  `reason` is None — and `loop-engine._guard_reason` returns None for any
  passing result, so the engine cannot surface a passing guard's text. Nothing
  in the skill currently invokes `loop-cohort check --phase implement`, which is
  why the notice needs a documented caller rather than inheriting one (source:
  `cmd_check` and `_emit` in `loop-cohort.py`, `GuardResult` in
  `_loop_guards.py`, `_guard_reason` in `loop-engine.py`, and a search of
  `SKILL.md` and its references, probe 2026-09-17)
- Technical: `canonical_contract` normalizes exactly four things — line endings,
  per-line trailing whitespace, the preamble status token, and checkbox bracket
  contents — so `plan_hash` changes for an ordinary prose edit to `plan.md`.
  That is why the discriminator is a digest of the wave partition rather than
  `plan_hash` (source: `canonical_contract` in `_loop_guards.py`, probe
  2026-09-17)
- Technical: `cmd_schedule` rewrites `schedule_waves` and resets
  `current_wave_index` to zero while leaving `run_id` unchanged, so the run
  identifier cannot scope a record across a re-schedule (source: `cmd_schedule`
  in `loop-cohort.py`, probe 2026-09-17)
- Technical: the contract-amendment path computes newly-completed tasks as those
  in the waves before the current index, so an amendment raised at wave index
  zero with no prior completions re-schedules the identical task graph and
  produces an identical partition — and therefore an identical digest. The
  digest alone cannot scope a record across an amendment, which is why the
  amendment path clears the container (source: `apply_contract_amendment` and
  `schedule_unfinished_plan` in `loop-cohort.py`, probe 2026-09-17)
- Technical: `non_negative_int` in the guard layer validates a field as a
  non-negative integer, rejects `bool` explicitly, and returns a reason string;
  `check_wave` and `check_plan_current` already consume it for this kind of
  field (source: `non_negative_int` in `_loop_guards.py`, probe 2026-09-17)
- Technical: five edges enter `CODE-IMPLEMENTATION` — `plan-locked`,
  `wave-passed`, `gates-failed`, `findings-remain`, and `blocker-applied` — and
  only `wave-passed` is paired with a cohort wave advance, so a repair round
  re-exits through this guard with the wave pointer unmoved (source: the
  transition table in `loop-engine.py`, probe 2026-09-17)
- Technical: `loop-cohort wave advance` is authorized by `--expect-run-id`
  alone. As shipped it is not coupled to this guard, which is why a record
  stays writable for an already-left wave; § Leaving a wave couples the
  advancing branch, so the uncoupled reading describes the pre-change code and
  is not the target state (source: `cmd_wave_advance` in `loop-cohort.py` and
  `check_wave` in `_loop_guards.py`, probe 2026-09-17)
- Technical: `cmd_status` refuses when `schema_version` is not the supported
  value and prints a flat mapping in both its default and `--json` forms
  (source: `cmd_status` in `loop-cohort.py`, probe 2026-09-17)
- Technical: `cmd_init` refuses an existing `state.json` and populates a new one
  from the bundled template alone, and `cmd_reset` unlinks the file (source:
  `cmd_init` and `cmd_reset` in `loop-cohort.py`, probe 2026-09-17)
- Technical: `check_phase` is wrapped by `@contained`, so an escaping exception
  becomes a refusal rather than a crash — the right direction, but with an
  opaque message, which is why malformed state gets named rows instead (source:
  `contained` and `check_phase` in `_loop_guards.py`, probe 2026-09-17)
- Technical: the receipt path specified at
  `notes/implementer-<task-id>-<iteration>.md` is written by `worktree record`,
  a verb the Phase-1 usage block lists as disabled, so the sequential path has
  no existing receipt writer to extend (source: the `worktree` entry in
  `loop-cohort.py`'s usage block, and `references/supervisor-mode.md` § step 3,
  probe 2026-09-17)
- Technical: ADR-0061 remains Frozen on Option A because a `pending_transition`
  schema is still absent (source:
  `docs/adr/0061-loop-infrastructure-phase-1.md` § Context, probe 2026-09-17)
- Technical: a dispatched `implementer` subagent ships with `Read` and `Bash`
  and is instructed to read the spec directory, which is where `run_id` sits as
  a plaintext key (source: `packs/core/.apm/agents/implementer.md` frontmatter
  and body, with `assets/state.json`, probe 2026-09-17)
- Process: executing tasks in the controller when no `implementer` subagent is
  installed is legitimate, so an absent record is sometimes correct and the
  guard must accept a recorded decline (source: `references/supervisor-mode.md`
  § Single-agent fallback, probe 2026-09-17)
- Product: the dispatch-rate measurement that motivated this change is recorded
  in `notes/verification-ledger.md`, which is its single home per the Durable
  Outputs table; it is not restated here, so the two cannot drift.
- Product: records are per-task rather than per-wave because the wave's task
  list is the denominator the guard needs, and a wave-granular record would let
  one entry discharge a whole wave — the gap this spec closes (source: design
  decision, this spec)
- Product: the absent-container notice is printed by `check --phase wave-exit`
  on stdout and `loop-cohort status` reports enforcement state. The owner chose
  `status` over widening scope to the engine's shared guard adapter; the stdout
  notice was added once `cmd_check`'s passing-message channel was confirmed, and
  the pre-exit check in GATES is what gives it a caller (source: user
  confirmation 2026-09-17, with the `cmd_check` probe above)
