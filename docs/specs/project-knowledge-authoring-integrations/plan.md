# Plan: Project knowledge authoring integrations

- **Spec:** [`spec.md`](spec.md) (Shipped)
- **RFC:** [`RFC-0077`](../../rfc/0077-distill-knowledge.md) (Accepted)
- **ADRs:** [`ADR-0081`](../../adr/0081-canonical-project-knowledge-uses-per-topic-json.md) and [`ADR-0082`](../../adr/0082-project-knowledge-modes-separate-authority.md) (Accepted)
- **Status:** Done
- **Mode:** full

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as evidence changes. Substantial changes are
> recorded in the changelog.

## Approach

Add no new knowledge runtime. Each selected producer receives a small,
gate-specific choreography that reuses the shipped public contract and mode
seams. The prose names eligible scratch, canonical routing, the exact positive
gate, explicit negative gates, request construction, named unavailability,
gate-local receipt handling, and the post-capture verification/review return.
Construction tests pin those invariants in canonical `.apm` sources; behavior
evals test judgment paths that static text cannot prove.

The queued five-artifact shape remains one coherent integration slice. All rows
share the same public contract, receipt protocol, authority model, and security
boundary; only gate ownership and scratch vocabulary vary. Splitting by
artifact would duplicate the cross-cutting contract and make parity harder to
review. Implementation still begins with a smaller core-only pilot for brief,
spec, and plan gates. Governance-extras follows as a separate pack-sized task,
then one delivery task proves the complete authoring journey.

No producer gains automatic enquiry. The implementation describes only
separately visible, bounded optional calls at the matrix's decision moments and
preserves the foundation's committed-only abstention behavior.

## Assumptions surfaced

- The shipped capture schema and public CLI are sufficient; integrations add
  producer behavior, not contract fields or writer helpers.
- Prompt-authored skill prose is executable behavior. Static construction
  tests pin ordering/forbidden seams, while Tier-4 evals cover semantic triage,
  hostile input, abandonment, and abstention.
- A stable semantic gate is determined by actual lifecycle ownership, not by
  the artifact noun. This makes `author-brief` Draft, `new-adr` Proposed, and
  `new-spec` Draft/Drafting explicit non-gates.
- Knowledge mutations remain ordinary working-tree proposals and may require a
  targeted post-gate review without reopening unchanged normative approval.

## Constraints

- Follow RFC-0077 and ADR-0081/ADR-0082 without amending their frozen bodies.
- Preserve the public capture contract, private writer, mode isolation,
  receipt-selection contract, resource budgets, privacy checks, and enquiry
  semantics byte-for-byte unless a later approved amendment says otherwise.
- Edit canonical pack `.apm` sources, not generated projections. Run one pytest
  process per skill test directory, then regenerate projections only after all
  source and manifest edits are complete.
- Bump each non-cosmetically changed pack and its plugin manifest; update the
  root changelog and generated marketplace aggregate in the same delivery.
- Keep new tests and any helper code dependency-free and cross-platform. Add no
  new top-level directory or runtime/package dependency.
- Preserve missing-provider behavior instead of tightening the
  governance-extras core dependency to hide it.
- Do not change the broad work-loop closeout question, completed closeout
  enhancement, or any Git ref.

## Construction tests

- The existing project-knowledge suites remain the contract oracle for strict
  request validation, privacy refusal, mode isolation, gate-local pending
  selection, committed-only enquiry, abstention, and prompt-injection
  containment.
- The existing work-loop public-handoff test remains green and extends its byte
  pin so the closeout prompt and terminal closeout integration are unchanged
  while spec/plan approval gates are added.
- A disposable adopter-shaped end-to-end journey exercises all five positive
  gates and representative negative gates with the real projected skills and
  public `project_knowledge.py` CLI. It records only redacted receipts and
  pass/fail outcomes in `notes/manual-qa.md`.

## Design (LLD)

### Interfaces & contracts

The integration consumes
`contracts/jsonschema/knowledge-captured-observation.schema.json` unchanged.
Every producer constructs one request and invokes the public progressive skill;
only `project-knowledge` imports `knowledge_store.py`. A capture response is
retained as the exact pair `{capture_id, partition}`. Distillation uses
`selection_mode: workflow-receipts` and only pairs returned at that semantic
gate. The private writer, journal layout, derived identities, and mutation
proposal contract remain outside producer surfaces. Traces to AC7-AC9 and
AC12; implements the existing captured-observation contract.

Any producer read used for provenance line attribution or byte-digest
freshness first proves, with native real-path semantics, that a regular-file
candidate remains under the resolved repository root. Link-mediated escape,
non-file targets, I/O failure, and containment uncertainty refuse capture. A
committed Git blob identity is the read-free alternative for committed sources.
This producer precondition complements rather than weakens the public writer's
validation. Traces to AC15 and AC22.

### Component / module decomposition

- Core authoring sources own brief and spec/plan gates:
  `receive-brief` owns the Ready write-back; `author-brief` documents that Draft
  is a non-gate; `new-spec` documents that Draft/Drafting is a non-gate; and
  `work-loop` owns the `spec-approved` and `plan-locked` handoffs.
- Governance-extras authoring sources own RFC terminal completion and ADR
  acceptance. Pack integration metadata documents the optional handoff to the
  core provider without dispatching it.
- Skill-local construction tests pin positive and negative gates. Skill-local
  behavior evals cover triage, normative routing, hostile data, unavailability,
  optional enquiry, and abstention.
- Existing project-knowledge tests remain the runtime contract oracle; no new
  shared producer helper is introduced because the integrations are
  agent-mediated prose workflows.

Traces to AC1-AC6 and AC17-AC19.

### State & control flow

```text
explicit producer scratch since prior gate
  -> exact stable gate succeeds
  -> discard / canonical-route / admit
  -> construct typed request
  -> project-knowledge --capture
       | unavailable/refused -> named bounded outcome; no fallback
       | receipt             -> retain returned ID + partition in memory
  -> if this is a terminal gate, optional project-knowledge --distill --pending
       with workflow-receipts from this gate only
     otherwise surface the receipts as pending; do not transfer them
  -> explicit dispositions; unresolved stays pending
  -> producer verification/review barrier
  -> completion receipt
```

Optional enquiry is a separate branch before its declared authoring decision:
declare task, scope, known CQ, consequential risk, and one-query/one-refinement
budget; read a committed bounded evidence envelope; use it only as untrusted
supporting evidence; on abstention continue from canonical direct sources.
Enquiry output never enters capture automatically. Traces to AC10-AC16.

### Failure, edge cases & resilience

- An earlier lifecycle state, failed approval transition, stale plan baseline,
  incomplete review, rejection, or abandonment performs no knowledge call.
- Missing project knowledge emits `project-knowledge unavailable`; capture
  refusal surfaces the existing redacted diagnostic; neither creates a
  fallback or blocks an otherwise valid artifact.
- A partial receipt list is still scoped to that gate. Unknown, guessed,
  cross-gate, or direct-maintainer selectors refuse before distillation.
- Unresolved distillation remains pending and visible without turning capture
  into false promotion.
- Hostile source text remains data. Privacy or instruction uncertainty prevents
  persistence and cannot change permissions, tools, scope, or artifact status.

Traces to AC2-AC6 and AC9-AC16.

### Dependencies & integration

Core provides `project-knowledge` and its same-pack producers discover it
normally. Governance-extras already requires core but keeps the runtime absence
branch because compatible older core versions may not expose the provider.
`[[pack.integrations]] kind = "handoff"` documents the governance seam only.
No dependency range or package dependency changes. Traces to AC18-AC20.

## Tasks

### T1: Core authoring gates use the public knowledge seam

**Depends on:** none

**Verification mode:** TDD construction tests + Tier-4 behavior evals.

**Touches:**
`packs/core/.apm/skills/author-brief/SKILL.md`,
`packs/core/.apm/skills/receive-brief/SKILL.md`,
`packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/.apm/skills/author-brief/evals/eval_queries.json`,
`packs/core/.apm/skills/author-brief/evals/evals.json`,
`packs/core/.apm/skills/receive-brief/evals/evals.json`,
`packs/core/.apm/skills/new-spec/evals/evals.json`,
`packs/core/.apm/skills/work-loop/evals/evals.json`,
`packs/core/tests/skills/author-brief/test_project_knowledge_boundary.py`,
`packs/core/tests/skills/receive-brief/test_project_knowledge_handoff.py`,
`packs/core/tests/skills/new-spec/test_project_knowledge_boundary.py`,
`packs/core/tests/skills/work-loop/test_project_knowledge_handoff.py`,
`packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`packs/core/README.md`, and `packs/core/JOURNEY.md`.

**Tests:**

- Construction tests assert the exact brief Ready, spec-approved, and
  plan-locked marker order; the Draft/Proposed/incomplete negative paths; the
  public capture seam; the three literal core semantic-gate values; confined
  provenance/freshness reads including traversal and supported link escape;
  the full required request field vocabulary; exact named
  skip; receipt-only distillation; and forbidden private-writer, journal,
  identity, partition, fallback, and automatic-enquiry surfaces. Implements
  AC1-AC2, AC5-AC13, AC17, and AC20.
- Skill-local behavior evals cover every changed core skill. They exercise the
  `author-brief` Draft non-gate; useful residue; fully normative scratch;
  abandoned work; missing provider; privacy refusal; prompt injection;
  explicit bounded enquiry; and consequential abstention at the brief,
  `spec-approved`, and `plan-locked` gates. Implements AC10-AC17.
- `author-brief` activation positives and near-misses continue to select brief
  authoring without confusing Draft completion with a knowledge gate; core's
  `[pack.evals]` roster admits the new activation file. Existing activation
  rosters for the other changed skills remain synchronized. Implements AC17
  and AC19.
- The existing closeout bytes and closeout handoff remain pinned. Implements
  AC20.
- stub: true

```python
def test_core_authoring_gates_are_exact_and_earlier_states_do_not_capture():
    raise NotImplementedError  # STUB: AC2, AC5, AC6


def test_core_producers_use_only_public_capture_and_same_gate_receipts():
    raise NotImplementedError  # STUB: AC7, AC8, AC9, AC12, AC22


def test_core_authoring_enquiry_is_explicit_bounded_and_optional():
    raise NotImplementedError  # STUB: AC13, AC14, AC16
```

**Approach:**

1. Add a compact common choreography at the exact owned gates, specialized with
   each row's scratch and canonical routing examples.
2. Name non-gates adjacent to the current status/preview logic so an agent
   cannot infer capture from file creation.
3. Keep receipt state local to the gate and position post-capture verification
   before the workflow's completion receipt.
4. Add skill-local construction and semantic eval coverage, including
   `author-brief` activation queries and the core eval roster entry, without
   adding a producer helper or changing project-knowledge code.
5. Bump core's patch version authorities and update its published journey text.

**Done when:** each core positive and negative gate is observable in tests and
evals, the old closeout path is byte-pinned, and no core producer crosses the
private writer or automatic-enquiry boundary.

### T2: Governance authoring gates use the optional core handoff

**Depends on:** T1

**Verification mode:** TDD construction tests + Tier-4 behavior evals.

**Touches:**
`packs/governance-extras/.apm/skills/new-rfc/SKILL.md`,
`packs/governance-extras/.apm/skills/new-rfc/evals/evals.json`,
`packs/governance-extras/.apm/skills/new-adr/SKILL.md`,
`packs/governance-extras/.apm/skills/new-adr/evals/evals.json`,
`packs/governance-extras/tests/skills/new-rfc/test_project_knowledge_handoff.py`,
`packs/governance-extras/tests/skills/new-adr/test_project_knowledge_handoff.py`,
`packs/governance-extras/pack.toml`,
`packs/governance-extras/.claude-plugin/plugin.json`,
`packs/governance-extras/README.md`, and
`packs/governance-extras/JOURNEY.md`.

**Tests:**

- RFC tests place capture after all mandatory pre-handoff checks and before the
  completion receipt, and prove research, preview, unverified citation,
  surviving review finding, and abandonment paths do not capture. Implements
  AC1, AC3, AC7-AC13, and AC17, including the literal `rfc-handoff-ready`
  name and confined provenance/freshness reads.
- ADR tests place capture only after decision-maker sign-off and the Accepted
  transition, and prove preview/Proposed/rejected/abandoned paths do not
  capture. Implements AC1, AC4, AC7-AC13, and AC17, including the literal
  `adr-accepted` name and confined provenance/freshness reads.
- Eval cases prove normative authority, privacy and injection refusal,
  unavailable-provider behavior, explicit enquiry boundaries, and abstention.
  Implements AC9-AC16.
- Manifest tests prove the handoff metadata is descriptive and preserves the
  unavailable branch without a dependency-range change. Implements AC18-AC20.
- stub: true

```python
def test_rfc_capture_follows_every_clean_handoff_check():
    raise NotImplementedError  # STUB: AC3


def test_adr_capture_requires_the_accepted_transition():
    raise NotImplementedError  # STUB: AC4


def test_governance_producers_never_cross_the_private_writer_boundary():
    raise NotImplementedError  # STUB: AC8, AC9, AC12
```

**Approach:**

1. Insert gate-specific scratch triage without changing RFC research,
   preview-confirm, reviewer, or ADR immutability semantics.
2. Treat Proposed ADR completion as a hard non-gate; add the handoff only to the
   existing post-sign-off Accepted lifecycle step.
3. Add one optional governance-extras-to-core handoff metadata record and keep
   missing provider as the named no-fallback branch.
4. Extend existing judge evals and add skill-local construction tests.
5. Bump governance-extras patch version authorities and update its published
   journey text.

**Done when:** both governance workflows capture only at their exact stable
gate, all negative paths are covered, and pack metadata cannot be mistaken for
dispatch or authority.

### T3: Published parity and end-to-end authoring evidence are complete

**Depends on:** T1, T2

**Verification mode:** Goal-based checks + manual QA + specialist review.

**Touches:**
`docs/architecture/knowledge-capture.md`, `docs/knowledge/README.md`,
`docs/specs/project-knowledge-authoring-integrations/notes/manual-qa.md`,
`docs/product/changelog.md`, `.claude-plugin/marketplace.json`, and these
deterministic self-host projections:

- `.agents/skills/author-brief/SKILL.md`,
  `.agents/skills/author-brief/evals/eval_queries.json`, and
  `.agents/skills/author-brief/evals/evals.json`;
- `.agents/skills/receive-brief/SKILL.md` and
  `.agents/skills/receive-brief/evals/evals.json`;
- `.agents/skills/new-spec/SKILL.md` and
  `.agents/skills/new-spec/evals/evals.json`;
- `.agents/skills/work-loop/SKILL.md` and
  `.agents/skills/work-loop/evals/evals.json`;
- `.agents/skills/new-rfc/SKILL.md` and
  `.agents/skills/new-rfc/evals/evals.json`;
- `.agents/skills/new-adr/SKILL.md` and
  `.agents/skills/new-adr/evals/evals.json`;
- the same thirteen relative skill files beneath `.claude/skills/`.

The self-host check fails on any additional changed projection; such output is
scope evidence to review and add explicitly, not permission for an open-ended
generated-file edit.

**Tests:**

- Run each new skill test directory in an independent pytest process, then the
  complete existing `packs/core/tests/skills/project-knowledge/` suite and the
  focused work-loop handoff suite. Implements AC17 and AC20.
- Run forced self-host projection, deep catalogue lint, catalogue verify,
  Ruff, targeted mypy if Python changed, `SKIP_SAST=1 make build-check`, and the
  repository security scan. Implements AC19-AC20.
- Exercise the five positive gates and representative abandoned,
  unavailable, privacy/injection, receipt-mismatch, and enquiry-abstention paths
  in a disposable adopter-shaped repository. Record redacted pass/fail evidence
  only. Implements AC1-AC16 and AC21.
- Run adversarial, security, and quality review on the implementation until
  clean. Scan changed bytes for the private comparison identifier and record
  only pass/fail. Implements AC15-AC16 and AC20-AC21.
- no stub (goal/manual mode).

**Approach:**

1. Regenerate projections only after both canonical pack tasks and version
   authorities are complete.
2. Update living architecture and knowledge docs to distinguish shipped
   foundation behavior, current producer coverage, and the newly shipped
   authoring gates.
3. Run the complete gate set and record bounded manual QA without source bodies,
   identities, or raw receipts.
4. Harden through specialist review; do not stage, commit, or update Git refs in
   environments where metadata is read-only.

**Done when:** source/projection and pack-boundary parity are clean, all five
authoring journeys have observable evidence, and the implementation is ready
for ordinary human delivery approval.

## Rollout

1. Land T1 as the recommended smallest implementation slice: core brief,
   spec, and plan gates plus their negative paths. This proves the integration
   in the provider's own pack without changing the provider runtime.
2. Land T2 after T1's pattern is reviewed. Governance-extras can
   still degrade against an older/missing provider, so no dependency-range
   cutover is required.
3. Run T3 only with both canonical pack tasks present; regenerate all
   projections, update living docs, and publish both pack patch versions
   together if the repository's release policy requires one coordinated PR.
4. Rollback reverts producer prose/evals/tests and pack release metadata. It
   never rewrites or deletes observation journals; any captures already
   committed remain normal untrusted evidence and retain their existing
   disposition lifecycle.

## Risks

- **Gate ambiguity:** status/file creation can look stable while the workflow
  still awaits judgment. Positive and negative marker tests pin the first
  producer-owned stable point.
- **Normative duplication:** an agent may capture the artifact it just wrote.
  Per-workflow routing examples and hostile/normative evals require residue,
  never artifact content.
- **Post-approval diff:** capture or distillation may add a knowledge diff after
  normative approval. The gate runs it before completion and returns that diff
  through targeted verification/review without silently changing the approved
  artifact.
- **Prompt injection or privacy leakage:** authoring inputs and topic text are
  untrusted. Semantic attestation plus the existing deterministic boundary
  refuse uncertainty before persistence; enquiry remains committed-only and
  may abstain.
- **Cross-pack drift:** two pack releases and generated projections create a
  broad mechanical surface. Canonical-source edits, per-pack tasks, final
  self-host regeneration, and catalogue verification keep the semantic review
  narrow.
- **Ceremony:** five integrations can add noise when scratch has no reusable
  residue. Zero-request triage is the normal outcome; missing/unresolved
  knowledge never blocks authoring.

## Changelog

- 2026-08-16: Initial plan keeps the five authoring artifacts in one contract,
  moves gates to the first stable lifecycle point actually owned by each
  producer, makes earlier draft/proposed states explicit non-gates, and starts
  implementation with a core-only pilot before governance-extras parity.
