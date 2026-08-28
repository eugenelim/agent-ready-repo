# Plan: Core guidance and artifact routing

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `ARCHITECTURE.md` and
  `docs/architecture/work-intake-and-artifact-routing.md`; analogous
  `docs/specs/work-intake-surface/` and
  `docs/specs/architecture-decision-surface-portability/`; current source/tests
  under `packs/core/.apm/skills/work-intake/` and
  `packs/core/tests/skills/work-intake/`. Uncertainty: AgentBundle's Workspace
  MCP brief label may be deleted as coupling or migrated to the canonical name;
  either outcome must pass the same lifecycle tests.

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; the approved baseline is immutable after sealing.

## Approach

Land the exact governance pointers authorized by RFC-0099, then add the small
canonical ladder at its seed/root owners. Create the intent and delivery-brief
owners by moving existing doctrine rather than wrapping it, narrow
`work-intake` to precedence and safe classification, and reduce the old brief
skills to aliases. Migrate canonical consumers and tracker matrices only after
the new targets exist. Finish with guides, versions, projections, and the real
routing-card exercise.

No shared routing framework is introduced. Existing callable seams and file
safety helpers are reused; a helper is extracted only if two production callers
need the same operation after the moves are visible.

## Constraints

- RFC-0099, including all 2026-08-27 Errata, is normative.
- The RFC-authorized charter amendment, two ADRs, frozen-ADR forward pointers,
  and RFC-0083/RFC-0096 Errata precede behavior implementation.
- Workspace entry schemas, lifecycle values, queue collections, and
  repository-canonical path contracts remain unchanged.
- Pack source is edited under `.apm/` and `seeds/`; generated projections are
  rebuilt, never hand-edited.
- Shipped pack content carries no repository-internal RFC/ADR citations.
- No new dependency, dynamic guidance loader, guide family, or public router is
  added.

## Construction tests

**Integration tests:** run the frozen R1–R12 routing cards against Core-only and
optional-pack installs; assert one first owner, canonical receipts, alias
compatibility, zero-spec Ready behavior, and no unintended writes. Run tracker
adapter matrices and Workspace MCP lifecycle tests against the same canonical
names.

**Manual verification:** invoke the built `work-intake`, `intake-intent`, both
`author-delivery-brief` modes, and both aliases through their documented happy
paths; record selected route, created/unchanged artifacts, status, receipt, and
deprecation notice. Record the observed stop point and out-of-scope downstream
effects; do not claim spec execution or tracker effects unless separately
exercised.

## Design (LLD)

### Component / module decomposition

- `packs/core/seeds/AGENTS.md` owns the portable ladder; root `AGENTS.md` owns
  this repository's curated adoption. Traces to AC1.
- `work-intake` owns neutral precedence, normalization, refresh, and safety;
  `intake-intent` owns intent rendering/admission; `author-delivery-brief` owns
  brief create/continue; aliases own only compatibility dispatch. Traces to
  AC2–AC5.
- Existing workspace, tracker, and Workspace MCP consumers point at canonical
  skill identities without becoming new authorities. Traces to AC6.

### State & control flow

`status → workspace-status`; explicit artifact/skill/work type → its owner;
otherwise `work-intake → classify safely → one owning skill`. Brief create
stops at Draft. Brief continue may reach Ready after human confirmation and
stops again before spec materialization until the slice is separately
confirmed. Traces to AC2–AC5.

### Failure, edge cases & resilience

Unsafe paths, sensitive locators, prompt-like payloads, unsupported source
authority, ambiguous routes, and unavailable optional processors fail closed
without alternate writes. Alias failure reports the canonical target and never
falls back to copied legacy behavior. Traces to AC2, AC5, AC7.

### Dependencies & integration

Core remains complete alone. Product Engineering and tracker packs consume
canonical routes through their existing optional integration boundaries.
AgentBundle changes only if Workspace MCP's current hard-coded label cannot be
removed. Traces to AC6 and AC9.

## Tasks

### T0: RFC-0099 governance prerequisites are authoritative and cross-linked

**Depends on:** none

**Touches:** `docs/CHARTER.md, docs/adr/{0009-product-brief-layer-and-plan-owned-lld.md,0019-product-intent-ontology-and-brief-projection.md,0076-briefs-persist-dispatch-starts-from-specs.md,0077-feature-projection-and-tracker-authority.md,0078-standalone-intake-and-deterministic-workspace-index.md,0098-artifact-admission-and-delivery-brief-lifecycle.md,0099-shaping-review-and-sealed-baseline-replacement.md,README.md}, docs/rfc/{0083-work-intake-and-artifact-routing.md,0096-portable-delivery-artifact-lifecycle.md,README.md}`

**Tests:**
- `no stub (goal-based)` — governance-link/index checks against the exact
  RFC-0099 section 11 inventory.
- Goal-based: the exact charter clause, two accepted ADRs, five frozen-ADR
  metadata forward pointers, and RFC-0083/RFC-0096 Errata match RFC-0099
  section 11; no other frozen body changed.
- Goal-based: internal links resolve and RFC/ADR indexes report the expected
  lifecycle states.

**Approach:**
- Author only the governance artifacts expressly authorized by RFC-0099.
- Preserve frozen bodies and add only legal metadata/Errata annotations.

**Done when:** the accepted governance chain exists and every later task can
cite it without a placeholder.

### T1: The canonical cut-before-adding ladder is enforced at its two guidance owners

**Depends on:** T0

**Touches:** `AGENTS.md, packs/core/seeds/AGENTS.md, packs/core/tests/pack/test_*seed*.py, guides/core/explanation/core-pack.md`

**Tests:**
- `no stub (goal-based)` — seed/root content construction and guide checks.
- Goal-based: focused construction tests pin all seven rungs, order, stop rule,
  bounded check language, obvious-code qualifier, and never-cut set (AC1).
- Goal-based: a repository scan rejects a second full-ladder copy introduced by
  this change while allowing narrow safety deltas.
- Goal-based: fixtures pin outcome-led guidance, suppression of routine tool
  narration, and receipts ending with state, verification, and remaining work.
- Goal-based construction: changed Core/root guidance fixtures remove an
  outcome-irrelevant claim, accept a necessary named-target assertion only with
  evidence from one bounded read/search, and otherwise require an explicit
  assumption or discovery predicate (AC1).
- Goal-based: the existing Core system explanation names the Razor product
  principle, explains the ladder and never-cut boundary, and does not recast it
  as either a fifth Charter admission bar or a tech-site design principle
  (AC1, AC8).

**Approach:**
- Add the concise portable ladder to the Core seed and a curated equivalent to
  root guidance.
- Consolidate overlapping existing simplification prose instead of stacking a
  second checklist.
- Ship the ladder, product-principle explanation, and communication-baseline
  guide delta in this task; add no new principles page or guide family.

**Done when:** AC1 construction tests pass against source and projected seed
content.

### T2: `intake-intent` owns minimum intent admission

**Depends on:** T0

**Touches:** `packs/core/.apm/skills/intake-intent/**, packs/core/.apm/skills/work-intake/assets/minimal-intent.md, packs/core/.apm/skills/work-intake/scripts/intake_guard.py, packs/core/pack.toml, packs/core/tests/skills/intake-intent/**, packs/core/tests/pack/test_work_intake_surface.py, packages/agentbundle/tests/integration/**, guides/core/how-to/start-or-remember-work.md`

**Tests:**
- `stub: true` —
  `packs/core/tests/skills/intake-intent/test_intake_intent.py` (`STUB: AC3`,
  `STUB: AC7`).
- The stub is one representative renderer/admission contract assertion; the
  complete trust-boundary matrix is an EXECUTE construction obligation, not a
  PLAN-stub completeness gate.
- TDD: minimum fields, repository admission, in-place identity, external-source
  authority transfer, sensitive locator minimization, and unsafe-path refusal
  cover AC3 and AC7.
- TDD: passive-effect fixtures fail on any HTTP, DNS, subprocess/shell,
  credential, tracker, filesystem stat, resolution, listing, read, or write
  during external-locator intent admission; only a human-confirmed repository
  destination may use confined file access (AC7).
- TDD: persisted locators strip all query/fragment data, credentials, tokens,
  personal absolute-home/private paths, and personal data, refusing when the
  minimized locator loses source identity (AC7).
- TDD: prompt-like tracker and personal/vault text remains delimited data and
  cannot alter identity, scope, tools, permissions, lifecycle status, reviewer
  routing or verdict, write targets, or normative ownership (AC7).
- Goal-based: activation/near-miss evals select intent-only prompts and reject
  direct RFC/spec/brief/defect work.
- Goal-based: the existing Core skill-permission test and adapter integration
  seam assert exact `intake-intent` tools/boundaries and every supported
  projection (AC7, AC9).

**Approach:**
- Move intent-specific doctrine and the template to the new owner.
- Reuse the current confined rendering seam where it remains a real shared
  caller; otherwise move it with the owner and delete the old path.
- Register the new skill and its activation/near-miss evals in the Core roster
  before any consumer selects it; defer only aggregate release/version work.
- Ship repository-intent admission guidance with the capability.

**Done when:** `intake-intent` can create/admit a valid intent independently and
`work-intake` no longer authors intent content itself.

### T3: `author-delivery-brief` owns create and continue without duplicated doctrine

**Depends on:** T0

**Touches:** `packs/core/.apm/skills/author-delivery-brief/**, packs/core/.apm/skills/author-brief/**, packs/core/.apm/skills/receive-brief/**, packs/core/seeds/docs/product/briefs/_template.md, packs/core/pack.toml, packs/core/tests/skills/*brief*/**, packs/core/tests/pack/test_work_intake_surface.py, packages/agentbundle/tests/integration/**, guides/core/{explanation/why-a-brief-layer.md,how-to/receive-a-product-brief-and-decompose-it-into-specs.md}`

**Tests:**
- `no stub (goal-based/eval/manual QA)` — caller eval fixtures under
  `packs/core/tests/skills/author-delivery-brief/` plus the existing brief
  coverage-linter contract after it moves to the canonical owner.
- Goal-based/eval: trusted create, hostile external create,
  continue/readiness, zero-spec Ready, separate slice confirmation, map
  separation, and project-knowledge producer identity cover AC4 and AC7.
- Goal-based/eval: passive-effect fixtures fail on any HTTP, DNS,
  subprocess/shell, credential, tracker, filesystem stat, resolution, listing,
  read, or write caused by an external locator in create or continue mode;
  only a human-confirmed repository destination may use confined file access
  (AC7).
- Goal-based/eval: persisted locator fixtures strip all query/fragment data,
  credentials, tokens, personal absolute-home/private paths, and personal data,
  refusing when minimization destroys source identity (AC7).
- Goal-based/eval: prompt-like brief text remains delimited data and cannot
  alter identity, scope, tools, permissions, lifecycle status, reviewer routing
  or verdict, write targets, or normative ownership (AC7).
- Goal-based: the existing Core skill-permission test and adapter integration
  seam assert exact `author-delivery-brief` tools/boundaries and every supported
  projection (AC7, AC9).
- Goal-based: mode-specific activation/evals and the coverage linter reject
  governance records in delivery rollups.

**Approach:**
- Move creation/readiness doctrine and existing examples/linter behind one
  mode-aware owner.
- Keep create and continue authority branches explicit; do not add a generic
  mode framework.
- Register the canonical skill and both mode-specific activation/eval sets in
  the Core roster before consumers select it; defer only aggregate
  release/version work.
- Ship create/continue, Ready-with-zero-specs, and slice-confirmation guidance
  with the capability.

**Done when:** both modes pass their behavior fixtures and the old skill bodies
contain no lifecycle doctrine.

### T4: Neutral intake and canonical consumers select exactly one owner

**Depends on:** T2, T3

**Touches:** `packs/core/.apm/skills/work-intake/**, packs/core/.apm/skills/workspace-status/**, packs/core/.apm/skills/new-spec/**, packs/core/.apm/skills/init-project/**, packages/agentbundle/{pyproject.toml,agentbundle/version.py,agentbundle/workspace_mcp.py,tests/test_workspace_mcp_lifecycle.py}, tests/roster/test_shaping_intake_handoff_matrix.py, guides/core/reference/work-intake-routing-and-lifecycle.md`

**Tests:**
- `stub: true` —
  `packs/core/tests/skills/work-intake/test_routing_precedence.py` (`STUB: AC2`,
  `STUB: AC6`).
- The stub pins one representative executable routing seam; the twelve-card
  matrix and near misses are completed during EXECUTE.
- TDD: precedence, explicit direct-owner paths, raw/ambiguous fallback,
  delegation identity, refresh/status preservation, and near misses cover AC2.
- Goal-based: the existing Core skill-permission test and supported-adapter
  integration seam assert exact tools/boundaries for every T4-edited Core
  skill, including `work-intake`; a listed owner that needs no content change
  remains untouched (AC7, AC9).
- Goal-based: schemas and queue names remain unchanged while every canonical
  consumer label is new-name-only (AC6).
- Goal-based: if Workspace MCP source changes, AgentBundle package-version
  parity and package release evidence are required in the same task (AC6).

**Approach:**
- Narrow router classification and update its matrix after both owners exist.
- Remove the Workspace MCP brief-label coupling if possible; otherwise migrate
  the constant and its package contract explicitly.
- Ship direct-owner precedence and MCP-as-invocation-route guidance with the
  routing change.

**Done when:** R1–R12 have one deterministic first owner and no changed
canonical consumer points at an alias.

### T5: Compatibility and tracker integrations read old and write new

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/author-brief/**, packs/core/.apm/skills/receive-brief/**, packs/{atlassian,github,linear,product-engineering}/**, packs/core/tests/skills/{author-brief,receive-brief}/**, packs/core/seeds/docs/CONVENTIONS.md, docs/CONVENTIONS.md, tests/roster/test_tracker_intake_adapters.py, guides/core/{explanation/role-journeys.md,explanation/why-a-brief-layer.md,explanation/why-work-begins-with-an-artifact.md,how-to/intake-an-external-brief.md,how-to/receive-a-product-brief-and-decompose-it-into-specs.md,how-to/run-a-live-demo.md,how-to/start-or-remember-work.md,reference/product-brief-fields.md,reference/spec-shape-and-lld.md,reference/work-intake-routing-and-lifecycle.md,tutorials/start-a-new-project.md}, guides/product-engineering/{explanation/the-discovery-loop.md,explanation/the-intent-tree.md,how-to/map-capabilities.md,how-to/run-a-capability-across-a-value-stream.md,how-to/run-a-discovery.md,how-to/shape-a-feature-intent.md,reference/intent-fields-and-modes.md,tutorials/walk-a-discovery-end-to-end.md}, guides/_shared/how-to/{use-work-intake.md,choose-a-tracker-integration.md}, guides/_shared/reference/work-intake-routing-and-lifecycle.md, guides/catalogue-curation/tutorials/your-first-skill.md`

**Tests:**
- `no stub (goal-based)` — alias contract tests under
  `packs/core/tests/skills/{author-brief,receive-brief}/`, following the shipped
  `capture-work` compatibility-contract pattern.
- Goal-based: alias delegation, notice, least privilege, canonical receipt, and
  `invoked_alias` cover AC5.
- Goal-based: static and supported-adapter projection fixtures reject either
  alias when it omits or widens the canonical target's tools/boundaries (AC7,
  AC9).
- Goal-based: tracker matrices and cross-pack references write canonical names;
  old prompts remain accepted only through aliases (AC6).
- Goal-based: prompt-like brief, tracker, and personal/vault source text remains
  delimited data and cannot alter identity, scope, tools, permissions,
  lifecycle status, reviewer routing or verdict, write targets, or normative
  ownership (AC7).
- Goal-based: a bounded source search over every published guide root, current
  architecture, changed pack README/DESIGN/JOURNEY sources, the Core convention
  seed, and regenerated `docs/CONVENTIONS.md` discovers canonical old-name
  teaching; update every hit, including the known shared and
  catalogue-curation examples, while preserving historical and explicit
  compatibility references (AC8).
- Goal-based: policy fixtures pin the rollback target, two-minor-release and
  90-day floor, advance notice, and first-eligible Approver decision without
  implementing removal.

**Approach:**
- Follow the shipped `capture-work` alias pattern without copying target prose.
- Update cross-pack matrices and direct references in the same release slice so
  no new artifact teaches the deprecated identity.
- Ship alias migration/removal-gate and tracker-handoff guidance with the
  compatibility change.

**Done when:** alias and tracker suites pass and a source search finds no new
canonical old-name examples.

### T6: Guides, versions, evals, and projections close the migration slice

**Depends on:** T0, T1, T2, T3, T4, T5

**Touches:** `guides/_shared/explanation/the-three-loops.md, docs/guides/reference/work-intake-maintenance.md, docs/architecture/work-intake-and-artifact-routing.md, packs/{core,atlassian,github,linear,product-engineering}/{README.md,DESIGN.md,JOURNEY.md,pack.toml,.claude-plugin/plugin.json}, tests/roster/test_shaping_intake_handoff_matrix.py, docs/product/changelog.md`

**Tests:**
- `no stub (goal-based/manual QA)` — aggregate guide/site, eval, catalogue,
  version, projection, and installed-profile evidence.
- Goal-based: guide lint/index/link/site checks, pack evals, catalogue
  lint/verify, manifest version parity, and self-host/build checks cover AC8–AC9.
- Goal-based: an aggregate static/projection check covers `work-intake`, both
  canonical skills, and both aliases and fails on every missing or widened
  tools/boundaries declaration across supported adapters (AC7, AC9).
- Goal-based: the versioned Core changelog entry contains a reviewed
  `Highlights` outcome for the Razor and canonical intent/delivery routes; the
  existing deterministic projection includes it at `/now/`, and no generated
  Now payload or page source is hand-edited (AC9).
- Goal-based: after T1–T5, repeat the bounded old-name search over published
  guide roots, current architecture, changed pack README/DESIGN/JOURNEY files,
  and the Core convention source/projection; fail on canonical teaching outside
  an explicit compatibility or historical context (AC8).
- Visual/manual QA: invoke canonical and alias paths in built Core-only and
  optional-pack profiles and record the routing-card evidence.

**Approach:**
- Finish only cross-cutting guide navigation, links, current architecture, and
  release/projection work; capability-specific guide slices live in T1–T5.
- Bump only packs/packages actually changed and regenerate owned projections.
- Treat the T6 pack set as an upper bound: T6 edits/releases only the packs
  whose shipped content T1–T5 actually changes.

**Done when:** AC1–AC9 are green, the routing study passes its accepted bar,
and the built catalogue teaches only canonical write-new names.

## Rollout

Ship canonical readers/writers and aliases in one release. Retain aliases for
at least two minor releases and 90 days; announce removal in advance and require
the named Approver decision at the first eligible release. Roll back to the last
alias-bearing pack release if activation or receipt fixtures regress. No
workspace data migration or irreversible operation occurs.

## Risks

- Moving rather than copying brief doctrine can leave an alias with hidden
  behavior; construction tests must reject classifiers/writers in alias trees.
- Cross-pack canonical-name updates can force unnecessary releases; touch only
  packs with a real shipped reference and record each unchanged consumer.
- Workspace MCP's hard-coded label can turn a content migration into an engine
  release; deletion of the coupling is preferred when lifecycle tests prove it.
- Root and seed guidance can drift; tests pin required semantics without making
  the curated root a byte-copy of the adopter seed.

## Changelog

- 2026-08-27: pre-execute review moved new-skill roster/projection registration
  into T2/T3, added filesystem-passive and minimized-locator fixtures, made the
  instruction/data boundary explicit, and required a manual-QA stop point.
- 2026-08-27: initial plan from accepted RFC-0099; declined a new routing
  framework, workspace schema migration, guide URL rename, and permanent alias
  layer.
