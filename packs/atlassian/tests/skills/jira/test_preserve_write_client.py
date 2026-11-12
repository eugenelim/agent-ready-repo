"""Jira client enforces the preserve-first guard at its request chokepoint.

Driven against a recording fake transport (``conftest.FakeJira``). Each test names
the spec criteria (ACn) it covers. Home is redirected to a temp dir for every test.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
from pathlib import Path
from typing import Any

import _client
import _preserve_write as pw
import httpx
import pytest
from _sso_config import SsoConfig

BASE = "https://jira.example.invalid"
KEY = "PROJ-12"
SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira"
PROFILE = SKILL_ROOT.parent / "jira-brief-intake/references/intake-profile.json"
INTAKE_BASE = "https://tracker.example.test"


@pytest.fixture(autouse=True)
def _home(tracker_home: Path) -> Path:
    return tracker_home


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def issues() -> dict[str, dict[str, Any]]:
    return {KEY: {"summary": "old summary", "description": "old description"}}


def credentials(flavor: str, base: str = BASE) -> _client.Credentials:
    return _client.Credentials(
        base_url=base, token="fixture", flavor=flavor,
        email="user@example.invalid" if flavor == "cloud" else None,
    )


@pytest.fixture(params=["server", "cloud"])
def flavor(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def fake(make_fake_jira: Any, flavor: str) -> Any:
    return make_fake_jira(BASE, flavor, issues())


def verified(
    flavor: str, *, notify: bool = True, fields: dict[str, dict[str, Any]] | None = None
) -> pw.VerifiedPlan:
    fields = fields or {
        "summary": {"current": "old summary", "proposed": "new summary", "disposition": "replace"},
        "labels": {"current": ["a"], "proposed": ["a"], "disposition": "keep"},
    }
    plan = pw.build_plan(
        target=KEY, flavor=flavor, base_url=BASE, method="PUT", notify=notify, fields=fields
    )
    return pw.verify_plan(plan, plan.digest)


async def _with_client(flavor: str, fn: Any) -> Any:
    async with _client.JiraClient(credentials(flavor)) as client:
        return await fn(client)


def call(flavor: str, fn: Any) -> Any:
    return run(_with_client(flavor, fn))


# --- AC6, AC30: deny by default --------------------------------------------------------------


def test_direct_update_issue_without_plan_is_refused_with_zero_requests(fake, flavor):
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.update_issue(KEY, {"summary": "x"}))
    assert fake.requests == []


def test_plan_with_changed_contents_cannot_be_verified_so_nothing_is_sent(fake, flavor):
    plan = pw.build_plan(
        target=KEY, flavor=flavor, base_url=BASE, method="PUT", notify=True,
        fields={"summary": {"current": "a", "proposed": "b", "disposition": "replace"}},
    )
    edited = dataclasses.replace(
        plan, fields={"summary": pw.FieldPlan("a", "EVIL", "replace")}
    )
    with pytest.raises(pw.GuardRefused):
        pw.verify_plan(edited, plan.digest)
    assert fake.requests == []


@pytest.mark.parametrize("method", ["PUT", "PATCH", "POST", "DELETE"])
@pytest.mark.parametrize(
    "target",
    [
        "/rest/api/3/issue/PROJ-12",                          # relative
        "https://jira.example.invalid/rest/api/3/issue/PROJ-12",  # absolute, same origin
        "/rest/api/2/issue/PROJ-12",                          # other version prefix
        "/rest/api/latest/issue/PROJ-12",                     # versioned alias
        "/rest/agile/1.0/issue/PROJ-12/rank",                 # Agile
        "/rest/api/3/bulk/issues/fields",                     # bulk edit
        "/rest/api/3/issue/PROJ-12%2Fcomment",                # percent-encoded separator
        "/rest/api/3/issue/PROJ-12/%2e%2e/PROJ-13",           # percent-encoded ..
        "/rest/api/3/issue/PROJ-12/",                         # trailing slash
        "/rest/api/3/issue/../issue/PROJ-12",                 # ..
        "/rest/api/3/issue;x=1/PROJ-12",                      # ; matrix parameter
        "/rest/api/3/issue/PROJ-12/comment/10000",            # comment edit
        "/rest/api/3/issue/PROJ-12/properties/k",
        "/rest/api/3/issue/",                                 # create route with trailing slash
    ],
)
def test_every_non_allowlisted_route_form_is_refused_without_a_plan(fake, flavor, method, target):
    # AC30, AC31: whatever the prefix or path form, no plan means no request.
    # (POST to the exact create route is the allowlist; the forms above are not it.)
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c._request(method, target, json_body={"fields": {"summary": "x"}}))
    assert fake.requests == []


def test_a_guarded_route_stays_refused_when_reached_through_raw(fake, flavor):
    for method, path, body in (
        ("PUT", "issue/PROJ-12", {"fields": {"summary": "x"}}),
        ("PATCH", "/rest/api/3/issue/PROJ-12", {"fields": {"summary": "x"}}),
        ("PUT", "issue/PROJ-12/comment/10000", {"body": "x"}),   # comment edit
        ("DELETE", "issue/PROJ-12", None),
        ("POST", "issue/PROJ-12/transitions",
         {"transition": {"id": "31"}, "fields": {"summary": "x"}}),
        ("POST", "issue/PROJ-12/transitions",
         {"transition": {"id": "31"}, "update": {"labels": [{"add": "x"}]}}),
        ("POST", "https://other.example.invalid/rest/api/3/issue", {"fields": {}}),
    ):
        with pytest.raises(pw.GuardRefused):
            call(flavor, lambda c, m=method, p=path, b=body: c.raw(m, p, json_body=b))
    assert fake.requests == []


# --- AC8, AC9, AC10: a verified plan authorizes exactly one request -------------------------------


def test_verified_plan_sends_exactly_one_put_with_the_resolved_body_only(fake, flavor):
    v = verified(flavor)
    call(flavor, lambda c: c.update_issue(
        KEY, v.write.body, notify_users=v.plan.notify, verified_plan=v))
    assert len(fake.writes) == 1
    sent = fake.writes[0]
    assert (sent.method, sent.url) == (v.write.method, v.write.url)
    assert sent.body == v.write.body
    assert set(sent.body) == {"fields"}                       # AC10: no other key
    assert set(sent.body["fields"]) == {"summary"}            # AC10: keep field omitted


def test_notify_false_is_in_the_bound_url(fake, flavor):
    v = verified(flavor, notify=False)
    assert v.write.url.endswith("?notifyUsers=false")
    call(flavor, lambda c: c.update_issue(
        KEY, v.write.body, notify_users=False, verified_plan=v))
    assert fake.writes[0].url == v.write.url
    # The plan's notify setting is part of what it authorizes.
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.update_issue(
            KEY, v.write.body, notify_users=True, verified_plan=v))
    assert len(fake.writes) == 1


@pytest.mark.parametrize(
    "variant",
    ["other_key", "other_method", "other_body", "extra_key", "other_host", "extra_param"],
)
def test_a_verified_plan_does_not_authorize_any_other_request(fake, flavor, variant):
    v = verified(flavor)
    api = fake.api
    body = v.write.body
    method, path, params = "PUT", f"{api}/issue/{KEY}", None
    if variant == "other_key":
        path = f"{api}/issue/PROJ-13"
    elif variant == "other_method":
        method = "PATCH"
    elif variant == "other_body":
        body = {"fields": {"summary": "different"}}
    elif variant == "extra_key":
        body = {**body, "update": {}}
    elif variant == "other_host":
        path = f"https://other.example.invalid{api}/issue/{KEY}"
    else:
        params = {"x": "1"}
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c._request(
            method, path, params=params, json_body=body, verified_plan=v))
    assert fake.requests == []


# --- AC31: deletes -------------------------------------------------------------------------------


def test_delete_goes_only_through_delete_issue_with_confirm(fake, flavor):
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.delete_issue(KEY))
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.delete_issue(KEY, confirm=False))
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.raw("DELETE", f"issue/{KEY}"))
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c._request("DELETE", f"{fake.api}/issue/{KEY}"))
    # Confirmation cannot widen the route: only an issue path is deletable.
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c._request(
            "DELETE", f"{fake.api}/project/PROJ", confirmed_delete=True))
    assert fake.requests == []
    call(flavor, lambda c: c.delete_issue(KEY, confirm=True))
    assert [(r.method, r.path) for r in fake.writes] == [("DELETE", f"{fake.api}/issue/{KEY}")]


# --- AC32: transitions with field content ------------------------------------------------------


def test_transition_with_fields_is_refused_before_the_name_lookup(fake, flavor):
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.transition_issue(
            KEY, transition_name="Done", fields={"resolution": {"name": "Done"}}))
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c.transition_issue(
            KEY, transition_id="31", fields={"summary": "x"}))
    for body in (
        {"transition": {"id": "31"}, "fields": {"summary": "x"}},
        {"transition": {"id": "31"}, "update": {"labels": []}},
    ):
        with pytest.raises(pw.GuardRefused):
            call(flavor, lambda c, b=body: c.raw("POST", f"issue/{KEY}/transitions", json_body=b))
        with pytest.raises(pw.GuardRefused):
            call(flavor, lambda c, b=body: c._request(
                "POST", f"{fake.api}/issue/{KEY}/transitions", json_body=b))
    assert fake.requests == []        # the name lookup GET included


def test_transition_without_fields_sends_the_lookup_and_one_post(fake, flavor):
    call(flavor, lambda c: c.transition_issue(KEY, transition_name="done"))
    assert [(r.method, r.path.rsplit("/", 1)[-1]) for r in fake.requests] == [
        ("GET", "transitions"), ("POST", "transitions"),
    ]
    assert fake.writes[0].body == {"transition": {"id": "31"}}


# --- AC33: origin and override headers ------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [
        "https://other.example.invalid/rest/api/3/issue",        # other host
        "http://jira.example.invalid/rest/api/3/issue",          # http downgrade
        "https://jira.example.invalid:8443/rest/api/3/issue",    # port change
    ],
)
def test_other_origin_is_refused_even_on_an_allowlisted_route(fake, flavor, target):
    path = target.replace("/rest/api/3", fake.api)
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c._request("POST", path, json_body={"fields": {}}))
    assert fake.requests == []


@pytest.mark.parametrize(
    "header", ["X-HTTP-Method-Override", "x-http-method", "X-Method-Override"]
)
def test_method_override_header_is_refused_even_on_an_allowlisted_route(fake, flavor, header):
    with pytest.raises(pw.GuardRefused):
        call(flavor, lambda c: c._request(
            "POST", f"{fake.api}/issue", json_body={"fields": {}},
            extra_headers={header: "DELETE"}))
    assert fake.requests == []


# --- AC34: no redirect following for writes ---------------------------------------------------------


def test_a_redirected_write_is_not_followed(fake, flavor):
    fake.override = lambda rec: (
        httpx.Response(307, headers={"Location": "https://other.example.invalid/x"})
        if rec.method != "GET" else None
    )
    with pytest.raises(_client.JiraError, match="redirect"):
        call(flavor, lambda c: c.create_issue({"summary": "x"}))
    v = verified(flavor)
    with pytest.raises(_client.JiraError, match="redirect"):
        call(flavor, lambda c: c.update_issue(
            KEY, v.write.body, notify_users=True, verified_plan=v))
    assert [r.method for r in fake.requests] == ["POST", "PUT"]   # one each, nothing followed


def test_a_redirected_read_is_still_followed(fake, flavor):
    def hop(rec: Any) -> httpx.Response | None:
        if rec.path == f"{fake.api}/issue/{KEY}" and "moved" not in rec.query:
            return httpx.Response(
                302, headers={"Location": f"{BASE}{fake.api}/issue/{KEY}?fields=summary&moved=1"})
        return None

    fake.override = hop
    issue = call(flavor, lambda c: c.get_issue(KEY, fields="summary"))
    assert issue["key"] == KEY
    assert len(fake.requests) == 2


# --- AC35: allowlisted writes are not refused by the guard -----------------------------------------


def test_allowlisted_writes_reach_the_wire_with_token_auth(fake, flavor, tmp_path):
    attachment = tmp_path / "note.txt"
    attachment.write_text("hello", encoding="utf-8")

    async def go(c: _client.JiraClient) -> None:
        await c.create_issue({"summary": "new"})
        await c.add_comment(KEY, "hello")
        await c.add_attachment(KEY, attachment)
        await c.transition_issue(KEY, transition_id="31")
        if flavor == "cloud":
            async for _ in c.iter_search("project = PROJ"):
                pass

    call(flavor, go)
    sent = [(r.method, r.path.removeprefix(fake.api)) for r in fake.writes]
    expected = [
        ("POST", "/issue"), ("POST", f"/issue/{KEY}/comment"),
        ("POST", f"/issue/{KEY}/attachments"), ("POST", f"/issue/{KEY}/transitions"),
    ]
    if flavor == "cloud":
        expected.append(("POST", "/search/jql"))
    assert sent == expected


def test_raw_post_to_an_allowlisted_route_is_not_refused(fake, flavor):
    call(flavor, lambda c: c.raw("POST", f"issue/{KEY}/comment", json_body={"body": "x"}))
    assert len(fake.writes) == 1


# --- AC37: the receipt refusal still fires, and first -----------------------------------------------


def _receipt(action: str) -> Any:
    from agentbundle._data.work_intake_refresh import RemoteActionReceipt

    return RemoteActionReceipt(
        "confirmation-1", "a" * 64, "1.0", "b" * 64, "approver@example.com", "maintainer",
        "2026-08-17T12:00:00Z", "current-human-session", action, "EX-1",
    )


def _intake_client() -> _client.JiraClient:
    policy = _client.IntakeRequestPolicy.from_profile(
        PROFILE, INTAKE_BASE,
        resolver=lambda host, port, **_k: [(None, None, None, None, ("93.184.216.34", port))],
    )
    return _client.JiraClient(credentials("server", INTAKE_BASE), intake_policy=policy)


@pytest.fixture
def intake_fake(make_fake_jira: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    return make_fake_jira(INTAKE_BASE, "server", {"EX-1": {"summary": "s"}})


def test_intake_policy_refuses_unreceipted_writes_before_the_guard(intake_fake):
    async def go() -> None:
        async with _intake_client() as c:
            for method, path in (("PUT", "/rest/api/2/issue/EX-1"),
                                 ("POST", "/rest/api/2/issue/EX-1/comment"),
                                 ("POST", "/rest/api/2/issue")):
                with pytest.raises(_client.JiraError, match="read-only") as info:
                    await c._request(method, path, json_body={})
                assert not isinstance(info.value, pw.GuardRefused)
            # Wrong-path receipt: still the intake refusal, not the guard.
            with pytest.raises(_client.JiraError, match="read-only"):
                await c._request(
                    "POST", "/rest/api/2/issue/EX-2/comment", json_body={},
                    guarded_write=_receipt("comment"))
            # transition by name: refused before the lookup, by the intake rule.
            with pytest.raises(_client.JiraError, match="read-only"):
                await c.transition_issue("EX-1", transition_name="Done")

    run(go())
    assert intake_fake.requests == []


def test_a_pending_receipt_still_authorizes_its_endpoint_through_the_guard(intake_fake):
    async def go() -> None:
        async with _intake_client() as c:
            await c.add_comment("EX-1", "hi", guarded_write=_receipt("comment"))
            await c.transition_issue(
                "EX-1", transition_id="31", guarded_write=_receipt("display-status"))
            # A receipt does not unlock field content on a transition.
            with pytest.raises(pw.GuardRefused):
                await c.transition_issue(
                    "EX-1", transition_id="31", fields={"summary": "x"},
                    guarded_write=_receipt("display-status"))

    run(go())
    assert [r.path.rsplit("/", 1)[-1] for r in intake_fake.writes] == ["comment", "transitions"]


# --- AC36, AC38: the SSO-cookie client -------------------------------------------------------------

SSO = SsoConfig(
    profile="jira",
    base_url="https://jira.corp.example.com",
    login_url="https://sso.corp.example.com/login",
    success_url_pattern="https://jira.corp.example.com/secure/Dashboard.jspa",
    cookie_domains=("corp.example.com",),
    validation_endpoint="/rest/api/2/myself",
)


@pytest.fixture
def sso_fake(make_fake_jira: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    credbroker = pytest.importorskip("credbroker")
    jar = tmp_path / "jar.json"
    jar.write_text(json.dumps([
        {"name": "JSESSIONID", "domain": "jira.corp.example.com", "value": "s", "path": "/"},
    ]), encoding="utf-8")
    monkeypatch.setattr(credbroker, "load_sso_cookies", lambda profile: jar)
    return make_fake_jira(SSO.base_url, "server", {KEY: {"summary": "old summary"}})


def test_sso_cookie_client_sends_nothing_for_every_write_and_still_reads(sso_fake, tmp_path):
    attachment = tmp_path / "note.txt"
    attachment.write_text("x", encoding="utf-8")

    async def go() -> None:
        async with _client.JiraClient.from_sso_cookies(SSO) as c:
            attempts = [
                lambda: c.transition_issue(KEY, transition_name="Done"),   # lookup behind auth
                lambda: c.transition_issue(KEY, transition_id="31"),
                lambda: c.create_issue({"summary": "x"}),
                lambda: c.add_comment(KEY, "x"),
                lambda: c.add_attachment(KEY, attachment),
                lambda: c.delete_issue(KEY, confirm=True),
                lambda: c.update_issue(KEY, {"summary": "x"}),
                lambda: c.raw("POST", f"issue/{KEY}/comment", json_body={}),
                lambda: c.raw("PUT", f"issue/{KEY}", json_body={}),
                lambda: c.raw("PATCH", f"issue/{KEY}", json_body={}),
                lambda: c.raw("DELETE", f"issue/{KEY}"),
            ]
            for attempt in attempts:
                with pytest.raises(_client.JiraError, match="SSO-cookie") as info:
                    await attempt()
                # The auth refusal fires before the guard, so it is a JiraError, not a GuardRefused.
                assert not isinstance(info.value, pw.GuardRefused)
            with pytest.raises(_client.JiraError, match="SSO-cookie"):
                c.assert_writes_supported()
            assert (await c.raw("GET", f"issue/{KEY}?fields=summary"))["key"] == KEY
            assert (await c.get_issue(KEY, fields="summary"))["key"] == KEY

    run(go())
    assert [r.method for r in sso_fake.requests] == ["GET", "GET"]
    assert all("authorization" not in r.headers for r in sso_fake.requests)


# --- AC4: tracker error bodies are encoded -------------------------------------------------------


def test_tracker_error_bodies_are_visibly_encoded(fake, flavor):
    fake.override = lambda rec: (
        httpx.Response(400, text="bad\x1b[31m‮end") if rec.method == "POST" else None
    )
    with pytest.raises(_client.JiraError) as info:
        call(flavor, lambda c: c.add_comment(KEY, "x"))
    message = str(info.value)
    assert "\x1b" not in message and "‮" not in message
    assert "\\x1b" in message and "\\u202e" in message
