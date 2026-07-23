---
pack: architect
scope: user
tagline: "Design docs, diagrams, and reviews — workspace-agnostic."
prerequisitePacks: []
contract:
  useItWhen: "You need a technical design doc, architecture diagram, or design critique for your codebase."
  youProvide: "The design problem, real constraints, and the repo's reference architecture."
  youReceive: "An approved Stage 1 design document with alternatives and an independent severity-tagged critique."
  yourDecisions:
    - "Approve the Stage 0 concept"
    - "Review the design and independent critique"
whatChanges: "After installing architect, every architecture artifact gets a method: `architect-design` produces Google-style design docs grounded against your repo's `reference.md`, `architect-diagram` draws the system in Mermaid (C4, sequence, state, ER, deployment), and `architect-review` critiques any design artifact with a severity-tagged rubric. The forked-context `design-reviewer` subagent gives every design an independent read — a reviewer that has not seen the authoring session."
skills:
  - name: architect-design
    description: "Authors a Google-style technical design doc: Stage 0 concept → Stage 1 full write-up → Stage 2 review-ready artifact, grounded against the repo's reference architecture."
    humanTouches: 2
  - name: architect-diagram
    description: "Draws the system, data model, flow, state, or deployment in Mermaid — C4 component, sequence, state, ER, or deployment topology."
    humanTouches: 1
  - name: architect-review
    description: "Critiques an existing design doc, diagram, RFC, or ADR with a rubric-routed severity-tagged review; dispatches the independent forked-context design-reviewer subagent."
    humanTouches: 1
humanGates:
  - id: G-concept
    globalGate: null
    label: "Approve the Stage 0 concept"
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
  - id: G-review
    globalGate: null
    label: "Review the design and independent critique"
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

### 1. Ground the design in the reference architecture

- **Agent does:** checks for a `reference.md` in the repo — the golden-path file that describes the stack, patterns, and constraints the architecture skills design against — and offers to create it if one doesn't exist.
- **You do:** confirm the reference is accurate for this task; update it before the design session starts if it is stale or missing a key constraint.
- **Output:** a current, grounded `reference.md` the design skills can rely on.

---

### 2. Frame the Stage 0 concept

- **You provide:** a description of the design problem.
- **Agent does:** runs `architect-design` in Stage 0 mode, producing a half-page concept that frames the problem, names constraints, and proposes a candidate approach with at least one alternative.
- **You decide:** approve the concept at the G-concept gate, or redirect before the full write-up begins; if the alternatives section feels thin, ask for one more before approving.
- **Output:** an approved Stage 0 concept.

---

### 3. Write the full design document

- **Agent does:** writes the full Stage 1 design document — problem statement, alternatives with rejection reasoning, proposed design, open questions, and success criteria — grounded against `reference.md` throughout.
- **You do:** watch the document take shape; if the alternatives section omits an approach the team has already discussed and ruled out, mention it; note any scope drift from the approved concept.
- **Output:** a full Stage 1 design document ready for independent review.

---

### 4. Review independently

- **Reviewer does:** reads the design cold in a forked context (`design-reviewer`) — a reviewer that has not seen the authoring session — and returns findings grouped by severity: Blockers, Concerns, Nits.
- **You do:** read the findings as they land; give a one-sentence steer on any Blocker you disagree with.
- **You decide:** for each Blocker, fix it or provide a one-sentence reason it doesn't apply; apply or defer Concerns and Nits with a reason.
- **Output:** a design doc with a clean independent review, or concerns surfaced clearly to you.
