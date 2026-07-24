---
pack: product-engineering
scope: user
tagline: "Raw idea → build-ready decision brief."
prerequisitePacks: []
contract:
  useItWhen: "You have a raw product idea or problem and need to converge on a build-ready decision brief before anyone writes code."
  youProvide: "A product idea or problem description, with any scope constraints or prior discovery context."
  youReceive: "A build-ready decision brief — intent, validated candidate, assumption-test, and decomposition into delivery briefs."
  yourDecisions:
    - "Shape intent"
    - "Mid-discovery check"
    - "Reconcile"
    - "Commit to build"
whatChanges: "After installing product-engineering, upstream intent work runs through discovery-loop: frame → explore → converge → commit. The discovery-lead agent diverges across candidate product shapes, drives the lens roster to convergence, and emits a connected hypothesis with validation hooks — no engine. You review at four human gates; the agent runs everything between them."
skills:
  - name: discovery-loop
    description: "The discovery supervisor. Diverges across candidate product shapes, drives the lens roster to convergence, and emits a connected hypothesis with validation hooks."
    humanTouches: 4
  - name: frame-intent
    description: "Establishes product framing — problem, user, outcome — before the loop begins."
    humanTouches: 1
  - name: frame-domain
    description: "Grounds the product in the real-world activity it serves and bounds the MVP — produces Domain Framing and Scope Boundary artifacts before the convergent design loop."
    humanTouches: 1
  - name: frame-situation
    description: "Classifies an initiative-level signal into a typed finding, assesses Wardley capability maturities, and anchors the team to the right entry point in the PE six-step shaping sequence."
    humanTouches: 1
  - name: identify-opportunities
    description: "Step 2 of the PE six-step shaping sequence — surfaces all functional, emotional, and social jobs behind an opportunity area, scores each via the Ulwick formula, and produces a ranked opportunity-assessment.md artifact."
    humanTouches: 1
  - name: diverge-solutions
    description: "Generates ≥3 structured comparable solution options for a confirmed opportunity, with a recommendation and retained rationale for parked and rejected options."
    humanTouches: 1
  - name: lean-canvas
    description: "Elicits an initiative brief through an adapted Lean Canvas (simple 5-box or full 9-box) and produces a single shareable initiative brief with a Value Proposition section."
    humanTouches: 1
  - name: de-risk-intent
    description: "Surfaces the riskiest assumption and designs a prototype approach to de-risk it before committing to build."
    humanTouches: 1
  - name: place-bet
    description: "Step 5 of the PE six-step shaping sequence — commits the team to a chosen direction by producing a structured bet.md with a full betting table for map-capabilities to reason against."
    humanTouches: 1
  - name: map-capabilities
    description: "Step 6 (terminal) of the PE six-step shaping sequence — translates a committed bet into a Capability Map with L1 domain organisation, Wardley × strategic-criticality annotation, Build/Buy/Partner/Adopt disposition, and a Build-only suggested build sequence anchoring M3–M6 spec-writing."
    humanTouches: 1
  - name: decompose-intent
    description: "Decomposes the chosen direction into briefs and specs for the delivery loop."
    humanTouches: 1
  - name: explore-options
    description: "Generates candidate product shapes with distinct tradeoff profiles."
    humanTouches: 0
  - name: plan-validation
    description: "Validates a plan against the discovery sidecar — checks that the build plan addresses the grounded hypothesis."
    humanTouches: 0
  - name: ux-writing
    description: "Characterizes a product's voice and writes blame-free, actionable UI copy."
    humanTouches: 1
  - name: align-value-stream
    description: "Coordinates a multi-component product intent across a business-unit value stream."
    humanTouches: 1
humanGates:
  - id: G0
    globalGate: "G0"
    label: "Shape intent"
    trigger: "After frame-intent emits the initial framing"
    duration: "10–15 minutes"
    whatToCheck:
      - "Is the problem statement specific enough to eliminate candidates? (A vague problem cannot be de-risked.)"
      - "Is the user named specifically — not 'users' or 'teams'?"
      - "Is the outcome measurable — what would change in the world if this succeeded?"
    whatGoodLooksLike: "A framing that names a specific user, a falsifiable problem, and a measurable outcome."
    whatBadLooksLike: "A framing that could apply to any product — 'improve developer productivity' is not a problem statement."
    consequence: "G0 is the framing gate. A bad framing means the entire discovery loop explores the wrong space."
  - id: "G1.5"
    globalGate: null
    label: "Mid-discovery check"
    trigger: "After explore-options and the first lens-roster pass"
    duration: "15–20 minutes"
    whatToCheck:
      - "Which candidates survived the lens roster? Do the survivors feel right?"
      - "Are eliminated candidates genuinely eliminated, or just deprioritized?"
      - "Is there a candidate missing that should be explored?"
    whatGoodLooksLike: "A clear field of two or three differentiated candidates, each with a distinct tradeoff profile."
    whatBadLooksLike: "All candidates converged to the same shape before the lens roster ran — the diverge step didn't diverge."
    consequence: "The mid-discovery check prevents the loop from converging on a bad candidate without the human noticing."
  - id: G2
    globalGate: null
    label: "Reconcile"
    trigger: "After the full lens-roster pass on the surviving candidates"
    duration: "20–30 minutes"
    whatToCheck:
      - "Did both discovery reviewers (threat + reliability) flag anything that would block the build?"
      - "Does the validated candidate's hypothesis have a clear validation hook?"
      - "Is the decomposition granular enough to fit in one build-loop iteration?"
    whatGoodLooksLike: "A build-ready decision brief — reviewers clean, falsifiable hypothesis, decomposition that fits the delivery loop."
    whatBadLooksLike: "A brief that passes the gate but skips the riskiest assumption. Or a decomposition too large for one loop."
    consequence: "G2 produces the build commitment artifact. A bad brief means the delivery loop builds the wrong thing faithfully."
  - id: G3
    globalGate: "G3"
    label: "Commit to build"
    trigger: "After the reconciliation record is ratified"
    duration: "5 minutes"
    whatToCheck:
      - "Is the decision brief complete? (intent, assumption-test, validated candidate, decomposition)"
      - "Is there anything in the brief you are not prepared to ship?"
    whatGoodLooksLike: "You ratify the brief and hand it to the delivery loop."
    whatBadLooksLike: "You ratify with reservations and don't surface them. The delivery loop builds faithfully to a brief you had doubts about."
    consequence: "G3 is the discovery-to-delivery handoff. After this gate, the delivery loop builds."
typicalSession:
  agentTurns: "12–20"
  humanTouches: 4
  wallClockMinutes: "60–120"
docsUrl: /docs/guides/product-engineering/
packUrl: /packs/product-engineering/
relatedJourneys:
  - core
---

### 1. Shape intent

- **You provide:** a product idea or problem description.
- **Agent does:** activates `discovery-loop`, runs `frame-intent` to establish product framing (problem, user, outcome), and emits an intent document.
- **You do:** read the intent document — the framing is only a page; give concrete corrections if the problem statement is too vague ("users want to collaborate faster" → "the PM can't see which stories are blocked without checking three tools").
- **You decide:** give G0 consent once the framing is specific enough to eliminate candidates — this gate sets the direction for everything that follows.
- **Output:** an intent document with a specific problem, named user, and measurable outcome.

---

### 2. Diverge across candidates

- **Agent does:** runs `explore-options` to generate candidate product shapes with distinct tradeoff profiles.
- **You do:** watch candidates appear; if a candidate is obviously out-of-scope or repeats a prior approach, say so before the lens roster runs — it saves a review cycle.
- **Output:** a set of candidate product shapes with distinct tradeoff profiles.

---

### 3. Run the lens roster

- **Reviewer does:** runs two discovery reviewers — threat and reliability — against each surviving candidate; each reads cold and returns findings; candidates that fail are eliminated.
- **You do:** monitor the review output; if a candidate you want to keep is eliminated, read the finding — sometimes it rests on a false premise you can correct with one sentence.
- **Output:** a filtered candidate set with review findings attached.

---

### 4. Check mid-discovery

- **Agent does:** surfaces the surviving candidates for a mid-course review.
- **You do:** review which candidates remain and whether the field feels right; if only one candidate survives and it feels too easy, consider asking the agent to re-explore from a different angle.
- **You decide:** confirm the surviving candidates at the mid-discovery check (G1.5), or direct a re-exploration — this is the last moment to expand the option space cheaply.
- **Output:** a confirmed candidate field ready for convergence.

---

### 5. Converge on the candidate

- **Agent does:** runs `de-risk-intent` to surface the riskiest assumption and design a prototype approach to test it; then runs `decompose-intent` to decompose the chosen direction into specs and briefs for the delivery loop.
- **You do:** watch the assumption-test take shape; if the prototype approach is too expensive or won't actually test the assumption, redirect — a bad de-risk approach means an untested assumption at the brief's core.
- **Output:** a de-risked candidate with decomposition into delivery briefs.

---

### 6. Reconcile and commit

- **Agent does:** presents the full discovery sidecar — intent, assumption-test, validated candidate, and decomposition.
- **You do:** read the full brief — all sections; G2 is "is this brief complete?" and G3 is "am I ready to build this?" — these are two distinct decisions.
- **You decide:** ratify the reconciliation record at G2; commit the brief to the delivery loop at G3.
- **Output:** a ratified decision brief handed to the delivery loop.
