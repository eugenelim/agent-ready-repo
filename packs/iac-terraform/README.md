# IaC (Terraform)

Your agent can turn a plain-language infrastructure request into reviewed Terraform or OpenTofu, and stop at a plan you approve.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it from inside the repository where your infrastructure code lives:

```bash
cd path/to/your-repo
agentbundle install --pack iac-terraform
```

You also need [Core](../core/README.md), [Governance Extras](../governance-extras/README.md), and the `terraform` or `tofu` command on your path.

## What your agent can do

- Record the infrastructure decision as an ADR before it writes any code.
- Write a spec and schema-grounded `.tf` files from your intent, with format, validate, policy, and security checks.
- Stop at a `terraform plan` with a pinned digest, for you to review.
- Audit drift against the last plan and propose accept, correct, or defer for each resource.
- Check an incoming infrastructure diff against your ADRs.

## Skills

- **`generate-iac`** — Decides, specifies, writes the Terraform, and stops at a pinned plan. It never runs `apply`.
- **`reconcile-iac`** — Audits drift, runs a pre-change check, and checks a diff against your ADRs. It never applies on its own.

## Works with

Works with Claude Code. It requires [Core](../core/README.md) and [Governance Extras](../governance-extras/README.md). AWS, GCP, and Databricks are validated. Azure and other providers are marked experimental. See [Change infrastructure](../../guides/iac-terraform/README.md) and [Release Engineering](../release-engineering/README.md) for shipping the change.

## Questions

**Does it run `terraform apply`?** No. It stops at a reviewed plan. You, or your CI pipeline, run apply. Deleting resources and migrating data always wait for you.

**Does it touch my state files or secrets?** No. State, backends, and locking stay with your pipeline. It never generates, stores, or reads a secret. Reference them as environment variables or Vault references.

**Does it call my cloud?** No. It reads provider schemas and registries through `terraform init`. It makes no direct cloud API calls.

**Terraform or OpenTofu?** Both. They share a baseline, and OpenTofu differences load only when you choose it.

## Details

Scope: repo (default) · Version: 0.1.12 · Source: [packs/iac-terraform](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/iac-terraform)
