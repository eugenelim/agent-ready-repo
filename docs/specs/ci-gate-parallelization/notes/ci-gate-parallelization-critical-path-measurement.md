# CI gate parallelization critical-path measurement

This note closes the deferred measurement recorded by
`ci-gate-parallelization-critical-path-measurement`. It preserves historical
evidence for the shipped specification; it does not amend that frozen contract.

## Evidence

- Pull request: [#1203](https://github.com/eugenelim/agent-ready-repo/pull/1203)
- Workflow run: [33536347836](https://github.com/eugenelim/agent-ready-repo/actions/runs/33536347836)
- Event class: docs-only pull request; the sole changed file was
  `docs/product/changelog.md`.
- Configuration boundary: the pull request did not edit `SAST_CONFIG`, the
  SAST relevance predicate, or the build-check workflow.

Durations are calculated from the GitHub Actions job timestamps in UTC.

| Job | Started | Completed | Duration | AC11 result |
| --- | --- | --- | ---: | --- |
| `make build-check` (required-check aggregator) | 17:18:29 | 17:18:39 | 10s | Meets the 200s merge-blocking budget |
| `gate-main` | 17:13:24 | 17:18:26 | 302s | Misses the 200s work-job budget by 102s |
| `gate-sast` | 17:13:50 | 17:14:17 | 27s | Meets the 200s work-job budget |
| `gate-export-boundary` | 17:13:26 | 17:16:10 | 164s | Meets the 200s work-job budget |

All four jobs concluded successfully, satisfying AC15's live docs-only,
non-relevant-diff proof without narrowing the SAST configuration.

## Miss diagnosis

The `gate-main` miss is cumulative rather than attributable to runner queue
time. Its two largest measured steps were:

- `Run make build-check`: 127s (17:13:37–17:15:44).
- `pytest catalogue-test carve-out destinations (RFC-0082)`: 74s
  (17:16:34–17:17:48).

Those steps account for 201s. Setup and the remaining checks account for about
101s collectively. This diagnoses the greater-than-20-second miss required by
AC11; another measurement loop is not needed to close the deferred evidence
task. The unresolved optimization work is owned by
[`ci-gate-main-runtime-budget`](../../../product/intents/ci-gate-main-runtime-budget.md).
