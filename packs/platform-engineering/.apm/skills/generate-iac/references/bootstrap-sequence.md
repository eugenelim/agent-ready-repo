# Bootstrap sequence — state-backend chicken-and-egg

> Load when planning the `bootstrap/` layer before a remote state backend
> exists. Backend preparation is distinct from governance discovery; it is
> never a prerequisite for resolving governing sources.

## The problem

The layered layout (bootstrap → foundation → platform → app) uses remote state
from layer 1 onward. But the bootstrap layer *creates* the remote state backend —
so it can't use it before it exists. Running `terraform init` against a remote
backend when the bucket doesn't yet exist fails with a credentials or
bucket-not-found error.

**Resolution: bootstrap runs with local state on the first apply, then migrates.**

## Authoring boundary and release phases

Standalone authoring prepares backend configuration and a reviewed saved plan.
Never run or emit apply or destroy commands. Use
[infrastructure-review.md](infrastructure-review.md) for state-impact and recovery
review; stop when backend identity or migration prerequisites are uncertain.

Actual backend creation and state migration belong to a separately authorized
release workflow, after the direct authoring checks. That workflow has two phases:

1. Create the state bucket, OIDC provider and CI roles using local state, with
   an isolated target and human approval. Protect local state from the outset:
   ignore `bootstrap/terraform.tfstate*` and `bootstrap/.terraform/`.
2. Once backend creation is verified, restore the remote backend configuration
   and migrate the protected local state under separate authorization. Verify
   identity and state continuity before planning subsequent layers.

Do not migrate partial or uncertain state to work around a failed release check.
No optional integration may replace a refusal or failure with a weaker fallback.

## Per-cloud backend-hcl.example content

Prepare `bootstrap/backend.hcl.example` with placeholders. The separately
authorized release workflow supplies real backend values in a git-ignored file.

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

## Recovery — partial release

A failed backend creation may leave real resources and local state. Stop and
report the partial state to the release owner. Recovery and migration require
that workflow's authorization; this authoring skill only updates configuration
and reviews a new saved plan after the state identity is confirmed.
