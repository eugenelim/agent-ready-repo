# OpenTofu vs Terraform — dual-support research (RFC-0065)

Audit trail for the D12 decision (can one `generate-iac` skill emit for both
engines, with OpenTofu differences behind progressive disclosure). Applied depth;
confidence tags + primacy per source.

## Adoption / governance (honest picture)

- **The fork is real and governance-independent.** HashiCorp relicensed Terraform
  MPL 2.0 → BSL/BUSL 1.1 (Aug 2023); the community forked to **OpenTofu** under the
  **Linux Foundation, MPL 2.0**, accepted as a **CNCF Sandbox project (Apr 2025)**.
  IBM **acquired HashiCorp (closed Feb 2025)** and is doubling down commercially
  (Project Infragraph; HCP free-tier reportedly ended Mar 2026) — no re-licensing
  back to MPL. `[high]` (Primary: HashiCorp BSL blog; CNCF OpenTofu page; IBM
  newsroom.)
- **A 2024 HashiCorp C&D / copyright claim over OpenTofu's `removed` block** did not
  become litigation and did not recur. `[moderate]` (Primary: OpenTofu response.)
- **Adoption is credible and growing but not dominant.** Terraform still holds the
  largest *overall* IaC share; OpenTofu's high usage figures (50–72%) are **within
  multi-IaC vendor platforms** (Spacelift/env0/Scalr) and are **vendor-telemetry,
  not independent** — treat % as directional. Named production adopters (Fidelity,
  Boeing, Capital One, AMD) exist; the most concrete (Fidelity) is self-published by
  OpenTofu. **Defensible claim: OpenTofu is credible, growing, license-safe (OSI/MPL),
  but not yet dominant.** `[moderate]` — downgrade: all share numbers vendor-sourced,
  no neutral survey found.
- **Enterprise drivers for OpenTofu:** BSL is not OSI-approved (FOSS-compliance
  procurement risk), fear of future IBM-controlled term changes, faster OSS feature
  cadence. `[moderate]`

## Technical compatibility (the load-bearing part)

- **OpenTofu forked from Terraform 1.5.x; HCL, `.tf` loading, `terraform {}` blocks,
  and provider interfaces are compatible for the vast majority of configs.** `[high]`
  The `tofu` CLI keeps the **same subcommands** and the **same `TF_*` env vars** (no
  `TOFU_*` prefix; exception `TF_ENCRYPTION`). (Primary: OpenTofu env-var + files docs.)
- **The official dual-tool escape hatch: `.tofu` / `_override.tofu` files.** OpenTofu
  loads `.tofu`/`.tofu.json`; if both `foo.tf` and `foo.tofu` exist it loads **only**
  the `.tofu` twin. **Terraform never reads `.tofu`.** So OpenTofu-only syntax siloed
  in `.tofu` files keeps one source tree dual-compatible. `[high]` (Primary: OpenTofu
  Override Files docs; 1.8.0 blog.) **This is the mechanism the pack uses.**
- **State interoperates *until* an OpenTofu-only feature is used.** `terraform.tfstate`
  is compatible both directions; switching binaries against unencrypted state is
  "the easy part." **State/plan encryption is a one-way door** — once OpenTofu
  encrypts state, Terraform cannot read it. `[high]` (Primary: OpenTofu encryption docs.)
- **Registry: `registry.opentofu.org` mirrors most of the Terraform registry; the
  same `source = "namespace/name/provider"` shorthand resolves on both** — so
  `required_providers` rarely needs branching. Divergence shows in **`.terraform.lock.hcl`
  content** (registry origin → different hashes/signing) → **regenerate the lock per
  engine at `init`.** `[moderate]` (Primary: OpenTofu registry; issue #2113.)

### The divergence set (small, enumerable)

**Identical → one template serves both:** core HCL, resource/data/variable/output/
locals, `required_providers` shorthand, module composition (git/local/registry),
`.tftest.hcl` basic subset, `TF_*` env vars, `init`/`plan`/`apply`/`validate`/`fmt`,
unencrypted state.

**Must branch (progressive disclosure):**
| Divergence | Engine | Handling |
| --- | --- | --- |
| State/plan **encryption** block (`TF_ENCRYPTION`) | OpenTofu-only; **one-way door** on state | isolate in a `.tofu` file; consent-gate-worthy (irreversible) |
| **Early/dynamic variable evaluation** (vars in `backend`/`module source`) | OpenTofu ≥1.8 | Terraform can't; don't emit into a shared `.tf` |
| **`-exclude` flag**, provider `for_each` | OpenTofu ≥1.9 | CLI/pipeline branch; Terraform falls back to `-target` |
| **OCI registry** sourcing (`oci://`) | OpenTofu ≥1.10 | branch only for OCI-based registries |
| **Ephemeral resources / write-only args** | Terraform ≥1.10/1.11 | OpenTofu substitutes state-encryption / external secret mgr |
| **Stacks** | Terraform/HCP-only | out of scope for OpenTofu targets |
| `.tofutest.hcl` test syntax | OpenTofu-only | default to `.tftest.hcl` (both) |
| `required_version` pins | per-engine capability by minor version | version-gate per engine |

**Caution (from the retriever):** several "engine-exclusive" features have
**converged** (provider-defined functions, `removed` blocks, test provider-mocking)
— treat any single blog's "X is only in engine Y" as time-stamped, re-verify against
primary changelogs. The most load-bearing durable divergence for codegen is
**early variable evaluation** (backend/module-source interpolation) and **state
encryption**.

## Design conclusion (feeds §6a / D12)

**Yes — one skill targets both.** The default emitted config is the **common subset
that runs unchanged on both engines**; the CLI/verbs/env-vars are identical, so the
pipeline generators parameterize only the binary (`terraform` ↔ `tofu`). The small
divergence set is handled by **one progressive-disclosure reference
(`references/opentofu-differences.md`)** loaded only when `engine = opentofu` and a
divergent feature is in play, using `.tofu` override files to silo OpenTofu-only
syntax. This is genuinely different from "multi-engine IaC" (Pulumi/CDK/CFN are
different languages needing separate codegen) — OpenTofu is the *same HCL dialect*,
so dual support is nearly free and does **not** violate the "no multi-engine
abstraction" non-goal.
