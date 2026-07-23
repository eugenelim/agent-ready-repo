---
pack: product-strategy
scope: user
tagline: "Market, UX, and content strategy — committed artifacts upstream of every initiative."
prerequisitePacks:
  - product-engineering
contract:
  useItWhen: "You're building the committed strategy layer — market analysis, altitude-0 direction, and OKR-derived gap routing — upstream of any product initiative."
  youProvide: "Company OKRs, any prior desk-research outputs, and the scope of the initiative or strategic question to address."
  youReceive: "Committed SWOT, PRFAQ, OKR-derived gap entries in workspace.toml, ux-strategy.md, and content-strategy.md."
  yourDecisions:
    - "Approve the market situation picture"
    - "Approve the PRFAQ"
    - "Approve the OKR cascade and gap routing"
whatChanges: "After installing product-strategy, the altitude-0 work above every initiative has a committed artifact set instead of planning-meeting notes. Nine skills span the full strategy layer: market context (PESTLE, Porter's Five Forces), portfolio position (BCG Matrix, SWOT), altitude-0 forcing function (PRFAQ), OKR cascade with direct routing to the PE pack's shaping queue, and the experience and content direction that the experience-design pack reads from. Every artifact commits to `docs/product/shaping/` where downstream packs — product-engineering and experience-design (including its content-design skill) — can reference it by path."
skills:
  - name: synthesize-stakeholder-research
    description: "Converts desk-research project outputs into a strategic narrative by theme — committed as stakeholder-synthesis.md. Surfaces a 'run desk-research project first' prompt if no research inputs are found."
    humanTouches: 0
  - name: run-pestle-analysis
    description: "Scans the macro environment through six lenses (Political, Economic, Social, Technological, Legal, Environmental) and commits the analysis to docs/product/shaping/ as macro-environment.md."
    humanTouches: 0
  - name: run-porters-five-forces
    description: "Maps the competitive landscape using Porter's Five Forces (Supplier Power, Buyer Power, New Entrants, Substitutes, Rivalry) and commits the analysis as competitive-landscape.md."
    humanTouches: 0
  - name: run-bcg-matrix
    description: "Positions each initiative in the BCG portfolio matrix (Stars, Cash Cows, Question Marks, Dogs) to surface portfolio priority and resource urgency, committed as portfolio-position.md."
    humanTouches: 0
  - name: run-swot
    description: "Synthesizes the macro environment, competitive landscape, and portfolio position into a single SWOT analysis — the capstone situation picture committed as swot-analysis.md."
    humanTouches: 1
  - name: write-prfaq
    description: "Authors a press release + FAQ as the altitude-0 forcing function — the imagined future press release that anchors initiative briefs and lets the team trace every shaping decision back to the original vision."
    humanTouches: 1
  - name: run-okr-cascade
    description: "Cascades company OKRs to team level, identifies gaps between current state and OKR targets, and routes each gap as a strategy-type entry into workspace.toml for the PE pack's frame-situation to pick up."
    humanTouches: 1
  - name: define-ux-strategy
    description: "Produces a committed ux-strategy.md (vision → goals+measures → plan) using the NN/g three-layer model and Gothelf/Seiden OKR-linked UX framing — the experience anchor that journey-mapping and user-flow read from."
    humanTouches: 0
  - name: define-content-strategy
    description: "Produces a committed content-strategy.md using the Halvorson quad (Purpose + Process + Structure + Governance) — the organizational governance layer that the experience-design pack's content-design skill consumes."
    humanTouches: 0
humanGates:
  - id: G-situation
    globalGate: null
    label: "Approve the market situation picture"
    trigger: "After run-swot synthesizes the macro environment, competitive landscape, and portfolio inputs"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the SWOT read as a synthesis of the PESTLE, Porter's, and BCG analyses — or does it introduce claims not grounded in those artifacts?"
      - "Are Strengths and Weaknesses grounded in the organization, not in the market? (Market position belongs in Opportunities/Threats.)"
      - "Is the most acute Threat named — the thing that could invalidate the strategy if it materializes?"
      - "Does the Opportunities list reflect addressable gaps, not aspirational wishes?"
    whatGoodLooksLike: "A SWOT that reads as a compressed situation summary — each quadrant traceable to a specific finding from PESTLE, Porter's, or the portfolio analysis, with the most critical items named explicitly."
    whatBadLooksLike: "A SWOT that could apply to any company in any market — generic strengths like 'talented team' and generic threats like 'competition'. This means the market analysis didn't surface specific signal."
    consequence: "The SWOT is the situation anchor for the PRFAQ and OKR cascade that follow. A vague SWOT means the altitude-0 artifacts build on an ungrounded situation picture — and the OKR cascade will identify the wrong gaps."
  - id: G-prfaq
    globalGate: null
    label: "Approve the PRFAQ"
    trigger: "After write-prfaq produces the press release and FAQ draft"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the press release name the specific person it's written for — not 'customers' but a named persona with a specific pain?"
      - "Is the benefit concrete enough to measure — can you determine after shipping whether you delivered it?"
      - "Does the FAQ address the hardest objection a skeptical stakeholder would raise, not the easiest?"
      - "Is the press release grounded in the market situation from Stage 1, or does it describe a product that belongs in a different market?"
    whatGoodLooksLike: "A press release that names a specific person, delivers a measurable benefit, and a FAQ that addresses real objections — readable without the prior market context and still fully specific."
    whatBadLooksLike: "A press release in corporate voice that names no specific person and delivers no measurable benefit. Or a FAQ that only addresses questions the team already knows the answers to."
    consequence: "The PRFAQ is the altitude-0 forcing function — the artifact that initiative briefs trace back to. An unspecific PRFAQ means teams shape initiatives without a shared vision of success. Every product engineer and designer will form their own theory of what 'done' means."
  - id: G-cascade
    globalGate: null
    label: "Approve the OKR cascade and gap routing"
    trigger: "After run-okr-cascade identifies gaps and before writing strategy-type entries to workspace.toml"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does each gap entry reflect an actual gap between current state and an OKR target — not a feature the team wants to build regardless?"
      - "Are the gaps ranked — does the highest-weight OKR produce the highest-priority gap entries?"
      - "Is each gap specific enough for frame-situation to scope into a shaping brief, or is it too vague to act on?"
      - "Are there OKR targets vague enough that the cascade missed important gaps — should any OKRs be tightened before the cascade completes?"
    whatGoodLooksLike: "A set of 3–7 gap entries that a product engineer could pick up from workspace-status and route directly into frame-situation — specific, ranked by OKR weight, and traceable to a named target."
    whatBadLooksLike: "More than 10 gap entries without priority ranking. Or gaps so broad that frame-situation would need to re-scope them from scratch before shaping could begin — a sign the OKR targets aren't specific enough."
    consequence: "The cascade write is a shared state change — gap entries appear in workspace-status and signal to product engineers what strategy-driven work to shape next. Approving vague or unranked gaps means the shaping queue fills with work of unclear strategic priority."
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

## 1. Build and gate the market situation

- **You provide:** the market and organizational context — company OKRs, any prior desk-research project outputs, and the scope of the initiative or strategic question to address.
- **Agent does:** runs synthesize-stakeholder-research if prior desk-research outputs exist; then runs run-pestle-analysis, run-porters-five-forces, and run-bcg-matrix; synthesizes all inputs into a committed SWOT as the capstone situation picture; commits each artifact to docs/product/shaping/.
- **You do:** before moving forward, confirm the SWOT reads as a synthesis of the prior analyses — redirect if it introduces claims you can't trace back to PESTLE, Porter's, or BCG.
- **You decide:** approve the market situation picture.
- **Output:** committed PESTLE, Porter's Five Forces, BCG matrix, and SWOT — the grounded situation picture all downstream artifacts build on.

---

## 2. Commit the altitude-0 direction

- **Agent does:** runs write-prfaq to draft the press release + FAQ — naming the specific person, the measurable benefit, and the hardest objection a skeptical stakeholder would raise; commits to docs/product/shaping/prfaq.md.
- **You do:** read the PRFAQ; if the press release doesn't name a specific person or deliver a measurable benefit, or doesn't connect to the approved situation picture, redirect before the cascade and experience direction are set against an unspecific vision.
- **You decide:** approve the PRFAQ.
- **Output:** committed prfaq.md — the altitude-0 forcing function that initiative briefs trace back to as their strategic rationale.

---

## 3. Cascade strategy gaps to the shaping queue

- **Agent does:** runs run-okr-cascade to derive team-level OKRs from company targets, identify gaps between current state and each target, and prepare strategy-type entries for workspace.toml; each gap becomes a {type = "strategy"} entry ranked by OKR weight.
- **You do:** review the gap list; confirm each gap reflects an actual gap (not a feature the team wants regardless of OKRs), is ranked by OKR weight, and is specific enough for frame-situation to scope into a shaping brief without re-scoping from scratch.
- **You decide:** approve the OKR cascade and gap routing.
- **Output:** strategy-type gap entries written to workspace.toml — signaling strategy-driven shaping items to product engineers via workspace-status.

---

## 4. Set experience and content direction

- **Agent does:** runs define-ux-strategy to produce a committed ux-strategy.md — experience vision, goals with measures, and plan, grounded in the approved market situation and PRFAQ; runs define-content-strategy to produce a committed content-strategy.md using the Halvorson quad (Purpose + Process + Structure + Governance).
- **You do:** review both artifacts before sharing with design and content teams; confirm ux-strategy.md connects to the approved PRFAQ; confirm content-strategy.md names specific decisions — channel priority, ownership model, update cadence — not aspirational intent.
- **Output:** committed ux-strategy.md and content-strategy.md — the anchors the experience-design pack reads from when journey-mapping and content-design run.
