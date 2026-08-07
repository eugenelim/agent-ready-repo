# Azure provider reference — experimental, not validated in v1

> **experimental — not validated in v1.** This reference is `contract-complete`
> but no worked example has passed `init -backend=false && fmt -check &&
> validate`. Treat as a starting point; verify the four-file contract produces
> valid HCL for your Azure configuration before relying on it.
>
> Named maintainer: eugenelim. Deprecation path: if this reference is not
> validated by v1.1, it will be marked deprecated.

## Four-file contract

### versions.tf

```hcl
terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}
```

### provider.tf

```hcl
provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
}
```

OIDC authentication for GitHub Actions:

```hcl
provider "azurerm" {
  features {}

  subscription_id            = var.subscription_id
  use_oidc                   = true
  client_id                  = var.client_id
  tenant_id                  = var.tenant_id
  oidc_token_file_path       = "/mnt/oidc-token"  # set via ARM_OIDC_TOKEN
}
```

Or use environment variables: `ARM_USE_OIDC=true`, `ARM_CLIENT_ID`,
`ARM_TENANT_ID`, `ARM_SUBSCRIPTION_ID` — do not hardcode in the provider block.

### backend.tf

```hcl
terraform {
  backend "azurerm" {}
}
```

### backend.hcl.example

```hcl
resource_group_name  = "<state-rg>"
storage_account_name = "<state-storage-account>"
container_name       = "tfstate"
key                  = "<system>/<env>/terraform.tfstate"
use_oidc             = true
```

## Networking equivalents

| Concept | Azure resource |
| --- | --- |
| Network | `azurerm_virtual_network` |
| Segment | `azurerm_subnet` |
| Firewall | `azurerm_network_security_group` + `azurerm_network_security_rule` |
| Private service access | `azurerm_private_endpoint` + `azurerm_private_dns_zone` |
| Front door | `azurerm_application_gateway` + `azurerm_web_application_firewall_policy`, or `azurerm_api_management` |

## Tags

Azure uses `tags` (string map) on most resources. Apply via `local.standard_tags`
merged into each resource's `tags` argument. Also tag the resource group.
No `default_tags` equivalent exists in the AzureRM provider — tags must be
explicit per resource.

Azure tag constraints: key max 512 chars, value max 256 chars. Keys are
case-insensitive. The hyphen in `cost-center` and `data-classification` is valid.

## OIDC / workload-federation for CI

Use Azure Federated Identity Credentials on a user-assigned managed identity:

```hcl
resource "azurerm_federated_identity_credential" "github" {
  name                = "github-actions-${var.environment}"
  resource_group_name = azurerm_resource_group.identity.name
  parent_id           = azurerm_user_assigned_identity.ci.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = "https://token.actions.githubusercontent.com"
  subject             = "repo:<org>/<repo>:environment:<env>"
}
```

## Managed Kubernetes (AKS)

AKS cluster provisioning uses `azurerm_kubernetes_cluster` (in this reference).
In-cluster resource management uses `kubernetes` / `helm` providers
(see `providers/kubernetes-workloads.md`).

## State locking

AzureRM backend uses blob lease locking automatically — no separate lock table.
Enable encryption: storage account must have Storage Service Encryption enabled
with a CMK for `internal`/`confidential` data.
