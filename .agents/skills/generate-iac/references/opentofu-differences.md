# OpenTofu differences

> **Load this file ONLY when `engine = opentofu` and a divergent feature is in
> play.** The engine-neutral baseline (the HCL emitted by `generate-iac` by
> default) runs unchanged on both Terraform and OpenTofu. This reference covers
> only the divergences.

## What OpenTofu IS (and is not)

OpenTofu is a **drop-in HCL-compatible fork of Terraform** (from Terraform
1.5.x, Linux Foundation, MPL 2.0 / CNCF Sandbox 2025). It:
- Reads `.tf` files and `terraform {}` blocks unchanged
- Keeps the same CLI subcommands (`init`, `plan`, `apply`, `fmt`, `validate`,
  `providers schema`, etc.)
- Uses the same `TF_*` env vars (no `TOFU_*` prefix)
- Mirrors the Terraform registry for `required_providers` shorthand resolution

Contrast Pulumi/CDK/CloudFormation — different languages needing separate
codegen. OpenTofu is the same HCL dialect; dual support is nearly free.

## OpenTofu-only features (emit when engine = opentofu)

### State/plan encryption

OpenTofu supports native state and plan encryption. This is a
**`reversibility-class: one-way-door`** action — Terraform cannot read
OpenTofu-encrypted state. Do NOT enable by default; require explicit opt-in
with the human acknowledging the one-way-door consequence.

```hcl
# encryption.tf — OpenTofu only; uses .tofu override mechanism
terraform {
  encryption {
    key_provider "pbkdf2" "main" {
      passphrase = var.state_encryption_passphrase
    }
    method "aes_gcm" "main" {
      keys = key_provider.pbkdf2.main
    }
    state {
      method = method.aes_gcm.main
    }
    plan {
      method = method.aes_gcm.main
    }
  }
}
```

### Early/dynamic variable evaluation

OpenTofu supports `var.*` and `local.*` in `backend {}` blocks and in module
`source` arguments — not supported in Terraform. Use `.tofu` override files
for this pattern (see below).

### `-exclude` flag and provider `for_each`

OpenTofu supports `terraform plan -exclude=<target>` and `provider for_each`
for dynamic provider configuration. Not available in Terraform 1.11.

### OCI registry sourcing

OpenTofu can source modules and providers from OCI-compatible registries.
Not supported in Terraform.

### `.tofutest.hcl` for tests

OpenTofu uses `.tofutest.hcl` (not `.tftest.hcl`). The format is compatible;
only the extension differs.

## Terraform-only features (do NOT emit for OpenTofu targets)

- **Ephemeral values / write-only arguments** (Terraform 1.10+) — no equivalent in OpenTofu
- **Terraform Stacks** — no equivalent in OpenTofu
- **HCP Terraform cloud blocks** — OpenTofu uses standard backends

## The `.tofu` override-file mechanism

OpenTofu loads files with `.tofu` extension and **ignores the `.tf` twin**.
Terraform never reads `.tofu` files. This lets the same directory stay
dual-compatible — OpenTofu-only syntax lives in `.tofu` files; the `.tf`
baseline runs on Terraform.

```
main.tf           # shared — runs on both
encryption.tofu   # OpenTofu-only — Terraform ignores
```

Use this for: state encryption, early variable eval in backend config,
provider `for_each`, OCI registry sourcing.

## Lock file

The `.terraform.lock.hcl` (Terraform) and `.terraform.lock.hcl` (OpenTofu —
same filename) are **not interchangeable** — registry origin changes recorded
hashes differ. Always run `init` for the target engine; never share a lock
across engines. The CI pipeline parameterizes only the binary name.

## CLI parameterization

```bash
# In CI, set ENGINE to 'terraform' or 'tofu'
${ENGINE} init -backend-config=backend.hcl
${ENGINE} fmt -check
${ENGINE} validate
${ENGINE} plan -out=tfplan
${ENGINE} show -json tfplan > tfplan.json
```

Everything else (OPA/Conftest, Trivy/Checkov, policy gate) is engine-agnostic.

## Adoption context (honest)

OpenTofu is credible and growing (Linux Foundation, CNCF Sandbox 2025) and
license-safe for FOSS-only procurement policies. Terraform holds the larger
overall market share; the higher OpenTofu percentages are typically vendor-
platform telemetry, not neutral surveys. The pack is engine-neutral to avoid
picking a licensing side — not because OpenTofu is dominant.
