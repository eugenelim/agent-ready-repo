---
pack: product-strategy
scope: user
tagline: "Market context, adoption hypothesis, and causal metric tree — committed upstream of every initiative."
prerequisitePacks:
  - product-engineering
contract:
  useItWhen: "You're building the committed strategy layer — market analysis, adoption path, and OKR-derived gap routing — upstream of any product initiative."
  youProvide: "Company OKRs, any prior desk-research outputs, and the scope of the initiative or strategic question to address."
  youReceive: "Committed SWOT, PRFAQ with adoption hypothesis, OKR cascade with Metric Tree, workspace.toml gap entries, ux-strategy.md, and content-strategy.md. Together these fill the 7 Strategy fields of the Digital Experience Contract."
  yourDecisions:
    - "Approve the market situation picture and differentiation mechanism"
    - "Approve the PRFAQ, first-success event, and adoption hypothesis"
    - "Approve the OKR cascade, causal metric tree, and gap routing"
whatChanges: "After installing product-strategy (v0.2.0), the strategy layer above every initiative produces a 14-point output structure: situation analysis (macro environment, competitive landscape, portfolio position, stakeholder perspectives) → diagnosis (SWOT with differentiation mechanism) → strategic choices → adoption hypothesis → first-success event → repeat-value behavior → value loop → causal metric tree (north-star + leading indicators) → strategy-to-experience handoff. The strategy-to-experience handoff maps directly to the 7 Strategy h3 headers of the Digital Experience Contract: Target User and Context, Diagnosis and Strategic Choices, Adoption Hypothesis, Value Loop, Metric Tree, Differentiation, Assumptions and Kill Criteria. Every artifact commits to `docs/product/shaping/` where downstream packs — product-engineering and experience-design (including its content-design skill) — can reference it by path."
skills:
  - name: synthesize-stakeholder-research
    description: "Turns existing stakeholder research into a strategic narrative organized by theme — and flags when adoption signal is absent from the research. Committed as stakeholder-synthesis.md. Surfaces a 'run desk-research project first' prompt if no research inputs are found."
    humanTouches: 0
  - name: run-pestle-analysis
    description: "Scans the macro environment through six lenses (Political, Economic, Social, Technological, Legal, Environmental) and names the top forces by strategic materiality. Does not claim moat — names the forces that feed SWOT. Committed as macro-environment.md."
    humanTouches: 0
  - name: run-porters-five-forces
    description: "Maps the competitive landscape and derives the structural mechanism that protects this player's position. Committed as competitive-landscape.md."
    humanTouches: 0
  - name: run-bcg-matrix
    description: "Positions each product in the portfolio matrix and names the reallocation decisions and investment implications per quadrant. Committed as portfolio-position.md."
    humanTouches: 0
  - name: run-swot
    description: "Synthesizes the situation picture into a SWOT and names the adoption hypothesis (which SO pair produces a first-success event) and the differentiation mechanism (the structural advantage that makes the position defensible). Committed as swot-analysis.md."
    humanTouches: 1
  - name: write-prfaq
    description: "Authors the altitude-0 forcing function: press release + adoption hypothesis (first-success event + repeat-value behavior) + internal FAQ with a success metric traceable to the first-success event. Committed as prfaq.md."
    humanTouches: 1
  - name: run-okr-cascade
    description: "Cascades company OKRs to team level, identifies gaps, derives the Metric Tree (north-star + leading indicators), and routes each gap as a strategy-type entry into workspace.toml. Committed as okr-cascade.md."
    humanTouches: 1
  - name: define-ux-strategy
    description: "Produces ux-strategy.md — vision, goals+measures with value loop and adoption hypothesis, and plan. The adoption hypothesis names the UX-level first-success event. Upstream of journey-mapping."
    humanTouches: 0
  - name: define-content-strategy
    description: "Produces content-strategy.md using the Halvorson quad (Purpose + Process + Structure + Governance) — the organizational governance layer above per-surface content-design."
    humanTouches: 0
humanGates:
  - id: G-situation
    globalGate: null
    label: "Approve the market situation picture and differentiation mechanism"
    trigger: "After run-swot synthesizes the macro environment, competitive landscape, and portfolio inputs"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the SWOT read as a synthesis of the PESTLE, Porter's, and BCG analyses — or does it introduce claims not grounded in those artifacts?"
      - "Are Strengths and Weaknesses grounded in the organization, not in the market?"
      - "Is the adoption hypothesis named? Which SO pair produces a first-success event, and what is that event specifically?"
      - "Is the differentiation mechanism named? What structural advantage makes this position defensible — network effect, switching cost, data advantage, proprietary capability?"
      - "Is the most acute Threat named — the thing that could invalidate the strategy if it materializes?"
    whatGoodLooksLike: "A SWOT that reads as a compressed situation summary — each quadrant traceable to a specific finding from PESTLE, Porter's, or the portfolio analysis, with an adoption hypothesis and a named differentiation mechanism."
    whatBadLooksLike: "A SWOT with generic strengths like 'talented team', no adoption hypothesis, and a moat claim without a mechanism. This means the situation analysis didn't surface specific signal."
    consequence: "The SWOT is the situation anchor for the PRFAQ and OKR cascade that follow. A SWOT without an adoption hypothesis means first-success goes unspecified; a SWOT without a differentiation mechanism means the moat is assumed, not named."
  - id: G-prfaq
    globalGate: null
    label: "Approve the PRFAQ, first-success event, and adoption hypothesis"
    trigger: "After write-prfaq produces the press release, adoption hypothesis, and FAQ draft"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the press release name a specific person with a specific pain?"
      - "Is the first-success event named — a specific observable behavior, not 'user signs up' or 'user completes onboarding'?"
      - "Does the internal FAQ success metric trace back to the first-success event — or is it a vanity metric?"
      - "Does the FAQ address the hardest objection a skeptical stakeholder would raise?"
      - "Is the PRFAQ grounded in the situation from Stage 1, or does it describe a product in a different market?"
    whatGoodLooksLike: "A press release that names a specific person and first-success event, with an internal FAQ success metric that traces to that first-success event. Readable without the prior market context and still fully specific."
    whatBadLooksLike: "A press release in corporate voice with no specific person, no named first-success event, and a success metric of 'grow user base'. Or an internal FAQ where the success metric is 'ship the product'."
    consequence: "The PRFAQ is the altitude-0 forcing function. An unspecific first-success event means every engineer and designer forms their own theory of what adoption looks like. The adoption hypothesis must be named here so it can be operationalized in PE framing."
  - id: G-cascade
    globalGate: null
    label: "Approve the OKR cascade, Metric Tree, and gap routing"
    trigger: "After run-okr-cascade identifies gaps and derives the causal metric tree"
    duration: "10–15 minutes"
    whatToCheck:
      - "Is the north-star metric a user-behavioral outcome metric — not an output like 'features shipped' or a vanity metric like 'page views'?"
      - "Does each leading indicator trace causally to the north-star — and is that causal connection named explicitly?"
      - "Does each gap entry reflect an actual gap between current state and an OKR target?"
      - "Are the gaps ranked by OKR weight — does the most strategically important gap come first?"
      - "Is each gap specific enough for frame-situation to scope into a shaping brief?"
    whatGoodLooksLike: "A causal metric tree where north-star and leading indicators are explicit, each leading indicator traces to a gap, and gaps are ranked. A set of 3–7 gap entries that a product engineer could pick up from workspace-status directly."
    whatBadLooksLike: "A metric list of 10 metrics with no causal chain named. Gaps without priority ranking. Or a 'north-star' that is actually an output metric (revenue, features shipped) rather than a user-behavioral outcome."
    consequence: "The causal metric tree is the measurement contract for the initiative. A metric list without causal chain produces measurement theater — dashboards that don't predict outcomes. Approving it means the team will instrument what's easy to count, not what causally predicts success."
typicalSession:
  agentTurns: "8–20"
  humanTouches: 3
  wallClockMinutes: "60–120"
docsUrl: /docs/guides/product-strategy/
packUrl: /packs/product-strategy/
relatedJourneys:
  - experience-design
  - desk-research
  - core
---

### 1. Build and gate the market situation

- **You provide:** the market and organizational context — company OKRs, any prior desk-research project outputs, and the scope of the initiative or strategic question to address.
- **Agent does:** runs synthesize-stakeholder-research if prior desk-research outputs exist (and flags if adoption signal is absent from the research); then runs run-pestle-analysis, run-porters-five-forces, and run-bcg-matrix; synthesizes all inputs into a committed SWOT as the capstone situation picture — including the adoption hypothesis (which SO pair produces a first-success event) and the differentiation mechanism (the structural advantage that makes the position defensible); commits each artifact to docs/product/shaping/.
- **You do:** before moving forward, confirm the SWOT names an adoption hypothesis and a differentiation mechanism — not just four quadrants. Redirect if the strategic implications section makes no choices.
- **You decide:** approve the market situation picture and differentiation mechanism.
- **Output:** committed PESTLE, Porter's Five Forces, BCG matrix, and SWOT — the grounded situation picture all downstream artifacts build on, including the adoption hypothesis that feeds the PRFAQ.

---

### 2. Commit the altitude-0 direction and adoption hypothesis

- **Agent does:** runs write-prfaq to draft the press release + adoption hypothesis — naming the specific person, the first-success event (the one action that proves first value), the repeat-value behavior, and the internal FAQ with a success metric traceable to the first-success event; commits to docs/product/shaping/prfaq.md.
- **You do:** read the PRFAQ; if the first-success event is not a specific observable behavior (not "user signs up" or "user completes onboarding"), redirect before the cascade sets metrics against an unspecific adoption target.
- **You decide:** approve the PRFAQ, first-success event, and adoption hypothesis.
- **Output:** committed prfaq.md — the altitude-0 forcing function with a named first-success event that the OKR cascade and PE pack's first-success operationalization will trace back to.

---

### 3. Cascade strategy gaps and causal metric tree to the shaping queue

- **Agent does:** runs run-okr-cascade to derive team-level OKRs from company targets; derives the causal metric tree (north-star metric + 2–4 leading indicators, each connected to a specific OKR gap); ranks gaps by OKR weight; prepares strategy-type entries for workspace.toml.
- **You do:** review the causal metric tree — confirm the north-star is a user-behavioral outcome (not an output metric), that each leading indicator traces causally to the north-star, and that gaps are ranked. A metric list without a causal chain is not a metric tree.
- **You decide:** approve the OKR cascade, causal metric tree, and gap routing.
- **Output:** strategy-type gap entries written to workspace.toml; okr-cascade.md with causal metric tree — the measurement contract that PE framing will operationalize into its first-success operationalization field.

---

### 4. Set experience direction and strategy-to-experience handoff

- **Agent does:** runs define-ux-strategy to produce ux-strategy.md — experience vision, goals+measures with value loop and adoption hypothesis (UX-level first-success event), and plan; runs define-content-strategy to produce content-strategy.md using the Halvorson quad. Together these complete the strategy-to-experience handoff: the seven Strategy h3 headers of the Digital Experience Contract (Target User and Context, Diagnosis and Strategic Choices, Adoption Hypothesis, Value Loop, Metric Tree, Differentiation, Assumptions and Kill Criteria) are now populated.
- **You do:** review both artifacts before sharing with design and content teams. Confirm ux-strategy.md names a value loop (not just a vision) and an adoption hypothesis (not just goals). Confirm the strategy-to-experience handoff is ready for the Digital Experience Contract.
- **Output:** committed ux-strategy.md and content-strategy.md; the Strategy section of the Digital Experience Contract is populated for downstream packs (product-engineering, experience-design, core) to read from.
