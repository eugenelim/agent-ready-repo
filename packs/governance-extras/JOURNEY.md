---
journey_id: governance-extras
pack: governance-extras
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: "decisions committed, proposals structured, conventions tracked."
prerequisitePacks:
  - core
contract:
  useItWhen: "A cross-cutting change, architectural decision, or working-convention update needs a structured paper trail that survives personnel changes."
  youProvide: "The change or decision to document, plus any objections or alternatives already under consideration."
  youReceive: "A completed RFC, a merged ADR, or an updated CONVENTIONS.md — with structured rationale the next person can follow."
  yourDecisions:
    - "Review the RFC draft before circulation"
    - "Accept, reject, or defer the RFC"
    - "Merge the ADR"
  decisionGateIds:
    - review-rfc-draft
    - decide-rfc
    - merge-accepted-adr
whatChanges: "After installing governance-extras, cross-cutting changes go through a structured RFC before anyone builds anything. Architectural decisions are recorded in ADRs with honest critique tracks. Before an ADR receives an ordinal or index, new-adr resolves the portable decision-record role through compatible Core so adopter policy and established custom or external destinations win; older or absent capability produces confirmation or a portable handoff rather than simulated resolution. When core project knowledge is present, reusable supporting practice can be captured only at the written-and-clean RFC handoff or the decision-maker's ADR acceptance; normative content stays in its owning artifact. CONVENTIONS.md evolves through tracked updates, not drift. Every significant 'why did we choose this?' has an answer that survives personnel changes."
skills:
  - name: new-rfc
    description: "Proposes a cross-cutting change through an RFC with structured proposer and objector perspectives, with optional supporting-practice capture only after the written draft passes every mandatory check."
    humanTouches: 3
  - name: new-adr
    description: "Records an architectural decision with two critique tracks and optional supporting-practice capture only when the decision-maker accepts it."
    humanTouches: 2
  - name: rfc-status
    description: "Surfaces the current RFC landscape at a glance — how many RFCs are in each lifecycle state, which are active, and how many findings are waiting in the candidate register."
    humanTouches: 0
humanGates:
  - id: review-rfc-draft
    globalGate: null
    label: "Review the RFC draft"
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
  - id: decide-rfc
    globalGate: null
    label: "Accept or decline the RFC"
    trigger: "After the comment period closes and the RFC is ready for a decision"
    duration: "15–30 minutes"
    whatToCheck:
      - "Have all objections been addressed — or explicitly acknowledged and set aside with a reason?"
      - "Is the decision clearly stated: Accepted or Rejected — with a rationale?"
      - "If Accepted: is there a follow-on ADR planned to record the architectural decision?"
    whatGoodLooksLike: "A clear disposition with a rationale a future reader could follow. Accepted means someone is building it. Rejected means no one is building it and the document explains why."
    whatBadLooksLike: "An RFC that accumulates comments and then sits in limbo — no decision, no follow-on."
    consequence: "An undecided RFC becomes technical debt in the governance register. People build around it, reference it as precedent, or ignore it entirely — none of those outcomes is what the RFC process is for."
  - id: merge-accepted-adr
    globalGate: "G4"
    label: "Merge the accepted ADR"
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

| Say this               | What happens                                            |
|------------------------|---------------------------------------------------------|
| `rfc-status`           | Orient — RFC landscape by status and findings count     |
| `new-rfc`              | Propose a cross-cutting change through a structured RFC |
| `new-adr`              | Record an architectural decision with critique tracks   |

---

### 1. Draft the RFC

Type `new-rfc` and describe the change you want to propose — the agent structures the proposal, models the proposer and objector perspectives, and previews the draft before writing anything.

```text
new-rfc [adopt trunk-based development]

  identifier   RFC-0043
  title        Trunk-based development over feature branches
  status       Draft
  target       docs/rfc/0043-trunk-based-development.md

  Proposer     Reduces integration latency; CI catches regressions fast
  Objector     Long-lived branches give teams isolation; trunk conflicts are costly

Approve? ›
```

- **You decide:** review the RFC draft before circulating — the most common error is naming the solution in the problem statement; redirect to reframe around the underlying need.
- **Output:** `docs/rfc/0043-trunk-based-development.md` — a circulated RFC draft with a clear problem statement and genuine adversarial perspectives. After every mandatory check is clean and the RFC and index entry are written, `rfc-handoff-ready` may capture reusable supporting practice through core's public seam; incomplete or abandoned work produces no capture.
- **State:** proposed-write

---

### 2. Manage the comment period

Type `rfc-status` at any point during the comment period to see where the RFC stands — the agent keeps the RFC's objector section updated as feedback arrives.

```text
rfc-status

  Active:

  | State | RFCs                                       |
  |-------|--------------------------------------------|
  | Open  | RFC-0043: Trunk-based development          |

  Resolved:

  | State    | Count |
  |----------|------:|
  | Accepted |    12 |
  | Rejected |     2 |

  RFC candidates: 3 entries
```

- **Output:** a resolved objection record — all objections addressed or explicitly set aside with a reason.
- **State:** draft

---

### 3. Decide and record

Close the comment period, state your decision, and type `new-adr` to lock in the
architectural record. The agent resolves `decision-record` before choosing the
ordinal/index, then previews the ADR before writing. This example repository has
confirmed the catalogue fallback; an adopter's custom location would win.

```text
new-adr [branching strategy: trunk-based development]

  identifier   ADR-0028
  title        Branching strategy: trunk-based development
  status       Proposed
  target       docs/adr/0028-branching-strategy-trunk-based.md

  Decision     Use trunk-based development over long-lived feature branches
  Tradeoff     Requires disciplined CI; enables faster integration loop

Approve? ›
```

- **You decide:** accept or decline the RFC; then merge the accepted ADR.
- **Output:** a decided RFC and, if accepted, a merged ADR with honest rationale — linked from the RFC that produced it. Only the decision-maker's Proposed-to-Accepted transition reaches `adr-accepted`; previewed, rejected, or abandoned ADRs never capture, and normative decisions remain solely in the ADR.
- **State:** confirmed-write
