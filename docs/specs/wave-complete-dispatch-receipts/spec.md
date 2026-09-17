# Spec: wave-complete dispatch receipts

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
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
semantics it has today, because the pre-PR hook runs that phase for every spec
directory on every push with no state-machine gate; moving the accounting into
it would turn a wave-exit guard into a repository-wide push gate for this
repository and for every adopter of the packaged hook.

What this does not do is prove that dispatch happened, and four limits are
deliberate rather than overlooked. A record is an assertion by whoever wrote it,
and any actor that can read `run_id` can write one, including a dispatched
`implementer`. One decline code records a human instruction with no testable
precondition. A repair round re-enters implementation without moving the wave
pointer, so the first pass's records satisfy its exit too. And the pass on an
absent receipts container cannot be told apart from a pass on a container that
was deleted, so removing that one key disables enforcement for the run and
leaves no record of having done so. The exit raises the cost of skipping
dispatch and leaves a durable per-task record of the choice; it does not make
skipping impossible. The plan's Risks section carries each limit and names who
can write a record.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable — the loop gains a refusal an adopter can hit | `docs/product/changelog.md`, `[core]` entry with a `Highlights` block | work-loop release step | Topmost `## [core][<version>]` entry agreeing with both pack manifests | Entry names the new refusal and the declines that avoid it, at the strength the Objective states |
| Maintainer procedure | Applicable — the controller gains a required call per plan task and a required check before the exit | `packs/core/.apm/skills/work-loop/SKILL.md` § Step 2. EXECUTE and § Step 3. GATES, and `references/supervisor-mode.md` § Single-agent fallback | this spec | Section-scoped checks find the record call, its authorship, the pre-exit check, and both decline reason codes | Projections regenerated and byte-identical across the three copies |
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
- Give every guard verdict a precondition that no other verdict's precondition
  can also satisfy, and make the verdicts jointly cover every cohort state. The
  verdict table below is the contract; branch order in the implementation is
  then an optimisation rather than the thing that decides behaviour.
- Reuse the guard layer's existing non-negative-integer validation for
  `current_wave_index` rather than introducing a second integer predicate. The
  existing one rejects `bool` and owns its message shape, and two predicates on
  one field is how they drift.
- Let the guard pass whenever it cannot account for a wave for a reason that is
  not the controller's fault — no schedule persisted, or cohort state written
  before receipts existed — so a run already in flight when this ships still
  completes.
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
- Coupling `loop-cohort wave advance` to this guard, or scoping a record to a
  repair round. Both change an existing verb's refusal set.
- Any change to the `wave-passed` guard or the review-phase guards.

### Never do

- Change what `check --phase implement` returns for any state. The pre-PR hook
  runs that phase for every spec directory on every push with no state-machine
  gate, so a refusal there is a push gate, not a wave gate.
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
- Remove a record by any path other than the two this spec names: a `schedule`
  run whose partition differs from the one a record was written under, and a
  contract amendment.
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

- [ ] A record accounts for its task when it is held under the digest of the
      current wave partition, and a decline record does so only when its reason
      is a member of the closed set `no-implementer-installed` and
      `human-directed`.
- [ ] A record held under any other partition digest accounts for no task.
- [ ] Editing `plan.md` in a way that leaves `schedule_waves` unchanged, then
      re-scheduling, leaves every existing record still accounting for its task.

### The record lifecycle

- [ ] `loop-cohort init` leaves the receipts container present in cohort state.
- [ ] `loop-cohort schedule` leaves the receipts container present in cohort
      state.
- [ ] A `loop-cohort schedule` run whose resulting partition equals the one a
      record was written under leaves that record present and unchanged.
- [ ] A `loop-cohort schedule` run whose resulting partition differs from the
      one a record was written under leaves no record under the superseded
      digest.
- [ ] A contract amendment leaves the receipts container empty, so no record
      written before the amendment accounts for a task after it — including when
      the amendment is raised at wave index zero with no completed tasks, where
      the re-scheduled partition is identical and its digest therefore unchanged.

### The `dispatch-receipt` verb

- [ ] Recording a receipt for a task in the named wave, with a matching run
      identifier, exits zero and leaves that task accounted for.
- [ ] Recording a decline for a task in the named wave, with a matching run
      identifier and a reason from the closed set, exits zero and leaves that
      task accounted for.
- [ ] Recording against the current wave index, and against any lower wave index
      the current schedule contains, exits zero.
- [ ] Recording against a wave index above the current wave index exits
      non-zero, so a wave the run has not yet reached cannot be recorded
      against.
- [ ] Recording against a wave index that is not a non-negative integer, by the
      guard layer's existing validation, exits non-zero.
- [ ] Recording when the current partition is empty, or when the current wave
      index is not a valid index into it, exits non-zero and names the unusable
      partition rather than raising.
- [ ] Requesting a receipt and a decline in one invocation exits non-zero.
- [ ] A decline reason outside the closed set exits non-zero and names the
      accepted set.
- [ ] A task identifier the named wave does not contain exits non-zero and names
      the task identifiers that wave does contain.
- [ ] A run identifier that does not match cohort state exits non-zero.
- [ ] On every invocation of the verb that exits non-zero, for any reason,
      `state.json` is byte-identical to its content before the invocation.
- [ ] Recording the same partition digest, wave index, and task identifier twice
      exits zero both times and leaves exactly one record for that triple.

### The `check --phase wave-exit` verdict

Exactly one row applies to any cohort state, and the rows together cover every
cohort state. A state is **well-formed at the top level** when `state.json`
parses, `schedule_waves` read with its default is a list, and the receipts
container is either absent or a mapping. A **current wave** is well-formed when
it is a list whose every element is a string. A pointer is **valid** when
`current_wave_index` is a non-negative integer by the guard layer's existing
validation, which rejects `bool`, and is less than the number of waves in the
partition. Naming the shared preconditions
once is deliberate: an earlier draft asserted that each row negated the rows
above it without writing those negations, and two rows then covered the same
state with opposite verdicts.

- [ ] `state.json` is missing or cannot be parsed: exits non-zero and names the
      state defect on stderr.
- [ ] `state.json` parses but the state is not well-formed at the top level:
      exits non-zero and names the malformed field on stderr, rather than
      surfacing an exception type.
- [ ] The state is well-formed at the top level and the partition is empty:
      exits zero and prints nothing to stdout or stderr.
- [ ] The state is well-formed at the top level, the partition is non-empty, and
      the receipts container is absent: exits zero and names the absent
      container on stdout.
- [ ] The state is well-formed at the top level, the partition is non-empty, the
      container is present, and the pointer is not valid: exits non-zero and
      names the invalid pointer on stderr.
- [ ] The state is well-formed at the top level, the partition is non-empty, the
      container is present, the pointer is valid, and the current wave is not
      well-formed: exits non-zero and names the malformed wave on stderr.
- [ ] The state is well-formed at the top level, the partition is non-empty, the
      container is present, the pointer is valid, the current wave is
      well-formed, and every task in the current wave is accounted for: exits
      zero and prints nothing to stdout or stderr.
- [ ] The state is well-formed at the top level, the partition is non-empty, the
      container is present, the pointer is valid, the current wave is
      well-formed, and at least one task in the current wave is not accounted
      for: exits non-zero and names every such task, and no accounted task, on
      stderr.
- [ ] No cohort state satisfies the preconditions of two of the eight rows
      above.
- [ ] No cohort state satisfies the preconditions of none of the eight rows
      above.
- [ ] Each of the eight rows above is satisfied by some cohort state.
- [ ] The states the three criteria above are checked over are constructed by
      varying the type and value of `schedule_waves`, of its element at the
      pointer, of the receipts container, and of `current_wave_index` — not by
      instantiating one example per row, which cannot exhibit a gap.
- [ ] For every row above whose state has a `state.json`, that file is
      byte-identical before and after a `check --phase wave-exit` invocation.
- [ ] The `wave-complete` transition out of `CODE-IMPLEMENTATION` is refused
      when the guard refuses.
- [ ] `check --phase implement` returns the same exit code and the same streams
      as it does before this change, for the golden parity replay of that phase
      and for one state per row of the table above — the states the new rows
      distinguish being the only ones whose verdict could have moved.

### Reporting and reaching the check

- [ ] `SKILL.md` § Step 3. GATES requires `loop-cohort check --phase wave-exit`
      to be run before the `wave-complete` transition is fired, which is what
      gives the absent-container notice a caller — the engine's guard adapter
      discards a passing guard's text, so the transition alone cannot surface
      it.
- [ ] `loop-cohort status` reports whether dispatch receipts are enforced for
      the run, in both its default output and its `--json` output.
- [ ] A record written by `loop-cohort dispatch-receipt` is counted by
      `check --phase wave-exit` in the same run, with no intervening
      re-schedule.

### Controller-facing surfaces

- [ ] `SKILL.md` § Step 2. EXECUTE names the literal
      `loop-cohort dispatch-receipt` as required once per plan task.
- [ ] `SKILL.md` § Step 2. EXECUTE states that the controller records it and
      that an `implementer` subagent does not record its own.
- [ ] `references/supervisor-mode.md` § Single-agent fallback names
      `no-implementer-installed` as the decline the controller records when no
      `implementer` subagent is installed.
- [ ] `references/supervisor-mode.md` § Single-agent fallback names
      `human-directed` as recording a human instruction with no testable
      precondition.
- [ ] `references/state-schema.md` names the receipts container and states that
      an absent container means the guard does not enforce.

### Proof

- [ ] A mutation record names each removed guard and verb clause, the test that
      turned red, and the observed failure, with no clause whose removal left
      the suite green.

## Follow-ons

- eugenelim: `workspace.toml` `[backlog].open`, entry on
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` — refuse or
  disambiguate a duplicate plan task heading. Registered 2026-09-17; independent
  of this spec.
- eugenelim: `workspace.toml` `[backlog].open`, entry keyed
  `wave-advance-uncoupled-from-the-exit-check` — pair leaving a wave index with
  that wave being accounted for. `loop-cohort wave advance` is authorized by
  `--expect-run-id` alone and is not coupled to this guard, so a controller that
  advances before firing `wave-complete` takes the skipped wave out of the
  guard's view. This spec keeps a record writable for an already-left wave so
  the record is not also lost.
- eugenelim: `workspace.toml` `[backlog].open`, entry keyed
  `repair-rounds-reuse-the-first-passes-receipts` — require a repair round to
  carry its own assertion. `gates-failed`, `findings-remain`, and
  `blocker-applied` all re-enter `CODE-IMPLEMENTATION` without moving
  `current_wave_index`. Scoping a record to a round needs a counter that
  advances on all three edges; `implementation_retry_count` advances on one, so
  building on it would look like a control without being one.
- eugenelim: `workspace.toml` `[backlog].open`, entry keyed
  `an-enforcement-off-wave-exit-leaves-no-durable-trace` — a wave exit that
  passes with no container, or with every task declined, leaves no record an
  after-the-fact reader can find, because the read-only guard cannot write and a
  durable side effect on a transition is ADR-0061 Option B. `loop-cohort status`
  also refuses when `schema_version` is unsupported, so for the oldest state
  class the guard tolerates, only the stdout notice remains.

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
  failure. So a refusal added to the `implement` phase becomes a push gate for
  every spec directory in the repository. This is the reason for a separate
  phase, and it is a caller no grep for `--phase implement` finds, because the
  phase name reaches the argument list through a loop variable (source:
  `tools/hooks/pre-pr.py`, probe 2026-09-17)
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
- Technical: `loop-cohort wave advance` is authorized by `--expect-run-id` alone
  and is not coupled to this guard, so advancing early moves the guard's
  denominator; that is why a record stays writable for an already-left wave
  (source: `cmd_wave_advance` in `loop-cohort.py` and `check_wave` in
  `_loop_guards.py`, probe 2026-09-17)
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
