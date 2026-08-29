# Spec: Agent Skill Engineering Languages and Execution

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md); [`Agent Skill Engineering Corpus`](../agent-skill-engineering-corpus/spec.md)
- **Brief:** [`agent-skill-engineering.md`](../../product/briefs/agent-skill-engineering.md)
- **Discovery:** none
- **Contract:** none — the foundation semantic provider request/response contract remains unchanged.
- **Shape:** mixed

> **Hard dependency:** this slice cannot begin until the Agent Skill Engineering
> Corpus spec is shipped. It depends on that slice's census, admission rule,
> taxonomy partition, and retrieval baseline.

> **Spec contract:** this document defines what a later implementation must
> deliver. This slice is scoped only; it implements no corpus content here.

## Objective

Add portable depth for the language and execution questions that remain outside
the corpus slice: Python/pytest, TypeScript/Node and JavaScript test runners,
process and filesystem cost, pack and CI critical paths, and worktrees, state
locks, and shared-host admission. The topics remain task-shaped guidance for
agent-skill scripts, evaluations, packs, and their execution environments;
they do not become general language or CI handbooks.

## Boundaries

### Always do

- Build on the corpus slice's governed admission, topology, and measured
  retrieval baseline rather than replacing their contracts.
- Keep Python/pytest and TypeScript/Node guidance distinct while applying the
  shared language contracts RFC-0097 defines.
- Keep execution guidance limited to skill scripts, evaluations, pack tests,
  CI, worktrees, locks, shared hosts, and measured machine-load decisions.

### Ask first

- Changing the semantic provider request/response contract or the corpus
  slice's admission and retrieval thresholds.
- Adding a dependency, runtime-specific claim, or delivery mechanism not
  licensed by the governing RFC.

### Never do

- Turn a language topic into a general programming-language handbook.
- Claim a runtime profile, `runtime-package`, plugin, hook, or subagent
  capability; those are owned by later slices.
- Re-record the corpus slice's foundation retrieval pins as part of this work.

## Testing Strategy

- Use TDD for topic admission, topology accounting, and per-case retrieval
  non-regression.
- Use goal-based checks for measured retrieval precision, deterministic builds,
  staged-tree confinement, and CI execution-economics evidence.
- Use observed behavior fixtures for the pytest-suite and Node/browser-suite
  cases before claiming their behavior coverage.

## Acceptance Criteria

- [ ] **AC1 — Five topology leaves are delivered.** The language and execution
  leaves from RFC-0097 D3 are accounted for by admitted topics or declared
  unpopulated records under the corpus admission contract.
- [ ] **AC2 — Language depth remains specific.** Python/pytest and
  TypeScript/Node guidance each covers the language-specific execution and
  test-isolation concerns RFC-0097 assigns to it, without collapsing them into
  one lowest-common-denominator topic.
- [ ] **AC3 — Execution economics is bounded and measured.** Process,
  filesystem, pack/CI critical-path, worktree, lock, shared-host, and
  machine-load guidance is limited to the corpus domain and supported by
  measured retrieval and execution evidence.
- [ ] **AC4 — Retrieval and baseline safety hold.** New retrieval cases are
  predeclared and measured, meet the corpus thresholds, and preserve every
  pinned foundation result.
- [ ] **AC5 — Behavior evidence expands.** The pytest-suite and Node/browser
  behavior fixtures are declared and recorded through the established observed
  evaluation process.

## Follow-ons

- Runtime composition profiles remain a separate slice after this one.
- Provider-mode and runtime-package availability remain governed by their
  respective approved delivery contracts.
