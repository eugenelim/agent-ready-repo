# Terraform best-practice standard

> **Binding.** Every generated module must comply with this standard. Cite which
> rule applies in the plan's standards-mapping table.

## Layered layout

```
bootstrap/      # one-time: remote state backend, OIDC provider, org-level IAM
foundation/     # VPC / network + shared DNS + cross-account roles
platform/       # EKS/GKE/AKS + databases + message queues + secrets store
app/            # workload compute + load balancer + service accounts
modules/        # reusable modules composed by the layers above
```

Each layer has **isolated remote state** — a layer reads another layer's
outputs via `terraform_remote_state` data sources or shared variable files;
it never manages another layer's resources. Deploy layers *compose* modules;
they do not inline resource blocks directly.

## Per-unit file structure

Every layer and module contains:
- `main.tf` — resources and data sources
- `variables.tf` — all inputs typed + described + validated
- `outputs.tf` — all outputs typed; sensitive outputs marked `sensitive = true`
- `versions.tf` — `required_version` + `required_providers`
- `backend.tf` (layers only) — empty partial backend block for the cloud's backend service
- `README.md` — purpose, inputs table, outputs table, usage example

## Naming

`name_prefix = <system>-<env>` for all resource names. Prevents collision
across environments. Never hardcode a fixed resource name.

## State

- **Remote state with locking.** Partial backend config in `backend.tf`;
  per-environment values in `backend.hcl` (committed) or passed via `-backend-config`.
- **AWS:** `use_lockfile = true` (GA in Terraform 1.11) — the native S3 lockfile.
  **Do NOT emit a DynamoDB lock table** — deprecated since Terraform 1.11.
- **GCP:** GCS backend with locking via object-metadata locks.
- **Azure:** Azure Blob backend with state locking.
- Commit `*.terraform.lock.hcl` — regenerate per engine at `init`.
- Never commit `*.tfstate`, `*.tfstate.backup`, or `.terraform/`.

## Version pinning

- `required_version` — use `>= 1.11` (Terraform) or `>= 1.7` (OpenTofu) when
  targeting AWS with native S3 locking (`use_lockfile = true`). Use `>= 1.6`
  for GCP/Azure/other providers, or as the dual-engine baseline floor.
- Provider version constraints — use `~>` (pessimistic constraint) to allow
  patch releases: `~> 5.0` allows 5.x but not 6.0.
- Commit `.terraform.lock.hcl` with the lock file for reproducibility.

## Variables

- Every variable: `type`, `description`, `validation` block where constrained.
- Sensitive variables marked `sensitive = true`.
- Never provide a `default` for secrets — require explicit supply via
  `TF_VAR_*` or CI vault injection.
- Commit `terraform.tfvars.example` with placeholder values.
- **`*.tfvars` must be git-ignored** (except `*.tfvars.example`).
- Supply real values via `TF_VAR_*` from CI vaults or the secret manager.
  Never commit a `terraform.tfvars` with real values.

## Secrets

- **No secrets in code or state inputs.**
- `sensitive = true` suppresses CLI display only — sensitive output values are
  stored in plaintext in the state file. Never output raw credentials; output
  only references/ARNs.
- Encrypt the state backend at rest: S3 SSE-KMS; GCS CMEK; Azure Storage
  Service Encryption + CMK.
- Reference secrets from a manager (AWS Secrets Manager / GCP Secret Manager /
  Azure Key Vault) via a data source — never hardcode them.

## IAM

- Least-privilege inline per layer — no god roles or wildcard policies without
  a documented exception in the governing ADR.
- No long-lived static credentials — use short-lived workload identity
  (see `security-iam-standard.md`).
- Everything tagged per the tagging standard.

## `fmt` and `validate`

- `terraform fmt` (or `tofu fmt`) must pass with zero changes.
- `terraform validate` (or `tofu validate`) must be clean before merge.

## Anti-patterns to reject (never emit)

| Anti-pattern | Why |
| --- | --- |
| Monolithic state | Blast radius: one failing apply blocks everything |
| God IAM roles / wildcard policies | Violates least-privilege; fails security review |
| Hardcoded region or account ID | Breaks environment promotion |
| `0.0.0.0/0` ingress in security groups | Fails networking-standard and OPA gate |
| Inline secrets in `.tf` or committed `*.tfvars` | Credentials in version control |
| `count`-churn where `for_each` is clearer | Causes resource replacement on index shift |
| Agent-run `apply` / `-auto-approve` without a human gate | Violates loop-arc contract |
| DynamoDB lock table for AWS state | Deprecated since Terraform 1.11; use native S3 lockfile |
| Referencing `tfsec` as a scanner | Merged into Trivy in 2023; cite Trivy instead |
