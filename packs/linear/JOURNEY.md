---
journey_id: linear
pack: linear
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "Linear source → reviewed repository work."
contract:
  useItWhen: "You want to start repository work from Linear or compare an existing tracker-origin artifact with its source."
  youProvide: "A Linear Issue, Project, Cycle, view, selection, or registered artifact path."
  youReceive: "A bounded content-based route or reviewed field delta, with separate confirmation for any declared coordination action."
  yourDecisions:
    - "Resolve any route or confidentiality gap"
    - "Approve local refresh field decisions"
    - "Confirm one exact Linear coordination action"
  decisionGateIds:
    - review-linear-route
    - confirm-linear-action
skills:
  - name: linear
    description: "Acquires bounded Linear data, registers the refresh profile, and performs only separately confirmed profile-declared coordination actions."
    humanTouches: 1
  - name: linear-brief-intake
    description: "Normalizes bounded Linear content and delegates it to the shared content-based repository route."
    humanTouches: 1
  - name: linear-brief-sync
    description: "Compatibility wording for a brief-specific request that delegates to the same reviewed refresh authority."
    humanTouches: 1
humanGates:
  - id: review-linear-route
    globalGate: null
    label: "Review the repository route"
    trigger: "After intake returns its artifact, lifecycle membership, processor, authority mode, and named gaps"
    duration: "1–5 minutes"
    whatToCheck:
      - "Does content and coherence support the route?"
      - "Is source provenance complete and the destination appropriate?"
    whatGoodLooksLike: "Equivalent content reaches the same route as every other supported profile."
    whatBadLooksLike: "A Project forced into a brief or a Cycle forced into a collection route by type alone."
    consequence: "The wrong durable artifact enters the repository lifecycle."
  - id: confirm-linear-action
    globalGate: null
    label: "Confirm one Linear coordination action"
    trigger: "After the exact action, target, and payload digest are shown"
    duration: "1–2 minutes"
    whatToCheck:
      - "Is this the registered source item?"
      - "Is the action declared by the exact profile version?"
    whatGoodLooksLike: "One bounded coordination action with a fresh confirmation and pending receipt."
    whatBadLooksLike: "A requirement rewrite, generic mutation, or automatic retry."
    consequence: "The wrong remote item may be changed and the confirmation cannot be reused."
typicalSession:
  agentTurns: "3–6"
  humanTouches: 1
  wallClockMinutes: "5–15"
docsUrl: /docs/guides/linear/
packUrl: /packs/linear/
---

| Say this | What happens |
| --- | --- |
| `Intake Linear issue LIN-123 as repository work. Start read-only.` | Bounded acquisition, strict normalization, and content-based routing |
| `Refresh docs/product/briefs/example.md from its registered Linear source.` | Field-level comparison under lifecycle and source authority |

### 1. Acquire and route

- **You provide:** the Linear work or selection.
- **Agent does:** validates the fixed API destination before credentials,
  acquires bounded content, and delegates normalized data to `work-intake`.
- **You decide:** resolve any coherence, evidence, or confidentiality gap.
- **Output:** artifact path and kind, membership, processor, authority,
  dispatchability, and next action.
- **State:** read-only

### 2. Materialize repository work

- **Agent does:** writes the selected canonical artifact before its workspace
  entry and dispatches only after both are durable.
- **You decide:** continue with the named processor or stop with a Draft.
- **Output:** registered repo-local work. Linear remains unchanged.
- **State:** confirmed-write

### 3. Refresh or coordinate later

- **You provide:** the registered tracker-origin artifact to compare.
- **Agent does:** applies lifecycle locks and presents authorized local field
  decisions. Remote coordination remains a separate confirmation.
- **You decide:** approve local fields, then confirm one exact remote action.
- **Output:** reviewed local authority state and, when confirmed, one declared
  Linear coordination result.
- **State:** confirmed-write
