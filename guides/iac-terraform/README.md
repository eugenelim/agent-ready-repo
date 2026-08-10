---
title: IaC (Terraform) guides
summary: Find the governed Terraform and OpenTofu generation workflow, drift checks, and validated provider coverage.
pack: iac-terraform
kind: reference
---

# `iac-terraform` — guides

An opt-in accelerator for Terraform and OpenTofu IaC generation. Two skills —
`generate-iac` (seven-stage governance-to-plan loop) and `reconcile-iac` (drift audit
before every follow-on change) — plus a reference library covering per-cloud
provider contracts, standards, and pipeline patterns.

**Dependencies:** `core` and `governance-extras >= 0.6.0`. The `generate-iac`
skill reads the repo's governance index (a domain → ADR manifest) at Stage 0 —
see [the governance-extras guide](../governance-extras/README.md) for how to
set one up.

## Skills

| Skill | Trigger | What it does |
| --- | --- | --- |
| `generate-iac` | "provision X", "create Terraform for", "generate IaC for" | Stage 0 ADR gate → SPECIFY → CLARIFY → PLAN → TASKS → WRITE TF → VERIFY → G4 handoff |
| `reconcile-iac` | "check for drift", "reconcile IaC" | Runs `terraform plan` and classifies every change before follow-on work |

## How-to

The guides here are task-oriented. Explanation of the design (zero seeds,
dual-engine, loop-arc alignment, category taxonomy) is in the pack README at
`packs/iac-terraform/README.md`.

### Getting started

1. Install the `iac-terraform` pack (requires `core` and `governance-extras >= 0.6`).
2. If you don't have a governance index yet, create one:
   [Set up a governance index](../governance-extras/how-to/governance-index.md).
3. Ask the agent: "Generate IaC for [what you want to provision] on [AWS/GCP/Azure]."
   The `generate-iac` skill runs Stage 0 first — it reads your governance index
   and asks about any missing ADRs before emitting Terraform.

### Common tasks

- **Generate IaC for a new workload** — invoke `generate-iac`. It asks for
  target cloud, engine (terraform/tofu), environment, and region. Stage 0 reads
  your governance index. Stages 1–2 specify the workload and collect inputs;
  Stage 3 plans; Stage 4 orders tasks; Stage 5 writes Terraform and the CI
  pipeline; Stage 6 formats, validates, plans, runs policy and security checks,
  and records the plan digest for handoff.

- **Check for drift before a follow-on change** — invoke `reconcile-iac`.
  It runs `terraform plan`, classifies every planned change by reversibility
  class, and emits a disposition report. Mandatory before every follow-on
  (`generate-iac` hard rule).

- **Add a new ADR for an infrastructure decision** — use `new-adr` with
  `mode: infra`. The `new-adr` infra mode (governance-extras 0.6.0) gives you
  the right framing question for each of the seven IaC ADR topics.

- **Set up the CI pipeline** — Stage 5 of `generate-iac` emits a pipeline
  file for your CI system; Stage 6 verifies the generated configuration. The
  GitHub Actions reference is at
  `packs/iac-terraform/.apm/skills/generate-iac/references/pipeline/github-actions.md`.

## Validated providers (v1)

| Provider | Status | Engine |
| --- | --- | --- |
| AWS (`hashicorp/aws`) | validated | terraform + tofu (both) |
| GCP (`hashicorp/google`) | validated | terraform |
| Databricks (`databricks/databricks`) | validated | terraform |
| Azure (`hashicorp/azurerm`) | experimental | terraform |
| Kubernetes workloads | experimental | terraform |
| Edge/CDN/DNS | experimental | terraform |
| HashiCorp platform (Vault, HCP) | experimental | terraform |
| Data platforms (Snowflake, etc.) | experimental | terraform |
| Observability vendors (Datadog, Grafana, etc.) | experimental | terraform |

---

Installing and upgrading live in [`../_shared/`](../_shared/).
