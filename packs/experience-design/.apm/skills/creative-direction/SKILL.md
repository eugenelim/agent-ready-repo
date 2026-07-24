---
name: creative-direction
description: Use when a designer or stakeholder has a felt "vibe" but no named direction — turning a vague mood into ranked emotional/brand goals and an creative-direction doc the rest of the build references. Triggers on "make it feel premium/calm/playful", "I want it to feel like X", "what's the vibe here", "we need a look and feel", "before we pick colors/type". Runs the interrogation that converges a mood into named goals, grounds each goal in a stable referent (persona, precedent, standards, platform conventions), then records which goal wins when two goals conflict. Do NOT use to derive a token or scale taxonomy (use `design-token-taxonomy`), to structure hierarchy and reading flow (use `information-architecture`), or to evaluate an existing screen (use `design-review`). Do NOT use to name copy voice goals — use `copy-direction` for a specific surface or `tone-of-voice` for brand-level register.
---

# Skill: creative-direction

Turns a vague "vibe" into a small set of **named, ranked emotional and brand goals**, each grounded in a stable referent, and records them in an creative-direction doc the rest of the build references. The doc is the durable artifact: it lets every later choice point back to a goal and its referent, not a fresh opinion.

## When to invoke

Confirm all four before drafting; if any fails, push back and resolve it first.

1. **There is a real vibe to name** — the user can describe a feeling, an audience, or examples to react to. A blank "make it nice" is not yet a brief; draw out a first felt word before proceeding.
2. **The direction isn't already named** — no current creative-direction doc owns this surface. If one exists, you're amending it, not starting fresh.
3. **You're naming direction, not deriving values** — the moment the ask is spacing, type, or color *values*, hand off to `design-token-taxonomy`. This skill stops at named goals.
4. **You know the target surface** — `responsive-web`, `iOS`, `Android`, or `cross-platform`. If absent, elicit it before grounding the goals; platform conventions are a referent for every goal.

## Procedure

1. **Map the audience.** Name each distinct reader type for this surface, write one JTBD sentence per type ("When {situation}, I want to {action}, so that {goal}"), and rank them (primary, secondary). Load `references/audience-jtbd.md`. Feed the ranked map into Step 2 — the vibe that emerges should serve the primary reader's cognitive mode. Record the map in the doc; it becomes the Persona referent for each named goal in Step 3.
2. **Run the interrogation.** Open from the felt vibe, probe the emotions, associations, and brand attributes behind it, and converge on a short set of named goals — each a noun phrase a non-designer can recall. Sharpen each against its opposite. Load `references/interrogation-sequence.md`.
3. **Ground each goal in stable referents.** For each named goal, name *what grounds it*: the persona it serves, any precedent that carries the quality, the standards it respects, and the platform conventions for the target surface. A goal without a referent is still a fresh opinion — ground it or push it back to Step 2. Load `references/grounding.md`.
4. **Rank the goals.** Order them so a tie can break. The top goal is the dominant one that wins when goals conflict.
5. **Record arbitration.** For each likely conflict, name which goal wins and why, so the build doesn't re-litigate it. Load `references/coherence-arbitration.md`.
6. **Capture the doc.** Copy `assets/creative-direction-template.md` into the user's repo and fill it: the surface, the ranked goals with their referents, what each means and what would violate it, the dominant goal, and open questions.
7. **Hold the floor.** The direction must not fight the shared `quality-floor` checklist (`../design-review/references/quality-floor.md`) — accessibility is not negotiable against aesthetics. If a goal pulls against the floor, the floor wins; record it as an open question, not a trade-off.
8. **Hand off.** Once the goals are named, ranked, and grounded, hand to `design-token-taxonomy` to derive the tokens and scales that express them.

## Genre canonical reference tier

When grounding creative direction for a surface with a declared genre (from the per-screen brief's `surface-genre:` field), use the genre canonical reference tier below as the starting set for the **precedent** referent in step 3 (Grounding). These are **study subjects, not prescriptive tools** — internalize the structural philosophy, the spatial grammar, the aesthetic philosophy each site embodies. Do not copy the surface treatment; do not name any of these as required implementation tools; do not reproduce their values.

**marketing** — Stripe marketing (conviction-led copywriting, full-bleed typographic design), Linear homepage (developer-aesthetic minimalism, restraint as persuasion), Vercel marketing (clean technical tone, performance as aesthetic).

**documentation** — Stripe Docs (reference density and navigation at scale), Vercel Docs (tutorial clarity and search-first architecture), MDN Web Docs (type-consistency and machine-readability at reference depth).

**informational** — The Elements of Typographic Style (Bringhurst) for line length, leading, and scale principles; Stripe's blog for code-adjacent editorial clarity; The Pudding for narrative and data-visualization integration.

**analytical** — Linear (high-density status layout and task-state clarity), Retool (flexible widget hierarchy, data-dense spatial grammar), Metabase (progressive disclosure in data exploration, approachable analytical aesthetic).

**marketplace** — Airbnb (browse-first spatial warmth, social-proof hierarchy, map-integrated discovery), GitHub Marketplace (developer-tool catalogue aesthetic, badge-first trust signals), npm (search-first, high-density reference information).

**workspace** — Linear (keyboard-first productivity, task-state clarity, spatial minimalism), Notion (context-persistence, collaborative editing state, content-as-structure), Cursor (agentic UI legibility, HITL confirmation surfaces, code-adjacent aesthetic).

**transactional-journey** — Stripe Checkout (trust signals, error recovery, form clarity), Calendly (clean multi-step booking, friction-free time selection), Apple Pay / Google Pay one-step flows (minimal-friction commitment surfaces, confirmation as design priority).

For each goal you ground in step 3, name which qualities of the reference you are drawing on — and which you are leaving. "Make it like Stripe" is not a ground; "borrow Stripe's typographic restraint and section-break discipline, leave the dark-mode palette and full-bleed hero" is.

## Anti-patterns to refuse

- **Printing the answer.** No palette, font name, or spacing/timing value here. This skill produces *direction*, not the values that express it — those are `design-token-taxonomy`'s job.
- **Goals nobody can recall.** If a goal isn't a short noun phrase a non-designer remembers, it can't arbitrate a choice later. Rewrite it until it sticks.
- **Unranked goals.** A flat list of equals can't break a tie. Refuse to close without a dominant goal.
- **Ungrounded goals.** A goal with no persona, precedent, standard, or platform referent is still a fresh opinion. Refuse to record it until it has at least one stable referent.
- **Copying an example whole.** "Make it like X" is a starting probe, not a direction. Name *which qualities* of X you're after and which you're leaving — see the interrogation reference.
- **Re-deriving taste mid-build.** Once the doc exists, conflicts resolve against it, not against fresh opinion. Amend the doc deliberately; don't quietly drift.
- **Reprinting platform values.** Name the standard that grounds the goal (Apple HIG, Material 3, MDN responsive); never reprint its spacing, type, or motion values.
