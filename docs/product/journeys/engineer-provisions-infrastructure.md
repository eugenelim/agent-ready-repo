---
type: customer-journey
slug: engineer-provisions-infrastructure
persona: engineer-implementer
outcome: governed-terraform-shipped-and-drift-managed
surface: cross-platform
status: planned
rfc_links:
  - id: RFC-0065
    name: iac-terraform pack
    role: primary
updated: 2026-07-18
---

# Journey: Engineer provisions infrastructure with iac-terraform

**Persona:** A software engineer or platform engineer who needs to provision cloud infrastructure for a feature or service. They are comfortable with Terraform concepts but want to avoid re-deriving best practices (layered state, OIDC, policy-as-code, least-privilege IAM) from scratch. They operate inside a repo that has `core` installed and follows the work-loop / release-loop conventions.

**Outcome:** Governed, schema-grounded Terraform is authored, verified with policy-as-code and security review, and shipped through the loop arc (G4 inner handoff → release-loop outer loop → G5 prod ship). Day-2 drift is audited and dispositioned without autonomous apply. The engineer never runs `terraform apply` directly — the loop arc owns it.

**Surface:** cross-platform — CLI/terminal inside the work-loop + release-loop cycle.

**Trigger:** Engineer needs to provision infrastructure — a new service environment, a data store, an ingestion pipeline, a secrets backend — and wants to do it governed and without re-deriving the scaffolding by hand.

**End state:** Terraform merged and applied to prod (G5 ratified). Plan digest and release readiness record in the PR. Day-2 `reconcile-iac` running on schedule. Engineer exits with a governed, auditable infrastructure footprint.

**Related RFC:** [RFC-0065 — the `iac-terraform` pack](../../rfc/0065-iac-terraform-pack.md)

---

## Prerequisites

| Pack | Scope | Provides |
|---|---|---|
| `core` | repo | `work-loop`, `infra-verification`, `operational-safety`, `security-checklists`, reviewers |
| `governance-extras` | repo | `new-adr`, governance-index template |
| `iac-terraform` | repo | `generate-iac`, `reconcile-iac` |

**Optional:** `release-engineering` (repo) — `release-loop` drives the outer deploy/apply/converge cycle (Stage 4). Without it, the generated human-gated pipeline is the apply path (degraded mode).

**One-time setup (first time only):**
1. Install `iac-terraform` at repo scope.
2. Create or confirm `governance-index.toml` at the repo root (if none exists, `generate-iac` offers to bootstrap it).

---

## Interaction model

### Without iac-terraform (now)

```mermaid
sequenceDiagram
    participant E as Engineer
    participant A as Agent
    participant TF as Terraform toolchain

    Note over E,TF: Before iac-terraform — hand-derived scaffolding
    E->>A: I need a hardened object store with private ingestion
    A->>A: Re-derive layered Terraform structure from memory
    Note over A: No ADR gate, no vocabulary firewall
    A->>TF: Write HCL (guessed resource args)
    TF-->>A: validate error — wrong attribute name
    A->>TF: Fix and retry (multiple rounds)
    A-->>E: Terraform written — review?
    Note over E: No policy-as-code pass, no digest pin
    E-->>E: Manually applies via CI or locally
    Note over E: No drift audit schedule — drift accumulates undetected
```

### With iac-terraform (to-be, RFC-0065)

```mermaid
sequenceDiagram
    participant E as Engineer
    participant SK as generate-iac skill
    participant WL as work-loop (inner)
    participant RL as release-loop (outer)
    participant GI as governance-index.toml

    Note over E,GI: Stage 0 — mandatory governance gate
    E->>SK: I need a hardened object store with private ingestion
    SK->>GI: Load governance index (read only bound ADRs)
    GI-->>E: ADRs cited — decision domains: state-backend, IAM, tagging, encryption
    E->>SK: Confirm governance gate (+ bootstrap if no index)

    Note over E,GI: Stage 1 — vocabulary-firewalled spec
    SK-->>E: Spec in generic terms — inputs collected (cloud, engine, isolation model)
    E->>SK: Confirm spec and isolation model

    Note over E,GI: Stage 2 — tier-ordered plan + schema-grounded generation
    SK->>WL: Tier-ordered task list (Foundation→Network→Compute/Data→App)
    E->>WL: Approve plan
    WL->>WL: acquire provider schema → write TF → fmt → validate → plan (iterate)

    Note over E,WL: Stage 3 — static preflight + G4 handoff
    WL->>WL: OPA/Conftest (plan JSON) + security-reviewer + adversarial-reviewer
    WL-->>E: G4 handoff: digest-pinned plan + policy-pass evidence + reversibility hints
    E->>WL: Approve G4

    Note over E,RL: Stage 4 — release-loop outer cycle (full mode only)
    RL->>RL: Deploy to ephemeral → apply → e2e → observe
    RL-->>RL: Apply-time failure? Feed back to inner loop
    RL->>RL: Converge

    Note over E,RL: Stage 5 — G5 prod ship
    RL-->>E: Release readiness record (apply log + e2e + telemetry + cost delta)
    E->>RL: Ratify (or reject with reason)

    Note over E,SK: Stage 6 — Day-2 drift
    SK->>SK: reconcile-iac: plan → drift audit → proposed disposition
    SK-->>E: Per-resource disposition + scope boundary (unmanaged resources invisible)
    E->>SK: Approve remediation PR
```

---

## Stage 0: Governance Gate (mandatory pre-work)

**RFC anchor:** [§2 Hard rules — Stage 0 is mandatory](../../rfc/0065-iac-terraform-pack.md#stage-0-is-mandatory)

### Without iac-terraform (now)

| Row | Content |
|-----|---------|
| **Actions** | Engineer invokes the agent and asks for Terraform. Agent proceeds directly to authoring. No ADR check. No governance index. No record of which decisions were made or why. |
| **Emotions** | Efficient (short-term positive). Unconstrained authoring feels fast. |
| **Pains** | "The Terraform was written correctly but there was no record of why we chose S3 over GCS, or why we used workspaces instead of separate accounts." "Three months later someone changes the state backend and doesn't know they're reversing a deliberate decision." "Security audit asks for decision records for infra choices; we have none." |
| **Opportunities** | A mandatory pre-authoring gate that loads the governance index, identifies the bound decision records, and surfaces any uncovered decision domain before a line of Terraform is written. |

> **With iac-terraform** — `generate-iac` makes Stage 0 mandatory and non-bypassable: before any authoring, the governance index is loaded and the intent is mapped to decision records. If a domain is uncovered, the skill stops and surfaces it. First-time use: if no governance-index.toml exists, the skill bootstraps one from existing ADRs and confirms with the human before proceeding.

---

## Stage 1: Specify with Vocabulary Firewall

**RFC anchor:** [§2 Hard rules — Vocabulary firewall at SPECIFY](../../rfc/0065-iac-terraform-pack.md#vocabulary-firewall)

### Without iac-terraform (now)

| Row | Content |
|-----|---------|
| **Actions** | Agent writes a spec (or skips it) in cloud-specific terms. "Use S3 for the object store." "Route via an ALB." Cloud service names leak into the spec and lock in the provider before any architecture decision is made. |
| **Emotions** | Concrete (neutral). Cloud-specific names feel precise. |
| **Pains** | "The spec says S3 — three months later someone asks why we didn't evaluate GCS and there's no record." "The spec and the implementation are in different services because the scope drifted between spec and plan." |
| **Opportunities** | A vocabulary firewall that forces generic terms ('managed database', 'object storage') in the spec and reserves cloud-specific names for PLAN and later. Cloud-agnosticism by construction. |

> **With iac-terraform** — `generate-iac` enforces the vocabulary firewall: spec uses generic terms; cloud-specific service names appear only from PLAN onward. The agent also collects the account/tenant isolation model as an input (shared workspaces vs. separate account per environment) and records the decision, since it drives OIDC trust-policy scoping and the state backend key structure.

---

## Stage 2: Generate Terraform (Inner Authoring Loop)

**RFC anchor:** [§2 — It is a loop, not a straight line](../../rfc/0065-iac-terraform-pack.md#inner-authoring-loop) · [§2 Hard rules — Ground every resource in the live provider schema](../../rfc/0065-iac-terraform-pack.md#ground-every-resource)

### Without iac-terraform (now)

| Row | Content |
|-----|---------|
| **Actions** | Agent writes Terraform from training data. Resource types and argument names are guessed. `terraform validate` errors surface multiple rounds of schema hallucination fixes. State backend, provider pin, and `.terraform.lock.hcl` discipline are inconsistently applied. |
| **Emotions** | Intermittently frustrated (neutral-to-negative). The validate → fix cycle is tedious and unpredictable. |
| **Pains** | "The agent guessed the wrong attribute name for the S3 server-side encryption block. Fixed it in round 3." "The provider was unpinned — `init` pulled a minor version with a breaking argument change." "The state backend was configured without a lock — concurrent applies clobber each other." |
| **Opportunities** | Schema-grounded generation that acquires the live provider schema before emitting any resource block. Tier-ordered task decomposition that prevents dependency-ordering apply failures. Lockfile and provider version pinning by default. |

> **With iac-terraform** — `generate-iac` acquires the live provider schema via `core`'s `contract-acquisition` oracle (`terraform providers schema -json`) before emitting any resource block. No resource type, argument, or attribute is guessed. Tasks are tier-ordered (Foundation → Network → Compute/Data → App → Polish) to prevent apply-time dependency failures. `.terraform.lock.hcl` is committed by default. Parallel tasks are marked `[P]` only where resources have no shared dependency.

---

## Stage 3: Static Preflight and G4 Handoff

**RFC anchor:** [§2 — Loop diagram (step 6, plan CLEAN = G4 hand-off)](../../rfc/0065-iac-terraform-pack.md#loop-diagram) · [§2a — Verification modes](../../rfc/0065-iac-terraform-pack.md#verification-modes) · [§7 — Policy companions](../../rfc/0065-iac-terraform-pack.md#policy-companions)

### Without iac-terraform (now)

| Row | Content |
|-----|---------|
| **Actions** | Engineer manually runs `terraform validate` and `plan`. No policy-as-code pass. No security review of the generated configs. PR is opened with an unverified diff. |
| **Emotions** | Uncertain (neutral). "I think it's correct." No objective signal. |
| **Pains** | "The plan was clean but the IAM policy was wildcard — no policy gate to catch it." "We didn't scan the generated configs for hardcoded credentials — one made it to prod." "No plan digest: the deploy step applied a newer, unreviewed plan." |
| **Opportunities** | A pre-G4 static preflight sequence: OPA/Conftest on plan JSON (not HCL), security reviewer with config-misconfig modules, adversarial reviewer cold-read, cost delta (Infracost), then a pinned plan digest as the G4 handoff artifact. |

> **With iac-terraform** — the inner loop runs a full static preflight before G4: OPA/Conftest evaluates the plan JSON (checked resource types, tags, encryption, no hardcoded credentials), `security-reviewer` runs with `security-checklists/config-misconfig` inlined, `adversarial-reviewer` reads the diff cold. Optional: Infracost produces a cost delta. The G4 handoff artifact is explicit: deploy-ready Terraform + pinned plan digest + policy-pass evidence + security review summary + reversibility hints.
>
> **G4 handoff artifacts (explicit):** deploy-ready Terraform directory · pinned plan file (`terraform plan -out=tfplan` + digest) · OPA/Conftest exit-0 log · Trivy/Checkov exit-0 log · reversibility hints on stateful resources · (optional) Infracost cost delta JSON.

---

## Stage 4: Release Loop — Deploy, Apply, Converge

**RFC anchor:** [§1b — Loop integration (outer deploy loop)](../../rfc/0065-iac-terraform-pack.md#loop-integration) · [§2 — Two operating modes](../../rfc/0065-iac-terraform-pack.md#two-operating-modes)

### Without release-loop (degraded mode — common today)

| Row | Content |
|-----|---------|
| **Actions** | Engineer manually triggers the CI pipeline (the generated human-gated pipeline). A human reviewer approves the apply step in GitHub Environments. Apply runs against the target account. Apply-time failures land in the CI log. Engineer reads them and creates follow-on PRs. |
| **Emotions** | Manageable but slow (neutral). Each apply-time failure is a full round-trip. |
| **Pains** | "IAM propagation took 30 seconds — the pipeline timed out and left a partial state." "The dependency ordering was wrong — the subnet referenced the VPC before it was created." "Each apply failure needed a new PR and a new CI run." |
| **Opportunities** | A release-loop outer cycle that iterates autonomously on apply-time failures against ephemeral envs, feeds them back to the inner loop, and converges before surfacing for G5. |

### With release-loop (full mode)

| Row | Content |
|-----|---------|
| **Actions** | `release-lead` deploys to an ephemeral env, runs `terraform apply` against the pinned plan, reads apply-time failures from the real environment, translates them to inner-loop build tasks, corrects the plan, and redeploys. Iterates until convergence (apply clean, e2e clean, telemetry stable). |
| **Emotions** | Monitored (positive). The engineer is watching the outer loop converge, not debugging CI manually. |
| **Pains** | "Apply-time AWS failures are slow to appear — quota checks take 2+ minutes." "The agent sometimes marks a telemetry anomaly as noise when it isn't." |
| **Opportunities** | Outer-loop convergence criteria that are service-specific (not generic "e2e passed"); anomaly-detection thresholds the engineer can calibrate per service. Post-M1 backlog. |

> **Full mode requires:** `release-engineering` installed + an ephemeral-env harness + the release-loop conformance canary (see RFC-0065 §1b). Without these, degraded mode is the supported path in v1.

---

## Stage 5: G5 — Release Readiness Record and Prod Ship

**RFC anchor:** [§1b — G5 + minimum-regret consent gates](../../rfc/0065-iac-terraform-pack.md#minimum-regret-consent)

### Now (any mode)

| Row | Content |
|-----|---------|
| **Actions** | In degraded mode: Engineer reviews the CI apply log and approves the GitHub Environments protection. In full mode: `release-loop` produces the release readiness record; engineer reads it and ratifies. |
| **Emotions** | Decisive (positive). G5 is the clear prod-ship gate. |
| **Pains** | "The release readiness record doesn't show the actual cost vs. Infracost estimate — I need to check CloudWatch Cost Explorer separately." "Borderline gates aren't grouped — I have to read the full log to find them." |
| **Opportunities** | An IaC-specific RRR template that includes: plan digest, policy-pass evidence, apply log summary, e2e results, telemetry snapshot, actual cost vs. Infracost estimate delta, borderline gates grouped. |

> **IaC-specific release readiness record (what to expect):** plan digest · policy-pass evidence · apply log (created/modified/destroyed count per resource type) · e2e smoke results · telemetry snapshot (key metrics) · cost delta (Infracost estimated vs. actual billed, if available) · borderline gates grouped.

---

## Stage 6: Day-2 — Drift and reconcile-iac

**RFC anchor:** [§2 — Two skills (generate-iac + reconcile-iac)](../../rfc/0065-iac-terraform-pack.md#two-skills) · [§2 Known blind spot: unmanaged resources](../../rfc/0065-iac-terraform-pack.md#unmanaged-resources)

### Without iac-terraform (now)

| Row | Content |
|-----|---------|
| **Actions** | Drift accumulates undetected. A follow-on change runs `terraform plan` and reveals unexpected diffs. Engineer investigates manually. No structured disposition. |
| **Emotions** | Reactive and surprised (negative). "Why does this have a diff? I didn't change anything." |
| **Pains** | "Drift is discovered only when something breaks or when a follow-on PR runs plan." "There's no structured way to record the decision: should we codify this drift back into IaC, or add ignore_changes?" "We can't tell if a ClickOps change was intentional or accidental." |
| **Opportunities** | A scheduled `reconcile-iac` run that produces a per-resource drift audit with cause class, blast radius, and proposed disposition — and that explicitly surfaces its own scope boundary (unmanaged resources are invisible). |

> **With iac-terraform** — `reconcile-iac` runs on three triggers: (1) **before every follow-on change** (mandatory preflight), (2) **weekly minimum** on a scheduled basis, and (3) **immediately after a known out-of-band event** (break-glass, console action, provider-managed service update). Each run produces a drift audit with per-resource disposition proposals and an explicit scope boundary notice (resources with no state entry are outside the audit). The skill never applies autonomously — every disposition requires human approval.
>
> **reconcile-iac scope boundary (honesty):** `terraform plan` sees only state-tracked resources. Resources created entirely outside Terraform (ClickOps, console actions, auto-provisioned resources) are invisible. The skill documents this limit explicitly in its output rather than implying full drift coverage.

---

## Frontstage actions

- **Skill:** generate-iac (Stage 0–3)
- **Skill:** reconcile-iac (Stage 6)
- **Loop:** work-loop inner loop (Stage 2–3)
- **Loop:** release-loop outer loop (Stage 4–5, full mode only)
- **Gate:** G-governance (Stage 0)
- **Gate:** G-plan (Stage 2 entry)
- **Gate:** G4 (Stage 3 exit)
- **Gate:** G5 (Stage 5 exit)

---

## Emotional arc

Highest point: **Stage 3 (G4 handoff review)** — the engineer sees a complete, policy-verified, digest-pinned artifact and knows exactly what will be applied. The governance record, policy-pass evidence, and reversibility hints together give a level of confidence that manually derived Terraform never does.

Lowest point (without iac-terraform): **Stage 6 (drift discovery)** — drift is found accidentally, with no structured way to disposition it. The engineer is reactive to something that could have been proactive.

Highest-opportunity pain: "I provisioned the infra correctly. But six weeks later there's drift I didn't know about, I can't tell if it's intentional, and the follow-on change might reverse a break-glass fix that someone else made deliberately."

Primary design response: `reconcile-iac` as a first-class skill on a scheduled + event-triggered basis, with a per-resource drift audit that includes cause class and explicit scope boundary. The engineer exits each `reconcile-iac` run knowing exactly what drifted, why, and what the proposed disposition is.

---

## How the journey changes with RFC-0065

| Stage | Before RFC-0065 | After RFC-0065 |
|---|---|---|
| **0 — Governance** | No gate; authoring starts immediately | Mandatory governance-index load; uncovered domains stop the skill |
| **1 — Specify** | Cloud-specific names in spec | Vocabulary firewall; cloud names deferred to PLAN |
| **2 — Generate** | Schema guessed from training data | Live schema acquired before every resource block |
| **3 — Preflight** | Manual validate/plan only | OPA/Conftest + security reviewer + adversarial reviewer + digest pin |
| **4 — Deploy** | Manual CI pipeline trigger; engineer debugs apply failures | `release-loop` outer cycle iterates autonomously on ephemeral envs (full mode) |
| **5 — G5** | GitHub Environments approval of CI apply | Full release readiness record with IaC-specific fields |
| **6 — Drift** | Drift discovered reactively | `reconcile-iac` on schedule + preflight + event-triggered |

---

## Handoff notes

**For `engineer-runs-work-loop` journey:** `iac-terraform` is IaC-flavored authoring inside `work-loop`. The plan review gate (Stage 3 in that journey) maps to Stages 2–3 here. The work-loop journey's M1.7 workspace integration applies to IaC specs exactly as to application specs.

**For `release` journey:** the release-loop journey covers Stage 4 from the loop's perspective. The iac-terraform journey extends it with IaC-specific inputs (the G4 handoff artifact set, reversibility hints, the IaC-flavored release readiness record fields).

**For future INI:** if `iac-terraform` becomes part of a platform-engineering initiative, this journey maps to its build-room stages. The shaping room journeys (product-engineer-shapes-initiative) are upstream prerequisites — the infrastructure intent flows from a brief into this journey's Stage 0.
