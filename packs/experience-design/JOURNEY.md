---
journey_id: experience-design
pack: experience-design
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Walkable design method. Outcome to independently-reviewed screens."
prerequisitePacks: []
contract:
  useItWhen: "A product team needs a full design thread — from outcome to independently-reviewed screens — before build begins."
  youProvide: "The feature, user, and intended outcome, plus any existing brand or design-system constraints."
  youReceive: "A complete, independently-reviewed design set — journey map, screen inventory, interaction specs, and accessibility-clean designs."
  yourDecisions:
    - "Approve the customer journey and derived screen list"
    - "Approve the aesthetic direction and token set"
    - "Review the designs after the independent experience-reviewer pass"
whatChanges: "After installing experience-design, every design task runs a fixed thread: journey-mapping to anchor user outcomes, user-flow to derive the screen inventory, a craft sequence (creative-direction → design-system → information-architecture → interaction-design) to design each screen, and an independent experience-reviewer pass that reads design artifacts cold. The quality floor — handle-all-states, WCAG 2.2 AA, reduced-motion — is non-negotiable at every step. You decide at three gates: the journey and screen list, the aesthetic direction, and the post-review pass before design feeds the build loop. experience-status orients to the thread at the start of any session."
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
docsUrl: /guides/experience-design/
packUrl: /packs/experience-design/
relatedJourneys:
  - architect
  - core
---

| Say this | What happens |
|----------|--------------|
| `experience-status` | Orient — where the design thread is, what's next |
| `journey-mapping` | Map the user's outcome: stages, emotions, pains |
| `content-design` | Set surface intent — what this screen says and for whom |
| `tone-of-voice` | Set the brand register — copy goals and arbitration rules |
| `user-flow` | Build the screen inventory with per-screen state briefs |
| `creative-direction` | Anchor the aesthetic in persona and precedent |
| `design-system` | Derive the token taxonomy from the aesthetic direction |
| `interaction-design` | Design states, feedback, and animation per screen |
| `experience-reviewer` | Independent cold review — forked context, read-only |

---

### 1. Map the customer journey

Type `journey-mapping` and describe the outcome you're designing for — the user, the goal, and where the current experience breaks down.

```text
journey-mapping

  journey  docs/design/journeys/onboarding.md

  Stage 1  Aware          finds product, expectations vague
  Stage 2  First-session  blank state, no direction, high drop-off
  Stage 3  Value          first export, relief, converts

Approve the journey and screen list? ›
```

- **You decide:** approve the journey map before screens are derived from it — a one-sentence redirect here saves a full design cycle.
- **Output:** an approved journey map with key failure modes and a derived screen list.
- **State:** draft

---

### 2. Derive the screen flow

Type `user-flow`. The agent sequences the screens implied by the journey and builds a per-screen brief for each, including the full state matrix.

```text
user-flow

  screens  docs/design/screen-flows/onboarding.md

  /onboarding/welcome  →  /onboarding/connect  →  /onboarding/done
  States per screen: default · loading · error · success · empty
```

- **Output:** a screen inventory with per-screen briefs, ready for the craft sequence.
- **State:** draft

---

### 3. Establish design intent

Type `creative-direction` to anchor the visual direction in persona, precedent, and platform conventions. Type `design-system` to derive the token taxonomy from it.

```text
creative-direction

  direction  docs/design/aesthetic/onboarding.md

  Goals   Calm confidence, platform-native trust
  Ref     Linear's focused workspace; Notion's quiet hierarchy

Approve the aesthetic direction? ›
```

- **You decide:** approve the direction before screens are designed — a vague direction ("clean and modern") is a rejection.
- **Output:** a named aesthetic direction with a derived token taxonomy.
- **State:** draft

---

### 4. Design each screen

Type `information-architecture` (or a genre-direct skill for dashboards, marketing, docs, or marketplace surfaces), then `interaction-design` per screen.

```text
interaction-design [/onboarding/welcome]

  screen  docs/design/screens/welcome.md
  States: default · loading · error · success · empty ✓
  Motion: entrance · field-focus · submit-feedback ✓
```

- **Output:** a designed screen set with all states handled and quality floor met.
- **State:** draft

---

### 5. Review independently

Type `experience-reviewer`. It reads your design artifacts cold — no authoring context — and returns findings across handle-all-states, WCAG 2.2 AA, aesthetic fit, and cross-screen coherence.

```text
experience-reviewer

  Blocker  Welcome screen: empty state not designed
  Concern  Connect screen: error text has no recovery action
  Nit      "Get started" → "Connect your first account"
```

- **You decide:** act on Blockers before design feeds the build loop.
- **Output:** a review-clean design set ready for build.
- **State:** confirmed-write
