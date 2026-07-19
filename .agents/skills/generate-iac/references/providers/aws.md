# AWS provider reference — validated in v1

**Status: validated** — passes `terraform init -backend=false && terraform fmt
-check && terraform validate` on both `terraform` and `tofu` (D5). See
`examples/aws/` for the worked example.

## Four-file contract

### versions.tf

```hcl
terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

### provider.tf

```hcl
provider "aws" {
  region = var.region

  default_tags {
    tags = local.standard_tags
  }
}
```

`default_tags` applies the mandatory tagging standard to all AWS resources
automatically. No need to repeat tags on each resource (though resources can
add resource-specific tags by merging with `local.standard_tags`).

### backend.tf

```hcl
terraform {
  backend "s3" {}
}
```

Empty partial backend block — values supplied via `backend.hcl` at init time.

### backend.hcl.example

```hcl
bucket         = "<your-state-bucket>"
key            = "<system>/<env>/terraform.tfstate"
region         = "<region>"
use_lockfile   = true
encrypt        = true
kms_key_id     = "<your-kms-key-arn>"
```

`use_lockfile = true` — native S3 lockfile (GA in Terraform 1.11 / OpenTofu 1.7+).
**Do NOT add a `dynamodb_table` — that mechanism is deprecated.** Requires
`required_version >= 1.11` (Terraform) or `>= 1.7` (OpenTofu) in `versions.tf`.

## Networking equivalents

| Concept | AWS resource |
| --- | --- |
| Network | `aws_vpc` |
| Segment | `aws_subnet` |
| Firewall | `aws_security_group`, `aws_vpc_security_group_ingress_rule`, `aws_network_acl` |
| Private service access | `aws_vpc_endpoint` (Gateway type for S3/DynamoDB; Interface type for others) |
| Front door | `aws_lb` (ALB) + `aws_wafv2_web_acl`, or `aws_api_gateway_rest_api` |

## OIDC / workload-federation for CI

GitHub Actions OIDC trust policy:

```hcl
data "aws_iam_policy_document" "github_oidc_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:<org>/<repo>:environment:<env>"]
    }
  }
}
```

**OIDC `sub` format note (2026-07-15):** GitHub changed the `sub` claim for
repos created on or after 2026-07-15 to use an immutable numeric repository ID.
Trust policies must use the current form: `repo:<org-name>/<repo-name>:...` for
older repos, or the numeric-ID form for new repos. A legacy name-only `sub` will
**silently fail** on new-format repos — test the OIDC claim before deploying.

## Account/tenant isolation model

**Recommended (default):** separate AWS account per environment (dev/staging/
prod). Drives OIDC trust policy `Condition` to scope to the environment's
account; each environment has its own state bucket.

**Alternative:** shared account + Terraform workspaces. Higher blast-radius;
workload isolation via IAM boundaries rather than account boundaries.

Document the chosen model in the `state` ADR.

## Credential tiering

The ephemeral-env CI role must be scoped to the ephemeral environment's account
and restricted to the resources it creates/modifies. It must not have `sts:AssumeRole`
to any prod-account role.

## Managed Kubernetes (EKS)

EKS cluster provisioning uses `aws_eks_cluster` (in this reference).
In-cluster Kubernetes resource management uses `kubernetes` / `helm` providers
(see `providers/kubernetes-workloads.md`).

## State locking note

Native S3 object-level locking (`use_lockfile = true`) is GA in Terraform 1.11
and OpenTofu 1.7+. It replaces the DynamoDB lock table pattern entirely — no
DynamoDB table resource is needed. **Raise `required_version` to `>= 1.11` (Terraform)
or `>= 1.7` (OpenTofu) before using `use_lockfile = true` in production** — the
validated worked example uses `>= 1.6` to keep the test runnable on both engines
without engine-specific overrides (`init -backend=false` never exercises locking).
