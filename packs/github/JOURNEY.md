---
journey_id: github
pack: github
start_state: read-only
end_state: confirmed-write
scope: user
tagline: "GitHub source → canonical repository work."
contract:
  useItWhen: "You want to start repository work from a GitHub Issue, Milestone, or selection, compare an existing tracker-origin artifact, or review, iterate on, or adopt a pull request."
  youType: "Start repository work from GitHub Milestone 12."
  youProvide: "A trusted configured repository plus an Issue, Milestone, selection, registered artifact path, or open pull request number."
  youReceive: "A bounded content-based route, a field-level refresh delta, a pull-request review draft, a per-item feedback plan, or an adoption contract, with an exact preview before any supported write."
  yourDecisions:
    - "Resolve any route or confidentiality gap"
    - "Approve each local refresh field decision"
    - "Confirm one exact GitHub coordination action, or approve the pull-request actions or adoption contract"
  decisionGateIds:
    - review-github-route
    - confirm-github-action
skills:
  - name: github-brief-intake
    description: "Acquires bounded Issue or Milestone data through fixed-host approved gh reads and delegates strict normalized content to work-intake."
    humanTouches: 1
  - name: github-refresh
    description: "Compares a registered tracker-origin artifact and performs only profile-declared coordination actions after exact confirmation."
    humanTouches: 1
  - name: github-pr
    description: "Reviews a pull request into a pending review, iterates on feedback and checks on yours, or adopts a contributor's pull request under one approved contract, acting only after approval."
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
    trigger: "After the exact action, target, and payload digest are shown, or the pull-request draft, plan, or adoption contract is shown"
    duration: "1–2 minutes"
    whatToCheck:
      - "Is the target the registered Issue?"
      - "Is this only a declared coordination action, not a requirement rewrite?"
      - "For a pull request, are the commit, reply text, review comments, and any merge terms exactly what you want?"
    whatGoodLooksLike: "One trace link, pull-request link, display-status label, comment, or closure bound to a fresh confirmation."
    whatBadLooksLike: "A generic update, Issue-body rewrite, or reused confirmation."
    consequence: "The wrong remote Issue may be changed and automatic retry is unavailable."
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
| `Review PR 42.` | Read-only draft review, then a pending review you submit |
| `Address the review feedback on PR 42.` | Read-only plan with merit judgments, then fixes, replies, and resolutions you approve |
| `Adopt PR 42 and carry it to merge.` | Evaluation, then one adoption contract; fixes, push, and merge only inside it |

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

### 4. Work through a pull request

- **You provide:** a pull request number and the job: review it, address
  feedback on it, or adopt it.
- **Agent does:** reads the pull request on github.com and shows what it
  would do: a draft review, a per-item feedback plan, or an adoption contract.
  PR-authored code runs only through a sandbox command you name.
- **You decide:** approve the exact actions, or the one adoption contract.
  Nothing is pushed, posted, or merged without that approval.
- **Output:** a pending review you submit, a new commit with approved replies
  and resolved threads, or an adopted pull request merged under the contract.
- **State:** confirmed-write
