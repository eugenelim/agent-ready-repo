# `iac-terraform` pack

> **Opt-in, repo-scope.** Not included in any default profile — install explicitly:
> `agentbundle install iac-terraform`

Turn a plain-language infrastructure intent into governed, best-practice
Terraform/OpenTofu — decision-record-driven, cloud-agnostic, and human-gated
at apply time.

## Skills

| Skill | Trigger | What it does |
| --- | --- | --- |
| `generate-iac` | "provision X", "create Terraform for", "generate IaC for" | Governance-first authoring: ADR gate → spec → plan → tasks → Terraform → verify. Stops at a digest-pinned `plan` (the G4 handoff). Never runs `apply`. |
| `reconcile-iac` | "reconcile my infrastructure", "check for drift", "drift audit" | `plan`-based drift audit → proposed disposition → route. Two triggers: before-change preflight (mandatory) and on-demand/scheduled. Never autonomously applies. |

## Design

- **Zero seeds** — all provider configs, pipeline YAML, and OPA rules are
  generated into the adopter repo from progressive references; the pack ships
  none.
- **Zero agents** — reuses `core`'s `adversarial-reviewer`, `quality-engineer`,
  and `security-reviewer` via the existing orchestrator-inlining mechanism.
- **Dual-engine** — Terraform and OpenTofu share an HCL-compatible baseline;
  divergences are in `references/opentofu-differences.md`, loaded only when
  `engine = opentofu`.
- **Loop-arc aligned** — `generate-iac` targets the G4 handoff (`plan`);
  `apply` is `release-loop`'s act on ephemeral environments, human-gated at
  irreversible exits. Where `release-loop` is absent, the generated CI pipeline
  is the degraded-mode fallback.
- **Category taxonomy** — provider coverage tracks the Terraform registry's
  own category list (MECE); each category gets a fit-for-purpose reference,
  not the cloud four-file mold.

## Validated in v1 (D5)

| Provider | Status | Note |
| --- | --- | --- |
| AWS | **validated** | Passes `init -backend=false && fmt -check && validate` on both `terraform` and `tofu` |
| GCP | **validated** | Passes `init -backend=false && fmt -check && validate` on `terraform` |
| Databricks | **validated** | Passes `init -backend=false && fmt -check && validate` on `terraform` |
| Azure | contract-complete | Unvalidated in v1 — stamped **experimental** |
| All other categories | contract-complete | Stamped **experimental — not validated in v1** |

## Dependencies

- `core` ^0.1 — infra-verification, operational-safety, security-checklists,
  contract-acquisition, and the three forked-context reviewers
- `governance-extras` ≥0.6 — governance-index template, new-adr infra mode

## Guides

Full user-facing documentation: [`docs/guides/iac-terraform/`](../../../../docs/guides/iac-terraform/)

---

*Establishing precedent: RFC-0065 (D2 charter exception — opt-in accelerator
packs for common tech stacks are explicitly in scope). Future tool-specific
packs are judged against this RFC.*
