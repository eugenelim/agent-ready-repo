---
pack: governance-extras
scope: repo
tagline: "Decision trail — RFCs, ADRs, and conventions for long-lived repos."
prerequisitePacks: []
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

## Stage 1 — Identify the change and open an RFC

You recognize a cross-cutting change — something that affects more than one person, more than one package, or an established convention. The agent activates `new-rfc`, drafts the problem statement, and structures the proposer and objector perspectives.

**You:** Read the RFC draft at the G-draft gate. The most common error at this stage is confusing the solution with the problem — the RFC should name what's broken or missing, not what you want to adopt. If the draft leads with the solution, redirect the agent to reframe around the underlying need. Circulate the draft to the relevant stakeholders after the draft gate passes.

---

## Stage 2 — Comment period and objection handling

Stakeholders review the RFC and raise objections. The agent helps document each objection and draft responses, keeping the RFC's objector section updated as the conversation evolves.

**You:** Manage the comment period — keep it time-boxed, ensure genuine objections get genuine responses, and prevent the RFC from accumulating comments without resolution. An RFC that's "still being discussed" with no decision date is a governance failure, not a process success.

---

## Stage 3 — Decision and follow-on ADR

Once the comment period closes, you make the decision — Accept, Reject, or Defer — and the agent updates the RFC status. If accepted, the agent runs `new-adr` to record the architectural decision that resulted from the RFC.

**You:** Make the call at the G-accept gate. Verify the ADR at the G-merge gate: check that it captures the actual decision and the honest forces behind it, not a post-hoc rationalization. Merge the ADR as part of the same PR or a directly following one — decisions and their documentation belong together.
