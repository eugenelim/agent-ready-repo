# Policy on plan (OPA / Conftest)

> **Load this when `policy = opa` is set or the human requests policy-as-code.**
>
> **Engine compatibility:** OPA / Conftest runs against `terraform show -json`
> output — engine-agnostic (Terraform and OpenTofu both produce compatible JSON).
> **Sentinel is incompatible with OpenTofu** and is therefore not the
> open-source path. OPA / Conftest is the only policy layer this pack supports.

## Why policy on plan (not apply)

`terraform plan -out=tfplan && terraform show -json tfplan` produces a
structured JSON representation of all planned resource changes. OPA / Conftest
evaluates this JSON before `apply` runs — no live resources are touched.
This makes policy evaluation:
- Fast (seconds, not minutes)
- Repeatable (idempotent against the same plan JSON)
- Catchable in CI before any deployment

## Starter Rego rules

Three starter policies cover the most common compliance requirements. All are
in `policy/deny-open-ingress.rego` (loaded separately). Here is the shape:

```
policy/
  deny-open-ingress.rego    # no 0.0.0.0/0 on ingress; no public S3 ACLs
  deny-tags.rego            # mandatory tag keys must be present (customise per repo)
  deny-unencrypted.rego     # EBS, S3, RDS encryption must be enabled
```

Customize `deny-tags.rego` to match your `tagging-standard.md` mandatory keys.

## Running Conftest

```bash
terraform show -json tfplan > tfplan.json

conftest test tfplan.json \
  --policy policy/ \
  --namespace terraform \
  --output table
```

`conftest test` exits non-zero if any deny rule fires — use this as the CI
gate condition (see `pipeline/github-actions.md`).

## OPA policy structure for Terraform plan JSON

The Terraform plan JSON schema (`resource_changes[_]`) is the stable input:

```rego
package terraform

import future.keywords.every

# resource_changes array — path into the plan JSON
resource_changes := input.resource_changes

# Helper: resource is being created or updated
is_create_or_update(change) {
  change.change.actions[_] == "create"
}
is_create_or_update(change) {
  change.change.actions[_] == "update"
}
```

See `policy/deny-open-ingress.rego` for the full implementation.

## Caveat: OPA evaluates plan-time values, not apply-time values

OPA sees the plan JSON as Terraform resolved it — which may include
`(known after apply)` sentinels for values that depend on resource IDs not
yet known. A rule that tries to match a specific computed value will not fire
against unknowns. Design rules around *absence* of a required field or the
*presence* of a forbidden value (like `0.0.0.0/0`) — these are resolvable at
plan time. Document this caveat in the policy README.

## Adding a policy gate to CI

See `pipeline/github-actions.md` for the `policy-gate` job that runs Conftest
against the saved plan JSON and gates `deploy` on its exit code.
