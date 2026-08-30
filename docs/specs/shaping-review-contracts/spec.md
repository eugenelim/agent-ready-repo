# Spec: Shaping review contracts

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099; ADR-0099; ADR-0042
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

Moving the contract-shape checks off `adversarial-reviewer` also settles what
each reviewer now owns: `new-spec`'s authoring rubric for acceptance-criterion
atomicity, planning sufficiency, and PLAN-time TDD stubs, and the pre-EXECUTE
reviewer's standard for what may block `Clean`. Execution-side RFC-0099 errata
are out of scope and recorded under Follow-ons.

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

- **TDD:** the source-metadata validator and the projection seam that strips it
  enforce exact boundary declarations.
- **Goal-based checks:** static agent/skill contract tests fix the mode and
  result schemas, caller routing, materiality, and refusal paths; all-adapter
  projections prove each target's read-only native permissions; package builds,
  manifest/version parity, caller evals, guide terminology, catalogue
  verification, and self-host projection prove the installed surface.
- **Stub tally:** two stubbed tasks — T1 (`STUB: AC6`, source-agent boundary
  validation) and T2 (`STUB: AC6`, the reviewer's own frontmatter contract). T3
  and T5 record `no stub (goal-based)`; T4 and T6 record
  `no stub (goal-based/manual QA)`.
- **Visual / manual QA:** fresh agents review one seeded artifact per mode plus
  unavailable-evidence and unavailable-independence cases; the observed report,
  caller response, and unchanged repository/status are recorded.

## Acceptance Criteria

### AC1 — One stateless reviewer with three modes

- [x] `packs/core/.apm/agents/shaping-reviewer.md` defines exactly `intent`,
  `delivery-brief`, and `spec` modes and rejects every other target as
  out-of-scope.
- [x] Intent mode checks artifact need, outcome, boundary, owner, assumptions,
  altitude when present, unresolved questions, core-only viability,
  falsifiability, and the least-artifact projection.
- [x] Delivery-brief mode checks shared outcome, coordination value,
  governance-reference/delivery-slice separation, deferred scope, readiness,
  speculative slices, and the confirmed materialization boundary.
- [x] Spec mode checks objective, boundaries, acceptance criteria, testing
  strategy, governing constraints, contract/construction separation,
  derived-fixture parent-scope exactness, and smallest independently shippable
  scope.
- [x] The reviewer adds no loop state, scripts, public skill, persistent report
  store, retry budget, or fourth mode.
- [x] Agent admission pins `name: shaping-reviewer`, a description that names
  cold contract review for intent/delivery-brief/spec and says `not code
  review`, plus a roster collision test proving its distinct work type and
  value under ADR-0042.

### AC2 — Compact result and revision binding

- [x] One invocation returns exactly `Clean` or `Findings`; no third reviewer
  result value is accepted.
- [x] The result carries the target path, reviewed revision when present,
  review context, consulted surfaces, and grounding gaps.
- [x] A `Findings` result orders findings by severity and gives a concrete fix
  for each finding.
- [x] The result contains no conversational preamble or process narration.
- [x] A material edit invalidates the prior result and triggers a fresh review.
- [x] A pre-seal wording, format, or evidence-link correction retains the prior
  result only when the lifecycle owner records that edit as nonmaterial.
- [x] Materiality matches RFC-0099 for intent, delivery brief, and spec.
- [x] A reviewer result never changes status or authorizes delivery.

### AC3 — Lifecycle owners receive findings and retain authority

- [x] `intake-intent` invokes intent mode for a Core-created minimal intent.
- [x] `frame-intent` or the authorized product owner invokes intent mode for a
  product intent.
- [x] `author-delivery-brief` invokes delivery-brief mode.
- [x] `new-spec` invokes spec mode.
- [x] Intent `Accepted` requires `Clean` plus explicit human confirmation.
- [x] Brief `Ready` requires `Clean` plus explicit human confirmation.
- [x] Spec `Clean` advances only to adversarial spec-plan review, never directly
  to `Approved`.
- [x] Every unresolved finding blocks its lifecycle transition.
- [x] A compatibility alias routes through its canonical owner and creates no
  second review result.

### AC4 — Independence is mandatory and portable

- [x] An isolated subagent is preferred; a genuinely fresh context or an
  independent human reviewing the same evidence packet is the only fallback.
- [x] Warm self-review is advisory and cannot satisfy the gate.
- [x] Absence of an independent route is refused by the lifecycle owner before
  invocation and emits a named `BLOCKED` lifecycle receipt outside the
  reviewer's two-value result vocabulary.
- [x] Core-only fixtures complete all three modes without Product Engineering.
- [x] `frame-intent` integration degrades honestly when Core review is
  unavailable.

### AC5 — Knowledge stays in skills and repository content

- [x] The lifecycle owner passes repository and installed-skill evidence in one
  attributed, untrusted evidence packet.
- [x] The reviewer performs no independent retrieval and issues no network
  query.
- [x] Hostile, stale, unavailable, malformed, over-broad, or
  confidentiality-refused evidence cannot mutate a file.
- [x] That same evidence cannot change routing, status, or verdict.
- [x] That same evidence cannot cause retrieved text to be persisted.
- [x] That same evidence cannot yield a false `Clean`.
- [x] A consequential absence of evidence becomes a recorded grounding gap.

### AC6 — Least privilege is declared and projected semantically

- [x] Catalogue validation accepts and validates a source agent's
  `metadata.boundaries`.
- [x] Every new or changed skill, agent, and alias in this slice declares its
  minimum tools.
- [x] Every new or changed skill, agent, and alias in this slice declares its
  applicable untrusted-read/write boundaries.
- [x] `shaping-reviewer` source tools are exactly repository read/search
  (`Read`, `Grep`, `Glob`).
- [x] Its boundary metadata names read-only untrusted evidence.
- [x] A construction test rejects write, shell, network, credential, mutation,
  skill, or recursive-dispatch authority on that agent.
- [x] Each supported adapter proves the equivalent native restriction—exact
  read tools or its coarse read-only sandbox.
- [x] No adapter widens permissions merely because opaque source metadata is
  not projected literally.
- [x] `shaping-reviewer` declares the source opt-out that suppresses a
  default-injected skill-resource glob.
- [x] Each adapter that injects such a glob by default asserts the suppression
  on the projected agent.
- [x] On Codex, the command tool is admissible only inside the projected
  read-only sandbox and only for bounded repository read/search.
- [x] On Codex, project execution, writes, network, credentials, MCP, skills,
  and recursive dispatch remain unavailable.
- [x] Missing or widened source declarations fail catalogue verification or an
  equivalent static construction gate.

### AC7 — Spec-contract review moves without weakening spec-plan review

- [x] `new-spec` runs shaping spec mode and resolves it before the existing
  adversarial review of the complete spec-plan pair.
- [x] An unresolved shaping finding blocks indexing and approval.
- [x] `new-spec` keeps its existing
  `adversarial-reviewer: no matching subagent installed; review skipped` note
  unchanged.
- [x] The Profile-A opt-out in
  `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` is
  unchanged.
- [x] The five contract-shape checks move to shaping review.
- [x] Adversarial review retains plan/spec mapping, duplicate-value, dependency
  order, derived-fixture scope, task verification modes, structural-plan, and
  implementation-conformance checks.
- [x] Construction fixtures seed every row of the RFC-0099 ownership split and
  fail when a row has no owning reviewer.
- [x] A row RFC-0099 assigns to both reviewers passes only when each reviewer
  applies it to its own target; that dual assignment is not a duplicate.
- [x] `new-spec` requires one independently testable claim per acceptance
  checklist item.
- [x] A universal claim enumerates its closed set or names the mechanism that
  makes coverage exhaustive.
- [x] A new claim becomes a new checklist item, not a lettered or semicolon
  graft.
- [x] `new-spec` and shaping review reject hard AC word budgets.
- [x] They keep observable behavior in the spec.
- [x] They put exact paths or symbols in the plan only when grounded.
- [x] An ungrounded task instead names the discovery predicate, constraint,
  required outcome, and verification mode without guessing the implementation
  seam.
- [x] `new-spec` routes a build-time contract question to the owner of the
  pinned build artifact without directly editing that artifact. The route is
  stated portably: `packs/AGENTS.md` bars shipped pack content from citing this
  catalogue's internal records, so the shipped skill must not name the
  `sealed-baseline-replacement` spec, which resolves to nothing in an installed
  tree.
- [x] This slice defines no run-record field, closure rule, or recovery
  transition.
- [x] `new-spec` defines planning sufficiency as an observable contract, owner,
  boundaries, ordering, discovery predicates, required outcomes, and
  verification modes adequate to begin safely.
- [x] A PLAN-time TDD stub supplies one compilable red contract-surface
  assertion for each already-grounded callable seam or coherent TDD task
  family; it is not required to encode the finished edge-case matrix.
- [x] A task whose callable seam can only be discovered during implementation
  records `no stub (implementation-discovered)` plus its discovery predicate,
  constraint, required outcome, and verification mode instead of inventing a
  helper, fixture, module, or symbol.
- [x] Pre-EXECUTE adversarial review sustains a mechanism or test-shape finding
  only when the plan cannot safely start or verify the contract; otherwise the
  finding is build-time guidance and cannot prevent `Clean`.

### AC8 — Integrations, guides, evals, and releases stay narrow

- [x] Core-internal callers need no synthetic pack integration.
- [x] Product Engineering declares only the optional `frame-intent` →
  `shaping-reviewer` integration and its fresh-context/human fallback.
- [x] Caller-local evals cover clean, findings, material revision, nonmaterial
  correction, unavailable independence, hostile evidence, and Core-only paths.
- [x] The internal reviewer is absent from the subagent list in
  `packs/core/docs/index.md`, while a sentence outside that list distinguishes
  shaping review from the three code-review lenses.
- [x] These eight documents distinguish shaping review from the three
  code-review lenses: `guides/_shared/explanation/the-three-loops.md`,
  `guides/core/explanation/core-pack.md`,
  `guides/core/how-to/plan-and-execute-non-trivial-work.md`,
  `guides/core/how-to/review-someone-elses-pr.md`, `packs/core/DESIGN.md`,
  `packs/core/docs/index.md`, `packs/core/JOURNEY.md`, and
  `packs/core/seeds/docs/CONVENTIONS.md`. This enumeration is the closed set;
  no search predicate stands behind it. Documents outside `packs/core/`,
  `guides/core/`, and that one shared explanation are out of scope for this
  slice even when they name the lenses — among them
  `guides/frontend-engineering/reference/frontend-engineering.md`,
  `packs/iac-terraform/README.md`,
  `docs-site/src/content/docs/getting-started/three-loops.md`, and
  `web/src/content/journeys/core.md`.
- [x] Editing `packs/core/seeds/docs/CONVENTIONS.md` regenerates root
  `docs/CONVENTIONS.md` through scaffold sync, and the source/target check is
  clean.
- [x] No new guide family is added.
- [x] Core, Product Engineering, and AgentBundle each move every one of their
  version-pinned release surfaces together, and no pack whose source this slice
  does not change receives a bump. Minimality of the bump *level* is the
  reviewer's judgement, not a checkable predicate; the checkable part is parity
  and the absence of unrelated bumps.

## Follow-ons

Not acceptance criteria for this slice. Separated on 2026-08-28 by the spec
owner after pre-EXECUTE review found them unmapped to this Objective; RFC-0099
places them on the execution side, not in the shaping-reviewer contract.

- **Execution-side RFC-0099 errata.** The root-cause cluster checkpoint after
  adjudication, the touched-seam cleanup-versus-neighboring-module boundary
  across `work-loop`/`implementer`/adversarial review/quality review, and claim
  minimization in the author and reviewer rubrics. Owner: repository
  maintainers. Evidence: `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md`
  Errata §§ on cluster disposition, touched-seam debt, and claim minimization.
  Tracked as `[backlog].open` slug `rfc0099-execution-side-errata`.

## Assumptions

- Technical: agents are auto-discovered from `.apm/agents/`; no agent roster is
  added to plugin metadata (source: existing pack layout and
  `packs/architect/.apm/agents/design-reviewer.md`).
- Technical: kiro-ide and kiro-cli inject
  `resources: ["skill://.kiro/skills/**/SKILL.md", ...]` into every projected
  agent unless the source declares `skills: []`; the other five adapters project
  no skill reach. Measured 2026-08-28 by projecting a synthetic read-only agent
  both ways through `agentbundle.build.adapters` (source: `contracts/adapter.toml`
  kiro-ide/kiro-cli `inject-resources`; `packs/core/.apm/agents/finding-adjudicator.md`
  is the existing repository idiom).
- Technical: `metadata` is not a recognised Claude Code subagent frontmatter
  key, and the documentation does not say how an unrecognised subagent key is
  handled. The recognised set is `name`, `description`, `tools`,
  `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`,
  `mcpServers`, `hooks`, `memory`, `background`, `effort`, `isolation`, `color`
  (source: https://code.claude.com/docs/en/sub-agents.md, checked 2026-08-28).
  Boundary metadata is therefore source-only: the projection seam strips it and
  catalogue verification validates it on the source agent, not on the projected
  `.claude/agents/` artifact, which today rejects the key
  (`packages/agentbundle/agentbundle/catalogue_tooling/verify.py`,
  `ALLOWED_AGENT_KEYS`).
- Technical: `docs/architecture/pack-layout.md`'s agent-frontmatter key list is
  stale against that same source — it omits `skills`, which the repository
  already ships on `finding-adjudicator`. Correcting it is not in this slice.
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
