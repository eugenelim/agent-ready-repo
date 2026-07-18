---
pack: iac-terraform
scope: repo
tagline: "Intent → governed Terraform. Stops at plan."
prerequisitePacks:
  - core
  - governance-extras
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

## Stage 0 — Governance gate

Before a single line of Terraform was written, the agent activated `generate-iac` and loaded the governance index — a manifest mapping each infrastructure decision domain (state backend, IAM model, OIDC trust policy, tagging, encryption at rest) to the ADRs and standards that bind it. It read only the 2–3 files the intent touched.

If no governance-index.toml existed yet, the agent offered to bootstrap one: scanning the repo's `docs/adr/` directory for infrastructure-adjacent ADRs and scaffolding the index structure from them. You reviewed and confirmed the bootstrap before any authoring began. If a decision domain had no covering ADR, the agent surfaced it and waited — either you drafted a new ADR via `new-adr` first, or you documented the assumption explicitly before the skill continued.

**You:** Reviewed the governance index load. Confirmed the right ADRs were cited for the intent's decision domains. Checked that no domain was uncovered. 5–15 minutes — this gate has no shortcut.

---

## Stage 1 — Specify with vocabulary firewall

The agent wrote the spec in generic infrastructure terms: "managed relational database", "object storage", "private ingestion pipeline". No cloud-specific service names appeared (no RDS, S3, GCS, Cloud Storage) — those are resolved at PLAN, not SPEC. This vocabulary firewall keeps the spec cloud-agnostic and prevents lock-in from leaking into the governing record.

The agent confirmed the required inputs: target cloud, engine (terraform or opentofu), environments, region, account/tenant isolation model (separate accounts per environment vs. shared account with workspaces), and CI system. The isolation model mattered most — it drove OIDC trust-policy scoping and the state backend key structure. The agent recorded the decision.

**You:** Read the spec. Confirmed the vocabulary firewall held. Confirmed the account isolation model. Approved the plan. 5–10 minutes.

---

## Stage 2 — Tier-ordered plan and schema-grounded generation

The agent decomposed the spec into a tier-ordered task list: Foundation (remote state, backend, provider config) → Network → Compute/Data → App → Polish. Each task cited the ADR and standard it satisfied. Tasks marked `[P]` were only those with no shared resource dependency.

Before emitting any resource block, the agent acquired the live provider schema via `core`'s `contract-acquisition` oracle — running `terraform providers schema -json` (or `tofu providers schema -json`) against the pinned provider version. No resource type, argument, or attribute was guessed from training data.

The authoring loop iterated: write Terraform → `fmt` → `validate` → `plan`. Schema hallucination errors (unknown argument, unsupported resource type) fed back immediately. The loop did not advance until the plan was clean.

**You:** Watched the iteration log at key moments. When a `validate` error surfaced a genuine schema ambiguity (not a hallucination), answered it directly. Let the loop run otherwise. 20–40 minutes.

---

## Stage 3 — Static preflight and G4 handoff

With a clean plan, the agent ran the static preflight gates in sequence:

1. **Policy-as-code**: OPA/Conftest evaluated the plan JSON — not the HCL, because HCL values are not resolved until plan time. Checks: approved resource types, required tags, encryption at rest, no hard-coded credentials.
2. **Security review**: `security-reviewer` with `security-checklists/config-misconfig` inlined — Trivy and Checkov scanned the generated configurations.
3. **Adversarial review**: `adversarial-reviewer` read the spec, plan, and diff cold, with no context from the authoring session.
4. **Cost delta** (optional): Infracost produced a plan-based cost estimate and surfaced it before the G4 gate.

When all gates passed, the agent pinned the plan digest and assembled the G4 handoff: the deploy-ready Terraform, the pinned plan file, policy-pass evidence, security review summary, reversibility hints on stateful resources, and the Infracost delta if present.

**You:** At G4, reviewed the handoff artifact. Confirmed the digest was pinned. Read the policy-pass evidence and security review summary. Checked reversibility hints on any stateful resources — a wrong hint silences the G5 consent gate. Decided whether the cost delta needed a spend approval at G5. 15–30 minutes.

---

## Stage 4 — Release loop: deploy, apply, converge

With the G4 handoff merged, `release-loop` took over. The `release-lead` agent deployed to an ephemeral environment — a uniquely named, per-cycle, teardownable account — and ran `terraform apply` against the exact pinned plan.

Apply-time failures invisible to `plan` surfaced here: IAM propagation delays, service quotas, dependency ordering (a subnet referenced before the VPC was created), resources reaching terminal `FAILED` states. The outer loop read these from the real environment, translated them into inner-loop build tasks, and fed them back to `generate-iac` for a corrected plan. The loop iterated until convergence: apply clean, e2e/smoke clean, telemetry stable.

**You:** Monitored the outer loop at the end of each deploy iteration. Looked for anomalies the agent might underweight — a quota increase requiring a support ticket, an IAM propagation window longer than expected. Provided judgment on what "stable" meant for this service. 15–30 minutes per iteration.

---

## Stage 5 — G5: Release readiness record and prod ship

After convergence, `release-loop` produced the release readiness record: plan digest, policy-pass evidence, apply log (which resources were created/modified/destroyed), e2e results, telemetry snapshot, security diff review, and cost delta (estimated vs. actual). Borderline gates were listed explicitly — cases where the agent decided "close enough."

**You:** Read the full record — not just the summary. The borderline gates section was the critical one. If the actual cost delta exceeded the Infracost estimate materially, you made the spend-gate call here. Ratified if satisfied. Rejected with a one-line reason if not — the agent re-entered the loop. 15–30 minutes.

---

## Stage 6 (Day 2) — Drift and reconcile-iac

Days after initial provision, drift accumulated: a security team made a break-glass IAM change, an AWS-managed service auto-modified a tag, the provider released a default value change. The agent ran `reconcile-iac` — on a weekly schedule, before a follow-on change (mandatory preflight), or triggered immediately after a known out-of-band event.

`reconcile-iac` ran `terraform plan` and produced a drift audit: per-drifted-resource, the cause class and blast radius against the governance standards. For each resource it proposed a disposition: codify back into IaC, add `ignore_changes`, open a remediation PR, or block the follow-on change.

One caveat the agent surfaced explicitly: resources created entirely outside Terraform — ClickOps, console actions with no state entry — were invisible to `plan`. The drift audit covered only state-tracked resources.

**You:** Read the drift audit. Approved clear dispositions (add `ignore_changes` for an auto-scaling group self-modification). Escalated ambiguous ones (a break-glass IAM change that expanded permissions — needed a new ADR before codifying back). Approved the remediation PR. 10–20 minutes.
