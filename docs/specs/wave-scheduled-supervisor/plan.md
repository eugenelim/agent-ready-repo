# Plan: wave-scheduled supervisor mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change lands inside the existing `loop-cohort.py`
(`packs/core/.apm/skills/work-loop/scripts/`) plus the `new-spec` plan
template — **no new module, dependency, or top-level dir** (ADR-0005). Build
order is bottom-up: first make `Depends on:` machine-parseable (T1), then the
pure graph logic that consumes it — DAG build + cycle/forward-ref detection
(T2) — then the execution change that flips the default to sequential
topological order (T3), then the opt-in parallel-write dispatch gate (T4, the
load-bearing decision-3 AC). The doc/template surface (T5 grammar + lint, T6
SKILL/supervisor-mode/CONVENTIONS + build-self) follows once behavior is
settled. The riskiest part is T4's worktree/merge surface — it carries a
mandatory real `git worktree add` dry-run (AC9), never a prose walk-through.
All scheduler logic is pure functions over parsed edges, so the bulk is TDD;
the worktree dry-run and the doc/lint surface are goal-based.

## Constraints

- **ADR-0005** + **RFC-0015** — topological-order default; parallel writes
  opt-in and gated on safe-category ∧ `git merge-tree` disjointness; read/write
  split; `merge-abort` preserved; reuse `loop-cohort`, no new subsystem.
- `docs/CONVENTIONS.md` §Supervisor mode — two-levels-deep; sequential merge in
  task-id order; conflict⇒PLAN; gates in primary; the dry-run "Known limitation".
- Self-host projection rule — edit `packs/core/...` source, then `make
  build-self`; never edit the generated `.claude/...` copies.

## Construction tests

Most live per-task below. Cross-cutting:

**Integration tests:** none beyond per-task tests (the scheduler is pure
functions over parsed edges; the gate's decision function is unit-tested).
**Manual verification:** AC9 — a real `git worktree add` + 2-task dispatch
round against a throwaway spec, exercising the parallel-write path end to end
(records the result in `notes/`); this is the dry-run CONVENTIONS mandates
before trusting the worktree/merge surface.

## Tasks

### T1: `Depends on:` is machine-parseable (robust parser + cross-spec marker)

**Depends on:** none

**Tests:** (`packages/agentbundle/tests/unit/test_loop_cohort_schedule.py`)
- prose-bearing field (`T11 (not parallelizable with T13/T14)`) → `{T11}` only.
- letter-suffixed IDs (`T1a`) and ranges (`T1-T6`) → expanded edge set.
- cross-spec marker `spec:<name>/TN` parses as a *cross-spec* dep and is
  **excluded** from the intra-plan edge set (verifies AC6).
- regression: `self-hosting`'s `` `distribution-adapters` T7 `` does **not**
  collide with its local `T7` (no phantom cycle).
- `parse_plan` preserves the **authored task-ID order** (the sequence of
  `### T<n>` headings) — required downstream for forward-ref detection (AC3).

**Approach:**
- Add `parse_depends_on(field, local_task_ids) -> (local_edges, cross_spec)`
  to `loop-cohort.py`; strip parenthetical prose, expand ranges, admit the
  `spec:<name>/TN` marker, intersect with local IDs.
- Add `parse_plan(text) -> (ordered_task_ids, deps_by_task)` that walks the
  `### T<n>` headings **in file order** and applies `parse_depends_on` per
  task — so authored position is captured, not just the edge set.

**Done when:** the five tests above are green, incl. authored-order preservation.

### T2: DAG build + cycle / forward-ref detection

**Depends on:** T1

**Tests:**
- topological order (Kahn supersteps) over a known plan = expected layers (AC1).
- a planted cycle → detection function returns/raises a PLAN-level error naming
  the cycle (AC2).
- forward-reference detection flags `agent-spec-cli` T13→T15 and
  `incompatible-hook-event-drop` T2→T3,T4 (AC3); a clean plan flags neither.

**Approach:**
- Add `build_dag(ordered_task_ids, deps_by_task)` + `detect_cycles` +
  `detect_forward_refs` to `loop-cohort.py`, consuming T1's `parse_plan`.
- `detect_forward_refs` compares each declared dep's **authored index**
  against the depending task's authored index (a forward-ref is a valid edge
  whose target is authored *later*) — hence T1's ordered-task-ID capture.
- Surface failures via the existing `stop(reason)` non-zero-exit path.

**Done when:** AC1–AC3 tests green; a cycle/forward-ref exits non-zero.

### T3: sequential topological execution is the default (remove auto-parallel branch)

**Depends on:** T2

**Tests:**
- execution order equals the topological order from T2 (AC4).
- a plan with ≥2 `Depends on: none` tasks **no longer** auto-branches to
  parallel fan-out — it runs sequentially (asserts the removed branch).

**Approach:**
- Replace the "≥2 `Depends on: none` ⇒ supervisor fan-out" trigger in
  `loop-cohort.py` + `references/supervisor-mode.md` with: compute the DAG (T2),
  run tasks in topological order, single-agent, by default.
- The `supervisor-mode.md` edit is confined to the **trigger/header text**
  (the loaded-on-demand intro); it touches **none** of the six dry-run-gated
  procedure surfaces (pre-flight, worktree creation, report ordering, merge
  order, cleanup, `state.json.worktrees` schema), so T3 needs no worktree
  dry-run — that obligation attaches to T4, which does touch dispatch.

**Done when:** AC4 tests green; no auto-parallel dispatch occurs by default.

### T4: opt-in parallel-write dispatch gate (decision 3 — required AC5)

**Depends on:** T2, T3

**Tests:**
- **allow-path:** a wave of **cannot-collide / typed-Group-B** tasks that
  `git merge-tree` reports disjoint → gate returns `parallel` (AC5).
- **serialize-on-fail, both halves independently:** (a) a *textual-loud*
  wave whose tasks **overlap** (merge-tree reports a conflict) → `serial`;
  (b) a wave containing any **non-safe** category (e.g. shared-state) →
  `serial` even if merge-tree is clean. Fail closed on either (AC5).
- `merge-abort → re-PLAN` still fires on a real merge conflict.
- **AC9 dry-run:** a real `git worktree add` + 2-task dispatch round against a
  throwaway spec exercises the parallel path end-to-end; result recorded in
  `notes/` (the CONVENTIONS-mandated worktree/merge dry-run).

**Approach:**
- Add `dispatch_decision(wave) -> "parallel" | "serial"` to `loop-cohort.py`:
  classify each task's category, run `git merge-tree` on the wave's branches
  for disjointness, require both; default off (opt-in flag). Wire into the
  worktree path behind the opt-in.

**Done when:** allow-path + both serialize-on-fail tests green; gate is off by
default; **and the AC9 worktree dry-run has been run with its result in
`notes/`** (not a prose walk-through).

### T5: plan-template `Depends on:` grammar + `new-spec` cycle/forward-ref lint

**Depends on:** T1

**Tests:** (goal-based)
- the lint, run over a fixture plan with a planted cycle, exits non-zero.
- run over the current `docs/specs/*/plan.md`: no *real* findings — the only
  exclusion is `kiro-ide-hook` (no `### T<n>` headings; 20 of 21 plans parse).
  Verifies AC7.

**Approach:**
- Document the grammar (local IDs, ranges, `spec:<name>/TN` marker) in
  `packs/core/.apm/skills/new-spec/assets/plan.md`; add a `new-spec` lint that
  reuses T1/T2 to flag cycles/forward-refs, invoked via `sys.executable`.

**Done when:** lint exits non-zero on the planted cycle and zero on current plans.

### T6: doc-of-record updates + clean projection

**Depends on:** T3, T4, T5

**Tests:** (goal-based)
- `make build-self` leaves a clean tree (`git status --short` empty).
- both lint surfaces pass: `lint-packs` (source) + `tools/lint-agent-artifacts.py`
  (projection) — verifies AC8.
- grep confirms no new module/dir/dependency was added (AC8).

**Approach:**
- Update `work-loop/SKILL.md` §EXECUTE, `references/supervisor-mode.md`, and
  `docs/CONVENTIONS.md` §Supervisor mode + §Multi-agent shape by profile to
  describe the topological default + the opt-in gate; `make build-self`.

**Done when:** clean tree, both lint surfaces green, AC8 holds.

### T7: proactive cleared-gate parallel surface (follow-on 1 — AC10)

**Depends on:** T4, T6

**Tests:** (`packages/agentbundle/tests/unit/test_loop_cohort_schedule.py`)
- on a `parallel` outcome, `dispatch-decision` prints the bare token `parallel`
  to **stdout** (unchanged) **and** a parallel-eligible rationale naming the
  task count to **stderr** (AC10).
- on a `serial` outcome from branch overlap (`merge_tree_clean` false), stderr
  names that the branches **conflict under `git merge-tree`** (not specific
  filenames — `wave_is_disjoint` returns a bool, so the observable is the
  conflict, not the path set); on a `serial` outcome from a non-safe category
  (merge clean), stderr names the **offending category**. stdout stays `serial`.
- **both-fail tie-break:** a wave that is *both* non-safe and overlapping →
  stderr names the **merge-tree-conflict** reason (matching the decision's
  short-circuit order), stdout `serial`.

**Approach:**
- Add the human-facing rationale to `cmd_dispatch_decision` in `loop-cohort.py`
  — stderr only; compute the serialize reason (merge-tree conflict vs. non-safe
  category, conflict-first to match `dispatch_decision`'s short-circuit) from
  the same inputs the decision used. stdout token unchanged so T4's existing
  verb tests still pass. No change to `wave_is_disjoint`'s bool contract.
- Instruct the agent in `work-loop/SKILL.md` §EXECUTE + `references/supervisor-mode.md`
  to **present** the cleared-gate opportunity (the parallel-eligible wave + its
  tasks) and fan out only on explicit human opt-in, defaulting to sequential
  absent one — never silently. This is *present-and-default-safe*, not the
  halt-and-wait Surface verb (which would block unattended runs). The
  opt-in is the existing per-wave human decision — **no new flag/state field**
  (that is follow-on 4). The edit touches SKILL §EXECUTE + the supervisor-mode
  **header/concept only — none of the six dry-run-gated procedure surfaces**
  (pre-flight, worktree creation, report ordering, merge order, cleanup,
  `state.json.worktrees` schema), so T7 needs no worktree dry-run (same carve-out
  as T3).
- `make build-self`; close follow-on 1 in `docs/backlog.md`.

**Done when:** the AC10 verb tests (incl. the both-fail tie-break) are green; a
grep confirms the present-the-opportunity instruction is present in **both**
`work-loop/SKILL.md` §EXECUTE and `references/supervisor-mode.md` (the goal-based
half of AC10); build-self leaves a clean tree.

## Rollout

Behavior change ships behind the **default flip** (sequential topological is the
new default; parallel writes are an opt-in flag, off by default). Reversible:
the opt-in flag gates all new parallel behavior, and the sequential path is the
pre-existing safe baseline. AC9's dry-run gates trusting the worktree surface
before any parallel path is exercised for real.

## Risks

- T4's worktree/merge surface is the historically under-validated part
  (CONVENTIONS "Known limitation"); the AC9 dry-run is mandatory, not optional.
- `git merge-tree` output parsing varies by git version; pin behavior with a
  fixture and the probed `git 2.50.1`.
- The default flip changes supervisor-mode behavior for every adopter — T6's
  doc updates and the clean-projection gate must land in the same change.

## Changelog

- 2026-05-29: initial plan (implements RFC-0015 + ADR-0005).
- 2026-05-29 (mid-EXECUTE): **forward-references are warnings, not hard
  errors.** Discovered while building T5's lint — AC3-as-a-hard-error
  conflicted with AC7's "no real findings over current plans", because the
  corpus genuinely contains forward-refs (the two AC3 cases). This
  **diverges from RFC-0015 decision 1**, whose body says "a forward-ref is a
  PLAN error"; the divergence is correct on the merits (a forward-ref is a
  valid acyclic edge the topological sort reorders — only a *cycle* is
  unschedulable) and is recorded in governance as **RFC-0015 § Errata**
  (Approver-signed 2026-05-29), not just here. The `schedule` verb + lint
  **warn** on a forward-ref and reorder; only a **cycle** is the hard error.
  Spec AC3/AC7 amended in this PR (drift closed in-place).
- 2026-05-29 (post-review, in-PR): **added T7 / AC10 — proactive cleared-gate
  surface** (ROADMAP follow-on 1, pulled into this PR at the user's request).
  The gate being opt-in (AC5) left no affordance that *presents* a cleared
  wave to the human, so parallelism defaulted to sequential by inertia. T7
  makes `dispatch-decision` emit a human-readable rationale and instructs the
  loop to present the opportunity for explicit opt-in. No new module/dep/dir;
  stdout token unchanged.
