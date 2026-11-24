# Terraform verify and iterate

> This reference owns direct authoring verification. Deployment-time probes
> belong to an optional, separately authorized release workflow; they are not
> prerequisites of standalone authoring. Never run apply or destroy here.

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

### Grounding and gated plan

Confirm engine/version, provider locks, target, backend and workspace first.
Initialize the selected providers with the confirmed backend configuration;
`init -backend=false` is suitable for isolated schema/validation checks only.
Run `<engine> providers schema -json` directly, where `<engine>` is `terraform`
or `tofu`, and check every resource and argument against that live contract.
Run `<engine> validate` directly as the companion grounding oracle.

Require `authoring_gate.py check-summary SUMMARY --root ROOT` to return `ready`
before planning. Choose a fresh run directory and unused saved-plan path:

```bash
<engine> fmt -check && <engine> validate && <engine> plan -out=tfplan
```

A failed step leaves no saved plan for handoff. Stop on failure, removing only
this run's partial plan if plan itself left output. Never reuse a stale plan.
After success, inspect with `<engine> show -json tfplan > tfplan.json` and record
the exact saved-plan digest. Run optional module lint when wired; failure stops.

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

Apply-mode integration tests belong only to the separately authorized release
path. Direct authoring uses plan-mode tests and never runs apply or destroy.

## Iteration loop

```
write TF → validate → plan → policy gate → iterate on findings
          ↑                              │
          └──────── fix + re-plan ───────┘
```

Fix each finding class:
- **Schema/argument hallucination:** ground the resource in the live schema via
  `<engine> providers schema -json` and `<engine> validate` before re-emitting.
- **Cycle:** restructure the dependency graph; use `depends_on` sparingly.
- **Missing variable:** add the variable with type + description + validation.
- **Policy violation:** fix the resource to comply; ask the owner to settle any intentional
  deviation, then update the governing summary and re-check it.

## Local review and bundle gate

Use [infrastructure-review.md](infrastructure-review.md) as the complete canonical
local checklist. Record all areas and bind the review to the saved plan and
checklist digests. Run
`authoring_gate.py check-review RECORD --root ROOT --saved-plan PATH --checklist PATH`.
Only `check-summary` ready and `check-review` pass allow bundle emission; validate
it using `plan_bundle.py validate INPUT --root ROOT --policy POLICY`.

## Optional release checks

Convergent deployment, readiness-aware smoke probes, recovery exercises and
post-deployment telemetry belong to the optional release workflow described in
[release-loop-integration.md](release-loop-integration.md). Core modules and
reviewers may add evidence after direct checks; their findings enter the review
record and never replace a local area. Refusal or a failed check stops the step;
no weaker fallback replaces it.
