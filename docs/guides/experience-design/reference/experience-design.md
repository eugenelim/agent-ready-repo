# `experience-design` — the skills, the reviewer, and the `quality-floor`

> **Reference** — information-oriented. The contract for each skill and the
> reviewer agent: when it triggers, what it produces, and what it routes away
> to. Mirrors the shipped `SKILL.md` / agent frontmatter; if a description
> changes, update this page in the same PR. For the steps, see the
> [how-to](../how-to/author-design-intent.md).

All skills are pure-markdown, framework-agnostic, and user-scope by default.
They install across all seven adapters (Claude Code, Codex, Copilot, Cursor,
Gemini, Kiro IDE, Kiro CLI). The artifact-writing skills resolve their output
path through the `[experience]` layout table (below).

## The connective thread

### `journey-mapping`

Use when a product team needs to understand how a customer moves through an experience end-to-end — mapping the stages, actions, emotions, pains, and opportunities along the path. Triggers on "map the customer journey", "what does the user go through", "journey map this flow", "map out the experience stages", "what are the customer touchpoints", "where does the user feel pain". Carries a platform/surface axis (responsive-web, iOS, Android, cross-platform) that changes what the method asks at each stage. Scoped to customer/end-user journeys only — employee journeys are out of v1. Do NOT use to design screen interactions (use `user-flow`), to blueprint the backing services (use `service-blueprint`), or to map an internal business process (use `process-mapping`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `user-flow`

Use when a customer journey needs to become the screens that realize it — sequencing the screens, the transitions between them, and the error/edge flows (a failed action lands the user where?), then emitting one self-contained brief per screen. Triggers on map the screen flow, what screens do we need, sequence the screens for this journey, design the screen-to-screen flow, what happens when this action fails, turn this journey into screens. Carries a platform/surface axis and ends in a whole-journey walk that never skips. Do NOT use to map the journey itself (use journey-mapping), to design how one screen behaves internally (use interaction-design), or to blueprint the backing services (use service-blueprint). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `service-blueprint`

Use when you need to map the backing services that fulfil a customer journey — building a service blueprint with four rows (frontstage / line-of-visibility / backstage / support) that ties every screen action to the service or system behind it. Triggers on "service blueprint", "what backs this screen", "map the backstage", "what services support this journey", "blueprint the service". Do NOT use to map the customer journey itself (use `journey-mapping`), to sequence screens and their transitions (use `user-flow`), or to derive a token/scale taxonomy (use `design-token-taxonomy`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `process-mapping` — the inside-out sibling

Use when a team needs to understand, document, or improve how an internal business operation works — mapping an APQC L3 process end-to-end as a swimlane flow with as-is and to-be states, a SIPOC scoping table, and a pain/waste register. Triggers on "map our internal process", "document this business process", "what does our current process look like", "as-is to-be process", "process improvement", "how does this workflow actually work", "swimlane diagram for this process", "map the claims process", "map the order fulfilment flow". This is the inside-out operations sibling of `journey-mapping`. Do NOT use to map what a customer experiences (use `journey-mapping`), to blueprint how screens tie to backing services (use `service-blueprint`), or to sequence screen transitions (use `user-flow`). Does NOT carry a platform/surface axis — it is actor/swimlane-shaped, not device-shaped. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

## The Define phase

### `design-principles`

Use when a design team needs shared, durable decision rules — converting journey-map insights and opportunity pains into 3–5 named principles that resolve design disputes and persist across sprints. Triggers on "what are our design principles", "how do we make design decisions consistently", "we keep relitigating the same tradeoffs", "write our design principles", "derive principles from this journey". Produces principles in the form [Imperative verb] + [what] + [why/for whom] with an arbitration test. Do NOT use to set visual direction (use `creative-direction`), to derive a token/scale taxonomy (use `design-token-taxonomy`), or to evaluate an existing screen (use `design-review`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

## The craft

### `creative-direction`

Use when a designer or stakeholder has a felt "vibe" but no named direction — turning a vague mood into ranked emotional/brand goals and an creative-direction doc the rest of the build references. Triggers on "make it feel premium/calm/playful", "I want it to feel like X", "what's the vibe here", "we need a look and feel", "before we pick colors/type". Runs the interrogation that converges a mood into named goals, grounds each goal in a stable referent (persona, precedent, standards, platform conventions), then records which goal wins when two goals conflict. Do NOT use to derive a token or scale taxonomy (use `design-token-taxonomy`), to structure hierarchy and reading flow (use `information-architecture`), or to evaluate an existing screen (use `design-review`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `design-token-taxonomy`

Use when an aesthetic direction exists and the next move is naming the token taxonomy — deriving a token/scale taxonomy and its rationale from intent. Triggers on "derive a token taxonomy", "name our tokens by semantic role", "what should our token naming convention be", "derive our spacing and type scale from the direction". Names tokens by semantic role, organizes scales by a single ratio-as-concept, treats accessibility as a floor, and composes atomically (build systems, not pages). Do NOT use to set up or implement the token foundation for a project — use `design-system-foundations` for that. Do NOT use to set the vibe first (use `creative-direction`), to lay out a screen's hierarchy and flow (use `information-architecture`), or to evaluate an existing surface (use `design-review`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `design-system-foundations`

Use when a token taxonomy exists and the next step is applying it as a working token foundation. Triggers on "apply design token foundations", "set up our token implementation", "build the design token foundation for this project", "implement the token system", "create the light and dark themes", "set up semantic aliases for our components". Takes a derived token taxonomy (from `design-token-taxonomy`) and produces the working foundation — lightweight mode covers semantic color roles, typography, spacing, radius, focus styles, key statuses, responsive breakpoints, and core component tokens; full mode adds DTCG 2025.10-compatible token source, light/dark theme switching, semantic alias layer, and full component anatomy. Near-misses — do not use to derive the taxonomy (use `design-token-taxonomy`), name felt direction (use `creative-direction`), evaluate an existing surface (use `design-review`), or structure hierarchy and reading flow (use `information-architecture`).

### `information-architecture`

Use when designing how a screen or flow is organized — what goes where, in what order, and how a user stays oriented. Triggers on "structure this screen", "information architecture", "lay out this flow", "what's the hierarchy here", "how should this navigation be organized", "why does this page feel cluttered". Produces an information-architecture and layout reasoning doc — hierarchy, reading flow, progressive disclosure, and wayfinding as concepts. Do NOT use when the work is choosing mood, type, or color personality (use `creative-direction`); when defining a token/scale taxonomy (use `design-token-taxonomy`); or when judging an existing design against a standard (use `design-review`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `interaction-design`

Use when a screen or component needs its behavioral layer designed — how it responds to actions, validates input, transitions between states, and guides users through gesture and cognitive fit. Triggers on "design how this form behaves", "what happens when the user taps submit", "design the loading and error states", "map the state machine for this component", "design the micro-interactions", "how should this feel to use". Do NOT use to structure hierarchy or wayfinding (use `information-architecture`), to name aesthetic direction (use `creative-direction`), to map cross-screen navigation routes (use `user-flow`), or to enumerate which states exist (that enumeration belongs to the shared quality floor). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `design-review`

Evaluate an existing screen, flow, or mockup with a severity-rated findings list using a three-pass structure: Pass 1 cold-read (audience, job, rendered state only); Pass 2 primary task and one unhappy path (desktop, tablet, mobile, keyboard, focus, zoom, reduced-motion); Pass 3 contract review (quality-floor, heuristics, marketing clarity, taste). Triggers on "critique this design", "review this screen", "what is wrong with this mockup", "do a heuristic eval", "is this usable", "does this fit our aesthetic", "does this page convert", "is this copy compelling", "tweet test". Do NOT use to name a felt direction (use creative-direction), to derive tokens (use design-token-taxonomy), or to structure hierarchy (use information-architecture). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `content-design`

Use when a designer or product person needs to decide what a surface should say, for whom, in what form, and to what objective — before any wireframe or screen flow is opened. Routes across two surface types: acquisition surfaces (marketing pages, landing pages, web onboarding flows) and product/reference surfaces (help pages, feature reference, in-product wayfinding). Triggers on "what should this landing page say", "write a content brief for our onboarding flow", "what's the narrative arc for this marketing page", "what does this feature page need to communicate", "help me decide the above-fold structure". Do NOT use to write final copy (use `tone-of-voice` for copy voice, then `ux-writing` for UI strings), to produce an analytics or CRO measurement framework, or to generate SEO keyword plans. Do NOT use for copy voice — use `copy-direction` (surface) or `tone-of-voice` (brand). Do NOT use for per-state UI strings — use `ux-writing` in the `product-engineering` pack.

### `tone-of-voice`

Use when a designer, copywriter, or builder has a felt "copy vibe" but no named direction — turning a vague register sense into ranked copy goals grounded in stable referents (persona language, copy precedents, persuasion standards), and recording copy arbitration rules the rest of the build references. Triggers on "what voice should our copy have", "write a tone-of-voice doc", "what is our brand register", "how should our brand sound across channels", "copy vibe check". Do NOT use for product UI copy states (error messages, empty states, button labels, form labels) — use `ux-writing` in the `product-engineering` pack for those. Do NOT use for SEO keyword targeting, advertising copy templates, or brand identity documentation. Do NOT use if you need copy direction for a specific marketing or acquisition surface (landing page, above-fold hero, announcement) — use `copy-direction` for that surface-specific scope.

### `copy-direction`

Use when the surface needs a defined copy voice — turning a vague 'how we sound' into named, ranked copy goals grounded in stable referents (persona language, copy precedents, persuasion standards), and recording copy arbitration rules the rest of the build references. Triggers on "what should our marketing copy sound like", "copy voice for our landing page", "how does our headline differ from competitors", "what should our positioning copy feel like", "before we write the hero copy we need to name the direction". Do NOT use for product UI strings (error messages, empty states, button labels) — use `ux-writing` in the `product-engineering` pack for those. Do NOT use for SEO keyword targeting or full brand identity documentation. Do NOT use for content structure or section jobs — use `content-design`. Do NOT use for general brand tone — use `tone-of-voice`.

## Genre-specific design

Declare the surface genre once in the per-screen brief's `surface-genre:` field; downstream skills read it to apply genre-appropriate methodology.

### `conversion-design`

Use when designing a marketing surface — a landing page, product homepage, pricing page, or acquisition flow — where the primary goal is to convert a visitor into a lead, trial user, or customer. Triggers on "design the landing page", "structure the homepage", "what goes above the fold", "convert visitors", "design the pricing page", "product marketing surface". Produces IA and structural specifications for conversion surfaces. Do NOT use for product UI design (use user-flow + interaction-design), documentation surfaces (use documentation-design), or analytical dashboards (use analytical-design). Surface genre: marketing. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `documentation-design`

Use when designing a documentation surface — a docs site, a help centre, an API reference, or a technical guide set. Decides what type of content belongs where, how navigation scales with content volume, and what the first-value-moment is for each content type. Triggers on "design the docs site", "structure the help centre", "what goes on the docs landing page", "how should we navigate the API reference", "TTFV for this tutorial". Produces IA and navigation specifications for documentation surfaces. Do NOT use for marketing surfaces (use conversion-design) or informational editorial pages (use informational-design). Surface genre: documentation. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `analytical-design`

Use when designing an analytical surface — a dashboard, a reporting view, a monitoring screen, or any surface whose primary purpose is to help a user understand a data set and act on it. Triggers on "design the dashboard", "structure the reporting view", "what goes on the analytics screen", "KPI layout", "design a monitoring view". Produces domain-model-first IA and widget hierarchy specifications. Scope boundary — individual chart encoding design is out of scope (use interaction-design for component state machines); this skill handles dashboard IA only. Do NOT use for marketing surfaces (use conversion-design) or workspace productivity surfaces (use workspace-design). Surface genre: analytical. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `marketplace-design`

Use when designing a marketplace surface — a catalogue, a listing grid, a product detail page, or a buying/transaction flow that connects buyers and sellers or producers and consumers. Triggers on "design the marketplace", "structure the listing page", "how should the catalogue work", "design the search and filter", "buyer journey on the marketplace", "product card design". Produces IA specifications for catalogue, filter, comparison, and transaction bridge surfaces. Do NOT use for single-product marketing surfaces (use conversion-design) or workspace tool surfaces (use workspace-design). Surface genre: marketplace. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `informational-design`

Use when designing an informational surface — an article page, a news or editorial page, a long-form content page, or a content-rich page whose primary purpose is to inform, not to convert or enable tasks. Triggers on "design the article page", "structure the editorial page", "how should the blog look", "long-form content design", "reading experience design". Uses typography as the primary design tool. Do NOT use for documentation (use documentation-design), marketing (use conversion-design), or tool/app surfaces (use workspace-design). Surface genre: informational. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

### `workspace-design`

Use when designing a workspace surface — a productivity tool, a collaborative environment, an agentic UI, or any surface whose primary purpose is to support sustained professional work across sessions. Triggers on "design the workspace", "structure the tool UI", "collaborative editing surface", "agentic UI design", "multi-agent coordination UI", "task management surface", "session arc design". Covers context-persistence, collaboration state IA, ambient attention, agentic patterns, and interrupt design. Do NOT use for dashboards and monitoring views (use analytical-design) or marketplace surfaces (use marketplace-design). Surface genre: workspace. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

## Status and orientation

### `experience-status`

Orient to the current design thread at a glance — reads design artifacts from the configured output directory and surfaces what exists, what's missing, and which skill to run next. Triggers on "where are we with the design", "what experience artifacts do we have", "status of the design thread", "what's next in the design", "show me what design work exists", or any cold-start orient for the experience-design work thread. Read-only: never writes files, never elicits configuration. Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.

## The reviewer agent

### `experience-reviewer`

A **forked-context, read-only** agent (not a skill) — the independent design-time
review. Reviews the journey, the screen flow + per-screen briefs, the aesthetic,
or a generated screen against four lenses: the **grounded aesthetic reference**,
**platform fit**, **cross-brief coherence**, and the **full quality floor**
(handle-all-states + accessibility + reduced-motion) — accessibility being the
one independent a11y check between human-value-add gates. Returns a verdict
(SHIP IT / SHIP WITH CHANGES / MAJOR REWRITE / WRONG ARTIFACT) + severity-tagged
findings. It flags, never rewrites; it never reviews code diffs (core's
reviewers) or architecture design docs (architect's `design-reviewer`).

## The `[experience]` layout

The artifact-writing skills resolve `<parent>` in three tiers — **config**
(`[experience]` table in the adopter-owned `agentbundle-layout.toml`, repo-root
over user-profile) → **default** (`docs/design`, the pack's `[pack.layout.repo]`)
→ **discover-by-marker** (scan for the frontmatter `type:` anchors:
`customer-journey` / `service-blueprint` / `screen-flow` / `process-flow`). Each
skill surfaces the resolved path before its first write and creates its dir
lazily. See any artifact-writing skill's `references/agentbundle-layout.md`.

## The `quality-floor` checklist

One shared floor every artifact clears. Lives at
`design-review/references/quality-floor.md` and is referenced sibling-relative
by every consuming skill (and the reviewer); a pack-level `references/` dir does
not project, so the single resident file is the shared home. Three commitments:

1. **Handle all states** — empty (first-run vs no-results), loading, error,
   success, partial, disabled, plus `permission/denied` as an *additional* gated
   state. A surface isn't designed until every state it can be in is designed.
2. **Accessibility floor** — meet the recognized standard (WCAG, at your
   context's level), read from the source. Perceivable contrast, operable
   without a pointer, meaning never on one channel alone, named for assistive
   tech, forgiving targets and timing. Points to the standard; never reprints a
   ratio.
3. **Motion communicates state — honor reduced-motion.** Motion earns its place
   by carrying meaning; always provide a reduced-motion path that preserves the
   information without the movement.
