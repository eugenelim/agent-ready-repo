# Tagging standard

> **Binding.** All six mandatory keys must be present on every taggable
> resource. Enforced by the `managed-by` OPA deny rule. Cite in the
> plan's standards-mapping table.

## Six mandatory keys

| Key | Values | Notes |
| --- | --- | --- |
| `environment` | `dev`, `staging`, `prod` (or org-specific) | Must match the environment being deployed to |
| `owner` | team name or email | Identifies responsible team for cost and incident routing |
| `cost-center` | org cost center ID | Required for cost allocation |
| `managed-by` | `terraform` | **Always literal `terraform`** — enforced by OPA rule 3 |
| `system` | system/service name (kebab-case) | Maps to the `name_prefix` in the Terraform config |
| `data-classification` | `public`, `internal`, `confidential` | Drives encryption-at-rest requirements (see security-iam-standard) |

## Implementation — emit as a `locals` block

```hcl
locals {
  standard_tags = {
    environment          = var.environment
    owner                = var.owner
    "cost-center"        = var.cost_center
    "managed-by"         = "terraform"
    system               = var.system
    "data-classification" = var.data_classification
  }
}
```

## Per-cloud application

**AWS** — use `default_tags` in the provider block (applies to all resources
automatically via the AWS provider):

```hcl
provider "aws" {
  region = var.region
  default_tags {
    tags = local.standard_tags
  }
}
```

**Azure** — merge into each resource's `tags` argument. Also tag the resource
group itself:

```hcl
resource "azurerm_resource_group" "main" {
  name     = "${var.system}-${var.environment}-rg"
  location = var.location
  tags     = local.standard_tags
}

resource "azurerm_storage_account" "main" {
  # ...
  tags = local.standard_tags
}
```

**GCP** — use `default_labels` in the provider block (applies to all resources
automatically, google provider ≥ 4.x):

```hcl
provider "google" {
  project        = var.project_id
  region         = var.region
  default_labels = local.standard_tags
}
```

Note: GCP labels are lowercase only — uppercase chars in values are rejected.
For resources that accept additional resource-specific labels, merge with
`merge(local.standard_tags, { resource-label = "value" })`.

GCP label constraints: keys and values must match `[a-z0-9_-]{1,63}`. The
`cost-center` key is valid (hyphen allowed); ensure values comply.

## Checklist

- [ ] All six keys present on every taggable resource.
- [ ] `managed-by = "terraform"` is literal — no variable.
- [ ] `data-classification` value is one of `public`, `internal`, `confidential`.
- [ ] AWS: `default_tags` used in the provider block.
- [ ] GCP: label values are lowercase and ≤63 chars.
- [ ] Tags enforced by the policy-as-code `deny-managed-by-tag` rule.
