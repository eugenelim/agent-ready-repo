# Verification ledger — portable-catalogue-authentication

Execution observations for run `4bf9c822-709f-45d8-9a79-b400a705f3a8`. The
approved `spec.md` and `plan.md` hold the obligations; this file holds what
execution observed against them.

## Stub verdicts

| Task | Stub test | Materialized at | Byte identity | Observed red |
| --- | --- | --- | --- | --- |
| T1 | `test_resolve_http_access_returns_public_anonymous_variant` | `packages/credbroker/tests/unit/test_http_access.py` | `cmp` against the plan block: identical | Collection error: `ImportError: cannot import name 'AnonymousHttpAccess' from 'credbroker'` |

## Discoveries

- **The vendored user-library floor is a drift-gated projection.**
  `packages/agentbundle/agentbundle/build/user_libs.py` projects
  `packages/credbroker/credbroker/` byte-faithfully into
  `packs/credential-brokers/.apm/user-libs/credbroker/` and
  `.agentbundle/lib/credbroker/`, and `make build-check` fails on drift. Any
  credbroker source change therefore regenerates both copies through
  `make build-self`, so the committed floor moves to 0.7 with this change. The
  AC-0003 co-location test cannot read its 0.6 floor from the committed tree.
  It reads the 0.6 package source from the `credbroker-v0.6.0` tag instead; the
  roster job checks out with `fetch-depth: 0`, so the tag is reachable in CI.
