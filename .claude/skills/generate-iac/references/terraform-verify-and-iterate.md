# Terraform verify and iterate

> This reference covers the **inner-loop verification modes** this pack owns.
> For the **outer-loop (deploy-time) probes** — idempotent convergent apply,
> the readiness-aware data-plane probe, rollback — **refer to `core`'s
> `infra-verification` V2**. This file does not re-specify those.

## Terraform's oracle model — why `plan` is special, and why it isn't enough

`terraform plan` is a **dry-run diff against refreshed state** — it shows what
the provider will change before mutation, and doubles as the drift detector (a
`plan` on unchanged code that shows a diff = drift). But:

- `plan` evaluates against the provider schema and last-known state — not the
  live control plane. Apply-time failures (IAM eventual-consistency propagation,
  service quotas, dependency ordering, resources that reach a terminal FAILED
  state, cross-region races) surface only on `apply` against a real account.
- `apply` is **not atomic** — a partial apply leaves real resources. Recovery
  is a named re-apply or targeted-destroy path, never an "undo".

**Inner oracle:** `plan` is the inner-loop verification signal — necessary but
not sufficient. A green `plan` does not certify intent.

**Outer oracle:** `apply` + smoke is the outer-loop oracle, owned by
`release-loop` on ephemeral isolated environments. The pack shapes its outputs
so the outer loop can drive them (see `release-loop-integration.md`).

## Inner-loop verification modes

### Static preflight (always run before `plan`)

```bash
terraform fmt -check               # canonical formatting
terraform validate                 # schema + syntax; requires `init` first
tflint --recursive                 # module-aware lint (if tflint is wired)
```

`validate` is a local typecheck analog — a green `validate` is necessary, never
a done-signal. It catches schema errors before a plan round-trip.

### Plan (the G4 artifact)

```bash
terraform init -backend-config=backend.hcl   # initialize with real backend config
terraform plan -out=tfplan                   # produce the binary plan
shasum -a 256 tfplan                         # record the plan digest
terraform show -json tfplan > tfplan.json    # serialize to JSON for policy gate
```

The deploy step applies *exactly* the pinned plan — **never a re-run**.

### Policy-on-plan gate

```bash
conftest test tfplan.json --policy policies/opa/
# or
trivy config .
checkov -d . --compact
```

**Known OPA caveat:** some values (from variables, module outputs, dynamic
blocks) may be unknown at plan time. Rules must tolerate absent fields.
A security-relevant field that is unknown at plan time requires a compensating
apply-time re-check, or the residual false-negative must be documented as
accepted. This is not just an OPA limitation — it is a security finding if
a violation could be carried by an unknown-at-plan value.

**Sentinel is incompatible with OpenTofu.** OPA/Conftest is the only
open-source policy engine that works on both engines. For OpenTofu users,
OPA/Conftest is the required path.

### Module and contract tests (inner, module-time)

Three tiers — choose based on what the unknown is:

| Tier | Tool | When |
| --- | --- | --- |
| Unit | `.tftest.hcl` with `command = plan` + mock providers | No cloud, no cost; fast; default for module authoring |
| Contract | Consumer-authored interface assertions (plan-mode); subnet AZ coverage, output CIDR shape | Validates module's public contract |
| E2E / Integration | Terratest or `.tftest.hcl` with `command = apply` against real resources | Only when apply-time behavior is the unknown; incurs cloud cost |

Default: **unit + contract** for module authoring. E2E only when you need to
confirm apply-time behavior (quota availability, IAM propagation, etc.).

Module tests are reused by `core`'s `quality-engineer` in test-author mode —
the skill taps existing test infrastructure, never re-ships it.

## Iteration loop

```
write TF → validate → plan → policy gate → iterate on findings
          ↑                              │
          └──────── fix + re-plan ───────┘
```

Fix each finding class:
- **Schema/argument hallucination:** ground the resource in the live schema via
  `contract-acquisition` before re-emitting.
- **Cycle:** restructure the dependency graph; use `depends_on` sparingly.
- **Missing variable:** add the variable with type + description + validation.
- **Policy violation:** fix the resource to comply; update the ADR if the
  deviation is intentional.

## Outer loop (defer to `infra-verification`)

The following are **`release-loop`'s territory** — do not re-specify them here:
- Idempotent convergent apply
- Readiness-aware data-plane probe (the V2 smoke probe)
- Rollback / known-good re-apply path
- Post-apply telemetry check

This pack's job at the outer-loop boundary: **shape outputs so these are
buildable** — emit a `verify-status` script, a `teardown` script, a
uniquely-named ephemeral target, seed data, and `reversibility-class`
annotations per stateful resource.
