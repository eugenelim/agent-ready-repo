---
name: reconcile-iac
description: Use this skill to audit Terraform/OpenTofu drift, reconcile state, run a pre-change preflight, or check an incoming IaC diff for ADR compliance. Triggers on "reconcile my infrastructure", "check for drift", "drift audit", "what drifted", "before I change X check drift", "is my infra in sync", "adr-check", "does this change comply", "check this diff against our ADRs", "compliance check this IaC change". Never autonomously applies. Shares generate-iac's references and reviewers.
---

# Skill: reconcile-iac

`plan`-based drift audit → ADR compliance check → proposed disposition → route.
Audit and propose; a human (or the `release-loop` consent gate) decides. Never
autonomously apply.

## Three triggers — all first-class

| Trigger | When | What it does |
| --- | --- | --- |
| **Before-change preflight** | Before every follow-on infrastructure change (mandatory, not optional) | Runs a `plan` against live state to surface drift *before* the new change lands on top of it — prevents layering change on unknown drift |
| **On-demand / scheduled** | On request or on a scheduled cadence | Standalone drift snapshot for quiescent infrastructure; the author-side safety net when `release-loop` is absent |
| **ADR compliance check** | When an IaC diff arrives that was NOT authored by `generate-iac` (hand-edit, external PR, CI gate) | Checks the diff against the governance-index ADRs — covers the compliance gap for changes the generation skill didn't author |

**Recommended cadence (Triggers 1 and 2):** (1) Before every follow-on change —
mandatory preflight; (2) Weekly minimum on a scheduled basis — regular drift
snapshot even in quiescent periods; (3) Immediately after a known out-of-band
event — break-glass action, console change, provider-managed auto-modification,
or a known pipeline failure.

**Trigger 3 fires on demand**, not on a cadence — invoke when a diff arrives
that did not go through `generate-iac`.

## Known blind spot — document and do not hide

`terraform plan` computes drift between **state and the live control plane** —
but resources created entirely outside Terraform (ClickOps, console actions with
*no state entry*) are **invisible to `plan`**. This skill inherits that limit.
Detecting unmanaged resources requires a separate layer (Snyk IaC / Driftctl
lineage, `terraform import` discovery pass, or platform health checks).

**Always document this scope boundary in the drift audit report.** Do not imply
full drift coverage — the audit covers managed resources only.

## Procedure

```
1. Confirm the repo's governance-index is loaded (Stage 0 of generate-iac).
   If the index is absent, offer to bootstrap it before proceeding.

2. Run a read-only plan:
   terraform plan -detailed-exitcode (or tofu plan -detailed-exitcode)
   Exit 0 = no diff (no drift detected; document and stop).
   Exit 2 = diff detected (proceed to audit).
   Exit 1 = error (surface the error; do not proceed).

3. For each drifted resource, produce a drift audit entry:
   - Resource address
   - Cause-class:
     • out-of-band-change (ClickOps / break-glass)
     • provider-managed (cloud-side default change / auto-scaling / patch)
     • multi-tool (another tool manages this resource outside Terraform)
     • pipeline-failure (a previous apply only partially completed)
     • unknown
   - Blast radius: what downstream resources depend on this resource
   - Standards violated by the drift (cite from governance-index domains)

4. For each drifted resource, propose a disposition:
   • codify-back: update IaC to match the live state (legitimate change)
   • add ignore_changes: mark as intentionally managed outside Terraform
   • open-remediation-PR: revert the drift via a follow-on `generate-iac`
   • block-follow-on: this drift must be resolved before the planned change
   • route-to-release-loop: runtime telemetry-driven drift → release-loop
     (only when release-loop is installed and the drift is ops-detected)

5. Emit the drift audit report:
   - Summary: N resources drifted, M unmanaged (scope-limited estimate)
   - Per-resource: address + cause-class + blast-radius + proposed disposition
   - Scope boundary note: unmanaged resources not covered by this audit
   - Recommendation: proceed / block / route

6. A human (or the release-loop consent gate) decides the disposition.
   Do not apply or destroy anything autonomously.
```

## ADR compliance check procedure (Trigger 3)

Use when an IaC diff arrives that was not authored by `generate-iac` — a
hand-edited `.tf` file, an external PR, a CI gate check. The governance-index
is the compliance oracle; this procedure is the enforcement path for changes
that bypassed Stage 0.

```
1. Load the governance-index (governance-index.yaml / governance-index.toml).
   If absent, surface it — offer to bootstrap via generate-iac Stage 0.

2. Identify which governance domains the diff touches. Map by resource type:
   • aws_iam_* / google_project_iam_* / azurerm_role_assignment → iam
   • aws_vpc_* / google_compute_network / azurerm_virtual_network → networking
   • terraform { backend } / aws_s3_bucket (state bucket) → state
   • resource_group / project / aws_organizations_account → layout
   • any provider block changes → layout
   • aws_security_group / aws_security_group_rule → networking + policy
   • tagging / labels arguments → tagging
   • CI config changes (GitHub Actions / ADO / GitLab) → pipeline_auth

3. For each touched domain, read the ADR(s) listed in the governance-index.
   Focus on the ADR's Decision, Constraints, and Consequences sections.

4. For each ADR, evaluate the diff against each constraint:
   • COMPLIANT — diff honours the constraint
   • VIOLATION — diff contradicts a constraint (e.g. introduces DynamoDB locking
     when ADR mandates native S3 lockfile; uses static creds when ADR mandates OIDC)
   • WARN — diff is in a grey area or the constraint is ambiguous

5. Emit the ADR compliance report:
   - Summary: N domains checked, M ADRs read, K violations, J warnings
   - Per-violation: domain → ADR number → specific constraint violated →
     diff lines that trigger it → recommended fix
   - Per-warning: domain → ADR number → ambiguity + suggested clarification

6. VIOLATION blocks the change — route to human to either:
   (a) fix the diff to comply, or
   (b) draft a new ADR (via new-adr, infra mode) to record a legitimate decision
       change, then re-check.
   Do not autonomously approve or suppress a VIOLATION.
```

**Domain-to-resource-type mapping is heuristic** — add a note in the report when
a resource type spans multiple domains or doesn't map cleanly. Human confirms the
domain assignment when ambiguous.

## Disposition decision guidance

The five dispositions map from cause-class and blast-radius. Use this table as a
starting heuristic — the human confirms every disposition before any action.

| Cause-class | Blast radius vs planned change | Recommended first disposition |
| --- | --- | --- |
| `out-of-band-change` | Overlaps | `block-follow-on` — confirm or codify before proceeding |
| `out-of-band-change` | No overlap | `codify-back` if legitimate; `open-remediation-PR` if it violates a standard |
| `provider-managed` | Overlaps | `block-follow-on` → investigate → `add ignore_changes` if intentional |
| `provider-managed` | No overlap | `add ignore_changes` if the provider change is known-good |
| `multi-tool` | Any | `add ignore_changes` — another tool owns this; coordinate out-of-band |
| `pipeline-failure` | Any | `open-remediation-PR` — revert via a `generate-iac` PR to pre-failure state |
| `unknown` | Any | `block-follow-on` — investigate cause before any disposition |

**Do not merge `codify-back` and `add ignore_changes` on the same resource.**
They are mutually exclusive: either Terraform owns the current state (codify-back)
or the drift is intentional and Terraform should stop tracking it (ignore_changes).

**`open-remediation-PR` always routes through `generate-iac`** — do not author
remediation HCL directly in `reconcile-iac`. Remediation PRs get the full
standards + reviewer set.

## Drift decomposition — who owns which moment

| Drift moment | Owner |
| --- | --- |
| Runtime / ops drift — a deployed env diverges (telemetry-detected) | `release-loop` (`drift-and-rollback`) — ops/SRE, when present |
| Drift → the code fix | release-loop feedback seam → work-loop + `generate-iac` |
| `plan`-based reconcile — before a follow-on change (preflight) or on-demand/scheduled, with or without `release-loop` | **this skill** — the author-side net |

`reconcile-iac` and `release-loop` are complementary, not competitive:
- `release-loop` is the runtime-telemetry-driven detection layer (when present)
- `reconcile-iac` is the `plan`-based author-side reconcile that works *with or
  without* `release-loop`

## References (shared with generate-iac — not duplicated)

Standards:
- `../generate-iac/references/terraform-standard.md`
- `../generate-iac/references/networking-standard.md`
- `../generate-iac/references/security-iam-standard.md`
- `../generate-iac/references/tagging-standard.md`

Drift-specific:
- `../generate-iac/references/terraform-verify-and-iterate.md` — the plan-vs-apply
  oracle split + drift detection model
- `../generate-iac/references/provider-contract.md` — for identifying drift
  in the provider configuration itself
- `../generate-iac/references/release-loop-integration.md` — when routing to
  release-loop (deployment-detected drift cases)

Provider references:
- `../generate-iac/references/providers/<cloud>.md` — load target cloud only

## Reviewers (same as generate-iac — reused from `core`)

After generating the drift audit report, if the disposition involves a
remediation PR:
- Route the remediation PR through `generate-iac` for authoring
- Apply the standard reviewer set (adversarial-reviewer + quality-engineer +
  security-reviewer) on the resulting diff

## Hard rules

- Never run `terraform apply`, `terraform destroy`, or any mutating command.
- Never autonomously decide a disposition — always surface and route.
- Always document the unmanaged-resources blind spot in every audit report.
- Block a follow-on change when drift is detected whose cause-class is
  `provider-managed` or `out-of-band-change` and the blast-radius overlaps
  with the planned change — until the disposition is confirmed by a human.
