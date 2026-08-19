---
journey_id: architect
pack: architect
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Concept to reviewed architecture doc — any workspace."
prerequisitePacks: []
contract:
  useItWhen: "You need a technical design doc, architecture diagram, or design critique for your codebase."
  youProvide: "The design problem, real constraints, and the repo's reference architecture."
  youReceive: "An approved Stage 1 design document with alternatives and an independent severity-tagged critique."
  yourDecisions:
    - "Approve the Stage 0 concept"
    - "Review the design and independent critique"
  decisionGateIds:
    - approve-architecture-concept
    - review-architecture-design
whatChanges: "After installing architect, every design decision gets a method: `architect-design` shapes a Stage 0 concept before any full write-up begins, writes the complete Google-style doc, and converges it against review; `architect-diagram` draws any system in Mermaid (C4, sequence, state, ER, or flowchart); `architect-review` critiques any design artifact with severity-tagged findings and may consult one bounded untrusted project-knowledge envelope after fixing its scope and rubric. The `design-reviewer` subagent reads finished artifacts cold — no authoring context — so the review cannot mark its own homework. Retrieved knowledge remains candidate evidence, and you decide at two gates: the Stage 0 concept before the full doc is written, and the independently grounded review findings before the doc is shared or acted on."
skills:
  - name: architect-design
    description: "Authors a Google-style technical design doc: Stage 0 concept → Stage 1 full write-up → Stage 2 review-ready artifact, grounded against the repo's reference architecture."
    humanTouches: 2
  - name: architect-diagram
    description: "Draws the system, data model, flow, state, or deployment in Mermaid — C4 component, sequence, state, ER, or deployment topology."
    humanTouches: 1
  - name: architect-review
    description: "Critiques an existing design doc, diagram, RFC, or ADR with a rubric-routed severity-tagged review; an optional CQ-REVIEW enquiry supplies untrusted candidate checks without changing independent judgment."
    humanTouches: 1
humanGates:
  - id: approve-architecture-concept
    globalGate: null
    label: "Approve the architecture concept"
    trigger: "After architect-design emits the initial Stage 0 concept framing"
    duration: "5–10 minutes"
    whatToCheck:
      - "Is the problem statement clear and bounded — does it eliminate non-solutions?"
      - "Are the listed constraints real constraints (things that cannot change) or preferences?"
      - "Does the concept name the users and success criteria, not just the proposed approach?"
      - "Is there an alternatives section, even at Stage 0 — at least two candidate approaches considered?"
    whatGoodLooksLike: "A half-page concept that names the problem, real constraints, and a candidate approach — specific enough to commit to a full design doc or redirect before one is written."
    whatBadLooksLike: "A concept that describes an approach without stating what problem it solves, or one that lists constraints the team would actually trade away if asked."
    consequence: "The concept approval gates the full write-up. A wrong concept means the agent writes a polished doc for the wrong problem — the cost is a full write-up cycle, not a concept cycle."
  - id: review-architecture-design
    globalGate: null
    label: "Review the architecture design"
    trigger: "After architect-review or the design-reviewer subagent returns its findings"
    duration: "15–25 minutes"
    whatToCheck:
      - "Did the independent design-reviewer flag any Blockers? (These are unchecked assumptions or missing alternatives — the ones a stakeholder would ask about.)"
      - "Is the alternatives section complete — does it explain why alternatives were rejected, not just that they were?"
      - "Are the open questions named explicitly — things not decided yet, distinguished from things decided badly?"
      - "Does the doc match the Stage 0 concept you approved, or did it drift?"
    whatGoodLooksLike: "A design doc with a clean independent review, a full alternatives section with reasoning, and explicitly named open questions."
    whatBadLooksLike: "A design doc that passes review because the reviewer was given the authoring context and couldn't disagree. Or one that omits the alternatives the team already considered."
    consequence: "The design doc is the artifact future engineers read when they encounter the system. An incomplete design doc creates an undocumented system — and every reader will form their own theory of why it works the way it does."
typicalSession:
  agentTurns: "6–10"
  humanTouches: 2
  wallClockMinutes: "30–60"
docsUrl: /docs/guides/architect/
packUrl: /packs/architect/
relatedJourneys:
  - core
  - experience-design
---

| Say this | What happens |
|----------|-------------|
| `architect-design` | Frame a concept, write a Google-style design doc, and converge it against review |
| `architect-diagram` | Draw a Mermaid diagram — C4, sequence, state, ER, or flowchart |
| `architect-review` | Critique a design doc or diagram with independently grounded, severity-tagged findings |

---

### 1. Ground in the reference architecture

Type `architect-design` — the skill checks what architecture context exists in the repo and states what it found before framing begins.

```text
architect-design

  Knowledge surface: docs/architecture/reference.md

  Stack       Node.js 20 · PostgreSQL 15 · S3
  Patterns    CQRS; event-sourced ledger for financial data
  Concern     Multi-tenancy, tenant data isolation
```

- **Output:** the architecture context the design will be grounded against, or an offer to create `reference.md` if none exists.
- **State:** read-only

---

### 2. Frame the Stage 0 concept

Type `architect-design [describe the problem]` — the agent shapes a ½-page concept covering the problem, constraints, and candidate approaches, then stops for your approval before the full doc is written.

```text
  concept  docs/design/multi-tenant-billing/concept.md

  Problem      Billing engine for a multi-tenant SaaS.
  Constraint   No shared state between tenants.
  Candidates   Event-sourced ledger; relational schema + row-level security

Approve this shape? ›
```

- **You decide:** approve the concept or redirect — a one-sentence redirect here saves a full write-up cycle.
- **Output:** `docs/design/multi-tenant-billing/concept.md` — the approved Stage 0 concept.
- **State:** draft

---

### 3. Write the full design document

The agent writes the complete Google-style doc — TL;DR, Context, Goals, Proposal, Alternatives, Risks, Rollout, Open Questions — self-checked against the design-doc rubric before you see it.

```text
  docs/design/multi-tenant-billing/design.md

  ## TL;DR

  Introduce a dedicated billing service backed by an event-sourced ledger.
  Tenant isolation is enforced at ingestion by partition key, not at query
  time by row-level security — a constraint we cannot control in
  third-party integrations.
```

- **Output:** `docs/design/multi-tenant-billing/design.md` — the full design doc, rubric-clean and ready for independent review.
- **State:** draft

---

### 4. Review independently

Type `architect-review` — the forked-context `design-reviewer` subagent reads the artifact cold with no authoring memory and returns severity-tagged findings.

```text
architect-review docs/design/multi-tenant-billing/design.md

  Verdict: SHIP WITH CHANGES

  🟥  Proposal §4 — trust boundary between billing service and payment
      processor is unlabeled; required before the integration contract
      can be implemented.
  🟧  Alternatives §2 — relational-plus-RLS rejection reason is thin.
  ⚪  TL;DR sentence 2 could be tightened.
```

- **You decide:** for each Blocker, apply the fix or give a one-sentence reason it doesn't apply; apply or defer Concerns and Nits with a reason.
- **Output:** a review-clean design doc ready to share with stakeholders or hand to the build loop.
- **State:** confirmed-write
