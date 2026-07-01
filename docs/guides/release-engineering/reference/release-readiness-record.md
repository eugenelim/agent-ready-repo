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
- Error budget: <rounds consumed> rounds, <cost> of <threshold> threshold

### Operational verdict — <PASS | PASS-WITH-NOTES | FAIL>
<quality-engineer (operational mode) findings>

### Security verdict — <PASS | PASS-WITH-NOTES | FAIL>
<security-reviewer findings on deployment config and infra changes>

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
| **Error budget** | Cost in rounds and dollars consumed against the configured caps. Consuming near the full budget is a signal worth noting even when convergence was reached — it may indicate underlying fragility. |

### Operational verdict

The `quality-engineer` subagent running in operational mode — observing the deployed system's health rather than the code's maintainability.

| Verdict | Meaning |
| --- | --- |
| `PASS` | No operational concerns. The system is healthy by all measured signals. |
| `PASS-WITH-NOTES` | Convergence was declared and the system is healthy, but the reviewer noted observations worth tracking. Notes do not block the release — they're surfaced for awareness. |
| `FAIL` | A significant operational concern was found. Convergence has not cleanly converged. G5 is not available until the failure is addressed. |

Common operational findings:
- Latency regressions on the changed surface (elevated p99 compared to baseline)
- Saturation signals (CPU or memory trending up under load)
- Migration duration that may be problematic at production data volumes
- Missing index on a newly queried column
- Error rate above threshold on non-changed routes (collateral impact)

### Security verdict

The `security-reviewer` subagent running on the deployment configuration and any infra-as-code changes in scope for this release.

| Verdict | Meaning |
| --- | --- |
| `PASS` | No security concerns found in the deployment config or infra changes. |
| `PASS-WITH-NOTES` | No blocking issues, but observations worth tracking — e.g., a credential present in a deployment variable that could be moved to the broker. |
| `FAIL` | A security concern was found that should be addressed before shipping — e.g., a credential visible in a log line, a new network path opened without a corresponding firewall rule, or a migration that backfills sensitive data in cleartext. |

The security reviewer at this stage does **not** re-review the application code — that was done during the build loop's adversarial review. It focuses on the deployment: how the artifact is configured to run, what credentials it receives, and what network boundaries it crosses.

### Budget status

| Field | What it means |
| --- | --- |
| **Rounds consumed/cap** | How many deploy-e2e-observe cycles ran vs. the maximum allowed. Hitting the cap without convergence terminates the loop and surfaces a non-convergence report (not a release-readiness record). |
| **Cost consumed/threshold** | Approximate cost of the release loop run vs. the configured spend threshold. This covers ephemeral environment runtime, not the cost of the inner loop. Exceeding the threshold during the loop triggers an escalation — the loop pauses and asks whether to continue. |

---

## Verdicts and G5 availability

G5 (the prod-ship consent gate) is available when:
- All convergence conditions are met
- No `FAIL` verdict in any section

G5 is **not** available when:
- Convergence conditions are not met (even partially)
- Any section carries a `FAIL` verdict

G5 is available despite `PASS-WITH-NOTES` verdicts — notes are surfaced for awareness, not as blockers. The human deciding at G5 can read the notes and decide whether they warrant holding the release.

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
