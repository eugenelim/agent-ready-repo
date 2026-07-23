---
pack: governance-extras
scope: repo
tagline: "Decision trail — RFCs, ADRs, and conventions for long-lived repos."
prerequisitePacks: []
contract:
  useItWhen: "A cross-cutting change, architectural decision, or working-convention update needs a structured paper trail that survives personnel changes."
  youProvide: "The change or decision to document, plus any objections or alternatives already under consideration."
  youReceive: "A completed RFC, a merged ADR, or an updated CONVENTIONS.md — with structured rationale the next person can follow."
  yourDecisions:
    - "Review the RFC draft before circulation"
    - "Accept, reject, or defer the RFC"
    - "Merge the ADR"
whatChanges: "After installing governance-extras, cross-cutting changes go through a structured RFC before anyone builds anything, architectural decisions are recorded in ADRs with critique tracks, and CONVENTIONS.md evolves through tracked updates. Every significant 'why did we choose this?' question has an answer that survives personnel changes."
skills:
  - name: new-rfc
    description: "Proposes a cross-cutting change through an RFC with structured proposer and objector perspectives — the front door for changes that affect more than one person or system."
    humanTouches: 3
  - name: new-adr
    description: "Records an architectural decision with two critique tracks — context, decision, alternatives considered, and consequences — so the next person doesn't re-litigate it."
    humanTouches: 2
  - name: update-conventions
    description: "Evolves CONVENTIONS.md with tracked changes — the living record of how this project's team works."
    humanTouches: 1
  - name: rfc-status
    description: "Surfaces the current RFC landscape at a glance — how many RFCs are in each lifecycle state, which are active, and how many findings are waiting in the candidate register."
    humanTouches: 0
humanGates:
  - id: G-draft
    globalGate: null
    label: "Review the RFC draft before circulation"
    trigger: "After new-rfc produces a draft — before it is shared with stakeholders"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the RFC name the problem clearly — not the solution, the problem?"
      - "Are the proposer and objector perspectives genuinely adversarial — not strawman objections?"
      - "Is the scope correct: is this a cross-cutting change that needs an RFC, or a single-team decision that doesn't?"
      - "Are the alternatives in the RFC real alternatives that were actually considered — not alternatives included to make the chosen option look better?"
    whatGoodLooksLike: "An RFC whose problem statement you could send to someone who doesn't know the project and they'd understand what's being debated. Objections that a thoughtful opponent would actually raise."
    whatBadLooksLike: "An RFC that proposes the solution in the problem statement — 'we should adopt X' instead of 'we need to solve Y.' Or objections that are obviously weaker than the proposer's case and weren't genuinely steelmanned."
    consequence: "A bad RFC draft circulates and the feedback it gets is on the framing, not the substance — wasting reviewers' time and forcing a rewrite. The draft gate is cheap; the rewrite gate is not."
  - id: G-accept
    globalGate: null
    label: "Accept, reject, or defer the RFC"
    trigger: "After the comment period closes and the RFC is ready for a decision"
    duration: "15–30 minutes"
    whatToCheck:
      - "Have all objections been addressed — or explicitly acknowledged and set aside with a reason?"
      - "Is the decision clearly stated: Accepted, Rejected, or Deferred — with a rationale?"
      - "If Accepted: is there a follow-on ADR planned to record the architectural decision?"
      - "If Deferred: is there a trigger condition that would bring it back — or is Deferred a polite way of saying Rejected?"
    whatGoodLooksLike: "A clear disposition with a rationale a future reader could follow. Accepted means someone is building it. Rejected means no one is building it and the document explains why."
    whatBadLooksLike: "An RFC that accumulates comments and then sits in limbo — no decision, no follow-on. Or a Deferred with no trigger condition, which means it will never be reconsidered."
    consequence: "An undecided RFC becomes technical debt in the governance register. People build around it, reference it as precedent, or ignore it entirely — none of those outcomes is what the RFC process is for."
  - id: G-merge
    globalGate: "G4"
    label: "Merge the ADR"
    trigger: "After new-adr produces a draft ADR ready for review"
    duration: "10–15 minutes"
    whatToCheck:
      - "Does the ADR record the decision that was actually made — not a slightly better version of it?"
      - "Is the 'Alternatives considered' section honest about why the alternatives were rejected?"
      - "Does the critique track surface the strongest case against the decision — the kind of challenge a skeptical future reader would raise?"
      - "Is the ADR linked from the RFC that preceded it (if one exists)?"
    whatGoodLooksLike: "An ADR a future engineer can read to understand not just what was decided but why — including what would change the decision if it were revisited."
    whatBadLooksLike: "An ADR whose 'Context' section is so thin that a future reader can't reconstruct the problem. Or an ADR that documents the decision but not the forces that drove it — which is exactly what the next person needs to know."
    consequence: "An ADR that doesn't capture the real reasoning is worse than no ADR — it gives false confidence that the decision is documented when the load-bearing reasoning was left in a chat transcript."
typicalSession:
  agentTurns: "6–10"
  humanTouches: 3
  wallClockMinutes: "20–45"
docsUrl: /docs/guides/governance-extras/
packUrl: /packs/governance-extras/
relatedJourneys:
  - core
---

### 1. Draft the RFC

- **You provide:** the cross-cutting change or problem to address, and any known stakeholders or alternatives.
- **Agent does:** activates `new-rfc`, drafts the problem statement, and structures the proposer and objector perspectives.
- **You do:** read the RFC draft; the most common error is confusing the solution with the problem — the RFC should name what's broken or missing; if the draft leads with the solution, redirect to reframe around the underlying need.
- **You decide:** review the RFC draft at G-draft before circulating to stakeholders.
- **Output:** a circulated RFC draft with a clear problem statement and genuine adversarial perspectives.

---

### 2. Manage the comment period

- **Agent does:** documents each objection and drafts responses, keeping the RFC's objector section updated as the conversation evolves.
- **You do:** manage the comment period — keep it time-boxed, ensure genuine objections get genuine responses, and prevent accumulation without resolution; an RFC with no decision date is a governance failure.
- **Output:** a resolved objection record with all objections addressed or explicitly set aside.

---

### 3. Decide and record

- **Agent does:** updates the RFC status with the decision; if accepted, runs `new-adr` to record the architectural decision.
- **You do:** verify the ADR captures the actual decision and the honest forces behind it — not a post-hoc rationalization; merge the ADR as part of the same PR or directly following one.
- **You decide:** accept, reject, or defer the RFC at G-accept; then merge the ADR at G-merge.
- **Output:** a decided RFC and, if accepted, a merged ADR with honest rationale.
