---
pack: iac-terraform
scope: repo
tagline: "Intent → governed Terraform. Stops at plan."
prerequisitePacks:
  - core
  - governance-extras
contract:
  useItWhen: "You're authoring or reconciling governed Terraform infrastructure — from intent to a digest-pinned, policy-clean plan."
  youProvide: "A plain-language infrastructure intent with target cloud, engine, environments, isolation model, and CI system."
  youReceive: "A digest-pinned Terraform plan with policy-pass evidence, security review, reversibility hints, and a release readiness record."
  yourDecisions:
    - "Approve the governance gate"
    - "Approve the inner-loop plan"
    - "Approve the G4 handoff — merge the PR"
    - "Approve the prod ship"
whatChanges: "After installing iac-terraform, a plain-language infrastructure intent moves through a governed authoring loop: a mandatory Stage-0 ADR gate → a vocabulary-firewalled spec → schema-grounded Terraform generation → policy-as-code and security preflight → G4 handoff to release-loop. The pack ships two skills: generate-iac authors the Terraform and stops at a digest-pinnable plan; reconcile-iac audits plan-visible drift and proposes a per-resource disposition without applying autonomously. The agent never runs terraform apply — it produces and pins the plan; release-loop (or the generated human-gated pipeline) routes it to the real account."
skills:
  - name: generate-iac
    description: "Turns a plain-language intent into governed, schema-grounded Terraform — ADR-gated, vocabulary-firewalled, and stopping at a digest-pinnable plan for G4 handoff."
    humanTouches: 3
  - name: reconcile-iac
    description: "Audits plan-visible drift between Terraform state and the live control plane, proposes a disposition per drifted resource, and routes remediation for human approval — never autonomously applies."
    humanTouches: 1
humanGates:
  - id: G-governance
    globalGate: null
    label: "Approve the governance gate"
    trigger: "Before any Terraform is authored — after the agent loads the governance index and identifies which ADRs bind the intent"
    duration: "5–15 minutes"
    whatToCheck:
      - "Does a governance-index.toml exist? If the agent bootstrapped one, is the scaffolded index complete enough to proceed?"
      - "Are the ADRs the agent identified the right ones for this decision domain?"
      - "Are there decision domains not yet covered by an ADR? (Draft one via new-adr or document the assumption before proceeding.)"
      - "Is the intent written in generic terms — no cloud-specific service names in the spec?"
    whatGoodLooksLike: "A governance index loaded, the right ADRs cited, no uncovered decision domain, and a vocabulary-firewalled spec."
    whatBadLooksLike: "The agent cited an ADR that doesn't cover the decision domain, skipped the governance index load, or wrote RDS/S3/GCS into the spec before PLAN."
    consequence: "If you skip or rubber-stamp the governance gate, the generated Terraform will be ungoverned — no decision records binding the choices, no constraint on which cloud services are used, and no way to review the decision retrospectively."
  - id: G-plan
    globalGate: null
    label: "Approve the inner-loop plan"
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
  - id: G4
    globalGate: "G4"
    label: "Approve the G4 handoff — merge the PR"
    trigger: "After plan is digest-pinned: fmt clean, validate clean, plan clean, policy-as-code clean, security reviewer clean"
    duration: "15–30 minutes"
    whatToCheck:
      - "Is the plan digest pinned in the PR? (The deploy step applies exactly this plan, nothing else.)"
      - "Did policy-as-code (OPA/Conftest) pass against the plan JSON — no unapproved resource types, required tags present?"
      - "Did the security reviewer find no new misconfigurations (Trivy/Checkov clean)?"
      - "Are reversibility hints correct? (Stateful data stores must be one-way-door, not reversible.)"
      - "If Infracost produced a cost delta, is the projected spend acceptable — or does it require a spend gate at G5?"
    whatGoodLooksLike: "A digest-pinned plan with policy-pass evidence, security review clean, correct reversibility hints, and an acceptable cost delta."
    whatBadLooksLike: "A plan without a pinned digest — the deploy step could apply a later, unreviewed plan. Or a reversibility hint of reversible on a DynamoDB table or RDS instance."
    consequence: "G4 is the last gate before deploy. An unpinned plan or missing policy-pass lets an unreviewed change reach a real account. A wrong reversibility hint silences the G5 spend or data gate."
  - id: G5
    globalGate: "G5"
    label: "Approve the prod ship"
    trigger: "After the deployed whole converges on the ephemeral environment — e2e clean, telemetry stable, security review done"
    duration: "15–30 minutes"
    whatToCheck:
      - "Is the release readiness record complete? (plan digest, policy-pass evidence, apply log, e2e results, telemetry snapshot, cost delta — estimated vs. actual)"
      - "Did the outer loop catch apply-time failures the plan didn't surface? (IAM propagation, quotas, dependency ordering — are they all resolved?)"
      - "Are there borderline gates in the record the agent marked 'close enough'?"
      - "Is the rollback path tested on the ephemeral environment — and do you trust it for prod?"
    whatGoodLooksLike: "A complete release readiness record, no open borderline gates, and a rollback path that was actually run on the ephemeral environment."
    whatBadLooksLike: "A record with missing sections, borderline gates waved through, or a rollback path that was described but never exercised."
    consequence: "G5 gates the prod ship. After this gate the change reaches real infrastructure — partially applied states require targeted destroy/re-apply paths, not clean undo."
typicalSession:
  agentTurns: "12–20"
  humanTouches: 3
  wallClockMinutes: "45–90"
docsUrl: /docs/guides/iac-terraform/
packUrl: /packs/iac-terraform/
relatedJourneys:
  - core
  - release
---

## 0. Gate the governance

- **Agent does:** activates generate-iac and loads the governance index — a manifest mapping each infrastructure decision domain (state backend, IAM model, OIDC trust policy, tagging, encryption at rest) to the ADRs and standards that bind it; reads only the 2–3 files the intent touches; if no governance-index.toml exists, bootstraps one from docs/adr/ and waits for your confirmation before proceeding; surfaces any uncovered decision domain and waits for a new ADR or explicit assumption before continuing.
- **You do:** review the governance index load; confirm the cited ADRs cover the intent's decision domains; check that no domain is uncovered; if the agent bootstrapped the index, verify it is complete enough to proceed.
- **You decide:** approve the governance gate.
- **Output:** a loaded governance index with binding ADRs confirmed and all decision domains covered.

---

## 1. Specify with a vocabulary firewall

- **You provide:** the required infrastructure inputs — target cloud, engine (terraform or opentofu), environments, region, account/tenant isolation model, and CI system.
- **Agent does:** writes the spec in generic infrastructure terms — no cloud-specific service names (no RDS, S3, GCS) before PLAN; records the account isolation model and its consequences for OIDC trust-policy scoping and state backend key structure; proposes the inner-loop plan.
- **You do:** read the spec; confirm the vocabulary firewall held; confirm the account isolation model is correct.
- **You decide:** approve the inner-loop plan.
- **Output:** a vocabulary-firewalled spec with the isolation model recorded, and an agreed plan ready for Terraform authoring.

---

## 2. Generate schema-grounded Terraform

- **Agent does:** decomposes the spec into a tier-ordered task list — Foundation (remote state, backend, provider config) → Network → Compute/Data → App → Polish — with ADR citations and parallel annotations only where no shared resource dependency exists; acquires the live provider schema via contract-acquisition (terraform/tofu providers schema -json against the pinned provider version) before authoring any resource block.
- **Loop does:** iterates write Terraform → fmt → validate → plan; feeds schema hallucination errors back immediately; does not advance until the plan is clean.
- **You do:** watch the iteration log at key moments; when a validate error surfaces a genuine schema ambiguity (not a hallucination), answer it directly; let the loop run otherwise.
- **Output:** a clean, schema-grounded Terraform plan with fmt, validate, and plan all passing.

---

## 3. Run static preflight and hand off to G4

- **Agent does:** runs policy-as-code (OPA/Conftest against the plan JSON — approved resource types, required tags, encryption at rest, no hard-coded credentials); runs Infracost for an optional cost delta; pins the plan digest; assembles the G4 handoff artifact with all evidence.
- **Reviewer does:** security-reviewer scans the generated configurations (Trivy/Checkov); adversarial-reviewer reads the spec, plan, and diff cold with no context from the authoring session.
- **You do:** read the policy-pass evidence and security review summary; check reversibility hints on stateful resources — a wrong hint silences the G5 spend or data gate; decide whether the cost delta requires a spend gate at G5.
- **You decide:** approve the G4 handoff — merge the PR.
- **Output:** a digest-pinned G4 handoff — deploy-ready Terraform, policy-pass evidence, security review summary, reversibility hints on stateful resources, and cost delta if present.

---

## 4. Deploy and converge

- **Agent does:** deploys to an ephemeral environment — uniquely named, per-cycle, teardownable — running terraform apply against the exact pinned plan.
- **Loop does:** reads apply-time failures invisible to plan (IAM propagation delays, service quotas, dependency ordering, terminal-failed resources) from the real environment; translates them into inner-loop build tasks for a corrected plan; redeploys until convergence — apply clean, e2e/smoke clean, telemetry stable.
- **You do:** monitor the outer loop at the end of each deploy iteration; watch for anomalies the agent might underweight — a quota increase requiring a support ticket, an IAM propagation window longer than expected; provide judgment on what "stable" means for this service.
- **Output:** a converged ephemeral deployment — apply clean, e2e/smoke clean, telemetry stable.

---

## 5. Ratify the release readiness record

- **Agent does:** produces the release readiness record — plan digest, policy-pass evidence, apply log (resources created/modified/destroyed), e2e results, telemetry snapshot, security diff review, and cost delta (estimated vs. actual); lists borderline gates explicitly.
- **You do:** read the full record, not just the summary; the borderline gates section is the critical one — these are cases where the agent decided "close enough"; make the spend-gate call if the actual cost delta materially exceeds the Infracost estimate.
- **You decide:** approve the prod ship — ratify if satisfied, or reject with a one-line reason to re-enter the loop.
- **Output:** a prod-ship decision; the change reaches real infrastructure after this gate.

---

## 6. Audit and reconcile drift

- **Agent does:** runs reconcile-iac on a weekly schedule, as mandatory preflight before a follow-on change, or immediately after a known out-of-band event; runs terraform plan and produces a drift audit — per-drifted-resource cause class, blast radius against governance standards, and proposed disposition (codify back into IaC, add ignore_changes, open a remediation PR, or block the follow-on change); surfaces that resources created entirely outside Terraform — ClickOps, console actions with no state entry — are invisible to plan and not covered by the audit.
- **You do:** read the drift audit; approve clear dispositions (e.g., ignore_changes for an auto-scaling group self-modification); escalate ambiguous ones that expand permissions or require a new ADR before codifying back; approve the remediation PR.
- **Output:** approved dispositions per drifted resource and a remediation PR where needed.
