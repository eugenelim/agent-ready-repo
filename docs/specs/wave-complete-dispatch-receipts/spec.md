# Spec: wave-complete dispatch receipts

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md) (Option A: `loop-engine` owns read-only guard enforcement, `loop-cohort` owns skill-invoked mutations); `loop-infrastructure-phase-1` (Shipped and frozen — its plan declares `check --phase implement` a Phase-1 compatibility stub, which this spec replaces); `work-loop-in-process-guards` (Shipped and frozen — it owns the in-process guard surface this spec extends)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

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

What this does not do is prove that dispatch happened. A receipt is an
assertion by whoever wrote it, and one decline code records a human instruction
with no testable precondition, so the exit raises the cost of skipping dispatch
and leaves a durable record of the choice; it does not make skipping impossible.
The plan's Risks section carries the consequences and names who can write a
record.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable — the loop gains a refusal an adopter can hit | `docs/product/changelog.md`, `[core]` entry with a `Highlights` block | work-loop release step | Topmost `## [core][<version>]` entry agreeing with both pack manifests | Entry names the new refusal and the declines that avoid it, at the strength the Objective states |
| Maintainer procedure | Applicable — the controller gains a required call per plan task | `packs/core/.apm/skills/work-loop/SKILL.md` § Step 2. EXECUTE and `references/supervisor-mode.md` § Single-agent fallback | this spec | Both named sections carry the receipt call and both decline reason codes | Projections regenerated and byte-identical across the three copies |
| Interface compatibility | Applicable — durable cohort state gains a field read by old and new versions | `packs/core/.apm/skills/work-loop/references/state-schema.md` | this spec | The field documented with its absence rule | State-schema reference names the field and what an absent field means |
| Decision rationale | Not applicable — ADR-0061 already decides the Option A split this change sits inside; no new decision is taken | — | — | — | — |
| Reusable learning | Applicable — the measurement that motivated this change | `docs/specs/wave-complete-dispatch-receipts/notes/verification-ledger.md` | this spec | Recorded dispatch-rate measurement and the mutation proof | Ledger records both |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the receipt write an explicit `loop-cohort` mutation and the wave-exit
  check a read-only `loop-engine`-consulted guard, per the ADR-0061 Option A
  split.
- Authorize the receipt write exactly as every other cohort mutation is
  authorized: by a matching `--expect-run-id`. Treat that as what it is — a
  staleness and run-pairing check that excludes a caller from another run. It is
  not an authenticator, and it does not establish which party called. Any actor
  that can read the spec directory can read `run_id` from `state.json` and
  invoke the verb, and that includes a dispatched `implementer` subagent, which
  ships with filesystem and shell access. The receipt therefore records an
  assertion, not a proof of who made it, and nothing scopes a record to the task
  its writer was dispatched for.
- Let the guard pass silently whenever it cannot account for a wave for a reason
  that is not the controller's fault — no schedule persisted, or cohort state
  written before receipts existed — so a run already in flight when this ships
  still completes.
- Name every task the guard could not account for in its refusal, not a count.

### Ask first

- Adding a decline reason code. The accepted set is closed, and a third code
  changes what the exit will excuse.
- Making the guard enforce anything beyond per-task accountability — the
  content of a report, or the identity of the party that recorded a receipt.
  Establishing caller identity is a new trust mechanism and needs sign-off.
- Changing `loop-engine.py`'s guard adapter. A passing `GuardResult` cannot
  carry a reason, so any design that needs the engine to surface a message from
  a guard that passed is a change to a contract every guard shares.
- Any change to the `wave-passed` guard or the review-phase guards. This spec
  touches the `wave-complete` exit from code implementation only.

### Never do

- Give the receipt durable side-effect semantics: no `pending_transition`
  record, no idempotency key, no crash-safe replay. Those are ADR-0061 Option B,
  they need a schema that does not exist, and building them here would require
  superseding a Frozen ADR.
- Let the read-only guard write, migrate, or repair cohort state — including
  creating an empty receipts container on first contact.
- Regenerate or hand-author a row in the golden CLI stream fixture. It is
  generated once, before the guard extraction, and deliberately never
  regenerated; a hand-written capture is a comparison value this change supplies
  for itself.
- Accept a receipt for a task the named wave does not contain, or for a wave
  index outside the current schedule.

## Testing Strategy

- **The mutation verb's accept and refuse behaviour: TDD.** A receipt write, a
  decline write, a rejected reason code, a rejected unknown task, a rejected
  wave index, a rejected run identifier, and a replaced duplicate are all
  compressible invariants over pure state, exercised by unit tests against the
  loaded module.
- **The guard's verdict: TDD.** Whether `check --phase implement` passes or
  refuses is a pure function of cohort state, tested at the guard boundary for
  the accounted, unaccounted, declined, unscheduled, absent-container, and
  out-of-range cases.
- **The guard reaching the live transition: goal-based check.** `Done when:` the
  `wave-complete` transition out of `CODE-IMPLEMENTATION` exits non-zero on a
  wave with an unaccounted task. A guard that refuses only when called directly
  would leave the real exit open, so this is verified through the transition
  rather than the guard.
- **The container-to-guard coupling: TDD.** The key `schedule` writes and the
  key the guard reads must be proved to be the same key by a test that reddens
  when they diverge. Asserting that the container is present cannot do that —
  a template writing one name while the guard reads another satisfies it and
  ships the control permanently inert.
- **The controller-facing surface: goal-based check.** `Done when:` a check
  scoped to each named section — not a whole-file grep — finds the literal call
  and both decline reason codes, and the three projected copies of each edited
  file are byte-identical.
- **Mutation proof: manual QA.** Each guard and verb clause is removed in turn,
  the suite is re-run, and the observed red is recorded. A clause whose removal
  leaves the suite green is not yet verified, whatever its tests are named.

## Acceptance Criteria

- [ ] Recording a receipt for a task in the named wave, with a matching run
      identifier, exits zero and leaves that task accounted for.
- [ ] Recording a decline for a task in the named wave, with a matching run
      identifier, exits zero and leaves that task accounted for.
- [ ] Requesting a receipt and a decline for the same task in one invocation
      exits non-zero and writes nothing.
- [ ] A decline reason is accepted only from the closed set
      `no-implementer-installed` and `human-directed`; any other value exits
      non-zero, names that accepted set, and writes nothing.
- [ ] Recording against a task the named wave does not contain exits non-zero,
      names the tasks that wave does contain, and writes nothing.
- [ ] Recording against a wave index outside the range of the current
      schedule's waves exits non-zero and writes nothing.
- [ ] Recording with a run identifier that does not match cohort state exits
      non-zero and writes nothing.
- [ ] A receipt or decline may name any wave index within the current schedule,
      including one the run has already advanced past.
- [ ] Every written record carries the run identifier and the plan hash that
      cohort state held when it was written.
- [ ] `check --phase implement` counts a record as accounting for its task only
      when both that record's run identifier and its plan hash equal cohort
      state's current values.
- [ ] Recording the same wave index and task identifier twice replaces the
      earlier record, exits zero, and leaves exactly one record for that pair.
- [ ] `check --phase implement` exits zero when every task in the current wave
      is accounted for.
- [ ] `check --phase implement` exits non-zero when at least one task in the
      current wave is not accounted for, and names every such task on stderr.
- [ ] `check --phase implement` exits zero when `schedule_waves` is empty.
- [ ] `check --phase implement` exits zero when cohort state carries no receipts
      container.
- [ ] `check --phase implement` exits non-zero when `current_wave_index` is not
      a valid index into `schedule_waves`.
- [ ] `check --phase implement` prints nothing to stdout and nothing to stderr
      whenever it exits zero.
- [ ] The bytes of `state.json` captured before a `check --phase implement` run
      equal its bytes after that run, on the absent-container path, the
      accounted-for passing path, and the refusing path.
- [ ] The `wave-complete` transition out of `CODE-IMPLEMENTATION` is refused
      when that guard refuses.
- [ ] `loop-cohort schedule` leaves the receipts container present in cohort
      state.
- [ ] A test reddens when the container key written by `loop-cohort schedule`
      and the container key read by `check --phase implement` differ.
- [ ] `loop-cohort status` reports that dispatch receipts are not enforced when
      cohort state carries no receipts container, and does not report that when
      the container is present.
- [ ] `SKILL.md` § Step 2. EXECUTE names the literal
      `loop-cohort dispatch-receipt` as required once per plan task.
- [ ] `references/supervisor-mode.md` § Single-agent fallback names
      `no-implementer-installed`, and names `human-directed` as recording a
      human instruction with no testable precondition.
- [ ] `references/state-schema.md` names the receipts container and states that
      an absent container means the guard does not enforce.
- [ ] A mutation record names each removed guard and verb clause, the test that
      turned red, and the observed failure, with no clause whose removal left
      the suite green.

## Follow-ons

- eugenelim: `workspace.toml` `[backlog].open` entry on
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` — refuse or
  disambiguate a duplicate plan task heading, which currently drops the earlier
  section's declared edges. Registered 2026-09-17; independent of this spec.
- eugenelim: pair leaving a wave index with that wave being accounted for.
  `loop-cohort wave advance` is authorized by `--expect-run-id` alone and is not
  coupled to `check --phase implement`, so a controller that advances before
  firing `wave-complete` moves the guard's denominator and the skipped wave is
  never checked. This spec keeps a receipt recordable for an already-advanced
  wave so the record is at least not lost, but closing the skip itself changes
  `wave advance`'s refusal set and owes its own specification. To be registered
  through `work-intake` on approval of this spec.
- eugenelim: retirement of the absent-container pass. Establishing the container
  at `schedule` bounds the class to runs scheduled before the upgrade rather
  than leaving it open-ended, but nothing distinguishes such a run from one
  whose container was removed. Its trigger is the arrival of a provenance
  mechanism — the `pending_transition` schema ADR-0061 names as the Option B
  prerequisite is the candidate. To be registered through `work-intake` on
  approval of this spec.

## Assumptions

- Technical: the guard on the `wave-complete` transition out of
  `CODE-IMPLEMENTATION` is `check --phase implement`, and that phase is an
  explicit Phase-1 compatibility stub returning ok for any readable state
  (source: `check_phase` in
  `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`, its `implement`
  branch; and the `("code", "wave-complete")` entry in `loop-engine.py`'s guard
  table, probe 2026-09-17)
- Technical: a passing `GuardResult` cannot carry a reason — its
  `__post_init__` raises `ValueError` unless `ok` is true exactly when `reason`
  is None — and `loop-engine`'s `_guard_reason` returns None for any passing
  result. So no guard that passes can describe itself to the engine, which is
  why the absent-container disclosure lives on `loop-cohort status` (source:
  `GuardResult` in `_loop_guards.py` and `_guard_reason` in `loop-engine.py`,
  probe 2026-09-17)
- Technical: the golden CLI stream row that replays `check --phase implement`
  supplies `schedule_waves: []`, so it is an *unscheduled* state rather than a
  state with an empty wave. A guard that passes silently when no schedule is
  persisted preserves that row's captured `returncode 0, stdout "", stderr ""`
  without an `after`, a `change_reason`, or an edit to the fixture's state
  builder (source: the `check/implement-ok` row in
  `packs/core/tests/skills/work-loop/fixtures/golden_cli_streams.json` and the
  `_state()` builder in `test_loop_guards_parity.py`, probe 2026-09-17)
- Technical: the golden fixture is generated once before the guard extraction
  and deliberately never regenerated, so no row may be added or rewritten by
  this change (source: the fixture-loading failure message in
  `packs/core/tests/skills/work-loop/test_golden_fixtures.py`, probe
  2026-09-17)
- Technical: `loop-cohort schedule` rewrites `schedule_waves`, resets
  `current_wave_index` to zero, and persists `plan_hash`, while leaving `run_id`
  unchanged. A contract amendment re-schedules under the same run, so the run
  identifier alone cannot scope a record to a schedule — which is why each
  record carries the plan hash (source: `cmd_schedule` in `loop-cohort.py` and
  `references/delivery-contract-lifecycle.md` § amendment, probe 2026-09-17)
- Technical: `loop-cohort wave advance` is authorized by `--expect-run-id`
  alone and is not coupled to `check --phase implement`, so advancing early
  moves the guard's denominator; that is why a receipt stays recordable for an
  already-advanced wave, and why closing the skip is a follow-on (source:
  `cmd_wave_advance` in `loop-cohort.py` and `check_wave` in `_loop_guards.py`,
  probe 2026-09-17)
- Technical: `cmd_init` refuses an existing `state.json` and populates a new one
  from the bundled template alone, and `cmd_reset` unlinks the file (source:
  `cmd_init` and `cmd_reset` in `loop-cohort.py`, probe 2026-09-17)
- Technical: the guard already reads cohort `state.json` through
  `_state_or_reason`, so no new file or read path is introduced (source:
  `_state_or_reason` in `_loop_guards.py`, probe 2026-09-17)
- Technical: the receipt path specified at
  `notes/implementer-<task-id>-<iteration>.md` is written by `worktree record`,
  a verb the Phase-1 usage block lists as disabled, so the sequential path has
  no existing receipt writer to extend (source: the `worktree` entry in
  `loop-cohort.py`'s usage block, and `references/supervisor-mode.md` § step 3,
  probe 2026-09-17)
- Technical: ADR-0061 remains Frozen on Option A because a `pending_transition`
  schema is still absent, so durable side-effect semantics are out of reach
  (source: `docs/adr/0061-loop-infrastructure-phase-1.md` § Context, probe
  2026-09-17)
- Technical: a dispatched `implementer` subagent ships with `Read` and `Bash`
  and is instructed to read the spec directory, which is where `run_id` sits as
  a plaintext key — so it can satisfy `--expect-run-id` and call the verb
  (source: `packs/core/.apm/agents/implementer.md` frontmatter and body, with
  `assets/state.json`, probe 2026-09-17)
- Process: executing tasks in the controller when no `implementer` subagent is
  installed is legitimate, so an absent receipt is sometimes correct and the
  guard must accept a recorded decline (source: `references/supervisor-mode.md`
  § Single-agent fallback, probe 2026-09-17)
- Product: the 2026-09-15 stdout reminder moved dispatch off zero but did not
  make it binding — of 11 sessions since that date that ran
  `loop-cohort schedule` against a spec directory, 3 dispatched an `implementer`
  and 8 did not, and the 8 performed 100 controller file edits between them. The
  pre-change baseline was 36 sessions, 0 dispatches, 1,285 edits (source: scan of
  783 transcripts under `~/.claude/projects/*agent-ready-repo*`, probe
  2026-09-17)
- Product: receipts are per-task rather than per-wave because the wave's task
  list is the denominator the guard needs, and a wave-granular receipt would let
  one record discharge a whole wave — the gap this spec closes (source: design
  decision, this spec)
- Product: the absent-container disclosure lives on `loop-cohort status` rather
  than on the transition, because a passing guard cannot carry a message and
  widening scope to the engine's shared guard adapter was declined (source: user
  confirmation 2026-09-17)
