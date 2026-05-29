# Spec: wave-scheduled supervisor mode

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0005, RFC-0015

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Generalize `work-loop` supervisor mode so it schedules a plan's tasks by the
**full `Depends on:` DAG** the plan template already mandates, instead of
reading only the `Depends on: none` subset. For the agent running a
multi-task plan, the user-visible outcomes are: (1) tasks execute in a
**verified topological order** — a dependency cycle or a forward-reference
(a task whose declared dep is authored later) is reported as a PLAN-level
error instead of silently running a task before its inputs exist; (2)
execution is **sequential by default on every adapter** (no auto-parallel
fan-out), so no *silent* parallel-write breakage can ship; (3) parallel
implementer **writes** happen **only** when explicitly opted in *and* a wave
clears the safety gate (a measured safe category **and** a `git merge-tree`
file-disjointness check), otherwise that wave runs serial. The `Depends on:`
field becomes machine-parseable (robust parser + a cross-spec marker) so the
scheduler can consume it. Success: a plan with declared dependencies runs in
correct order on any adapter; an ill-formed plan (cycle / forward-ref) fails
loud at PLAN; and parallel writes never run for a wave that can't clear the
gate.

## Boundaries

### Always do

- Edit the **pack source** (`packs/core/.apm/skills/work-loop/...`,
  `packs/core/.apm/skills/new-spec/assets/plan.md`) and run `make build-self`;
  treat the projected `.claude/...` copies as generated.
- Keep the **sequential topological order the default** on every adapter;
  parallel writes are opt-in only.
- Gate every parallel-write wave on **both** a safe-category check **and** a
  `git merge-tree` file-disjointness check; fail closed (serialize) on either.
- Preserve `merge-abort → re-PLAN` as the textual backstop on any worktree merge.

### Ask first

- Widening the **safe-category allowlist** beyond the three RFC-0015 categories
  (cannot-collide / typed-Group-B / textual-loud).
- Any change to the worktree/merge surface in `references/supervisor-mode.md`
  (RFC-0015 / CONVENTIONS require a real `git worktree add` + dispatch dry-run,
  not a prose walk-through).
- Enabling parallel writes on by default, or for a host whose merge/typecheck
  backstop hasn't been confirmed.

### Never do

- **Never add a new module, package, or top-level directory, or a new runtime
  dependency** — the scheduler, parser, and gate live inside the existing
  `loop-cohort.py` + plan template (RFC-0015: reuse, no new subsystem).
- Never auto-fire parallel implementer fan-out (the behavior this spec removes).
- Never run a *silent-failing* category (dynamic-semantic interference, shared
  mutable state, move/extract-vs-edit, migration ordering, shared fixtures)
  in parallel — those serialize regardless of disjointness.
- Never relax `merge-abort`, and never edit the generated `.claude/...` paths
  directly.

## Testing Strategy

- **DAG build + cycle/forward-ref detection** — **TDD**. Pure graph logic over
  parsed `Depends on:` edges; a compressible invariant (topological order;
  cycle/forward-ref → error). Construction tests in `plan.md`.
- **Robust `Depends on:` parser + cross-spec marker** — **TDD**. Pure parsing;
  fixture inputs (prose, letter-suffixed IDs, ranges, `spec:<name>/TN`) → edge
  sets. Includes the `self-hosting` cross-spec no-collision regression.
- **Sequential topological execution + the parallel-write dispatch gate**
  (safe-category ∧ `git merge-tree` disjointness; else serial) — **TDD** for
  the gate's decision function (allow vs serialize), plus a **goal-based**
  dry-run (`git worktree add` + a 2-task dispatch round) for the worktree/merge
  surface per the CONVENTIONS "Known limitation".
- **Plan-template grammar + `new-spec` lint** — **goal-based check**: the lint
  parses every `docs/specs/*/plan.md`, flags cycles/forward-refs, and exits
  non-zero on an ill-formed graph; verified by running it over the repo.
- **Doc-of-record updates** (`work-loop` SKILL §EXECUTE, `supervisor-mode.md`,
  `CONVENTIONS.md` §Supervisor mode + §Multi-agent shape by profile) —
  **goal-based check**: both lint surfaces (`lint-packs` + `tools/lint-agent-artifacts.py`)
  pass and `make build-self` leaves a clean tree.

## Acceptance Criteria

- [ ] AC1 — `loop-cohort` builds the full dependency graph from every task's
  `Depends on:` and produces a topological order (Kahn supersteps).
- [ ] AC2 — a dependency **cycle** is detected and reported as a PLAN-level
  error (non-zero exit), naming the cycle.
- [ ] AC3 — a **forward-reference** (a task whose declared dep is authored
  later) is detected and **reported as a warning**, and the topological order
  **reorders it** so the dependency runs first (a forward-ref is a valid
  acyclic edge — unlike a cycle, it is schedulable; only AC2's cycle is a hard
  error). The two real cases in the repo's plans (`agent-spec-cli` T13→T15;
  `incompatible-hook-event-drop` T2→T3,T4) are covered by tests.
- [ ] AC4 — default execution is **sequential in topological order on every
  adapter**; the old auto-parallel-on-`Depends on: none` branch no longer fires.
- [ ] AC5 *(required — RFC-0015 decision 3)* — parallel-write dispatch occurs
  **only** when a wave's tasks are all in a safe category (cannot-collide /
  typed-Group-B / textual-loud) **and** the wave passes a `git merge-tree`
  file-disjointness check; **both** an allow-path test and a
  serialize-on-fail-path test exist and pass.
- [ ] AC6 — the `Depends on:` parser handles prose, letter-suffixed IDs (`T1a`),
  ranges (`T1-T6`), and the cross-spec marker `spec:<name>/TN`, and ignores
  cross-spec deps for intra-plan scheduling (the `self-hosting` no-collision
  regression passes).
- [ ] AC7 — the plan template documents the `Depends on:` grammar + cross-spec
  marker; the `new-spec` lint **fails on cycles** and **warns on
  forward-references**, and over all current plans reports **zero cycles**
  (the two forward-refs — `agent-spec-cli`, `incompatible-hook-event-drop` —
  surface as warnings, not failures), with `kiro-ide-hook` excluded (no
  `### T<n>` headings; 20 of 21 plans parse).
- [ ] AC8 — `make build-self` leaves a clean tree and both lint surfaces pass;
  no new module, dependency, or top-level directory was introduced.
- [ ] AC9 — the worktree/merge dispatch path was exercised by a real
  `git worktree add` + 2-task dry-run (not a prose walk-through), per CONVENTIONS.

## Assumptions

- Technical: scheduler + parser + gate live in `loop-cohort.py` and
  `references/supervisor-mode.md` (source: `packs/core/.apm/skills/work-loop/`, probe #1).
- Technical: `Depends on:` grammar lives in the plan template (source:
  `packs/core/.apm/skills/new-spec/assets/plan.md`, probe #2).
- Technical: `git merge-tree` is available for the disjointness gate (source:
  `git version 2.50.1`, probe #3).
- Technical: implementation is Python, projected via `make build-self` (source:
  probes #4–5; `Makefile:38`).
- Technical: loop-cohort has no dedicated test suite today; scheduler tests
  land in `packages/agentbundle/tests/unit/test_loop_cohort_schedule.py` — the
  CLI/integration test root, chosen over the adapter/contract root
  (`agentbundle/build/tests/`) because the scheduler is plain Python logic, not
  a build-pipeline/adapter contract (source: grep — only an indirect ref in
  `test_pre_pr_py.py`; author decision 2026-05-29).
- Process: design + scope are fixed by RFC-0015 (Accepted) and ADR-0005
  (Accepted); edit pack source not projected paths (source: RFC-0015 follow-on;
  self-host projection rule).
- Product: serves work-loop supervisor-mode users on multi-task plans; T2-live
  (real-implementer break frequency) is out of scope (source: RFC-0015
  Experiment section).
