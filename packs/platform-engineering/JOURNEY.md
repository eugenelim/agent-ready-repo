---
journey_id: platform-engineering
pack: platform-engineering
start_state: read-only
end_state: confirmed-write
scope: repo
tagline: "Plan infrastructure. Prepare releases. Verify deployment."
prerequisitePacks: []
contract:
  useItWhen: "You need governed Terraform authoring, drift review or release preparation and protected GitHub Actions execution from existing evidence."
  youType: "Create reviewed Terraform, prepare its release handoff and validate the release in an isolated environment."
  youProvide: "An infrastructure intent or existing release evidence, plus an explicit target, trusted policy and separate execution authority."
  youReceive: "A digest-pinned Terraform plan with policy-pass evidence, security review, reversibility hints, and a release readiness record."
  yourDecisions:
    - "Approve the governance gate"
    - "Approve the inner-loop plan"
    - "Approve the G4 handoff — merge the PR"
    - "Approve the prod ship"
  decisionGateIds:
    - approve-infrastructure-governance
    - approve-infrastructure-plan
    - merge-infrastructure-change
    - approve-production-release
whatChanges: "After installing platform-engineering, generate-iac turns infrastructure intent into a governed, schema-grounded, digest-pinned plan without apply. reconcile-iac audits managed-resource drift. prepare-release-handoff collects existing evidence, and release-loop admits and reviews candidates before protected GitHub Actions execution. define-slo supplies service objectives. Release-only work needs no Terraform tooling; production always needs your decision."
skills:
  - name: generate-iac
    description: "Turns a plain-language intent into governed, schema-grounded Terraform — ADR-gated, vocabulary-firewalled, and stopping at a digest-pinnable plan for a reviewed handoff."
    humanTouches: 3
  - name: reconcile-iac
    description: "Audits plan-visible drift between Terraform state and the live control plane, proposes a disposition per drifted resource, and routes remediation for human approval — never autonomously applies."
    humanTouches: 1
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
  - id: approve-infrastructure-governance
    globalGate: null
    label: "Approve the infrastructure governance"
    trigger: "Before any Terraform is authored — after the agent checks the governance summary and identifies the sources that bind the intent"
    duration: "5–15 minutes"
    whatToCheck:
      - "Does check-summary return ready for the governing instructions, accepted decisions and explicit inputs?"
      - "Are the ADRs the agent identified the right ones for this decision domain?"
      - "Are there unresolved decision domains? Resolve them with the owner and record explicit inputs before proceeding."
      - "Is the intent written in generic terms — no cloud-specific service names in the spec?"
    whatGoodLooksLike: "A ready governance summary, the right sources cited, no uncovered decision domain, and a vocabulary-firewalled spec."
    whatBadLooksLike: "The agent cited an ADR that doesn't cover the decision domain, skipped the summary check, or wrote RDS/S3/GCS into the spec before PLAN."
    consequence: "If you skip or rubber-stamp the governance gate, the generated Terraform will be ungoverned — no decision records binding the choices, no constraint on which cloud services are used, and no way to review the decision retrospectively."
  - id: approve-infrastructure-plan
    globalGate: null
    label: "Approve the infrastructure plan"
    trigger: "After ADR gate passes and inputs are confirmed — before Terraform authoring begins"
    duration: "5–10 minutes"
    whatToCheck:
      - "Are tasks ordered by infrastructure tier (Foundation → Network → Compute/Data → App → Polish)?"
      - "Are parallel tasks ([P]) only on resources with no shared dependency?"
      - "Does the plan cite which ADR and standard each task satisfies?"
      - "Is the account/tenant isolation model documented — shared workspaces vs. separate account per environment?"
    whatGoodLooksLike: "A tier-ordered task list with ADR citations, explicit isolation model, and parallel annotations only where safe."
    whatBadLooksLike: "Tasks in arbitrary order, missing ADR citations, or the account isolation model left undocumented."
    consequence: "A mis-ordered task plan produces apply-time dependency conflicts — the most expensive class of apply-time failure, invisible to plan."
  - id: merge-infrastructure-change
    globalGate: "G4"
    label: "Merge the infrastructure change"
    trigger: "After plan is digest-pinned: fmt clean, validate clean, plan clean, policy-as-code clean, security reviewer clean"
    duration: "15–30 minutes"
    whatToCheck:
      - "Is the plan digest pinned in the PR? (The deploy step applies exactly this plan, nothing else.)"
      - "Did policy-as-code (OPA/Conftest) pass against the plan JSON — no unapproved resource types, required tags present?"
      - "Did the security reviewer find no new misconfigurations (Trivy/Checkov clean)?"
      - "Are reversibility hints correct? (Stateful data stores must be one-way-door, not reversible.)"
      - "If Infracost produced a cost delta, is the projected spend acceptable — or does it require a production spend gate?"
    whatGoodLooksLike: "A digest-pinned plan with policy-pass evidence, security review clean, correct reversibility hints, and an acceptable cost delta."
    whatBadLooksLike: "A plan without a pinned digest — the deploy step could apply a later, unreviewed plan. Or a reversibility hint of reversible on a DynamoDB table or RDS instance."
    consequence: "This is the last gate before deploy. An unpinned plan or missing policy-pass lets an unreviewed change reach a real account. A wrong reversibility hint silences the production spend or data gate."
  - id: approve-production-release
    globalGate: "G5"
    label: "Approve the production release"
    trigger: "After the deployed whole converges — e2e clean, telemetry stable, security review done"
    duration: "15–30 minutes"
    whatToCheck:
      - "Is the release readiness record complete? (e2e results, telemetry snapshot, focused reliability and security records)"
      - "Are there any borderline gates in the record? (The agent surfaces these — don't skip them.)"
      - "Is there anything in the diff that wasn't in the scope of this release?"
      - "Is the rollback path documented and tested?"
    whatGoodLooksLike: "A release readiness record showing convergence — e2e clean, telemetry stable, focused reliability and security records passing, no borderline gates."
    whatBadLooksLike: "A record that notes borderline gates you wave through. Or a record that omits the security diff review."
    consequence: "This gates the production release. The agent stops at the ratified record and does not ship; you or your deploy pipeline roll out to production, and after that the change reaches real users or real data — irreversible."
typicalSession:
  agentTurns: "12–20"
  humanTouches: 3
  wallClockMinutes: "45–90"
docsUrl: /docs/guides/platform-engineering/
packUrl: /packs/platform-engineering/
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

### 0. Gate the governance

- **Agent does:** activates generate-iac, discovers effective repository instructions and decision records, and records constraints with source digests in a governance summary. It runs check-summary and stops on any refusal, conflict or unresolved issue. Optional integrations cannot weaken a result or permit fallback after refusal.
- **You do:** confirm the sources cover the intent and resolve open decisions with the owner. No index, template or bootstrap is required.
- **You decide:** approve the governance gate.
- **Output:** a ready governance summary with binding sources confirmed.
- **State:** read-only

---

### 1. Specify with a vocabulary firewall

- **You provide:** the required infrastructure inputs — target cloud, engine (terraform or opentofu), environments, region, account/tenant isolation model, and CI system.
- **Agent does:** writes the spec in generic infrastructure terms — no cloud-specific service names (no RDS, S3, GCS) before PLAN; records the account isolation model and its consequences for OIDC trust-policy scoping and state backend key structure; proposes the inner-loop plan.
- **You do:** read the spec; confirm the vocabulary firewall held; confirm the account isolation model is correct.
- **You decide:** approve the inner-loop plan.
- **Output:** a vocabulary-firewalled spec with the isolation model recorded, and an agreed plan ready for Terraform authoring.
- **State:** draft

---

### 2. Generate schema-grounded Terraform

- **Agent does:** decomposes the spec into a tier-ordered task list — Foundation (remote state, backend, provider config) → Network → Compute/Data → App → Polish — with ADR citations and parallel annotations only where no shared resource dependency exists; acquires the live provider schema directly (terraform/tofu providers schema -json against the pinned provider version; contract-acquisition is an optional integration) before authoring any resource block.
- **Loop does:** iterates write Terraform → fmt → validate → plan; feeds schema hallucination errors back immediately; does not advance until the plan is clean.
- **You do:** watch the iteration log at key moments; when a validate error surfaces a genuine schema ambiguity (not a hallucination), answer it directly; let the loop run otherwise.
- **Output:** a clean, schema-grounded Terraform plan with fmt, validate, and plan all passing.
- **State:** draft

---

### 3. Run static preflight and prepare the reviewed handoff

- **Agent does:** runs policy-as-code (OPA/Conftest against the plan JSON — approved resource types, required tags, encryption at rest, no hard-coded credentials); runs Infracost for an optional cost delta; pins the plan digest; assembles the reviewed handoff artifact with all evidence.
- **Reviewer does:** follows the canonical infrastructure-review checklist and records evidence for all seven areas. check-review must pass for the exact saved plan and checklist bytes. Core reviewers are optional additions and cannot repair missing coverage or override a blocker.
- **You do:** read the policy-pass evidence and security review summary; check reversibility hints on stateful resources — a wrong hint silences the production spend or data gate; decide whether the cost delta requires a production spend gate.
- **You decide:** merge the infrastructure change.
- **Output:** a digest-pinned reviewed handoff — deploy-ready Terraform, policy-pass evidence, security review summary, reversibility hints on stateful resources, and cost delta if present.
- **State:** confirmed-write

---


### 4. Collect, admit and review

- **You provide:** existing CI, human or workflow evidence, the protected root, trusted policy and expected target.
- **Agent does:** runs `prepare-release-handoff`, reports `ready` or exact gaps, then independently admits the candidate. `release-reliability-reviewer` and `release-security-reviewer` return focused records; both must pass `check-review` before `check-stage` at pre-deploy.
- **You decide:** resolve gaps with the named owner; confirm separate execution authority before deployment.
- **Output:** a fresh candidate and admission record, or a refusal naming what must be fixed. No build, test, plan, deploy or fetch runs during collection or admission.
- **State:** read-only

---

### 5. Validate and converge

- **Loop does:** within the agreed authority and budget, deploys to the temporary environment, gathers fresh runtime evidence and checks both post-deploy review records and their stage prerequisites. A failed check routes a bounded repair handoff to the recorded owner. Replacement candidates re-enter collection, admission and review with the attempt count carried forward.
- **You do:** check in at the end of each outer loop iteration — skim the e2e results and telemetry snapshot; flag anomalies the agent might not catch (an assertion too weak to detect a real failure, a telemetry spike marked as noise); provide judgment on what "stable" means for your service.
- **Output:** a converged deployed state — e2e clean, telemetry stable.
- **State:** read-only

---

### 6. Ratify the release readiness record

- **Agent does:** checks final prerequisites: passing pre-deploy, post-deploy and final review pairs, budgets, cleanup and remaining risks. The focused records must pass `check-review`; `check-stage` returns `human-decision-required`. Collector readiness, admission, review pass and stage progression grant no execution or production authority.
- **You do:** read the full release readiness record, not just the summary; the borderline gates section matters most — these are the agent's "close enough" calls you may decide differently.
- **You decide:** approve the prod ship — ratify if satisfied, or reject with a one-line reason to re-enter the loop.
- **Output:** a prod-ship decision; after this gate the change reaches real users or real data.
- **State:** confirmed-write

---

### 7. Audit and reconcile drift

- **Agent does:** runs reconcile-iac on a weekly schedule, as mandatory preflight before a follow-on change, or immediately after a known out-of-band event; runs terraform plan and produces a drift audit — per-drifted-resource cause class, blast radius against governance standards, and proposed disposition (codify back into IaC, add ignore_changes, open a remediation PR, or block the follow-on change); surfaces that resources created entirely outside Terraform — ClickOps, console actions with no state entry — are invisible to plan and not covered by the audit.
- **You do:** read the drift audit; approve clear dispositions (e.g., ignore_changes for an auto-scaling group self-modification); escalate ambiguous ones that expand permissions or require a new ADR before codifying back; approve the remediation PR.
- **You decide:** approve or escalate each drifted-resource disposition before remediation applies.
- **Output:** approved dispositions per drifted resource and a remediation PR where needed.
- **State:** proposed-write

## Migration

See [the migration how-to](../../docs/guides/platform-engineering/how-to/migrate-from-iac-terraform-and-release-engineering/) for the two-phase move from the retired packs and rollback from a pinned catalogue.
