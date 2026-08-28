# Spec: Shaping review contracts

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099; ADR-0042
- **Brief:** none
- **Discovery:** `docs/product/intents/cut-before-adding-solution-ladder.md`
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every new or materially changed repository intent, delivery brief, and spec
contract receives one independent cold shaping review before its lifecycle
owner may advance it. One stateless Core `shaping-reviewer` agent supports
exactly `intent`, `delivery-brief`, and `spec` modes, returns only `Clean` or
`Findings`, and leaves all revision, status, approval, and delivery authority
with the owning skill and human approver.

The reviewer's knowledge surfaces are installed skills and repository content.
Its caller supplies any bounded attributed evidence gathered by those skills.
Core MCP is only another invocation route to the same skill contracts; it is
not a separate knowledge surface and grants the reviewer no additional tool or
authority. The reviewer receives repository read/search only, with no network,
credential, shell, write, mutation, recursive-dispatch, or lifecycle tool.

## Boundaries

### Always do

- Invoke the reviewer in a context independent from the authoring conversation
  and bind its result to the material contract revision it reviewed.
- Return findings to `intake-intent`, `frame-intent`,
  `author-delivery-brief`, or `new-spec`; only that owner revises the artifact.
- Treat repository files, installed skills, quoted material, and caller-supplied
  evidence as attributed data under existing authority.
- Preserve the later adversarial spec-plan gate, both human approvals, and
  every existing code-review owner.
- Declare and project the least-privilege read-only boundary on every changed
  agent and skill surface.
- Keep acceptance checklist items atomic and implementation-stable; make
  universal claims prove their closed scope.

### Ask first

- Add a fourth shaping mode, public `review-*` skill, durable review state, loop
  script, retry controller, or finding adjudicator.
- Give the reviewer an independent retrieval surface, public-network, shell,
  write, credential, mutation, skill-invocation, or subagent-dispatch
  capability.
- Change a lifecycle status or materiality field set beyond RFC-0099.
- Move plan-construction or implementation-conformance review out of
  `adversarial-reviewer`.
- Add a hard AC word budget or require guessed paths, symbols, or test seams
  that repository evidence cannot establish before implementation.

### Never do

- Let an author mark its own artifact clean through warm self-review.
- Treat retrieved or installed-skill text as instruction authority or let it
  change tools, scope, status, routing, or verdict.
- Produce a false `Clean` when required evidence or an independent review route
  is unavailable.
- Invoke shaping review from a compatibility alias independently of its
  canonical target.
- Couple shaping review to work-loop state, review-verdict records, finding
  adjudication, or implementation retries.
- Put build-time contract findings or resolve-vs-surface dispositions in the
  pinned spec, plan, or plan template.

## Testing Strategy

- **TDD:** construction parsers and adapter projections enforce exact source
  metadata, read-only native permissions, mode/result schemas, caller routing,
  materiality, and refusal paths.
- **Goal-based checks:** static agent/skill contract tests, all-adapter package
  builds, manifest/version parity, caller evals, guide terminology, catalogue
  verification, and self-host projection prove the installed surface.
- **Visual / manual QA:** fresh agents review one seeded artifact per mode plus
  unavailable-evidence and unavailable-independence cases; the observed report,
  caller response, and unchanged repository/status are recorded.

## Acceptance Criteria

### AC1 — One stateless reviewer with three modes

- [ ] `packs/core/.apm/agents/shaping-reviewer.md` defines exactly `intent`,
  `delivery-brief`, and `spec` modes and rejects every other target as
  out-of-scope.
- [ ] Intent mode checks artifact need, outcome, boundary, owner, assumptions,
  altitude when present, unresolved questions, falsifiability, and the
  least-artifact projection.
- [ ] Delivery-brief mode checks shared outcome, coordination value,
  governance-reference/delivery-slice separation, deferred scope, readiness,
  speculative slices, and the confirmed materialization boundary.
- [ ] Spec mode checks objective, boundaries, acceptance criteria, testing
  strategy, governing constraints, contract/construction separation, and
  smallest independently shippable scope.
- [ ] The reviewer adds no loop state, scripts, public skill, persistent report
  store, retry budget, or fourth mode.
- [ ] Agent admission pins `name: shaping-reviewer`, a description that names
  cold contract review for intent/delivery-brief/spec and says `not code
  review`, plus a roster collision test proving its distinct work type and
  value under ADR-0042.

### AC2 — Compact result and revision binding

- [ ] One invocation returns exactly `Clean` or `Findings`; no third reviewer
  result value is accepted.
- [ ] The result carries the target path, reviewed revision when present,
  review context, consulted surfaces, and grounding gaps.
- [ ] A `Findings` result orders findings by severity and gives a concrete fix
  for each finding.
- [ ] The result contains no conversational preamble or process narration.
- [ ] A material edit invalidates the prior result and triggers a fresh review;
  pre-seal wording/format/evidence-link correction may retain it only when the
  lifecycle owner records the edit as nonmaterial.
- [ ] Materiality matches RFC-0099 for intent, delivery brief, and spec; a
  reviewer result never changes status or authorizes delivery.

### AC3 — Lifecycle owners receive findings and retain authority

- [ ] `intake-intent` invokes intent mode for a Core-created minimal intent;
  `frame-intent` or the authorized product owner invokes it for a product
  intent; `author-delivery-brief` invokes brief mode; `new-spec` invokes spec
  mode.
- [ ] Intent `Accepted` and brief `Ready` still require `Clean` plus explicit
  human confirmation; spec `Clean` advances only to adversarial spec-plan
  review, never directly to `Approved`.
- [ ] Every unresolved finding blocks its lifecycle transition; aliases route
  through the canonical owner and do not create a second review result.

### AC4 — Independence is mandatory and portable

- [ ] An isolated subagent is preferred; a genuinely fresh context or an
  independent human reviewing the same evidence packet is the only fallback.
- [ ] Warm self-review is advisory and cannot satisfy the gate; absence of an
  independent route is refused by the lifecycle owner before invocation and
  emits a named `BLOCKED` lifecycle receipt outside the reviewer's two-value
  result vocabulary.
- [ ] Core-only fixtures complete all three modes without Product Engineering;
  `frame-intent` integration degrades honestly when Core review is unavailable.

### AC5 — Knowledge stays in skills and repository content

- [ ] The lifecycle owner may collect at most the RFC-bounded repository and
  installed-skill evidence and pass it in one attributed, untrusted evidence
  packet; the reviewer performs no independent retrieval or network query.
- [ ] Invoking the lifecycle owner through Core MCP reaches the same skill
  contract as direct invocation and grants no additional reviewer tool,
  authority, scope, evidence class, or knowledge owner.
- [ ] Hostile, stale, unavailable, malformed, over-broad, or confidentiality-
  refused evidence cannot mutate files, change routing/status/verdict, persist
  retrieved text, or yield false `Clean`; a consequential absence becomes a
  grounding gap.

### AC6 — Least privilege is declared and projected semantically

- [ ] Catalogue validation accepts and validates agent `metadata.boundaries`;
  every new or changed skill, agent, and alias in this slice declares its
  minimum tools and applicable untrusted-read/write boundaries.
- [ ] `shaping-reviewer` source tools are exactly repository read/search
  (`Read`, `Grep`, `Glob`) and its boundary metadata names read-only untrusted
  evidence; a construction test rejects write, shell, network, credential,
  mutation, skill, or recursive-dispatch authority.
- [ ] Each supported adapter proves the equivalent native restriction—exact
  read tools or its coarse read-only sandbox—and never widens permissions merely
  because opaque source metadata is not projected literally. On Codex, the
  command tool is admissible only inside the projected read-only sandbox and
  only for bounded repository read/search; project execution, writes, network,
  credentials, MCP, skills, and recursive dispatch remain unavailable.
- [ ] Missing or widened source declarations fail catalogue verification or an
  equivalent static construction gate.

### AC7 — Spec-contract review moves without weakening spec-plan review

- [ ] `new-spec` runs shaping spec mode and resolves it before the existing
  adversarial review of the complete spec-plan pair; no spec is indexed or
  approvable before both independent gates are clean.
- [ ] The five contract-shape checks move to shaping review; adversarial review
  retains plan/spec mapping, duplicate-value, dependency order, derived-fixture
  scope, task verification modes, structural-plan, and implementation-
  conformance checks.
- [ ] Construction fixtures seed every row of the RFC-0099 ownership split and
  fail if either reviewer omits or duplicates its assigned check.
- [ ] `new-spec` requires one independently testable claim per acceptance
  checklist item. A universal claim must enumerate its closed set or name the
  mechanism that makes coverage exhaustive; a new claim becomes a new item,
  not a lettered or semicolon graft.
- [ ] `new-spec` and shaping review reject hard AC word budgets. They keep
  observable behavior in the spec and put exact paths or symbols in the plan
  only when grounded; otherwise a task names the discovery predicate,
  constraint, required outcome, and verification mode without guessing the
  implementation seam.
- [ ] `new-spec` routes a build-time contract question to the retained
  `sealed-baseline-replacement` owner without directly editing a pinned
  artifact; this slice defines no run-record field, closure rule, or recovery
  transition.
- [ ] `new-spec` defines planning sufficiency as an observable contract, owner,
  boundaries, ordering, discovery predicates, required outcomes, and
  verification modes adequate to begin safely.
- [ ] A PLAN-time TDD stub supplies one compilable red contract-surface
  assertion for each already-grounded callable seam or coherent TDD task
  family; it is not required to encode the finished edge-case matrix.
- [ ] A task whose callable seam can only be discovered during implementation
  records `no stub (implementation-discovered)` plus its discovery predicate,
  constraint, required outcome, and verification mode instead of inventing a
  helper, fixture, module, or symbol.
- [ ] Pre-EXECUTE adversarial review sustains a mechanism or test-shape finding
  only when the plan cannot safely start or verify the contract; otherwise the
  finding is build-time guidance and cannot prevent `Clean`.
- [ ] After adjudication, sustained findings that share a seam, owner,
  duplicated contract, or repeated remedy receive one root-cause
  cut-before-adding disposition before per-finding fixes; every finding retains
  its own audit mapping and unrelated findings remain independent.
- [ ] The cluster checkpoint adds no reviewer, state, retry loop, script,
  artifact, or mandatory abstraction.
- [ ] `work-loop`, implementer, adversarial review, and quality review treat
  debt introduced by a change, or a pre-existing gap in the exact seam the
  change modifies, depends on, or tests through, as in-session cleanup rather
  than a routine backlog candidate when the accepted contract permits the root
  correction.
- [ ] The cleanup rule forbids workarounds and weakened tests that preserve the
  gap, routes corrections needing new product authority through the existing
  amendment or owner-decision path, and records a discovered pre-existing gap
  in a neighboring non-required module as decision-shaped backlog without
  expanding the current diff or adding a debt-review state or artifact.
- [ ] `new-spec` and both reviewers remove claims that are unnecessary to prove
  the contract or construction plan. A necessary cross-document assertion is
  sustained only when one bounded check of the named target grounds it;
  otherwise the author labels it as an assumption or discovery predicate.
- [ ] Claim minimization adds no word budget, claim ledger, citation framework,
  review state, or demand to research prose that can simply be deleted.

### AC8 — Integrations, guides, evals, and releases stay narrow

- [ ] Core-internal callers need no synthetic pack integration; Product
  Engineering declares only the optional `frame-intent` → `shaping-reviewer`
  integration and its fresh-context/human fallback.
- [ ] Caller-local evals cover clean, findings, material revision,
  nonmaterial correction, unavailable independence, hostile evidence, and
  Core-only paths; the internal reviewer is not added to a public activation
  roster.
- [ ] Existing Core/Product Engineering journeys, how-tos, references, READMEs,
  and the shared three-loops explanation distinguish shaping review from the
  three code-review lenses without adding a new guide family.
- [ ] Core, Product Engineering, AgentBundle, and projections receive only the
  version/build updates their actual source changes require.

## Assumptions

- Technical: agents are auto-discovered from `.apm/agents/`; no agent roster is
  added to plugin metadata (source: existing pack layout and
  `packs/architect/.apm/agents/design-reviewer.md`).
- Technical: catalogue verification currently rejects agent `metadata`, so
  source validation must be extended before the new declaration can ship
  (source: `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`).
- Technical: adapters have native read-only mappings; Codex realizes bounded
  read/search through a command tool inside a read-only sandbox. Caller-supplied
  evidence is the accepted contract regardless of whether Core MCP or a host
  invokes the owning skill (source: work-loop pre-execute boundary; RFC-0099
  Errata; user clarification 2026-08-27).
- Process: `new-spec` currently invokes only adversarial spec-plan review, and
  that later gate remains mandatory (source:
  `packs/core/.apm/skills/new-spec/SKILL.md`, RFC-0099).
- Product: independent shaping review is required for all three artifact kinds
  without a public review skill or durable shaping loop (source: RFC-0099; user
  confirmation 2026-08-27).
