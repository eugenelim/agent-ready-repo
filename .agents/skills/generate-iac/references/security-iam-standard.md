# Security and IAM standard

> **Binding.** Every generated configuration must comply. Cite in the plan's
> standards-mapping table. On infra work, `security-reviewer` + the
> `config-misconfig` module are mandatory and non-skippable.

## Identity and access

- **Least-privilege inline per layer.** No wildcard policies (`*` actions or
  resources) without a documented exception in the governing ADR.
- **No long-lived static cloud credentials** — ever. Use short-lived workload
  identity per cloud:
  - AWS: IAM roles via IRSA (EKS) or instance profiles; assume roles via
    OIDC federation from CI (GitHub Actions / GitLab / Azure DevOps).
  - Azure: User-assigned managed identities for workloads; OIDC federation
    for CI pipelines.
  - GCP: Service accounts + Workload Identity for GKE; Direct Workload Identity
    Federation for CI (GitHub / GitLab).
- **Pipelines authenticate via OIDC only.** No static API keys, access keys,
  or service account key files checked into the repo or stored in CI secrets.
- **Credential tiering (release-loop requirement):** the ephemeral/autonomous
  zone's workload identity can assume **ephemeral-tier roles only** — scoped to
  the ephemeral environment's account/project/subscription. Never a role that
  can access prod.

## Data protection

- **Encryption at rest:** CMK (Customer-Managed Key) for `internal` and
  `confidential` classified data. AES-256 minimum. Cloud-native: AWS SSE-KMS;
  GCP CMEK; Azure SSE + CMK.
- **Encryption in transit:** TLS 1.2+ enforced. Reject plaintext endpoints.
- **Secrets in a manager, never in code.** Reference via data source:
  - AWS: `aws_secretsmanager_secret_version` or `aws_ssm_parameter`
  - GCP: `google_secret_manager_secret_version`
  - Azure: `azurerm_key_vault_secret`
- State backend must be encrypted at rest (S3 SSE-KMS / GCS CMEK / Azure SSE).
- `sensitive = true` on any output that contains a credential reference (even
  an ARN) — suppresses CLI display; does not encrypt state.

## CI/CD guardrails

Wire these into the CI pipeline as mandatory pre-apply gates:
- Static analysis: **Trivy** (replaces deprecated `tfsec`) + **Checkov**
- Policy-as-code: **OPA/Conftest** against plan JSON (see `policy-on-plan.md`)
  — or native cloud policy (AWS SCP / Azure Policy / GCP Org Policy) as a
  complementary layer
- Secret scanning: detect committed credentials before any plan/apply
- Note: **Sentinel is incompatible with OpenTofu**. OPA/Conftest is the only
  open-source policy path that works on both Terraform and OpenTofu engines.

## Checklist (review before merge)

- [ ] No static credentials in `.tf` files, CI environment variables, or
  committed `*.tfvars`.
- [ ] IAM roles/policies follow least-privilege; no wildcards without ADR.
- [ ] Pipelines use OIDC only; no static access keys.
- [ ] Sensitive outputs marked `sensitive = true`.
- [ ] Data at rest encrypted with CMK for internal/confidential data.
- [ ] TLS enforced on all data-in-transit endpoints.
- [ ] Trivy and Checkov (or equivalent) wired into CI as pre-merge gates.
- [ ] OPA/Conftest (or native cloud policy) as plan-JSON gate.
- [ ] Credential tiering: ephemeral-env identity cannot assume prod roles.
