# drift-and-rollback — read-only drift detection, known-good re-apply path

> **Loaded when:** the change manages long-lived infrastructure that can drift
> from its declared state, or where a deploy needs a defined recovery path if
> the smoke probe fails.
> **Grounded in:** F1.4 (drift detection is read-only and separable from
> remediation; auto-remediation default is contested), F2.6 (no atomic
> rollback — re-apply the prior known-good config). Operational taxonomy: AWS
> Well-Architected Failure Management; Google SRE Incident Response; Pulumi
> Day-2 drift detection + remediation.
> **Delegation legend:** `tool` = scanner / CI-gate-owned · `hybrid` = gate
> surfaces the signal, you judge the fix · `reason` = reviewer-only judgment.

This is the **divergence-detection-and-recovery** lens — deliberately separate
from `state-and-idempotency`'s write-path convergence (every major operational
taxonomy splits the two). Detection is safe, frequent, and read-only; recovery
is mutating and gated.

## Implementation checks

- `reason` **Drift detection is read-only.** The "are we drifted?" check must
  not mutate — it compares declared vs. live state and reports, separate from
  any remediation step. Flag a detection path that silently corrects as it
  reads.
- `reason` **A known-good re-apply path is named *before* the first apply.**
  There is no atomic rollback for a partially applied deploy; the recovery path
  is re-applying the previous versioned known-good config, not state surgery.
  Confirm this path is named in the plan's `## Rollout` (the work-loop's infra
  verification mode requires it before the first apply).
- `reason` **Early detection over hard rollback.** Because rollback is hard,
  small increments and a real smoke probe (see `observability-and-smoke`) are
  what keep rollback rarely needed. Flag a large, all-at-once apply with no
  early-detection layer in front of it.

## The auto-remediation default — an unresolved tension (surface, do not resolve)

Whether detected drift should be **gated** (detect → alert → a human decides
whether to re-apply) or **auto-synced** (continuously reconcile, auto-reverting
any out-of-band change) is a **genuine, unresolved tension** — both defaults are
well-evidenced under different conditions:

- **Gate it** — the Terraform-community default: detection is read-only and
  remediation is a separate, human-gated step, because an auto-revert can stomp
  a legitimate emergency hotfix applied out-of-band.
- **Auto-sync** — the GitOps default (Argo CD, Flux): continuous reconciliation
  treats the declared state as the single source of truth and auto-reverts
  drift, because allowing drift to persist is itself the risk.

**This module surfaces the tension; it does not pick a side.** When reviewing,
name which default the change assumes and whether that default fits *this*
resource's risk profile — an auto-syncing reconciler on a resource that takes
legitimate emergency edits is a finding; a gated detector on a
must-never-drift security control may be too lax. The right answer is
context-dependent, so flag a mismatch, don't impose one default.

## Established-pattern bypass

Resolve the repo's sanctioned drift / recovery model — the scheduled read-only
drift check, the versioned-config re-apply runbook, the GitOps reconciler — and
flag a change that introduces a divergent recovery story (state surgery as the
rollback plan, an auto-sync reconciler bolted onto a gated environment).

*Illustrative only (never normative):* `plan -refresh-only` for read-only
drift, re-applying a previous tagged config for recovery, or an Argo CD / Flux
reconciler for auto-sync, exhibit these shapes — but the checks are the
*properties* (read-only detection, a named re-apply path, a context-fit
remediation default), not any one tool.
