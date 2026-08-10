# Plan: Confluence crawler check auto-login

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> the changelog records why.

## Approach

Adapt Jira's proven recovery flow to Confluence's flag-based entry point without
copying Jira's separate `--register` or destination-attestation surface. First,
add a narrow client subtype that preserves the unavailable-session signal while
leaving configuration, confinement, 403, and operational failures terminal.
Second, route only SSO-cookie `--check` to a direct probe → one profile-only
refresh → one new probe handler before shared crawl construction. Finally,
update the skill guidance and required pack release/lifecycle artifacts, project
the source, and run the full repository gates and security reviews.

## Constraints

- RFC-0035 keeps SSO-cookie and token selection explicit and fail-closed.
- ADR-0026 keeps SSO consumer resolution and refresh in CredBroker; the
  Confluence client preserves its typed signal instead of recreating broker
  state or accepting a destination.
- CredBroker 0.6.0 is already published. This change consumes its existing
  `refresh_sso_session(profile)` API and does not modify or publish CredBroker.
- `.apm/` is the source of truth; self-host projections are regenerated only
  after all pack edits.
- Pack release policy requires an Atlassian patch bump in `pack.toml` and the
  Claude plugin manifest plus an adopter-facing changelog entry.

## Construction tests

**Integration tests:**

- `packs/atlassian/tests/skills/confluence-crawler/test_check_sso_login.py`
  drives the real selector and `main_async` with fake clients/broker modules;
  no credential, profile, browser, or network state is accessed.
- The full existing `packs/atlassian/tests/skills/confluence-crawler/` suite
  proves token and crawl behavior stays compatible.

**Manual verification:**

- Run the flag parser and `main_async` against a throwaway config with the real
  selector/client factory and stubbed broker/HTTP transport. Record exit 0, two
  probes, one refresh, and the four-part stderr disclosure in
  `docs/specs/confluence-crawler-check-auto-login/manual-qa.md`. The session
  stops after the second stubbed `whoami()` result. Real credentials, browser
  state, browser launch, network access, setup, and crawl output are explicitly
  not exercised.
- Record the pre-implementation secure-design verdict and post-implementation
  diff verdict in
  `docs/specs/confluence-crawler-check-auto-login/security-review.md`, including
  any findings and their resolutions.

## Design (LLD)

### Interfaces & contracts

No new public contract is introduced. The existing CLI flag and CredBroker API
are consumed unchanged. `SsoSessionUnavailable(AuthError)` is an internal
Confluence-client discriminator used by the CLI boundary. Traces to AC1–AC10.

### Failure, edge cases & resilience

The first probe has exactly one recoverable exception type. All other auth and
operational failures preserve their current exits. Refresh has three mapped
failure families and no retry. The second probe catches the ordinary Confluence
error taxonomy and cannot return to refresh. Traces to AC3–AC10.

### Dependencies & integration

`crawl_space.py` lazily feature-detects the existing CredBroker recapture API
only after both SSO authentication and `--check` are known. `refresh_sso_session`
receives the profile from validated SSO config and resolves the destination from
CredBroker's registered profile. Traces to AC1, AC6, AC7, AC10.

## Tasks

### T1: The Confluence client exposes only unavailable SSO sessions as recoverable

**Depends on:** none

**Touches:** `packs/atlassian/.apm/skills/confluence-crawler/scripts/_client.py`, `packs/atlassian/tests/skills/confluence-crawler/test_check_sso_login.py`

**Verification mode:** TDD.

**Tests:**

- Red tests prove the subtype relationship and typed mapping for CredBroker
  unavailable sessions, HTTP 401/3xx, and unusable SSO identity responses
  (AC3, AC4).
- Red tests prove unreadable, undecodable, non-JSON, and wrong-shape cookie jars
  are recoverable without including jar or exception bytes in diagnostics
  (AC3).
- Red tests prove configuration/confinement failures and HTTP 403 stay plain
  `AuthError`, while token response behavior stays unchanged (AC3–AC5).

`stub: true`

```python
import json

import credbroker
import httpx
import pytest

import scripts._client as _client


def test_credbroker_unavailable_crosses_as_the_only_recoverable_auth_error(
    monkeypatch, sso_config
):
    # STUB: AC3
    monkeypatch.setattr(
        credbroker,
        "load_sso_cookies",
        lambda profile: (_ for _ in ()).throw(
            credbroker.SsoSessionUnavailableError("unavailable")
        ),
    )
    with pytest.raises(_client.SsoSessionUnavailable):
        _client.ConfluenceClient.from_sso_cookies(sso_config)
    assert issubclass(_client.SsoSessionUnavailable, _client.AuthError)
    raise NotImplementedError  # STUB: AC3


@pytest.mark.parametrize("payload", [b"{not json", b'"wrong shape"', b"\xff"])
def test_materialized_jar_failures_are_recoverable_without_leaking_bytes(
    monkeypatch, tmp_path, sso_config, payload
):
    # STUB: AC3
    jar = tmp_path / "session.jar"
    jar.write_bytes(payload)
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: jar)
    with pytest.raises(_client.SsoSessionUnavailable) as exc:
        _client.ConfluenceClient.from_sso_cookies(sso_config)
    assert "profile" in str(exc.value)
    assert "not json" not in str(exc.value)
    raise NotImplementedError  # STUB: AC3


@pytest.mark.parametrize(
    "record",
    [
        {"domain": "corp.example.com", "value": "v"},
        {"name": "sid", "domain": 7, "value": "v"},
        {"name": "sid", "domain": "corp.example.com", "value": None},
        {"name": "sid", "domain": "corp.example.com", "value": "v", "path": 7},
        "not-a-record",
    ],
)
def test_cookie_record_shape_is_validated_before_filter_or_attachment(
    monkeypatch, tmp_path, sso_config, record
):
    # STUB: AC3
    jar = tmp_path / "session.jar"
    jar.write_text(json.dumps([record]), encoding="utf-8")
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: jar)
    monkeypatch.setattr(
        credbroker,
        "filter_jar_to_domains",
        lambda *args, **kwargs: pytest.fail("invalid record reached domain filtering"),
    )
    monkeypatch.setattr(
        _client.httpx,
        "AsyncClient",
        lambda *args, **kwargs: pytest.fail("invalid record reached cookie attachment"),
    )
    with pytest.raises(_client.SsoSessionUnavailable) as exc:
        _client.ConfluenceClient.from_sso_cookies(sso_config)
    assert "session.jar" not in str(exc.value)
    assert exc.value.__cause__ is not None
    raise NotImplementedError  # STUB: AC3


@pytest.mark.parametrize("extra", [{}, {"path": None}, {"path": "/wiki"}])
def test_cookie_record_accepts_missing_null_or_string_path(extra):
    # STUB: AC3
    record = {
        "name": "sid",
        "domain": "corp.example.com",
        "value": "v",
        **extra,
    }
    assert _client._validate_jar_shape([record]) is None
    raise NotImplementedError  # STUB: AC3


@pytest.mark.parametrize("status", [401, 302])
def test_sso_expiry_responses_use_the_typed_signal(cookie_client, status):
    # STUB: AC4
    cookie_client.respond(httpx.Response(status))
    with pytest.raises(_client.SsoSessionUnavailable):
        cookie_client.run_whoami()
    raise NotImplementedError  # STUB: AC4


def test_identity_selector_is_exact_and_403_is_not_recoverable(cookie_client):
    # STUB: AC4 / AC5
    assert _client.identity_of({"username": "Example User"}) == "Example User"
    assert _client.identity_of({"displayName": None, "accountId": "abc"}) == "abc"
    assert _client.identity_of({"username": 7}) is None
    cookie_client.respond(httpx.Response(403))
    with pytest.raises(_client.AuthError) as exc:
        cookie_client.run_whoami()
    assert not isinstance(exc.value, _client.SsoSessionUnavailable)
    raise NotImplementedError  # STUB: AC4
```

**Approach:**

- Add `SsoSessionUnavailable(AuthError)` and preserve
  `credbroker.SsoSessionUnavailableError` before the generic broker catch.
- Validate the materialized jar as a list of cookie mappings with typed
  `name`, `domain`, `value`, and optional/null/string `path` before calling the
  domain filter or attaching cookies; map read/parse/shape failures to fixed
  profile-only text with the cause chained.
- Raise the subtype only at the SSO expired/unavailable response sites; share
  identity selection between the client guard and check output.

**Done when:** the focused discriminator tests pass and no generic `AuthError`
is recoverable.

### T2: SSO `--check` performs one disclosed refresh and one decisive re-probe

**Depends on:** T1

**Touches:** `packs/atlassian/.apm/skills/confluence-crawler/scripts/crawl_space.py`, `packs/atlassian/tests/skills/confluence-crawler/test_check_sso_login.py`

**Verification mode:** TDD plus stubbed CLI journey.

**Tests:**

- Red flow tests cover initial success, recovery success, failed second probe,
  never registered, interaction required, generic broker failure, 403,
  exactly-one refresh, direct probe, and reliable closure (AC1–AC9, AC12).
- Red blast-radius tests prove token `--check`, SSO crawl, malformed config,
  confinement, and old/missing CredBroker paths do not refresh (AC1, AC5, AC10).
- Captured stderr proves the four-part disclosure and bounded manual
  remediation, while call recording proves profile-only refresh (AC6–AC10).

`stub: true`

```python
import credbroker
import pytest

import scripts.crawl_space as crawl_space


def test_healthy_initial_probe_succeeds_without_refresh(
    sso_check, broker_recorder
):
    # STUB: AC1 / AC2 / AC12
    sso_check.probes = [{"username": "Example User"}]
    assert sso_check.run() == crawl_space.EXIT_OK
    assert sso_check.probe_count == 1
    assert sso_check.close_count == 1
    assert broker_recorder.refresh_calls == []
    raise NotImplementedError  # STUB: AC12


def test_unavailable_check_refreshes_profile_once_then_reprobes(
    sso_check, broker_recorder, capsys
):
    # STUB: AC1 / AC2 / AC6 / AC7 / AC8
    sso_check.probes = [crawl_space.SsoSessionUnavailable("expired"), {"username": "ok"}]
    assert sso_check.run() == crawl_space.EXIT_OK
    assert broker_recorder.refresh_calls == [("confluence",)]
    assert sso_check.probe_count == 2
    assert sso_check.close_count == 2
    disclosure = capsys.readouterr().err.lower()
    for phrase in ("unavailable", "headless", "no browser window", "registered profile"):
        assert phrase in disclosure
    raise NotImplementedError  # STUB: AC1


def test_failed_second_probe_never_refreshes_twice(sso_check, broker_recorder):
    # STUB: AC7 / AC8
    sso_check.probes = [
        crawl_space.SsoSessionUnavailable("expired"),
        crawl_space.SsoSessionUnavailable("still expired"),
    ]
    assert sso_check.run() == crawl_space.EXIT_USER_ACTION
    assert broker_recorder.refresh_calls == [("confluence",)]
    assert sso_check.probe_count == 2
    raise NotImplementedError  # STUB: AC8


def test_never_registered_names_manual_setup_without_registering(
    sso_check, broker_recorder, capsys
):
    # STUB: AC9 / AC12
    sso_check.probes = [crawl_space.SsoSessionUnavailable("expired")]
    broker_recorder.refresh_error = credbroker.SsoProfileNotRegisteredError("detail")
    assert sso_check.run() == crawl_space.EXIT_USER_ACTION
    stderr = capsys.readouterr().err
    assert "python scripts/setup_sso.py" in stderr
    assert broker_recorder.register_calls == []
    assert sso_check.probe_count == 1
    raise NotImplementedError  # STUB: AC9


def test_interaction_required_is_bounded_and_never_registers(
    sso_check, broker_recorder, capsys
):
    # STUB: AC9 / AC12
    sso_check.probes = [crawl_space.SsoSessionUnavailable("expired")]
    broker_recorder.refresh_error = credbroker.SsoInteractionRequiredError("secret detail")
    assert sso_check.run() == crawl_space.EXIT_USER_ACTION
    assert broker_recorder.register_calls == []
    stderr = capsys.readouterr().err
    assert "No browser was opened" in stderr
    assert "python scripts/setup_sso.py" in stderr
    assert "secret detail" not in stderr
    raise NotImplementedError  # STUB: AC9


def test_generic_credbroker_failure_omits_exception_text_and_does_not_reprobe(
    sso_check, broker_recorder, capsys
):
    # STUB: AC9 / AC12
    sso_check.probes = [crawl_space.SsoSessionUnavailable("expired")]
    broker_recorder.refresh_error = credbroker.SsoRecaptureFailedError(
        "SECRET ENGINE DETAIL"
    )
    assert sso_check.run() == crawl_space.EXIT_USER_ACTION
    stderr = capsys.readouterr().err
    assert "SECRET ENGINE DETAIL" not in stderr
    assert sso_check.probe_count == 1
    assert len(broker_recorder.refresh_calls) == 1
    raise NotImplementedError  # STUB: AC9


@pytest.mark.parametrize(
    "case",
    ["http-403", "malformed-config", "confinement", "missing-credbroker"],
)
def test_terminal_failure_matrix_never_refreshes(
    case, terminal_failure_check, broker_recorder
):
    # STUB: AC5 / AC10 / AC12
    assert terminal_failure_check.run(case) in {
        crawl_space.EXIT_ERROR,
        crawl_space.EXIT_USER_ACTION,
    }
    assert broker_recorder.refresh_calls == []
    raise NotImplementedError  # STUB: AC5


def test_token_crawl_and_generic_auth_paths_never_refresh(
    token_check, sso_crawl, generic_auth_check, broker_recorder
):
    # STUB: AC1 / AC5
    token_check.run()
    sso_crawl.run()
    generic_auth_check.run()
    assert broker_recorder.refresh_calls == []
    raise NotImplementedError  # STUB: AC5


def test_selector_time_old_credbroker_is_bounded_only_for_sso_check(
    old_or_missing_credbroker, sso_check, token_check, sso_crawl, capsys
):
    # STUB: AC10 / AC12
    assert sso_check.run() == crawl_space.EXIT_USER_ACTION
    assert "credbroker>=0.5.0" in capsys.readouterr().err
    token_check.run()
    sso_crawl.run()
    assert old_or_missing_credbroker.refresh_calls == []
    raise NotImplementedError  # STUB: AC10


def test_probe_calls_whoami_directly_and_closes_on_failure(
    sso_check, monkeypatch
):
    # STUB: AC2 / AC12
    async def must_not_route_through_run_check(client, flavor):
        raise AssertionError("the SSO probe must call whoami directly")

    monkeypatch.setattr(crawl_space, "_run_check", must_not_route_through_run_check)
    sso_check.probes = [crawl_space.SsoSessionUnavailable("expired")]
    sso_check.run()
    assert sso_check.close_count == 1
    raise NotImplementedError  # STUB: AC2
```

**Approach:**

- Feature-detect CredBroker after selecting SSO plus `--check`, then route to a
  dedicated handler before shared client construction. If SSO config selection
  itself raises a CredBroker import/missing-symbol error, map it to the same
  floor message only when `--check` is true; malformed configuration remains
  the ordinary fail-closed selector error, and token/crawl paths gain no global
  guard.
- Probe with direct `whoami()` and `finally` closure. Catch only the typed
  unavailable signal before refresh; map broker errors; re-probe once.

**Done when:** the new focused module passes with all external behavior stubbed
and the projected CLI harness records two probes and one refresh.

### T3: Guidance, pack release, projection, and workspace lifecycle agree

**Depends on:** T2

**Touches:** `packs/atlassian/.apm/skills/confluence-crawler/SKILL.md`, `packs/atlassian/pack.toml`, `packs/atlassian/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `docs/specs/README.md`, `docs/specs/confluence-crawler-check-auto-login/{manual-qa,security-review}.md`, `workspace.toml`, generated projections

**Verification mode:** goal-based checks.

**Tests:**

- Skill text states the check-first/single-headless-attempt/manual-fallback
  sequence and never instructs automatic setup (AC11).
- Version parity, changelog, self-host projection, catalogue lint/verify,
  policy, and spec-status checks pass (AC12, AC13).
- `security-review.md` records clean spec-stage and diff-stage security verdicts
  after any findings are resolved (AC5–AC10, AC13).

`no stub (goal-based and review-artifact checks)`

**Approach:**

- Update adopter guidance, bump Atlassian 0.8.1 → 0.8.2, add the changelog,
  regenerate projections, and record the shipped spec while removing only the
  resolved backlog entry.

**Done when:** the full Confluence suite and repository-required release,
projection, policy, and lifecycle gates pass.

## Rollout

The behavior ships directly in Atlassian pack 0.8.2. Rollback is the pack patch
revert; there is no data migration, persistent schema change, infrastructure,
or CredBroker release. Existing profiles remain the only automatic destination
source.

## Risks

- Catching `AuthError` instead of the subtype would turn permission,
  confinement, and transport problems into browser automation attempts.
- Routing after shared client construction would make crawls recover implicitly
  or swallow the construction-time discriminator before the dedicated handler.
- Treating refresh success as authentication success would report a working
  session without proving the refreshed cookies resolve.
- Importing or checking the recapture API globally would regress token or crawl
  paths for adopters with older CredBroker installations.

## Changelog

- 2026-08-10: Initial full-mode plan, adapted from Jira's shipped flow and
  restricted to Confluence's existing SSO-cookie `--check` flag.
- 2026-08-10: Added field-level cookie-jar validation, selector-time dependency
  handling, concrete TDD stubs, and named QA/security artifacts in response to
  pre-implementation review. Scope and plan approval derive from the user's
  implementation brief and explicit proceed steer; loop state files are
  unavailable under the managed read-only shell.
