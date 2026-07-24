---
pack: experience-design
scope: user
tagline: "The design/UX seat for product teams."
prerequisitePacks: []
contract:
  useItWhen: "A product team needs a full design thread — from outcome to independently-reviewed screens — before build begins."
  youProvide: "The feature, user, and intended outcome, plus any existing brand or design-system constraints."
  youReceive: "A complete, independently-reviewed design set — journey map, screen inventory, interaction specs, and accessibility-clean designs."
  yourDecisions:
    - "Approve the customer journey and derived screen list"
    - "Approve the aesthetic direction and token set"
    - "Review the designs after the independent experience-reviewer pass"
whatChanges: "After installing experience-design, product-engineering work has a full design thread from outcome to realization. `journey-mapping` maps the journey; `content-design` and `tone-of-voice` name what the surface says and how it sounds. `design-principles` records the decision rules that hold screens to a shared standard. `user-flow` derives the screen list. `creative-direction` and `design-system` set the visual constraints. Genre-specific Direct skills (`analytical-design`, `conversion-design`, `documentation-design`, `informational-design`, `marketplace-design`, `workspace-design`) produce surface-appropriate IA before `interaction-design` and `design-review` craft and critique each screen. The forked-context `experience-reviewer` gives every design an independent pass — handle-all-states, WCAG 2.2 AA, reduced-motion. `experience-status` orients to the design thread at a glance — what artifacts exist, what's missing, and which skill to run next. Experience design skills fill the Experience Design section of the Digital Experience Contract — the shared schema that connects strategy intent to rendered evidence."
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

### 1. Map the customer journey

- **You provide:** the feature, user, and intended outcome.
- **Agent does:** runs `journey-mapping` to produce the current-state and desired-state journey map with key failure modes; then runs `content-design` and `tone-of-voice` to set content intent and register before screens are sequenced.
- **You do:** read the journey map and content brief informally; if the map describes what the current product does rather than what the user is trying to achieve, redirect before the screen flow is derived — a one-sentence correction here saves a full design cycle.
- **You decide:** approve the customer journey and derived screen list at G-journey — the screen list flows directly from it.
- **Output:** an approved journey map with content brief and copy direction.

---

### 2. Derive the screen flow

- **Agent does:** runs `user-flow` to derive the screen inventory — what screens exist, what state each handles (empty, loading, populated, error), and what the transitions are; produces a per-screen brief for each.
- **You do:** check that the screen list doesn't add screens not implied by the journey and doesn't miss screens the journey requires; remove any screen not derived from the journey.
- **Output:** a screen inventory with per-screen briefs derived from the approved journey.

---

### 3. Establish design intent

- **Agent does:** runs `design-principles` to derive 3–5 named decision rules from the journey map; then runs `creative-direction` to establish the visual character and `design-system` to derive the token set.
- **You do:** review the design principles alongside the aesthetic direction.
- **You decide:** approve the aesthetic direction and token set at G-aesthetic; an aesthetic direction that says "clean and professional" is not specific enough — reject tokens that introduce hardcoded values outside the semantic token system.
- **Output:** approved design principles, aesthetic direction, and token set.

---

### 4. Design each screen

- **Agent does:** runs a structural IA skill on each screen — `information-architecture` for general screens, or a genre-specific skill for dashboards (`analytical-design`), marketing surfaces (`conversion-design`), docs (`documentation-design`), editorial pages (`informational-design`), marketplaces (`marketplace-design`), or workspace tools (`workspace-design`) — then `interaction-design` for states and transitions, and `design-review` as a pre-independent-review self-check.
- **You do:** watch each screen take shape; if a screen is missing a state — no empty state for a list, no loading state for an async action — name it; catching it here is cheaper than the independent review.
- **Output:** a self-reviewed screen set with states, transitions, and accessibility checks applied.

---

### 5. Review independently

- **Reviewer does:** runs the `experience-reviewer` in a forked context — no access to the authoring session — returning findings on the full screen set: handle-all-states violations, WCAG 2.2 AA failures, and aesthetic inconsistencies.
- **You do:** read the findings; apply Blockers before design intent feeds the build loop — they are the floor every screen must clear; handle-all-states violations are the most common finding.
- **You decide:** review the designs after the independent experience-reviewer pass.
- **Output:** a review-clean design set ready to feed the build loop.
