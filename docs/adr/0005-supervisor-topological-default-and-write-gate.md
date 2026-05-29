# ADR-0005: Supervisor mode — topological-order default, gated parallel writes

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-05-29
- **Deciders:** @eugenelim
- **Supersedes:** none
- **Related:** RFC-0015 (`docs/rfc/0015-wave-scheduled-supervisor-mode.md`); spec `docs/specs/wave-scheduled-supervisor/`; `docs/CONVENTIONS.md` §Supervisor mode; `work-loop` skill.

## Context

The `work-loop` supervisor mode auto-branches to parallel `implementer`
fan-out whenever a plan declares two or more tasks `Depends on: none`, and
discards every other dependency edge — even though the `new-spec` plan
template mandates a `Depends on:` on every task (so the full task DAG is
already present and thrown away).

RFC-0015 ran six deterministic experiments and surfaced the forces:

- **The write problem is real.** Two DAG-independent tasks editing
  *different* files can make incompatible *implicit decisions* that
  survive textual merge **and** each task's own gates, breaking only in
  the integrated state — a *silent* failure today's auto-parallel default
  ships. The conflict literature names this (Horwitz–Prins–Reps
  *interference*; Mens' detection ladder): the dangerous classes are the
  ones a default gate can't catch.
- **DAG-independence is a weak safety signal.** Measured over the repo's
  plans, only ~⅓ of declared-independent waves are actually file-disjoint.
- **The read/write split.** Parallel *readers* (reviewers) are safe;
  parallel *writers* for coding are the fragile regime (corroborated by
  Anthropic, LangChain, Cognition; AgenticFlict measures a 27.67% textual
  conflict rate across 142K+ agentic PRs — the *loud* rate, silent extra).

Constraints we operate under: the change must be **portable across every
adapter** (the `agent` primitive's availability varies); it must **reuse
`loop-cohort` and worktrees — no new subsystem**; and worktree isolation
carries hazards under a shared `.git` (multi-session drivers).

## Decision

> Supervisor mode will schedule tasks by the full `Depends on:` DAG and
> execute them in **topological order, sequentially, by default** on every
> adapter; parallel implementer **writes** are **opt-in and gated** on (a)
> membership in a measured safe category *and* (b) a `git merge-tree`
> file-disjointness check, with everything else run serial.

Elaboration and boundaries:

- The **read/write split is the governing boundary.** Parallel reads
  (reviewer fan-out) stay free; parallel writes are gated, never automatic.
- The sequential topological default's value is **scheduling correctness**
  (cycle + forward-reference detection), not speed; it is ~1× tokens and
  runs identically on every adapter.
- Safe categories (the only ones the gate admits): *cannot-collide*
  (per-file codemod / additive / disjoint-no-shared-symbol), *typed
  Group B* (signature/type changes in a statically-typed repo, caught by a
  post-merge typecheck), and *textual-loud* (caught by `git merge`). All
  others — dynamic-semantic interference, shared mutable state,
  move/extract-vs-edit, migration ordering, shared fixtures — run serial.
- **`merge-abort` is preserved** as the textual backstop; it is never
  relaxed. Write isolation comes from a git worktree (loop-managed
  standalone; delegated to the driver when one is present — never stacked).

## Consequences

**Positive:**
- Correct, verified task ordering on every adapter (catches real
  forward-reference bugs the loop ships unverified today).
- The *silent* parallel-write failure path is closed by default; parallel
  writes only run where a loud backstop (merge or typecheck) or a covering
  integrated test applies.
- Reuses `loop-cohort` + worktrees; no new subsystem or dependency.

**Negative:**
- A DAG scheduler + a dispatch gate to build and maintain in `loop-cohort`.
- Parallelism applies to a *minority* of waves here (~⅓ file-disjoint), so
  the throughput upside is modest and sublinear.
- A one-plan `Depends on:` grammar migration (the cross-spec marker).

**Neutral / to revisit:**
- The real-implementer break *frequency* per category is unmeasured;
  **T2-live** (a post-acceptance spike) measures it before the parallel
  path is expanded.
- The safe-category list may widen if static-interference tooling matures
  enough to make a currently-silent class loud.

## Alternatives considered

- **Do nothing (keep auto-parallel on `Depends on: none`).** Rejected: it
  ships *silent* semantic breaks and never verifies ordering — the failures
  recur on every multi-task plan.
- **Always-parallel / a self-writing orchestration engine** (the dynamic-
  workflows regime). Rejected: ~15× tokens, sublinear speedup, and it
  *maximizes* the silent-break surface — the opposite of the read/write
  split's lesson.
- **Adopt Claude Code Agent Teams as *the* substrate.** Rejected:
  experimental and not portable across adapters; each host's own runtime is
  a per-host substrate candidate instead.

## References

- RFC-0015 (the full decision record, experiments, and citations).
- Mens, *A State-of-the-Art Survey on Software Merging*, IEEE TSE 2002;
  Horwitz, Prins & Reps, *Integrating Non-Interfering Versions of
  Programs*, ACM TOPLAS 1989 (the detection ladder + interference).
- AgenticFlict, [arXiv 2604.03551](https://arxiv.org/abs/2604.03551) (the
  measured agentic-PR conflict rate).
