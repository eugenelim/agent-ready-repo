"""Contract tests for the shared preserve-first write module (spec ACs cited per test).

Home is redirected to a temp dir for every test; nothing touches the real
``~/.agentbundle``. T2 and T3 build the client and CLI behaviour on these names.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import _preserve_write as pw
import pytest

BASE = "https://jira.example.invalid"
KEY = "PROJ-12"
CLOUD_API = "/rest/api/3"
SERVER_API = "/rest/api/2"
ALIGN_API = "/rest/align/api/2"
POSIX_ONLY = pytest.mark.skipif(os.name != "posix", reason="POSIX modes and ownership")


@pytest.fixture(autouse=True)
def home(tracker_home: Path) -> Path:
    """Use the suite's shared isolated home for every module test."""
    return tracker_home


def doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "version": 1, "content": list(nodes)}


def para(text: str, marks: list[str] | None = None) -> dict[str, Any]:
    t: dict[str, Any] = {"type": "text", "text": text}
    if marks:
        t["marks"] = [{"type": m} for m in marks]
    return {"type": "paragraph", "content": [t]}


def make_plan(
    *,
    flavor: str = pw.FLAVOR_SERVER,
    target: str = KEY,
    method: str = "PUT",
    notify: bool = True,
    fields: dict[str, dict[str, Any]] | None = None,
    base: str = BASE,
) -> pw.Plan:
    fields = fields if fields is not None else {
        "summary": {"current": "old", "proposed": "new", "disposition": "replace"},
        "description": {"current": "d", "proposed": "e", "disposition": "keep"},
    }
    return pw.build_plan(
        target=target, flavor=flavor, base_url=base, method=method, notify=notify, fields=fields
    )


def approved(plan: pw.Plan) -> pw.VerifiedPlan:
    return pw.verify_plan(plan, plan.digest)


def guard(method: str, target: str, **kw: Any) -> None:
    kw.setdefault("client", "jira")
    kw.setdefault("api_prefix", CLOUD_API)
    pw.guard_request(method=method, target=target, base_url=BASE, **kw)


# --- constants ----------------------------------------------------------------


def test_guard_exit_code_is_10_and_guard_refused_is_exception() -> None:
    """Spec preamble: guard error is GuardRefused, exit code 10."""
    assert pw.GUARD_EXIT_CODE == 10
    assert issubclass(pw.GuardRefused, Exception)


# --- AC3 / AC6 / AC7: digest -----------------------------------------------------


def test_ac3_digest_is_stable_and_recomputed_from_contents() -> None:
    a, b = make_plan(), make_plan()
    assert a.digest == b.digest == a.recomputed_digest()
    assert len(a.digest) == 64


@pytest.mark.parametrize(
    "change",
    [
        {"target": "PROJ-13"},
        {"flavor": pw.FLAVOR_CLOUD},
        {"base": "https://other.example.invalid"},
        {"notify": False},
        {
            "fields": {
                "summary": {"current": "x", "proposed": "new", "disposition": "replace"},
            }
        },
        {
            "fields": {
                "summary": {"current": "old", "proposed": "y", "disposition": "replace"},
            }
        },
        {
            "fields": {
                "summary": {"current": "old", "proposed": "new", "disposition": "append"},
            }
        },
    ],
)
def test_ac3_digest_covers_each_input(change: dict[str, Any]) -> None:
    base_fields = {"summary": {"current": "old", "proposed": "new", "disposition": "replace"}}
    ref = make_plan(fields=base_fields)
    assert make_plan(**{"fields": base_fields, **change}).digest != ref.digest


def test_ac3_digest_covers_method_for_align() -> None:
    f = {"Title": {"current": "a", "proposed": "b", "disposition": "replace"}}
    put = make_plan(flavor=pw.FLAVOR_ALIGN, target="epics/5", method="PUT", fields=f)
    patch = make_plan(flavor=pw.FLAVOR_ALIGN, target="epics/5", method="PATCH", fields=f)
    assert put.digest != patch.digest


def test_ac6_wrong_approved_digest_refused() -> None:
    with pytest.raises(pw.GuardRefused):
        pw.verify_plan(make_plan(), "0" * 64)


def test_ac7_edited_plan_with_unchanged_stored_digest_refused(tmp_path: Path) -> None:
    plan = make_plan()
    path = pw.write_plan_file(plan)
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["fields"]["summary"]["proposed"] = "tampered"
    path.write_text(json.dumps(obj), encoding="utf-8")
    loaded = pw.load_plan(path, base_url=BASE)
    assert loaded.digest == plan.digest
    with pytest.raises(pw.GuardRefused):
        pw.verify_plan(loaded, plan.digest)


def test_ac6_verified_plan_cannot_be_forged_directly() -> None:
    with pytest.raises(pw.GuardRefused):
        pw.VerifiedPlan(make_plan(), object())


# --- AC8 / AC9 / AC10: binding and body ------------------------------------------------


def test_ac8_ac9_plan_authorizes_only_its_resolved_write() -> None:
    plan = make_plan()
    v = approved(plan)
    w = pw.resolved_write(plan)
    assert (w.method, w.url) == ("PUT", f"{BASE}{SERVER_API}/issue/{KEY}")
    guard("PUT", w.url, api_prefix=SERVER_API, body=w.body, verified_plan=v)
    guard("PUT", f"{SERVER_API}/issue/{KEY}", api_prefix=SERVER_API, body=w.body, verified_plan=v)


@pytest.mark.parametrize(
    ("method", "target", "body_change"),
    [
        ("POST", f"{SERVER_API}/issue/{KEY}", None),
        ("DELETE", f"{SERVER_API}/issue/{KEY}", None),
        ("PUT", f"{SERVER_API}/issue/PROJ-99", None),
        ("PUT", f"{SERVER_API}/issue/{KEY}/properties/x", None),
        ("PUT", f"{SERVER_API}/issue/{KEY}?notifyUsers=false", None),
        ("PUT", f"{SERVER_API}/issue/{KEY}", {"fields": {"summary": "other"}}),
        ("PUT", f"{SERVER_API}/issue/{KEY}", {"fields": {"summary": "new", "extra": 1}}),
    ],
)
def test_ac8_other_request_with_plan_refused(
    method: str, target: str, body_change: dict[str, Any] | None
) -> None:
    plan = make_plan()
    v = approved(plan)
    body = body_change if body_change is not None else pw.resolved_write(plan).body
    with pytest.raises(pw.GuardRefused):
        guard(method, target, api_prefix=SERVER_API, body=body, verified_plan=v)


def test_ac8_notify_false_url_binds_query() -> None:
    plan = make_plan(notify=False)
    w = pw.resolved_write(plan)
    assert w.url.endswith("?notifyUsers=false")
    guard(
        "PUT", f"{SERVER_API}/issue/{KEY}", api_prefix=SERVER_API, body=w.body,
        params={"notifyUsers": "false"}, verified_plan=approved(plan),
    )
    with pytest.raises(pw.GuardRefused):
        guard("PUT", f"{SERVER_API}/issue/{KEY}", api_prefix=SERVER_API, body=w.body,
              verified_plan=approved(plan))


def test_ac6_guarded_request_without_plan_sends_nothing() -> None:
    with pytest.raises(pw.GuardRefused):
        guard("PUT", f"{CLOUD_API}/issue/{KEY}", body={"fields": {}})


def test_ac10_body_holds_replace_and_append_only() -> None:
    plan = make_plan(
        fields={
            "summary": {"current": "a", "proposed": "b", "disposition": "replace"},
            "description": {"current": "x", "proposed": "y", "disposition": "append"},
            "labels": {"current": ["q"], "proposed": ["z"], "disposition": "keep"},
        }
    )
    body = pw.build_write_body(plan)
    assert set(body) == {"fields"}
    assert set(body["fields"]) == {"summary", "description"}
    assert body["fields"]["summary"] == "b"
    assert body["fields"]["description"].startswith("x")


def test_ac10_align_body_is_the_bare_field_map() -> None:
    plan = make_plan(
        flavor=pw.FLAVOR_ALIGN, target="epics/5", method="PATCH",
        fields={"Title": {"current": "a", "proposed": "b", "disposition": "replace"},
                "Notes": {"current": "a", "proposed": "b", "disposition": "keep"}},
    )
    assert pw.build_write_body(plan) == {"Title": "b"}
    assert pw.resolved_write(plan).url == f"{BASE}{ALIGN_API}/epics/5"
    assert pw.resolved_write(plan).method == "PATCH"


# --- AC11: stale check ---------------------------------------------------------------------


def test_ac11_unchanged_fields_pass_and_drift_refused() -> None:
    plan = make_plan()
    pw.check_unchanged(plan, {"summary": "old", "description": "d"})
    with pytest.raises(pw.GuardRefused, match="summary"):
        pw.check_unchanged(plan, {"summary": "edited", "description": "d"})
    with pytest.raises(pw.GuardRefused, match="description"):
        pw.check_unchanged(plan, {"summary": "old"})


def test_ac11_prepare_write_refuses_drift_and_returns_write_when_fresh() -> None:
    plan = make_plan()
    v = approved(plan)
    assert pw.prepare_write(v, {"summary": "old", "description": "d"}) == pw.resolved_write(plan)
    with pytest.raises(pw.GuardRefused):
        pw.prepare_write(v, {"summary": "new", "description": "d"})


def test_prepare_write_refuses_all_keep_plan() -> None:
    plan = make_plan(fields={"summary": {"current": "a", "proposed": "b", "disposition": "keep"}})
    with pytest.raises(pw.GuardRefused):
        pw.prepare_write(approved(plan), {"summary": "a"})


# --- AC23-AC25, AC29: append ------------------------------------------------------------------


def test_ac23_adf_append_keeps_existing_nodes_in_order() -> None:
    cur = doc(para("one"), {"type": "panel", "content": [para("two")]}, para("three"))
    new = pw.append_value(pw.FLAVOR_CLOUD, cur, doc(para("added")))
    assert new["content"][:3] == cur["content"]
    assert new["content"][3]["content"][0]["text"] == pw.APPEND_LABEL
    assert new["content"][4] == para("added")
    assert len(new["content"]) == 5
    assert cur["content"][2] == para("three")  # input not mutated


def test_ac23_adf_append_onto_empty_field_and_string_proposal_refused() -> None:
    new = pw.append_value(pw.FLAVOR_CLOUD, None, doc(para("plain")))
    assert new["type"] == "doc"
    assert new["content"][-1] == para("plain")
    with pytest.raises(pw.GuardRefused):  # Cloud proposals are ADF documents
        pw.append_value(pw.FLAVOR_CLOUD, doc(para("a")), "plain")


def test_ac24_server_append_original_is_byte_exact_prefix() -> None:
    cur = "line one\r\n  tail é \n"
    out = pw.append_value(pw.FLAVOR_SERVER, cur, "more")
    assert out.encode().startswith(cur.encode())
    assert pw.APPEND_LABEL in out
    assert out.endswith("more")


def test_ac25_align_append_original_is_byte_exact_prefix() -> None:
    cur = "  keep\tme\n"
    out = pw.append_value(pw.FLAVOR_ALIGN, cur, "more")
    assert out.encode().startswith(cur.encode())


def test_append_to_empty_string_has_no_leading_blank_line() -> None:
    assert pw.append_value(pw.FLAVOR_SERVER, "", "x") == f"{pw.APPEND_LABEL}\nx"


@pytest.mark.parametrize(
    ("flavor", "current", "proposed"),
    [
        (pw.FLAVOR_CLOUD, ["a"], ["b"]),
        (pw.FLAVOR_CLOUD, {"name": "High"}, {"name": "Low"}),
        (pw.FLAVOR_SERVER, ["a"], ["b"]),
        (pw.FLAVOR_SERVER, 3, 4),
        (pw.FLAVOR_ALIGN, {"a": 1}, {"a": 2}),
    ],
)
def test_ac29_append_on_non_text_field_refused(flavor: str, current: Any, proposed: Any) -> None:
    with pytest.raises(pw.GuardRefused):
        pw.append_value(flavor, current, proposed)
    target = "epics/5" if flavor == pw.FLAVOR_ALIGN else KEY
    with pytest.raises(pw.GuardRefused):
        make_plan(
            flavor=flavor, target=target,
            fields={"f": {"current": current, "proposed": proposed, "disposition": "append"}},
        )


# --- AC26-AC28: lossy ------------------------------------------------------------------------


def test_ac27_dropping_only_exempt_types_is_not_blocking() -> None:
    cur = doc(
        {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "h"}]},
        {"type": "bulletList", "content": [{"type": "listItem", "content": [para("a")]}]},
        {"type": "codeBlock", "content": [{"type": "text", "text": "x"}]},
        {"type": "paragraph", "content": [{"type": "hardBreak"}]},
    )
    report = pw.lossy_report(cur, doc(para("plain")))
    assert {"heading", "bulletList", "listItem", "codeBlock", "hardBreak"} <= set(report.node_types)
    assert not report.blocking


@pytest.mark.parametrize("node_type", ["panel", "table", "mention", "media", "rule", "orderedList2"])
def test_ac26_dropping_non_exempt_node_type_blocks(node_type: str) -> None:
    cur = doc(para("a"), {"type": node_type})
    report = pw.lossy_report(cur, doc(para("a")))
    assert report.blocking
    assert node_type in report.node_types
    assert node_type in report.blocking_nodes


def test_ac26_dropping_any_mark_type_blocks() -> None:
    cur = doc(para("a", ["strong"]))
    report = pw.lossy_report(cur, doc(para("a")))
    assert report.mark_types == ("strong",)
    assert report.blocking


def test_ac26_keeping_the_type_in_proposed_is_not_a_drop() -> None:
    cur = doc(para("a", ["strong"]), {"type": "panel"})
    assert not pw.lossy_report(cur, doc(para("b", ["strong"]), {"type": "panel"})).blocking


def test_ac26_prepare_write_refuses_lossy_replace_without_flag() -> None:
    cur = doc(para("a", ["em"]), {"type": "panel"})
    plan = make_plan(
        flavor=pw.FLAVOR_CLOUD,
        fields={"description": {"current": cur, "proposed": doc(para("b")),
                                "disposition": "replace"}},
    )
    v = approved(plan)
    with pytest.raises(pw.GuardRefused, match="panel"):
        pw.prepare_write(v, {"description": cur})
    assert pw.prepare_write(v, {"description": cur}, allow_lossy=True).body["fields"]


def test_ac27_prepare_write_proceeds_when_only_exempt_types_dropped() -> None:
    cur = doc({"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "h"}]})
    plan = make_plan(
        flavor=pw.FLAVOR_CLOUD,
        fields={"description": {"current": cur, "proposed": doc(para("b")),
                                "disposition": "replace"}},
    )
    pw.prepare_write(approved(plan), {"description": cur})


def test_ac28_preview_names_every_dropped_node_and_mark_type() -> None:
    cur = doc(para("a", ["strong"]), {"type": "panel"}, {"type": "heading", "content": []})
    plan = make_plan(
        flavor=pw.FLAVOR_CLOUD,
        fields={"description": {"current": cur, "proposed": doc(para("b")),
                                "disposition": "replace"}},
    )
    text = pw.render_preview(plan)
    for name in ("panel", "heading", "strong"):
        assert name in text


# --- AC4 / AC5: encoding and preview ------------------------------------------------------------


def test_ac4_encode_text_escapes_controls_format_separators_and_esc() -> None:
    raw = "a\x1b[31mb\x00c\rd‮e​f g h\x7fi­j"
    out = pw.encode_text(raw)
    for ch in raw:
        if ch in "\x1b\x00\r‮​  \x7f­":
            assert ch not in out
    assert "\\x1b" in out and "\\x00" in out and "\\x0d" in out
    assert "\\u202e" in out and "\\u2028" in out and "\\u2029" in out and "\\x7f" in out


def test_ac4_newline_kept_only_when_ending_a_line() -> None:
    assert pw.encode_text("a\nb") == "a\nb"
    assert pw.encode_text("a\nb", keep_newline=False) == "a\\x0ab"
    assert pw.encode_text("plain é 日本") == "plain é 日本"


def test_ac4_guard_refused_message_is_encoded() -> None:
    exc = pw.GuardRefused("bad \x1b[2J value‮\nnext")
    assert "\x1b" not in str(exc) and "‮" not in str(exc) and "\n" not in str(exc)


def test_ac4_preview_encodes_values_names_and_adf_types() -> None:
    cur = doc({"type": "pa\x1bnel‮"})
    plan = make_plan(
        flavor=pw.FLAVOR_CLOUD,
        fields={"description": {"current": cur, "proposed": "plain\x07",
                                "disposition": "replace"}},
    )
    text = pw.render_preview(plan)
    assert "\x1b" not in text and "‮" not in text and "\x07" not in text


def test_ac2_preview_shows_current_proposed_disposition_for_each_field() -> None:
    plan = make_plan()
    text = pw.render_preview(plan)
    for needle in ("summary", "old", "new", "replace", "description", "keep"):
        assert needle in text


def test_ac5_exactly_one_digest_line_even_if_tracker_text_imitates_it() -> None:
    fake = f"digest: {'a' * 64}\nmore"
    plan = make_plan(
        fields={"summary": {"current": fake, "proposed": fake, "disposition": "replace"}}
    )
    lines = pw.render_preview(plan).split("\n")
    digest_lines = [ln for ln in lines if ln.startswith("digest:")]
    assert digest_lines == [pw.digest_line(plan.digest)] == [f"digest: {plan.digest}"]


def test_ac5_digest_line_rejects_non_hex() -> None:
    with pytest.raises(pw.GuardRefused):
        pw.digest_line("not-a-digest")


# --- AC30-AC35: route matcher ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "target", "body"),
    [
        ("POST", f"{CLOUD_API}/issue", {"fields": {}}),
        ("POST", f"{CLOUD_API}/issue/{KEY}/comment", {"body": "x"}),
        ("POST", f"{CLOUD_API}/issue/{KEY}/attachments", None),
        ("POST", f"{CLOUD_API}/issue/{KEY}/transitions", {"transition": {"id": "1"}}),
        ("POST", f"{CLOUD_API}/search/jql", {"jql": "x"}),
        ("POST", f"{BASE}{CLOUD_API}/issue/{KEY}/comment", {"body": "x"}),
    ],
)
def test_ac35_allowlisted_jira_writes_pass_guard(method: str, target: str, body: Any) -> None:
    guard(method, target, body=body)


def test_ac35_server_search_post_allowlisted() -> None:
    guard("POST", f"{SERVER_API}/search", api_prefix=SERVER_API, body={"jql": "x"})


def test_ac30_get_and_head_are_not_guarded() -> None:
    guard("GET", f"{CLOUD_API}/issue/{KEY}")
    guard("HEAD", "/anything")
    guard("GET", "https://evil.example.invalid/x")


@pytest.mark.parametrize(
    "target",
    [
        f"{CLOUD_API}/issue/{KEY}",  # relative PUT target
        "/rest/api/latest/issue",
        "/rest/api/2/issue",  # wrong version for a cloud prefix
        "/rest/agile/1.0/issue/1/rank",
        "/rest/api/3/issue/bulk",
        f"{CLOUD_API}/issue/",
        f"{CLOUD_API}/issue/{KEY}/comment/",
        f"{CLOUD_API}//issue",
        f"{CLOUD_API}/issue/{KEY}/comment/10001",
        f"{CLOUD_API}/issue/{KEY}/properties/x",
        f"{CLOUD_API}/issue/lowercase-1/comment",
        f"{CLOUD_API}/issue/{KEY}/remotelink",
        "/rest/api/3",
        "/",
    ],
)
def test_ac30_unlisted_paths_need_a_plan(target: str) -> None:
    with pytest.raises(pw.GuardRefused):
        guard("POST", target, body={})
    with pytest.raises(pw.GuardRefused):
        guard("PUT", target, body={})


@pytest.mark.parametrize(
    "target",
    [
        f"{CLOUD_API}/issue/{KEY}/comment/../../issue",
        f"{CLOUD_API}/../api/3/issue",
        f"{CLOUD_API}/issue/%2e%2e/{KEY}",
        f"{CLOUD_API}/issue/%252e%252e/{KEY}",
        f"{CLOUD_API}/issue;x=1",
        f"{CLOUD_API}/issue/{KEY}/comment;jsessionid=1",
        f"{CLOUD_API}/issue%2f{KEY}",
        f"{CLOUD_API}/issue%2F{KEY}/comment",
        f"{CLOUD_API}%5cissue",
        f"{CLOUD_API}/issue%252f{KEY}",
        f"{CLOUD_API}\\issue",
        f"{CLOUD_API}/issue%00",
        f"{CLOUD_API}/%252525252e%252525252e/x",
    ],
)
def test_ac30_smuggling_forms_refused_even_with_a_plan(target: str) -> None:
    plan = make_plan(flavor=pw.FLAVOR_CLOUD, fields={
        "summary": {"current": "a", "proposed": "b", "disposition": "replace"}})
    with pytest.raises(pw.GuardRefused):
        guard("POST", target, body={"fields": {}})
    with pytest.raises(pw.GuardRefused):
        guard("PUT", target, body=pw.resolved_write(plan).body, verified_plan=approved(plan))


def test_ac30_percent_encoded_form_of_allowlisted_route_resolves_and_matches() -> None:
    guard("POST", f"{CLOUD_API}/iss%75e/{KEY}/comment", body={"body": "x"})


@pytest.mark.parametrize(
    "target",
    [
        "https://other.example.invalid/rest/api/3/issue",
        "http://jira.example.invalid/rest/api/3/issue",
        "https://jira.example.invalid:8443/rest/api/3/issue",
        "//other.example.invalid/rest/api/3/issue",
        "https://user@jira.example.invalid/rest/api/3/issue",
        "https://jira.example.invalid.evil.invalid/rest/api/3/issue",
    ],
)
def test_ac33_foreign_origin_refused(target: str) -> None:
    with pytest.raises(pw.GuardRefused):
        guard("POST", target, body={"fields": {}})


def test_ac33_default_port_and_case_equal_the_base_origin() -> None:
    guard("POST", "https://JIRA.example.invalid:443/rest/api/3/issue", body={})


@pytest.mark.parametrize(
    "header", ["X-HTTP-Method-Override", "x-http-method", "X-Method-Override"]
)
def test_ac33_method_override_headers_refused(header: str) -> None:
    with pytest.raises(pw.GuardRefused):
        guard("POST", f"{CLOUD_API}/issue", body={}, headers={header: "DELETE"})


def test_ac33_foreign_origin_refused_even_for_verified_plan_write() -> None:
    plan = make_plan()
    w = pw.resolved_write(plan)
    evil = w.url.replace("jira.example.invalid", "other.example.invalid")
    with pytest.raises(pw.GuardRefused):
        guard("PUT", evil, api_prefix=SERVER_API, body=w.body, verified_plan=approved(plan))


def test_ac33_context_path_base_url() -> None:
    base = "https://host.example.invalid/jira"
    pw.guard_request(client="jira", method="POST", base_url=base, api_prefix=SERVER_API,
                     target=f"{base}{SERVER_API}/issue", body={})
    pw.guard_request(client="jira", method="POST", base_url=base, api_prefix=SERVER_API,
                     target=f"{SERVER_API}/issue", body={})
    with pytest.raises(pw.GuardRefused):
        pw.guard_request(client="jira", method="POST", base_url=base, api_prefix=SERVER_API,
                         target=f"https://host.example.invalid{SERVER_API}/issue", body={})


def test_ac34_only_reads_follow_redirects() -> None:
    assert pw.may_follow_redirect("GET") and pw.may_follow_redirect("head")
    for m in ("POST", "PUT", "PATCH", "DELETE"):
        assert not pw.may_follow_redirect(m)


@pytest.mark.parametrize("extra", [{"fields": {"summary": "x"}}, {"update": {"labels": []}}])
def test_ac32_transition_with_field_content_always_refused(extra: dict[str, Any]) -> None:
    body = {"transition": {"id": "1"}, **extra}
    path = f"{CLOUD_API}/issue/{KEY}/transitions"
    with pytest.raises(pw.GuardRefused):
        guard("POST", path, body=body)
    with pytest.raises(pw.GuardRefused):
        pw.assert_transition_body_allowed(body)
    plan = make_plan(flavor=pw.FLAVOR_CLOUD, fields={
        "summary": {"current": "a", "proposed": "b", "disposition": "replace"}})
    with pytest.raises(pw.GuardRefused):
        guard("POST", path, body=body, verified_plan=approved(plan))


def test_ac32_clean_transition_body_allowed_and_non_mapping_body_guarded() -> None:
    pw.assert_transition_body_allowed({"transition": {"id": "1"}})
    with pytest.raises(pw.GuardRefused):
        guard("POST", f"{CLOUD_API}/issue/{KEY}/transitions", body=None)


def test_ac31_delete_needs_confirmed_delete_flag() -> None:
    path = f"{CLOUD_API}/issue/{KEY}"
    with pytest.raises(pw.GuardRefused):
        guard("DELETE", path)
    guard("DELETE", path, confirmed_delete=True)
    with pytest.raises(pw.GuardRefused):
        guard("DELETE", f"{CLOUD_API}/issue/{KEY}/comment/1", confirmed_delete=True)
    with pytest.raises(pw.GuardRefused):
        guard("DELETE", f"{CLOUD_API}/issue", confirmed_delete=True)


def test_ac31_confirmed_delete_flag_does_not_allow_other_methods() -> None:
    with pytest.raises(pw.GuardRefused):
        guard("PUT", f"{CLOUD_API}/issue/{KEY}", confirmed_delete=True, body={})


def test_align_allowlist_is_create_on_a_single_segment_and_confirmed_delete() -> None:
    def align(method: str, target: str, **kw: Any) -> None:
        pw.guard_request(client="jira-align", method=method, target=target, base_url=BASE,
                         api_prefix=ALIGN_API, **kw)

    align("POST", f"{ALIGN_API}/epics", body={"Title": "x"})
    align("POST", f"{BASE}{ALIGN_API}/Features", body={})
    for bad in (f"{ALIGN_API}/epics/5", f"{ALIGN_API}/epics/5/comments", f"{ALIGN_API}",
                f"{ALIGN_API}/epics/", f"{ALIGN_API}/1bad", "/rest/align/api/3/epics",
                f"{ALIGN_API}/epics/%2e%2e/x"):
        with pytest.raises(pw.GuardRefused):
            align("POST", bad, body={})
    for method in ("PUT", "PATCH"):
        with pytest.raises(pw.GuardRefused):
            align(method, f"{ALIGN_API}/epics/5", body={})
    with pytest.raises(pw.GuardRefused):
        align("DELETE", f"{ALIGN_API}/epics/5")
    align("DELETE", f"{ALIGN_API}/epics/5", confirmed_delete=True)
    with pytest.raises(pw.GuardRefused):
        align("DELETE", f"{ALIGN_API}/epics/05", confirmed_delete=True)


def test_ac8_align_plan_authorizes_only_its_method() -> None:
    f = {"Title": {"current": "a", "proposed": "b", "disposition": "replace"}}
    plan = make_plan(flavor=pw.FLAVOR_ALIGN, target="epics/5", method="PATCH", fields=f)
    v = approved(plan)
    w = pw.resolved_write(plan)

    def align(method: str, **kw: Any) -> None:
        pw.guard_request(client="jira-align", method=method, target=w.url, base_url=BASE,
                         api_prefix=ALIGN_API, body=w.body, verified_plan=v, **kw)

    align("PATCH")
    with pytest.raises(pw.GuardRefused):
        align("PUT")


def test_classify_route_reports_allowed_and_guarded() -> None:
    kw = {"client": "jira", "base_url": BASE, "api_prefix": CLOUD_API}
    assert pw.classify_route(method="POST", target=f"{CLOUD_API}/issue", **kw) == pw.ROUTE_ALLOWED
    assert pw.classify_route(method="PUT", target=f"{CLOUD_API}/issue/{KEY}", **kw) == pw.ROUTE_GUARDED


# --- AC15, AC16: root and slug -------------------------------------------------------------------------


def test_ac15_state_root_follows_home(home: Path) -> None:
    assert pw.state_root() == home / ".agentbundle" / "tracker-write-back"


def test_ac16_slug_is_host_plus_hash_in_closed_alphabet() -> None:
    slug = pw.instance_slug("https://Jira.Example.invalid/")
    assert slug.startswith("jira.example.invalid-")
    assert set(slug) <= set("abcdefghijklmnopqrstuvwxyz0123456789.-")
    assert slug == pw.instance_slug("https://jira.example.invalid:443")


def test_ac16_slug_hash_covers_scheme_host_port_and_path() -> None:
    slugs = {
        pw.instance_slug(u)
        for u in (
            "https://jira.example.invalid",
            "http://jira.example.invalid",
            "https://jira.example.invalid:8443",
            "https://jira.example.invalid/jira",
            "https://jira.example.invalid/other",
        )
    }
    assert len(slugs) == 5


@pytest.mark.parametrize(
    "url", ["https://[::1]:8443/x", "https://x_y.example.invalid", "https://...", "https://a..b/"]
)
def test_ac16_slug_never_empty_dots_only_or_outside_alphabet(url: str) -> None:
    try:
        slug = pw.instance_slug(url)
    except pw.GuardRefused:
        return
    assert slug and set(slug) != {"."} and set(slug) <= set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
    )


@pytest.mark.parametrize("url", ["", "ftp://x.example.invalid", "https://", "not a url",
                                 "https://u:p@x.example.invalid", "https://x.example.invalid?q=1"])
def test_ac16_bad_base_url_refused(url: str) -> None:
    with pytest.raises(pw.GuardRefused):
        pw.instance_slug(url)


# --- AC17-AC19: file handling ----------------------------------------------------------------------------


@POSIX_ONLY
def test_ac15_ac17_plan_file_location_mode_and_exclusive_create(home: Path) -> None:
    plan = make_plan()
    path = pw.write_plan_file(plan)
    root = pw.state_root().resolve()
    assert root in path.resolve().parents
    assert path.parent == pw.state_root() / pw.instance_slug(BASE) / "plans"
    assert path.name == f"{KEY}-{plan.digest[:12]}.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert json.loads(path.read_text(encoding="utf-8"))["digest"] == plan.digest


@POSIX_ONLY
def test_ac17_plan_name_clash_gets_unique_suffix_and_leaves_original(home: Path) -> None:
    plan = make_plan()
    first = pw.write_plan_file(plan)
    original = first.read_bytes()
    second = pw.write_plan_file(plan)
    third = pw.write_plan_file(plan)
    assert {first.name, second.name, third.name} == {
        f"{KEY}-{plan.digest[:12]}.json",
        f"{KEY}-{plan.digest[:12]}-1.json",
        f"{KEY}-{plan.digest[:12]}-2.json",
    }
    assert first.read_bytes() == original
    for p in (second, third):
        assert stat.S_IMODE(p.stat().st_mode) == 0o600


@POSIX_ONLY
def test_ac17_never_writes_through_a_preplaced_symlink_file(home: Path, tmp_path: Path) -> None:
    plan = make_plan()
    first = pw.write_plan_file(plan)
    victim = tmp_path / "victim.txt"
    victim.write_text("keep", encoding="utf-8")
    first.unlink()
    first.symlink_to(victim)
    second = pw.write_plan_file(plan)
    assert victim.read_text(encoding="utf-8") == "keep"
    assert second != first and not second.is_symlink()


@POSIX_ONLY
def test_ac17_mode_is_0600_even_under_a_loose_umask(home: Path) -> None:
    old = os.umask(0)
    try:
        path = pw.write_plan_file(make_plan())
    finally:
        os.umask(old)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@POSIX_ONLY
def test_ac18_created_folders_are_0700(home: Path) -> None:
    old = os.umask(0)
    try:
        path = pw.write_plan_file(make_plan())
    finally:
        os.umask(old)
    folder = path.parent
    while folder != home / ".agentbundle":
        assert stat.S_IMODE(folder.stat().st_mode) == 0o700
        folder = folder.parent


@POSIX_ONLY
@pytest.mark.parametrize("mode", [0o750, 0o705, 0o755, 0o770])
def test_ac18_existing_folder_with_group_or_other_access_refused(home: Path, mode: int) -> None:
    pw.write_plan_file(make_plan())
    victim = pw.state_root() / pw.instance_slug(BASE) / "plans"
    victim.chmod(mode)
    try:
        before = sorted(p.name for p in victim.iterdir())
        with pytest.raises(pw.GuardRefused):
            pw.write_plan_file(make_plan(notify=False))
        assert sorted(p.name for p in victim.iterdir()) == before
    finally:
        victim.chmod(0o700)


@POSIX_ONLY
def test_ac18_loose_root_or_instance_folder_refused(home: Path) -> None:
    pw.write_plan_file(make_plan())
    for victim in (pw.state_root(), pw.state_root() / pw.instance_slug(BASE)):
        victim.chmod(0o755)
        try:
            with pytest.raises(pw.GuardRefused):
                pw.write_plan_file(make_plan(notify=False))
        finally:
            victim.chmod(0o700)


@POSIX_ONLY
def test_ac18_folder_owned_by_another_user_refused(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pw.write_plan_file(make_plan())
    monkeypatch.setattr(os, "getuid", lambda: home.stat().st_uid + 1)
    with pytest.raises(pw.GuardRefused):
        pw.write_plan_file(make_plan(notify=False))


@POSIX_ONLY
def test_ac18_preexisting_loose_agentbundle_dir_is_tolerated(home: Path) -> None:
    (home / ".agentbundle").mkdir(mode=0o755)
    (home / ".agentbundle").chmod(0o755)
    path = pw.write_plan_file(make_plan())
    assert path.exists()


@POSIX_ONLY
@pytest.mark.parametrize("depth", ["agentbundle", "root", "instance", "plans"])
def test_ac19_symlink_at_any_folder_refused(home: Path, tmp_path: Path, depth: str) -> None:
    pw.write_plan_file(make_plan())
    paths = {
        "agentbundle": home / ".agentbundle",
        "root": pw.state_root(),
        "instance": pw.state_root() / pw.instance_slug(BASE),
        "plans": pw.state_root() / pw.instance_slug(BASE) / "plans",
    }
    target = paths[depth]
    elsewhere = tmp_path / "elsewhere"
    target.rename(elsewhere)
    target.symlink_to(elsewhere, target_is_directory=True)
    before = sorted(str(p) for p in elsewhere.rglob("*"))
    with pytest.raises(pw.GuardRefused):
        pw.write_plan_file(make_plan(notify=False))
    if depth != "plans":  # the prior folder does not sit under plans/
        with pytest.raises(pw.GuardRefused):
            pw.write_prior_then_call(BASE, prior(), lambda: pytest.fail("write must not run"))
    assert sorted(str(p) for p in elsewhere.rglob("*")) == before


def test_ac19_reparse_point_attribute_counts_as_a_link(monkeypatch: pytest.MonkeyPatch) -> None:
    class St:
        st_mode = stat.S_IFDIR | 0o700
        st_file_attributes = 0x400

    monkeypatch.setattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400, raising=False)
    assert pw._is_link(St())  # type: ignore[arg-type]


# --- AC12-AC14, AC21, AC22: prior record -------------------------------------------------------------------------


def prior(**kw: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "identifier": KEY,
        "plan_digest": "a" * 64,
        "entries": [("summary", "old", "new")],
    }
    args.update(kw)
    return pw.build_prior_record(**args)


def test_ac14_record_holds_field_old_written_identifier_and_digest() -> None:
    rec = prior(entries=[("summary", "old", "new"), ("labels", ["a"], ["b"])])
    assert rec == {
        "identifier": KEY,
        "plan_digest": "a" * 64,
        "entries": [
            {"field": "summary", "old": "old", "written": "new"},
            {"field": "labels", "old": ["a"], "written": ["b"]},
        ],
    }


def test_ac41_align_record_holds_full_record() -> None:
    rec = prior(identifier="epics/5", record={"id": 5, "Title": "a", "Other": "x"})
    assert rec["record"] == {"id": 5, "Title": "a", "Other": "x"}


def test_ac12_ac22_record_exists_before_write_and_path_is_announced_first(home: Path) -> None:
    events: list[str] = []
    seen: dict[str, Any] = {}

    def write() -> str:
        recs = list((pw.state_root() / pw.instance_slug(BASE) / "prior").iterdir())
        seen["count"] = len(recs)
        seen["body"] = json.loads(recs[0].read_text(encoding="utf-8"))
        events.append("write")
        return "sent"

    path, result = pw.write_prior_then_call(
        BASE, prior(), write, announce=lambda p: events.append(f"announce:{p.name}")
    )
    assert result == "sent"
    assert events == [f"announce:{path.name}", "write"]
    assert seen["count"] == 1 and seen["body"]["identifier"] == KEY
    assert path.name.endswith(f"-{KEY}.json")
    assert pw.state_root() in path.parents


@POSIX_ONLY
def test_ac17_record_mode_0600_and_each_record_is_its_own_file(home: Path) -> None:
    a, _ = pw.write_prior_then_call(BASE, prior(), lambda: None)
    b, _ = pw.write_prior_then_call(BASE, prior(), lambda: None)
    assert a != b
    assert stat.S_IMODE(a.stat().st_mode) == 0o600 == stat.S_IMODE(b.stat().st_mode)


@POSIX_ONLY
def test_ac13_failing_record_write_prevents_the_write_callback(home: Path) -> None:
    pw.write_prior_then_call(BASE, prior(), lambda: None)
    folder = pw.state_root() / pw.instance_slug(BASE) / "prior"
    folder.chmod(0o500)
    called: list[str] = []
    try:
        with pytest.raises(pw.GuardRefused):
            pw.write_prior_then_call(
                BASE, prior(), lambda: called.append("sent"), announce=called.append
            )
    finally:
        folder.chmod(0o700)
    assert called == []


def test_ac13_unwritable_home_prevents_the_write_callback(
    home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (home / ".agentbundle").write_text("a file, not a folder", encoding="utf-8")
    called: list[str] = []
    with pytest.raises(pw.GuardRefused):
        pw.write_prior_then_call(BASE, prior(), lambda: called.append("sent"))
    assert called == []


def test_write_failure_after_record_leaves_record_and_propagates(home: Path) -> None:
    def boom() -> None:
        raise RuntimeError("remote failed")

    with pytest.raises(RuntimeError):
        pw.write_prior_then_call(BASE, prior(), boom)
    assert len(list((pw.state_root() / pw.instance_slug(BASE) / "prior").iterdir())) == 1


def test_ac15_nothing_written_outside_the_redirected_home(home: Path, tmp_path: Path) -> None:
    pw.write_plan_file(make_plan())
    pw.write_prior_then_call(BASE, prior(), lambda: None)
    created = set(tmp_path.rglob("*"))
    assert all(home in p.parents or p == home for p in created if p != home)


# --- AC20: loaders ----------------------------------------------------------------------------------------------


def stored_plan(**kw: Any) -> tuple[pw.Plan, Path, dict[str, Any]]:
    plan = make_plan(**kw)
    path = pw.write_plan_file(plan)
    return plan, path, json.loads(path.read_text(encoding="utf-8"))


def rewrite(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_ac20_plan_round_trips_through_file_and_loader() -> None:
    plan, path, _ = stored_plan()
    loaded = pw.load_plan(path, base_url=BASE)
    assert loaded == plan
    assert pw.verify_plan(loaded, plan.digest).plan == loaded


def test_ac20_base_url_compared_after_normalisation() -> None:
    _, path, _ = stored_plan()
    assert pw.load_plan(path, base_url="https://JIRA.example.invalid:443/").digest


@pytest.mark.parametrize(
    "mutate",
    [
        lambda o: o.update(extra=1),
        lambda o: o.update(path="/rest/api/2/issue/X-1"),
        lambda o: o.update(headers={"X": "y"}),
        lambda o: o.pop("digest"),
        lambda o: o.update(contract_version=2),
        lambda o: o.update(contract_version=True),
        lambda o: o.update(contract_version="1"),
        lambda o: o.update(target="proj-12"),
        lambda o: o.update(target="PROJ-012"),
        lambda o: o.update(target="PROJ-12/../x"),
        lambda o: o.update(target="A" * 11 + "-1"),
        lambda o: o.update(target=5),
        lambda o: o.update(flavor="onprem"),
        lambda o: o.update(flavor=None),
        lambda o: o.update(base_url="https://other.example.invalid"),
        lambda o: o.update(base_url=7),
        lambda o: o.update(method="PATCH"),  # server flavor: only PUT
        lambda o: o.update(method="DELETE"),
        lambda o: o.update(method=["PUT"]),
        lambda o: o.update(notify="true"),
        lambda o: o.update(notify=1),
        lambda o: o.update(digest="XYZ"),
        lambda o: o.update(digest="A" * 64),
        lambda o: o.update(fields=[]),
        lambda o: o.update(fields={}),
        lambda o: o["fields"]["summary"].update(extra=1),
        lambda o: o["fields"]["summary"].pop("proposed"),
        lambda o: o["fields"]["summary"].update(disposition="delete"),
        lambda o: o["fields"]["summary"].update(disposition=1),
        lambda o: o["fields"].update({"": {"current": 1, "proposed": 2, "disposition": "keep"}}),
        lambda o: o["fields"].update({"a\x1bb": {"current": 1, "proposed": 2,
                                                 "disposition": "keep"}}),
        lambda o: o["fields"].update(summary="text"),
        lambda o: o["fields"]["summary"].update(current=[1], proposed=[2], disposition="append"),
    ],
)
def test_ac20_malformed_plan_refused(mutate: Any) -> None:
    _, path, obj = stored_plan()
    mutate(obj)
    rewrite(path, obj)
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(path, base_url=BASE)


def test_ac20_align_plan_alphabet_and_methods() -> None:
    f = {"Title": {"current": "a", "proposed": "b", "disposition": "replace"}}
    _, path, obj = stored_plan(flavor=pw.FLAVOR_ALIGN, target="epics/5", method="PATCH", fields=f)
    assert pw.load_plan(path, base_url=BASE).method == "PATCH"
    for target in ("PROJ-12", "epics/05", "epics/5/6", "1epics/5", "epics/", "e" * 65 + "/5"):
        bad = {**obj, "target": target}
        rewrite(path, bad)
        with pytest.raises(pw.GuardRefused):
            pw.load_plan(path, base_url=BASE)
    rewrite(path, {**obj, "method": "PUT"})
    assert pw.load_plan(path, base_url=BASE).method == "PUT"
    rewrite(path, {**obj, "method": "POST"})
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(path, base_url=BASE)


def test_ac20_plan_not_json_or_duplicate_key_or_nan_refused() -> None:
    _, path, obj = stored_plan()
    for text in (
        "not json",
        "",
        "[]",
        '{"contract_version":1,"contract_version":1}',
        json.dumps(obj).replace('"current": "old"', '"current": NaN'),
        "\xff",
    ):
        path.write_text(text, encoding="utf-8")
        with pytest.raises(pw.GuardRefused):
            pw.load_plan(path, base_url=BASE)


def test_ac20_plan_outside_root_refused(tmp_path: Path) -> None:
    plan, path, _ = stored_plan()
    outside = tmp_path / "plan.json"
    outside.write_bytes(path.read_bytes())
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(outside, base_url=BASE)
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(path.parent / ".." / ".." / ".." / ".." / "plan.json", base_url=BASE)
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(pw.state_root() / "missing.json", base_url=BASE)
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(path.parent, base_url=BASE)


@POSIX_ONLY
def test_ac20_plan_symlink_inside_root_pointing_outside_refused(home: Path, tmp_path: Path) -> None:
    plan, path, _ = stored_plan()
    outside = tmp_path / "plan.json"
    outside.write_bytes(path.read_bytes())
    link = path.parent / "link.json"
    link.symlink_to(outside)
    with pytest.raises(pw.GuardRefused):
        pw.load_plan(link, base_url=BASE)


def record_file(obj: dict[str, Any]) -> Path:
    path, _ = pw.write_prior_then_call(BASE, obj, lambda: None)
    return path


def test_ac20_record_round_trips_and_undo_plan_is_built_from_it() -> None:
    rec = prior(entries=[("summary", "old", "new"), ("description", "d0", "d1")])
    path = record_file(rec)
    loaded = pw.load_record(path)
    assert loaded == rec
    undo = pw.build_undo_plan(
        loaded, flavor=pw.FLAVOR_SERVER, base_url=BASE, method="PUT", notify=True
    )
    assert undo.target == KEY
    assert {n: (f.current, f.proposed, f.disposition) for n, f in undo.fields.items()} == {
        "summary": ("new", "old", "replace"),
        "description": ("d1", "d0", "replace"),
    }
    assert pw.build_write_body(undo) == {"fields": {"summary": "old", "description": "d0"}}


def test_ac43_ac44_undo_plan_is_stale_when_remote_is_not_the_written_value() -> None:
    undo = pw.build_undo_plan(
        prior(), flavor=pw.FLAVOR_SERVER, base_url=BASE, method="PUT", notify=True
    )
    v = approved(undo)
    assert pw.prepare_write(v, {"summary": "new"}).body == {"fields": {"summary": "old"}}
    with pytest.raises(pw.GuardRefused):
        pw.prepare_write(v, {"summary": "edited since"})


def test_ac20_align_record_requires_and_allows_full_record() -> None:
    rec = prior(identifier="epics/5", record={"id": 5})
    assert pw.load_record(record_file(rec))["record"] == {"id": 5}
    undo = pw.build_undo_plan(
        pw.load_record(record_file(rec)), flavor=pw.FLAVOR_ALIGN, base_url=BASE,
        method="PATCH", notify=True,
    )
    assert undo.target == "epics/5"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda o: o.update(extra=1),
        lambda o: o.update(record={"id": 1}),  # record on a Jira key
        lambda o: o.pop("entries"),
        lambda o: o.pop("plan_digest"),
        lambda o: o.update(identifier="proj-12"),
        lambda o: o.update(identifier="PROJ-0"),
        lambda o: o.update(identifier="../etc/passwd"),
        lambda o: o.update(identifier=12),
        lambda o: o.update(identifier="epics/0"),
        lambda o: o.update(plan_digest="abc"),
        lambda o: o.update(plan_digest=5),
        lambda o: o.update(entries={}),
        lambda o: o.update(entries=[]),
        lambda o: o.update(entries=["x"]),
        lambda o: o.update(entries=[{"field": "a", "old": 1}]),
        lambda o: o.update(entries=[{"field": "a", "old": 1, "written": 2, "x": 3}]),
        lambda o: o.update(entries=[{"field": 1, "old": 1, "written": 2}]),
        lambda o: o.update(entries=[{"field": "", "old": 1, "written": 2}]),
    ],
)
def test_ac20_malformed_record_refused(mutate: Any) -> None:
    path = record_file(prior())
    obj = json.loads(path.read_text(encoding="utf-8"))
    mutate(obj)
    rewrite(path, obj)
    with pytest.raises(pw.GuardRefused):
        pw.load_record(path)


def test_ac20_align_record_without_record_or_with_non_object_refused() -> None:
    path = record_file(prior(identifier="epics/5", record={"id": 5}))
    obj = json.loads(path.read_text(encoding="utf-8"))
    rewrite(path, {**obj, "record": [1]})
    with pytest.raises(pw.GuardRefused):
        pw.load_record(path)


def test_ac20_record_outside_root_refused(tmp_path: Path) -> None:
    path = record_file(prior())
    outside = tmp_path / "rec.json"
    outside.write_bytes(path.read_bytes())
    with pytest.raises(pw.GuardRefused):
        pw.load_record(outside)


def test_ac21_loader_errors_do_not_echo_file_values() -> None:
    path = record_file(prior(entries=[("summary", "SECRET-OLD-VALUE", "SECRET-NEW")]))
    obj = json.loads(path.read_text(encoding="utf-8"))
    obj["extra"] = "SECRET-EXTRA"
    rewrite(path, obj)
    with pytest.raises(pw.GuardRefused) as err:
        pw.load_record(path)
    assert "SECRET" not in str(err.value)


def test_api_prefix_for_each_flavor() -> None:
    assert pw.api_prefix_for(pw.FLAVOR_CLOUD) == CLOUD_API
    assert pw.api_prefix_for(pw.FLAVOR_SERVER) == SERVER_API
    assert pw.api_prefix_for(pw.FLAVOR_ALIGN) == ALIGN_API
    with pytest.raises(pw.GuardRefused):
        pw.api_prefix_for("x")


def test_build_plan_rejects_bad_inputs() -> None:
    f = {"a": {"current": 1, "proposed": 2, "disposition": "replace"}}
    for kw in (
        {"flavor": "x"},
        {"method": "PATCH"},
        {"target": "bad"},
        {"notify": "yes"},
        {"fields": {}},
        {"fields": {"a": {"current": 1, "proposed": 2, "disposition": "merge"}}},
    ):
        with pytest.raises(pw.GuardRefused):
            make_plan(**{"fields": f, **kw})


@pytest.mark.parametrize("part", ["current", "proposed"])
def test_the_digest_covers_keep_entries(part: str) -> None:
    def digest(value: str) -> str:
        keep = {"current": "c", "proposed": "p", "disposition": "keep"}
        keep[part] = value
        return make_plan(fields={
            "summary": {"current": "old", "proposed": "new", "disposition": "replace"},
            "description": keep,
        }).digest

    assert digest("one") != digest("two")


# --- T13: strict numeric loading ------------------------------------------------


@pytest.mark.parametrize("literal", ["1e400", "-1e400"])
@pytest.mark.parametrize("location", ["current", "proposed", "old", "written", "record"])
def test_t13_loaders_refuse_overflow_anywhere(
    tracker_home: Path, make_fake_jira: Any, literal: str, location: str,
) -> None:
    """Overflow in nested arrays or objects is refused without echoing its value."""
    make_fake_jira(BASE, "server", {KEY: {}})
    path = pw.write_plan_file(make_plan())
    if location in {"current", "proposed"}:
        obj = pw.plan_to_obj(make_plan())
        obj["fields"]["summary"][location] = {"nested": ["NUMBER_SENTINEL"]}
    else:
        obj = {
            "identifier": "epics/5", "plan_digest": "a" * 64,
            "entries": [{"field": "title", "old": "before", "written": "after"}],
            "record": {},
        }
        if location == "record":
            obj["record"] = {"nested": ["NUMBER_SENTINEL"]}
        else:
            obj["entries"][0][location] = {"nested": ["NUMBER_SENTINEL"]}
    path.write_text(json.dumps(obj).replace('"NUMBER_SENTINEL"', literal), encoding="utf-8")
    with pytest.raises(pw.GuardRefused, match="non-finite number") as exc:
        if location in {"current", "proposed"}:
            pw.load_plan(path, base_url=BASE)
        else:
            pw.load_record(path)
    assert literal not in str(exc.value)


def test_t13_finite_nested_numbers_still_load(tracker_home: Path, make_fake_jira: Any) -> None:
    """The numeric guard retains ordinary finite JSON numbers."""
    make_fake_jira(BASE, "server", {KEY: {}})
    plan = make_plan(fields={"number": {
        "current": {"nested": [1e300, -1e300, 0, 1.25]},
        "proposed": 3.5, "disposition": "replace",
    }})
    loaded = pw.load_plan(pw.write_plan_file(plan), base_url=BASE)
    assert loaded.recomputed_digest() == plan.digest


@pytest.mark.parametrize("surrogate", ["\ud800", "\udfff"])
def test_t14_encode_text_escapes_lone_surrogates(surrogate: str) -> None:
    """Surrogates use visible escapes while ordinary Unicode stays intact."""
    raw = "plain é 日本 😀\ue000\u0378" + surrogate
    for keep_newline in (True, False):
        shown = pw.encode_text(raw, keep_newline=keep_newline)
        assert shown == raw[:-1] + f"\\u{ord(surrogate):04x}"
        shown.encode("utf-8", errors="strict")
