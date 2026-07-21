---
pack: product-strategy
scope: user
tagline: "Market, UX, and content strategy — committed artifacts upstream of every initiative."
prerequisitePacks:
  - product-engineering
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

## Stage 1 — Build the market situation

You give the agent the market and organizational context. If prior desk-research project outputs exist, the agent runs `synthesize-stakeholder-research` first to produce a committed stakeholder narrative. It then runs `run-pestle-analysis` and `run-porters-five-forces` to cover the macro environment and competitive landscape, `run-bcg-matrix` to map portfolio position, and `run-swot` as the capstone — synthesizing all four inputs into the committed situation picture.

**You:** Approve the situation picture at the G-situation gate before moving forward — the PRFAQ and OKR cascade both build on this foundation. The cheapest correction is here: if the SWOT introduces claims you can't trace to the prior analyses, redirect before the altitude-0 artifacts are committed.

---

## Stage 2 — Commit the altitude-0 direction

With the situation picture approved, the agent runs `write-prfaq` to draft the press release + FAQ. The PRFAQ is the altitude-0 forcing function: the imagined future press release that answers "who is this for, what changes for them, and why does it matter?" before any initiative is scoped. It commits to `docs/product/shaping/prfaq.md` where initiative briefs can link to it as their strategic rationale.

**You:** Approve the PRFAQ at the G-prfaq gate. The press release is the altitude-0 forcing function — once committed, initiative briefs trace back to it. A PRFAQ that any product could claim is not yet a PRFAQ; redirect before the cascade and experience direction are set against an unspecific vision.

---

## Stage 3 — Cascade strategy gaps to the shaping queue

The agent runs `run-okr-cascade` to derive team-level OKRs from the company targets, identify the gaps between current state and each target, and prepare strategy-type entries to route into `workspace.toml`. Each gap becomes a `{type = "strategy"}` entry in the shaping queue, signaling to the PE pack's `frame-situation` which items to pick up next.

**You:** Review the gap list at the G-cascade gate before it writes to `workspace.toml`. The cascade write is a shared state change — once entries appear in the shaping queue, product engineers will treat them as the highest-priority strategy-driven work. The correction window is here, before the write.

---

## Stage 4 — Set the experience and content direction

The agent runs `define-ux-strategy` to produce a committed `ux-strategy.md` — the experience vision, goals with measures, and plan, grounded in the approved market situation and PRFAQ. It then runs `define-content-strategy` to produce a committed `content-strategy.md` using the Halvorson quad (Purpose + Process + Structure + Governance), the organizational governance layer that sets the intent above per-surface content work.

**You:** Review both artifacts before sharing them with design and content teams. `ux-strategy.md` is the anchor the experience-design pack reads from when `journey-mapping` and `user-flow` run — an experience vision that doesn't connect to the approved PRFAQ will cause drift between strategy and design. `content-strategy.md` sets the organizational governance intent that the experience-design pack's content-design skill operates within — a governance doc that doesn't name specific decisions (channel priority, ownership model, update cadence) is still a wish list.
