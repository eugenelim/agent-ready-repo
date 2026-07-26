# Experience Design

> A user-scope pack of 19 skills and a forked-context experience-reviewer subagent for the full design thread — from journey mapping to per-screen craft — grounded in published standards, never pixel comps.

## Why this pack exists

Product teams designing screens without structured UX tooling default to the happy path: the interface works when everything goes right, but falls apart on errors, edge states, and the emotional arc of a real user session. Without a shared design methodology, handoffs between PMs, designers, and engineers carry implicit assumptions that only surface when users complain. With this pack, every design decision has an explicit method, an artifact format that engineers can build from, and an independent review from a subagent that never sees the authoring assumptions.

## What it is

**Skills (19) in two families:**

*Connective skills* walk the thread from outcome to surface: `journey-mapping` (map customer journey stages, actions, emotions, pains, and opportunities), `content-design` (decide what a surface says, for whom, before wireframes), `tone-of-voice` (turn a vague copy register into named copy goals and arbitration rules), `user-flow` (sequence screens and transitions with error flows and per-screen briefs), `service-blueprint` (map backing services across frontstage, backstage, and support rows), `process-mapping` (map internal operations as swimlane flows — as-is/to-be, SIPOC, pain register), `design-principles` (derive 3–5 named principles from journey insights to resolve design disputes).

*Craft skills* design and critique each screen: `creative-direction` (turn a vague mood into ranked emotional and brand goals), `design-system` (derive a token taxonomy from an aesthetic direction), `information-architecture` (organize a screen — hierarchy, reading flow, wayfinding), `interaction-design` (design the behavioral layer — states, validation, transitions, micro-interactions), `design-review` (severity-rated heuristic, accessibility, and aesthetic critique of an existing screen). Six surface-genre skills apply the full craft method to a specific screen type: `analytical-design`, `conversion-design`, `documentation-design`, `informational-design`, `marketplace-design`, `workspace-design`. Plus `experience-status` for read-only orientation to the current design thread.

**Subagents (1):** `experience-reviewer` — forked-context, design-time critique subagent. It receives only the artifact (journey map, screen flow, aesthetic direction, or generated screen), never the authoring chain of thought.

No seeds.

See the README for the complete manifest table.

## What it is not

- Not a prototyping tool — it produces design intent artifacts (flows, token taxonomies, screen briefs), not interactive mockups.
- Not a production design system — the token taxonomies it derives are design intent inputs; production implementation is the engineer's responsibility.
- Not a visual design tool — it outputs structured text artifacts that reference published standards (WCAG, Material 3, Apple HIG); it does not produce images or SVGs.

## How it relates to other packs

No required pack dependencies. Works alongside `core` when implementing a designed surface — core's `adversarial-reviewer` evaluates the implementation diff, while `experience-reviewer` evaluates the design artifact. The `architect` pack covers the systems layer above UX (service architecture, data flow, API contracts).
