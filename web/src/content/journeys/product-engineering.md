---
pack: product-engineering
scope: user
tagline: "Raw idea → build-ready decision brief with a committed thin slice."
prerequisitePacks: []
contract:
  useItWhen: "You're turning a problem or opportunity into a committed bet — from a raw idea through a shaped intent, de-risked assumption, and placed bet with a thin slice and learning contract."
  youProvide: "A problem, opportunity, or raw idea to shape; any prior research or context."
  youReceive: "A level-tagged intent, a de-risked assumption with a predeclared kill condition, structured solution options, a committed bet.md with thin-slice and learning-contract, and a capability map."
  yourDecisions:
    - "Approve the framed intent"
    - "Choose the option to bet on"
    - "Confirm the thin-slice definition"
    - "Accept the learning contract"
whatChanges: "After installing product-engineering, the shaping loop has a committed artifact set at every stage — from a framed intent through a placed bet with a thin slice, first-success event, and post-launch learning contract. Every bet.md connects to the Digital Experience Contract's PE section, ensuring first-success and thin-slice outputs are visible to experience designers and frontend engineers downstream."
skills:
  - name: frame-intent
    description: "Shapes an idea or request into a level-tagged intent — an outcome + the opportunity behind it. Authors an intent at any altitude: product-vision, product-strategy, capability, or feature."
    humanTouches: 1
  - name: de-risk-intent
    description: "Tests whether the framed intent's bet holds before building it out — naming the riskiest assumption by evidence level, predeclaring a kill condition, and routing to the right prototype approach."
    humanTouches: 1
  - name: diverge-solutions
    description: "Turns a known initiative- or capability-scope opportunity into ≥3 structured, comparable solution options that place-bet can reason against."
    humanTouches: 1
  - name: explore-options
    description: "Generates options for a freeform or feature-scope brief when structured comparable alternatives aren't required."
    humanTouches: 1
  - name: place-bet
    description: "Commits the team to a chosen direction — producing bet.md with a full betting table including thin-slice definition, first-success event, specialist lenses, and post-launch learning contract."
    humanTouches: 1
  - name: map-capabilities
    description: "Translates the committed bet into a Capability Map — L1 domains, Wardley × strategic-criticality annotation, Build/Buy/Partner/Adopt dispositions, and a suggested build sequence."
    humanTouches: 0
  - name: ux-writing
    description: "Shapes the actual words users read in the UI — characterizing the product's voice and writing error, empty, button, and label copy from blame-free, actionable formulas."
    humanTouches: 0
  - name: discovery-loop
    description: "Turns a raw idea into a build-ready decision brief — diverging across candidate shapes, converging through a lens roster with two discovery reviewers, and emitting a connected hypothesis with validation hooks."
    humanTouches: 2
  - name: decompose-intent
    description: "Breaks an intent into the next level down — child intents, or a spec/slice at the leaf — and projects the tree onto your tracker."
    humanTouches: 1
  - name: align-value-stream
    description: "Stands up and keeps current a value-stream meta-repo — coordinating artifacts across component repos for business-unit scale delivery."
    humanTouches: 1
  - name: frame-domain
    description: "Grounds the product in the real-world activity it serves and bounds the MVP — produces Domain Framing and Scope Boundary artifacts."
    humanTouches: 1
  - name: frame-situation
    description: "Classifies an initiative-level signal into a typed finding, assesses Wardley capability maturities, and anchors the team to the right entry point in the shaping sequence."
    humanTouches: 1
  - name: identify-opportunities
    description: "Surfaces all functional, emotional, and social jobs behind an opportunity area, scores each via the Ulwick formula, and produces a ranked opportunity-assessment artifact."
    humanTouches: 1
  - name: lean-canvas
    description: "Elicits an initiative brief through an adapted Lean Canvas and produces a single shareable initiative brief with a Value Proposition section."
    humanTouches: 1
  - name: plan-validation
    description: "Validates a plan against the discovery sidecar — checks that the build plan addresses the grounded hypothesis."
    humanTouches: 0
humanGates:
  - id: G-intent
    globalGate: null
    label: "Approve the framed intent"
    trigger: "After frame-intent produces the outcome + opportunity"
    duration: "5–10 minutes"
    whatToCheck:
      - "Does the outcome name what changes, for whom — not a solution or a task?"
      - "Is the opportunity solution-independent — does it name the job or struggle, not the feature?"
      - "Is the level tagged correctly (product-vision / product-strategy / capability / feature)?"
    whatGoodLooksLike: "A two-sentence intent you could hand to someone who wasn't in the room and they would understand what success looks like and why it matters — without naming a specific UI."
    whatBadLooksLike: "An intent that reads as a spec (names a specific implementation) or a task (names a deliverable rather than an outcome). The test: can you falsify it without building anything?"
    consequence: "An un-scrutinized intent propagates a wrong framing through de-risk, diverge, and bet. Catching it here costs one conversation; catching it at bet costs a sprint."
  - id: G-bet
    globalGate: null
    label: "Choose the option and confirm the thin-slice definition"
    trigger: "After place-bet presents the betting table with all four new required fields"
    duration: "15–30 minutes"
    whatToCheck:
      - "Does the thin-slice definition name a specific user, a specific task, a specific result, a specific failure-recovery, and a specific instrumentation event?"
      - "Is the first-success event observable — would two people agree whether it happened?"
      - "Does the learning contract name specific signals (not 'we'll check metrics'), a review date, and a specific pivot condition?"
      - "Are the specialist lenses complete — product/experience/architecture/safety as default?"
    whatGoodLooksLike: "A thin-slice definition you could hand to a developer as a literal acceptance criterion. A learning contract with a named date and a named signal. A first-success event that reads as a behavior, not a sentiment."
    whatBadLooksLike: "A thin slice that describes a product tour rather than a real task. A learning contract with three blank fields. A first-success event that says 'users adopt it' without naming a behavior."
    consequence: "An under-specified thin slice produces a feature that ships technically complete but never validates the bet. A blank learning contract means the team can never tell whether the bet paid off."
typicalSession:
  agentTurns: "10–20"
  humanTouches: 2
  wallClockMinutes: "30–90"
docsUrl: /docs/guides/product-engineering/
packUrl: /packs/product-engineering/
relatedJourneys:
  - product-strategy
  - experience-design
  - core
---

### 1. Frame the intent

- **You provide:** a problem, opportunity, or raw idea — as rough as "users churn after week one" or "we need to handle enterprise compliance."
- **Agent does:** runs `frame-intent` to shape it into a level-tagged intent — outcome + opportunity, solution-independent. Resolves altitude (product-vision / product-strategy / capability / feature), determines greenfield or brownfield, seeds assumptions.
- **You do:** read the framed intent; confirm the outcome names what changes for a real user and the opportunity names the job or struggle — not a feature. Redirect if it reads as a spec.
- **You decide:** approve the framed intent.
- **Output:** `docs/product/intents/<slug>.md` — the level-tagged intent anchoring the rest of the shaping sequence.

---

### 2. Test the riskiest assumption

- **Agent does:** runs `de-risk-intent` to name the riskiest assumption on the evidence ladder (`observed → supported → inferred → assumed → unknown`), predeclare a kill condition in the test's own currency, and choose a prototype approach (validate-first for one-way doors; prototype-led for two-way doors). Carries a validation hook the discovery loop can consume.
- **You do:** confirm the chosen assumption is genuinely the riskiest — the one that, if wrong, sinks the bet. Check that the kill condition is declared *before* any result is seen.
- **Output:** de-risked intent with a validation hook — `assumption → kill_condition → activity → evidence_level`.

---

### 3. Diverge solution options

- **Agent does:** runs `diverge-solutions` to produce ≥3 structured, comparable solution options — spanning meaningfully different mechanics, scopes, or bets — with a recommendation. Options must not be trivial variations; at least one dimension (mechanic / scope / first-success path) must differ across the set.
- **You do:** review the option set; confirm the options are genuinely different bets (not superficial variations) and that the recommended option's dominant bet is one the team is willing to take.
- **Output:** `docs/product/shaping/<slug>/solution-options.md`.

---

### 4. Place the bet and define the thin slice

- **Agent does:** runs `place-bet` to commit the team to a direction — filling the full betting table including the four new required fields: `thin-slice`, `first-success-event`, `specialist-lenses`, and `learning-contract`. The thin-slice definition names one user, one real task, one meaningful result, one recoverable failure, and one instrumentation event. The learning contract names the signals, the review cadence, and the pivot condition.
- **You do:** confirm the thin-slice definition is specific enough to hand to a developer as an acceptance criterion. Confirm the first-success event is behavioral and observable. Confirm the learning contract has a date and a named pivot condition — not "we'll check metrics."
- **You decide:** choose the option; confirm the thin-slice definition and learning contract.
- **Output:** `docs/product/shaping/<slug>/bet.md` — the anchor for `map-capabilities`.

---

### 5. Map capabilities

- **Agent does:** runs `map-capabilities` to translate the committed bet into a Capability Map — L1 domains, Wardley × strategic-criticality annotation (Genesis → Custom-built → Product → Commodity), Build/Buy/Partner/Adopt dispositions, and a suggested build sequence. Non-Build capabilities appear in domain tables with their disposition.
- **You do:** review the Build sequence; surface any Commodity + Differentiating tensions the agent flags; confirm the sequence order reflects real dependencies and strategic priority.
- **Output:** `docs/product/shaping/<slug>/capability-map.md` — the artifact that routes work into the build loop.
