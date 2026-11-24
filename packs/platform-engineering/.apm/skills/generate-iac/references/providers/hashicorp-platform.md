# HashiCorp platform providers reference — experimental, not validated in v1

> **experimental — not validated in v1.** Vault is the most-requested
> provider here; Boundary and HCP are less common. Validate before use.

## Vault

**Provider:** `hashicorp/vault`

```hcl
terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
  }
}

provider "vault" {
  address = var.vault_addr  # e.g. "https://vault.example.com"
  # Token supplied via VAULT_TOKEN env var or AppRole login in CI
}
```

Common patterns:
- `vault_mount` — enable a secrets engine (kv-v2, aws, pki)
- `vault_kv_secret_v2` — write a KV v2 secret
- `vault_aws_secret_backend_role` — dynamic AWS credentials
- `vault_policy` — write a Vault policy
- `vault_auth_backend` / `vault_jwt_auth_backend` — enable auth methods (JWT
  for OIDC, Kubernetes, AppRole)
- `vault_pki_secret_backend_cert` — issue a PKI certificate

**CI authentication:** Use JWT/OIDC auth via `vault_jwt_auth_backend` with the
GitHub Actions OIDC issuer. Never use a long-lived root token in CI. An
AppRole with short-TTL token is acceptable if OIDC auth is not available.

**State backend note:** Vault secrets written via Terraform are stored
unencrypted in Terraform state. Use a state backend with encryption enabled
(see `terraform-standard.md` for S3 + KMS, GCS + CMEK, or AzureRM + CMK).
Consider marking sensitive outputs with `sensitive = true`.

**Operational-safety concern:** Revoking Vault auth methods, removing policies,
or disabling secrets engines are `reversibility-class: one-way-door` or
`costly-to-reverse` operations — classify in the ADR before applying.

## HashiCorp Boundary

**Provider:** `hashicorp/boundary`

Manages Boundary's access control: targets, host catalogs, host sets,
credential stores, and role assignments. Authentication to Boundary's
management plane uses a recovery token or password auth method in CI.

## HCP (HashiCorp Cloud Platform)

**Provider:** `hashicorp/hcp`

Manages HCP Vault Dedicated, HCP Consul, and HCP Terraform (formerly TFC)
organizational resources — projects, networks (HVN), cluster configurations.

```hcl
terraform {
  required_providers {
    hcp = {
      source  = "hashicorp/hcp"
      version = "~> 0.90"
    }
  }
}

provider "hcp" {
  # Credentials via HCP_CLIENT_ID / HCP_CLIENT_SECRET env vars
}
```

**OpenTofu note:** Sentinel policies (HCP Terraform feature) are **incompatible
with OpenTofu** — the policy evaluation runtime is HCP-proprietary. Use OPA /
Conftest as the policy-as-code layer instead (see `policy-on-plan.md`).
