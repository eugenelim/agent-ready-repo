# Spec: Agent Skill Engineering Languages and Execution

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`RFC-0097`](../../rfc/0097-agent-skill-engineering.md); [`Agent Skill Engineering Corpus`](../agent-skill-engineering-corpus/spec.md)
- **Brief:** docs/product/briefs/agent-skill-engineering.md
- **Discovery:** none
- **Contract:** none — the foundation semantic provider request/response contract remains unchanged.
- **Shape:** mixed

> **Hard dependency, satisfied.** This slice depends on the Agent Skill
> Engineering Corpus slice's census, admission rule, taxonomy partition, and
> retrieval baseline. That slice shipped in `ea3a0f625`; its spec reads
> `Shipped` and the workspace engine reports the dependency edge cleared.
> Implementation is authorized.

## Objective

Add portable depth for the language and execution questions that remain outside
the corpus slice: Python/pytest, TypeScript/Node and JavaScript test runners,
process and filesystem cost, pack and CI critical paths, and worktrees, state
locks, and shared-host admission. The topics remain task-shaped guidance for
agent-skill scripts, evaluations, packs, and their execution environments;
they do not become general language or CI handbooks.

These five leaves are admitted on the **doctrine** basis, not observed practice.
Their evidence is documented external contracts plus recorded controlled
measurement, which is what RFC-0097's own evidence notes assembled for them.
The corpus slice implemented doctrine's field validation but deliberately left
doctrine-side body parity unimplemented as a loud failure, naming the successor
slice as its owner. This slice is that successor, so closing that gap is part of
the work rather than an incidental fix.

## Boundaries

### Always do

- Build on the corpus slice's governed admission, topology, and measured
  retrieval baseline rather than replacing their contracts.
- Keep Python/pytest and TypeScript/Node guidance distinct while applying the
  shared language contracts RFC-0097 defines.
- Keep execution guidance limited to skill scripts, evaluations, pack tests,
  CI, worktrees, locks, shared hosts, and measured machine-load decisions.
- Give every doctrine claim group a promotion class the inherited predicate
  already admits, and cite sources that name themselves, when they were read,
  and their version state.
- Re-measure any recorded evidence whose covered content changed. A digest that
  moved is re-measured, never re-stamped onto the earlier observation.

### Ask first

- Changing the semantic provider request/response contract or the corpus
  slice's admission and retrieval thresholds.
- Adding a dependency, runtime-specific claim, or delivery mechanism not
  licensed by the governing RFC.
- Adding a promotion class to the inherited doctrine vocabulary. Implementing
  the parity check the corpus slice left unimplemented is not such a change:
  it enforces an existing requirement rather than widening the rule.

### Never do

- Turn a language topic into a general programming-language handbook.
- Claim a runtime profile, `runtime-package`, plugin, or subagent capability;
  those are owned by later slices.
- Re-record the corpus slice's foundation retrieval pins as part of this work.
  The 24 inherited per-case pins are a non-regression gate: a measurement that
  moves one is a defect to surface, never a pin to rewrite.
- Claim maturity for a topic whose governing evidence note withholds it.
- Reword an acceptance criterion, assertion, or retrieval case after seeing its
  measured result.

## Testing Strategy

- Use TDD for topic admission, doctrine-side parity, topology accounting, and
  per-case retrieval non-regression.
- Use goal-based checks for measured retrieval precision, deterministic builds,
  staged-tree confinement, and CI execution-economics evidence.
- Use observed behavior fixtures for the pytest-suite and Node/browser-suite
  cases before claiming their behavior coverage.
- Prove every new or changed guard by mutation: state the invariant, the test
  that must catch its removal, the exact mutation, and the observed failure.
  The doctrine arm has never executed against any input, so its first exercise
  carries a mutation proof for each predicate limb it newly reaches.

## Acceptance Criteria

- [ ] **AC1 — Five topology leaves are delivered.** The language and execution
  leaves from RFC-0097 D3 are accounted for by admitted topics or declared
  unpopulated records under the corpus admission contract, with every leaf in
  exactly one set and neither set naming a leaf the taxonomy does not have.
- [ ] **AC2 — Language depth remains specific.** Python/pytest and
  TypeScript/Node guidance each covers the language-specific execution and
  test-isolation concerns RFC-0097 assigns to it, without collapsing them into
  one lowest-common-denominator topic. The TypeScript/Node topic states the
  maturity limit its governing evidence note records rather than implying a
  maturity that note withholds.
- [ ] **AC3 — Execution economics is bounded and measured.** Process,
  filesystem, pack/CI critical-path, worktree, lock, shared-host, and
  machine-load guidance is limited to the corpus domain and supported by
  measured retrieval and execution evidence.
- [ ] **AC4 — Retrieval and baseline safety hold.** New retrieval cases are
  predeclared and measured, meet the corpus thresholds, and preserve every
  pinned foundation result. Both the retrieval record and the generic-negative
  record are re-measured against the tree they describe, since both are bound
  to the same digest triple that admitting a topic moves.
- [ ] **AC5 — Behavior evidence expands.** The pytest-suite and Node/browser
  behavior fixtures are declared and recorded through the established observed
  evaluation process, and every graded result whose pinned source digest this
  slice moves is re-measured rather than re-stamped.
- [ ] **AC6 — Doctrine-side source parity is enforced, not deferred.** Each
  cited source's identity and retrieval date appears in both the authored and
  the compiled projection of the topic that cites it. The check replaces the
  corpus slice's unconditional failure, and each predicate limb the doctrine
  arm newly exercises carries a recorded mutation proof.
- [ ] **AC7 — Shipped language-availability statements match what shipped.**
  Every shipped statement about language-extension family availability agrees
  with the admitted topic set, so no adopter-facing text promises an absence
  the corpus no longer has.

## Follow-ons

- Runtime composition profiles remain a separate slice after this one, together
  with the composition and runtime-profile leaves and the remaining two behavior
  fixtures: subagent composition and hook/plugin design.
- Provider-mode and runtime-package availability remain governed by their
  respective approved delivery contracts.
- A first-party or external TypeScript/Node pilot is the evidence that would let
  a later slice withdraw this slice's recorded maturity limit.
