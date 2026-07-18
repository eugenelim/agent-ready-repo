---
pack: release-engineering
scope: repo
tagline: "Deploy. Verify. Converge. Then ship."
prerequisitePacks:
  - core
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

## Stage 1 — Trigger release loop

A completed inner build loop (work-loop + adversarial review clean) triggers the release loop. The `release-lead` agent activates `release-loop` and deploys the integrated whole to an ephemeral environment.

**You:** Watch the initial deploy log in the chat to confirm the right environment is targeted. You do not intervene in the deploy itself, but reading the first deploy confirms the agent is operating on the right branch and config. If the deploy target looks wrong, stop it early — it's cheaper than a mid-cycle redirect.

---

## Stage 2 — E2E validation and convergence

The agent runs end-to-end tests against the deployed environment, observes telemetry, and feeds deployed findings back to the inner loop — no human relay. It redeploys after each inner-loop fix. It iterates until the deployed whole converges: e2e clean, telemetry stable.

**You:** Check in at the end of each outer loop iteration — after each redeploy, skim the e2e results and the telemetry snapshot. Look for anomalies the agent might not flag: a test that passes but whose assertion is too weak to catch a real failure, or a telemetry spike the agent marked as noise. The agent handles the mechanical convergence; you provide the judgment on what "stable" means for your service.

---

## Stage 3 — Release readiness record

After the deployed whole converges, the agent generates a release readiness record: e2e results, telemetry snapshot, security review on the deployed diff, what was deferred, and any borderline gates.

**You:** At G5, read the full release readiness record — not just the summary. The borderline gates section is the one that matters most: these are cases where the agent decided "close enough" and you may decide differently. Ratify if satisfied. Reject with a one-line reason if not — the agent re-enters the loop. This gate is the only one between the ephemeral environment and production.
