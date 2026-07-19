---
name: information-architecture
description: Use when designing how a screen or flow is organized — what goes where, in what order, and how a user stays oriented. Triggers on "structure this screen", "information architecture", "lay out this flow", "what's the hierarchy here", "how should this navigation be organized", "why does this page feel cluttered". Produces an information-architecture and layout reasoning doc — hierarchy, reading flow, progressive disclosure, and wayfinding as concepts. Do NOT use when the work is choosing mood, type, or color personality (use `creative-direction`); when defining reusable tokens, scales, or component rules (use `design-system`); or when judging an existing design against a standard (use `design-review`).
---

# Skill: information-architecture

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
- **Success metric.** Before designing hierarchy, name the success metric —
  the measurable outcome the surface serves. What does "this surface worked" look
  like? (Examples: task completion rate, time to first action, conversion rate,
  findability score, session re-engagement after return.) The hierarchy design
  serves this metric; choices that cannot be traced to it are decoration.

If the ask is mood/type/color, hand to `creative-direction`; if it's
reusable tokens or component rules, `design-system`; if it's
judging an existing screen, `design-review`.

## Procedure

0. **Surface inventory (multi-surface platforms only).** If the subject is a multi-surface platform: (a) enumerate every surface and label its genre; (b) confirm which surface this pass covers; (c) note which other surfaces exist — they need separate passes; (d) flag: cross-surface wayfinding check required (see step 6). If the subject is a single surface, skip to step 1.

1. **Frame the surface(s) and route by genre.** For each, write its one job and
   its audience. This anchors every later call. Then **route by surface genre**:
   if the per-screen brief declares a `surface-genre:`, read the corresponding
   genre skill's output before designing hierarchy — the genre skill has already
   made the primary structural decisions for that surface type. If no brief exists,
   elicit the genre inline ("What kind of surface is this?").

   Use the genre routing table below to find the upstream skill output to read first:

   | Surface genre | Read before designing hierarchy |
   |--------------|--------------------------------|
   | `marketing` | `conversion-design` output — hero approach, scroll-story zones, above-fold spec |
   | `documentation` | `documentation-design` output — Diátaxis type map, navigation strategy, TTFV target |
   | `informational` | `informational-design` output — reading pattern, typographic hierarchy, editorial grid |
   | `analytical` | `analytical-design` output — widget tier hierarchy, spatial layout grammar, role-based views |
   | `marketplace` | `marketplace-design` output — card IA, filter architecture, browse-first vs. search-first |
   | `workspace` | `workspace-design` output — session arc, context-persistence patterns, attention zones |
   | `transactional-journey` | `interaction-design` wizard-and-stepper pattern families |

   If the genre is unknown, determine it before framing hierarchy — the genre determines the structural vocabulary.
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

   **Cross-surface wayfinding** (when this surface is part of a multi-surface platform): does every surface have a visible, persistent path to each other surface a user could reasonably want to return to? The path must be present on every page — not just the landing page and not just the footer. A footer link is the minimum; a persistent header element is the standard. Flag the absence of a docs→marketing bridge as a blocker finding: users entering via search have no context and no exit path.

7. **Walk the states.** Run the surface against the shared
   `quality-floor` checklist
   (`../design-review/references/quality-floor.md`). Empty, loading, and
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
