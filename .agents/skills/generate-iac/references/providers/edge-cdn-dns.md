# Edge / CDN / DNS providers reference — experimental, not validated in v1

> **experimental — not validated in v1.** Contract-complete for Cloudflare;
> other providers are reference-only. Validate before use.

## Cloudflare

**Provider:** `cloudflare/cloudflare`

```hcl
terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}

provider "cloudflare" {
  # api_token supplied via CLOUDFLARE_API_TOKEN env var — never hardcode
}
```

Common resources:
- `cloudflare_zone` — DNS zone management
- `cloudflare_record` — DNS records (A, CNAME, TXT, MX)
- `cloudflare_ruleset` — WAF rules, rate limiting, transform rules
- `cloudflare_access_application` / `cloudflare_access_policy` — Zero Trust access policies
- `cloudflare_workers_script` — edge compute

Account and zone IDs are stable and safe to commit; API token must come from
`CLOUDFLARE_API_TOKEN` or a secrets manager, never from `provider {}` block or
a `var.*` defaulted to a literal.

**State backend:** Use a cloud-native backend (S3, GCS, AzureRM) — not
Cloudflare itself. No lock table; use the relevant cloud backend's native locking.

## Akamai

**Provider:** `akamai/akamai`

Akamai's Terraform provider manages EdgeWorkers, property configurations, and
DNS (Edge DNS). The Akamai provider uses a `.edgerc` credential file or
environment variables (`AKAMAI_*`). Never store the `.edgerc` file in the
repo.

## AWS CloudFront (in the `aws` provider)

CloudFront is in the `hashicorp/aws` provider — see `providers/aws.md`. No
separate provider needed.

## Azure CDN / Front Door (in the `azurerm` provider)

Azure CDN and Front Door are in the `hashicorp/azurerm` provider — see
`providers/azure.md`. No separate provider needed.

## GCP Cloud CDN (in the `google` provider)

Cloud CDN is backed by `google_compute_backend_service` — in the
`hashicorp/google` provider. See `providers/gcp.md`. No separate provider
needed.

## External DNS / Route 53 / Cloud DNS

- **AWS Route 53:** `aws_route53_zone`, `aws_route53_record` — in the
  `hashicorp/aws` provider.
- **GCP Cloud DNS:** `google_dns_managed_zone`, `google_dns_record_set` — in
  the `hashicorp/google` provider.
- **Azure DNS:** `azurerm_dns_zone`, `azurerm_dns_a_record` — in the
  `hashicorp/azurerm` provider.

Multi-cloud DNS delegation (NS records in Route 53 delegating to Cloud DNS) is
a common pattern for hybrid setups — both providers in the same root module.

## Security note

CDN/WAF policies govern external traffic. Changes to WAF rulesets or access
policies are operational-safety events — run `reconcile-iac` before any
follow-on changes. Removing an access policy is a `reversibility-class:
costly-to-reverse` action; removing a WAF rule without a staged rollout is
`one-way-door` if a security incident follows.
