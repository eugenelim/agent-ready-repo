# `experience` — the skills, the reviewer, and the `quality-floor`

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

### `map-customer-journey`

**Triggers on:** "map the customer journey", "what does the user go through",
"journey map this flow", "what are the touchpoints", "where does the user feel
pain".

**Use when** a team needs to understand how a customer moves through an
experience end-to-end. Produces a journey map — stages × actions / emotions /
pains / opportunities, outside-in — carrying a `surface` axis. Customer/end-user
scoped (employee journeys are out of v1). **Consumed by** `map-screen-flow` and
`blueprint-service`.

**Do NOT use** to design screen interactions (use `map-screen-flow`), to
blueprint services (use `blueprint-service`), or to map an internal process (use
`map-internal-process`).

**Writes:** `<parent>/journeys/<slug>.md` (`type: customer-journey`).

### `map-screen-flow`

**Triggers on:** "map the screen flow", "what screens do we need", "sequence the
screens", "design the screen-to-screen flow", "what happens when this action
fails".

**Use when** a journey needs to become the screens that realize it. Produces a
**screen flow** — screens sequenced, with transitions and error/edge flows, a
per-screen state matrix (deferring to the quality floor), and the surface axis —
plus **one per-screen brief per screen** (shared-contract / per-screen-spec
split). Ends in a cross-brief consistency pass and a **non-droppable steel
thread** (prototype → text-only, never nothing). Can emit an optional design-tool
handover (instructions, never pixels). **Consumed by** the craft skills,
`voice-and-microcopy`, and `experience-reviewer`.

**Do NOT use** to map the journey (use `map-customer-journey`), to design
in-screen behavior (use `interaction-design`), or to blueprint services (use
`blueprint-service`).

**Writes:** `<parent>/screens/<slug>-flow.md` (`type: screen-flow`) + briefs at
`<parent>/screens/<slug>/<screen>.md` + optional `<screen>.handover.md`.

### `blueprint-service`

**Triggers on:** "blueprint the service", "what services back these screens",
"map frontstage and backstage", "what happens behind the line of visibility".

**Use when** the screens exist and the next question is what's behind them.
Produces a service blueprint — frontstage / line-of-visibility / backstage /
support. The backstage column is the slicing instrument handed **by-name** to
`architect` / `contracts` (named textually when those are absent). **Consumed
by** `architect` and the spec LLD.

**Do NOT use** to map the customer's experience (use `map-customer-journey`) or
to map an internal process with no customer touchpoint (use
`map-internal-process`).

**Writes:** `<parent>/blueprints/<slug>.md` (`type: service-blueprint`).

### `map-internal-process` — the inside-out sibling

**Triggers on:** "map our internal process", "current-state / target-state of
this workflow", "swimlane this process", "as-is and to-be for this operation".

**Use when** the process spans many touchpoints, has no customer-facing layer,
or is a constraint on the solution. Produces (anchored on APQC L3→L4): a SIPOC
scoping table, a mermaid swimlane (`flowchart` + `subgraph` lanes), **as-is + to-be**
with an as-is→to-be delta table, and a pain/waste register. Points to APQC PCF /
BPMN 2.0 / BABOK, reprints none. **Carries no surface axis.** Cross-references
the service blueprint by-name when customer-triggered; is the producer of
`product-engineering`'s `frame-intent` "current-state process map" input.

**Do NOT use** for the customer-facing journey (use `map-customer-journey`).

**Writes:** `<parent>/processes/<slug>.md` (`type: process-flow`).

## The craft

### `aesthetic-direction`

**Triggers on:** "make it feel premium/calm/playful", "I want it to feel like
X", "what's the vibe here", "we need a look and feel", "before we pick
colors/type".

**Use when** there's a felt "vibe" but no named direction. Converges a mood into
named, ranked goals, **grounds each goal in a stable referent** (persona,
precedent, standards, platform conventions for the target `surface`), records
what grounds each, and copies an aesthetic-direction doc into the repo. Stays
method-not-values.

**Ships:** `references/interrogation-sequence.md`,
`references/coherence-arbitration.md`, `references/grounding.md`, and
`assets/aesthetic-direction-template.md`.

### `design-system-foundations`

**Triggers on:** "derive a scale", "set up design tokens", "name our tokens",
"turn the direction into a system".

**Use when** a direction exists and the next move is a system. Derives a
token/scale taxonomy from intent — semantic-role naming, ratio-as-concept scales,
accessibility as a floor, atomic composition. Points to WCAG and the W3C Design
Tokens shape; **never reprints a values table.**

### `layout-and-information-architecture`

**Triggers on:** "structure this screen", "information architecture", "lay out
this flow", "what's the hierarchy here", "why does this page feel cluttered".

**Use when** designing how a screen or flow is organized — hierarchy, reading
flow, progressive disclosure, wayfinding, **as concepts** (never ARIA roles or
CSS grid).

### `interaction-design`

**Triggers on:** "design how this behaves", "what's the feedback for this
action", "model this component's states", "how should this form validate", "what
motion does this need".

**Use when** designing **how a screen behaves** — feedback & timing (the Doherty
perceived-performance lens, design-time), input & forms, a component **state
machine** (mermaid `stateDiagram-v2`; statecharts as the referent, never a
state-management library), purposeful motion (honors reduced-motion, reprints no
durations/easing), navigation-as-behavior, gesture/pointer on the surface axis,
and cognitive-law fit. **References** onboarding and search-interaction pattern
families. **Enriches the per-screen brief**; owns no file-per-slug artifact and
no layout entry.

**Do NOT confuse with** `layout-and-information-architecture` (structure),
`aesthetic-direction` (visual taste), the quality floor (the state *set*), or
`map-screen-flow` (the *cross-screen* macro flow). It owns the *in-component*
state machine, motion, and feedback.

### `design-critique`

**Triggers on:** "critique this design", "review this screen", "what's wrong
with this mockup", "do a heuristic eval", "is this usable".

**Use to** evaluate an existing screen — an interactive, **authoring-time**
critique. Applies the shared `quality-floor`, evaluates against usability
heuristics, and runs a **taste mode** (against the grounded aesthetic reference +
platform fit). Maps each issue to its principle, rates severity (0–4), returns a
prioritized list. It is **not fresh-context and not the reviewer agent** — a
same-session critique marks its own homework; the independent pass is
`experience-reviewer`.

**Ships:** `references/heuristics.md`, `references/taste-critique.md`,
`references/quality-floor.md` (the shared floor below).

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
`design-critique/references/quality-floor.md` and is referenced sibling-relative
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
