# The socket-budget assertion tolerates timer precision

- **Status:** Draft
- **Level:** feature

## Outcome

`pytest credbroker (windows)` does not fail on timer precision: the shared-budget
assertion in `test_socket_timeout_reaches_the_opener_and_tracks_the_budget`
compares against its budget with a tolerance, so a result that exceeds it by a
float epsilon passes.

## Opportunity

`packages/credbroker/tests/unit/test_sso_derivation.py:369` asserts
`seen[-1] <= 1.0` against a `_DerivationBudget(1.0)`, with no tolerance. On
Windows the derived socket timeout came back as `1.0000000000000142` — over by
1.4e-14 — and reddened `pytest credbroker (windows)`, which in turn reddened
`make build-check (windows)`, since that job aggregates the Windows suites
(`credbroker=failure agentbundle=success lock-semantics=success`).

The invariant the assertion protects is real and worth keeping: a late hop must
not outlive the shared budget. Only the exact-comparison form is wrong. A
tolerance of one ULP, or `math.isclose` with a small `rel_tol`, preserves the
guarantee while surviving platform timer arithmetic.

Observed on PR #1161, whose diff touches no credbroker path and no
Windows-specific path; the same suite passed on Linux in the same run.

## Assumptions

- The failure is precision, not a behavioural regression: 1.4e-14 over a 1.0
  budget cannot represent a real timeout overrun.
- Loosening this one comparison does not weaken the neighbouring assertion
  `0 < seen[-1] <= _DERIVE_SOCKET_TIMEOUT_S`, which is a separate bound.

## Source

- Mode: repo-origin
- Locator: packages/credbroker/tests/unit/test_sso_derivation.py
- Revision: local-2026-08-29
