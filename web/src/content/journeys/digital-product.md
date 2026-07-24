---
pack: digital-product
scope: user
tagline: "Strategy → shaping → experience → build hand-off — one toolkit, end to end."
prerequisitePacks: []
contract:
  useItWhen: "You're a product manager, product designer, or product lead on a cross-functional team who owns a digital product from strategy through to build — and you want a single user-scope toolkit that covers the full arc."
  youProvide: "Company OKRs, market context, and the scope of the product or initiative you're working on."
  youReceive: "A connected chain from market situation through committed strategy artifacts, shaping briefs, and independently-reviewed experience designs — all feeding the Digital Experience Contract that the build repo's core pack reads from."
  yourDecisions:
    - "Approve the market situation picture and differentiation mechanism (product-strategy)"
    - "Approve the adoption hypothesis, PRFAQ, and OKR cascade (product-strategy)"
    - "Approve the customer journey, screen list, and aesthetic direction (experience-design)"
    - "Review designs after the independent experience-reviewer pass (experience-design)"
whatChanges: "After installing the digital-product profile, a single `agentbundle install --profile digital-product <catalogue>` gives you four packs at user scope: desk-research (eleven research skills + retrieval subagents for grounded evidence), product-strategy (fourteen-point output structure from market situation through strategy-to-experience handoff, filling the seven Strategy fields of the Digital Experience Contract), product-engineering (shaping queue, first-success operationalization, thin-slice learning contract), and experience-design (full XD chain: journey mapping → screen flow → aesthetic direction → per-screen design → three-pass self-review → independent experience-reviewer). The full chain produces a Digital Experience Contract — the shared schema connecting strategy intent to rendered evidence — that your build repo's core pack reads from. The profile is user-scope; each repo gets its own core (build loop) installed separately."
skills:
  - name: desk-research
    description: "Scopes and executes evidence-grounded research projects. Eleven skills covering research scoping, source curation, synthesis, adversarial review, and a four-skill project-mode lifecycle for sustained investigations. Upstream of strategy and experience work."
    humanTouches: 1
  - name: run-swot
    description: "Synthesizes the market situation into a SWOT and names the adoption hypothesis and differentiation mechanism. The capstone of the product-strategy situation analysis stage."
    humanTouches: 1
  - name: write-prfaq
    description: "Authors the altitude-0 forcing function: press release + adoption hypothesis (first-success event, repeat-value behavior) + internal FAQ. The PRFAQ's first-success event is the measurement contract that all downstream work — PE shaping, XD journey, instrumentation — traces back to."
    humanTouches: 1
  - name: journey-mapping
    description: "Maps the current and desired customer journey to derive the key touchpoints and failure modes a product must address. The connective thread that drives the screen list."
    humanTouches: 1
  - name: user-flow
    description: "Derives the screen inventory and flow from the customer journey — what screens exist, what state each handles, and what the transitions are. Each screen becomes a per-screen brief for downstream design."
    humanTouches: 1
  - name: design-review
    description: "Runs a three-pass authoring-time self-check on each screen (cold-read → primary task + unhappy path → full 18-state quality-floor contract review) before the independent experience-reviewer pass."
    humanTouches: 0
humanGates:
  - id: G-situation
    globalGate: null
    label: "Approve the market situation picture and differentiation mechanism"
    trigger: "After run-swot synthesizes the market environment, competitive landscape, and portfolio inputs"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the SWOT name an adoption hypothesis — which SO pair produces a first-success event, and what is that event specifically?"
      - "Is the differentiation mechanism named — a structural advantage, not a generic moat claim?"
      - "Is the most acute threat named — the thing that could invalidate the strategy?"
    whatGoodLooksLike: "A SWOT where every quadrant is traceable to a specific finding from the situation analysis, with an adoption hypothesis and a named differentiation mechanism."
    whatBadLooksLike: "Generic strengths like 'talented team', no adoption hypothesis, and a moat claim with no mechanism."
    consequence: "The SWOT anchors all downstream artifacts. A SWOT without an adoption hypothesis means first-success goes unspecified; a SWOT without a differentiation mechanism means the moat is assumed, not named."
  - id: G-prfaq
    globalGate: null
    label: "Approve the PRFAQ and adoption hypothesis"
    trigger: "After write-prfaq produces the press release, adoption hypothesis, and FAQ draft"
    duration: "10–20 minutes"
    whatToCheck:
      - "Is the first-success event a specific observable behavior — not 'user signs up' or 'user completes onboarding'?"
      - "Does the internal FAQ success metric trace back to the first-success event?"
      - "Does the FAQ address the hardest objection a skeptical stakeholder would raise?"
    whatGoodLooksLike: "A press release that names a specific person and first-success event, with a success metric traceable to that event."
    whatBadLooksLike: "A press release in corporate voice with no specific person, no named first-success event, and a success metric of 'grow user base'."
    consequence: "The first-success event named here is the measurement contract that PE shaping, XD journey mapping, and instrumentation all trace back to. An unspecific first-success event means every discipline forms its own theory of adoption."
  - id: G-journey
    globalGate: null
    label: "Approve the customer journey and derived screen list"
    trigger: "After journey-mapping and user-flow complete"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the journey capture the outcome the user is trying to achieve — not just the tasks they perform in the current product?"
      - "Is every screen in the list implied by the journey?"
      - "Are the key failure modes named — the moments the current journey breaks down?"
    whatGoodLooksLike: "A journey map that names the outcome and failure modes, with a screen list where each screen is traceable to a journey moment."
    whatBadLooksLike: "A screen list that maps to the current implementation screen-by-screen — the agent documented the status quo instead of designing for the outcome."
    consequence: "The screen list is the contract for all design work that follows. A screen list derived from the wrong model designs the wrong product — faithfully."
  - id: G-experience-review
    globalGate: null
    label: "Review the designs after the independent experience-reviewer pass"
    trigger: "After the experience-reviewer subagent returns findings on the completed screen designs"
    duration: "15–25 minutes"
    whatToCheck:
      - "Did the reviewer flag any handle-all-states violations? (Missing empty, loading, error, or success states are the most common finding.)"
      - "Are all WCAG 2.2 AA requirements met?"
      - "Are the screens consistent with the approved aesthetic direction?"
    whatGoodLooksLike: "A design set the independent reviewer marks clean — all states handled, accessibility floor met, aesthetic direction consistently applied."
    whatBadLooksLike: "Screens that look good in the happy-path state but have no designed empty state, loading state, or error recovery."
    consequence: "The experience-reviewer is the design analogue of adversarial-reviewer in the build loop. An unreviewed design is a set of unverified assumptions about how the product behaves when things go wrong."
typicalSession:
  agentTurns: "20–40"
  humanTouches: 4
  wallClockMinutes: "180–360"
docsUrl: /docs/guides/experience-design/tutorials/xd-digital-product-profile/
relatedJourneys:
  - desk-research
  - product-strategy
  - experience-design
  - core
---

### 1. Research the market context

- **You provide:** the market or domain you're working in, the competitive landscape you know, and any existing research or organizational context.
- **Agent does:** runs `desk-research` skills to scope the research question, curate sources, and synthesize evidence into committed artifacts — competitive signal, user behavior patterns, and any prior stakeholder research inputs.
- **You do:** review the research synthesis before moving to strategy; if the synthesis doesn't surface adoption signal (evidence of how users behave, not just who they are), redirect — a strategy built on market description alone doesn't produce an adoption hypothesis.
- **Output:** grounded research synthesis ready to feed the situation analysis.

---

### 2. Build and gate the market situation

- **Agent does:** runs `synthesize-stakeholder-research` if prior research outputs exist; then runs `run-pestle-analysis`, `run-porters-five-forces`, and `run-bcg-matrix`; synthesizes all inputs into a committed SWOT — including the adoption hypothesis (which SO pair produces a first-success event) and the differentiation mechanism; commits each artifact to `docs/product/shaping/`.
- **You do:** before moving forward, confirm the SWOT names an adoption hypothesis and a differentiation mechanism — not just four quadrants.
- **You decide:** approve the market situation picture and differentiation mechanism.
- **Output:** committed situation picture — the grounded anchor all downstream artifacts build on.

---

### 3. Commit the altitude-0 direction and adoption hypothesis

- **Agent does:** runs `write-prfaq` to draft the press release + adoption hypothesis — naming the specific person, the first-success event (the one action that proves first value), the repeat-value behavior, and the internal FAQ with a success metric traceable to the first-success event; then runs `run-okr-cascade` to cascade company OKRs, derive the causal metric tree, and route gaps into `workspace.toml`; then runs `define-ux-strategy` and `define-content-strategy` to complete the strategy-to-experience handoff. Together these fill the seven Strategy fields of the Digital Experience Contract.
- **You do:** read the PRFAQ; if the first-success event is not a specific observable behavior, redirect before the cascade sets metrics against an unspecific adoption target.
- **You decide:** approve the PRFAQ and adoption hypothesis; approve the OKR cascade, causal metric tree, and gap routing.
- **Output:** committed `prfaq.md`, `okr-cascade.md`, `ux-strategy.md`, `content-strategy.md`; the Strategy section of the Digital Experience Contract is populated.

---

### 4. Shape the initiative and first-success operationalization

- **Agent does:** using the product-engineering pack, runs the shaping skills to produce a shaping brief (problem, first-success event operationalization, thin-slice scope) and routes it as a `strategy`-type entry in `workspace.toml`; applies the first-success operationalization to name the specific user action, the observable system response, and the measurement event.
- **You do:** confirm the shaping brief names the same first-success event as the PRFAQ — if they diverge, the measurement contract is broken before build begins.
- **Output:** committed shaping brief with first-success operationalization; workspace entry ready for the build loop.

---

### 5. Map the customer journey and design the experience

- **Agent does:** runs `journey-mapping` and `user-flow` to derive the screen list from the customer journey; establishes design intent via `design-principles`, `creative-direction`, `design-token-taxonomy`, and `design-system-foundations`; designs each screen through `information-architecture`, the appropriate genre-specific skill, `interaction-design`, and the three-pass `design-review` self-check; then runs the forked-context `experience-reviewer` for an independent pass.
- **You do:** approve the customer journey and screen list before screens are designed — a screen list derived from the wrong model designs the wrong product; approve the aesthetic direction and token set; review the independent reviewer's findings before design intent feeds the build.
- **You decide:** approve the journey and screen list; approve the aesthetic direction; review designs after the independent pass.
- **Output:** a review-clean design set — journey map, screen inventory, per-screen briefs, design principles, token foundation, and independently-reviewed screens — ready to feed the build loop.

---

### 6. Hand off to the build loop

- **Agent does:** the Digital Experience Contract — now populated with strategy, shaping, and experience fields — is the hand-off artifact the build repo's `core` pack reads from. The core pack's `work-loop` and `frontend-engineering` skill read the contract fields to ground build decisions in the strategy and design intent.
- **You do:** install `core` in the target repo (`agentbundle install --pack core <catalogue>`), point it to the contract, and confirm the first-success event named in the contract matches what the build loop will instrument.
- **Output:** build loop launched with grounded strategy and design intent; instrumentation anchored to the first-success event named upstream.
