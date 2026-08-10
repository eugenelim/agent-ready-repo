# Spec: Confluence crawler check auto-login

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** @eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0035](../../rfc/0035-sso-cookie-auth-for-atlassian-pack.md); [ADR-0026](../../adr/0026-sso-consumer-resolution-in-credbroker.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

When `confluence-crawler` uses SSO-cookie authentication, `--check` verifies the
stored session and recovers one unavailable session by asking CredBroker to
refresh its registered profile headlessly, then verifies the refreshed session
with one new probe. The user sees where the automatic action comes from and
receives bounded manual-setup guidance when recovery cannot proceed. Crawls,
token authentication, and non-session failures retain their existing behavior
and never trigger automatic recapture.

## Boundaries

### Always do

- Route automatic recovery only from `auth_path == "sso-cookie"` together with
  `args.check`, before the shared crawl client-construction path.
- Preserve CredBroker's unavailable-session signal as a dedicated
  `AuthError` subtype across the Confluence client boundary, close every client
  created by a probe, and make the post-refresh probe the success criterion.
- Keep diagnostics bounded and secret-free; disclose the headless attempt on
  stderr before calling CredBroker.

### Ask first

- Ask before adding a new CLI flag, changing the existing SSO configuration
  schema, or changing the CredBroker public API.
- Ask before changing token authentication, crawl output, crawl traversal, or
  any non-`--check` exit-code contract.
- Ask before changing dependency declarations beyond a repository-required
  pack release bump.

### Never do

- Never auto-recapture during a crawl, on the token path, on any non-check
  path, or in response to a generic `AuthError` or operational failure.
- Never pass a login URL, destination, cookie, or other SSO configuration value
  to `refresh_sso_session`; the automatic call carries the profile only.
- Never launch or fall back to a headed browser, republish CredBroker, add a
  dependency, create a new module boundary, or absorb adjacent SSO backlog work.

## Testing Strategy

- **Typed recovery boundary: TDD at the client and CLI integration surfaces.**
  Focused pytest cases stub CredBroker and HTTP transport behavior to prove
  which failures are recoverable and which remain terminal. Red construction
  stubs cover AC1–AC10 and AC12; AC11 and AC13 use goal-based checks.
- **Blast-radius preservation: TDD through `main_async`.** Focused tests drive
  the real flag-based selector and demonstrate that token `--check` and SSO
  crawl paths never call refresh.
- **User disclosure and remediation: TDD through captured stderr/logging.**
  Tests assert the headless/no-window/profile-source disclosure and bounded
  exit-2 messages without inspecting or exposing credential material.
- **Pack delivery: goal-based checks.** The existing Confluence suite, Ruff,
  catalogue lint/verify, self-host projection, policy gates, and spec-status
  lint prove the shipped source and projections agree.
- **CLI journey: visual/manual QA via a stubbed subprocess invocation.** A
  throwaway SSO config, fake cookie resolution, and mock transport exercise the
  documented `--check` path without credentials, network access, or a browser.

## Acceptance Criteria

- [x] **AC1 — exact routing boundary.** Automatic recovery is reachable only
  when authentication selects `sso-cookie` and `--check` is true. A crawl,
  token-path check, or any other path makes zero refresh calls.
- [x] **AC2 — direct bounded probe.** Each SSO check probe constructs a fresh
  SSO-cookie `ConfluenceClient`, calls `whoami()` directly, and closes the
  client in a `finally` path on success or failure.
- [x] **AC3 — typed discriminator.** `SsoSessionUnavailable` subclasses
  `AuthError`. CredBroker's `SsoSessionUnavailableError` crosses client
  construction as that subtype; other CredBroker/configuration/confinement
  errors remain plain `AuthError` values. An unreadable, undecodable,
  non-JSON, or wrong-shape materialized cookie jar also raises
  `SsoSessionUnavailable`. The jar shape is a list of mapping records with
  string `name`, `domain`, and `value`; `path` is absent, null, or a string.
  Validation occurs before domain filtering or cookie attachment and emits
  fixed text naming only the profile; cookie bytes and underlying exception
  text never enter the diagnostic.
- [x] **AC4 — expired response signals.** On the SSO-cookie path only, HTTP
  401, an unfollowed 3xx login redirect, a non-JSON 2xx identity response, or a
  JSON 2xx response with no usable identity raises `SsoSessionUnavailable`.
  A usable identity is the first non-empty string among `username`,
  `displayName`, `publicName`, `email`, and `accountId`, in that order. One
  selector supplies both the client guard and check output. HTTP 403 remains a
  plain `AuthError`. Token-client response behavior remains unchanged.
- [x] **AC5 — narrow failure set.** Malformed SSO configuration,
  cookie-domain confinement, TLS, timeout, transport, 403, server,
  missing/incompatible dependency, and generic authentication failures trigger
  no recapture and retain their existing exit band.
- [x] **AC6 — disclosure before action.** Before refresh, stderr says the
  stored session is unavailable, recovery is headless, no browser window is
  shown, and the destination comes from CredBroker's registered profile.
- [x] **AC7 — profile-only, at most once.** One process calls
  `credbroker.refresh_sso_session(profile)` no more than once and passes no
  keyword arguments or destination-bearing values.
- [x] **AC8 — re-probe decides success.** A successful refresh is followed by
  exactly one fresh probe. Only that probe can return success; a failed second
  probe exits without another refresh.
- [x] **AC9 — safe refusal mapping.** Never-registered and
  interaction-required CredBroker errors exit 2, name
  `python scripts/setup_sso.py` as the manual action, and state in the latter
  case that no browser was opened. Other CredBroker errors exit 2 with a
  bounded diagnostic that does not include exception text or secret material.
- [x] **AC10 — scoped compatibility guard.** The recapture API is
  feature-detected only on the SSO-cookie `--check` path. An older CredBroker
  exits 2 there with a bounded `credbroker>=0.5.0` upgrade message and does not
  gate token or crawl paths. Existing requirements retain that floor.
- [x] **AC11 — skill guidance.** The Confluence skill instructs agents to run
  `--check`, allow its single headless recovery attempt, and request manual
  setup only when recovery refuses or fails; it never instructs the agent to
  launch setup or a browser automatically.
- [x] **AC12 — isolated coverage.** A focused Confluence test module covers
  initial success, recovery success, failed second probe, never registered,
  interaction required, generic CredBroker failure, 403, configuration and
  confinement failures, token and crawl paths, exactly one attempt, client
  closure, dependency floor, and disclosure text while stubbing all broker,
  browser, credential, and network behavior. The existing Confluence suite
  remains green.
- [x] **AC13 — release and lifecycle.** The Atlassian pack receives the
  repository-required patch version and changelog entry, projections are
  regenerated, this spec is recorded as shipped, and the resolved backlog item
  is removed without changing adjacent SSO items.

## Assumptions

- Technical: Confluence already selects `sso-cookie` via `sso-config.toml`,
  exposes a flag-based `--check`, and otherwise shares client construction with
  crawls (source: `packs/atlassian/.apm/skills/confluence-crawler/scripts/crawl_space.py`).
- Technical: Jira's shipped implementation defines the typed discriminator,
  direct probe, profile-only refresh, and one-reprobe contract (source:
  `packs/atlassian/.apm/skills/jira/scripts/jira.py` and
  `packs/atlassian/tests/skills/jira/test_check_sso_login.py`).
- Technical: Jira and Confluence already declare `credbroker>=0.5.0`, so no
  dependency-floor change is required (source: both skills' `requirements.txt`).
- Process: authentication/session work runs in full mode with security review
  (source: `docs/CONVENTIONS.md` and `.agents/skills/work-loop/SKILL.md`).
- Process: a non-cosmetic pack change requires a patch bump in both manifests,
  self-host projection, and a changelog entry (source: `packs/AGENTS.md` and
  `packs/AGENTS.local.md`).
- Product: recovery scope and manual-remediation behavior are fixed by the
  user's numbered requirements (source: user confirmation 2026-08-10).
