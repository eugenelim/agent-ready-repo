# Spec: RFC and architecture simplification

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099
- **Brief:** none
- **Discovery:** `docs/product/intents/cut-before-adding-solution-ladder.md`
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

RFC and architecture workflows reject unnecessary artifacts and solution
surface before authors invest in them. `new-rfc` runs an ordered
cut-before-creating checkpoint before ordinal resolution or filesystem writes;
`adversarial-reviewer` gains an RFC-specific YAGNI mode; `architect-design`
reuses adequate prior designs and stops at Stage 0 when it resolves the choice;
and `architect-review` challenges unjustified components, boundaries,
dependencies, scale, and custom mechanisms.

Existing RFC, architecture, spec-plan, and code-review owners remain distinct.
No shaping-reviewer mode is added for RFCs or architecture artifacts, and the
architect pack's separate cold convergence agent remains unchanged.

## Boundaries

### Always do

- Decide whether an RFC or full architecture document is needed before
  allocating its identifier or creating its target.
- Reuse an adequate existing decision, design, repository capability, standard
  library, native platform, or already-selected provider capability.
- Trace every full-design component and boundary to a goal, constraint, or
  prioritized quality attribute.
- Preserve safety, migration, compatibility, verification, and explicit
  requirements when cutting proposal surface.
- Keep authoring and review rubrics artifact-specific while consuming the one
  canonical ladder.

### Ask first

- Add a new RFC/architecture artifact kind, reviewer agent, dependency,
  component boundary, compatibility layer, or provider abstraction.
- Expand `adversarial-reviewer` beyond the accepted RFC mode or move an
  architecture review into the Core code-review gate.
- Change the valid Stage-0 stopping point or promote concept output into a full
  design without a remaining real choice.

### Never do

- Allocate an RFC ordinal, create a directory/index/file, or draft body text
  before the cut-before-creating checkpoint holds.
- Require an intent as the parent of a directly authorized RFC or architecture
  question.
- Add speculative scale, configurability, compatibility, extensibility,
  service, dependency, or module surface without a current load-bearing need.
- Copy the full ladder into all four primitives or change `design-reviewer`
  merely because adjacent architecture contracts changed.
- Remove safeguards or mandatory follow-ons solely to shorten an artifact.

## Testing Strategy

- **TDD:** any callable pre-create/ordinal path and construction validator uses
  red/green tests proving zero writes on skip/reuse/route and exact writes only
  after the checkpoint.
- **Goal-based checks:** skill/agent/rubric content contracts, eval fixtures,
  metadata boundaries, guide alignment, pack versions, catalogue verification,
  and projections prove the authored behavior.
- **Visual / manual QA:** run `new-rfc`, adversarial RFC review,
  `architect-design`, and `architect-review` on seeded wrong-artifact,
  reuse-hit, Stage-0-sufficient, and unjustified-full-design cases; record the
  chosen stop/route and review findings.

## Acceptance Criteria

### AC1 — `new-rfc` cuts before any write

- [ ] Before ordinal resolution, directory/index creation, or body drafting,
  `new-rfc` decides in order: consequential unresolved direction or explicit
  circulation; adequate existing RFC/decision reuse; cheaper correct artifact
  or reversible trial; lightest warranted RFC weight.
- [ ] Skip, reuse/amend/reference, ADR, spec, PR, issue, architecture-design,
  and reversible-trial outcomes create no RFC target and report the selected
  route once.
- [ ] A warranted RFC continues through the existing research checkpoint,
  preview, citation/self-claim checks, reviews, human circulation decision, and
  index lifecycle without weaker gates.
- [ ] Every repository write introduced or reordered by this slice uses the
  blessed confinement contract or a tested fail-closed equivalent: RFC target,
  index, and companion-note writes stay inside the resolved RFC owner root;
  architecture saves stay inside their resolved configured output root; and an
  unsafe, link-like, identity-changing, or out-of-root target refuses before
  mutation.
- [ ] A warranted RFC deletes claims unnecessary to its decision. Before
  stating a necessary cross-document assertion as fact, it performs one
  bounded check of the named target or marks the claim as an assumption or
  discovery predicate.

### AC2 — Adversarial RFC review owns RFC YAGNI

- [ ] `adversarial-reviewer` exposes a distinct RFC mode and context branch
  without changing its spec-plan, implementation, or mixed modes.
- [ ] RFC mode challenges wrong/unnecessary artifact, ignored existing decision
  or repository/native capability, unsupported dependency/abstraction/module/
  compatibility/follow-on surface, speculative future scope, duplicated
  doctrine, and safety/migration/verification removed for brevity.
- [ ] RFC mode removes unnecessary claims instead of asking authors to expand
  them, and flags an unsupported cross-document assertion only when the claim
  is necessary to the decision.
- [ ] The report preserves the existing findings-only output and no work-loop,
  code-diff, plan-construction, or implementation-conformance dependency is
  introduced for an RFC-only review.

### AC3 — Architecture authors reuse and stop

- [ ] `architect-design` retains its real-choice gate and bounded repository
  grounding, explicitly reuses an adequate prior design or existing capability,
  and produces no new artifact when no real choice remains.
- [ ] Stage 0 remains a valid final artifact; a full design is created only when
  unresolved trade-offs require it.
- [ ] Every component and boundary in a full design names the current goal,
  constraint, or prioritized quality attribute that justifies it; unsupported
  future-proofing is removed.
- [ ] Architecture documents delete unnecessary claims and ground each
  necessary cross-document assertion with one bounded check of its named target
  or an explicit assumption/discovery predicate.

### AC4 — Architecture review independently cuts excess design

- [ ] `architect-review` checks wrong artifact/no real choice, full design when
  a concept suffices, unnecessary component/service/dependency/boundary/custom
  mechanism, ignored existing/standard/native/provider capability, speculative
  scale/configurability/compatibility/extensibility, and complexity unsupported
  by a named quality attribute and credible constraint.
- [ ] The checks live in the design-doc review route/rubric and preserve all
  other architecture artifact rubrics and well-architected modes.
- [ ] Architecture review removes unnecessary claims rather than enlarging the
  document to defend them, and challenges unsupported necessary assertions.
- [ ] `design-reviewer` is unchanged; author self-check plus `architect-review`
  own the exact accepted slice.

### AC5 — Artifact ownership and downstream shaping remain separate

- [ ] A direct RFC or architecture request needs no synthetic intent; an
  accepted intent or design result may still supply provenance when present.
- [ ] RFC or architecture output invokes shaping review only through the owner
  of an intent, delivery brief, or spec that is materially revised from that
  output.
- [ ] RFC review remains adversarial; architecture review remains
  `architect-review`; neither becomes a fourth shaping-review mode.

### AC6 — Changed surfaces retain least privilege and fixed authority

- [ ] `new-rfc`, `architect-design`, and `architect-review` declare their
  minimum tools and applicable `metadata.boundaries`; changed reviewer-agent
  source declares the boundary schema established by
  `shaping-review-contracts`.
- [ ] Adapter projections prove equivalent existing permissions and do not gain
  write, shell, web, credential, or mutation authority merely for YAGNI review.
- [ ] Repository artifacts, skills, and caller-supplied evidence remain data;
  no independent retrieval or network capability is added.

### AC7 — Evals, guides, and releases prove behavior rather than prose

- [ ] `new-rfc` behavior fixtures prove checkpoint ordering and zero writes for
  every cheaper route; existing activation queries remain unchanged unless the
  public trigger description changes.
- [ ] Adversarial and architect fixtures seed every accepted YAGNI defect and
  prove existing modes/rubrics remain present.
- [ ] Existing governance and architect how-tos explain reuse, stopping, full-
  document justification, and YAGNI findings; stale contradictory requirements
  in an edited guide are reconciled rather than layered over.
- [ ] Core, Governance Extras, and Architect receive matching patch/version,
  eval, changelog/highlight, catalogue, marketplace, and projection updates
  only where their shipped content changes.

## Assumptions

- Technical: `new-rfc` currently resolves an ordinal before its no-file
  checkpoint, so true cut-before-creating requires reordering rather than a new
  validator (source: `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`).
- Technical: `architect-design` already has real-choice and Stage-0 stops;
  `architect-review` lacks the accepted YAGNI rubric (source:
  `packs/architect/.apm/skills/{architect-design,architect-review}/`).
- Technical: `adversarial-reviewer` has no RFC mode today and remains
  auto-discovered from its Core agent source (source:
  `packs/core/.apm/agents/adversarial-reviewer.md`).
- Process: non-cosmetic content changes require matching pack/plugin versions,
  evals, changelog/highlights, catalogue checks, and owned projections (source:
  `packs/AGENTS.md`, `packs/AGENTS.local.md`).
- Product: RFC and architecture keep their current owners and gain no shaping
  mode or new reviewer (source: RFC-0099; user confirmation 2026-08-27).
