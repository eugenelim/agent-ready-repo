---
pack: experience
scope: user
tagline: "The design/UX seat for product teams."
prerequisitePacks: []
whatChanges: "After installing experience, product-engineering work has a full design thread from outcome to realization. `map-customer-journey` and `map-screen-flow` derive the screen list from a named outcome. `aesthetic-direction` and `design-system-foundations` establish the visual constraints before any screen is designed. `interaction-design` and `design-critique` craft and critique each screen to a shared quality floor. The forked-context `experience-reviewer` gives every design an independent pass — handle-all-states, WCAG 2.2 AA, reduced-motion."
skills:
  - name: map-customer-journey
    description: "Maps the current and desired customer journey to derive the key touchpoints and failure modes a product must address."
    humanTouches: 1
  - name: map-screen-flow
    description: "Derives the screen inventory and flow from the customer journey — what screens exist, what state each handles, what the transitions are."
    humanTouches: 1
  - name: blueprint-service
    description: "Maps front-stage screen flows to the back-stage processes and human actors that support them — the service blueprint."
    humanTouches: 0
  - name: map-internal-process
    description: "Documents the internal processes that run behind user-facing screens — the APQC/BPMN model of what people do."
    humanTouches: 0
  - name: aesthetic-direction
    description: "Establishes the visual direction for a surface — palette, typography, spacing — as a named aesthetic reference that all subsequent screens must satisfy."
    humanTouches: 1
  - name: design-system-foundations
    description: "Derives the design token set from the aesthetic direction — the primitive and semantic tokens that carry the design into code."
    humanTouches: 0
  - name: layout-and-information-architecture
    description: "Designs the layout zones and information hierarchy for a screen, given its per-screen brief."
    humanTouches: 0
  - name: interaction-design
    description: "Designs the interactive behaviors for a screen — states, transitions, feedback patterns — against WCAG 2.2 AA."
    humanTouches: 0
  - name: design-critique
    description: "Critiques an existing screen design against the quality floor — handle-all-states, accessibility, reduced-motion — before the independent review."
    humanTouches: 0
humanGates:
  - id: G-journey
    globalGate: null
    label: "Approve the customer journey and derived screen list"
    trigger: "After map-customer-journey and map-screen-flow complete"
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
    trigger: "After aesthetic-direction and optionally design-system-foundations complete"
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
docsUrl: /docs/guides/experience/
packUrl: /packs/experience/
relatedJourneys:
  - architect
  - core
---

## Stage 1 — Map the customer journey

You described the feature, user, and outcome. The agent ran `map-customer-journey` to produce the customer journey map — the current state (what happens today), the desired state (what should happen after this feature), and the key moments where the current journey breaks down.

**You did:** Read the journey map and approved it at the G-journey gate. This is the most important gate in the experience thread — the screen list flows directly from it. If the map describes what the current product does rather than what the user is trying to achieve, redirect before the screen flow is derived. A one-sentence correction here saves a full design cycle.

---

## Stage 2 — Derive the screen flow

With the journey approved, the agent ran `map-screen-flow` to derive the screen inventory: what screens exist, what state each one handles (empty, loading, populated, error), and what the transitions between them are. Each screen got a per-screen brief: the user's goal, the information they need, the states to handle.

**You did:** Checked that the screen list felt right — that it didn't add screens not implied by the journey, and didn't miss screens the journey required. If the agent added a screen that looked useful but wasn't derived from the journey, remove it here.

---

## Stage 3 — Establish design intent

Before designing any screen, the agent ran `aesthetic-direction` to establish the visual character of the surface — palette, typography, spacing — as a named aesthetic reference. It then ran `design-system-foundations` to derive the design token set.

**You did:** Approved the aesthetic direction at the G-aesthetic gate. An aesthetic direction that says "clean and professional" is not an aesthetic direction — it needs to name a specific visual character with enough specificity to say whether a given design decision is consistent or not. If the tokens introduced hardcoded values outside the semantic token system, reject them.

---

## Stage 4 — Design each screen

The agent ran `layout-and-information-architecture` and `interaction-design` on each screen in the flow, working from each screen's per-screen brief. It then ran `design-critique` on each screen before the independent review — a self-check against the quality floor.

**You did:** Watched each screen take shape. If a screen was missing a state — no empty state for a list that could be empty, no loading state for an async action — name it. The agent will miss states not explicitly mentioned in the brief; that's what the experience-reviewer catches, but catching it here is cheaper.

---

## Stage 5 — Independent review

The agent ran the `experience-reviewer` subagent in a forked context — a reviewer that had not seen the authoring session. The reviewer returned findings on the full screen set: handle-all-states violations, accessibility failures, aesthetic inconsistencies.

**You did:** Read the review findings at the G-experience-review gate. Handle-all-states violations are the most common finding — a screen that works for the happy path but has no designed error state. WCAG findings affect all users. Apply Blockers before the design intent feeds the build loop; they represent the floor the spec says all screens must clear.
