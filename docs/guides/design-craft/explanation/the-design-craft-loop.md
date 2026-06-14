# The design-craft loop

> **Explanation** — understanding-oriented. Why this pack is shaped the way it
> is. For the steps, see the [how-to](../how-to/author-design-intent.md); for
> the per-skill contract, see the [reference](../reference/design-craft.md).

## Design as upstream intent

A UI build consumes more than a feature spec. It consumes **design intent**:
what the product should feel like, the token and scale system that expresses
that feeling, how a screen is organized, and whether the result holds up to
scrutiny. When that intent is implicit — living only in a designer's head or a
pile of mockups — the build re-derives it badly, and every later choice
re-argues taste.

`design-craft` makes the intent explicit and durable, the way
`product-engineering` makes product intent explicit. It is the design-side twin
of that seam: the artifacts it produces (an aesthetic-direction doc, a token
taxonomy rationale, an information architecture, a critique) live in the repo
and steer the build.

## Four skills, one loop

The pack runs a recognizable loop — **direct → systematize → structure →
critique**:

1. **`aesthetic-direction`** — *direct.* Turn a vague "vibe" into a small set of
   named, ranked emotional and brand goals, and record which goal wins when two
   conflict. The output is direction every later choice points back to, instead
   of re-arguing taste.
2. **`design-system-foundations`** — *systematize.* Derive a token and scale
   taxonomy from those goals: name tokens by semantic role, organize scales
   around a single ratio-as-concept, treat accessibility as a floor, compose
   atomically.
3. **`layout-and-information-architecture`** — *structure.* Organize a screen or
   flow: rank content, choose a reading pattern, stage complexity with
   progressive disclosure, and keep the user oriented with wayfinding.
4. **`design-critique`** — *critique.* Evaluate an existing surface against
   recognized usability principles, map each issue to the principle it
   violates, rate its severity, and return a prioritized findings list.

The loop is not strictly linear — a critique sends you back to direction, a
layout question surfaces a missing token — but the four phases name the work.

## The shared `quality-floor`

All four skills clear a shared **`quality-floor` checklist**, three commitments
no design is done without:

- **Handle all states** — empty, loading, error, success, partial, disabled.
  The happy path is one state among several.
- **Accessibility floor** — meet the recognized standard (WCAG, at your
  context's level), read from the source.
- **Motion communicates state, honor reduced-motion** — motion earns its place
  by carrying meaning, and always offers a reduced-motion path that keeps the
  meaning.

`design-critique` applies the floor as an explicit pass; the authoring skills
reference it so the work never drifts below it.

## Why framework-agnostic

A design pack is the most tempting place to bake in a stack — a default
palette, a spacing scale, a CSS snippet, a component-library convention. The
charter's rule is "not a framework that picks your tech stack," so `design-craft`
ships **method, not values**. Two guardrails make that concrete:

- **Point to standards, never reprint values.** The skills name WCAG and the
  W3C Design Tokens interchange shape and teach you to *derive* your scales and
  tokens — they never hand you a palette or a ratio table.
- **Concepts, not platform primitives.** Wayfinding is orientation, not markup
  roles; layout is hierarchy and reading flow, not a grid system; motion is the
  reduced-motion *principle*, not a media query.

The payoff: the discipline travels to any repo, any stack, any toolchain, and
survives a framework change because it never depended on one. A pack-scoped lint
enforces the guardrails so a well-meaning edit can't quietly erode them.

## What's deliberately not here

`design-craft` is **habits, not infrastructure**. No hooks, no engine, no
in-pack validator, no reviewer subagent. `design-critique` is an interactive,
authoring-time **skill** you run in the conversation — not an automated
`work-loop` reviewer. A forked-context `design-reviewer` subagent is a possible
later proposal, deliberately left out of v1.
