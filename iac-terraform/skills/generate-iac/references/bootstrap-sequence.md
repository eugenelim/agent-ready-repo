# Bootstrap sequence — state-backend chicken-and-egg

> Load this reference when initialising the `bootstrap/` layer for the first
> time (no remote state backend exists yet). This is the #1 first-apply failure
> pattern in layered Terraform — skipping or guessing through it silently breaks
> all subsequent layers.

## The problem

The layered layout (bootstrap → foundation → platform → app) uses remote state
from layer 1 onward. But the bootstrap layer *creates* the remote state backend —
so it can't use it before it exists. Running `terraform init` against a remote
backend when the bucket doesn't yet exist fails with a credentials or
bucket-not-found error.

**Resolution: bootstrap runs with local state on the first apply, then migrates.**

## Two-phase procedure

### Phase 1 — Create the backend with local state

1. **Temporarily disable the remote backend** in `bootstrap/backend.tf`:

   ```hcl
   # Phase 1 only — remove after migration
   terraform {}
   ```

2. Run `terraform init` (writes `terraform.tfstate` locally).

3. Run `terraform plan -out=bootstrap.tfplan` — review. The plan should create
   only the state bucket, OIDC provider, and CI roles.

4. Run `terraform apply bootstrap.tfplan` — the backend infrastructure is live.
   A local `terraform.tfstate` now exists.

5. Immediately extend `.gitignore` — never commit the local state:

   ```
   bootstrap/terraform.tfstate*
   bootstrap/.terraform/
   ```

### Phase 2 — Migrate local state to the remote backend

6. **Restore the remote backend block** in `bootstrap/backend.tf`:

   ```hcl
   terraform {
     backend "s3" {}    # or "gcs" / "azurerm" — partial config
   }
   ```

7. Run `terraform init -migrate-state -backend-config=backend.hcl`.
   Terraform detects existing local state and prompts to copy it to the remote
   bucket. Answer yes.

8. Verify with `terraform plan` (should show no changes — state matches live).

9. **Commit** `backend.tf` with the restored backend block and the updated
   `.gitignore`. Do **not** commit `terraform.tfstate` or `.terraform/`.

## Per-cloud backend-hcl.example content

Copy the appropriate block to `bootstrap/backend.hcl` (git-ignored) before
Phase 1 `terraform init`. The `-migrate-state` step reads it automatically.

**AWS — S3:**
```hcl
bucket       = "<state-bucket-name>"
key          = "bootstrap/terraform.tfstate"
region       = "<region>"
encrypt      = true
kms_key_id   = "alias/terraform-state"
use_lockfile = true    # Terraform >= 1.11 or OpenTofu >= 1.7
```

**GCP — GCS:**
```hcl
bucket = "<state-bucket-name>"
prefix = "bootstrap"
```

**Azure — Azure Blob:**
```hcl
resource_group_name  = "<rg>"
storage_account_name = "<sa>"
container_name       = "tfstate"
key                  = "bootstrap.tfstate"
```

## What the bootstrap layer creates (minimum viable)

| Resource | AWS | GCP | Azure |
| --- | --- | --- | --- |
| State bucket | S3 + versioning + SSE-KMS + lifecycle | GCS + versioning + CMEK | Storage account + blob container |
| OIDC provider | `aws_iam_openid_connect_provider` | Workload Identity Pool + Provider | Azure AD app + federated credential |
| CI role(s) | `aws_iam_role` (plan role + apply role, separate) | Service account per role | Managed identity |

Bootstrap does **not** create VPCs, compute, databases, or application resources
(those belong to foundation / platform / app layers).

## Recovery — partial apply

If the bootstrap apply failed mid-way, do **not** run `terraform init -migrate-state`
yet. First re-run `terraform apply` (Phase 1) to converge the partial state, then
verify resources exist in the cloud console, then proceed to Phase 2. A
partially-applied state migrated to remote state is valid — Terraform tracks what
was created.
