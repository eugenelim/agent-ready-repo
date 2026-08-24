---
journey_id: architect
pack: architect
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Understand what exists, choose where to look, and act on evidence."
prerequisitePacks: []
contract:
  useItWhen: "You need to understand, harden, optimize, scale, modernize, rationalize, design, diagram, or review an architecture."
  youProvide: "The repository or system boundary, the decision you need to make, and approval for any evidence beyond ordinary read-only inspection."
  youReceive: "A corrected current-state model, evidence coverage, attention hotspots, bounded findings, and traced action waves; or the routed design, diagram, or review artifact."
  yourDecisions:
    - "Correct or accept the current-state model"
    - "Redirect or accept the hotspot drill-downs"
    - "Accept the evidence and action priority, request more proof, or route into future-state design"
  decisionGateIds:
    - correct-current-state-map
    - choose-architecture-hotspots
    - accept-architecture-action
whatChanges: "After installing architect, a broad request such as 'Assess architecture and provide an action plan' follows one progressive method instead of collapsing into a folder or compliance audit. architect-assess separates target evidence, enterprise context, and reusable pack knowledge; supports survey, standard, and deep stopping depths; and asks before private retrieval, execution, runtime evidence, experiments, or writes. architect-design owns future-state choices, architect-diagram owns the picture, architect-review owns supplied-artifact critique, and design-reviewer supplies the independent cold-context pass. Saved architecture-design and current-architecture outputs resolve separately; the user-scope pack remains useful in chat-only and explicit personal-workspace modes, while compatible repositories consume Core's semantic-surface-resolution.v1 and other repositories receive a zero-write portable handoff. The generated architecture-lenses-reference skill is internal knowledge routing, not a fifth user workflow."
skills:
  - name: architect-assess
    description: "Maps and pressure-tests the implemented architecture through Frame, Map, Focus, Investigate, Act, and Close."
    humanTouches: 3
  - name: architect-design
    description: "Shapes a Stage-0 concept, writes a Google-style design doc, and converges it against review."
    humanTouches: 2
  - name: architect-diagram
    description: "Draws the system, flow, state, data model, or deployment topology in Mermaid."
    humanTouches: 1
  - name: architect-review
    description: "Critiques an assessment, design doc, diagram, RFC, or ADR with a rubric-routed verdict and severity-tagged findings."
    humanTouches: 1
  - name: architecture-lenses-reference
    description: "Supplies the architect pack's generated, read-only knowledge paths to its workflows; it is not a user-facing workflow."
    humanTouches: 0
humanGates:
  - id: correct-current-state-map
    globalGate: null
    label: "Correct the conceptual current state"
    trigger: "After Map shows the system boundary, views, evidence ledger, and unknowns"
    duration: "5–15 minutes"
    whatToCheck:
      - "Are repositories, deployables, runtimes, data stores, and external systems distinguished?"
      - "Are responsibilities and trust boundaries recognizable?"
      - "Are inferred or missing dependencies marked instead of invented?"
    whatGoodLooksLike: "A conceptual model the team recognizes, with observed, inferred, reported, and unknown elements kept distinct."
    whatBadLooksLike: "A directory tree relabeled as architecture, or a repo boundary treated as the whole production system."
    consequence: "A wrong model distorts hotspot selection and every later finding; correct it before expensive investigation."
  - id: choose-architecture-hotspots
    globalGate: null
    label: "Choose the hotspot drill-downs"
    trigger: "After Focus shows raw attention dimensions and proposed hotspot cards"
    duration: "5–10 minutes"
    whatToCheck:
      - "Do the raw signals and counter-evidence justify investigation?"
      - "Which user journey or quality scenario could be affected?"
      - "Is the proposed drill-down bounded and decision-relevant?"
    whatGoodLooksLike: "A small accepted set of hotspots with evidence pointers, plausible consequences, unknowns, and next checks."
    whatBadLooksLike: "Heat treated as severity, or every large/churned file queued for equal investigation."
    consequence: "Survey may stop here; standard and deep spend their investigation budget only on the accepted set."
  - id: accept-architecture-action
    globalGate: null
    label: "Accept the evidence and action priority"
    trigger: "After Close presents findings, strengths, unknowns, action waves, coverage, and confidence"
    duration: "15–30 minutes"
    whatToCheck:
      - "Does each finding trace evidence to a mechanism and stakeholder or measurable scenario?"
      - "Does every wave cite finding IDs, dependencies, completion proof, and containment or rollback?"
      - "Are active defects contained before generalized controls and broad modernization?"
      - "Which remaining uncertainty could change the decision?"
    whatGoodLooksLike: "Actions fit the assessment intent and can be proven complete without erasing strengths or unknowns."
    whatBadLooksLike: "A generic cleanup or rewrite backlog derived from heat, style, file size, or best-practice claims."
    consequence: "You decide whether to act, gather more evidence, save the report, or route a future-state choice to architect-design."
typicalSession:
  agentTurns: "4–10"
  humanTouches: 3
  wallClockMinutes: "20–90"
docsUrl: /docs/guides/architect/
packUrl: /packs/architect/
relatedJourneys:
  - core
  - experience-design
---

> Assess architecture and provide an action plan.

### 1. Frame the decision

- **You provide:** the request above, optionally adding hardening, optimization,
  growth, transformation, or disposition intent.
- **Agent does:** bounds the target and evidence, selects standard mode, names
  enterprise knowledge it can detect, and stays read-only.
- **You decide:** correct scope or continue.
- **Output:** an assessment charter with exclusions and unknowns.
- **State:** read-only

### 2. Correct the current-state map

- **You provide:** a boundary correction, or `continue`.
- **Agent does:** inventories required evidence and maps context, runtime,
  modules, data, interactions, delivery/operations, and trust/identity.
- **You decide:** accept the model before Focus.
- **Output:** the conceptual model, evidence ledger, shape/workload hypotheses,
  and important unknowns.
- **State:** read-only

### 3. Choose the hotspots

- **You provide:** an added, removed, or redirected hotspot, or `continue`.
- **Agent does:** shows consequence, pressure, coupling/concentration,
  verification weakness, exposure, and confidence separately.
- **You decide:** stop with a survey or accept the drill-down set.
- **Output:** an attention heat map and bounded hotspot cards. Heat is not
  finding severity.
- **State:** read-only

### 4. Investigate and act

- **You provide:** a request to continue in standard mode and separate approval for any executable,
  private, runtime, stakeholder, or experimental evidence.
- **Agent does:** traces normal, side-effect, and failure/recovery paths; proves
  or refutes hypotheses; and sequences findings into action waves.
- **You decide:** act, request more proof, or route a future-state choice.
- **Output:** findings, strengths, unknowns, lens coverage, completion proof,
  containment, and one next decision.
- **State:** draft

### 5. Save or review

- **You provide:** “Save this assessment” or “Review this assessment report.”
- **Agent does:** classifies the saved artifact as current architecture or
  architecture design, names chat-only, personal-workspace,
  repository-resolved, or repository-handoff mode, surfaces the final local
  path before an approved write only for a confined writable mode, stops a
  repository handoff without writing, or sends the supplied artifact through
  independent review without rescanning.
- **You decide:** accept the report as decision evidence or revise it.
- **Output:** `<resolved destination>/<topic-slug>/assessment.md` when saved,
  a portable repository handoff when Core is unavailable, or an inline
  severity-tagged report critique.
- **State:** confirmed-write
