---
name: reconcile-iac
description: Use this skill to audit Terraform/OpenTofu drift, reconcile state, or run a pre-change preflight before a follow-on infrastructure change. Triggers on "reconcile my infrastructure", "check for drift", "drift audit", "what drifted", "before I change X check drift", "is my infra in sync". Never autonomously applies. Shares generate-iac's references and reviewers.
---

# Skill: reconcile-iac

`plan`-based drift audit → proposed disposition → route. Audit and propose;
a human (or the `release-loop` consent gate) decides. Never autonomously apply.

## Two triggers — both are first-class

| Trigger | When | What it does |
| --- | --- | --- |
| **Before-change preflight** | Before every follow-on infrastructure change (mandatory, not optional) | Runs a `plan` against live state to surface drift *before* the new change lands on top of it — prevents layering change on unknown drift |
| **On-demand / scheduled** | On request or on a scheduled cadence | Standalone drift snapshot for quiescent infrastructure; the author-side safety net when `release-loop` is absent |

**Recommended cadence:** (1) Before every follow-on change — mandatory preflight;
(2) Weekly minimum on a scheduled basis — regular drift snapshot even in
quiescent periods; (3) Immediately after a known out-of-band event — break-glass
action, console change, provider-managed auto-modification, or a known pipeline
failure.

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
