---
name: layout-and-information-architecture
description: Use when designing how a screen or flow is organized — what goes where, in what order, and how a user stays oriented. Triggers on "structure this screen", "information architecture", "lay out this flow", "what's the hierarchy here", "how should this navigation be organized", "why does this page feel cluttered". Produces an information-architecture and layout reasoning doc — hierarchy, reading flow, progressive disclosure, and wayfinding as concepts. Do NOT use when the work is choosing mood, type, or color personality (use `aesthetic-direction`); when defining reusable tokens, scales, or component rules (use `design-system-foundations`); or when judging an existing design against a standard (use `design-critique`).
---

# Skill: layout-and-information-architecture

Produces an information architecture and the layout reasoning behind it for
a screen or flow — what belongs on the surface, in what order the eye should
meet it, and how the user stays oriented. Reasoning and concepts, never
layout code.

## When to invoke

Confirm before drafting:

- **Scope.** One screen, or a flow of several? Name the surfaces in play so
  the IA covers the whole journey, not a fragment.
- **Job and audience.** What is each surface *for*, and who scans it? The
  reading pattern and the depth-vs-breadth call both follow from this.
- **Content reality.** Roughly what content and how much — real or
  representative? Hierarchy reasoning on imagined content is wishful.

If the ask is mood/type/color, hand to `aesthetic-direction`; if it's
reusable tokens or component rules, `design-system-foundations`; if it's
judging an existing screen, `design-critique`.

## Procedure

1. **Frame the surface(s).** For each, write its one job and its audience.
   This anchors every later call.
2. **Rank the content.** List what must appear, then order it
   primary / secondary / tertiary. The rank is the design; the visuals just
   express it. See visual hierarchy in `references/reading-patterns.md`.
3. **Pick the reading pattern.** Choose F-pattern for dense, scannable
   surfaces and Z-pattern for sparse, hero-style ones, from the surface's
   job — not habit. Lay the ranked content along that scan path.
   (`references/reading-patterns.md`.)
4. **Stage the complexity.** Decide what shows now and what reveals on
   demand — progressive disclosure — so the surface stays legible without
   hiding anything essential. (`references/reading-patterns.md`.)
5. **Shape the navigation tree.** Trade depth against breadth so common
   destinations stay a few steps away and each level offers a handful of
   distinct, predictable choices. (`references/reading-patterns.md`.)
6. **Design wayfinding.** Make every screen answer *where am I, where can I
   go, how do I get back*; place landmarks, signposts, grouping, and
   consistent positions as concepts. (`references/wayfinding-concepts.md`.)
7. **Walk the states.** Run the surface against the shared
   `quality-floor` checklist
   (`../design-critique/references/quality-floor.md`). Empty, loading, and
   error states change the IA — first-run orients and invites, no-results
   shows recovery, loading preserves layout so the surface doesn't jump.
8. **Write the IA doc** — the ranked content, the reading pattern and why,
   the disclosure stages, the navigation shape, the wayfinding plan, and
   the per-state layout notes. Reasoning and rationale, no layout code.

## Anti-patterns to refuse

- **Reaching for markup or styling code.** This skill outputs concepts and
  reasoning. The moment the answer wants to be code, stop — that's the
  build's job, downstream of this.
- **Naming orientation as platform roles.** Describe landmarks, signposts,
  and "you are here" as the user's mental model. Roles and attributes are
  implementation; they never appear in the IA doc.
- **Flat rank — everything important.** If the content has no primary, the
  eye has no lead and the surface reads as noise. Force a rank order.
- **Designing the happy path only.** A surface isn't designed until its
  empty, loading, error, and partial states are. Skipping them ships a
  product that feels broken at the edges.
- **A tree that mirrors the schema or org chart.** Group by how users look
  for things, not by how the data is stored or the team is organized.
