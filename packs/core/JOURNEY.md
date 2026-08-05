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
    - "Merge the PR"
whatChanges: "After installing core, every coding task in your repo runs through work-loop: plan → execute → verify → adversarial review. Lint, typecheck, and tests are mechanical gates the loop runs before you see the diff. The adversarial reviewer reads the diff cold — no context from the build session. The loop cannot self-certify: it always surfaces to you for plan approval and PR merge. For HTML/CSS/JS work, install the frontend-engineering pack to unlock craft rules, WCAG 2.2 AA guidance, and the evidence manifest."
skills:
  - name: work-loop
    description: "The build loop. Plans, executes, verifies, and reviews — mechanical gates and human checkpoints the agent cannot bypass."
    humanTouches: 2
  - name: new-spec
    description: "Authors a spec document before the build loop starts. Captures the trio (problem, user, success criteria) and acceptance criteria."
    humanTouches: 1
  - name: bug-fix
    description: "Diagnoses and fixes a bug with a targeted root-cause analysis before writing a line of code."
    humanTouches: 1
  - name: contract-acquisition
    description: "Grounds agent code against an unfamiliar API or library contract before implementation — prevents guessed signatures."
    humanTouches: 0
  - name: receive-brief
    description: "Receives a structured brief from an external source and grounds it against the project scope and conventions before implementation begins."
    humanTouches: 1
  - name: init-project
    description: "Initializes a new project with the full agent-ready-repo structure, conventions, and AGENTS.md."
    humanTouches: 1
  - name: adapt-to-project
    description: "Adapts the agent-ready-repo conventions to an existing project's idioms and structure — the on-ramp for brownfield repos."
    humanTouches: 1
  - name: author-brief
    description: "Converts unstructured external input (email threads, prose, Linear issues) into a DoR-compliant product brief and queues it in workspace.toml."
    humanTouches: 1
  - name: capture-work
    description: "Captures follow-ons, deferred scope, and audit items surfaced in a session into workspace.toml so later sessions can pick them up cold."
    humanTouches: 1
  - name: workspace-status
    description: "Reads workspace.toml and surfaces ready-to-start items, blocked items, parallel candidates, and active signals — the cold-start orient for every session."
    humanTouches: 0
  - name: operational-safety
    description: "Provides failure-mode-keyed operational safety checklists for the work-loop's quality-engineer reviewer. Loaded selectively for infra and destructive work — not invoked directly."
    humanTouches: 0
  - name: security-checklists
    description: "Provides boundary-keyed security checklists for the security-reviewer. The work-loop loads only the boundary-matching modules — not invoked directly."
    humanTouches: 0
humanGates:
  - id: G-plan
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
  - id: G-pr
    globalGate: "G4"
    label: "Merge the PR"
    trigger: "After all mechanical gates pass and adversarial review is clean"
    duration: "10–20 minutes"
    whatToCheck:
      - "Is adversarial review marked clean? (Re-run if in doubt — it's fast.)"
      - "Does the implementation match the spec? If not, did the spec update?"
      - "Are the tests testing behavior, not implementation details?"
      - "Is there anything in the diff that wasn't in the plan?"
    whatGoodLooksLike: "Green gates, clean adversarial review, spec and implementation aligned, no unexplained diff."
    whatBadLooksLike: "Adversarial reviewer flagged a Blocker and you merged anyway. Or the spec drifted from the implementation without an update."
    consequence: "G4 is the last line of defense before the build loop output goes to release. A bad merge is harder to undo than a bad plan."
typicalSession:
  agentTurns: "8–12"
  humanTouches: 2
  wallClockMinutes: "25–45"
docsUrl: /guides/core/
packUrl: /packs/core/
relatedJourneys:
  - release-engineering
---

| Say this | What happens |
|----------|-------------|
| `workspace-status` | Orient — what's ready, blocked, and done |
| `author-brief` | Turn any idea, email, or issue into a queued brief |
| `work-loop` | Plan → execute → gates → adversarial review → merge |
| `bug-fix` | Diagnose and fix a specific bug |
| `new-spec` | Author a spec directly, without the brief layer |

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

### 2. Author a brief

Type `author-brief` and paste any unstructured input — an idea, email thread, or issue. The agent extracts the outcome, appetite, and key constraints, then queues the brief in `workspace.toml`.

```text
  brief   docs/product/briefs/data-export.md
  queued  sprint-8/data-export → ready
```

- **Output:** `docs/product/briefs/data-export.md` — review the brief before it enters the work loop.
- **State:** draft

---

### 3. Agree the plan

Type `work-loop docs/product/briefs/data-export.md`. The agent checks risk triggers, writes the spec and plan, surfaces assumptions, and stops for your sign-off before a line of code is written.

```text
mode: full — new dependency trigger
  spec  docs/specs/data-export/spec.md
  plan  docs/specs/data-export/plan.md

  Problem  Streaming export crashes above 50k rows.
  User     Engineer shipping the bulk-export feature.
  Success  1M rows under 2 GB peak RSS.

  Assumption: streaming CSV is acceptable; XLSX is deferred.

Approve? ›
```

- **You decide:** approve spec and plan — 5–10 minutes, the cheapest gate.
- **Output:** `docs/specs/data-export/spec.md` + `plan.md` — your checkpoint before any code is written.
- **State:** draft

---

### 4. Execute

Type `work-loop execute spec/data-export`. The agent implements, runs lint / typecheck / tests after each logical change, and hands the diff to `adversarial-reviewer` in a fresh session.

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

### Autonomous dispatch

For control-harness use — sessions driven programmatically without a human watching each turn — the two human touches collapse to gate responses via ACP. The harness calls `workspace_status()` to read the queue, dispatches an item, polls for `gate_pending`, routes the gate question to a human channel, and responds to the pending ACP elicitation request with the human's answer to unblock the gate.

The work-loop runs the same gates; the harness is what answers them instead of a person at a keyboard.

→ [Run a headless session](../../docs/guides/core/how-to/run-headless-session/)
