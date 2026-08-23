---
journey_id: core
pack: core
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: "Spec → shipped code. Supervised."
prerequisitePacks: []
contract:
  useItWhen: "You're implementing a feature, fixing a bug, or changing an existing repo."
  youProvide: "The task and its important constraints."
  youReceive: "An agreed plan, a checked implementation, review findings, and a merge decision."
  yourDecisions:
    - "Approve the plan"
    - "Approve each local refresh field decision"
    - "Confirm every remote tracker mutation separately"
    - "Merge the PR"
  decisionGateIds:
    - approve-plan
    - merge-reviewed-change
whatChanges: "After installing core, work-intake becomes the front door for starting, remembering, inspecting, or refreshing work. It writes a canonical artifact and lifecycle entry before any processor runs. Approved specs then move through work-loop: plan → execute → verify → independently grounded review. Stable brief/spec/plan authoring gates may capture reusable supporting practice through project-knowledge; review planning may separately enquire once for untrusted candidate checks, while Draft work, reviewer scratch, findings, and normative artifact content remain untouched. The loop cannot self-certify: it surfaces to you for plan approval and merge."
skills:
  - name: work-intake
    description: "Routes start, remember, status, and refresh requests into canonical artifacts and workspace lifecycle state before dispatch."
    humanTouches: 0
  - name: work-loop
    description: "The build loop. Plans, executes, verifies, and reviews; spec-approved and plan-locked may capture reusable supporting practice, while one bounded CQ-REVIEW enquiry may inform candidate checks without changing reviewer authority."
    humanTouches: 2
  - name: new-spec
    description: "Authors a Draft spec and Drafting plan before the build loop starts. These are explicit project-knowledge non-gates."
    humanTouches: 1
  - name: bug-fix
    description: "Diagnoses and fixes a bug with a targeted root-cause analysis before writing a line of code."
    humanTouches: 1
  - name: contract-acquisition
    description: "Grounds agent code against an unfamiliar API or library contract before implementation — prevents guessed signatures."
    humanTouches: 0
  - name: receive-brief
    description: "Receives and decomposes a structured brief; after the brief-ready gate it may capture reusable supporting practice through the public project-knowledge seam."
    humanTouches: 1
  - name: init-project
    description: "Initializes a new project with the full agent-ready-repo structure, conventions, and AGENTS.md."
    humanTouches: 1
  - name: adapt-to-project
    description: "Adapts the agent-ready-repo conventions to an existing project's idioms and structure — the on-ramp for brownfield repos."
    humanTouches: 1
  - name: author-brief
    description: "Materializes a coherent multi-feature outcome as a registered Draft brief. Draft completion is an explicit project-knowledge non-gate."
    humanTouches: 1
  - name: capture-work
    description: "Compatibility alias that forwards equivalent requests to work-intake; new guidance uses work-intake directly."
    humanTouches: 0
  - name: workspace-status
    description: "Reads workspace.toml and surfaces ready-to-start items, blocked items, parallel candidates, and active signals — the cold-start orient for every session."
    humanTouches: 0
  - name: project-knowledge
    description: "Captures, distills, and enquires over committed project knowledge through one progressive skill. Capture writes observations; distill proposes topic changes; enquire reads active committed topics."
    humanTouches: 0
  - name: operational-safety
    description: "Provides failure-mode-keyed operational safety checklists for the work-loop's quality-engineer reviewer. Loaded selectively for infra and destructive work — not invoked directly."
    humanTouches: 0
  - name: security-checklists
    description: "Provides boundary-keyed security checklists for the security-reviewer. The work-loop loads only the boundary-matching modules — not invoked directly."
    humanTouches: 0
  - name: security-checklists-reference
    description: "Provides a read-only reference view of the security checklist library. Normal security reviews use security-checklists."
    humanTouches: 0
humanGates:
  - id: approve-plan
    globalGate: null
    label: "Approve the plan"
    trigger: "Before work-loop begins execution — after the agent writes the trio and risk-trigger assessment"
    duration: "5–10 minutes"
    whatToCheck:
      - "Is the Trio complete? (problem, user, success criteria — each in one sentence)"
      - "Do the stated risk triggers match the actual change? (a one-file auth change is full-mode; a familiar two-file change can be light)"
      - "Is the plan scoped to what was asked — nothing more?"
      - "Are the assumption surfacings plausible, not defensive?"
    whatGoodLooksLike: "A bounded plan with a clear trio, no scope creep, correct risk-trigger assessment, and plausible assumptions."
    whatBadLooksLike: "A plan that extends the scope of the request, missing risk triggers that should have fired, or a trio that doesn't name a specific user."
    consequence: "If you approve a bad plan, the agent executes it faithfully. The cost of a bad plan is the cost of a full loop iteration — plan approval is the cheapest gate."
  - id: merge-reviewed-change
    globalGate: "G4"
    label: "Merge the reviewed change"
    trigger: "After all mechanical gates pass and adversarial review is clean"
    duration: "10–20 minutes"
    whatToCheck:
      - "Is adversarial review marked clean? (Re-run if in doubt — it's fast.)"
      - "Does the implementation match the spec? If not, did the spec update?"
      - "Are the tests testing behavior, not implementation details?"
      - "Is there anything in the diff that wasn't in the plan?"
    whatGoodLooksLike: "Green gates, clean adversarial review, spec and implementation aligned, no unexplained diff."
    whatBadLooksLike: "Adversarial reviewer flagged a Blocker and you merged anyway. Or the spec drifted from the implementation without an update."
    consequence: "This is the last line of defense before the build loop output goes to release. A bad merge is harder to undo than a bad plan."
typicalSession:
  agentTurns: "8–12"
  humanTouches: 2
  wallClockMinutes: "25–45"
docsUrl: /docs/guides/core/
packUrl: /packs/core/
relatedJourneys:
  - release-engineering
eyebrow: "From scoped work to a reviewed merge"
goodOutputDescription: |-
  **You:** Start work on adding export filters without changing the existing
  API route.
  **Agent:** I routed this to the approved spec. The plan changes the query
  contract, handler, and emitted API tests. It adds no dependency or
  migration.
  **You:** Approve the plan.
  **Agent:** Implemented. Focused tests, type checking, lint, and the full suite
  pass. The emitted contract exposes filters and preserves existing defaults.
  **Independent reviewer:** Clean — ready to commit.
  **Agent:** The reviewed change is ready for your merge decision.
---

| Say this | What happens |
|----------|-------------|
| `work-intake` | Route a start, remember, status, or refresh request into durable state |
| `workspace-status` | Orient — what's ready, blocked, and done |
| `work-loop` | Plan → execute → gates → bounded evidence-assisted review → merge |
| `bug-fix` | Diagnose and fix a specific bug |
| `new-spec` | Author a spec directly, without the brief layer |
| `project-knowledge` | Capture, distill, and explicitly enquire over committed project lessons |

---

### 1. Orient — every session

Type `workspace-status` to see what's ready to start, what's blocked, and what shipped last session.

```text
● sprint-8/data-export     ready    spec approved · 3 tasks
⚠ sprint-8/auth-refresh    blocked  needs spec/api-contract
✓ sprint-7/payment-ui      done     shipped 2026-07-25
```

- **Output:** queue state — ready items, blocked items with reason, recent completions.
- **State:** read-only

---

### 2. Route the work

Describe the work to `work-intake`. The agent selects one artifact route from
the content, writes the artifact, then registers its lifecycle state. A
multi-feature outcome becomes a Draft brief; one independently shippable change
continues to `new-spec`; an opportunity can remain a non-dispatchable intent.

```text
  artifact    docs/product/briefs/data-export.md
  membership  draft · non-dispatchable
  processor   author-brief
```

- **Output:** `docs/product/briefs/data-export.md` — review the brief before it enters the work loop.
- **State:** draft

#### Optional return path — refresh tracked work

For an existing tracker-origin artifact, ask `work-intake` to compare the
registered source revision. You receive a field-level delta before anything
changes. Approve each local decision; if you later request a tracker comment,
trace link, pull-request link, display-status change, or closure, confirm that
one remote mutation separately.

- **You decide:** each local field outcome, then each exact remote mutation.
- **Output:** updated local authority and revision mirror, plus a pending,
  failed, or succeeded receipt for any confirmed remote action.
- **State:** confirmed-write

---

### 3. Make one slice ready

Run `receive-brief docs/product/briefs/data-export.md`. After the brief passes
its Ready gate, choose one independently shippable slice. `new-spec` writes its
Approved spec and sibling plan; the brief itself never enters `work-loop`.

```text
brief: Ready
slice: streaming-csv-export
  spec  docs/specs/data-export/spec.md
  plan  docs/specs/data-export/plan.md

  Problem  Streaming export crashes above 50k rows.
  User     Engineer shipping the bulk-export feature.
  Success  1M rows under 2 GB peak RSS.

  Assumption: streaming CSV is acceptable; XLSX is deferred.

approved: spec and plan
```

- **You decide:** approve the brief, slice, spec, and plan before implementation.
- **Output:** `docs/specs/data-export/spec.md` + `plan.md` — the executable contract and plan.
- **State:** confirmed-write

---

### 4. Execute

Type `work-loop docs/specs/data-export/spec.md`. The agent implements, runs lint / typecheck / tests after each logical change, and hands the diff to `adversarial-reviewer` in a fresh session.

```text
  ● Lint          ok
  ● Typecheck     ok
  ● Tests  246/246 ok
  ● Review        1 blocker → fixed → clean
```

- **Output:** code and tests across multiple files — too many to enumerate individually. Review the PR diff.
- **State:** draft

---

### 5. Merge

The agent opens the PR. Read the description before the diff — it tells you what the agent decided when it had choices, and what was deferred.

- **You decide:** merge, redirect, or defer.
- **Output:** a merged change.
- **State:** confirmed-write

---

### 6. Preserve reusable lessons

At semantic gates, the workflow may hand one strict observation to `project-knowledge --capture`. That journal event is durable and pending, but it is not a query source. Later `--distill` runs reconcile pending observations into reviewed topic proposals, route them to stronger artifacts, or record bounded terminal dispositions.

Use `project-knowledge --enquire` only when you need a declared competency question answered from committed active topics. Enquiry reads one committed Git snapshot, verifies freshness sources for consequential use, and returns bounded evidence with a receipt. It does not read scratch, pending journals, legacy rows, or working-tree-only topics, and retrieved text cannot approve changes, select tools, widen scope, or become evidence by writing itself back.

During review planning, `work-loop` can declare one consequential `CQ-REVIEW`
question after fixing the target and structural scope. Adversarial, security,
and quality reviewers share the same untrusted envelope, derive findings
independently, and keep all scratch, findings, severities, and verdicts outside
project knowledge. Missing knowledge is a named no-write skip.

Scratch before capture can be lost if the workflow or worktree disappears. Retention and compaction are intentionally deferred to a future whole-partition policy; this slice has no per-event deletion path.

- **Output:** committed topic evidence and receipts for explicit competency questions.
- **State:** read-only

---

### Autonomous dispatch

For control-harness use — sessions driven programmatically without a human watching each turn — the two human touches collapse to gate responses via ACP. The harness calls `workspace_status()` to read the queue, dispatches an item, then waits for an `elicitation/create` request that arrives when the work-loop reaches a gate — routes the gate question to a human channel, and responds to the pending ACP elicitation request with the human's answer to unblock the gate.

The work-loop runs the same gates; the harness is what answers them instead of a person at a keyboard.

→ [Run a headless session with workspace-mcp](../../docs/guides/core/how-to/run-headless-session/)
