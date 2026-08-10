# `experience-design` — skill and reviewer reference

> **Reference** — information-oriented. This page mirrors the shipped skill and
> agent contracts: what each one accepts, returns, reads or writes, and routes
> away. When frontmatter changes, update this page in the same change. For a
> task-oriented walkthrough, see [Thread a feature from journey to screens](../how-to/author-design-intent.md).

The pack contains 20 pure-Markdown skills and one independent reviewer agent.
It installs at user scope across every adapter declared by the pack manifest.

## Operating contract

**Inputs:** natural-language design requests, relevant product context, and any
existing journey, screen, content, direction, or rendered artifact the selected
skill needs.

**Returns:** a design decision, specification, map, brief, status report, or
severity-rated review. Artifact-writing skills resolve their location through
the `[design]` layout described below.

**Reads:** supplied context and existing design artifacts. `experience-status`
also reads the configured design output to report what exists.

**Writes:** only when the selected skill's contract names an artifact. The
resolved path is surfaced before the first write. `experience-status` and the
`experience-reviewer` agent are read-only.

**Limits:** the pack does not choose product strategy, frame or commit the
product-engineering bet, write frontend code, produce pixel comps, or replace
the person who approves the design. Skills ship method rather than framework
syntax or fixed visual values.

## Intent index

| If you need to… | Use | You receive | Nearest boundary |
| --- | --- | --- | --- |
| Understand an end user's path | `journey-mapping` | Customer journey map | Not product strategy or feature shaping |
| Connect a journey to backstage support | `service-blueprint` | Service blueprint | Not service/frontend implementation |
| Turn a journey into screens and edge paths | `user-flow` | Screen flow and per-screen briefs | Not bet scope or screen code |
| Map an internal operation | `process-mapping` | SIPOC, swimlanes, as-is/to-be map | Not operating strategy or workflow implementation |
| Orient to existing design work | `experience-status` | Read-only status and next design skill | Not portfolio, shaping, or build status |
| Create durable design arbitration rules | `design-principles` | Named principles with tests | Not product positioning or component rules |
| Name a visual direction | `creative-direction` | Ranked aesthetic goals | Not market positioning or visual implementation |
| Derive token names and scales | `design-system` | Token taxonomy and rationale | Not token implementation |
| Organize hierarchy and wayfinding | `information-architecture` | IA and layout reasoning | Not markup or styles |
| Specify behavior within a screen | `interaction-design` | Behavioral and state specification | Not component code or UI strings |
| Critique an existing design | `design-review` | Severity-rated findings | Not code review or new design creation |
| Decide a surface's message and structure | `content-design` | Content brief | Not brand register, copy goals, or UI strings |
| Set copy goals for one acquisition surface | `copy-direction` | Copy-direction record | Not brand register, content structure, or UI strings |
| Define the cross-surface brand register | `tone-of-voice` | Brand-register document | Not one surface's copy direction or UI strings |
| Structure a marketing or acquisition surface | `conversion-design` | Conversion-surface specification | Not go-to-market strategy, final copy, or page code |
| Structure docs, help, or API reference | `documentation-design` | Docs IA and navigation specification | Not docs strategy, technical authoring, or site code |
| Structure a dashboard or reporting view | `analytical-design` | Analytical IA and widget hierarchy | Not metric strategy or chart implementation |
| Structure an editorial reading surface | `informational-design` | Typography and reading-flow specification | Not editorial strategy, article writing, or template code |
| Structure marketplace discovery and choice | `marketplace-design` | Catalogue and transaction-bridge IA | Not marketplace strategy or implementation |
| Structure sustained professional work | `workspace-design` | Workspace-surface specification | Not feature scope, implementation, or UI strings |

## Connective and operational skills

### `journey-mapping`

**Use when:** “Map what a new customer goes through from first awareness to
first successful use.”

**Returns:** stages, actions, touchpoints, emotions, pains, and opportunities in
a customer journey map, adjusted for the target platform. Writes
`<output_dir>/journeys/<slug>.md` with `type: customer-journey`.

**Routes away:** product/adoption strategy; selecting or scoping a bet; screen
implementation. Use `service-blueprint` for backing services, `user-flow` for
screens, and `process-mapping` for internal operations.

### `service-blueprint`

**Use when:** “Show which backstage services and teams support every step of
this customer journey.”

**Returns:** a four-part service blueprint covering frontstage, line of
visibility, backstage, and support. Writes
`<output_dir>/blueprints/<slug>.md` with `type: service-blueprint`.

**Routes away:** service strategy, initiative framing, and implementation of
service calls or frontend behavior. Use `journey-mapping` to discover the
customer path, `user-flow` for screen transitions, and `process-mapping` for an
internal operation without the customer lens.

### `user-flow`

**Use when:** “Turn this approved onboarding journey into screens, transitions,
and failure paths.”

**Returns:** a complete screen sequence, edge paths, one brief per screen, and a
whole-flow check. Writes `<output_dir>/screens/<slug>-flow.md`, briefs under
`<output_dir>/screens/<slug>/`, and an optional design-tool handover.

**Routes away:** adoption strategy, appetite and scope, and implementation of
routes or screens. Use `journey-mapping` first, `interaction-design` for
within-screen behavior, and `service-blueprint` for backing services.

### `process-mapping`

**Use when:** “Map our internal fulfilment process across teams, including
handoffs and waste.”

**Returns:** a SIPOC scope, swimlane map, as-is/to-be flow, delta table, and
pain/waste register. Writes `<output_dir>/processes/<slug>.md` with
`type: process-flow`.

**Routes away:** operating or product strategy, shaping an automation bet, and
implementing workflow software. Use `journey-mapping` for the customer's path,
`service-blueprint` for customer-facing backstage support, and `user-flow` for
screens.

### `experience-status`

**Use when:** “Orient me to the current design thread and tell me which design
artifact is missing.”

**Returns:** a read-only inventory of existing design artifacts, gaps, and the
next relevant design skill. It never writes or elicits configuration.

**Routes away:** product or portfolio status, prioritizing or shaping the next
feature, and implementation/build status.

## Principles and craft

### `design-principles`

**Use when:** “Turn these journey pains into a few design principles we can use
to settle tradeoffs.”

**Returns:** 3–5 named principles grounded in evidence, each with rationale and
an arbitration test. Writes `docs/design/principles/<slug>.md`; this skill does
not currently consult `[design] output_dir`.

**Routes away:** target segments and product positioning, choosing or scoping a
bet, and encoding rules in components. Use `creative-direction` for visual
goals, `design-system` for token taxonomy, and `design-review` for critique.

### `creative-direction`

**Use when:** “We keep saying calm and premium; turn that into a visual
direction the team can use.”

**Returns:** ranked aesthetic goals grounded in stable referents, plus rules for
which goal wins when goals conflict, recorded in `creative-direction.md`.

**Routes away:** product positioning, framing or scoping the bet, and
implementing colors, type, or components. Use `design-system` after the
direction, `information-architecture` for hierarchy, and `design-review` for
critique.

### `design-system`

**Use when:** “Derive semantic spacing, type, and color token names from our
approved direction.”

**Returns:** a semantic token/scale taxonomy and its rationale. It names and
organizes the system but does not implement token values.

**Routes away:** product differentiation, design-system initiative shaping, and
token or component implementation. Use `creative-direction` to establish the
vibe, `information-architecture` for page hierarchy, and `design-review` for
evaluation.

### `information-architecture`

**Use when:** “Organize this settings area so people know what is primary and
where to go next.”

**Returns:** hierarchy, reading flow, progressive disclosure, navigation, and
wayfinding in an information-architecture and layout-reasoning document.

**Routes away:** product direction, feature scope, and markup/styles. Use
`creative-direction` for visual mood, `interaction-design` for within-screen
behavior, `user-flow` for screen sequence, and `design-review` for critique.

### `interaction-design`

**Use when:** “Design how this upload component behaves from idle through
progress, failure, and retry.”

**Returns:** behavioral and state specifications for one screen or component;
it may enrich a per-screen brief and does not create a separate layout entry.

**Routes away:** product strategy, feature shaping, component implementation,
and writing the strings shown in states. Use `information-architecture` for
hierarchy, `user-flow` for cross-screen routes, and `ux-writing` for UI strings.

### `design-review`

**Use when:** “Review this working checkout flow and rank the design problems by
severity.”

**Returns:** an authoring-time, severity-rated findings list grounded in the
rendered artifact, shared quality floor, usability heuristics, clarity, and the
approved aesthetic reference.

**Routes away:** product-strategy review, bet selection/framing, and code or
implementation review. Use `creative-direction` to create a direction,
`information-architecture` to design hierarchy, and `design-system` to derive
tokens.

## Content and copy

The copy path has four owners in sequence: `tone-of-voice` defines the brand
register; `content-design` decides what the surface communicates and how it is
structured; `copy-direction` sets acquisition-surface copy goals; `ux-writing`
in product engineering writes product UI strings.

### `content-design`

**Use when:** “Before wireframes, decide what our onboarding page must say and
how the story should unfold.”

**Returns:** a content brief for acquisition, product, or reference surfaces,
including the message, audience, form, order, objective, and
`communication_mode`.

**Routes away:** organization-level content strategy, feature framing, and page
or content-system implementation. It does not own brand register,
acquisition-surface copy goals, or product UI strings.

### `copy-direction`

**Use when:** “Name the copy goals for this pricing-page hero before anyone
writes the lines.”

**Returns:** ranked, grounded copy goals for one marketing or acquisition
surface. Writes `<output_dir>/copy/<surface-slug>.md`.

**Routes away:** product/growth strategy, acquisition-bet framing, and surface
implementation. It may reference `tone-of-voice`, runs after `content-design`,
and does not own `ux-writing`'s product UI strings.

### `tone-of-voice`

**Use when:** “Our teams sound inconsistent; define the brand voice every
channel should share.”

**Returns:** a cross-surface brand register with named, ranked voice goals and
arbitration rules. Writes `<output_dir>/copy/brand-register.md`.

**Routes away:** organization-level product/content strategy, initiative
shaping, and copy implementation. It anchors but does not replace
`content-design`, `copy-direction`, or `ux-writing`.

## Surface genres

Declare the chosen genre once in the per-screen brief's `surface-genre:` field.
The matching skill applies that genre's method without replacing the connective
or craft skills.

### `conversion-design`

**Use when:** “Structure a pricing page so a qualified visitor understands the
offer and can act.”

**Returns:** information architecture and structural specifications for a
marketing or acquisition surface, including its above-fold and scroll story.

**Routes away:** go-to-market strategy, acquisition-initiative shaping, final
copy, and page implementation. Use `content-design` for message hierarchy,
`copy-direction` for copy goals, and the flow/interaction skills for product UI.

### `documentation-design`

**Use when:** “Design the help center so new users reach the right task guide
quickly.”

**Returns:** content-type, information-architecture, navigation-at-scale, and
first-value specifications for docs, help, or API-reference surfaces.

**Routes away:** organization-level documentation strategy, docs-platform
shaping, technical content authoring, and site/theme implementation. Use
`conversion-design` for marketing and `informational-design` for editorial
reading.

### `analytical-design`

**Use when:** “Design a monitoring view that helps operators spot a problem and
decide what to do.”

**Returns:** domain-model-first analytical information architecture, business
questions, role-aware views, and widget hierarchy. Individual chart code is not
the output.

**Routes away:** metric/outcome strategy, analytics-product shaping, and chart
or data-binding implementation. Use `interaction-design` for component behavior
and `workspace-design` for sustained-work tools.

### `informational-design`

**Use when:** “Design a long-form article template that stays readable through
dense material.”

**Returns:** typography, hierarchy, editorial grid, reading flow, and the next-
content path for an informational surface.

**Routes away:** editorial/product strategy, publishing-product shaping,
article writing, and template implementation. Use `documentation-design` for
task/reference systems and `conversion-design` for acquisition pages.

### `marketplace-design`

**Use when:** “Design catalogue filters and comparison views that help buyers
choose between listings.”

**Returns:** search, filter, listing, comparison, detail, and transaction-bridge
information architecture for a multi-party exchange.

**Routes away:** marketplace strategy, bet framing/sizing, implementation of
search/transactions, and listing copy. Use `conversion-design` for a
single-product marketing page and `workspace-design` for an internal tool.

### `workspace-design`

**Use when:** “Design a collaborative workspace that preserves context across
sessions and interruptions.”

**Returns:** a workspace-surface specification covering context persistence,
collaboration state, ambient attention, interruption handling, agentic patterns,
and session arcs.

**Routes away:** product strategy, feature appetite/scope, workspace
implementation, and UI-string authoring. Use `analytical-design` for dashboards,
`marketplace-design` for exchange surfaces, and `ux-writing` for UI strings.

## Independent reviewer

### `experience-reviewer`

The forked-context `experience-reviewer` is an agent, not a skill. It reads the
journey, screen flow, per-screen briefs, aesthetic reference, or rendered screen
and returns a verdict plus severity-tagged findings across aesthetic grounding,
platform fit, cross-brief coherence, state coverage, accessibility, and reduced
motion. It is read-only, never rewrites the artifact, and does not review code
diffs or architecture documents.

## `[design]` layout

Layout-aware artifact-writing skills resolve `<output_dir>` in three tiers: the
adopter-owned `[design] output_dir` in `agentbundle-layout.toml` (repository
setting before user setting), then the pack default `docs/design`, then
discovery by existing artifact markers. Each skill surfaces the resolved path
before its first write and creates its subdirectory only when needed.

**Current exception:** `design-principles` writes to the fixed
`docs/design/principles/<slug>.md` path, which is also where `design-review`
looks for a principles artifact. It does not currently use the configurable
`[design] output_dir` contract.

## Shared `quality-floor`

The canonical checklist lives at
`design-review/references/quality-floor.md` and is shared by consuming skills and
the reviewer. It requires:

1. Every applicable state, including empty, loading, error, success, partial,
   disabled, and permission/denied.
2. The recognized accessibility standard for the context, with keyboard,
   assistive-technology, target, timing, contrast, and non-color requirements.
3. Motion that communicates state and a reduced-motion path that preserves the
   same information.
