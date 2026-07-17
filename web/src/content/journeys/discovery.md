---
pack: product-engineering
scope: user
tagline: "Raw idea → build-ready decision brief."
prerequisitePacks: []
whatChanges: "After installing product-engineering, upstream intent work runs through discovery-loop: frame → explore → converge → commit. The discovery-lead agent diverges across candidate product shapes, drives the lens roster to convergence, and emits a connected hypothesis with validation hooks — no engine. You review at four human gates; the agent runs everything between them."
skills:
  - name: discovery-loop
    description: "The discovery supervisor. Diverges across candidate product shapes, drives the lens roster to convergence, and emits a connected hypothesis with validation hooks."
    humanTouches: 4
  - name: frame-intent
    description: "Establishes product framing — problem, user, outcome — before the loop begins."
    humanTouches: 1
  - name: de-risk-intent
    description: "Surfaces the riskiest assumption and designs a prototype approach to de-risk it before committing to build."
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
  - name: voice-and-microcopy
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

## Stage 1 — Shape intent

You described a product idea or problem to the `discovery-lead` agent. The agent activated `discovery-loop`, ran `frame-intent` to establish product framing (problem, user, outcome), and emitted an intent document.

**You did:** Read the intent document — the framing is only a page. Gave concrete corrections if the problem statement was too vague ("users want to collaborate faster" → "the PM can't see which stories are blocked without checking three tools"). Provided the G0 consent once the framing was specific enough to eliminate candidates from. This gate sets the direction for everything that follows.

---

## Stage 2 — Diverge

The agent ran `explore-options` to generate candidate product shapes with distinct tradeoff profiles. Each candidate represented a meaningfully different approach to the problem.

**You did:** Watched as candidates appeared. If a candidate was obviously out-of-scope or repeated a prior approach, say so before the lens roster runs — it saves a review cycle. Otherwise, let the diverge step complete.

---

## Stage 3 — Lens roster

After generating candidates, the agent ran two discovery reviewers — threat and reliability — against each candidate. Each reviewer read cold and returned findings. Candidates that failed the reviewers were eliminated.

**You did:** Monitored the review output. If a candidate you wanted to keep was eliminated, read the finding that killed it — sometimes the finding is correct and you needed to hear it; sometimes it rests on a false premise you can correct with one sentence.

---

## Stage 4 — Mid-discovery check

The agent surfaced the surviving candidates for a mid-course human check. You reviewed which candidates remained and whether the field felt right.

**You did:** At G1.5 you made a call. If only one candidate survived and it felt too easy, ask the agent to re-explore from a different angle. If the survivors felt genuinely distinct, confirm and let the loop converge. This is the last moment to expand the option space cheaply.

---

## Stage 5 — Converge

The agent ran `de-risk-intent` to surface the riskiest assumption and design a prototype approach to test it. It then ran `decompose-intent` to decompose the chosen direction into specs and briefs for the delivery loop.

**You did:** Watched the assumption-test take shape. If the prototype approach the agent proposed was too expensive or wouldn't actually test the assumption, redirect. A bad de-risk approach means the brief reaches the delivery loop with an untested assumption at its core.

---

## Stage 6 — Reconcile and commit

The agent presented the full discovery sidecar — intent, assumption-test, validated candidate, decomposition. You reviewed the G2 reconciliation record and confirmed the decision brief was build-ready.

**You did:** Read the full brief — all sections. At G2 you ratified the reconciliation record; at G3 you committed the brief to the delivery loop. These are two distinct decisions: G2 is "is this brief complete?" and G3 is "am I ready to build this?" A brief can be complete but still wrong.
