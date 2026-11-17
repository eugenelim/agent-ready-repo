---
title: Release-readiness record
summary: Field reference for the release-readiness record — sections, verdicts, and when G5 is available.
pack: release-engineering
kind: reference
---

# Release-readiness record

The release-readiness record is the structured output `release-lead` surfaces at G5 — the convergence assessment a human reads before ratifying the prod ship. It is not a go/no-go; it is a structured snapshot of the release's health at the moment convergence was declared.

The record is written by `release-lead` at the end of the final convergence round. It is append-only and harness-attested: the agent cannot alter it after writing, and the human ratification is recorded by the harness (not by the agent).

---

## Format

```
## Release-readiness record — <release-name> / <date>

### Convergence
- Rounds: <n> / <cap> cap
- E2e: <passing>/<total> passing, <coverage>% changed-surface coverage
- Canary: <p50> p50, <p99> p99 (<SLO status>), error rate <rate>
- Flake rate: <rate>%
- Loop budget: <rounds consumed> rounds, <cost> of <threshold> threshold

### Reliability review — <pass | blocked | insufficient-evidence>
<release-reliability-reviewer records and check-review results by stage>

### Security review — <pass | blocked | insufficient-evidence>
<release-security-reviewer records and check-review results by stage>

### Stage checks
<pre-deploy, post-deploy and final check-stage results>
- Final: human-decision-required
- Cleanup: <recorded cleanup status>
- Remaining risks: <recorded risks>
- Human decision: <pending | ratified | declined>

### Budget status
- Rounds: <consumed>/<cap>
- Cost: ~<consumed> / <threshold>
```

---

## Fields

### Convergence

| Field | What it means |
| --- | --- |
| **Rounds** | How many deploy-e2e-observe cycles ran before convergence was declared. A low round count (1–2) is typical for a healthy change. A high count (near the cap) warrants investigation even if convergence was declared. |
| **E2e** | Number of passing / total e2e tests, plus changed-surface coverage. Changed-surface coverage is the fraction of changed endpoints or code paths that have at least one passing e2e test. 100% is required for convergence. |
| **Canary** | Latency distribution (p50, p99) and error rate for the changed surface, against the configured SLOs. Canary passing SLOs is required for convergence. |
| **Flake rate** | Fraction of e2e tests that ran more than once (indicating a retry was needed). Above the configured threshold (default: 2%) blocks convergence. Flake above 2% typically means either the test is genuinely flaky (fix it) or the underlying feature is non-deterministic under load (investigate before shipping). |
| **Loop budget** | Cost in rounds and dollars consumed against the configured caps. Consuming near the full budget is a signal worth noting even when convergence was reached — it may indicate underlying fragility. |

### Reliability review

`release-reliability-reviewer` returns a focused record for each required stage.
It covers the release's operational evidence using the release-loop reliability
checklist. Keep the record and its `check-review` result together.

| Result | Meaning |
| --- | --- |
| `pass` | Every required area has resolving evidence and no open blocker. |
| `blocked` | An open blocker remains despite complete area coverage. |
| `insufficient-evidence` | An area or its evidence is missing, stale or unresolved. |

Runtime evidence must be newer than all pre-deploy evidence and must not have
been cited pre-deploy. A pre-deploy assessment cannot replace deployed checks.

### Security review

`release-security-reviewer` returns a focused record for each required security
review stage. It uses the release-loop security checklist and the same three
results as the reliability role. Save its record and `check-review` result.
Both roles bind their records to the candidate, target, permissions, stage and
checklist digest. Changed artifact, target, permissions or state assumptions
require reassessment.

Installed `quality-engineer` and `security-reviewer` agents are optional
additional reviewers. Their pass never replaces a required local area; their
refusal stops the step without a weaker fallback.

### Stage checks

Run `check-review` on each focused record before `check-stage`. The readiness
record includes the checked review pairs at pre-deploy, post-deploy and final.
Recovery requires a passing reliability record with failure evidence when that
stage applies.

| Stage | Successful result |
| --- | --- |
| Admission | `preparation` |
| Pre-deploy | `execution-eligible` with `authority_checks_required: true` |
| Post-deploy | `evaluation-or-recovery` |
| Recovery | `authorized-recovery-or-pause` |
| Final | `human-decision-required` |

Final also needs budgets, cleanup and remaining risks. A `not-torn-down`
cleanup status refuses final progression. Same-stage, later-stage and self
review records cannot serve as evidence. See [Release admission](release-admission.md)
for the commands, closed review areas, record fields and refusal codes.
Collection readiness, admission, review pass and stage progression grant no
execution or production authority. Separate isolation, credential and consent
checks still apply.

### Budget status

| Field | What it means |
| --- | --- |
| **Rounds consumed/cap** | How many deploy-e2e-observe cycles ran vs. the maximum allowed. Hitting the cap without convergence terminates the loop and surfaces a non-convergence report (not a release-readiness record). |
| **Cost consumed/threshold** | Approximate cost of the release loop run vs. the configured spend threshold. This covers ephemeral environment runtime, not the cost of the inner loop. Exceeding the threshold during the loop triggers an escalation — the loop pauses and asks whether to continue. |

---

## Verdicts and G5 availability

G5 is the human decision on production shipment. The release-readiness record
must show convergence, passing focused review pairs at every required stage,
and a successful final `check-stage` result of `human-decision-required`.
Budgets, cleanup and remaining risks must be recorded.

A `blocked` or `insufficient-evidence` review, a refused stage check, or unmet
convergence conditions stops progression. Review notes and remaining risks stay
visible for the human decision. The stage result does not ratify or execute a
production release.

---

## The G5 ratification record

When you ratify G5, the harness appends a ratification record to the release-readiness record:

```
### G5 ratification
- Ratified by: <identity>
- At: <timestamp>
- Decision: Ratified / Declined
- Reason: <optional — required if Declined>
```

This record is harness-attested: the agent cannot write or alter it. It serves as the audit trail for the prod-ship decision.

If you decline at G5, the ephemeral environment is torn down. The release-readiness record and the G5 ratification record (with your decline reason) are retained. The artifact can re-enter the release loop when you're ready.

## Wire your deploy target

The release loop needs a way to create and tear down the temporary environment. If it cannot find one, it tells you what it looked for. Ask it which deploy target it needs and what is missing. It names the missing deploy, test, or teardown step for your platform, such as a Kubernetes namespace, a cloud preview environment, or a Docker Compose file.

## When the loop runs out of rounds

If the loop runs out of rounds or budget before the checks hold, the agent reports what failed and the likely fix. Fix the build and re-enter the loop, loosen a policy that is too strict for a known flaky test, or decide not to ship this version.
