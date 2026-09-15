# Spec: loop-cohort unknown dependency refusal

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`loop-cohort schedule` reads each plan task's `Depends on:` field and builds the
dependency graph that decides wave order. When a task still to be scheduled
declares a dependency that names no task in the plan, the command stops, names
every offending `task -> dependency` pair it can see, and persists nothing. It
sees the IDs preceding the first parenthesis; the Assumptions record why.

This matters because the wave is the unit the gate run is keyed to. A dropped
edge merges two waves into one, and the per-wave GATES run merges with them.
When the intended order is not task-id order, work runs in the wrong order and
the gate that would have caught it never runs separately.

The other two ill-formed plan shapes keep the behaviour they already have. A
dependency cycle stops the run. A forward reference — a dependency authored
later in the file than the task declaring it — warns on stderr, is reordered so
the dependency runs first, and the run continues, because a forward reference is
a valid acyclic edge that executes correctly once reordered.

## Durable Outputs

- `loop-cohort schedule <spec-dir>` refuses a plan in which a task still to be
  scheduled declares an unknown local dependency, leaving `state.json` untouched.
- `schedule_unfinished_plan` refuses the same shape. It is the only wave builder,
  and the CLI path reaches it unconditionally before any state write, so the one
  refusal serves both entry points.
- The plan template and the supervisor-mode reference state the refusal, so an
  author reads the same contract the scheduler enforces.

## Boundaries

### Always do

- Refuse before any state write.
- Name every offending pair in one refusal, so one run fixes the whole plan.

### Ask first

- Any change to the forward-reference or cycle contract.
- Adding an opt-out flag or environment escape for the refusal.

### Never do

- Refuse a plan because a dependency names a task that is already **completed**.
  A completed task still counts as a satisfied dependency.
- Refuse a plan because of a declaration made by a task that is already
  completed. Its edges cannot affect a remaining wave, and its section is
  content-pinned, so the author cannot correct the line without an amendment.
- Treat a cross-spec dependency (`spec:<name>/T<n>` or `` `<name>` T<n> ``) as an
  unknown local dependency.
- Change the published signatures pinned by AC8.

## Testing Strategy

- **The unknown-dependency predicate: TDD.** A pure function over plan text with
  a compressible invariant — a plan and a set of tasks to scan in, a sorted pair
  list out. Unit tests cover each plan shape below.
- **The `schedule` refusal and its exit code: goal-based check, exercised by an
  integration test.** The behaviour only proves out across the CLI boundary: a
  subprocess run of the real script against a fixture spec dir, asserting the
  non-zero exit, the stderr text, and that `state.json` is unchanged.
- **The false-positive boundary: TDD.** Every legitimate dependency form — plain
  ID, letter suffix, in-plan range, both cross-spec markers, `none`, trailing
  parenthetical prose — is asserted not to trip the refusal, driven from the same
  fixture table as the positive cases.
- **The resolution set and the scan set: TDD.** Separate cases pin each. The
  resolution set is the whole plan, so a completed dependency counts as met. The
  scan set is the unfinished tasks, so a completed task's stale declaration is
  ignored. One case must isolate the resolution set by naming a dependency that
  is in the plan but outside the scan set — without it, an implementation that
  derives one set from the other passes every other case.
- **The documentation alignment: goal-based check.** A recursive scan whose
  absence result exits 0, plus the predicate and the cycle check run over the
  shipped plan template.
- **The mutation proof: goal-based check.** Deleting the new predicate's call
  site must turn the refusal tests red. Recorded per
  `references/mutation-proof.md`, in the verification ledger.

## Acceptance Criteria

- [ ] **AC1 — Unknown local ID is refused.** `loop-cohort schedule <spec-dir>` on
  a plan whose unfinished task declares `**Depends on:** T7` where the plan
  contains no `T7` exits non-zero, writes a stderr line naming the pair
  `T<n>->T7`, and does not write `state.json`.
- [ ] **AC2 — Every offending pair is named in one refusal.** A plan carrying two
  or more unknown dependencies names all of them, sorted by declaring task then
  dependency, in a single refusal. "All" is bounded by the parenthesis-truncation
  limit recorded in Assumptions: an ID after the first `(` is not a declared
  dependency for any caller, so it is not among the pairs.
- [ ] **AC3 — Forward reference is still warned, not refused.** A plan whose task
  depends on a task authored later in the file exits zero, warns on stderr, and
  schedules the dependency into an earlier wave than the task declaring it.
  `test_schedule_warns_but_reorders_on_forward_ref` continues to pass unmodified.
- [ ] **AC4 — Cycle is still refused.** A plan whose only fault is a dependency
  cycle exits non-zero with the existing cycle message, unchanged. When a plan
  carries both an unknown dependency and a cycle, the unknown-dependency refusal
  takes precedence, because it is the fault that makes the graph unreadable.
- [ ] **AC5 — Cross-spec dependencies do not trip the refusal.** A task declaring
  `spec:<name>/T7` or `` `<name>` T7 `` where the plan contains no `T7` schedules
  normally and exits zero.
- [ ] **AC6 — Every other legitimate dependency form is unaffected.** `none`,
  a plain in-plan ID, a letter-suffixed ID (`T1a`), an in-plan range (`T1-T3`),
  and trailing parenthetical prose all schedule exactly as they did before.
- [ ] **AC6a — A range spanning an absent ID is refused.** A task declaring
  `**Depends on:** T1-T3` in a plan containing `T1` and `T3` but no `T2` is
  refused naming the pair `T<n>->T2`. A range names every ID it spans, so an
  absent intermediate is an unknown dependency like any other. No plan in this
  repository uses this form today.
- [ ] **AC7 — A dependency on a completed task is met, not unknown.** In an
  amended plan, an unfinished task depending on a **completed** task schedules
  successfully. The IDs a dependency is resolved against are every task in the
  plan file, not the unfinished remainder.
- [ ] **AC7a — A completed task's own declaration is out of scope.** In an
  amended plan, a **completed** task whose `Depends on:` names an absent ID does
  not refuse the run; the remaining tasks schedule normally. Only the
  declarations of tasks still to be scheduled are examined.
- [ ] **AC8 — Published signatures are unchanged.** This is the canonical
  statement of both pins: `parse_plan` returns exactly `(ordered, deps)`, and
  `parse_depends_on` returns exactly `(local, cross)` and still filters to
  in-plan IDs. Neither raises.
- [ ] **AC9 — Mutation proof recorded.** The refusal has exactly one call site:
  inside `schedule_unfinished_plan`, immediately before its `detect_cycles` call.
  Removing that single call turns named tests red on **both** the CLI path and the
  amendment path; the command, the test ids, and the observed failures are
  recorded in `notes/verification-ledger.md`. A second, redundant call site is
  forbidden: it would make this proof pass for a deleted guard.
- [ ] **AC10 — The documented contract matches the code.** A recursive scan of
  `packs/core/` for the retired claim that an absent dependency is dropped
  without a diagnostic finds no match and exits 0, and `references/supervisor-mode.md`,
  the plan template's `Depends on:` grammar block, and
  `seeds/docs/CONVENTIONS.md`'s supervisor-mode paragraph all state the refusal.
  The conventions paragraph enumerates what `schedule` does with an ill-formed
  plan and this change makes that list three members, so it ships stale unless it
  is updated; the seed is the owning source and `docs/CONVENTIONS.md` is projected
  from it.
- [ ] **AC11 — The shipped plan template schedules clean.** Run over
  `packs/core/.apm/skills/new-spec/assets/plan.md`, the unknown-dependency
  predicate returns no pairs **and** the cycle check returns no task IDs. The
  `Depends on:` placeholder reads `<none | comma-separated prior task IDs>`,
  which names no task ID at all and so can produce neither an unknown dependency
  nor a self-edge.
- [ ] **AC12 — Release surface agrees.** `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the same new patch version, and
  `docs/product/changelog.md` carries a `## [core][<version>] — <date>` section
  at the top level directly beneath `## [Unreleased]`, never nested inside it.
  The entry carries a `### Highlights` subsection, because this change alters what
  a pack consumer can do: a plan that schedules today can start refusing.
- [ ] **AC13 — Projections are byte-identical.** After `make build-self`, each
  edited `.apm/` file and its regenerated adapter copies under `.claude/` and
  `.agents/` match byte-for-byte.
- [ ] **AC14 — The eval harness reflects the changed behaviour.** The `work-loop`
  skill's `evals/evals.json` contains an entry with
  `"id": "schedule-refuses-unknown-dependency"` whose assertions require the
  answer to say `schedule` refuses rather than warns, and to distinguish the
  forward-reference case. `agentbundle catalogue lint --root . --deep` and
  `agentbundle catalogue verify --root .` both pass.

## Follow-ons

None. The forward-reference and cycle contracts are settled and out of scope.

## Assumptions

- **Refusing is safe for this repository.** Measured before authoring: across 344
  plan-shaped `.md` files under `docs/`, `docs/specs/`, and `packs/`, exactly one
  carried an unknown local dependency — the `new-spec` plan **template**, whose
  placeholder read `**Depends on:** <none | T0, ...>`. No real plan changes
  behaviour. Re-measured across the 17 `.py` files carrying plan-shaped string
  literals, parsed from the syntax tree rather than the raw file text: exactly one
  file carries unknown local IDs — `test_loop_cohort_schedule.py:134-138`, whose
  forward-reference fixture declares `T13->T2` and `T15->T4` in a plan holding only
  `T13`, `T14`, `T15`. That fixture is fed to `parse_plan` and
  `detect_forward_refs` only, never to a refusing path, so it is unaffected. An
  earlier count of zero came from a probe that anchored its heading pattern to the
  start of a line and so could not see an indented, quote-prefixed fixture; it
  carried no control case to reveal that. No plan anywhere used a range spanning an
  absent intermediate ID.
- **Adopter plans are unmeasurable.** A plan outside this repository carrying a
  stale ID works today and starts failing at PLAN. The owner accepted this
  breaking change explicitly and declined an opt-out flag.
- **After cross-spec markers are stripped, an unresolved `T\d+[a-z]?` is
  unambiguously a local ID.** Both cross-spec forms are substituted out of the
  working string before local IDs are extracted.
- **Accepted limit: the refusal does not reach past the first parenthesis.**
  `parse_depends_on` truncates the field at the first `(`, a documented behaviour
  the template describes as "parenthetical prose after the IDs is ignored". So
  `**Depends on:** T1 (a), T7` still drops `T7` silently — verified: the field
  parses to `({'T1'}, [])`. Extending the refusal past the truncation would change
  what counts as a declared dependency for every caller, which is a wider change
  than this defect warrants.
