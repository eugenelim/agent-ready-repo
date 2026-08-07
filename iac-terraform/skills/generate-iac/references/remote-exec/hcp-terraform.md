# HCP Terraform remote execution — reference

> **Load ONLY when `platform = hcp-terraform`** — not valid for OpenTofu targets
> (`cloud {}` is a Terraform-only feature; use `scalr.md` for OpenTofu).
>
> This file provides the platform *delta*: config block, auth, credential model,
> CI trigger notes, and bootstrap narrative. It composes with
> `references/pipeline/<ci>.md` (CI pipeline source of truth) and
> `references/providers/<cloud>.md` (cloud provider config). Those files do not
> change; this file documents what to add or omit for HCP Terraform.

## Config block — `cloud {}`

The `cloud {}` block replaces `backend.tf` and `backend.hcl.example` entirely.
It lives inside the `terraform {}` block in `versions.tf` (alongside
`required_providers`). Requires Terraform ≥ 1.1.

```hcl
terraform {
  required_version = ">= 1.1.0"
  required_providers { /* ... */ }

  cloud {
    organization = "<org-name>"        # or TF_CLOUD_ORGANIZATION
    # hostname = "..."  # omit for SaaS (app.terraform.io); set only for Terraform Enterprise (self-hosted)

    workspaces {
      name    = "<workspace-name>"   # or TF_WORKSPACE
      # Alternatively: tags = ["<tag>"]
      # project = "<project-name>"  # or TF_CLOUD_PROJECT
    }
  }
}
```

**Files to emit when `platform = hcp-terraform`:**
- `versions.tf` — with `cloud {}` block above
- `provider.tf` — unchanged from vanilla shape
- **No `backend.tf`** — the `cloud {}` block replaces it
- **No `backend.hcl.example`** — unused with `cloud {}`

**Environment variable overrides** — all `cloud {}` fields can be set via env
vars, making the HCL environment-agnostic:

| Env var | Overrides | Note |
| --- | --- | --- |
| `TF_TOKEN_app_terraform_io` | — | API token (dots → underscores). Required in CI. |
| `TF_CLOUD_ORGANIZATION` | `cloud.organization` | |
| `TF_CLOUD_HOSTNAME` | `cloud.hostname` | For Terraform Enterprise (self-hosted); leave unset for `app.terraform.io` SaaS |
| `TF_WORKSPACE` | `workspaces.name` | |
| `TF_CLOUD_PROJECT` | `workspaces.project` | |

With all values in env vars (`TF_CLOUD_ORGANIZATION`, `TF_WORKSPACE`, `TF_TOKEN_app_terraform_io`), a minimal `versions.tf` config is:

```hcl
terraform {
  cloud {}
}
```

## Auth — token types and capabilities

**Critical guard:** organisation tokens cannot trigger runs or create
configuration versions. CI workflows must use a **team token** or **user token**.

| Token type | Trigger runs? | Create config versions? | Correct for CI? |
| --- | --- | --- | --- |
| User token | ✓ | ✓ | ✓ (scoped to user perms) |
| Team token | ✓ | ✓ | ✓ (recommended for CI) |
| **Organisation token** | **✗** | **✗** | **✗ — fails silently or 403** |

Set `TF_TOKEN_app_terraform_io` in the CI secrets store to a **team token**
scoped to the target workspace(s). Never use an organisation token in CI.

## Credential model

### Preferred: Dynamic Provider Credentials (OIDC federation)

HCP Terraform's Dynamic Provider Credentials (verify current tier requirements
with HashiCorp — historically Plus and above; tier gating may have changed)
use OIDC to federate with the cloud provider. The remote runner exchanges a
short-lived JWT for a cloud credential at run time — no static key stored or
rotated.

Configure in HCP Terraform workspace settings → **Provider Credentials**:

| Cloud | Dynamic credential mechanism |
| --- | --- |
| AWS | OIDC trust policy in AWS IAM; no `AWS_ACCESS_KEY_ID` needed |
| GCP | Workload Identity Federation; no `GOOGLE_CREDENTIALS` needed |
| Azure | Workload Identity with federated credential; no `ARM_CLIENT_SECRET` needed |

This is the preferred model — it aligns with the pack's no-long-lived-keys
invariant. Document the tier requirement in `REMOTE_EXEC_SETUP.md`.

### Fallback: workspace environment variables

When Dynamic Provider Credentials are not available or not yet configured, set
cloud provider credentials as **workspace environment variables** inside HCP
Terraform. These are injected into the remote runner at run time. They are
**not** read from the local shell, CI runner environment, or credential files.

| Cloud | Workspace env vars (minimum) |
| --- | --- |
| AWS | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| GCP | `GOOGLE_CREDENTIALS` (JSON service-account key; mark sensitive) |
| Azure | `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID` |

Mark any secret-valued variable as **sensitive** in the workspace UI — it becomes
write-only and is never displayed in logs or the API.

## Remote operations model

In CLI-driven mode (`terraform plan` / `terraform apply` run in CI with `cloud {}`
present):
- Local environment variables are **not forwarded** to the remote runner
- Local credential files (`~/.aws/credentials`, `~/.config/gcloud/`, etc.) are
  **not forwarded**
- The plan and apply run on a HCP Terraform-managed ephemeral VM; logs stream
  back to the terminal
- Cloud-provider credentials are **not** sourced from the CI runner — they come
  from Dynamic Provider Credentials (OIDC on the remote VM) or workspace env
  vars set in the HCP Terraform UI. No cloud-provider OIDC role assumption is
  needed in the CI workflow.

## Run states to handle

| State | Meaning | Action |
| --- | --- | --- |
| `pending` | Queued | Poll |
| `planning` | Running plan | Poll |
| `cost_estimating` | Estimating cost | Poll |
| `policy_checking` | OPA / Sentinel policies evaluating | Poll |
| **`needs_confirmation`** | Plan clean; apply waiting for approval | Human reviews plan then confirms or discards |
| **`policy_override`** | Soft-mandatory policy failed | Authorised user overrides or discards; hard-mandatory blocks unconditionally |
| `applying` | Running apply | Poll |
| `applied` | Complete | Success |
| `planned_and_finished` | Plan-only run done | Success (no apply requested) |
| `plan_errored` | Plan failed | Surface error; stop |
| `apply_errored` | Apply failed | Surface error; stop |
| `discarded` / `canceled` | Aborted | Surface to human |

## Policy enforcement

HCP Terraform supports OPA and Sentinel natively. This pack uses **OPA/Conftest**
in the CI pipeline — not HCP Terraform's native policy evaluation. The two
coexist independently:

- **Conftest in CI (pack's mandated path):** runs in the CI pipeline as a step,
  before or after the remote plan, using the same `.rego` rules from `policy/`.
  Unaffected by HCP Terraform's policy tier.
- **HCP Terraform native OPA (optional, paid tier):** runs post-plan inside the
  platform; surfaces via `policy_checking` run state. Can augment the Conftest
  pass but does not replace it.

**Never emit Sentinel** — it is Terraform-only, requires an HCP Terraform paid
tier, and is incompatible with the pack's engine-neutral and open-source-policy
invariants.

## CI trigger notes — platform delta

When `cloud {}` is present, `terraform plan` and `terraform apply` in CI proxy
to HCP Terraform. The CI YAML becomes simpler:

**Removed vs vanilla CI:**
- No OIDC role assumption to the state backend (state lives in HCP Terraform)
- No `-backend-config backend.hcl` flag to `terraform init`
- No cloud-provider OIDC role assumption in CI — cloud auth is handled on the
  remote runner via Dynamic Provider Credentials or workspace env vars

**Unchanged vs vanilla CI:**
- Human approval gate before apply (GitHub environment protection /
  Azure DevOps approval / GitLab manual job)
- `fmt -check` → `validate` → `plan` → Conftest → Trivy steps

**Composing with `references/pipeline/<ci>.md`:** that file is the pipeline
source of truth and defines the full YAML structure. This file provides the
HCP Terraform delta only — omit the backend OIDC step, remove
`-backend-config`, add `TF_TOKEN_app_terraform_io` to CI secrets.

## Bootstrap narrative

For a new HCP Terraform workspace (no pre-existing remote state to migrate):

1. **Create the workspace** in the HCP Terraform UI or via the `hashicorp/tfe`
   Terraform provider (if provisioning the workspace itself via Terraform).
2. **Configure credentials** in workspace settings:
   - Preferred: enable Dynamic Provider Credentials for the target cloud.
   - Fallback: add workspace environment variables for cloud provider credentials.
3. **Set the platform token** in the CI secret store:
   `TF_TOKEN_app_terraform_io = <team-token>` (never an organisation token).
4. **Run `terraform init`** with `cloud {}` in `versions.tf` — connects to HCP
   Terraform and registers the workspace.
5. **First `terraform plan`** runs remotely on HCP Terraform. The plan runs on
   the platform's infrastructure, not the CI runner.

There is no object-store chicken-and-egg problem (`bootstrap-sequence.md` covers
the object-store case). The backend IS the SaaS platform — no bucket to provision
before init.
