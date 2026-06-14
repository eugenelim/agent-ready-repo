# `design-craft` — the four skills and the `quality-floor` checklist

> **Reference** — information-oriented. The contract for each skill: when it
> triggers, what it produces, and what it routes away to. Mirrors the shipped
> `SKILL.md` frontmatter; if a skill's `description` changes, update this page
> in the same PR. For the steps, see the
> [how-to](../how-to/author-design-intent.md).

All four skills are pure-markdown, framework-agnostic, and user-scope by
default. They install across all seven adapters (Claude Code, Codex, Copilot,
Cursor, Gemini, Kiro IDE, Kiro CLI).

## `aesthetic-direction`

**Triggers on:** "make it feel premium/calm/playful", "I want it to feel like
X", "what's the vibe here", "we need a look and feel", "before we pick
colors/type".

**Use when** a designer or stakeholder has a felt "vibe" but no named
direction. Runs the interrogation that converges a mood into named, ranked
emotional/brand goals, records which goal wins when two conflict, and copies an
**aesthetic-direction doc** into the repo as the durable artifact.

**Do NOT use** to derive a token or scale taxonomy (use
`design-system-foundations`), to structure hierarchy and reading flow (use
`layout-and-information-architecture`), or to evaluate an existing screen (use
`design-critique`).

**Ships:** `references/interrogation-sequence.md`,
`references/coherence-arbitration.md`, and an
`assets/aesthetic-direction-template.md` copied into the repo at runtime.

## `design-system-foundations`

**Triggers on:** "derive a scale", "set up design tokens", "name our tokens",
"what's our spacing/type system", "turn the direction into a system".

**Use when** an aesthetic direction exists and the next move is a system.
Derives a token/scale taxonomy and its rationale from intent: names tokens by
semantic role, organizes scales by a single ratio-as-concept, treats
accessibility as a floor, and composes atomically (build systems, not pages).
Points to WCAG and the W3C Design Tokens interchange shape; **never reprints a
values table**.

**Do NOT use** to set the vibe first (use `aesthetic-direction`), to lay out a
screen's hierarchy and flow (use `layout-and-information-architecture`), or to
evaluate an existing surface (use `design-critique`).

**Ships:** `references/token-taxonomy-derivation.md`,
`references/atomic-composition.md`.

## `layout-and-information-architecture`

**Triggers on:** "structure this screen", "information architecture", "lay out
this flow", "what's the hierarchy here", "how should this navigation be
organized", "why does this page feel cluttered".

**Use when** designing how a screen or flow is organized — what goes where, in
what order, and how a user stays oriented. Produces an information-architecture
and layout reasoning doc covering hierarchy, reading flow, progressive
disclosure, and wayfinding **as concepts** — never ARIA roles or CSS grid, no
layout code.

**Do NOT use** when the work is choosing mood, type, or color personality (use
`aesthetic-direction`); when defining reusable tokens, scales, or component
rules (use `design-system-foundations`); or when judging an existing design
against a standard (use `design-critique`).

**Ships:** `references/reading-patterns.md`, `references/wayfinding-concepts.md`.

## `design-critique`

**Triggers on:** "critique this design", "review this screen", "what's wrong
with this mockup", "do a heuristic eval", "is this usable".

**Use to** evaluate an existing screen, flow, or mockup — an interactive,
authoring-time heuristic critique that reviews against recognized usability
principles, maps each issue to the principle it violates, rates severity (0–4),
and returns a prioritized findings list with a fix per finding. Applies the
shared `quality-floor` checklist as part of the pass. It is a **skill**, not a
`work-loop` reviewer subagent.

**Do NOT use** to name a felt direction (use `aesthetic-direction`), to derive
tokens or scales (use `design-system-foundations`), or to structure hierarchy
and reading flow (use `layout-and-information-architecture`).

**Ships:** `references/heuristics.md` (Nielsen's 10 principles + the severity
scale) and `references/quality-floor.md` (the shared checklist below).

## The `quality-floor` checklist

The shared floor every design-craft artifact clears. Lives at
`design-critique/references/quality-floor.md`; the authoring skills reference
it, `design-critique` applies it as an explicit pass. Three commitments:

1. **Handle all states** — empty (distinguish first-run from no-results),
   loading, error, success, partial, disabled/unavailable. A surface isn't
   designed until every state it can be in is designed.
2. **Accessibility floor** — meet the recognized standard (WCAG, at the
   conformance level your context requires), read from the source. Perceivable
   contrast, operable without a pointer, meaning never on one channel alone,
   named for assistive tech, forgiving targets and timing. The checklist points
   to the standard; it never reprints a ratio.
3. **Motion communicates state — honor reduced-motion.** Motion earns its place
   by carrying meaning (state change, continuity, spatial relationship). Every
   animation answers "what does this tell the user?"; always provide a
   reduced-motion path that preserves the information without the movement.
