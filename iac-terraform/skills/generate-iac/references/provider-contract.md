# Provider extension contract

> The four-file contract applies to **major public clouds** (AWS, Azure, GCP,
> extensible to OCI / AliCloud). It deliberately does not stretch to non-cloud
> providers (Cloudflare, Datadog, Kubernetes — no backend/region/cloud-IAM-
> federation). Those use category-appropriate reference shapes (see
> `providers/` directory).

## The four-file shape (hyperscalers only)

Every hyperscaler provider reference must produce these four files when used:

| File | Contract |
| --- | --- |
| `versions.tf` | `required_version >= 1.6`; the cloud's provider pinned with `~>` |
| `provider.tf` | provider block; standard tags/labels; region from `var.region`; **OIDC auth, no static credentials** |
| `backend.tf` | empty partial backend block for the cloud's remote-state service |
| `backend.hcl.example` | per-environment backend values template |

## Required mappings per cloud (extension contract DoD)

A new cloud provider is `contract-complete` when all of these are defined:

1. **Remote-state service + locking** — which backend service, how locking works
2. **Short-lived workload-identity primitive** — no static keys; OIDC trust-policy
   `sub` format and configuration (note: GitHub changed the OIDC `sub` claim
   format for repos created on/after 2026-07-15 to an immutable numeric-ID form;
   trust policies must use the current form)
3. **Tags vs labels** — field name, charset constraints, max length
4. **Network/subnet/firewall/private-service-access/front-door equivalents** —
   mapping table per `networking-standard.md`
5. **OIDC / workload-federation login** per CI system (GitHub Actions / GitLab /
   Azure DevOps)
6. **Account/tenant isolation model** — shared account + workspaces vs. separate
   account/subscription/project per environment; drives OIDC trust-policy `sub`
   scoping and state backend key structure
7. **Credential tiering** — ephemeral-zone identity can assume ephemeral-tier
   roles only; never a prod-assumable role

## Acceptance bars

**`contract-complete`** — the four files exist; the networking table has a column
for the cloud; the tagging notes cover tags-vs-labels + charset; the manifest
lists it; the provider index lists it. *(No worked example required.)*

**`validated`** — contract-complete **plus** at least one worked example that
passes `terraform init -backend=false && terraform fmt -check && terraform
validate`. For AWS, the example must additionally pass on **both `terraform`
and `tofu`** (dual-engine claim requires dual coverage).

In v1: **AWS + GCP are `validated`; Azure is `contract-complete` only.**

## Credential tiering (release-loop integration requirement)

The ephemeral/autonomous zone's workload identity **must** be scoped to
ephemeral-tier roles only. Concretely:

- **AWS:** the OIDC trust policy `Condition` scopes to the ephemeral environment's
  account and branch ref — never a prod-assumable role ARN.
- **Azure:** managed identity scoped to the ephemeral subscription or resource
  group — never a prod subscription.
- **GCP:** service account with roles bound to the ephemeral project only —
  never a prod project binding.

This is a hard requirement for `release-loop` compatibility (release-loop
control (g) — autonomous zone can never hold prod-scope credentials).

## Non-cloud providers — category taxonomy (see `providers/`)

Non-cloud providers (Cloudflare, Vault, Databricks, Datadog…) use
**category-appropriate reference shapes**, not this four-file mold:
- No backend configuration (SaaS/API providers)
- No region primitive (global or tenant-scoped)
- No cloud-IAM-federation (API token or OAuth — provider-specific)
- Auth mapping documented per provider in `providers/<category>.md`

A non-cloud reference is `contract-complete` when: resource-shape reference
exists; auth mapping is documented; governance-index domain row exists;
provider index lists it. It is `validated` when a worked example additionally
passes `init -backend=false && fmt -check && validate`.
