# Plan: Agent Skill Engineering Languages and Execution

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `docs/rfc/0097-agent-skill-engineering.md` D3 and
  shared language contracts; `docs/specs/agent-skill-engineering-corpus/` for
  the prerequisite admission, topology, and retrieval baseline.

> **Plan contract:** this is the implementation strategy for a later delivery.
> It is intentionally scoped only and authorizes no implementation while the
> hard dependency remains incomplete.

## Approach

1. Confirm the corpus slice has shipped and retain its topology partition,
   admission fixture, and foundation retrieval pins.
2. Establish evidence for the five language and execution leaves before
   authoring any topic body; record unsupported leaves as unpopulated.
3. Add predeclared retrieval cases and the pytest-suite and Node/browser
   behavior fixtures, then take one measured run against the assembled tree.
4. Regenerate governed references and verify deterministic compilation,
   confinement, portability, exact retrieval thresholds, and per-case
   foundation non-regression.

## Tasks

### T1: Confirm the corpus prerequisite and evidence boundaries

**Depends on:** Agent Skill Engineering Corpus spec shipped

Identify the five D3 leaves and the evidence needed to admit each without
changing the corpus slice's contracts or pins.

### T2: Author admissible language and execution topics

**Depends on:** T1

Add only topics whose claim groups satisfy the inherited admission rule; record
the remaining leaves as unpopulated with their admission path.

### T3: Measure retrieval and behavior evidence

**Depends on:** T2

Predeclare retrieval cases and the pytest-suite and Node/browser fixtures,
then record the observed assembled-tree results and foundation-pin comparison.

### T4: Regenerate and verify the portable corpus

**Depends on:** T3

Regenerate through the governed compiler and run the owning admission,
retrieval, deterministic-build, staged-tree, and portability gates.

## Risks

| Risk | Mitigation |
| --- | --- |
| A language claim becomes generic developer guidance | Limit every topic and retrieval case to skills, evaluations, packs, or their execution environments. |
| New topics move a foundation result | Treat the inherited 24 per-case pins as a hard non-regression gate. |
| Evidence cannot support a leaf | Record it as unpopulated rather than lowering the admission rule. |
