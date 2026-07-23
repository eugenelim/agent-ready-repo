# Scalr remote execution — reference

> **Load ONLY when `platform = scalr`** — valid for both `engine = terraform`
> and `engine = opentofu`. Scalr is the pack's recommended remote execution
> option for OpenTofu targets.
>
> This file provides the platform *delta*: config block, auth, credential model,
> CI trigger notes, and bootstrap narrative. It composes with
> `references/pipeline/<ci>.md` (CI pipeline source of truth) and
> `references/providers/<cloud>.md` (cloud provider config). Those files do not
> change; this file documents what to add or omit for Scalr.

## Config block — `backend "remote"`

Scalr uses the standard `backend "remote"` block — **not** `cloud {}`.
The block lives in `backend.tf`.

```hcl
terraform {
  backend "remote" {
    hostname     = "<account-name>.scalr.io"
    organization = "<environment-name>"    # ← Scalr ENVIRONMENT name, not account

    workspaces {
      name = "<workspace-name>"
      # Alternatively: tags = ["<tag>"]
    }
  }
}
```

**Critical naming trap:** the `organization` field takes the **Scalr environment
name** (e.g. `production`, `staging`, `dev`) — **not the account name**. The
account name is encoded in `hostname` (`<account>.scalr.io`). Using the account
name in `organization` produces a confusing authentication error; it is the most
common misconfiguration when porting TFC configs to Scalr. Surface this warning
in `REMOTE_EXEC_SETUP.md`.

**Files to emit when `platform = scalr`:**
- `backend.tf` — with `backend "remote"` block above
- `versions.tf` — standard, no `cloud {}` block
- `provider.tf` — unchanged from vanilla shape
- **No `backend.hcl.example`** — unused (hostname and org are in `backend.tf`)

**Environment variable overrides:**

| Env var | Purpose |
| --- | --- |
| `TF_TOKEN_<account>_scalr_io` | API token. Encoding: dots → `_`, hyphens → `__`. E.g. account `myorg` (no hyphens): `TF_TOKEN_myorg_scalr_io`; hyphenated account `my-org`: `TF_TOKEN_my__org_scalr_io`. The double-underscore encoding ensures the name is a valid bash identifier. Required in CI. |
| `SCALR_TOKEN` | Scalr CLI-specific alternative to `TF_TOKEN_*` |
| `SCALR_HOSTNAME` | Scalr CLI: hostname |
| `SCALR_ACCOUNT` | Scalr CLI: account name |

**OpenTofu compatibility:** `backend "remote"` is a standard Terraform backend
protocol — not a HashiCorp-proprietary extension. Scalr accepts both the
`terraform` and `tofu` binaries via this backend. The `cloud {}` block
(Terraform-only) is never used with Scalr.

## Auth — token types

Scalr uses **personal tokens** and **service account tokens**. There is no
equivalent of HCP Terraform's organisation-token restriction — Scalr tokens are
user-scoped or service-account-scoped and can trigger runs within their
assigned permissions.

In CI, set `TF_TOKEN_<account>_scalr_io` to a **service account token** scoped
to the relevant environments and workspaces.

## Three-tier hierarchy

Scalr's hierarchy determines where variables, policies, and credentials live:

```
account            ← top-level; manages RBAC and OPA policies; hosts module registry
  └── environment  ← team-level grouping (maps to the "organization" field in backend block)
        └── workspace  ← execution unit; runs plans and applies
```

Variables, OPA policies, and credentials cascade downward (account →
environment → workspace). Any level can mark a value `final` to prevent
override by a lower scope — this enables a central security team to lock
credentials at account level and prevent teams from substituting their own.

## Credential model

### Preferred: provider integrations (OIDC federation)

Scalr's native cloud-provider credential management injects credentials into the
remote runner via OIDC federation at run time — no static key stored or rotated.

Configure in the Scalr UI under the environment → **Credentials**:

| Cloud | Provider integration |
| --- | --- |
| AWS | AWS provider integration (OIDC trust auto-managed by Scalr) |
| GCP | GCP provider integration (Workload Identity Federation) |
| Azure | Azure provider integration |

Set integrations at the **environment level** so all workspaces under that
environment inherit the credentials automatically.

This is the preferred model — it satisfies the pack's no-long-lived-keys
invariant. **Availability:** provider integrations are a paid-tier feature in
Scalr; verify your plan before relying on this model.

### Fallback: workspace / environment variables

When provider integrations are not available or not yet configured, set cloud
provider credentials as Scalr variables at the environment or workspace level.
Variable inheritance follows the three-tier cascade.

| Cloud | Variables (minimum) |
| --- | --- |
| AWS | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| GCP | `GOOGLE_CREDENTIALS` (JSON service-account key; mark sensitive) |
| Azure | `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID` |

Mark secret-valued variables as **sensitive** — they become write-only.
Set at the **environment level** (not workspace level) so all workspaces in the
environment inherit them automatically.

**Variable `final` flag:** a parent scope can set a variable as `final` to
prevent workspace-level override — useful for enforcing a shared credential
across a team's workspaces.

## Remote operations model

In CLI-driven mode (`terraform plan` / `terraform apply` run in CI with
`backend "remote"` pointing to Scalr):
- Local environment variables are **not forwarded** to the remote runner
- Local credential files are **not forwarded**
- Scalr injects provider-integration credentials (or workspace variables) at run
  time
- Logs stream back to the terminal

## OPA policy enforcement

Scalr supports OPA only — no Sentinel. Policies are written in Rego and
registered via **policy groups** in the Scalr UI (linked to a VCS repository
containing `.rego` files) or through the Scalr API.

**Two enforcement points:**
- **Pre-plan:** runs before the plan is generated; input includes workspace
  metadata and user/VCS info. Blocks before any cloud API calls.
- **Post-plan:** runs after the plan; input includes the full plan JSON
  (`tfplan`). Can evaluate resource-level changes.

**Three enforcement levels:**
- `hard-mandatory` — blocks unconditionally; no override path
- `soft-mandatory` — blocks but an authorised user can override
- `advisory` — warning only; run proceeds

Policies are defined at account level, assigned to environments, and cascade to
workspaces. The same Rego rules in `policy/` used by Conftest in CI can also be
deployed to Scalr — a single policy corpus covers both paths.

## CI trigger notes — platform delta

When `backend "remote"` points to a Scalr hostname, `terraform plan` and
`terraform apply` in CI proxy to Scalr. The CI YAML becomes simpler, same
pattern as HCP Terraform:

**Removed vs vanilla CI:**
- No OIDC role assumption to the state backend (state lives in Scalr)
- No `-backend-config backend.hcl` flag to `terraform init` (backend is in
  `backend.tf`)
- No cloud-provider OIDC role assumption in CI — cloud auth is handled on the
  remote runner via provider integrations (OIDC) or environment/workspace
  variables

**Unchanged vs vanilla CI:**
- Human approval gate before apply
- `fmt -check` → `validate` → `plan` → Conftest → Trivy steps

**Composing with `references/pipeline/<ci>.md`:** that file is the pipeline
source of truth. This file provides the Scalr delta only — omit the backend
OIDC step, remove `-backend-config`, add `TF_TOKEN_<account>_scalr_io` to CI
secrets.

## Bootstrap narrative

For a new Scalr workspace (no pre-existing remote state to migrate):

1. **Create the hierarchy:** account already exists → create an environment
   (e.g. `dev`) in the Scalr UI → create a workspace under the environment.
2. **Configure credentials** at the environment level:
   - Preferred: set up provider integrations for the target cloud.
   - Fallback: add cloud provider variables at the environment level.
3. **Set the platform token** in the CI secret store:
   `TF_TOKEN_<account>_scalr_io = <service-account-token>`
4. **Verify `backend.tf`** uses the **environment name** (not the account name)
   in the `organization` field.
5. **Run `terraform init`** (or `tofu init`) — connects to Scalr and registers
   the workspace.
6. **First `terraform plan`** runs remotely on Scalr.

There is no object-store chicken-and-egg problem. The backend IS the SaaS
platform — no bucket to provision before init.
