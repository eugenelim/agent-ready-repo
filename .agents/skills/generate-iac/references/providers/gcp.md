# GCP provider reference — validated in v1

**Status: validated** — passes `terraform init -backend=false && terraform fmt
-check && terraform validate` on `terraform`. See `examples/gcp/` for the
worked example.

## Four-file contract

### versions.tf

```hcl
terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}
```

### provider.tf

```hcl
provider "google" {
  project = var.project_id
  region  = var.region
}
```

For Workload Identity Federation (GitHub Actions OIDC):
Do not set `credentials` in the provider block. Instead use environment
variables (`GOOGLE_APPLICATION_CREDENTIALS`) or Direct Workload Identity
Federation (preferred — no credential file on disk).

### backend.tf

```hcl
terraform {
  backend "gcs" {}
}
```

### backend.hcl.example

```hcl
bucket = "<your-state-bucket>"
prefix = "<system>/<env>"
```

GCS backend uses object metadata locks for state locking — no separate
lock table required.

## Networking equivalents

| Concept | GCP resource |
| --- | --- |
| Network | `google_compute_network` (global — not regional) |
| Segment | `google_compute_subnetwork` (regional) |
| Firewall | `google_compute_firewall` |
| Private service access | `google_compute_private_service_connect_endpoint`, `google_service_networking_connection` (Private Service Connect / Private Google Access) |
| Front door | `google_compute_backend_service` + `google_compute_url_map` + `google_compute_security_policy` (Cloud Armor), or `google_api_gateway_api` |

## GCP VPC is global — a key difference

GCP VPC networks span all regions. Subnetworks are regional. A single VPC
can serve multiple regions without peering. This differs from AWS/Azure where
VPCs/VNets are regional-scoped. When designing the network layout, the
`google_compute_network` has no `region` argument.

## Labels

GCP uses `labels` (not `tags`). Apply via `default_labels` in the provider
block (google provider ≥ 4.x) using `local.standard_tags`:

```hcl
provider "google" {
  project        = var.project_id
  region         = var.region
  default_labels = local.standard_tags
}
```

Constraints:
- Keys and values must match `[a-z0-9_-]` (lowercase, numbers, hyphens,
  underscores only)
- Max 64 characters per key and value
- Max 64 labels per resource

The `managed-by` key with value `terraform` is valid. Keys like `cost-center`
(with hyphen) are valid in GCP labels.

## OIDC / workload-federation for CI

Direct Workload Identity Federation (no service account key file):

```hcl
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-${var.environment}"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
  attribute_condition = "assertion.repository == \"<org>/<repo>\""
}

resource "google_service_account_iam_member" "github_binding" {
  service_account_id = google_service_account.ci.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/<org>/<repo>"
}
```

## Account/tenant isolation model

**Recommended:** separate GCP project per environment (dev/staging/prod).
Each project has its own state bucket, service accounts, and IAM bindings.
Credential tiering: the CI service account for the ephemeral env project
must have no IAM bindings to prod project resources.

## Managed Kubernetes (GKE)

GKE cluster provisioning uses `google_container_cluster` and
`google_container_node_pool` (in this reference).
In-cluster resource management uses `kubernetes` / `helm` providers
(see `providers/kubernetes-workloads.md`).
