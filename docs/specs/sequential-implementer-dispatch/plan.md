# Plan: sequential implementer dispatch

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0061 (Frozen; defers Phase 2 and
  `pending_transition`) and `docs/CONVENTIONS.md` § Supervisor mode.
  **An owner already exists for this responsibility:**
  `work-loop/references/supervisor-mode.md` states the sequential rule today and
  states the opposite of this spec's outcome, so this slice amends an existing
  owner rather than designing a new one. Analogous production implementations:
  `security-checklists` (the orchestrator inlines boundary modules into a
  reviewer's brief; the subagent never self-discovers) and `operational-safety`'s
  cloud-implementation-craft module, already inlined into this very agent's
  brief — those two fix the shape of the inlining work. Their construction path
  is `packs/core/tests/skills/work-loop/test_reference_routing.py`, whose
  hand-authored phrase tuples are the shape the pack tests here extend.
  Named uncertainty: `SKILL.md` and the guide are pinned by anchor assertions in
  `tests/roster/`; T0 records the extent and blocks every editing task.

> **Plan contract:** the implementation strategy. Allowed to change while Status
> is `Drafting` or `Executing`.

## Approach

Dispatch only. Extraction was split into U3 at slice confirmation, so nothing
moves out of `SKILL.md` here and no new reference file is created.

Three edits and two proofs. `SKILL.md` § EXECUTE gains a dispatch declaration,
and its existing § "Conditional-reference routing" table gains an inline verb —
that table is the right home because it is already a predicate→reference lookup,
and its rows give AC7 a closed set without inventing one. `implementer.md` gains
the two-root envelope, one commit owner per root, and the inlining clause. Four
surfaces that currently deny the outcome are amended.

**Why inlining rather than a path in the agent contract.** The agent can read a
path it is handed; what it cannot do is construct one, because the same
reference projects to `.claude/skills/work-loop/references/` on one adapter and
`.agents/skills/work-loop/references/` on the other. A single path in the
contract would be wrong on at least one host, and the repository's shipped
doctrine already forbids depth that depends on self-discovery.

**Riskiest part:** the contradiction sweep. Measured at HEAD, three members
assert the contradiction (`supervisor-mode.md`, the CONVENTIONS seed, and
`implementer.md`) and one is merely silent (the `evals.json` record). An
absence-only assertion passes over the silent one before any edit, which is why
AC8 and AC9 split the predicate by defect kind rather than by file.

## Constraints

- Every gate runs with `PYTHONPATH=packages/agentbundle:packages/credbroker`,
  or it resolves a stale site-packages install and fails falsely.
- Edit `packs/core/seeds/docs/CONVENTIONS.md`; `docs/CONVENTIONS.md` is its
  self-host projection and `make build-self` regenerates it.
- Pack tests stay anchored inside their owning pack. AC8's set reaches the seed,
  which is inside `packs/core`, but the roster is the safer home for a
  cross-file sweep; `Makefile` line 530 collects `tests/roster/` by directory,
  so no by-name CI wiring is required.
- The gate set for this slice: `lint-spec-status.py`, `lint-brief-coverage.py`,
  `workspace_status.py --root .`, `catalogue verify`, and
  `catalogue lint --root . --deep`. This is the list T5 means.
- The spec's `Never do` list binds this plan and is not restated here.

## T0 register — anchor couplings over the files this change edits

Recorded before any edit, per `work-loop/SKILL.md` § 8a. The § 8a patterns
(`hashlib`, `sha`, `==` on content, `len(lines)`, counted assertions) do not
catch ordering or prose-substring pins, so the sweep additionally matched
`_assert_order` and `.index(`.

| # | Edited file | Pinned by | Shape | Consequence |
| --- | --- | --- | --- | --- |
| A1 | `work-loop/SKILL.md` | `tests/roster/test_tdd_stub_lifecycle_contract.py` | `_assert_order` via `text.index()`; raises on a missing needle | the TDD lifecycle phrases must survive in order. U1 does not touch them; U3 must migrate the assertion |
| A2 | `work-loop/SKILL.md` | `tests/roster/test_wave4_durable_outputs_and_release.py` | `len(splitlines()) <= 1000`; `count("references/delivery-contract-lifecycle.md") >= 3` | the declaration must not displace any of those three pointers |
| A3 | `packs/core/seeds/docs/CONVENTIONS.md` | `tests/roster/test_shaping_review_documentation_contract.py` | root == seed byte equality | edit the seed, then `make build-self` |
| A4 | seed `CONVENTIONS.md` | `test_tdd_stub_lifecycle_contract.py` | phrase presence in the seed | the TDD phrases must survive the seed edit |
| A5 | the how-to guide | `tests/roster/test_spec_review_adjudication_documentation.py` | ordered `.index()` plus `0 <= gap <= 40` characters | T5 must not reorder that region or widen the gap |
| A6 | `work-loop/SKILL.md` | `packs/core/tests/skills/work-loop/test_non_gating_nits.py` | heading-uniqueness count | a new § heading must not collide |
| A7 | `supervisor-mode.md` | `packs/core/tests/skills/work-loop/test_reference_routing.py` | six plain `in` substring assertions | `parallel fan-out`, `those verbs exit non-zero` and `wave-complete` all sit inside the Phase 1 section T3 rewrites — preserve all six needles |
| A8 | `work-loop/SKILL.md` | same test | substring pin on `[Supervisor and fan-out procedure](references/supervisor-mode.md)` plus an anchor-resolution sweep | T1 must keep that link text intact and must not leave a dangling `](#...)` anchor |

| A9 | every edited `packs/core/.apm/**` source | `tests/roster/test_cognitive_load_repository_contract.py` | projection-equality between each canonical source and its self-host projection | re-run `FORCE=1 make build-self` after the **last** source edit, not once mid-change |
| A10 | `work-loop/SKILL.md` | `packs/core/tests/skills/work-loop/test_work_loop_repository_anchors.py` | plain substring controls | preserve the anchored phrases |
| A11 | the how-to guide and `evals/evals.json` | `tests/roster/test_tdd_stub_lifecycle_contract.py` | further substring pins beyond A1 | preserve them |
| A12 | `pack.toml`, `.claude-plugin/plugin.json`, `docs/product/changelog.md` | `test_wave4_durable_outputs_and_release.py`, `test_thirty_day_cooling_and_retirement.py`, `test_cognitive_load_repository_contract.py` | release-surface agreement | all three version surfaces must move together |

`implementer.md` and `evals/evals.json` carry no *content-hash* pin, but both
carry substring pins (A11). Two sweep lessons are recorded because both cost a
red run: the § 8a pattern list does not catch plain `in` substring assertions
(A7, A8, A10, A11), and `rg` skips dot-directories by default, which is how
`.claude-plugin/plugin.json` (A12) escaped the version sweep.

## Construction tests

**Pack-source**, under `packs/core/tests/skills/work-loop/` (collected by
directory at `Makefile` line 545). **Roster**, under `tests/roster/`, for AC8's
cross-file sweep. **Build**, under `packages/agentbundle/tests/build_pipeline/`,
projecting the real `packs/core` through both adapters — genuine rather than a
restatement of projection mechanics, because the adapters emit different agent
paths and the existing adapter suites use synthetic fixture packs that never
exercise the real `implementer`.

## Durable-output map

| Spec durable output | Task | Evidence handed to `close-work` |
| --- | --- | --- |
| Interface compatibility | T2, T4 | AC2-AC6 green; both adapters project the contract |
| Current architecture | T3 | AC8 and AC9 green over the enumerated set |
| User promise | T5 | AC10 green; guide retains the fan-out statement |
| Release history | T5 | Core pack changelog entry |

## Design (LLD)

### Design decisions

- The inline verb goes in `SKILL.md`'s existing conditional-reference table
  rather than a new file: the table already answers "which predicate, which
  reference", and its rows become AC7's closed set.
- The refusal and inlining clauses live in `implementer.md`, not the controller,
  because the agent contract is what both adapters project and what a directly
  invoked agent reads.

### State & control flow

Unchanged. `CODE-IMPLEMENTATION` has one entry edge (`plan-locked`) and four
re-entry edges; `wave-passed` carries the next wave's plan tasks and dispatches,
while `gates-failed`, `findings-remain` and `blocker-applied` carry repair and
do not.

### Failure, edge cases & resilience

Two failures this must not create. An implementer committing into a shared
checkout under a controller that believes it owns the index — prevented by one
commit owner per root, asserted over both roots. And craft silently vanishing
when execution moves into a subagent — prevented by the inline verb, degrading
through the shipped named-skip rule when a source pack is absent.

### Dependencies & integration

No new dependency, module boundary, or top-level directory.

## Tasks

### T0: the anchor register is complete and every editing task is bound by it

**Depends on:** none
**Verification mode:** goal-based check
**Artifact:** the register table above.

**Tests:**
- The register covers every file this change edits, not only a subset, and
  states a consequence for each coupling.

**Approach:** discharged; the table above is the output. Re-run the sweep if the
edit set grows.

**Done when:** every file in the edit set appears in the register or is recorded
as unpinned.

### T1: the controller declares sequential dispatch and what it inlines

**Depends on:** T0
**Verification mode:** goal-based check
**Artifact:** a new test file under `packs/core/tests/skills/work-loop/`.

**Tests:**
- Verify the declaration states all four elements. Verifies AC1.
- Verify every executor-craft row of the conditional-reference table states its
  inline disposition and its absent-source behaviour. Verifies AC7; the table's
  rows are the domain, so assert the row set too, not only each row.
- Verify A2's pointer count did not fall below three.
- **Mutation proof.** Invariant: the declaration is complete. Mutation: delete
  the once-per-plan-task element. Expected: AC1's assertion fails naming the
  missing element — a test that passes with three of four is not proof.

**Approach:** add the declaration to § EXECUTE and the inline verb to the
routing table. Do not touch the TDD, contract-grounding, verification-mode or
`notes/` statements; they are U3's and two of them are anchor-pinned.

**Done when:** the pack test passes and fails under the stated mutation.

### T2: the agent contract admits both roots, one commit owner each, craft inlined

**Depends on:** T0
**Verification mode:** goal-based check
**Artifact:** the same pack test file as T1.

**Tests:**
- Verify the two admitted roots, controller-supplied. Verifies AC3.
- Verify the frontmatter use condition no longer restricts the agent. AC2.
- Verify exactly one commit owner per root, asserting over both. AC4.
- Verify the inlining clause and the missing-field refusal. AC5, AC6.
- Sweep for worktree-presuming statements outside the operating envelope — the
  anti-patterns section and the `ready` status definition both carry one today —
  and verify the sweep is complete rather than sampling named lines.
- **Mutation proof.** Invariant: no root lacks a commit owner. Mutation: delete
  the primary-tree commit owner, leaving the denial in place. Expected: the test
  fails naming the ownerless root.

**Done when:** the pack test passes and fails under the stated mutation.

### T3: no surface denies the envelope, and the dispatch-bearing ones name it

**Depends on:** T0
**Verification mode:** goal-based check
**Artifact:** a new test file under `tests/roster/`.

**Tests:**
- Negative half over the enumerated set: no member states a single-agent default
  or requires a worktree. Verifies AC8.
- Positive half over the same set: each member describing how a
  `CODE-IMPLEMENTATION` task executes either names `implementer` dispatch or
  conditions single-agent execution on no installed matching subagent. Verifies
  AC9. This half is what catches the two members whose defect is omission rather
  than assertion — an absence-only predicate passes over them at HEAD.
- **Mutation proof, two mutations**, one per half.
  (a) Restore `single-agent, on every adapter` in `supervisor-mode.md`;
  expected: the negative half fails on that member.
  (b) Remove `implementer` from the `phase1-disabled-parallel-commands`
  `expected_output`; expected: the positive half fails on the omission member.
  This is the member the positive half exists for, so a mutation on any other
  member would not prove it. A mutation on the fallback condition is not used:
  after T3, `supervisor-mode.md` satisfies the positive half by naming dispatch,
  so removing the fallback condition leaves it green.

**Approach:** amend in place. Edit the CONVENTIONS **seed** and regenerate the
projection with `make build-self`. Anchor every edit on section identity.

**Done when:** the roster test passes and fails under both mutations separately.

### T4: both adapters project the agent contract

**Depends on:** T2
**Verification mode:** goal-based check
**Artifact:** a new test under `packages/agentbundle/tests/build_pipeline/`.

**Tests:**
- Verify AC11 per adapter, naming `implementer` explicitly rather than asserting
  a directory. Declare the expected paths independently of the adapter code
  under test.
- **Mutation proof, two mutations.**
  (a) Product-side: make one adapter emit the other's agent root. Expected:
  exactly that adapter fails, proving the path half is load-bearing.
  (b) Remove the agent from pack source. Expected: both adapters fail.

**Approach:** one build-pipeline test projecting once per adapter into a
temporary directory; the probe measured 1.08s for both, so no caching is
warranted.

**Done when:** the test passes and fails under both mutations separately.

### T5: adopter-visible surfaces describe the shipped behaviour

**Depends on:** T1, T2, T3, T4
**Verification mode:** goal-based check
**Artifact:** an assertion in T3's roster test file.

**Tests:**
- Verify the guide describes dispatch and retains the fan-out-disabled
  statement. Verifies AC10. Respect A5: do not reorder that region.
- **Mutation proof.** Invariant: the guide keeps the fan-out statement.
  Mutation: delete that sentence. Expected: the assertion fails.
- Goal-based: the five gates named in § Constraints exit 0.

**Approach:** update the guide leading with the worktree path. Add a
`## [core][2.24.0] — <date>` section to `docs/product/changelog.md` directly
beneath `[Unreleased]`, bump `packs/core/pack.toml` to `2.24.0`, and let the
build regenerate `web/src/lib/now-highlights.generated.json`. Keep development
vocabulary out of the entry — it projects onto the `/now/` surface. There is no
`packs/core/CHANGELOG.md` and none is created; packs do not carry one.

**Done when:** all five gates exit 0 and the guide assertion fails under the
stated mutation.

## Rollout

- **Delivery:** single PR, reversible by revert. No state, schema, or persisted
  artifact changes, so nothing migrates back.
- **Infrastructure / external systems / sequencing:** none beyond the task DAG.

## Risks

- One member is silent rather than wrong today, so the negative half alone
  cannot fail over it. AC9 exists for that; if the positive half is dropped in
  review, the sweep stops proving anything about that member.
- `make build-self` must run after the seed edit or the byte-equality roster
  test reds on a change that looks complete locally.
- The frontend inlining unit is a 703-line router with no module index; naming
  the wrong unit inlines either too much or nothing. T1 names the unit.
- U1 adds lines to `SKILL.md` rather than removing them, so it raises the body
  count. U3's baseline must be re-measured after U1 lands; the brief's recorded
  822 is U1's starting point, not U3's.

## Changelog

- 2026-09-03 — initial draft from confirmed brief slice U1.
- 2026-09-03 — reshaped from "move procedure" to delete-and-cite after a Codex
  boundary investigation found seven of nine statements already owned; corrected
  the delivery mechanism after establishing that craft reaches the agent inlined.
- 2026-09-03 — extraction split into U3 by owner decision. Six of nine candidate
  statements proved immovable for independent reasons, leaving roughly three
  movable lines; the remaining scope is dispatch only. An earlier draft assigned
  TDD to the refusal criterion, which was wrong — the subject is a contract file
  and a prose edit has no red-green cycle.
