---
pack: release-engineering
scope: repo
tagline: "Deploy. Verify. Converge. Then ship."
prerequisitePacks:
  - core
contract:
  useItWhen: "A build-loop PR is adversarial-review-clean and ready to go to production."
  youProvide: "A merged, adversarial-review-clean inner build-loop output."
  youReceive: "A release readiness record — e2e results, telemetry snapshot, security review — and a convergence-verified prod ship."
  yourDecisions:
    - "Approve the prod ship"
whatChanges: "After installing release-engineering, completed build-loop output goes through release-loop before reaching production. The release-lead agent deploys to an ephemeral environment, runs e2e tests, observes telemetry, and feeds deployed findings back to the inner loop — no human relay. You review at one gate: the prod ship."
skills:
  - name: release-loop
    description: "The release supervisor. Deploys to ephemeral env, runs e2e, feeds findings back to the inner loop, iterates to convergence, then surfaces for prod ship approval."
    humanTouches: 1
humanGates:
  - id: G5
    globalGate: "G5"
    label: "Approve the prod ship"
    trigger: "After the deployed whole converges — e2e clean, telemetry stable, security review done"
    duration: "15–30 minutes"
    whatToCheck:
      - "Is the release readiness record complete? (e2e results, telemetry snapshot, security review)"
      - "Are there any borderline gates in the record? (The agent surfaces these — don't skip them.)"
      - "Is there anything in the diff that wasn't in the scope of this release?"
      - "Is the rollback path documented and tested?"
    whatGoodLooksLike: "A release readiness record showing convergence — e2e clean, telemetry stable, security reviewer clean, no borderline gates."
    whatBadLooksLike: "A record that notes borderline gates you wave through. Or a record that omits the security diff review."
    consequence: "G5 gates the prod ship. The agent cannot ship to production without your ratification. After this gate, the change reaches real users or real data — irreversible."
typicalSession:
  agentTurns: "varies"
  humanTouches: 1
  wallClockMinutes: "15–30"
docsUrl: /docs/guides/release-engineering/
packUrl: /packs/release-engineering/
relatedJourneys:
  - core
---

## 1. Trigger and confirm the deploy

- **Agent does:** activates release-loop on completion of the inner build loop (work-loop + adversarial review clean); deploys the integrated whole to an ephemeral environment.
- **You do:** watch the initial deploy log to confirm the right branch and config are targeted; if the deploy target looks wrong, stop it early — a mid-cycle redirect costs more than catching it at the first log line.
- **Output:** a running ephemeral deployment.

---

## 2. Validate and converge

- **Loop does:** runs end-to-end tests against the deployed environment, observes telemetry, feeds deployed findings back to the inner loop, redeploys after each inner-loop fix, and iterates until convergence — e2e clean, telemetry stable.
- **You do:** check in at the end of each outer loop iteration — skim the e2e results and telemetry snapshot; flag anomalies the agent might not catch (an assertion too weak to detect a real failure, a telemetry spike marked as noise); provide judgment on what "stable" means for your service.
- **Output:** a converged deployed state — e2e clean, telemetry stable.

---

## 3. Ratify the release readiness record

- **Agent does:** generates the release readiness record — e2e results, telemetry snapshot, security review on the deployed diff, deferred items, and any borderline gates.
- **You do:** read the full release readiness record, not just the summary; the borderline gates section matters most — these are the agent's "close enough" calls you may decide differently.
- **You decide:** approve the prod ship — ratify if satisfied, or reject with a one-line reason to re-enter the loop.
- **Output:** a prod-ship decision; after this gate the change reaches real users or real data.
