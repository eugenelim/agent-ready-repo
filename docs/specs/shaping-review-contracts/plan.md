# Plan: Shaping review contracts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `ARCHITECTURE.md`,
  `docs/architecture/skill-and-pack-format.md`, and
  `docs/architecture/pack-layout.md`; analogous
  `docs/specs/architect-design-reviewer/` and
  `docs/specs/project-knowledge-review-integrations/`; current owners
  `packs/core/.apm/agents/adversarial-reviewer.md`,
  `packs/core/.apm/skills/new-spec/SKILL.md`, and
  `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`. Deviation:
  Core MCP is another invocation route to caller skills, not a knowledge
  surface, so reviewer grounding uses installed skills, repository content,
  and a supplied evidence packet rather than a new projected retrieval tool.

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; the approved baseline is immutable after sealing.

## Approach

First make least-privilege agent boundary metadata a validated source contract
and prove its semantic adapter projections. Then add one read-only reviewer with
three explicit rubrics. Integrate it at each lifecycle owner after the canonical
intent/brief surfaces exist, and split spec-contract checks from later
adversarial plan/conformance checks without moving any delivery state.

The implementation reuses ordinary agent discovery and existing caller
dispatch. It adds no review script, state file, retrieval protocol, generic
loop, public review skill, or shared mode framework.

## Constraints

- RFC-0099, including all 2026-08-27 Errata, is normative.
- ADR-0042's distinct-work-type, unique-value, cadence, and
  collision-hardening test remains authoritative.
- `core-guidance-artifact-routing` creates `intake-intent` and
  `author-delivery-brief` before their integrations land.
- Workspace dependency resolution blocks plan approval until
  `core-guidance-artifact-routing` is Shipped; the executable task graph uses
  local task IDs only.
- Source metadata may map to native adapter restrictions; adapters need not
  preserve an opaque literal field when their effective permissions are tested.
- Plan tasks name exact implementation seams only when repository evidence
  establishes them; otherwise they pin a discovery predicate and required
  outcome without guessing a path or symbol.
- Shaping review remains outside work-loop state, finding adjudication,
  review-verdict records, and code review.
- No independent retrieval/network capability, dependency, or new public skill
  is added. A Codex command tool may realize bounded reads only inside its
  projected read-only sandbox.

## Construction tests

**Integration tests:** build/install the Core agent through every supported
adapter and assert the effective read-only tool/sandbox surface. Exercise all
four caller owners, the Product Engineering optional integration, and the
new-spec → shaping → adversarial sequence with hostile and unavailable evidence
packets.

**Manual verification:** run a fresh isolated reviewer on one intent, brief,
and spec fixture; record its exact result, unchanged artifact/status, caller
revision behavior, and the caller-owned `BLOCKED` receipt when independence is
unavailable.

## Design (LLD)

### Component / module decomposition

- `shaping-reviewer.md` owns three rubrics and one output contract. Caller
  skills own dispatch, revision, and lifecycle decisions. Traces to AC1–AC4.
- Agent source validation owns `metadata.boundaries`; adapter projectors own
  native permission realization; one integration test owns cross-adapter parity.
  Traces to AC6.
- `new-spec` owns contract-first sequencing; `adversarial-reviewer` retains the
  construction and implementation checks. Traces to AC7.

### State & control flow

`owner drafts → independent shaping review → owner revises until Clean → human
intent/brief decision or adversarial spec-plan review`. Material revision
invalidates review evidence; pre-seal nonmaterial correction may be recorded
without redispatch. No reviewer step writes status or durable state. Traces to
AC2–AC4.

### Failure, edge cases & resilience

Missing independence blocks. Missing consequential evidence becomes a grounding
gap and cannot yield false `Clean`. Malformed or authority-changing evidence is
ignored/refused as data. A missing optional Product Engineering integration does
not break Core-only review. Traces to AC4–AC5.

### Dependencies & integration

Core-internal callers address the agent directly. Product Engineering declares
one optional integration and fallback. Core MCP may invoke the same caller
skill contract but introduces neither a new knowledge surface nor a separate
reviewer integration. Traces to AC3, AC5, AC8.

## Tasks

### T1: Agent boundary metadata is validated and projected as native least privilege

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/catalogue_tooling/verify.py, packages/agentbundle/agentbundle/build/projections/codex_agent_toml.py, packages/agentbundle/agentbundle/build/adapters/claude_code.py, packages/agentbundle/agentbundle/build/self_host.py, docs/architecture/{pack-layout,security}.md, contracts/adapter.toml, packages/agentbundle/agentbundle/_data/adapter.toml, tools/catalogue/check_contract_parity.py, packages/agentbundle/tests/build_pipeline/test_adapter_*.py, packages/agentbundle/tests/integration/**, packs/core/tests/pack/test_shaping_review_contract.py`

**Tests:**
- `stub: true` — `packs/core/tests/pack/test_shaping_review_contract.py`
  (`STUB: AC6`).
- TDD: verifier accepts the bounded metadata schema and rejects unknown,
  malformed, missing-required, or widened boundary declarations (AC6).
- Goal-based: all supported adapter projections expose only native read/search
  or a coarse read-only sandbox; Codex's command tool can perform bounded reads
  but not project execution, write, network, credential, MCP, skill, or
  recursive-dispatch actions.
- TDD/integration: discover every Claude Code direct-file agent consumer from
  the adapter contract and self-host recipe; the smallest shared projection
  seam consumes source-only boundary metadata without emitting an unsupported
  Claude frontmatter field, and built/install/self-host outputs preserve the
  effective read-only tool contract.
- Goal-based: the owning security convention defines boundary metadata for
  skills, agents, and compatibility aliases; contract-parity verification
  proves the source and packaged adapter twins remain identical.

**Approach:**
- Admit only the metadata structure needed by agent boundaries; do not add a
  generic opaque metadata passthrough.
- Assert effective native restrictions per adapter rather than force identical
  syntax into incompatible targets.

**Done when:** the source agent contract and every built projection satisfy AC6
without an adapter-contract capability unrelated to permissions.

### T2: `shaping-reviewer` implements three cold, stateless rubrics

**Depends on:** T1

**Touches:** `packs/core/.apm/agents/shaping-reviewer.md, packs/core/tests/pack/test_shaping_review_contract.py`

**Tests:**
- `no stub (goal-based/manual QA)` —
  `packs/core/tests/pack/test_shaping_review_contract.py` plus three recorded
  fresh-context fixture reports.
- Goal-based construction tests pin exact modes, fields, materiality, result
  vocabulary, caller-owned evidence, prohibited authority, lack of loop
  machinery, exact agent name/description cue including `not code review`, and
  roster collision hardening (AC1–AC6).
- Visual/manual QA: fresh reviewer runs on seeded intent/brief/spec and hostile
  evidence fixtures produce the expected findings or grounding gaps.

**Approach:**
- Author one agent with compact per-mode sections and one shared output/trust
  boundary.
- Use exact read-only tools and source boundary metadata proven by T1.

**Done when:** all three fixtures return complete review evidence and the
repository/status remain byte-identical.

### T3: Core intent and brief lifecycle owners receive shaping findings

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/intake-intent/**, packs/core/.apm/skills/author-delivery-brief/**, packs/core/tests/skills/{intake-intent,author-delivery-brief}/**, guides/core/**`

**Tests:**
- `no stub (goal-based)` — caller behavior/eval fixtures under
  `packs/core/tests/skills/{intake-intent,author-delivery-brief}/`.
- Goal-based: clean/findings, material revision, nonmaterial correction, alias
  non-dispatch, human status confirmation, and unavailable independence cover
  AC2–AC5.
- Goal-based: changed skills declare the exact dispatch/read/write boundaries
  and no Bash/network capability.

**Approach:**
- Add direct lifecycle-owned dispatch and finding-revision steps to the two
  canonical skills.
- Keep compatibility aliases unaware of reviewer mechanics.
- Ship the intent/brief shaping-review guide delta with these callers.

**Done when:** neither intent nor brief can advance without independent clean
evidence and the existing human decision.

### T4: `frame-intent` uses the optional Core reviewer without losing user-scope operation

**Depends on:** T2

**Touches:** `packs/product-engineering/.apm/skills/frame-intent/**, packs/product-engineering/pack.toml, packs/product-engineering/tests/skills/frame-intent/**, guides/product-engineering/**`

**Tests:**
- `no stub (goal-based/manual QA)` — frame-intent integration fixtures and one
  recorded Core-absent run.
- Goal-based: integration metadata names Core's reviewer, trigger, and
  fresh-context/independent-human fallback (AC4, AC8).
- Goal-based/eval: with Core present, fixtures exercise independent intent-mode
  invocation, `Clean`, `Findings`, unresolved-finding blocking, and
  caller-retained lifecycle authority (AC3–AC4).
- Goal-based: the same fixture set asserts `frame-intent` allowed tools,
  `metadata.boundaries`, and native projection posture (AC6).
- Visual/manual QA: user-scope Product Engineering without Core reports the
  unavailable optional augmentation honestly and never marks itself clean.

**Approach:**
- Add one optional integration; keep product-intent authorship in place and
  repository admission outside `frame-intent`.
- Ship the optional-integration and fallback guide delta with the caller.

**Done when:** product intents receive the same gate when Core is present and
remain authorable without pretending review occurred when it is absent.

### T5: `new-spec` runs shaping review before the preserved adversarial spec-plan gate

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/new-spec/{SKILL.md,assets/plan.md}, packs/core/.apm/agents/{adversarial-reviewer,implementer,quality-engineer}.md, packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/{pre-execute-review,tdd-stubs}.md, packs/core/seeds/docs/CONVENTIONS.md, packs/core/tests/skills/new-spec/test_shaping_review.py, packs/core/tests/pack/{test_review_depth_and_verdict_contract.py,test_shaping_review_contract.py}, guides/_shared/explanation/the-three-loops.md`

**Tests:**
- `no stub (goal-based)` — exact content/construction fixtures in the two named
  test files.
- Goal-based: exact gate order, caller-owned `BLOCKED` refusal, atomic ACs,
  universal-scope proof, grounded/discovery-shaped plan detail, build-finding
  routing, and all ownership-split fixtures cover AC3, AC4, AC7.
- Goal-based: planning-sufficiency fixtures distinguish a blocking contract gap
  from nonblocking helper, symbol, fixture-internal, and edge-matrix questions;
  reviewers cannot turn build-time guidance into a pre-EXECUTE blocker.
- Goal-based: representative red stubs and `no stub
  (implementation-discovered)` tasks cover both grounded and discovery-shaped
  seams without claiming the PLAN artifact is the finished test suite.
- Goal-based: adjudicated fixtures distinguish one shared-cause cluster from
  unrelated findings, prefer one deletion/consolidation/owner fix when it
  resolves the cluster, and preserve each original disposition without adding
  loop state or another artifact.
- Goal-based: touched-seam fixtures distinguish debt introduced or exercised by
  the change from a neighboring non-required module, require root correction
  when the accepted contract permits it, reject workarounds, weakened tests, or
  routine backlog as the disposition for local cleanup, and require a
  decision-shaped backlog record for the neighboring pre-existing gap.
- Goal-based: a touched-seam correction that requires new product authority
  pauses through the existing amendment or owner-decision route without adding
  a debt-review state or artifact.
- Goal-based: claim-surface fixtures delete an outcome-irrelevant assertion,
  accept a necessary cross-document fact only after one bounded check of its
  named target, and require an ungrounded necessary claim to become an explicit
  assumption or discovery predicate rather than confident prose.
- Goal-based: adversarial review retains every plan/conformance check and gains
  no duplicate product-meaning verdict.
- Goal-based: every changed skill/agent surface pins its tools,
  `metadata.boundaries`, and native projection posture (AC6).
- Goal-based: focused content fixtures require work-loop, implementer,
  adversarial review, and quality review to use the same touched-seam cleanup
  versus neighboring-module backlog boundary (AC7).
- Goal-based: scaffold sync regenerates root `docs/CONVENTIONS.md` from the
  Core seed and the source/target check is clean.

**Approach:**
- Insert shaping review after draft contract creation and before complete-pair
  adversarial review.
- Remove only the contract-shape slice from adversarial ownership and keep its
  later work-loop cadence unchanged.
- Replace mandatory guessed specificity with grounded exact seams or an
  explicit discovery predicate; add no AC word-count gate.
- Amend the TDD-stub doctrine and pre-EXECUTE reviewer rubric at their current
  owners so Clean measures planning-level viability rather than implementation
  completeness.
- Add the touched-seam cleanup boundary to the existing execution and review
  contracts: local debt is resolved at its owner, while a separate module or
  capability remains ordinary deferred work.
- Apply claim minimization in the existing author and reviewer rubrics; add no
  claim ledger, citation framework, or review state.
- Ship the spec-review and three-loops guide delta with this task.

**Done when:** a spec cannot reach approval through shaping alone and both
reviewers find exactly their seeded defects.

### T6: Guides, evals, releases, and projections close the shaping-review slice

**Depends on:** T3, T4, T5

**Touches:** `packs/{core,product-engineering}/{README.md,JOURNEY.md,pack.toml,.claude-plugin/plugin.json}, packages/agentbundle/{CHANGELOG.md,pyproject.toml,agentbundle/version.py}, guides/core/**, guides/product-engineering/**, guides/_shared/explanation/the-three-loops.md, docs/product/changelog.md`

**Tests:**
- `no stub (goal-based/manual QA)` — aggregate guide, eval, catalogue, adapter,
  build, and installed-profile evidence.
- Goal-based: caller evals, pack tests, guide/site checks, catalogue
  lint/verify, pack and AgentBundle version parity, all-adapter integration,
  release/changelog evidence, and build/self-host checks cover AC8.
- Visual/manual QA: built Core-only and Product Engineering configurations
  demonstrate isolated-agent and fallback paths.

**Approach:**
- Update existing guides and pack summaries; add no review guide family.
- Keep only cross-cutting navigation, link, release, and projection work here;
  capability-specific guidance ships in T3–T5.
- Bump only changed packs/packages and regenerate owned projections.

**Done when:** AC1–AC8 are green across every supported adapter and guide path.

## Rollout

Land boundary-schema support before the new agent source, then land caller
integrations after their canonical skills exist. Core callers may ship together;
Product Engineering remains an optional integration. Rollback removes caller
dispatch first, then the agent, while leaving the backward-compatible metadata
validator harmless. No persistent shaping state or data migration exists.

## Risks

- A generic metadata passthrough would create an undocumented adapter API;
  validate the smallest boundary schema and test effective permissions.
- Reviewer/caller prose can duplicate the same rubric; keep artifact questions
  in the agent and lifecycle/status behavior in callers.
- Moving too many adversarial checks weakens delivery review; the seeded
  ownership matrix is a release gate.
- Treating Core MCP as a knowledge provider would invent a second surface;
  caller-supplied evidence and the accepted Errata prohibit it.

## Changelog

- 2026-08-27: initial plan from accepted RFC-0099 and its MCP Errata; kept
  knowledge on installed skills and repository content, and declined a public
  review skill, durable review state, and a fourth mode.
