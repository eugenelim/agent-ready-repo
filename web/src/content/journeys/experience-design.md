---
pack: experience-design
scope: user
tagline: "The design/UX seat for product teams."
prerequisitePacks: []
whatChanges: "After installing experience-design, product-engineering work has a full design thread from outcome to realization. `journey-mapping` maps the journey; `content-design` and `tone-of-voice` name what the surface says and how it sounds. `design-principles` records the decision rules that hold screens to a shared standard. `user-flow` derives the screen list. `creative-direction` and `design-system` set the visual constraints. Genre-specific Direct skills (`analytical-design`, `conversion-design`, `documentation-design`, `informational-design`, `marketplace-design`, `workspace-design`) produce surface-appropriate IA before `interaction-design` and `design-review` craft and critique each screen. The forked-context `experience-reviewer` gives every design an independent pass — handle-all-states, WCAG 2.2 AA, reduced-motion. `experience-status` orients to the design thread at a glance — what artifacts exist, what's missing, and which skill to run next."
skills:
  - name: journey-mapping
    description: "Maps the current and desired customer journey to derive the key touchpoints and failure modes a product must address."
    humanTouches: 1
  - name: content-design
    description: "Produces a content brief for a surface — what it should say, for whom, in what form, and to what objective — before any wireframe or screen flow starts."
    humanTouches: 0
  - name: tone-of-voice
    description: "Turns a vague copy vibe into named, ranked copy goals grounded in stable referents, and records copy arbitration rules the rest of the build references."
    humanTouches: 0
  - name: user-flow
    description: "Derives the screen inventory and flow from the customer journey — what screens exist, what state each handles, what the transitions are."
    humanTouches: 1
  - name: service-blueprint
    description: "Maps front-stage screen flows to the back-stage processes and human actors that support them — the service blueprint."
    humanTouches: 0
  - name: process-mapping
    description: "Documents the internal processes that run behind user-facing screens — the APQC/BPMN model of what people do."
    humanTouches: 0
  - name: design-principles
    description: "Converts journey-map insights into 3–5 named design principles — decision rules that resolve disputes and persist across sprints, each grounded in a journey moment."
    humanTouches: 0
  - name: creative-direction
    description: "Establishes the visual direction for a surface — named emotional and brand goals grounded in stable referents — as the aesthetic reference all subsequent screens must satisfy."
    humanTouches: 1
  - name: design-system
    description: "Derives the design token set from the creative direction — the primitive and semantic tokens that carry the design into code."
    humanTouches: 0
  - name: information-architecture
    description: "Designs the layout zones and information hierarchy for a screen, given its per-screen brief."
    humanTouches: 0
  - name: analytical-design
    description: "Produces a structural specification for an analytical surface — dashboard IA, widget hierarchy, and role-based view architecture — from business questions and domain model."
    humanTouches: 0
  - name: conversion-design
    description: "Produces a structural specification for a marketing surface — above-fold contract, scroll story, and social-proof architecture — from content brief and design principles."
    humanTouches: 0
  - name: documentation-design
    description: "Produces a structural specification for a documentation surface — content hierarchy, navigation strategy, and TTFV architecture — from Diátaxis content typing and reading goal."
    humanTouches: 0
  - name: informational-design
    description: "Produces a structural specification for an informational surface — typographic hierarchy, reading-pattern calibration, and editorial grid — from editorial structure and reading goal."
    humanTouches: 0
  - name: marketplace-design
    description: "Produces a structural specification for a marketplace surface — listing card IA, filter and facet architecture, and transaction bridge — from buyer journey and listing object model."
    humanTouches: 0
  - name: workspace-design
    description: "Produces a structural specification for a workspace surface — context-persistence architecture, attention zone layout, and interrupt design — from session arc and collaboration model."
    humanTouches: 0
  - name: interaction-design
    description: "Designs the interactive behaviors for a screen — states, transitions, feedback patterns — against WCAG 2.2 AA."
    humanTouches: 0
  - name: design-review
    description: "Reviews an existing screen design against the quality floor — handle-all-states, accessibility, reduced-motion — before the independent review."
    humanTouches: 0
  - name: experience-status
    description: "Orients to the current design thread at a glance — reads design artifacts from the configured output directory and surfaces what exists, what's missing, and which skill to run next."
    humanTouches: 0
humanGates:
  - id: G-journey
    globalGate: null
    label: "Approve the customer journey and derived screen list"
    trigger: "After journey-mapping and user-flow complete"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the journey capture the outcome the user is trying to achieve — not just the tasks they perform in the current product?"
      - "Is the screen list derived from the journey, not from the existing implementation or a wish list?"
      - "Are the key failure modes named — the moments the current journey breaks down, and why?"
      - "Is every screen in the list implied by the journey? (Remove screens that aren't.)"
    whatGoodLooksLike: "A journey map that names the outcome, the failure modes, and a screen list with a clear derivation — each screen traceable to a moment in the journey."
    whatBadLooksLike: "A screen list that maps to the current implementation screen-by-screen. This means the agent documented the status quo instead of designing for the outcome."
    consequence: "The screen list is the contract for all design work that follows. A screen list derived from the wrong model means the design thread designs the wrong product — faithfully."
  - id: G-aesthetic
    globalGate: null
    label: "Approve the aesthetic direction and token set"
    trigger: "After creative-direction and optionally design-system complete"
    duration: "5–10 minutes"
    whatToCheck:
      - "Does the aesthetic direction name a specific visual character — not just 'clean and modern'?"
      - "Are the contrast ratios in the token set verified at WCAG 2.2 AA minimum?"
      - "Is the palette constrained to a small number of semantic roles — does adding a new color require a decision?"
      - "Are the tokens derived from the aesthetic direction, not borrowed from a generic design system?"
    whatGoodLooksLike: "A named aesthetic reference with a token set that derives directly from it, passes the contrast floor, and could be handed to a developer without ambiguity."
    whatBadLooksLike: "An aesthetic direction that could apply to any product, or a token set that introduces hardcoded values outside the semantic token system."
    consequence: "The aesthetic direction is the constraint every subsequent screen must satisfy. Approving a vague direction means screens drift with no shared reference to hold them together — and the experience-reviewer will flag every screen for the same missing constraint."
  - id: G-experience-review
    globalGate: null
    label: "Review the designs after the independent experience-reviewer pass"
    trigger: "After the experience-reviewer subagent returns findings on the completed screen designs"
    duration: "15–25 minutes"
    whatToCheck:
      - "Did the reviewer flag any handle-all-states violations? (Missing empty, loading, error, or success states are the most common finding.)"
      - "Are all WCAG 2.2 AA requirements met — color contrast, label associations, focus order?"
      - "Is reduced-motion handled — are transitions guarded with prefers-reduced-motion?"
      - "Are the screens consistent with the approved aesthetic direction — or did any screen introduce its own visual language?"
    whatGoodLooksLike: "A design set that the independent reviewer marks clean — all states handled, accessibility floor met, aesthetic direction consistently applied across every screen."
    whatBadLooksLike: "Screens that look good in the happy-path state but have no designed empty state, loading state, or error recovery. Or screens that pass visually but fail the accessibility audit."
    consequence: "The experience-reviewer is the design analogue of adversarial-reviewer in the build loop. Its findings are the last check before design intent feeds the build. An unreviewed design is a set of unverified assumptions about how the product behaves when things go wrong."
typicalSession:
  agentTurns: "8–15"
  humanTouches: 3
  wallClockMinutes: "45–90"
docsUrl: /docs/guides/experience-design/
packUrl: /packs/experience-design/
relatedJourneys:
  - architect
  - core
---

## Stage 1 — Map the customer journey

You describe the feature, user, and outcome. The agent runs `journey-mapping` to produce the customer journey map — the current state (what happens today), the desired state (what should happen after this feature), and the key moments where the current journey breaks down.

With the journey in hand, the agent can run `content-design` to produce a content brief — what the surface should say, for whom, and to what objective — and `tone-of-voice` to name the copy direction. These run before the screen flow is derived, so the surface's content intent and register are set as constraints before screens are sequenced. The content brief and copy direction don't require a separate gate; review them informally when you read the journey map.

**You:** Read the journey map and approve it at the G-journey gate. This is the most important gate in the experience thread — the screen list flows directly from it. If the map describes what the current product does rather than what the user is trying to achieve, redirect before the screen flow is derived. A one-sentence correction here saves a full design cycle.

---

## Stage 2 — Derive the screen flow

With the journey approved, the agent runs `user-flow` to derive the screen inventory: what screens exist, what state each one handles (empty, loading, populated, error), and what the transitions between them are. Each screen gets a per-screen brief: the user's goal, the information they need, the states to handle.

**You:** Check that the screen list feels right — that it doesn't add screens not implied by the journey, and doesn't miss screens the journey requires. If the agent adds a screen that looks useful but isn't derived from the journey, remove it here.

---

## Stage 3 — Establish design intent

Before designing any screen, the agent runs `design-principles` to convert journey-map insights into 3–5 named decision rules — the principles that resolve design disputes and hold screens to a shared standard across the sprint. The principles don't require a separate gate; review them alongside the aesthetic direction below. The agent then runs `creative-direction` to establish the visual character of the surface — named emotional and brand goals grounded in stable referents — as a named aesthetic reference. `design-system` derives the design token set from that direction.

**You:** Approve the aesthetic direction at the G-aesthetic gate. An aesthetic direction that says "clean and professional" is not an aesthetic direction — it needs to name a specific visual character with enough specificity to say whether a given design decision is consistent or not. If the tokens introduce hardcoded values outside the semantic token system, reject them.

---

## Stage 4 — Design each screen

The agent runs a structural IA skill on each screen before `interaction-design`. For general screens it uses `information-architecture`. When a screen has a specific surface genre, a genre-specific Direct skill produces a more targeted specification: `analytical-design` for dashboards and reporting views; `conversion-design` for marketing and acquisition surfaces; `documentation-design` for docs sites and help centres; `informational-design` for article and editorial pages; `marketplace-design` for catalogue and listing surfaces; `workspace-design` for productivity and agentic tool UIs. Once the IA is set, `interaction-design` designs the states, transitions, and feedback patterns, and `design-review` applies the quality floor as a self-check before the independent review.

**You:** Watch each screen take shape. If a screen is missing a state — no empty state for a list that could be empty, no loading state for an async action — name it. The agent will miss states not explicitly mentioned in the brief; that's what the experience-reviewer catches, but catching it here is cheaper.

---

## Stage 5 — Independent review

The agent runs the `experience-reviewer` subagent in a forked context — a reviewer that has not seen the authoring session. The reviewer returns findings on the full screen set: handle-all-states violations, accessibility failures, aesthetic inconsistencies.

**You:** Read the review findings at the G-experience-review gate. Handle-all-states violations are the most common finding — a screen that works for the happy path but has no designed error state. WCAG findings affect all users. Apply Blockers before the design intent feeds the build loop; they represent the floor the spec says all screens must clear.
