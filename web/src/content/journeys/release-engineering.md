---
generated: true
journey_id: release-engineering
pack: release-engineering
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: "Deploy. Verify. Converge. Then ship."
prerequisitePacks:
  - core
contract:
  useItWhen: "Existing CI, human or workflow evidence is ready for release preparation."
  youType: "Prepare a release handoff from existing evidence, admit the candidate and run the release loop."
  youProvide: "Existing build, check and provenance evidence, an explicit target and caller-selected trusted policy."
  youReceive: "A release readiness record — e2e results, telemetry snapshot, security review — and, once you ratify, a ship decision for you or your deploy pipeline to carry out."
  yourDecisions:
    - "Approve the prod ship"
  decisionGateIds:
    - approve-production-release
whatChanges: "After installing release-engineering, existing evidence goes through collection, admission and focused release review before release stages. The release-lead agent deploys to an ephemeral environment, runs e2e tests, observes telemetry, and feeds deployed findings back to the inner loop — no human relay. You review at one gate: the prod ship."
skills:
  - name: prepare-release-handoff
    description: "Collects existing evidence into a validated candidate or reports named gaps; runs no missing work."
    humanTouches: 0
  - name: release-loop
    description: "The release supervisor. Deploys to ephemeral env, runs e2e, feeds findings back to the inner loop, iterates to convergence, then surfaces for prod ship approval."
    humanTouches: 1
  - name: define-slo
    description: "Authors an OpenSLO v1 YAML document for a service. Produces the SLO artifact the release-loop PRR gate reads to populate the error-budget status field."
    humanTouches: 0
humanGates:
  - id: approve-production-release
    globalGate: "G5"
    label: "Approve the production release"
    trigger: "After the deployed whole converges — e2e clean, telemetry stable, security review done"
    duration: "15–30 minutes"
    whatToCheck:
      - "Is the release readiness record complete? (e2e results, telemetry snapshot, security review)"
      - "Are there any borderline gates in the record? (The agent surfaces these — don't skip them.)"
      - "Is there anything in the diff that wasn't in the scope of this release?"
      - "Is the rollback path documented and tested?"
    whatGoodLooksLike: "A release readiness record showing convergence — e2e clean, telemetry stable, security reviewer clean, no borderline gates."
    whatBadLooksLike: "A record that notes borderline gates you wave through. Or a record that omits the security diff review."
    consequence: "This gates the production release. The agent stops at the ratified record and does not ship; you or your deploy pipeline roll out to production, and after that the change reaches real users or real data — irreversible."
typicalSession:
  agentTurns: "varies"
  humanTouches: 1
  wallClockMinutes: "15–30"
docsUrl: /docs/guides/release-engineering/
packUrl: /packs/release-engineering/
relatedJourneys:
  - core
eyebrow: "From a clean build to a verified production release"
goodOutputDescription: |-
  **You:** Use `release-loop` for the merged export-filter change. Deploy it to
  an isolated ephemeral environment, converge on end-to-end results and
  telemetry, then prepare the release-readiness record. Do not deploy to
  production without my approval.
  **Agent:** The target is the merged, independently reviewed change. The
  environment is isolated from production data and traffic, and teardown is
  available. Starting the ephemeral deployment.
  **Agent:** First iteration: the empty-result export flow failed end to end.
  Other checks and telemetry remained stable. I returned the defect to the
  inner loop, verified the reviewed fix, and redeployed.
  **Agent:** Second iteration: all release end-to-end checks pass; latency and
  errors remain within the recorded service objectives; the deployed-diff
  security review is clean; and the rollback rehearsal passes. The
  release-readiness record links the evidence. Borderline gates: none.
  Production remains unchanged.
  **You:** Approve the production release.
---

### 1. Collect, admit and review

- **You do:** provide existing CI, human or workflow evidence, the protected root, trusted policy and expected target.
- **Agent does:** runs `prepare-release-handoff`, reports `ready` or exact gaps, then independently admits the candidate. Both focused reliability and security reviewers must pass before the pre-deploy stage check.
- **You get:** a fresh candidate and admission record, or a refusal naming what must be fixed. No build, test, plan, deploy or fetch runs during collection or admission.
- **Decision:** resolve gaps with the named owner; confirm separate execution authority before deployment.
- **State:** read-only

---

### 2. Validate and converge

- **Loop does:** within the agreed authority and budget, deploys to the temporary environment, gathers fresh runtime evidence and checks both post-deploy reviews. A failed check routes a bounded repair handoff to the recorded owner. Replacement candidates re-enter collection, admission and review with the attempt count carried forward.
- **You do:** check in at the end of each outer loop iteration — skim the e2e results and telemetry snapshot; flag anomalies the agent might not catch (an assertion too weak to detect a real failure, a telemetry spike marked as noise); provide judgment on what "stable" means for your service.
- **Output:** a converged deployed state — e2e clean, telemetry stable.
- **State:** read-only

---

### 3. Ratify the release readiness record

- **Agent does:** checks final prerequisites: passing pre-deploy and post-deploy review pairs, budgets, cleanup and remaining risks. The result is `human-decision-required`. Collector readiness, admission, review pass and stage progression grant no execution or production authority.
- **You do:** read the full release readiness record, not just the summary; the borderline gates section matters most — these are the agent's "close enough" calls you may decide differently.
- **You decide:** approve the prod ship — ratify if satisfied, or reject with a one-line reason to re-enter the loop.
- **Output:** a prod-ship decision; after this gate the change reaches real users or real data.
- **State:** confirmed-write

See [Release admission](../../guides/release-engineering/reference/release-admission.md) for commands, refusal codes and the stage table. Core reviewers are optional additions after the required local checks; their refusal stops the step without a weaker fallback. Installation still requires Core.
