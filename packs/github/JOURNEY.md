---
journey_id: github
pack: github
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "GitHub source → canonical repository work."
contract:
  useItWhen: "You want to start repository work from a GitHub Issue, Milestone, or selection, compare an existing tracker-origin artifact, or work through review feedback on an open pull request."
  youType: "Start repository work from GitHub Milestone 12."
  youProvide: "A trusted configured repository plus an Issue, Milestone, selection, registered artifact path, or open pull request number."
  youReceive: "A bounded content-based route, a field-level refresh delta, or a per-item pull-request feedback plan, with an exact preview before any supported write."
  yourDecisions:
    - "Resolve any route or confidentiality gap"
    - "Approve each local refresh field decision"
    - "Confirm one exact GitHub coordination action"
    - "Approve the pull-request feedback plan"
  decisionGateIds:
    - review-github-route
    - confirm-github-action
    - approve-pr-iteration-plan
skills:
  - name: github-brief-intake
    description: "Acquires bounded Issue or Milestone data through fixed-host approved gh reads and delegates strict normalized content to work-intake."
    humanTouches: 1
  - name: github-refresh
    description: "Compares a registered tracker-origin artifact and performs only profile-declared coordination actions after exact confirmation."
    humanTouches: 1
  - name: github-pr-iterate
    description: "Reads an open pull request's review threads and checks, judges each item, and applies fixes, replies, and resolutions only after plan approval."
    humanTouches: 1
humanGates:
  - id: review-github-route
    globalGate: null
    label: "Review the repository route"
    trigger: "After intake returns an artifact, lifecycle membership, processor, authority mode, and named gaps"
    duration: "1–5 minutes"
    whatToCheck:
      - "Does the content support this artifact rather than relying on Issue or Milestone type?"
      - "Is the destination repository and confidentiality boundary correct?"
    whatGoodLooksLike: "One coherent route, or an explicit non-dispatchable gap when the selection is not coherent."
    whatBadLooksLike: "A Milestone forced into a brief or an Issue forced into a spec because of its object name."
    consequence: "A wrong route creates the wrong durable artifact before delivery begins."
  - id: confirm-github-action
    globalGate: null
    label: "Confirm one GitHub coordination action"
    trigger: "After the exact action, target, and payload digest are shown"
    duration: "1–2 minutes"
    whatToCheck:
      - "Is the target the registered Issue?"
      - "Is this only a declared coordination action, not a requirement rewrite?"
    whatGoodLooksLike: "One trace link, pull-request link, display-status label, comment, or closure bound to a fresh confirmation."
    whatBadLooksLike: "A generic update, Issue-body rewrite, or reused confirmation."
    consequence: "The wrong remote Issue may be changed and automatic retry is unavailable."
  - id: approve-pr-iteration-plan
    globalGate: null
    label: "Approve the pull-request feedback plan"
    trigger: "After the agent shows each feedback item with its merit judgment, options, and exact reply text"
    duration: "2–10 minutes"
    whatToCheck:
      - "Is each comment judged on its merits rather than applied blindly?"
      - "Are the commit, reply text, and threads to resolve exactly what you want?"
    whatGoodLooksLike: "Per-item choices named by id, with push-back and deferred items left for the reviewer."
    whatBadLooksLike: "A blanket approval of items you did not read."
    consequence: "A pushed commit, a posted reply, or a resolved thread cannot be undone by the agent."
typicalSession:
  agentTurns: "3–6"
  humanTouches: 1
  wallClockMinutes: "5–15"
docsUrl: /docs/guides/github/
packUrl: /packs/github/
---

| Say this | What happens |
| --- | --- |
| `Intake GitHub issue 123 as repository work. Start read-only.` | Bounded acquisition, strict normalization, and content-based routing |
| `Refresh docs/specs/example/spec.md from its registered GitHub source.` | Field-level comparison under the artifact's lifecycle and authority |
| `Address the review feedback on PR 42.` | Read-only plan with merit judgments, then fixes, replies, and resolutions you approve |

### 1. Acquire and route

- **You provide:** the Issue, Milestone, or explicit selection.
- **Agent does:** runs fixed-host approved `gh` reads, validates provenance, and
  delegates normalized content to `work-intake`.
- **You decide:** resolve any coherence, evidence, or confidentiality gap.
- **Output:** artifact path and kind, lifecycle membership, processor,
  authority mode, dispatchability, and one next action.
- **State:** read-only

### 2. Materialize repository work

- **Agent does:** `work-intake` writes the selected canonical artifact, then
  registers it before processor dispatch.
- **You decide:** continue with the named processor or stop with a Draft.
- **Output:** durable repo-local work. GitHub remains unchanged.
- **State:** confirmed-write

### 3. Refresh or coordinate later

- **You provide:** the existing registered tracker-origin artifact to compare.
- **Agent does:** presents field decisions. A remote coordination action is a
  separate request with a fresh confirmation and pending receipt.
- **You decide:** approve local fields, then confirm one exact remote action.
- **Output:** reviewed local authority state and, when confirmed, one bounded
  GitHub coordination result.
- **State:** confirmed-write

### 4. Iterate on a pull request

- **You provide:** an open pull request number.
- **Agent does:** reads the review threads and checks, judges each item, and
  shows a per-item plan with options and exact reply text.
- **You decide:** which items to apply, answer, defer, or push back on.
- **Output:** one new commit on the pull request branch, the approved replies,
  and resolved threads for fixes that landed.
- **State:** confirmed-write
