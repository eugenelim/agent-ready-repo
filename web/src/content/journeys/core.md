---
pack: core
scope: repo
tagline: "Spec → shipped code. Supervised."
prerequisitePacks: []
whatChanges: "After installing core, every coding task in your repo runs through work-loop: plan → execute → verify → adversarial review. You get lint, typecheck, and tests as mechanical gates. Three specialist reviewers read every diff cold. The loop cannot self-certify — it always surfaces to you for plan approval and PR merge."
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
  - name: frontend-engineering
    description: "Establishes design intent and craft rules before writing HTML/CSS — pre-flight before any frontend surface change."
    humanTouches: 0
  - name: contract-acquisition
    description: "Grounds agent code against an unfamiliar API or library contract before implementation — prevents guessed signatures."
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
docsUrl: /docs/guides/core/
packUrl: /packs/core/
relatedJourneys:
  - release
---

## Stage 1 — Brief the loop

You opened a task and described it to your agent. The agent activated `work-loop`, checked whether risk triggers required full mode, wrote the lean inline spec (trio: problem, user, success criteria), identified risk triggers, and surfaced assumptions.

**You did:** Read the trio in the chat. Confirmed the scope matched what you asked for — or redirected if the agent overreached. Checked that the correct mode (light or full) was selected. Approved the plan. 5–10 minutes of focused reading; this is the gate that costs least and protects most.

---

## Stage 2 — Execution

After your plan approval, the agent implemented against the spec. It ran lint, typecheck, and tests after each logical change. When a gate failed, it fixed the issue and re-ran the gate before continuing.

**You did:** Watched the chat at key moments — after each logical task completes, skim the agent's output to catch early drift. You do not need to read every line; look for file names you didn't expect, for scope creep, and for the agent surfacing a question. If it surfaces, answer quickly — a blocked agent costs more time than a fast redirect. If all is well, let it run.

---

## Stage 3 — Specialist review

After all mechanical gates passed, the agent ran `adversarial-reviewer` in a fresh session. The reviewer read the diff cold — no context from the build session. It returned findings grouped by severity (Blockers, Concerns, Nits). The loop iterated on Blockers until the reviewer reported clean.

**You did:** Monitored the review output as it landed. If the reviewer flagged a Blocker you disagreed with, provide a brief direction to the agent ("this is expected behavior because…") so the next fix targets the real issue. For Concerns and Nits, scan them — you may choose to apply or defer without waiting for the loop to finish.

---

## Stage 4 — PR and merge

After all reviewers reported clean, the agent opened the PR with a description including: what changed, why, what was deferred, and what was found mid-implementation.

**You did:** Reviewed the PR diff in GitHub or your editor. Read the description, not just the diff — the description tells you what the agent decided when it had choices. Checked that the spec and implementation aligned. Looked for anything in the diff that wasn't in the plan you approved. Merged when satisfied.
