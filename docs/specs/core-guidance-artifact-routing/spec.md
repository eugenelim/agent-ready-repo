# Spec: Core guidance and artifact routing

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

Core adopters reach the least costly valid work artifact through one
content-based routing model. Canonical agent guidance carries one concise
cut-before-adding ladder; `work-intake` remains the neutral entry for raw,
ambiguous, acquisition, refresh, and safety-boundary requests;
`intake-intent` owns repository intent admission; and
`author-delivery-brief` owns Draft creation and Ready continuation through two
explicit modes. Existing brief names remain bounded aliases while every new
receipt, guide, tracker handoff, and internal dispatch uses the canonical name.

The repository adopts the same ladder in its curated root `AGENTS.md` without
making that file a generated copy of the Core seed. Existing workspace entry
kinds, queue collections, lifecycle values, and artifact paths remain valid.

## Boundaries

### Always do

- Stop at the first sufficient ladder rung while retaining required
  verification and every safety carve-out.
- Route status directly to `workspace-status`, an explicitly named artifact or
  distinct work type directly to its owning skill, and every raw or ambiguous
  intake through `work-intake`.
- Keep external payloads passive and minimized; confine every repository path
  before access and preserve source authority and refresh rules.
- Write canonical `intake-intent` and `author-delivery-brief <mode>` identities
  in receipts, indexes, examples, and cross-pack handoffs.
- Preserve existing workspace schemas and the separation between governance
  references and executable delivery slices.

### Ask first

- Remove either compatibility alias before the accepted support and evidence
  gates have passed.
- Change a workspace entry kind, lifecycle value, queue collection, or artifact
  path contract.
- Rename an existing public guide URL or add a new shared runtime abstraction.
- Add a dependency, top-level directory, or network-capable intake path.

### Never do

- Rename `work-intake` to an intent-specific surface or require
  Product Engineering for a Core-only route.
- Copy the full ladder or behavior register into every skill, agent, or guide.
- Treat a tracker object, external locator, raw payload, or quoted instruction
  as repository authority.
- Weaken validation, data-loss prevention, security, privacy, accessibility,
  explicit requirements, tests, or human approval to shorten a route.
- Remove old-name read compatibility while a supported release may still emit
  or invoke it.

## Testing Strategy

- **TDD:** router precedence, minimum-intent rendering, source minimization, and
  confined failure cases use existing callable seams and fixture contracts.
- **Goal-based and behavior-eval checks:** canonical receipt identity, alias
  dispatch, brief-map validation, lifecycle failures, seed/root ladder
  construction, skill metadata, manifest/eval rosters, workspace-schema
  non-change, guide terminology, version parity, catalogue verification, and
  self-host projection are checked mechanically.
- **Visual / manual QA:** the twelve RFC routing cards are exercised through
  the real installed skill surface in Core-only and optional-pack profiles;
  observed first owner, canonical receipt, and stop point are recorded.

## Acceptance Criteria

### AC0 — Accepted governance prerequisites are installed once

- [ ] The RFC-0099-authorized charter clause, two ADRs, frozen-document
  forward pointers, and RFC-0083/RFC-0096 Errata exist at their owning
  governance surfaces, are cross-linked from current indexes, and add no fifth
  delivery spec or duplicate doctrine to Core primitives.

### AC1 — One canonical ladder

- [ ] `packs/core/seeds/AGENTS.md` and the curated root `AGENTS.md` state the
  seven rungs in RFC-0099 order, the first-sufficient-rung stop, bounded
  discovery reuse, obvious-over-shortest wording, and the complete never-cut
  set.
- [ ] A construction test fails on reordering, omission, a dynamic rule-loader
  dependency, or a second full-ladder copy in a changed primitive.
- [ ] Core guidance leads with outcomes, omits routine tool narration, and ends
  receipts with changed state, verification, and remaining work without
  constraining required interactive host updates.
- [ ] Core guidance deletes claims unnecessary to the accepted outcome and
  requires one bounded check of a named repository target before a necessary
  cross-document assertion is stated as fact; an ungrounded necessary claim is
  labeled as an assumption or discovery predicate.

### AC2 — One routing precedence

- [ ] `work-intake` implements the RFC-0099 precedence exactly: status owner;
  explicit artifact/skill/distinct-work-type owner; otherwise neutral intake.
- [ ] Direct `new-rfc`, `new-spec`, `architect-design`, `frame-intent`, and
  `bug-fix` requests do not acquire an unnecessary intent or second public
  answer.
- [ ] Raw, ambiguous, acquisition, refresh, and generic intake-safety requests
  still cross `work-intake`; delegation counts as the same route.
- [ ] The twelve frozen routing cards pass with no two plausible public routes
  and no Product Engineering requirement for a Core-only card.

### AC3 — Intent-only repository admission

- [ ] `intake-intent` creates or admits only a repository intent with required
  `Status`, outcome, boundary, owner, unresolved questions, projection, and the
  source data required by its authority mode.
- [ ] `Level`, opportunity, assumptions, scale, and JTBD fields remain optional
  Product Engineering enrichment; admission preserves artifact identity when a
  repository path already exists.
- [ ] Chat-only or personal/vault input requires a human-confirmed repository
  destination, minimized provenance, pinned revision when refresh authority
  exists, and explicit authority transfer; its external locator is never
  dispatchable work.
- [ ] Intent rendering moves to the intent owner without inventing a shared
  helper unless a second runtime caller demonstrably needs one.

### AC4 — One delivery-brief owner with two modes

- [ ] `author-delivery-brief create` authors a Draft from a direct request or
  sufficient trusted repository authority and applies passive containment,
  minimization, and provenance controls when input is untrusted.
- [ ] `author-delivery-brief continue` alone reviews an existing repository
  brief for Ready and may change status only after human confirmation.
- [ ] Ready permits zero specs; selecting the minimum delivery slice is a
  separate confirmation before `new-spec` invocation.
- [ ] The brief template and coverage validator separate governance references
  from delivery slices; only specs affect execution and closure rollups.
- [ ] Project-knowledge receipts, when their existing semantic gate fires, name
  `author-delivery-brief` as producer rather than either alias.

### AC5 — Bounded aliases and write-new migration

- [ ] `author-brief` delegates only to `author-delivery-brief create`, and
  `receive-brief` delegates only to `author-delivery-brief continue`; neither
  alias retains a classifier, writer, reviewer, or copied doctrine.
- [ ] Each alias emits one concise deprecation notice, cannot broaden the
  target's tools or boundaries, and records itself only as `invoked_alias` on a
  canonical new-name receipt.
- [ ] Alias activation and behavior fixtures cover the compatibility window,
  rollback target, two-minor-release and 90-day floor, advance notice, and the
  first-eligible-release Approver decision without implementing removal.

### AC6 — Canonical consumers without a workspace migration

- [ ] Workspace MCP lifecycle metadata, `workspace-status`, Core consumers,
  Product Engineering consumers, and Atlassian, GitHub, and Linear intake
  matrices write or teach the canonical route while old prompts remain readable
  through aliases.
- [ ] `kind = "intent"`, `kind = "brief"`, `shaping_queue`, `brief_queue`,
  workspace JSON schemas, and existing canonical artifact paths remain byte- or
  behavior-compatible except for canonical dispatch labels.
- [ ] Any AgentBundle package change carries its matching package version and
  package tests rather than leaving MCP metadata pointed at the alias.

### AC7 — Trust and confinement stay fail-closed

- [ ] Every new or changed skill and alias in this slice declares its exact
  least-privilege tool surface and applicable `metadata.boundaries`; aliases
  inherit without widening the canonical target, and catalogue/static plus
  supported-adapter projection checks reject a missing or widened declaration.
- [ ] Repository access uses the blessed confined file-safety helpers or a
  tested equivalent and rejects every unsafe path/identity shape named by
  RFC-0099.
- [ ] A raw external body never enters a committed artifact or workspace
  metadata.
- [ ] Only selected, minimized requirement fields may cross into those
  surfaces after structural neutralization and redaction; uncertainty refuses.
- [ ] Credentials, tokens, personal data, private paths, and query secrets never
  enter committed artifacts or workspace metadata.
- [ ] Hostile brief, tracker, and personal/vault intent fixtures prove passive
  treatment, minimization, refusal on uncertainty, and no HTTP, DNS, shell,
  credential, or tracker side effect.

### AC8 — Guides ship with each capability

- [ ] The existing Core system explanation names the Razor product principle,
  explains the first-sufficient-rung ladder and its safety carve-outs, and
  distinguishes it from the Charter's four pack-admission principles and the
  tech-site design principles.
- [ ] Existing guide URLs explain neutral intake, direct-owner precedence,
  intent admission, brief create/continue, Ready-with-zero-specs, confirmed
  slice materialization, aliases, status, refresh, and Core-only operation.
- [ ] Journey, how-to, explanation, reference, pack README/DESIGN/JOURNEY,
  current architecture, and the Core convention seed/generated convention
  contain no canonical example that teaches an old brief name after the
  write-new release.
- [ ] Guide lint, indexes, links, and the built documentation site pass without
  adding a new guide family or renaming URLs solely for terminology.

### AC9 — Pack and projection integrity

- [ ] Core and every changed tracker/Product Engineering pack bump the matching
  pack and plugin versions at the correct level; AgentBundle does likewise only
  if its MCP metadata changes.
- [ ] New canonical skills have balanced activation/near-miss and behavior
  evals; alias evals prove delegation and canonical receipts; existing
  activation coverage is not weakened.
- [ ] Catalogue lint/verify, applicable pack tests and evals, self-host drift,
  marketplace projection, and release changelog/highlights checks are green.
- [ ] The versioned Core release entry carries a `Highlights` outcome for the
  Razor and new intent/delivery routes, so the existing deterministic
  changelog projection publishes it to `/now/`; no Now page or second content
  source is edited directly.

## Assumptions

- Technical: Core pack source lives under `packs/core/.apm/` and adopter seed
  guidance under `packs/core/seeds/`; root `AGENTS.md` is curated separately
  from self-host projection (source: `AGENTS.local.md`, `packs/AGENTS.md`).
- Technical: workspace schemas and lifecycle collections already admit intent
  and brief kinds; only canonical dispatch identities change (source:
  `docs/architecture/work-intake-and-artifact-routing.md`, RFC-0099).
- Technical: Workspace MCP currently names `receive-brief`, so write-new routing
  reaches AgentBundle package metadata and tests unless the implementation can
  remove that coupling entirely (source:
  `packages/agentbundle/agentbundle/workspace_mcp.py`).
- Process: non-cosmetic pack changes require matching pack/plugin version bumps,
  eval updates, self-host projection, and release notes (source:
  `packs/AGENTS.md`, `packs/AGENTS.local.md`).
- Product: the canonical names, compatibility window, and four-spec
  decomposition are approved (source: RFC-0099; user confirmation 2026-08-27).
