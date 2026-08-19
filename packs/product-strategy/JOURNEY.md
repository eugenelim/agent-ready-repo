---
journey_id: product-strategy
pack: product-strategy
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Strategy seat upstream of every initiative — committed artifacts."
prerequisitePacks: []
contract:
  useItWhen: "You're building the committed strategy layer — market analysis, altitude-0 direction, and OKR-derived gap routing — upstream of any product initiative."
  youProvide: "Company OKRs, any prior desk-research outputs, and the scope of the initiative or strategic question to address."
  youReceive: "Committed SWOT, PRFAQ, OKR-derived gap entries in workspace.toml, ux-strategy.md, and content-strategy.md."
  decisionGateIds:
    - approve-strategy-situation
    - approve-prfaq
    - approve-okr-cascade
whatChanges: "After installing product-strategy, every initiative starts with a committed artifact set instead of planning-meeting notes. Nine skills span the full strategy layer: market situation (PESTLE, Porter's, BCG, SWOT), altitude-0 direction (PRFAQ), OKR routing to the PE shaping queue, and the UX and content strategy anchors the experience-design pack reads from. Every artifact commits to `docs/product/shaping/` — the shared path downstream packs reference by name. The OKR cascade writes directly to `workspace.toml`, where product engineers pick up strategy-driven shaping items via `workspace-status`."
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
  - id: approve-strategy-situation
    globalGate: null
    label: "Approve the situation framing"
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
  - id: approve-prfaq
    globalGate: null
    label: "Approve the PR/FAQ"
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
  - id: approve-okr-cascade
    globalGate: null
    label: "Approve the OKR cascade"
    trigger: "After run-okr-cascade identifies gaps and before writing strategy-type entries to workspace.toml"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the OKR cascade identify actual gaps between current state and each target — not features the team wants to build regardless?"
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

| Say this | What happens |
|----------|--------------|
| `run-pestle-analysis` | Scan the macro environment: Political, Economic, Social, Technological, Legal, Environmental |
| `run-porters-five-forces` | Map competitive forces: supplier/buyer power, new entrants, substitutes, rivalry |
| `run-bcg-matrix` | Position each initiative in the portfolio: Stars, Cash Cows, Question Marks, Dogs |
| `run-swot` | Synthesize the situation picture: Strengths, Weaknesses, Opportunities, Threats |
| `run-okr-cascade` | Cascade OKRs, identify gaps, and route them to the PE shaping queue |
| `write-prfaq` | Draft the press release + FAQ before the product exists |
| `synthesize-stakeholder-research` | Synthesize desk-research outputs into a strategic narrative by theme |
| `define-ux-strategy` | Set the experience vision, goals, and plan — upstream of journey-mapping |
| `define-content-strategy` | Set the content governance layer — upstream of content-design |

---

### 1. Analyze the market situation

Run the market analysis sequence — `run-pestle-analysis` (macro environment) → `run-porters-five-forces` (competitive landscape) → `run-bcg-matrix` (portfolio position) — then `run-swot` to synthesize all three into the capstone situation picture.

```text
run-swot

  Quadrant       Items
  ─────────────  ──────────────────────────────────────────────────
  Strengths      Developer-first positioning; fast iteration cycle
  Weaknesses     Low brand awareness outside early-adopter segment
  Opportunities  AI-native distribution; enterprise channel open
  Threats        Funded competitor entering adjacent market

  Approve the situation picture? ›
```

- **You decide:** approve the SWOT before the PRFAQ and OKR cascade build on it — a vague situation picture means downstream artifacts build on ungrounded assumptions.
- **Output:** `docs/product/shaping/swot-analysis.md` — the capstone situation picture built from `macro-environment.md`, `competitive-landscape.md`, and `portfolio-position.md`.
- **State:** draft

---

### 2. Commit altitude-0 direction

Type `write-prfaq` and describe the product concept; the agent drafts the press release and FAQ, naming the specific customer, the measurable benefit, and the hardest objection a skeptical stakeholder would raise.

```text
write-prfaq

  Headline:  [Company] ships workspace.toml — product engineers who
             coordinate AI agent work across sessions.

  Customer:  A solo engineer shipping a 3-person startup's backlog
             with AI coding agents.
  Problem:   Every session starts blind. The agent doesn't know
             what was decided, what's blocked, or what ships next.
  Solution:  workspace.toml — a version-controlled queue the agent
             reads at session start. One grep, full context.

  Approve the PRFAQ? ›
```

- **You decide:** approve the PRFAQ — if the press release doesn't name a specific person or deliver a measurable benefit, redirect before the cascade sets gaps against an underspecified vision.
- **Output:** `docs/product/shaping/prfaq.md` — the altitude-0 forcing function initiative briefs trace back to.
- **State:** draft

---

### 3. Cascade OKRs to the shaping queue

Type `run-okr-cascade`; the agent derives team-level OKRs from company targets, identifies gaps between current state and each target, and prepares strategy-type entries for `workspace.toml`.

```text
run-okr-cascade

  Gap slug              KR                        Priority
  ──────────────────    ──────────────────────    ──────────
  retention-cohort      Retain 60% at week 4      High
  activation-depth      3 features in 14 days     High
  channel-enterprise    ARR from enterprise        Medium

  Approve and write to workspace.toml? ›
```

- **You decide:** approve the gap list — confirm each gap reflects an actual OKR delta, is ranked by OKR weight, and is specific enough for `frame-situation` to scope without re-scoping from scratch.
- **Output:** `docs/product/shaping/okr-cascade.md` and strategy-type entries in `workspace.toml` — gaps product engineers pick up from `workspace-status`.
- **State:** confirmed-write

---

### 4. Set experience and content direction

Type `define-ux-strategy` to commit the experience vision, goals with measures, and plan; type `define-content-strategy` to commit the organizational and governance layer for content.

```text
define-ux-strategy

  Vision:  Reduce session-start friction for engineers who run AI
           coding agents daily — every agent reads context in under
           10 seconds.

  Goals:
    KR-1   Task-completion rate > 80% without re-scoping
    KR-2   Session-start orient time < 10 s (p75)

  committed  docs/product/shaping/ux-strategy.md
```

- **Output:** `docs/product/shaping/ux-strategy.md` and `docs/product/shaping/content-strategy.md` — the anchors the experience-design pack reads from when `journey-mapping` and `content-design` run.
- **State:** draft
