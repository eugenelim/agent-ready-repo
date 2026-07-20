# Release-loop integration

> This file records how `iac-terraform` integrates with `core`'s
> `operational-safety` skill and `release-loop` skill.
>
> **Targeted versions:**
> - `operational-safety` module-contract: `core 0.12.0`
> - Reversibility enum: `reversible | costly-to-reverse | one-way-door`

## Integration point: `generate-iac` ↔ `operational-safety`

The `generate-iac` skill's G4 handoff artifact set includes:

| Artifact | operational-safety module it maps to |
| --- | --- |
| Pinned plan + apply evidence | `state-and-idempotency` |
| Reversibility classification (per resource) | `drift-and-rollback` |
| Trivy / Checkov evidence | `cloud-implementation-craft` |
| OPA / Conftest policy evidence | `cloud-implementation-craft` |
| Environment isolation proof | `environment-isolation` |
| Infracost delta (optional) | `cost-and-teardown` |
| Active smoke result | `observability-and-smoke` |

The `reconcile-iac` skill maps its cadence to `drift-and-rollback`:
- Before every follow-on change (mandatory) ← `drift-and-rollback` precondition
- Weekly minimum ← `drift-and-rollback` recommended cadence
- Post out-of-band change ← `drift-and-rollback` event trigger

## Reversibility classification

Use the three-value enum when annotating resources in the G4 handoff ADR and
in the `reconcile-iac` disposition report:

| Class | Meaning | Examples |
| --- | --- | --- |
| `reversible` | Can be destroyed and re-created with no lasting state loss | EC2 instance, security group, IAM role |
| `costly-to-reverse` | Can be undone, but it requires significant time, cost, or coordination | RDS deletion-protection removal, VPC CIDR change, EKS version downgrade |
| `one-way-door` | Cannot be undone after apply, or undoing it causes data loss | S3 bucket deletion, OpenTofu state encryption enablement, DynamoDB table deletion, GCP project deletion, Databricks table drop |

## OpenTofu state encryption is always `one-way-door`

As documented in `opentofu-differences.md`: once state encryption is enabled,
Terraform cannot read the state. This must be classified `one-way-door` in the
G4 handoff ADR and confirmed by a human before applying.

## release-loop integration

IaC changes flow through `release-loop` when the infrastructure is
part of a released service. The operational-safety gate in `release-loop`
requires:
1. All `generate-iac`-managed resources are in state (no untracked changes)
2. `reconcile-iac` drift report shows no unplanned drift
3. Reversibility classification recorded for all resources changed in the PR

When `release-loop` runs its smoke gate, the IaC layer's active smoke result
(from `observability-and-smoke`) is the multi-hop probe that confirms the data
plane is reachable — not a `terraform plan` (a plan is a `reversible`-state
confirmation, not a data-plane probe).

## Module references (core 0.12.0)

The six operational-safety modules this integration references:

```
packs/core/.apm/skills/operational-safety/references/
  state-and-idempotency.md
  drift-and-rollback.md
  environment-isolation.md
  cost-and-teardown.md
  observability-and-smoke.md
  cloud-implementation-craft.md
```

Load the relevant module on demand when the corresponding G4 artifact
is being assembled.
