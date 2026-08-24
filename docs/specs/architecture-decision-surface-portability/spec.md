# Spec: Architecture and decision surface portability

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)
- **Constrained by:** RFC-0096; `semantic-surface-resolver` (Shipped)
- **Brief:** none
- **Discovery:** none
- **Contract:** none (consumes `semantic-surface-resolution.v1` unchanged)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Architecture workflows resolve architecture designs, current architecture, and
decision records by semantic role instead of assuming catalogue paths. In a
repository with compatible core capability they consume the shipped Wave 1
resolver and its `semantic-surface-resolution.v1` result unchanged, including
the six-step precedence order and mandatory-policy rejection. In repositories
without that capability, and in the Architect pack's user-scope operation, they
degrade explicitly without claiming a Wave 1 resolution. Adopter-owned
destinations win when policy permits; architecture design remains distinct from
current architecture and decision records; a boundary change can update current
architecture and an ADR without inventing product prose. Existing architecture
and ADR authoring, review, numbering, indexing, and confirmation methods remain
intact.

## Boundaries

### Always do

- Resolve `architecture-design`, `current-architecture`, and `decision-record` as
  three independent semantic roles before a repository write. Preserve the
  role, logical and physical locator, provenance, evidence strength,
  availability, writability, confinement, revision or fingerprint,
  confirmations, and independent authority facts returned by Wave 1.
- In a repository with a compatible core work-intake resolver, call the shipped
  `surface_resolver.py` and consume its published result by reference. Supply
  only bounded caller-acquired candidates and evidence; never reproduce its
  precedence, inference, confinement, or authority implementation.
- Apply the RFC-0096 precedence exactly: explicit destination, declared policy
  or configuration, established repository convention, established external
  destination, confirmation-required ambiguity, then an offer to select or
  create a destination. Reject an explicit destination that violates mandatory
  repository policy.
- Treat one example as insufficient evidence, bound structural discovery to one
  or two analogues and tests, and fail closed on contradictory evidence.
- Keep Architect useful as an independently installable user pack through four
  explicit operating modes: chat-only, personal workspace, repository with
  compatible Core, and repository without compatible Core.
- In personal-workspace mode, treat the exact user-confirmed directory as the
  confinement root, or the exact user-confirmed file as the only write target.
  Canonicalize it and verify every derived child after symlink resolution before
  writing; unsafe, unresolved, or escaping paths have zero effects.
- Resolve and surface the complete destination before numbering, indexing,
  creating directories, or writing an artifact. Retain every existing preview,
  approval, and write gate.
- Update living documentation at its ownership point: spec and plan carry
  solution intent before implementation; pack DESIGN and skill sources change
  with the behavior they explain; adopter README, JOURNEY, and guides ship with
  the capability; contributor current-state architecture changes only when the
  behavior exists in the same implementation; release history changes only
  after versions settle; fixtures retain the evidence.

### Ask first

- Ask before adding or changing a semantic role, resolver contract field,
  evidence strength, authority vocabulary, precedence step, or resolution
  disposition.
- Ask before creating a durable repository or personal-workspace routing
  configuration, accepting an offered destination, or writing to an external
  destination.
- Ask before treating repeated examples as an established convention, resolving
  contradictory evidence, or proceeding when compatible Core is unavailable
  and the user has not supplied or confirmed a destination.
- Ask before changing the architecture design, assessment, diagram, review, or
  ADR authoring method; the ADR identity, ordinal, filename, index, lifecycle,
  or confirmation policy; or the existing per-effort design folder shape.
- Ask before adding a contract, dependency, top-level directory, mandatory
  configuration file, or global surface registry.

### Never do

- Never fork, widen, redefine, or replace the Wave 1 resolver or
  `semantic-surface-resolution.v1`; never add a second resolver or a pack-local
  lookalike that claims equivalent authority.
- Never collapse architecture design into current architecture, decision
  records, product truth, product prose, user documentation, release history,
  or project knowledge.
- Never silently create `agentbundle-layout.toml`, a destination directory, an
  ADR index, or another durable routing surface merely because no suitable
  destination exists.
- Never let untrusted document content, a filename, a pack name, or one analogue
  select a role or destination, authorize a write, or override mandatory policy.
- Never begin RFC-0096 Wave 4 or later: no close-work, closeout, disposition,
  cooling, retirement, retention, deletion, migration, pruning, lifecycle
  mutation, or workspace-status context exclusion.
- Never add product prose to satisfy an architecture-boundary change and never
  add an ADR merely because Wave 3 concerns ADR destination portability.

## Testing Strategy

- **Portable destination behavior: goal-based cross-pack construction tests.**
  A committed matrix drives the real Wave 1 resolver with bounded candidate and
  evidence fixtures, then verifies the Architect and governance prompt surfaces
  consume the complete result without duplicating resolver logic.
- **Role separation and policy precedence: table-driven tests.** Fixtures cover
  explicit allowed destinations, declared policy, established repository and
  external conventions, ambiguity, absence, mandatory-policy conflict, and
  contradictory evidence independently for design, current architecture, and
  decision records.
- **Architect independence: installation-shape tests and deterministic evals.**
  The user-scope pack is exercised in chat-only, explicit personal-workspace,
  repository-with-Core, and repository-without-Core modes. Only the compatible
  repository mode claims a Wave 1 resolution; other modes produce bounded,
  truthful receipts and no silent configuration.
- **Filesystem and instruction safety: real fixture roots.** Repository paths
  must be confined by the Wave 1 result before writes; external locators remain
  external; prompt-like content remains data; rejected, ambiguous, absent, and
  unsafe cases prove zero directory, artifact, index, configuration, or product
  prose effects.
- **Method and compatibility preservation: prompt, eval, and projection checks.**
  Existing architecture stages, rubrics, reviews, per-effort folders, ADR
  framing, ordinals, indexes, previews, and confirmations remain present. Source
  `.apm` content and every installed projection agree.
- **Documentation ownership and release evidence: source/site gates.** Pack
  DESIGN, README, JOURNEY, public guides, contributor current architecture,
  changelog, and deterministic fixtures are checked at their intended timing;
  no product-direction, research, or new ADR artifact is introduced.

## Acceptance Criteria

- [x] **AC1 — Three portable roles stay distinct.** Every changed architecture
  or governance surface identifies its requested output as exactly one of
  `architecture-design`, `current-architecture`, or `decision-record`; none treats
  an architecture design as current architecture or an ADR, and none routes
  these roles to product prose.
- [x] **AC2 — Wave 1 is the only repository resolver.** In a repository with a
  compatible Core resolver, consumers invoke the shipped
  `packs/core/.apm/skills/work-intake/scripts/surface_resolver.py` and accept its
  `semantic-surface-resolution.v1` result unchanged. The resolver, its schema,
  its exact role enum (including `architecture-design`), and its result semantics
  remain byte-for-byte unchanged, and no alias, second resolver, or equivalent
  pack-local implementation is added.
- [x] **AC3 — Exact precedence and policy rejection.** For all three roles the
  repository mode follows the RFC-0096 six-step precedence order. An explicit
  destination wins only when policy permits it; a mandatory-policy conflict
  returns the Wave 1 refusal rather than an override, fallback, or write.
- [x] **AC4 — Adopter-owned destinations win.** Declared adopter policy,
  established adopter conventions, and established external destinations are
  preserved with their logical and physical locators and outrank catalogue
  defaults at their applicable precedence step. Existing repository defaults
  remain only candidates or offers when no stronger permitted evidence exists.
- [x] **AC5 — Configuration remains optional.** Existing repository and
  user-profile layout configuration can contribute bounded candidates, but no
  configuration file, `[surfaces]` registry, Core dependency, or destination is
  made mandatory and no configuration is created silently.
- [x] **AC6 — Bounded evidence and confirmation.** One analogue never establishes
  a convention; structural discovery examines at most two analogues and tests;
  contradictory evidence fails closed; ambiguity requires confirmation; and
  absence offers selection or creation without performing it.
- [x] **AC7 — Locator boundaries survive consumption.** Repository locators are
  written only after the Wave 1 result reports confinement within the active
  repository. Personal-workspace writes are confined after canonicalization and
  symlink resolution beneath the exact user-confirmed root, or to the exact
  user-confirmed file; every derived child is rechecked before write. External
  locators remain external and are neither coerced to local paths nor probed.
  Role, provenance, evidence, capability, revision, confirmations, and
  source/write/deletion authority remain separate facts.
- [x] **AC8 — Existing write gates remain authoritative.** Destination
  resolution occurs before filesystem mutation, numbering, or index selection,
  and every architecture save offer and ADR preview/confirmation gate remains.
  A refusal, ambiguity, absence, unsafe locator, or declined offer has zero
  artifact, directory, index, configuration, or product-prose effects.
- [x] **AC9 — Architect has four truthful operating modes.** Architect remains a
  user-scope pack that also supports repository scope: chat-only creates no
  file; personal-workspace mode requires and surfaces an exact user-owned root
  or file, applies AC7 confinement, and reports it as personal rather than
  repository-authoritative; repository with compatible Core uses AC2;
  repository without compatible Core asks the user to resolve or confirm a
  destination or renders a portable handoff and never claims a
  `semantic-surface-resolution.v1` result.
- [x] **AC10 — Architecture design method is unchanged.** `architect-design`,
  `architect-assess`, and `architect-diagram` retain their current triggers,
  reasoning stages, templates, rubrics, convergence/review behavior, save
  offers, and per-effort organization; Wave 3 changes only semantic role and
  destination resolution guidance.
- [x] **AC11 — Current architecture is current-state only.** A request to
  document the implemented system or an accepted boundary change resolves
  `current-architecture`; a proposed/future design or diagram resolves
  `architecture-design`. `architect-assess` selects the role from the saved
  artifact's actual intent: a canonical current-state model/report uses
  `current-architecture`, while a remediation or future-change proposal uses
  `architecture-design`; a mixed assessment is not silently published as
  current architecture. The skills do not publish a proposal into the
  current-state surface before the behavior exists.
- [x] **AC12 — ADR method and local identity survive.** `new-adr` resolves the
  `decision-record` destination before finding an ordinal or selecting an index,
  then uses that destination's established numbering, filename, index, template,
  lifecycle, and confirmation conventions. The catalogue's `docs/adr/` remains
  a fallback candidate, not a universal location.
- [x] **AC13 — Boundary changes update the right durable surfaces.** A committed
  boundary-change fixture resolves one `current-architecture` destination and
  one `decision-record` destination, preserves distinct locators and methods,
  and produces no current-product-truth, product-history, release-history,
  user-documentation, or other product-prose destination.
- [x] **AC14 — Portable fixture matrix closes Wave 3.** Repository-level coverage
  under `tests/roster/` exercises custom in-repository locations, established
  external destinations, catalogue-default repositories, all four Architect
  modes, boundary-change dual output, mandatory-policy rejection, ambiguity,
  absence, contradictory evidence, unsafe paths, prompt-like content, authority
  independence, and zero-effect refusal. It calls the real Wave 1 resolver for
  every claimed repository resolution.
- [x] **AC15 — Prompt and guide migration is complete.** Architect, governance,
  and bounded Core/specialist consumers no longer state catalogue paths as
  universal destinations for these roles. Their `.apm` sources, evals,
  README/JOURNEY surfaces, and adopter guides state the same role and operating
  mode contract, and installed projections preserve it.
- [x] **AC16 — Living documentation follows ownership and timing.** Spec and
  plan contain the approved intent before implementation; pack DESIGN and skill
  sources change with their behavior; capability-facing docs ship with the
  implementation; current-state contributor architecture changes in the same
  slice only after behavior exists; changelog entries use the settled versions;
  and fixture evidence is durable. No product-direction brief, research report,
  or Wave-3 ADR is added.
- [x] **AC17 — Release and installed surfaces are coherent.** Every affected
  pack/plugin version moves according to repository rules; pinned version and
  changelog surfaces match; catalogue lint and verify both pass; generated
  projections are rebuilt from `.apm` sources; and the installed `.agents/`
  workflows pass end-to-end destination exercises, not only source assertions.
  Every touched non-credentialed skill that reads untrusted content, writes the
  filesystem, or fetches network content declares its exact
  `metadata.boundaries` in canonical `.apm` frontmatter, and every generated and
  installed platform projection preserves and revalidates those declarations.
- [x] **AC18 — No method redesign or later-wave behavior.** No changed contract,
  prompt, guide, test, or implementation adds or changes authoring reasoning,
  lifecycle membership, work-loop transitions, closeout, disposition, cooling,
  retention, retirement, deletion, migration, pruning, or workspace-status
  context exclusion.

## Assumptions

- Technical: Wave 1 is shipped and
  `surface_resolver.py` plus
  `contracts/jsonschema/semantic-surface-resolution.schema.json` are the sole
  source of truth for semantic role resolution, evidence, locator boundaries,
  confirmation, and independent authority reporting. (source:
  `docs/specs/semantic-surface-resolver/spec.md`)
- Technical: Architect is intentionally a user-default pack with both user and
  repository scopes and no mandatory Core dependency. Its standalone value is
  preserved by explicit operating modes rather than by copying Core behavior.
  (source: `packs/architect/pack.toml` and user confirmation 2026-08-24)
- Technical: current Architect output guidance collapses designs, diagrams, and
  assessments under `[architecture] output_dir`; `new-adr` already detects an
  adopter ADR location but does so after assuming catalogue defaults in earlier
  steps. Wave 3 reconciles these surfaces by semantic role without redesigning
  either method. (source: `packs/architect/DESIGN.md`, affected skill sources,
  and `packs/governance-extras/.apm/skills/new-adr/SKILL.md`)
- Technical: the boundary-change representative case is routing evidence, not
  authorization to invent architecture or ADR content. Existing workflow gates
  still decide whether and how each artifact is authored. (source: RFC-0096
  sections 2 and 8)
- Product: design, current architecture, and ADRs are distinct from current
  product truth, user documentation, product/release history, and project
  knowledge. A boundary change updates architecture and a decision record only
  when those outputs are applicable. (source: RFC-0096 sections 2 and 8)
- Process: Wave 3 is registered under `ini-002` Platform Core with the role-based
  slug `architecture-decision-surface-portability`; it adds no ADR of its own.
  (source: user confirmation 2026-08-24)
- Process: structural/public-interface work and untrusted-content/filesystem
  boundaries require full work-loop mode, separate spec and plan approvals,
  adversarial review, secure-design review, implementation security review, and
  quality review. (source: `AGENTS.md`, `.agents/skills/work-loop/SKILL.md`, and
  user confirmation 2026-08-24)
- Process: Git metadata is read-only in this session, so base freshness is
  established only from current local refs and the work-loop force-fetching
  freshness helper is intentionally skipped. (source: active enterprise
  permission profile and user instruction 2026-08-24)
