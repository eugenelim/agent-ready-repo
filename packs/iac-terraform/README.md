# `iac-terraform` pack

> **Opt-in, repo-scope.** Not included in any default profile.
> `agentbundle install --pack iac-terraform <catalogue>`
> (`<catalogue>` is a local clone path or a `git+https://…` URL)

Turn a plain-language infrastructure intent into governed, best-practice Terraform/OpenTofu — decision-record-driven, cloud-agnostic, and human-gated at apply time.

**The agent produces the plan. You gate apply.**

---

## Start here

Describe what infrastructure you need.

```text
Provision an S3 bucket with versioning enabled and a lifecycle policy
that moves objects to Glacier after 90 days.
```

```text
Check whether my infrastructure has drifted from the last plan.
```

The pack runs in two modes:

- **generate-iac** — governance gate → spec → plan → `.tf` files → `terraform plan` pinned for your review. Stops before `apply`.
- **reconcile-iac** — drift audit against the last plan → proposed disposition per resource → route for your decision.

---

## Common jobs

**Generate governed Terraform from an intent**
Describe the infrastructure you want to provision.
The pack starts with a mandatory **Stage 0 ADR gate** — the infrastructure decision is recorded before any code is written. Then it produces a vocabulary-firewalled spec, schema-grounded `.tf` files, and an OPA policy + security preflight. It stops at a digest-pinnable `terraform plan` output.

```text
provision-vpc

  Stage 0 (ADR gate)
  ● Decision recorded → docs/adr/0042-vpc-design.md
  Approve to continue? ›

  Generating .tf files ...
  ● terraform fmt -check ✓
  ● terraform validate ✓
  ● OPA policy check ✓
  ● Security preflight ✓

  Plan output: infra/plans/vpc-2026-07-29.plan (digest pinned)

  Review the plan? ›   Gate apply? ›
```

**Audit infrastructure drift**
Say `reconcile-iac` — before a change, or on a schedule.
Runs a `terraform plan`-based drift audit and proposes a per-resource disposition (accept / correct / defer). You decide what to do with each resource. Nothing is applied.

---

## Infrastructure boundary — what the agent does and does not do

| Zone | Who acts |
|------|----------|
| ADR gate, spec, `.tf` generation, preflight, `plan` | Agent (autonomous) |
| Review the `terraform plan` output | **You** |
| `terraform apply` | **You** (or your CI pipeline at G4 handoff) |
| Irreversible destructive actions (resource deletion, data migration) | **You** — always human-gated |

**State files** are never touched by the agent — state management (`terraform state`, backends, locking) is the responsibility of your CI pipeline and your `terraform apply` step.

**Secrets** (API keys, service-account credentials) are never generated, stored, or read by the agent. Use your credential store; reference them as environment variables or Vault references in the generated configuration.

**Rollback:** if you need to roll back a change, re-run `reconcile-iac` from the last known-good plan to produce a reverse disposition, then review and apply it.

---

## Validated in v1

| Provider | Status | Note |
|----------|--------|------|
| AWS | **validated** | Passes `init -backend=false && fmt -check && validate` on both `terraform` and `tofu` |
| GCP | **validated** | Passes `init -backend=false && fmt -check && validate` on `terraform` |
| Databricks | **validated** | Passes `init -backend=false && fmt -check && validate` on `terraform` |
| Azure | contract-complete | Unvalidated in v1 — stamped **experimental** |
| All other categories | contract-complete | Stamped **experimental — not validated in v1** |

---

## Installation and trust

- **Scope:** repo — installs into the repo where your infrastructure code lives
- **Reads:** your infrastructure intent, existing `.tf` files, provider schemas (via `terraform providers schema`)
- **Local writes:** `.tf` files, ADR records, plan digest file — only after you approve each gate
- **Remote reads:** provider registries (via `terraform init`); no direct cloud API calls
- **Remote writes:** none — `apply` is always yours
- **Requires:** `core` ≥0.1, `governance-extras` ≥0.6, `terraform` or `tofu` CLI in PATH

---

## Design

- **Zero seeds** — all provider configs, pipeline YAML, and OPA rules are generated into the adopter repo; the pack ships none.
- **Zero agents** — reuses `core`'s `adversarial-reviewer`, `quality-engineer`, and `security-reviewer` via the existing orchestrator-inlining mechanism.
- **Dual-engine** — Terraform and OpenTofu share an HCL-compatible baseline; divergences are in `references/opentofu-differences.md`, loaded only when `engine = opentofu`.
- **Category taxonomy** — provider coverage tracks the Terraform registry's own category list (MECE); each category gets a fit-for-purpose reference.

---

## Skills included — under the hood

| Skill | Trigger | What it does |
|-------|---------|-------------|
| `generate-iac` | "provision X", "create Terraform for", "generate IaC for" | ADR gate → spec → plan → Terraform → `terraform plan` pinned for G4 handoff. Never runs `apply`. |
| `reconcile-iac` | "reconcile my infrastructure", "check for drift", "drift audit" | `plan`-based drift audit → proposed disposition → route for your decision. Never applies autonomously. |

---

## Go deeper

→ [`guides/iac-terraform/`](../../guides/iac-terraform/)
→ [`JOURNEY.md`](JOURNEY.md) — the seven-stage governance loop from intent to plan
