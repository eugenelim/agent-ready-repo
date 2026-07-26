---
name: generate-iac
description: Use this skill to author governed, best-practice Terraform/OpenTofu infrastructure from a plain-language intent. Triggers on "provision X", "create Terraform for", "generate IaC for", "set up cloud resources", "write Terraform for", "scaffold infrastructure". Stops at a digest-pinned `terraform plan` (G4 handoff); never runs `apply`. Governance-first — loads the decision-record index before any code.
---

# Skill: generate-iac

Author governed, best-practice Terraform/OpenTofu from a plain-language intent.
The output is a deploy-ready Terraform directory with a pinned, clean `plan` —
the G4 handoff to `release-loop` (or the generated human-gated pipeline where
`release-loop` is absent). Apply is never in scope for this skill.

## v1 scope — governed realization, not architectural design

**In scope (v1):** governed HCL generation from a pre-formed architectural
intent; provider-contract, tagging, naming, state, IAM, networking, and
observability standards applied; OPA/Conftest policy gate; Trivy security scan;
CI pipeline wiring (GitHub Actions / Azure DevOps / GitLab) with OIDC auth;
plan-based drift audit via `reconcile-iac`.

**Out of scope in v1 — bring a pre-formed architectural decision:**
- **Workload selection.** RDS vs Aurora vs DynamoDB, EKS vs ECS vs Lambda, VM
  vs container vs serverless. This skill governs and builds what you chose; it
  does not evaluate requirements → service fit.
- **Network topology design.** Hub-spoke vs flat, Transit Gateway vs VPC
  peering, on-prem connectivity (DX / ExpressRoute / Interconnect), multi-region
  topology. This skill consumes a network; it does not design one.
- **Load balancer type/tier selection.** L4 vs L7, global vs regional,
  health-check strategy, blue/green or canary traffic-shift. "Governed front
  door only" means the skill wires an LB you specify.
- **Multi-account / landing-zone orchestration.** AWS Control Tower, Azure
  Landing Zones, GCP org-hierarchy. Account-isolation model is an input; the
  org infrastructure is not provisioned here.
- **Compliance-framework content.** CIS, NIST, PCI-DSS, HIPAA, FedRAMP, SOC 2
  control mapping. Adopt via governance-index domain rows + custom standard
  references; built-in standards are security-best-practice, not a
  control-framework map.
- **IAM guardrail layer.** AWS SCPs, AWS permission boundaries, Azure Policy at
  management-group scope, GCP Org Policy constraints. The pack enforces
  least-privilege role policies; org-level guardrails are an adopter addition
  (see `security-iam-standard.md` § Organization-level guardrails).
- **Autonomous apply / operational self-healing.** `reconcile-iac` v1 is
  managed-drift detect-propose-approve (never autonomous). Runtime operational
  self-healing (auto-remediate live service degradation) is not in scope.

## Hard rules — non-negotiable

- **Stage 0 is mandatory and non-bypassable.** Before any Terraform, load the
  repo's governance index (`governance-index.toml` / `governance-index.yaml`)
  and read only the 2–3 files it maps to the intent's domains. The plan must
  list which decision records it satisfies and why. Do not proceed to Stage 1
  until Stage 0 is complete.
  - **First-time use (no governance-index exists yet):** offer to bootstrap one
    — scan `docs/adr/` for infrastructure-adjacent ADRs, scaffold the index
    structure with their references (using the template from
    `governance-extras/seeds/governance/manifest.example.yaml`), and confirm
    the bootstrap with the human before proceeding. The bootstrapped index is a
    starting point; the human confirms completeness before Stage 0 proceeds.
- **Never invent a decision record.** If an intent conflicts with an existing
  ADR, or no ADR covers a material decision, stop and surface it — draft a new
  ADR via `governance-extras`' `new-adr` (infra mode); do not silently resolve.
- **Never hardcode a cloud.** The target cloud is always an input; provider,
  backend, and module choices resolve from `references/providers/<cloud>.md`.
- **Vocabulary firewall at Stage 1 (SPECIFY).** `spec.md` names only generic
  infrastructure ("managed database", "object storage", "container
  orchestration") — no cloud-specific service names. Concrete services (RDS,
  Blob Storage, GKE…) appear only from PLAN onward. Cloud-agnosticism by
  construction.
- **Tier-ordered tasks at Stage 4 (TASKS).** Order `tasks.md` by infrastructure
  tier: Foundation → Network → Compute/Data → App → Polish. Mark a task `[P]`
  only when it touches disjoint files with no resource/data dependency.
- **Scenario-independence.** Each infra slice must be independently deployable,
  validatable, and rollback-able.
- **Ground every resource in the live provider schema — always on.** Before
  emitting any resource, acquire the provider's live contract via `core`'s
  `contract-acquisition` oracle and reference the cited schema slice. Never
  guess a resource type, argument, or field. The ground-truth oracle is the
  toolchain's own `terraform providers schema -json` / `tofu providers schema
  -json` combined with `validate`. The HashiCorp Terraform MCP server and
  Registry API are optional discovery accelerants — never dependencies.
- **Standards are binding.** The standard references (terraform-standard,
  networking-standard, security-iam-standard, tagging-standard,
  observability-standard) are law. Cite the standard applied.
- **Apply is the outer loop's, gated by the loop arc.** The skill's
  deliverable is a green, digest-pinnable `plan` = the G4 handoff. Deploy and
  apply are `release-loop`'s act on ephemeral isolated envs, human-gated at
  the irreversible exits. **Never emit a command that runs `apply` or
  `destroy`.**

## Inputs to collect (ask if missing; use documented defaults)

| Input | Default | Note |
| --- | --- | --- |
| Target cloud | **ask** | Never guess |
| Engine | `terraform` | `terraform \| opentofu` — emit engine-neutral HCL unless a divergent feature is requested; load `opentofu-differences.md` only when `engine = opentofu` |
| Environment(s) | `dev` | |
| Region | **ask** | |
| Decision-record source | repo's `docs/adr/` | |
| CI system | `github-actions` | `github-actions \| azure-devops \| gitlab` |
| Remote execution platform | `none` | `none \| hcp-terraform \| scalr`; when `engine = opentofu`, only `none` and `scalr` are valid — `cloud {}` is Terraform-only and incompatible with OpenTofu |
| State backend | derive from cloud | S3 (AWS), GCS (GCP), Azure Blob — **only when `remote_exec_platform = none`**; remote exec platforms own the state |
| Account/tenant isolation model | separate account per env | drives OIDC trust-policy scoping and state backend key structure |

## Stage sequence

```
Stage 0: ADR gate (mandatory, non-bypassable)
  → load governance-index; bootstrap if absent; read 2-3 governing files
Stage 1: SPECIFY
  → vocabulary firewall — generic names only in spec.md; no cloud service names
Stage 2: CLARIFY
  → collect all inputs; ask for missing; confirm engine + cloud + region
Stage 3: PLAN
  → load provider reference for target cloud; load CI reference for target CI
  → when platform ≠ none: load references/remote-exec/<platform>.md
  → draft: ADR-compliance table + standards-mapping table + layered layout
  → networking design + pipeline design + reversibility hints per stateful resource
  → ADR-compliance table must have zero ❌/⚠️ rows before proceeding to Stage 4
  → optional deep-design pass: tap `architect` pack's Well-Architected lenses
    when installed (soft dependency — degrade cleanly when absent)
Stage 4: TASKS
  → tier-ordered (Foundation → Network → Compute/Data → App → Polish)
  → [P] only when files are disjoint with no resource/data dependency
Stage 5: WRITE TF
  → ground every resource type in live schema via contract-acquisition
  → emit provider config files (versions.tf / provider.tf) per
    references/provider-contract.md; backend config branches on platform:
    • platform = none (default): backend.tf + backend.hcl.example
      (cloud-native object store: S3 / GCS / Azure Blob)
    • platform = hcp-terraform: cloud {} block in versions.tf;
      no backend.tf, no backend.hcl.example
    • platform = scalr: backend.tf with backend "remote" block;
      no backend.hcl.example
  → when platform ≠ none: emit REMOTE_EXEC_SETUP.md (credential guidance,
    token setup, traps) per references/remote-exec/<platform>.md
  → apply all mandatory tagging (references/tagging-standard.md)
  → tag stateful resources with reversibility-class annotations
    (reversible | costly-to-reverse | one-way-door)
  → emit OPA/Conftest starter rules (references/policy-on-plan.md)
  → emit CI pipeline (references/pipeline/<ci>.md) with OIDC auth, no static keys
Stage 6: VERIFY (inner loop — iterate until clean)
  → terraform fmt -check (or tofu fmt -check)
  → terraform validate (or tofu validate)
  → terraform plan -out=tfplan (or tofu plan -out=tfplan)
  → shasum -a 256 tfplan → record the plan digest
  → terraform show -json tfplan | conftest test (or tofu show ...)
  → trivy config . (or checkov -d .)
  → [optional] infracost diff --path . --format json
G4 handoff
  → deploy-ready Terraform directory
  → pinned plan file + digest (shasum -a 256 tfplan)
  → OPA/Conftest exit-0 evidence (plan JSON + checks applied + zero violations)
  → Trivy/Checkov exit-0 evidence
  → reversibility hints per stateful resource
  → [optional] Infracost cost delta JSON
```

## References (load on demand per target)

Standards (always load):
- `references/terraform-standard.md` — layered layout, versioning, state, anti-patterns
- `references/networking-standard.md` — private-by-default, per-cloud table
- `references/security-iam-standard.md` — least-privilege, OIDC, data protection
- `references/tagging-standard.md` — 6 mandatory keys + per-cloud application
- `references/observability-standard.md` — OTEL emit + collector + backend + dashboards

Verification and provider shape:
- `references/terraform-verify-and-iterate.md` — plan-vs-apply oracle, module tests
- `references/provider-contract.md` — four-file shape + credential tiering + DoD
- `references/release-loop-integration.md` — G4 artifact set, preflight-set shaping
- `references/bootstrap-sequence.md` — **load for first bootstrap/ apply** — local-state → create-backend → migrate-state chicken-and-egg story

Load per target (never all at once):
- `references/providers/<cloud>.md` — cloud-specific config (aws / gcp / azure / …)
- `references/opentofu-differences.md` — **load ONLY when engine = opentofu**
- `references/pipeline/<ci>.md` — CI pipeline shape (github-actions / azure-devops / gitlab)
- `references/remote-exec/<platform>.md` — **load ONLY when platform ≠ none** — config block, auth, credential model, CI trigger delta, bootstrap narrative (hcp-terraform / scalr)

Policy and plan shape:
- `references/policy-on-plan.md` — starter Rego rules + Trivy/Checkov guidance
- `references/spec-plan-tasks-shape.md` — mandatory ADR-compliance-table plan shape

## Reuse — do not duplicate `core`

This skill **references** `core`'s depth rather than re-stating it:
- Verification method (phased oracle fidelity, plan/preview discipline, drive
  the deploy yourself) → `core`'s infra-verification mode
- Operational depth (state & idempotency, drift & rollback, environment
  isolation, cost & teardown, observability & smoke) → `core`'s
  `operational-safety` modules, inlined by the orchestrator
- IaC/deploy-config misconfiguration review → `core`'s `security-checklists`
  (`config-misconfig` module), mandatory and non-skippable on infra work
- ADR authoring → `governance-extras`' `new-adr` (infra mode)

## Reviewers (reused from `core` — zero new agents)

Route through the orchestrator-inlining mechanism at REVIEW:
- `adversarial-reviewer` — spec/plan/diff; always after GATES pass
- `quality-engineer` — operational lens, with `operational-safety` modules
  (state-and-idempotency, drift-and-rollback, environment-isolation,
  cost-and-teardown, observability-and-smoke, cloud-implementation-craft)
  inlined by orchestrator
- `security-reviewer` — `security-checklists/config-misconfig` + matching
  modules (access-control, secrets-and-crypto as diff trips them); mandatory
  on infra work

## Loop arc

```
inner loop (work-loop):
  intent → Stage 0 → spec → plan → tasks → write TF
                    ↕
  fmt · validate · plan  ── errors? ─────────────────┘
       │  (schema/arg hallucination, cycle, missing var)
       ▼  plan CLEAN + digest-pinned  ==  G4 hand-off

outer loop (release-loop, when installed):
  deploy to ephemeral env → apply → e2e/smoke → observe
       │
       └── apply-time failure? ── feed back to inner ──┘
  converge → release-readiness record → G5 (human)
```

**Full mode** (`release-loop` + ephemeral envs + conformance canary present):
autonomous apply-iteration catches AWS-style apply-time failures (IAM
propagation, service quotas, terminal FAILED states).

**Degraded mode** (common case — `release-loop` absent): `work-loop` inner
loop + generated human-gated pipeline. Still a real improvement over hand-
written scaffolding; without the outer loop, autonomous apply-iteration is
unavailable. The RFC does not claim full mode as the default.

## Anti-patterns this skill refuses

- Emitting `terraform apply`, `terraform destroy`, or any autonomous apply path.
- Skipping Stage 0 for "simple" or "small" infrastructure.
- Inventing a decision record to satisfy Stage 0.
- Hardcoding a cloud-specific service name in the SPECIFY spec.
- Referencing `tfsec` (merged into Trivy in 2023) or DynamoDB state locking
  (superseded by native S3 lockfile, GA in Terraform 1.11).
- Committing `*.tfvars` with real values or raw credentials.
- Emitting a Sentinel policy (incompatible with OpenTofu — use OPA/Conftest
  for the open-source policy path that works on both engines).
- Emitting `backend "remote" { hostname = "app.terraform.io" ... }` for an HCP
  Terraform target — this is the deprecated form; generate a `cloud {}` block
  in `versions.tf` instead.
- Emitting a `cloud {}` block for an `engine = opentofu` target — it is
  Terraform-only and incompatible; offer `platform = scalr` with
  `backend "remote"` as the OpenTofu-compatible remote execution alternative.
