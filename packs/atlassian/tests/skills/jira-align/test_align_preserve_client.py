"""Jira Align client enforces the preserve-first guard at its request chokepoint.

Driven against a recording fake transport (``conftest.FakeAlign``). Each test names the
spec criteria (ACn) it covers. Home is redirected to a temp dir for every test.
"""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import Any

import align_skill_scripts._client as _client
import align_skill_scripts._preserve_write as pw
import httpx
import pytest

BASE = "https://align.example.invalid"
TARGET = "epics/5"
API = "/rest/align/api/2"
SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira-align"
PROFILE = SKILL_ROOT.parent / "jira-align-brief-intake/references/intake-profile.json"
INTAKE_BASE = "https://portfolio-tracker.example.test"


@pytest.fixture(autouse=True)
def _home(tracker_home: Path) -> Path:
    return tracker_home


def run(coro: Any) -> Any:
    return asyncio.run(coro)


def records() -> dict[str, dict[str, Any]]:
    return {TARGET: {"id": 5, "title": "old title", "description": "old text", "points": 3}}


def credentials(base: str = BASE) -> _client.Credentials:
    return _client.Credentials(base_url=base, token="fixture", flavor="onprem")


@pytest.fixture
def fake(make_fake_align: Any) -> Any:
    return make_fake_align(BASE, records())


def verified(method: str = "PATCH") -> pw.VerifiedPlan:
    plan = pw.build_plan(
        target=TARGET, flavor="align", base_url=BASE, method=method, notify=True,
        fields={
            "title": {"current": "old title", "proposed": "new title", "disposition": "replace"},
            "points": {"current": 3, "proposed": 3, "disposition": "keep"},
        },
    )
    return pw.verify_plan(plan, plan.digest)


async def _with_client(fn: Any) -> Any:
    async with _client.JiraAlignClient(credentials()) as client:
        return await fn(client)


def call(fn: Any) -> Any:
    return run(_with_client(fn))


# --- AC6, AC30: deny by default --------------------------------------------------------------


def test_direct_update_without_a_plan_is_refused_with_zero_requests(fake):
    for method in ("PATCH", "PUT"):
        with pytest.raises(pw.GuardRefused):
            call(lambda c, m=method: c.update("epics", "5", {"title": "x"}, method=m))
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c.update("epics", "5", {"title": "x"}))
    assert fake.requests == []


def test_plan_with_changed_contents_cannot_be_verified_so_nothing_is_sent(fake):
    plan = pw.build_plan(
        target=TARGET, flavor="align", base_url=BASE, method="PATCH", notify=True,
        fields={"title": {"current": "a", "proposed": "b", "disposition": "replace"}},
    )
    edited = dataclasses.replace(plan, fields={"title": pw.FieldPlan("a", "EVIL", "replace")})
    with pytest.raises(pw.GuardRefused):
        pw.verify_plan(edited, plan.digest)
    assert fake.requests == []


@pytest.mark.parametrize("method", ["PUT", "PATCH", "POST", "DELETE"])
@pytest.mark.parametrize(
    "target",
    [
        f"{API}/epics/5",                                 # relative, the record path
        f"{BASE}{API}/epics/5",                           # absolute, same origin
        "/rest/align/api/1/epics/5",                      # other version prefix
        "/rest/align/api/2/epics/5/children",             # sub-resource
        f"{API}/epics/5/",                                # trailing slash
        f"{API}/epics%2F5",                               # percent-encoded separator
        f"{API}/epics/%2e%2e/features/5",                 # percent-encoded ..
        f"{API}/epics/../features/5",                     # ..
        f"{API}/epics;x=1/5",                             # ; matrix parameter
        f"{API}/epics/",                                  # create route with trailing slash
        f"{API}/",                                        # no resource
        "/rest/api/2/epics",                              # not the Align prefix
        f"{API}/ep ics",                                  # outside the resource alphabet
    ],
)
def test_every_non_allowlisted_route_form_is_refused_without_a_plan(fake, method, target):
    # AC30, AC31: whatever the prefix or path form, no plan means no request.
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c._request(method, target, json_body={"title": "x"}))
    assert fake.requests == []


def test_create_matches_a_single_path_segment_only(fake):
    for target in (f"{API}/epics/5", f"{API}/epics/5/children", f"{API}/epics/"):
        with pytest.raises(pw.GuardRefused):
            call(lambda c, t=target: c._request("POST", t, json_body={"title": "x"}))
    assert fake.requests == []
    call(lambda c: c.create("epics", {"title": "new"}))                       # AC35
    assert [(r.method, r.path) for r in fake.writes] == [("POST", f"{API}/epics")]
    assert fake.writes[0].body == {"title": "new"}


def test_a_guarded_route_stays_refused_when_reached_through_raw(fake):
    for method, path, body in (
        ("PUT", "epics/5", {"title": "x"}),
        ("PATCH", f"{API}/epics/5", {"title": "x"}),
        ("DELETE", "epics/5", None),
        ("POST", "epics/5", {"title": "x"}),
        ("POST", "epics/5/children", {"title": "x"}),
        ("PUT", "epics/5/", {"title": "x"}),
        ("PATCH", "epics/../features/5", {"title": "x"}),
        ("PATCH", "epics%2F5", {"title": "x"}),
        ("POST", "https://other.example.invalid/rest/align/api/2/epics", {"title": "x"}),
    ):
        with pytest.raises(pw.GuardRefused):
            call(lambda c, m=method, p=path, b=body: c.raw(m, p, json_body=b))
    assert fake.requests == []


# --- AC8, AC9, AC10: a verified plan authorizes exactly one request -------------------------------


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_verified_plan_sends_exactly_one_request_with_the_resolved_body_only(fake, method):
    v = verified(method)
    call(lambda c: c.update("epics", "5", v.write.body, method=v.write.method, verified_plan=v))
    assert len(fake.writes) == 1
    sent = fake.writes[0]
    assert (sent.method, sent.url) == (method, v.write.url)                  # AC9, AC40
    assert sent.body == v.write.body == {"title": "new title"}              # AC10: no keep field
    assert fake.records[TARGET]["title"] == "new title"


def test_the_plans_method_is_part_of_what_it_authorizes(fake):
    patch_plan, put_plan = verified("PATCH"), verified("PUT")
    with pytest.raises(pw.GuardRefused):                                      # AC40: no PUT from a PATCH plan
        call(lambda c: c.update(
            "epics", "5", patch_plan.write.body, method="PUT", verified_plan=patch_plan))
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c.update(
            "epics", "5", put_plan.write.body, method="PATCH", verified_plan=put_plan))
    assert patch_plan.plan.digest != put_plan.plan.digest                    # AC3: method is bound
    assert fake.requests == []


@pytest.mark.parametrize(
    "variant",
    ["other_id", "other_resource", "other_method", "other_body", "extra_key", "other_host",
     "extra_param"],
)
def test_a_verified_plan_does_not_authorize_any_other_request(fake, variant):
    v = verified()
    body = v.write.body
    method, path, params = "PATCH", f"{API}/epics/5", None
    if variant == "other_id":
        path = f"{API}/epics/6"
    elif variant == "other_resource":
        path = f"{API}/features/5"
    elif variant == "other_method":
        method = "PUT"
    elif variant == "other_body":
        body = {"title": "different"}
    elif variant == "extra_key":
        body = {**body, "state": "Done"}
    elif variant == "other_host":
        path = f"https://other.example.invalid{API}/epics/5"
    else:
        params = {"x": "1"}
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c._request(method, path, params=params, json_body=body, verified_plan=v))
    assert fake.requests == []


# --- AC31: deletes -------------------------------------------------------------------------------


def test_delete_goes_only_through_delete_with_confirm(fake):
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c.delete("epics", "5"))
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c.delete("epics", "5", confirm=False))
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c.raw("DELETE", "epics/5"))
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c._request("DELETE", f"{API}/epics/5"))
    # Confirmation cannot widen the route: only {resource}/{id} is deletable.
    for target in (f"{API}/epics", f"{API}/epics/5/children", f"{API}/epics/five"):
        with pytest.raises(pw.GuardRefused):
            call(lambda c, t=target: c._request("DELETE", t, confirmed_delete=True))
    assert fake.requests == []
    call(lambda c: c.delete("epics", "5", confirm=True))
    assert [(r.method, r.path) for r in fake.writes] == [("DELETE", f"{API}/epics/5")]


# --- AC33: origin and override headers ------------------------------------------------------------


@pytest.mark.parametrize(
    "target",
    [
        "https://other.example.invalid/rest/align/api/2/epics",        # other host
        "http://align.example.invalid/rest/align/api/2/epics",         # http downgrade
        "https://align.example.invalid:8443/rest/align/api/2/epics",   # port change
    ],
)
def test_other_origin_is_refused_even_on_an_allowlisted_route(fake, target):
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c._request("POST", target, json_body={"title": "x"}))
    assert fake.requests == []


@pytest.mark.parametrize(
    "header", ["X-HTTP-Method-Override", "x-http-method", "X-Method-Override"]
)
def test_method_override_header_is_refused_even_on_an_allowlisted_route(fake, header):
    with pytest.raises(pw.GuardRefused):
        call(lambda c: c._request(
            "POST", f"{API}/epics", json_body={"title": "x"}, extra_headers={header: "DELETE"}))
    assert fake.requests == []


# --- AC34: no redirect following for writes ---------------------------------------------------------


def test_a_redirected_write_is_not_followed(fake):
    fake.override = lambda rec: (
        httpx.Response(307, headers={"Location": "https://other.example.invalid/x"})
        if rec.method != "GET" else None
    )
    with pytest.raises(_client.JiraAlignError, match="redirect"):
        call(lambda c: c.create("epics", {"title": "x"}))
    v = verified()
    with pytest.raises(_client.JiraAlignError, match="redirect"):
        call(lambda c: c.update("epics", "5", v.write.body, method="PATCH", verified_plan=v))
    assert [r.method for r in fake.requests] == ["POST", "PATCH"]   # one each, nothing followed


def test_a_redirected_read_is_still_followed(fake):
    def hop(rec: Any) -> httpx.Response | None:
        if rec.path == f"{API}/epics/5" and "moved" not in rec.query:
            return httpx.Response(302, headers={"Location": f"{BASE}{API}/epics/5?moved=1"})
        return None

    fake.override = hop
    assert call(lambda c: c.get_one("epics", "5"))["id"] == 5
    assert len(fake.requests) == 2


# --- AC35: allowlisted writes are not refused by the guard -----------------------------------------


def test_raw_post_to_the_allowlisted_create_route_is_not_refused(fake):
    call(lambda c: c.raw("POST", "epics", json_body={"title": "x"}))
    assert len(fake.writes) == 1


# --- AC37: the intake-policy non-GET refusal still fires, and first ---------------------------------


def _intake_client() -> _client.JiraAlignClient:
    policy = _client.IntakeRequestPolicy.from_profile(
        PROFILE, INTAKE_BASE,
        resolver=lambda host, port, **_k: [(None, None, None, None, ("93.184.216.34", port))],
    )
    return _client.JiraAlignClient(credentials(INTAKE_BASE), intake_policy=policy)


def test_intake_policy_refuses_every_non_get_before_the_guard(
    make_fake_align: Any, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    intake_fake = make_fake_align(INTAKE_BASE, {TARGET: {"id": 5, "title": "t"}})
    v = verified()

    async def go() -> None:
        async with _intake_client() as c:
            for method, path in (
                ("PATCH", f"{API}/epics/5"),
                ("PUT", f"{API}/epics/5"),
                ("POST", f"{API}/epics"),                # allowlisted by the guard, refused here
                ("DELETE", f"{API}/epics/5"),
            ):
                with pytest.raises(_client.JiraAlignError, match="read-only") as info:
                    await c._request(method, path, json_body={})
                assert not isinstance(info.value, pw.GuardRefused)
            with pytest.raises(_client.JiraAlignError, match="read-only"):
                await c.update("epics", "5", v.write.body, method="PATCH", verified_plan=v)
            with pytest.raises(_client.JiraAlignError, match="read-only"):
                await c.delete("epics", "5", confirm=True)
            with pytest.raises(_client.JiraAlignError, match="read-only"):
                c.assert_writes_supported()

    run(go())
    assert intake_fake.requests == []


def test_a_client_without_an_intake_policy_supports_writes(fake):
    call(lambda c: _none(c.assert_writes_supported()))


async def _none(_: Any) -> None:
    return None


# --- AC4: tracker error bodies are encoded -------------------------------------------------------


def test_tracker_error_bodies_are_visibly_encoded(fake):
    fake.override = lambda rec: (
        httpx.Response(400, text="bad\x1b[31m\u202eend") if rec.method == "POST" else None
    )
    with pytest.raises(_client.JiraAlignError) as info:
        call(lambda c: c.create("epics", {"title": "x"}))
    message = str(info.value)
    assert "\x1b" not in message and "\u202e" not in message
    assert "\\x1b" in message and "\\u202e" in message
