"""Construction tests for the readiness bridge.

``intent_readiness.py`` reads untrusted bytes: the output of work-loop's argless
``dispatch.py --root``.  The first half drives its ``read``, ``check``, ``start`` and
``project`` with named byte streams and read descriptors.  The second half drives
``export --readiness -`` through ``run_export`` and child interpreters, and runs the
real ``dispatch.py`` over the replay suite's case trees.  The oracle for each case is the
reason or value the spec names; no expected reason is read from the module.
"""

from __future__ import annotations

import ast
import atexit
import collections
import contextlib
import copy
import datetime
import importlib.util
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from html.parser import HTMLParser
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_ENGINE = _PACK / ".apm" / "skills" / "workspace-status" / "scripts" / "workspace_status_engine.py"
_DISPATCH = _PACK / ".apm" / "skills" / "work-loop" / "scripts" / "dispatch.py"
_REPLAY = _PACK / "tests" / "skills" / "work-loop" / "test_header_derived_dispatch_replay.py"


def _load(path: pathlib.Path, module_name: str) -> Any:
    """Load a script by path under a pack-and-skill-unique module name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


rd = _load(_SCRIPTS / "intent_readiness.py", "core_navigate_intents_readiness_rd")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from navigate_intents_fixture_builders import HOSTILE_NEEDLES, outside_data_block  # noqa: E402

LIMIT = 4_194_304
READY = "docs/specs/bravo-spec/spec.md"
ACTIVE = "docs/specs/charlie-spec/spec.md"
BLOCKED = "docs/specs/golf-new/spec.md"
PATH_TO_ID = {
    READY: "spec:bravo-spec",
    ACTIVE: "spec:charlie-spec",
    BLOCKED: "spec:golf-new",
    "docs/product/intents/FEAT-0001-bravo-feat.md": "intent:bravo-feat",
}
OTHER = "docs/product/intents/FEAT-0001-bravo-feat.md"
DEP_ACTION = "Complete or explicitly revise the dependency."
_ABSENT = object()


def finding(
    code: str = "unsatisfied_dependency",
    action: str = DEP_ACTION,
    path: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """A finding with exactly the four members dispatch.py prints (plus any ``extra``)."""
    return {"code": code, "path": path, "dispatchable": False, "next_action": action, **extra}


def entry(path: str, findings: list | None = None, **extra: Any) -> dict[str, Any]:
    """An item with exactly the four members dispatch.py prints (plus any ``extra``)."""
    base = {"path": path, "slug": "a-slug", "status": "Approved", "findings": findings or []}
    return {**base, **extra}


def argless_decision(active: list[dict], ready: list[dict]) -> dict[str, Any]:
    """The decision dispatch.py derives with no selector, written from the spec's definition."""
    act, rdy = [i["path"] for i in active], [i["path"] for i in ready]
    if len(act) == 1:
        action, path, cands = "resume", act[0], []
    elif act:
        action, path, cands = "ask", None, act
    elif len(rdy) == 1:
        action, path, cands = "start", rdy[0], []
    elif rdy:
        action, path, cands = "ask", None, rdy
    else:
        action, path, cands = "none", None, []
    return {"action": action, "path": path, "candidates": cands, "findings": []}


def decision_of(action: str, path: str | None = None, candidates=None, findings=None) -> dict:
    return {
        "action": action, "path": path,
        "candidates": candidates or [], "findings": findings or [],
    }


def dispatch_json(
    ready=None, active=None, blocked=None, findings=None, decision=None
) -> dict[str, Any]:
    """Return dispatch output holding one ready, one active and one blocked item by default."""
    ready = [entry(READY)] if ready is None else ready
    active = [entry(ACTIVE)] if active is None else active
    blocked = [entry(BLOCKED, [finding()])] if blocked is None else blocked
    return {
        "schema_version": 1,
        "ready": ready,
        "active": active,
        "blocked": blocked,
        "findings": [] if findings is None else findings,
        "decision": argless_decision(active, ready) if decision is None else decision,
    }


def encode(obj: Any) -> bytes:
    return json.dumps(obj).encode("utf-8")


BASE = {
    "schema_version": 1,
    "ready": [],
    "active": [],
    "blocked": [],
    "findings": [],
    "decision": {"action": "none", "path": None, "candidates": [], "findings": []},
}
BASE_BYTES = encode(BASE)
assert dispatch_json(ready=[], active=[], blocked=[]) == BASE


def feed(data: bytes) -> tuple[Callable[[], int], Callable[[], None]]:
    """Return an opener over a pipe that delivers ``data`` then end of file."""
    r, w = os.pipe()

    def write() -> None:
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(w, view[:65_536]) :]
        except BrokenPipeError:
            pass  # the export refused before reading, and the reader closed
        finally:
            os.close(w)

    thread = threading.Thread(target=write, daemon=True)
    thread.start()

    def finish() -> None:
        os.close(r)  # a writer blocked on an unread pipe gets EPIPE and exits
        thread.join(30)

    return (lambda: r), finish


def through_pipe(data: bytes) -> Any:
    """Read ``data`` through a real descriptor, then check it; return bytes-or-reason result."""
    opener, finish = feed(data)
    try:
        result = rd.read(opener, LIMIT, 30)
    finally:
        finish()
    if result.reason is not None:
        return result.reason
    return rd.check(result.data)


def reason_or_checked(outcome: Any) -> str:
    return outcome if isinstance(outcome, str) else "checked"


# --- AC-0001 to AC-0006: the table of named byte streams ------------------------------


def mutated(mutate: Callable[[dict], None], obj: dict | None = None) -> bytes:
    data = copy.deepcopy(obj if obj is not None else dispatch_json())
    mutate(data)
    return encode(data)


def _set(target: dict, key: str, value: Any) -> None:
    if value is _ABSENT:
        del target[key]
    else:
        target[key] = value


def top_set(key: str, value: Any) -> Callable[[dict], None]:
    return lambda data: _set(data, key, value)


def blocked_finding_set(key: str, value: Any) -> Callable[[dict], None]:
    return lambda data: _set(data["blocked"][0]["findings"][0], key, value)


def blocked_entry_set(key: str, value: Any) -> Callable[[dict], None]:
    return lambda data: _set(data["blocked"][0], key, value)


def ready_entry_set(key: str, value: Any) -> Callable[[dict], None]:
    return lambda data: _set(data["ready"][0], key, value)


def decision_set(key: str, value: Any) -> Callable[[dict], None]:
    return lambda data: _set(data["decision"], key, value)


def top_finding_set(key: str, value: Any) -> Callable[[dict], None]:
    def apply(data: dict) -> None:
        data["findings"] = [finding()]
        _set(data["findings"][0], key, value)

    return apply


def decision_finding_set(key: str, value: Any) -> Callable[[dict], None]:
    """Plant a finding in ``decision.findings`` on an argless refusal, then change it."""

    def apply(data: dict) -> None:
        data.update(dispatch_json(ready=[], active=[], blocked=[]))
        data["decision"] = decision_of("refuse", findings=[finding("invalid_workspace", "x")])
        _set(data["decision"]["findings"][0], key, value)

    return apply


def built(**lists: Any) -> bytes:
    """Dispatch output over the given lists, with the decision recomputed from them."""
    return encode(dispatch_json(**lists))


def with_extra_member(raw: str) -> bytes:
    """Return the base input with ``"x": <raw>`` appended as a raw JSON text member."""
    text = BASE_BYTES.decode("utf-8")
    return (text[:-1] + ', "x": ' + raw + "}").encode("utf-8")


def workspace_status_output() -> bytes:
    """The stdout of ``workspace-status status``, which is not dispatch output."""
    return encode({
        "schema_version": 1, "mode": "status", "workspace_present": True, "workspace_root": ".",
        "canonical": {
            "performed": True, "bounded": True, "findings": [],
            "ready": [{"path": READY, "dispatchable": True, "findings": []}],
            "active": [], "blocked": [],
        },
    })


NESTED = "[" * 100_000 + "]" * 100_000
WORKSPACE_FAILURES = ("invalid_workspace", "configuration_mismatch", "unsafe_path")
REFUSAL = decision_of("refuse", findings=[finding("invalid_workspace", "Correct workspace.toml.")])


def refusal_output(**changes: Any) -> bytes:
    """The output dispatch.py prints with no selector when it cannot use workspace.toml."""
    data = dispatch_json(ready=[], active=[], blocked=[], decision=REFUSAL)
    data["findings"] = [finding("invalid_workspace", "Correct workspace.toml.")]
    data.update(changes)
    return encode(data)


def _two_ready() -> dict[str, Any]:
    return dispatch_json(ready=[entry(READY), entry(BLOCKED)], active=[], blocked=[])


CHECK_CASES: list[tuple[str, bytes, str]] = [
    # AC-0006: the early reasons
    ("zero_bytes", b"", "empty"),
    ("only_whitespace", b" \t\r\n \n", "empty"),
    ("invalid_utf8", b"\xff\xfe" + BASE_BYTES, "not_json"),
    ("byte_order_mark", b"\xef\xbb\xbf" + BASE_BYTES, "not_json"),
    ("array_top_level", b"[1, 2]", "not_json"),
    ("string_top_level", b'"status"', "not_json"),
    ("number_top_level", b"1", "not_json"),
    ("null_top_level", b"null", "not_json"),
    ("truncated_object", BASE_BYTES[:-5], "not_json"),
    ("repeated_name_top", BASE_BYTES[:-1] + b', "ready": []}', "not_json"),
    (
        "repeated_name_nested",
        BASE_BYTES.replace(b'"candidates": []', b'"candidates": [], "candidates": []'),
        "not_json",
    ),
    ("nan", with_extra_member("NaN"), "not_json"),
    ("infinity", with_extra_member("Infinity"), "not_json"),
    ("negative_infinity", with_extra_member("-Infinity"), "not_json"),
    ("second_value", BASE_BYTES + b" " + BASE_BYTES, "not_json"),
    ("second_value_adjacent", BASE_BYTES + b"{}", "not_json"),
    ("nested_100000_deep", with_extra_member(NESTED), "not_json"),
    (
        "repeated_name_and_schema_version_2",
        b'{"schema_version": 2, "schema_version": 2, "ready": []}',
        "not_json",
    ),
    # AC-0001: the top level
    ("top_key_absent_decision", mutated(top_set("decision", _ABSENT)), "wrong_schema"),
    ("top_key_absent_findings", mutated(top_set("findings", _ABSENT)), "wrong_schema"),
    ("top_key_added", mutated(top_set("mode", "status")), "wrong_schema"),
    ("top_key_added_null", mutated(top_set("workspace_present", None)), "wrong_schema"),
    ("schema_version_true", mutated(top_set("schema_version", True)), "wrong_schema"),
    ("schema_version_float", mutated(top_set("schema_version", 1.0)), "wrong_schema"),
    ("schema_version_string", mutated(top_set("schema_version", "1")), "wrong_schema"),
    ("schema_version_2", mutated(top_set("schema_version", 2)), "wrong_schema"),
    ("schema_version_absent", mutated(top_set("schema_version", _ABSENT)), "wrong_schema"),
    *[
        (f"{key}_{label}", mutated(top_set(key, value)), "wrong_schema")
        for key in ("ready", "active", "blocked", "findings")
        for label, value in (("absent", _ABSENT), ("object", {}), ("null", None), ("str", "x"))
    ],
    # AC-0001: items
    ("item_not_object", built(blocked=["x"]), "wrong_schema"),
    ("item_key_absent_slug", mutated(blocked_entry_set("slug", _ABSENT)), "wrong_schema"),
    ("item_key_absent_status", mutated(blocked_entry_set("status", _ABSENT)), "wrong_schema"),
    ("item_key_absent_findings", mutated(blocked_entry_set("findings", _ABSENT)), "wrong_schema"),
    ("item_key_added", mutated(blocked_entry_set("dispatchable", False)), "wrong_schema"),
    ("item_path_absent", mutated(blocked_entry_set("path", _ABSENT)), "wrong_schema"),
    ("item_path_number", mutated(blocked_entry_set("path", 7)), "wrong_schema"),
    ("item_path_null", mutated(blocked_entry_set("path", None)), "wrong_schema"),
    ("item_slug_number", mutated(blocked_entry_set("slug", 7)), "wrong_schema"),
    ("item_slug_null", mutated(blocked_entry_set("slug", None)), "wrong_schema"),
    ("item_status_number", mutated(blocked_entry_set("status", 7)), "wrong_schema"),
    ("item_status_bool", mutated(blocked_entry_set("status", False)), "wrong_schema"),
    ("item_status_list", mutated(blocked_entry_set("status", [])), "wrong_schema"),
    ("item_findings_object", mutated(blocked_entry_set("findings", {})), "wrong_schema"),
    ("item_findings_null", mutated(blocked_entry_set("findings", None)), "wrong_schema"),
    ("ready_item_with_a_finding", built(ready=[entry(READY, [finding()])]), "wrong_schema"),
    ("active_item_with_a_finding", built(active=[entry(ACTIVE, [finding()])]), "wrong_schema"),
    ("ready_item_status_number", mutated(ready_entry_set("status", 1)), "wrong_schema"),
    ("path_in_ready_and_active", built(active=[entry(READY)]), "wrong_schema"),
    ("path_in_ready_and_blocked", built(blocked=[entry(READY, [finding()])]), "wrong_schema"),
    ("path_in_active_and_blocked", built(blocked=[entry(ACTIVE, [finding()])]), "wrong_schema"),
    (
        "path_twice_in_ready",
        built(ready=[entry(READY), entry(READY)], active=[], blocked=[]),
        "wrong_schema",
    ),
    (
        "path_twice_in_active",
        built(ready=[], active=[entry(ACTIVE), entry(ACTIVE)], blocked=[]),
        "wrong_schema",
    ),
    # AC-0002: findings, in each of the three places
    *[
        (f"{place}_{label}", mutated(mutate(key, value)), "wrong_schema")
        for place, mutate in (
            ("blocked_finding", blocked_finding_set),
            ("top_finding", top_finding_set),
            ("decision_finding", decision_finding_set),
        )
        for label, key, value in (
            ("key_absent_code", "code", _ABSENT),
            ("key_absent_path", "path", _ABSENT),
            ("key_absent_dispatchable", "dispatchable", _ABSENT),
            ("key_absent_next_action", "next_action", _ABSENT),
            ("key_added", "detail", "marker"),
            ("code_number", "code", 3),
            ("code_empty", "code", ""),
            ("code_uppercase_start", "code", "Bad"),
            ("code_digit_start", "code", "1bad"),
            ("code_65_chars", "code", "a" * 65),
            ("code_plus_space", "code", "missing_plan "),
            ("code_plus_dash", "code", "missing_plan-"),
            ("code_plus_uppercase", "code", "missing_planX"),
            ("code_plus_non_ascii", "code", "missing_plané"),
            ("code_plus_line_feed", "code", "missing_plan\n"),
            ("path_number", "path", 3),
            ("path_list", "path", []),
            ("dispatchable_string", "dispatchable", "no"),
            ("dispatchable_null", "dispatchable", None),
            ("dispatchable_zero", "dispatchable", 0),
            ("next_action_number", "next_action", 1),
            ("next_action_null", "next_action", None),
            ("next_action_501", "next_action", "x" * 501),
            ("next_action_high_surrogate", "next_action", "a\ud800b"),
            ("next_action_low_surrogate", "next_action", "\udfff"),
        )
    ],
    ("blocked_finding_not_object", mutated(blocked_entry_set("findings", ["x"])), "wrong_schema"),
    ("top_finding_not_object", mutated(top_set("findings", [3])), "wrong_schema"),
    (
        "decision_finding_not_object",
        mutated(top_set("decision", decision_of("none", findings=[3]))),
        "wrong_schema",
    ),
    # AC-0003: the decision
    ("decision_absent", mutated(top_set("decision", _ABSENT)), "wrong_schema"),
    ("decision_list", mutated(top_set("decision", [])), "wrong_schema"),
    ("decision_null", mutated(top_set("decision", None)), "wrong_schema"),
    ("decision_key_absent_action", mutated(decision_set("action", _ABSENT)), "wrong_schema"),
    ("decision_key_absent_path", mutated(decision_set("path", _ABSENT)), "wrong_schema"),
    ("decision_key_absent_candidates", mutated(decision_set("candidates", _ABSENT)), "wrong_schema"),
    ("decision_key_absent_findings", mutated(decision_set("findings", _ABSENT)), "wrong_schema"),
    ("decision_key_added", mutated(decision_set("reason", "x")), "wrong_schema"),
    *[
        (f"decision_action_{name}", mutated(decision_set("action", value)), "wrong_schema")
        for name, value in (
            ("other", "invalid_selector"), ("capital", "Start"), ("empty", ""),
            ("number", 1), ("null", None), ("list", ["none"]),
        )
    ],
    ("decision_path_number", mutated(decision_set("path", 3)), "wrong_schema"),
    ("decision_path_list", mutated(decision_set("path", [])), "wrong_schema"),
    ("decision_candidates_null", mutated(decision_set("candidates", None)), "wrong_schema"),
    ("decision_candidates_object", mutated(decision_set("candidates", {})), "wrong_schema"),
    ("decision_candidates_numbers", mutated(decision_set("candidates", [1])), "wrong_schema"),
    ("decision_candidates_null_member", mutated(decision_set("candidates", [None])), "wrong_schema"),
    ("decision_findings_object", mutated(decision_set("findings", {})), "wrong_schema"),
    ("workspace_status_status_output", workspace_status_output(), "wrong_schema"),
    # AC-0004: the decision must be the argless decision or the argless refusal
    (
        "start_names_a_blocked_item",
        built(ready=[], active=[], blocked=[entry(BLOCKED, [finding()])],
              decision=decision_of("start", BLOCKED)),
        "wrong_schema",
    ),
    (
        "start_names_a_path_in_no_list",
        built(decision=decision_of("start", "docs/specs/nowhere/spec.md")),
        "wrong_schema",
    ),
    (
        "start_over_one_ready_and_one_active",
        built(decision=decision_of("start", READY)),
        "wrong_schema",
    ),
    (
        "resume_names_a_ready_item",
        built(ready=[entry(READY)], active=[], blocked=[], decision=decision_of("resume", READY)),
        "wrong_schema",
    ),
    (
        "ask_omits_a_ready_path",
        built(ready=[entry(READY), entry(BLOCKED)], active=[], blocked=[],
              decision=decision_of("ask", None, [READY])),
        "wrong_schema",
    ),
    (
        "ask_in_the_wrong_order",
        built(ready=[entry(READY), entry(BLOCKED)], active=[], blocked=[],
              decision=decision_of("ask", None, [BLOCKED, READY])),
        "wrong_schema",
    ),
    (
        "ask_over_ready_while_one_is_active",
        built(decision=decision_of("ask", None, [READY])),
        "wrong_schema",
    ),
    (
        "none_with_a_ready_item",
        built(ready=[entry(READY)], active=[], blocked=[], decision=decision_of("none")),
        "wrong_schema",
    ),
    (
        "none_carrying_a_finding",
        built(ready=[], active=[], blocked=[],
              decision=decision_of("none", findings=[finding("missing_artifact", "x")])),
        "wrong_schema",
    ),
    (
        "start_carrying_a_finding",
        built(ready=[entry(READY)], active=[], blocked=[],
              decision=decision_of("start", READY, findings=[finding("missing_artifact", "x")])),
        "wrong_schema",
    ),
    (
        "start_with_a_candidate",
        built(ready=[entry(READY)], active=[], blocked=[],
              decision=decision_of("start", READY, [READY])),
        "wrong_schema",
    ),
    (
        "named_start_over_two_ready",
        encode({**_two_ready(), "decision": decision_of("start", READY)}),
        "wrong_schema",
    ),
    (
        "named_start_no_such_usable_workspace",
        built(ready=[entry(READY)], active=[], blocked=[],
              decision=decision_of("refuse", findings=[finding("missing_artifact", "Create it.")])),
        "wrong_schema",
    ),
    (
        "named_start_no_such_no_workspace_toml",
        built(ready=[], active=[], blocked=[],
              decision=decision_of("refuse", findings=[finding("missing_artifact", "Create it.")])),
        "wrong_schema",
    ),
    ("refusal_with_a_ready_item", refusal_output(ready=[entry(READY)]), "wrong_schema"),
    ("refusal_with_a_blocked_item", refusal_output(blocked=[entry(BLOCKED, [finding()])]), "wrong_schema"),
    (
        "refusal_with_a_path",
        refusal_output(decision=decision_of("refuse", READY, findings=REFUSAL["findings"])),
        "wrong_schema",
    ),
    (
        "refusal_with_a_candidate",
        refusal_output(decision=decision_of("refuse", None, [READY], REFUSAL["findings"])),
        "wrong_schema",
    ),
    (
        "refusal_with_no_finding",
        refusal_output(decision=decision_of("refuse")),
        "wrong_schema",
    ),
    (
        "refusal_with_two_findings",
        refusal_output(decision=decision_of("refuse", findings=[
            finding("invalid_workspace", "a"), finding("invalid_workspace", "b")])),
        "wrong_schema",
    ),
    (
        "refusal_with_another_code",
        refusal_output(decision=decision_of("refuse", findings=[finding("missing_plan", "a")])),
        "wrong_schema",
    ),
    # AC-0005: the three workspace failure codes
    ("argless_refusal", refusal_output(), "bad_workspace"),
    (
        "argless_refusal_with_empty_top_findings",
        refusal_output(findings=[]),
        "bad_workspace",
    ),
    *[
        (
            f"workspace_failure_{code}_in_a_blocked_item",
            built(blocked=[entry("workspace.toml", [finding(code, "Fix it.", "workspace.toml")])]),
            "bad_workspace",
        )
        for code in WORKSPACE_FAILURES
    ],
    *[
        (
            f"workspace_failure_{code}_top_level_only",
            built(findings=[finding(code, "Replace it.")]),
            "bad_workspace",
        )
        for code in WORKSPACE_FAILURES
    ],
    (
        "workspace_failure_in_a_refusal_beside_a_top_level_one",
        refusal_output(findings=[finding("unsafe_path", "Replace it.")]),
        "bad_workspace",
    ),
    # AC-0006: wrong schema is checked before bad workspace
    (
        "wrong_schema_beats_bad_workspace",
        mutated(lambda d: (d.update(schema_version=2),
                           d.update(findings=[finding("unsafe_path", "Replace it.")]))),
        "wrong_schema",
    ),
    (
        "wrong_schema_decision_beats_bad_workspace",
        built(findings=[finding("unsafe_path", "x")], decision=decision_of("none")),
        "wrong_schema",
    ),
    # accepted inputs
    ("base_input", BASE_BYTES, "checked"),
    ("populated_input", encode(dispatch_json()), "checked"),
    ("leading_and_trailing_whitespace", b" \r\n" + BASE_BYTES + b"\n\t ", "checked"),
    ("blocked_item_with_a_null_status", built(blocked=[entry(BLOCKED, [finding()], status=None)]), "checked"),
    ("ready_item_with_a_null_status", built(ready=[entry(READY, status=None)]), "checked"),
    ("next_action_500", mutated(blocked_finding_set("next_action", "x" * 500)), "checked"),
    ("finding_code_64_chars", mutated(blocked_finding_set("code", "a" * 64)), "checked"),
    ("finding_path_null", mutated(blocked_finding_set("path", None)), "checked"),
    ("finding_path_string", mutated(blocked_finding_set("path", "anything")), "checked"),
    ("two_ready_ask", encode(_two_ready()), "checked"),
    (
        "two_active_ask",
        built(ready=[entry(READY)], active=[entry(ACTIVE), entry(BLOCKED)], blocked=[]),
        "checked",
    ),
    (
        "one_ready_only_start",
        built(ready=[entry(READY)], active=[], blocked=[]),
        "checked",
    ),
    (
        "lawful_repeat_in_blocked",
        built(blocked=[entry(BLOCKED, [finding()]), entry(BLOCKED, [finding()])]),
        "checked",
    ),
    (
        "blocked_waiter_beside_a_ready_dependency",
        built(ready=[entry(READY)], active=[], blocked=[entry(BLOCKED, [finding(path=READY)])]),
        "checked",
    ),
]


@pytest.mark.parametrize(
    ("data", "expected"),
    [pytest.param(d, e, id=name) for name, d, e in CHECK_CASES],
)
def test_check_gives_the_reason_the_spec_names(data: bytes, expected: str) -> None:
    assert reason_or_checked(rd.check(data)) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [pytest.param(d, e, id=name) for name, d, e in CHECK_CASES],
)
def test_every_case_gives_the_same_reason_through_a_pipe(data: bytes, expected: str) -> None:
    assert reason_or_checked(through_pipe(data)) == expected


def test_case_names_are_unique() -> None:
    names = [name for name, _, _ in CHECK_CASES]
    assert len(names) == len(set(names))


def test_surrogate_pair_next_action_is_not_a_lone_surrogate() -> None:
    data = mutated(blocked_finding_set("next_action", "\U0001f600"))
    assert not isinstance(rd.check(data), str)


def test_check_never_raises_on_hostile_json_shapes() -> None:
    for raw in (b"{}", b"[]", b'{"decision": 1}', b'{"ready": true}', b"0"):
        assert isinstance(rd.check(raw), str)


# --- AC-0006: the size limit ----------------------------------------------------------


def padded(size: int) -> bytes:
    return BASE_BYTES + b" " * (size - len(BASE_BYTES))


def test_limit_and_deadline_constants() -> None:
    assert rd.INPUT_LIMIT_BYTES == 4_194_304
    assert rd.READ_DEADLINE_SECONDS == 60


def test_input_of_exactly_the_limit_is_checked() -> None:
    data = padded(4_194_304)
    assert len(data) == 4_194_304
    assert reason_or_checked(through_pipe(data)) == "checked"


def test_input_one_byte_over_the_limit_is_too_large() -> None:
    data = padded(4_194_305)
    assert len(data) == 4_194_305
    assert through_pipe(data) == "too_large"


def test_never_ending_stream_stops_after_limit_plus_one_bytes(monkeypatch) -> None:
    r, w = os.pipe()
    consumed = 0
    real_read = os.read

    def counting_read(fd: int, n: int) -> bytes:
        nonlocal consumed
        chunk = real_read(fd, n)
        if fd == r:
            consumed += len(chunk)
        return chunk

    def write_forever() -> None:
        block = b" " * 65_536
        try:
            while True:
                os.write(w, block)
        except OSError:
            pass

    monkeypatch.setattr(os, "read", counting_read)
    writer = threading.Thread(target=write_forever, daemon=True)
    writer.start()
    result = rd.read(lambda: r, LIMIT, 30)
    monkeypatch.undo()
    os.close(r)  # the writer's next write fails and it exits
    writer.join(10)
    os.close(w)
    assert (result.data, result.reason) == (None, "too_large")
    assert consumed <= 4_194_305
    assert not writer.is_alive()


def _release_held_pipe(r: int, w: int, before: set[threading.Thread]) -> None:
    """Close a held-open pipe only once every reader thread started on it has exited.

    Closing the write end gives a blocked reader end of file; the read end is closed after
    those threads are joined, so no abandoned reader can ever read a reused descriptor.
    """
    os.close(w)
    for thread in set(threading.enumerate()) - before:
        if thread is not threading.current_thread():
            thread.join(30)
            assert not thread.is_alive(), thread
    os.close(r)


# --- AC-0047: the deadline ------------------------------------------------------------


@pytest.mark.parametrize("sent", [b"", BASE_BYTES[:100]], ids=["no_bytes", "first_100_bytes"])
def test_a_held_open_pipe_times_out_and_its_bytes_are_unused(sent: bytes) -> None:
    r, w = os.pipe()
    before = set(threading.enumerate())
    try:
        os.write(w, sent) if sent else None
        started = time.monotonic()
        result = rd.read(lambda: r, LIMIT, 0.5)
        elapsed = time.monotonic() - started
        assert (result.data, result.reason) == (None, "timed_out")
        assert elapsed < 2
    finally:
        _release_held_pipe(r, w, before)


# --- AC-0046: unusable descriptors, with nothing on standard error --------------------


def test_opener_returning_none_is_unreadable(capfd) -> None:
    assert rd.read(lambda: None, LIMIT, 5).reason == "unreadable"
    assert capfd.readouterr().err == ""


def test_closed_descriptor_is_unreadable(capfd) -> None:
    r, w = os.pipe()
    os.close(r)
    os.close(w)
    result = rd.read(lambda: r, LIMIT, 5)
    assert (result.data, result.reason) == (None, "unreadable")
    assert capfd.readouterr().err == ""


def test_directory_descriptor_is_unreadable(tmp_path, capfd) -> None:
    fd = os.open(tmp_path, os.O_RDONLY)
    try:
        result = rd.read(lambda: fd, LIMIT, 5)
    finally:
        os.close(fd)
    assert (result.data, result.reason) == (None, "unreadable")
    assert capfd.readouterr().err == ""


def test_write_only_descriptor_is_unreadable(tmp_path, capfd) -> None:
    target = tmp_path / "out.json"
    target.write_bytes(BASE_BYTES)
    fd = os.open(target, os.O_WRONLY)
    try:
        result = rd.read(lambda: fd, LIMIT, 5)
    finally:
        os.close(fd)
    assert (result.data, result.reason) == (None, "unreadable")
    assert capfd.readouterr().err == ""


def test_empty_non_blocking_pipe_with_open_write_end_is_unreadable(capfd) -> None:
    r, w = os.pipe()
    os.set_blocking(r, False)
    try:
        started = time.monotonic()
        result = rd.read(lambda: r, LIMIT, 5)
        assert time.monotonic() - started < 2
    finally:
        os.close(r)
        os.close(w)
    assert (result.data, result.reason) == (None, "unreadable")
    assert capfd.readouterr().err == ""


def test_opener_raising_unsupported_operation_is_unreadable(capfd) -> None:
    def opener() -> int:
        raise io.UnsupportedOperation("fileno")

    result = rd.read(opener, LIMIT, 5)
    assert (result.data, result.reason) == (None, "unreadable")
    assert capfd.readouterr().err == ""


def test_opener_returning_a_non_descriptor_is_unreadable(capfd) -> None:
    result = rd.read(lambda: "0", LIMIT, 5)  # type: ignore[arg-type,return-value]
    assert result.reason == "unreadable"
    assert capfd.readouterr().err == ""


# --- AC-0007: a terminal reads nothing ------------------------------------------------


def test_terminal_is_empty_and_nothing_is_read(monkeypatch) -> None:
    master, slave = os.openpty()
    reads: list[int] = []
    real_read = os.read

    def watching_read(fd: int, n: int) -> bytes:
        reads.append(fd)
        return real_read(fd, n)

    try:
        os.write(master, b"typed text\n")
        monkeypatch.setattr(os, "read", watching_read)
        result = rd.read(lambda: slave, LIMIT, 5)
        monkeypatch.undo()
    finally:
        os.close(master)
        os.close(slave)
    assert (result.data, result.reason) == (None, "empty")
    assert slave not in reads


# --- AC-0009: the argless work-loop mark ----------------------------------------------


def checked_of(obj: dict) -> Any:
    checked = rd.check(encode(obj))
    assert not isinstance(checked, str), checked
    return checked


def mark(**lists: Any) -> dict[str, Any]:
    return rd.start(checked_of(dispatch_json(**lists)), PATH_TO_ID)


def test_one_ready_item_outside_the_export_starts_nothing_marked() -> None:
    obj = dispatch_json(ready=[entry("docs/specs/absent-spec/spec.md")], active=[], blocked=[])
    projection = rd.project(checked_of(obj), PATH_TO_ID)
    assert projection["start"] == {"rule": "start", "id": None, "held": False, "active_count": 0}
    assert projection["ready"] == []


def test_the_four_marks() -> None:
    assert mark(ready=[entry(READY)], active=[entry(ACTIVE)], blocked=[]) == {
        "rule": "resume", "id": "spec:charlie-spec", "held": False, "active_count": 1,
    }
    assert mark(ready=[entry(READY)], active=[], blocked=[]) == {
        "rule": "start", "id": "spec:bravo-spec", "held": False, "active_count": 0,
    }
    assert mark(ready=[entry(READY), entry(BLOCKED)], active=[], blocked=[]) == {
        "rule": "ask", "id": None, "held": False, "active_count": 0,
    }
    assert mark(ready=[], active=[], blocked=[]) == {
        "rule": "none", "id": None, "held": False, "active_count": 0,
    }


def test_one_active_item_outside_the_export_resumes_nothing_marked() -> None:
    assert mark(ready=[entry(READY)], active=[entry("elsewhere.md")], blocked=[]) == {
        "rule": "resume", "id": None, "held": False, "active_count": 1,
    }


def test_two_active_items_ask_even_when_one_path_is_unloaded() -> None:
    obj = dispatch_json(ready=[entry(READY)], active=[entry(ACTIVE), entry("elsewhere.md")], blocked=[])
    checked = checked_of(obj)
    assert rd.start(checked, PATH_TO_ID) == {
        "rule": "ask", "id": None, "held": False, "active_count": 2,
    }
    assert rd.project(checked, PATH_TO_ID)["active"] == ["spec:charlie-spec"]


def test_the_dep_spec_open_shape_starts_the_ready_dependency() -> None:
    """A ready bravo-spec and a blocked waiter whose finding names bravo-spec still start."""
    got = mark(
        ready=[entry(READY)], active=[],
        blocked=[entry(BLOCKED, [finding(path=READY)])],
    )
    assert got == {"rule": "start", "id": "spec:bravo-spec", "held": False, "active_count": 0}


def test_a_top_level_finding_about_the_resumed_path_does_not_hold_the_mark() -> None:
    got = mark(ready=[], active=[entry(ACTIVE)], blocked=[], findings=[finding(path=ACTIVE)])
    assert (got["rule"], got["id"], got["held"]) == ("resume", "spec:charlie-spec", False)


def test_ask_over_two_ready_items_marks_nothing() -> None:
    got = mark(ready=[entry(READY), entry(BLOCKED)], active=[], blocked=[])
    assert (got["rule"], got["id"], got["held"], got["active_count"]) == ("ask", None, False, 0)


def test_start_reads_the_checked_decision() -> None:
    checked = checked_of(dispatch_json(ready=[entry(READY)], active=[], blocked=[]))
    assert checked.decision == decision_of("start", READY)
    forged = checked._replace(decision=decision_of("start", ACTIVE))
    assert rd.start(forged, PATH_TO_ID)["id"] == "spec:charlie-spec"


# --- the projection ---------------------------------------------------------------------


def test_projection_has_exactly_the_allowlisted_members() -> None:
    obj = dispatch_json(
        ready=[entry(READY, slug="marker-slug-r", status="marker-status-r")],
        active=[entry(ACTIVE, slug="marker-slug-a", status=None)],
        blocked=[entry(BLOCKED, [finding(path="marker-path")], slug="marker-slug-b")],
        findings=[finding(path="marker-top")],
    )
    projection = rd.project(checked_of(obj), PATH_TO_ID)
    assert set(projection) == {"checked", "active", "ready", "blocked", "start"}
    assert projection["checked"] is True
    assert projection["active"] == ["spec:charlie-spec"]
    assert projection["ready"] == ["spec:bravo-spec"]
    assert projection["blocked"] == [
        {
            "id": "spec:golf-new",
            "findings": [
                {"code": "unsatisfied_dependency", "next_action": DEP_ACTION, "known": True}
            ],
        }
    ]
    assert list(projection["start"]) == ["rule", "id", "held", "active_count"]
    assert "marker" not in json.dumps(projection)


DROPPED = [
    "/etc/passwd",
    "C:\\x\\spec.md",
    "../x/spec.md",
    "docs/specs/../../x/spec.md",
    "docs/specs//bravo-spec/spec.md",
    "no-such-slug",
    "docs/specs/absent-spec/spec.md",
    "docs/specs/bravo-spec/spec.md/",
    "docs/specs/Bravo-Spec/spec.md",
    "workspace.toml",
]


def test_only_exact_loaded_paths_are_kept() -> None:
    as_ready = dispatch_json(ready=[entry(p) for p in DROPPED], active=[], blocked=[])
    as_active = dispatch_json(ready=[], active=[entry(p) for p in DROPPED], blocked=[])
    as_blocked = dispatch_json(ready=[], active=[], blocked=[entry(p, [finding()]) for p in DROPPED])
    assert rd.project(checked_of(as_ready), PATH_TO_ID)["ready"] == []
    assert rd.project(checked_of(as_active), PATH_TO_ID)["active"] == []
    assert rd.project(checked_of(as_blocked), PATH_TO_ID)["blocked"] == []


def test_lists_keep_input_order() -> None:
    obj = dispatch_json(ready=[entry(BLOCKED), entry(READY)], active=[], blocked=[])
    assert rd.project(checked_of(obj), PATH_TO_ID)["ready"] == ["spec:golf-new", "spec:bravo-spec"]


def test_a_repeated_blocked_path_appears_once_with_codes_in_input_order() -> None:
    blocked = [
        entry(BLOCKED, [finding("missing_plan", "Create and approve the plan before dispatch.")]),
        entry(OTHER, [finding()]),
        entry(
            BLOCKED,
            [
                finding("unsatisfied_dependency"),
                finding("missing_plan", "Create and approve the plan before dispatch."),
            ],
        ),
        entry(
            BLOCKED,
            [finding("dependency_cycle", "Break the cycle through an explicit plan change.")],
        ),
    ]
    projection = rd.project(
        checked_of(dispatch_json(ready=[], active=[], blocked=blocked)), PATH_TO_ID
    )
    assert [b["id"] for b in projection["blocked"]] == ["spec:golf-new", "intent:bravo-feat"]
    codes = [f["code"] for f in projection["blocked"][0]["findings"]]
    assert codes == ["missing_plan", "unsatisfied_dependency", "dependency_cycle"]


def test_known_is_true_only_for_a_pair_in_the_finding_table() -> None:
    table = rd._KNOWN_FINDINGS
    assert table
    # The workspace-failure codes refuse the whole input, so they never project.
    pairs = [(c, a) for c, a in table.items() if c not in WORKSPACE_FAILURES]
    blocked = [
        entry(BLOCKED, [finding(code, action) for code, action in pairs]),
        entry(READY, [finding(pairs[0][0], "another sentence")]),
        entry(ACTIVE, [finding("brand_new_code", pairs[0][1])]),
    ]
    projection = rd.project(
        checked_of(dispatch_json(ready=[], active=[], blocked=blocked)), PATH_TO_ID
    )
    by_id = {b["id"]: b["findings"] for b in projection["blocked"]}
    assert all(f["known"] is True for f in by_id["spec:golf-new"])
    assert [f["code"] for f in by_id["spec:golf-new"]] == [c for c, _ in pairs]
    assert by_id["spec:bravo-spec"][0]["known"] is False
    assert by_id["spec:charlie-spec"][0]["known"] is False
    assert by_id["spec:bravo-spec"][0]["next_action"] == "another sentence"


def test_member_wraps_a_refusal_and_a_projection_failure() -> None:
    assert rd.member(b"", PATH_TO_ID) == {"checked": False, "reason": "empty"}
    assert rd.member(encode(dispatch_json()), PATH_TO_ID)["checked"] is True
    assert rd.member(encode(dispatch_json()), None) == {  # type: ignore[arg-type]
        "checked": False,
        "reason": "wrong_schema",
    }
    assert rd.unchecked("not_requested") == {"checked": False, "reason": "not_requested"}


def test_reason_set_matches_the_spec() -> None:
    assert (rd.NOT_REQUESTED, *rd.REASONS) == (
        "not_requested",
        "unreadable",
        "timed_out",
        "too_large",
        "empty",
        "not_json",
        "wrong_schema",
        "bad_workspace",
        "page_too_big",
    )
    assert "no_workspace" not in rd.REASONS
    assert max(map(len, rd.REASONS)) <= len("not_requested")


# --- the finding vocabulary copy --------------------------------------------------------


def test_readiness_vocabulary_matches_workspace_status() -> None:
    tree = ast.parse(_ENGINE.read_text(encoding="utf-8"))
    values = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_FINDING_NEXT_ACTIONS" for t in node.targets)
    ]
    assert len(values) == 1
    assert ast.literal_eval(values[0]) == rd._KNOWN_FINDINGS


# =======================================================================================
# export --readiness -: the command, the payload member and the safety of the page
# =======================================================================================

nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_readiness_nav_t")
view = nav._load_view_mod()
rmod = nav._load_readiness_mod()  # the module run_export loads: the deadline seam lives here

_MIXED = pathlib.Path(__file__).resolve().parent / "fixtures" / "mixed"
_OUTSIDE: dict[str, pathlib.Path] = {}


def _mixed_outside_git() -> pathlib.Path:
    """Return one copy of ``mixed`` outside any Git repository, made on first use.

    An export from inside a repository asks Git for its work trees before it writes, under a
    five-second limit.  The failing-input tables run hundreds of exports and test nothing about
    the destination, so they export from this copy and never wait on that call under load.
    """
    if "root" not in _OUTSIDE:
        base = pathlib.Path(tempfile.mkdtemp(prefix="readiness-mixed-")).resolve()
        atexit.register(shutil.rmtree, base, True)  # the copy lives as long as the session
        root = base / "mixed"
        shutil.copytree(_MIXED, root)
        _OUTSIDE["root"] = root
    return _OUTSIDE["root"]


_SCRIPT = _SCRIPTS / "navigate_intents.py"
_PIN = datetime.datetime(2026, 10, 21, 12, 0, tzinfo=datetime.UTC)
_DATA_BLOCK = re.compile(
    r'<script type="application/json" id="intent-data">(.*?)</script>', re.DOTALL
)
_PAYLOAD_KEYS = [
    "schema", "scope", "provenance", "summary", "records", "outstanding",
    "nodes", "edges", "source_links", "dependencies", "readiness",
]
_derived: dict[tuple[str, str | None], dict[str, Any]] = {}


@pytest.fixture
def pinned(monkeypatch):
    """Pin the clock and derive each corpus once.

    The failing-input tables run one export per case.  Deriving the same corpus
    each time would cost minutes and tests nothing about the status input, so
    the derivation is cached under the pinned clock and copied per call.
    """
    monkeypatch.setattr(nav, "_now", lambda: _PIN)
    real = nav.build_view_payload

    def cached(root, from_identity=None, **kwargs):
        key = (str(root), from_identity)
        if key not in _derived:
            _derived[key] = real(root, from_identity, **kwargs)
        return copy.deepcopy(_derived[key])

    monkeypatch.setattr(nav, "build_view_payload", cached)


class Ran:
    """One export: its result, exit code, and the page and payload it wrote, if any."""

    def __init__(self, result: dict[str, Any], code: int, dest: pathlib.Path) -> None:
        self.result, self.code, self.dest = result, code, dest
        self.files = sorted(p.name for p in dest.iterdir())
        self.html: str | None = None
        self.payload: dict[str, Any] | None = None
        if result.get("status") == "ok":
            self.html = pathlib.Path(result["path"]).read_text(encoding="utf-8")
            block = _DATA_BLOCK.search(self.html)
            assert block is not None
            self.payload = json.loads(block.group(1))


def export(
    tmp_path: pathlib.Path,
    source: Any = None,
    *,
    root: pathlib.Path | None = None,
    from_id: str | None = None,
    deadline: float | None = None,
    monkeypatch: Any = None,
) -> Ran:
    """Run ``run_export``.  ``source`` is None (no flag), bytes, or ``(opener, cleanup)``."""
    dest = pathlib.Path(tempfile.mkdtemp(dir=tmp_path)).resolve()
    if root is None:
        root = _mixed_outside_git()
    if deadline is not None:
        monkeypatch.setattr(rmod, "READ_DEADLINE_SECONDS", deadline)
    flag: str | None = None
    opener = None
    cleanup: Callable[[], None] = lambda: None  # noqa: E731
    if source is not None:
        flag = "-"
        if isinstance(source, bytes):
            opener, cleanup = feed(source)
        else:
            opener, cleanup = source
    try:
        result, code = nav.run_export(
            root, str(dest), "view.html", from_id, readiness=flag, readiness_stream=opener
        )
    finally:
        cleanup()
    return Ran(result, code, dest)


def stripped(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a payload copy without the two members AC-0013 allows to differ."""
    out = copy.deepcopy(payload)
    out["provenance"].pop("generated_at")
    out["readiness"].pop("reason")
    return out


# --- the failing-input table: every case of AC-0006 to AC-0011, AC-0046 and AC-0047 ----

Source = tuple[Callable[[], int | None], Callable[[], None]]


def _noop() -> None:
    return None


def _none_source() -> Source:
    return (lambda: None), _noop


def _closed_source() -> Source:
    r, w = os.pipe()
    os.close(r)
    os.close(w)
    return (lambda: r), _noop


def _directory_source() -> Source:
    fd = os.open(tempfile.gettempdir(), os.O_RDONLY)
    return (lambda: fd), lambda: os.close(fd)


def _write_only_source() -> Source:
    fd = os.open(os.devnull, os.O_WRONLY)
    return (lambda: fd), lambda: os.close(fd)


def _non_blocking_source() -> Source:
    r, w = os.pipe()
    os.set_blocking(r, False)

    def close() -> None:
        os.close(r)
        os.close(w)

    return (lambda: r), close


def _raising_source() -> Source:
    def opener() -> int:
        raise io.UnsupportedOperation("fileno")

    return opener, _noop


def _terminal_source() -> Source:
    master, slave = os.openpty()
    os.write(master, b"typed text\n")

    def close() -> None:
        os.close(master)
        os.close(slave)

    return (lambda: slave), close


def _held_open_source(sent: bytes) -> Callable[[], Source]:
    def make() -> Source:
        r, w = os.pipe()
        before = set(threading.enumerate())
        if sent:
            os.write(w, sent)

        def close() -> None:
            _release_held_pipe(r, w, before)

        return (lambda: r), close

    return make


class FailingCase:
    def __init__(
        self, name: str, make: Callable[[], Any], reason: str, deadline: float | None = None
    ) -> None:
        self.name, self.make, self.reason, self.deadline = name, make, reason, deadline

    def __repr__(self) -> str:
        return self.name


FAILING: list[FailingCase] = [
    *[
        FailingCase(name, (lambda d=data: d), expected)
        for name, data, expected in CHECK_CASES
        if expected != "checked"
    ],
    FailingCase(
        "lone_surrogate_next_action",
        lambda: mutated(blocked_finding_set("next_action", "\ud800")),
        "wrong_schema",
    ),
    FailingCase("padded_4194305", lambda: padded(4_194_305), "too_large"),
    FailingCase("held_open_no_bytes", _held_open_source(b""), "timed_out", 0.3),
    FailingCase("held_open_100_bytes", _held_open_source(BASE_BYTES[:100]), "timed_out", 0.3),
    FailingCase("opener_none", _none_source, "unreadable"),
    FailingCase("closed_descriptor", _closed_source, "unreadable"),
    FailingCase("directory", _directory_source, "unreadable"),
    FailingCase("write_only", _write_only_source, "unreadable"),
    FailingCase("non_blocking_empty", _non_blocking_source, "unreadable"),
    FailingCase("fileno_raises", _raising_source, "unreadable"),
    FailingCase("terminal", _terminal_source, "empty"),
]
_FAILING_PARAMS = [pytest.param(c, id=c.name) for c in FAILING]


def fail_export(tmp_path: pathlib.Path, case: FailingCase, monkeypatch: Any) -> Ran:
    return export(tmp_path, case.make(), deadline=case.deadline, monkeypatch=monkeypatch)


def hostile_checked_status() -> bytes:
    """A checked input whose not-known next actions are multi-byte text."""
    action = "\u2192 \u00e9\u00e8 " * 40
    return encode(dispatch_json(blocked=[entry(BLOCKED, [finding("custom_code", action)])]))


# --- AC-0001 and AC-0002: the flag value, in a child with a never-written stdin ----------


def _child_main(
    args: list[str], dest: pathlib.Path, stdin_open: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run ``main`` in ``python -I`` with an open pipe on standard input that is never written."""
    proc = subprocess.Popen(
        [sys.executable, "-I", str(_SCRIPT), "export", "--root", str(_MIXED),
         "--destination", str(dest), "--name", "view.html", *args],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        out, err = proc.communicate(timeout=30) if not stdin_open else _wait(proc)
    finally:
        if proc.poll() is None:
            proc.kill()
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def _wait(proc: subprocess.Popen[str]) -> tuple[str, str]:
    """Wait for the child without closing its standard input."""
    out_chunks: list[str] = []
    err_chunks: list[str] = []
    readers = [
        threading.Thread(target=lambda s=stream, c=chunks: c.append(s.read()), daemon=True)
        for stream, chunks in ((proc.stdout, out_chunks), (proc.stderr, err_chunks))
    ]
    for reader in readers:
        reader.start()
    proc.wait(timeout=30)
    for reader in readers:
        reader.join(5)
    return "".join(out_chunks), "".join(err_chunks)


@pytest.mark.parametrize(
    "args",
    [
        ["--readiness", "foo"],
        ["--readiness=-x"],
        ["--readiness", "-1"],
        ["--readiness", "-x y"],
    ],
    ids=["foo", "equals_dash_x", "dash_one", "dash_x_space_y"],
)
def test_a_value_other_than_dash_is_invalid_query_and_reads_nothing(args, tmp_path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    done = _child_main(args, dest)
    assert done.returncode == 1, done.stderr
    assert json.loads(done.stdout)["error"]["code"] == "invalid_query"
    assert list(dest.iterdir()) == []


@pytest.mark.parametrize(
    "args",
    [["--readiness", "-x"], ["--readiness", "--"], ["--readiness"]],
    ids=["dash_x", "double_dash", "bare_trailing"],
)
def test_inputs_the_parser_rejects_exit_two_and_write_nothing(args, tmp_path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    done = _child_main(args, dest)
    assert done.returncode == 2
    assert done.stdout == ""
    assert list(dest.iterdir()) == []


def test_without_the_flag_a_never_written_stdin_is_not_read(tmp_path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    done = _child_main([], dest)
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert result["status"] == "ok"
    assert (dest / "view.html").is_file()


def test_the_closed_standard_input_gives_unreadable(tmp_path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    done = subprocess.run(
        ["sh", "-c", 'exec 0<&-; exec "$0" "$@"', sys.executable, "-I", str(_SCRIPT), "export",
         "--root", str(_MIXED), "--destination", str(dest), "--name", "view.html",
         "--readiness", "-"],
        capture_output=True, text=True, timeout=30,
    )
    assert done.returncode == 0 and done.stderr == ""
    result = json.loads(done.stdout)
    assert result["readiness"] == {"checked": False, "reason": "unreadable"}


def test_an_unloadable_readiness_module_refuses_and_writes_nothing(monkeypatch, tmp_path) -> None:
    """A readiness module that will not load refuses with its own message and writes no file."""

    def _missing() -> Any:
        raise ImportError("readiness module removed")

    monkeypatch.setattr(nav, "_load_readiness_mod", _missing)
    dest = tmp_path / "out"
    dest.mkdir()
    result, code = nav.run_export(_MIXED, str(dest), "v.html", readiness="-",
                                  readiness_stream=lambda: pytest.fail("the stream was opened"))
    assert code == 1
    assert result["error"]["code"] == "resolver_unavailable"
    assert result["error"]["message"] == "readiness module is unavailable"
    assert list(dest.iterdir()) == []


def test_run_export_refuses_a_bad_value_before_anything_else(tmp_path) -> None:
    result, code = nav.run_export(
        tmp_path / "no-such-root", str(tmp_path), "v.html", readiness="foo",
        readiness_stream=lambda: pytest.fail("the stream was opened"),
    )
    assert code == 1 and result["error"]["code"] == "invalid_query"
    assert list(tmp_path.iterdir()) == []


# --- AC-0003, AC-0004 and AC-0005: the result field and the payload member ---------------


def test_without_the_flag_readiness_is_not_requested(tmp_path) -> None:
    ran = export(tmp_path)
    assert ran.payload is not None
    assert list(ran.payload) == _PAYLOAD_KEYS
    assert ran.payload["schema"] == "intent-navigation.view.v1"
    assert ran.payload["readiness"] == {"checked": False, "reason": "not_requested"}
    assert ran.result["readiness"] == {"checked": False, "reason": "not_requested"}
    assert list(ran.result["readiness"]) == ["checked", "reason"]


def test_checked_readiness_gives_a_null_reason_and_the_projected_member(tmp_path) -> None:
    ran = export(tmp_path, encode(dispatch_json()))
    assert ran.payload is not None
    assert list(ran.payload) == _PAYLOAD_KEYS
    assert ran.result["readiness"] == {"checked": True, "reason": None}
    member = ran.payload["readiness"]
    assert list(member) == ["checked", "active", "ready", "blocked", "start"]
    assert member["ready"] == ["spec:bravo-spec"]
    assert member["active"] == ["spec:charlie-spec"]
    assert [b["id"] for b in member["blocked"]] == ["spec:golf-new"]


def test_an_unchecked_reason_is_the_same_in_the_result_and_the_payload(tmp_path) -> None:
    ran = export(tmp_path, b"not json")
    assert ran.payload is not None
    assert ran.payload["readiness"] == {"checked": False, "reason": "not_json"}
    assert ran.result["readiness"] == {"checked": False, "reason": "not_json"}


# --- AC-0013: a failing input never fails the export -------------------------------------


@pytest.mark.parametrize("case", _FAILING_PARAMS)
def test_a_failing_input_exports_ok_and_leaves_the_payload_alone(
    case, tmp_path, pinned, capfd, monkeypatch
) -> None:
    baseline = export(tmp_path)
    capfd.readouterr()
    ran = fail_export(tmp_path, case, monkeypatch)
    assert ran.code == 0 and ran.result["status"] == "ok", ran.result
    assert ran.files == ["view.html"]
    assert capfd.readouterr().err == ""
    assert ran.payload is not None and baseline.payload is not None
    assert ran.payload["readiness"] == {"checked": False, "reason": case.reason}
    assert ran.result["readiness"] == {"checked": False, "reason": case.reason}
    assert stripped(ran.payload) == stripped(baseline.payload)


def test_a_page_that_fails_to_render_with_readiness_still_exports(tmp_path, pinned, monkeypatch) -> None:
    real = view.build_html

    def refuse_checked(payload):
        if payload["readiness"]["checked"]:
            raise RuntimeError("page builder failed")
        return real(payload)

    monkeypatch.setattr(view, "build_html", refuse_checked)
    ran = export(tmp_path, BASE_BYTES)
    assert ran.code == 0 and ran.result["status"] == "ok", ran.result
    assert ran.files == ["view.html"]
    assert ran.payload is not None
    assert ran.payload["readiness"] == {"checked": False, "reason": "wrong_schema"}
    assert ran.result["readiness"] == {"checked": False, "reason": "wrong_schema"}


def test_many_distinct_codes_on_one_record_project_in_one_pass() -> None:
    path = "docs/specs/bravo-spec/spec.md"
    count = 50_000
    findings = [finding(f"c{i}", "x") for i in range(count)]
    obj = dispatch_json(ready=[], active=[], blocked=[entry(path, findings)])
    started = time.monotonic()
    got = rd.member(encode(obj), {path: "spec:bravo-spec"})
    # One pass takes well under a second; a scan of the codes already kept per finding
    # would take minutes at this size.
    assert time.monotonic() - started < 10
    assert [f["code"] for f in got["blocked"][0]["findings"]] == [f"c{i}" for i in range(count)]


def test_the_cached_derivation_equals_a_real_one(tmp_path, pinned, monkeypatch) -> None:
    cached = export(tmp_path, b"")
    monkeypatch.undo()
    real = export(tmp_path, b"")
    assert cached.payload is not None and real.payload is not None
    assert stripped(cached.payload) == stripped(real.payload)


# --- AC-0048 and AC-0050: the size budget -------------------------------------------------


def _no_flag_size(tmp_path: pathlib.Path) -> int:
    ran = export(tmp_path)
    assert ran.html is not None
    return len(ran.html.encode("utf-8"))


def test_a_checked_page_over_the_budget_is_written_with_page_too_big(
    tmp_path, pinned, monkeypatch
) -> None:
    size = _no_flag_size(tmp_path)
    with monkeypatch.context() as roomy:
        roomy.setattr(view, "EXPORT_BUDGET_BYTES", size + 1_000_000)
        assert export(tmp_path, hostile_checked_status()).result["readiness"]["checked"] is True
    monkeypatch.setattr(view, "EXPORT_BUDGET_BYTES", size)
    ran = export(tmp_path, hostile_checked_status())
    assert ran.code == 0 and ran.result["status"] == "ok", ran.result
    assert ran.result["readiness"] == {"checked": False, "reason": "page_too_big"}
    assert ran.payload is not None
    assert ran.payload["readiness"] == {"checked": False, "reason": "page_too_big"}
    assert ran.files == ["view.html"]
    assert ran.result["bytes"] <= size


@pytest.mark.parametrize("case", _FAILING_PARAMS)
def test_every_failing_input_also_exports_ok_at_exactly_the_budget(
    case, tmp_path, pinned, capfd, monkeypatch
) -> None:
    baseline = export(tmp_path)
    assert baseline.html is not None and baseline.payload is not None
    monkeypatch.setattr(view, "EXPORT_BUDGET_BYTES", len(baseline.html.encode("utf-8")))
    capfd.readouterr()
    ran = fail_export(tmp_path, case, monkeypatch)
    assert ran.code == 0 and ran.result["status"] == "ok", ran.result
    assert ran.files == ["view.html"]
    assert capfd.readouterr().err == ""
    assert ran.payload is not None
    assert ran.payload["readiness"] == {"checked": False, "reason": case.reason}
    assert stripped(ran.payload) == stripped(baseline.payload)


def _assert_refused_for_size(ran: Ran, budget: int, size: int) -> None:
    assert ran.code == 1 and ran.result["status"] == "error", ran.result
    error = ran.result["error"]
    assert error["code"] == "export_too_large"
    assert error["limits"] == {"budget_bytes": budget, "bounded_route": "--from"}
    assert error["observed"] == {"bytes": size}
    assert ran.files == []


def test_a_baseline_one_byte_over_the_budget_refuses_a_checked_input(
    tmp_path, pinned, monkeypatch
) -> None:
    size = _no_flag_size(tmp_path)
    monkeypatch.setattr(view, "EXPORT_BUDGET_BYTES", size - 1)
    _assert_refused_for_size(export(tmp_path, hostile_checked_status()), size - 1, size)


@pytest.mark.parametrize("case", _FAILING_PARAMS)
def test_a_baseline_one_byte_over_the_budget_refuses_every_failing_input(
    case, tmp_path, pinned, monkeypatch
) -> None:
    size = _no_flag_size(tmp_path)
    monkeypatch.setattr(view, "EXPORT_BUDGET_BYTES", size - 1)
    _assert_refused_for_size(fail_export(tmp_path, case, monkeypatch), size - 1, size)


# --- AC-0015, AC-0016 and AC-0034: what reaches the page ---------------------------------


class _VisibleText(HTMLParser):
    """Collect the text nodes of a page with its script and style elements removed."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.text.append(data)


def visible_text(html: str) -> str:
    parser = _VisibleText()
    parser.feed(html)
    return "\n".join(parser.text)


def test_entries_naming_nothing_loaded_are_dropped_from_data_and_text(tmp_path) -> None:
    obj = dispatch_json(
        ready=[entry(p) for p in DROPPED] + [entry(READY)],
        active=[],
        blocked=[entry(f"{p}#b", [finding()]) for p in DROPPED]
        + [entry(BLOCKED, [finding()])],
    )
    ran = export(tmp_path, encode(obj))
    assert ran.payload is not None and ran.html is not None
    member = ran.payload["readiness"]
    assert member["checked"] is True
    assert member["ready"] == ["spec:bravo-spec"]
    assert [b["id"] for b in member["blocked"]] == ["spec:golf-new"]
    # several items are ready, so work-loop asks and nothing is marked
    assert member["start"] == {"rule": "ask", "id": None, "held": False, "active_count": 0}
    block = json.dumps(member)
    text = visible_text(ran.html)
    for path in DROPPED:
        assert path not in block, path
        assert path not in text, path
    # the static text does not depend on the readiness input at all
    assert visible_text(export(tmp_path).html or "") == text


def test_a_loaded_path_outside_the_from_scope_is_dropped(tmp_path) -> None:
    ran = export(tmp_path, encode(dispatch_json(active=[], blocked=[])), from_id="intent:india-none")
    assert ran.payload is not None and ran.html is not None
    member = ran.payload["readiness"]
    assert member["checked"] is True
    assert member["ready"] == [] and member["active"] == [] and member["blocked"] == []
    assert member["start"] == {"rule": "start", "id": None, "held": False, "active_count": 0}
    assert "docs/specs/bravo-spec/spec.md" not in json.dumps(member)


def test_marker_strings_never_reach_the_html(tmp_path) -> None:
    """AC-0008: slug, status, finding paths, and the code and next action the page drops."""
    blocked = [
        entry(BLOCKED, [finding(path="marker-blocked-finding-path")],
              slug="marker-blocked-slug", status="marker-blocked-status"),
        entry("docs/specs/absent-spec/spec.md",
              [finding("marker_unloaded_code", "marker-unloaded-next-action",
                       path="marker-unloaded-finding-path")],
              slug="marker-unloaded-slug", status="marker-unloaded-status"),
    ]
    obj = dispatch_json(
        ready=[entry(READY, slug="marker-ready-slug", status="marker-ready-status")],
        active=[entry(ACTIVE, slug="marker-active-slug", status="marker-active-status")],
        blocked=blocked,
        findings=[finding("marker_top_code", "marker-top-next-action", path="marker-top-path")],
    )
    ran = export(tmp_path, encode(obj))
    assert ran.html is not None and ran.payload is not None
    assert ran.payload["readiness"]["checked"] is True
    assert "marker-" not in ran.html and "marker_" not in ran.html


def test_a_repeated_blocked_path_reaches_the_payload_once(tmp_path) -> None:
    obj = dispatch_json(
        ready=[], active=[],
        blocked=[
            entry(BLOCKED, [finding("missing_plan", "p"), finding("a_code", "q")]),
            entry(BLOCKED, [finding("a_code", "q"), finding("b_code", "r")]),
        ],
    )
    ran = export(tmp_path, encode(obj))
    assert ran.payload is not None
    blocked = ran.payload["readiness"]["blocked"]
    assert [b["id"] for b in blocked] == ["spec:golf-new"]
    assert [f["code"] for f in blocked[0]["findings"]] == ["missing_plan", "a_code", "b_code"]


HOSTILE_ACTIONS = [
    "</script><script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    '"><svg onload=alert(1)>',
    "line\u2028separator\u2029paragraph",
    "bidi \u202e override \u200f mark",
]


def test_hostile_next_actions_stay_inside_the_data_block(tmp_path) -> None:
    findings = [finding(f"hostile_{i}", action) for i, action in enumerate(HOSTILE_ACTIONS)]
    data = encode(dispatch_json(blocked=[entry(BLOCKED, findings)]))
    ran = export(tmp_path, data)
    assert ran.html is not None and ran.payload is not None
    outside = outside_data_block(ran.html)
    for needle in HOSTILE_NEEDLES:
        assert needle not in outside, needle
    checked = rd.check(data)
    assert not isinstance(checked, str)
    path_to_id = {n["path"]: n["id"] for n in ran.payload["nodes"]}
    expected = rd.project(checked, path_to_id)
    assert ran.payload["readiness"] == expected
    got = ran.payload["readiness"]["blocked"][0]["findings"]
    assert [f["next_action"] for f in got] == HOSTILE_ACTIONS
    assert all(f["known"] is False for f in got)


# --- AC-0019: the payload does not depend on workspace.toml ------------------------------

_HOSTILE_WORKSPACE = (
    pathlib.Path(__file__).resolve().parent / "fixtures" / "hostile_workspace" / "workspace.toml"
)
_HOSTILE_TOML = _HOSTILE_WORKSPACE.read_text(encoding="utf-8")


def test_workspace_toml_states_give_one_payload(tmp_path) -> None:
    root = tmp_path / "root"
    shutil.copytree(_MIXED, root)
    data = encode(dispatch_json())
    toml = root / "workspace.toml"
    payloads = {}
    payloads["absent"] = export(tmp_path, data, root=root).payload
    toml.write_text(_HOSTILE_TOML, encoding="utf-8")
    payloads["hostile"] = export(tmp_path, data, root=root).payload
    toml.chmod(0)
    try:
        payloads["unreadable"] = export(tmp_path, data, root=root).payload
    finally:
        toml.chmod(0o600)
    toml.unlink()
    toml.mkdir()
    payloads["directory"] = export(tmp_path, data, root=root).payload
    assert all(p is not None for p in payloads.values())
    assert payloads["absent"]["readiness"]["checked"] is True
    base = copy.deepcopy(payloads["absent"])
    base["provenance"].pop("generated_at")
    for state, payload in payloads.items():
        got = copy.deepcopy(payload)
        got["provenance"].pop("generated_at")
        assert got == base, state


# --- AC-0020: no extra process and no extra file --------------------------------------------

_AUDIT_CHILD = r"""
import importlib.util, json, os, re, sys
events = []
WATCH = {"subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn",
         "os.fork", "os.forkpty", "os.startfile"}
def hook(event, args):
    if event == "open":
        events.append(["open", os.fsdecode(args[0]) if not isinstance(args[0], int) else "fd"])
    elif event in WATCH:
        events.append([event, repr(args[:2])])
sys.addaudithook(hook)
sys.dont_write_bytecode = True  # a pyc written by one run would change what the next opens
script, root, dest, flag, status_bytes = sys.argv[1:6]
spec = importlib.util.spec_from_file_location("audited_nav", script)
mod = importlib.util.module_from_spec(spec)
sys.modules["audited_nav"] = mod
spec.loader.exec_module(mod)
stream = None
if flag == "-":
    r, w = os.pipe()
    os.write(w, status_bytes.encode("utf-8"))
    os.close(w)
    stream = lambda: r
result, code = mod.run_export(root, dest, "view.html", None,
                              readiness=None if flag == "none" else "-",
                              readiness_stream=stream)
assert code == 0, result
print(json.dumps({"events": events, "dest": os.path.realpath(dest)}))
"""


def _audited(tmp_path: pathlib.Path, label: str, flag: str) -> set[tuple[str, str]]:
    dest = tmp_path / label
    dest.mkdir()
    done = subprocess.run(
        [sys.executable, "-I", "-c", _AUDIT_CHILD, str(_SCRIPT), str(_MIXED), str(dest), flag,
         encode(dispatch_json()).decode("utf-8")],
        capture_output=True, text=True, timeout=60,
    )
    assert done.returncode == 0, done.stderr
    recorded = json.loads(done.stdout)
    own = recorded["dest"]
    tmp_name = re.compile(r"\.intent-graph-[0-9a-f]{16}\.tmp")
    normalised = set()
    for event, value in recorded["events"]:
        value = tmp_name.sub("<TMP>", value.replace(own, "<DEST>"))
        normalised.add((event, value))
    return normalised


def test_the_flag_starts_no_process_and_opens_no_file_the_plain_export_does_not(tmp_path) -> None:
    plain = _audited(tmp_path, "plain", "none")
    piped = _audited(tmp_path, "piped", "-")
    opens = {v for e, v in plain if e == "open"}
    # Python opens a module's cached bytecode when it has one and its source when it does not.
    assert any("intent_readiness." in v for v in opens), "the module is always loaded"
    assert any("intent_view." in v for v in opens)
    assert "<DEST>" in opens and "<TMP>" in opens, "both normalisations applied"
    assert piped == plain


# --- AC-0034: the help text --------------------------------------------------------------


def test_export_help_gives_the_dispatch_command_for_readiness(monkeypatch, capsys) -> None:
    monkeypatch.setenv("COLUMNS", "400")
    assert nav.main(["export", "--help"]) == 0
    text = " ".join(capsys.readouterr().out.split())
    assert "Pass - to read the output of work-loop's dispatch.py --root from standard input." in text
    assert "workspace-status" not in text


# --- AC-0011: the hand-built hostile input -----------------------------------------------

_HOSTILE_ALL = " ".join(HOSTILE_ACTIONS)


def test_a_hand_built_hostile_input_exports_safely(tmp_path) -> None:
    unloaded = "docs/specs/absent-spec/spec.md " + _HOSTILE_ALL
    obj = dispatch_json(
        ready=[entry(READY, slug=_HOSTILE_ALL, status=_HOSTILE_ALL)],
        active=[entry(ACTIVE, slug=_HOSTILE_ALL, status=_HOSTILE_ALL)],
        blocked=[
            entry(BLOCKED, [finding("custom_code", _HOSTILE_ALL, path=_HOSTILE_ALL)],
                  slug=_HOSTILE_ALL, status=_HOSTILE_ALL),
            entry(unloaded, [finding("custom_code", _HOSTILE_ALL, path=_HOSTILE_ALL)],
                  slug=_HOSTILE_ALL, status=_HOSTILE_ALL),
        ],
        findings=[finding("custom_top", _HOSTILE_ALL, path=_HOSTILE_ALL)],
    )
    ran = export(tmp_path, encode(obj))
    assert ran.code == 0 and ran.result["status"] == "ok", ran.result
    assert ran.result["readiness"] == {"checked": True, "reason": None}
    assert ran.html is not None and ran.payload is not None
    assert [b["id"] for b in ran.payload["readiness"]["blocked"]] == ["spec:golf-new"]
    outside = outside_data_block(ran.html)
    for needle in HOSTILE_NEEDLES:
        assert needle not in outside, needle
    assert unloaded not in ran.html


# --- AC-0010 and AC-0011: the real dispatch.py output ------------------------------------

replay = _load(_REPLAY, "core_navigate_intents_readiness_replay_t")
_COUNTER = iter(range(10**9))


@pytest.fixture(scope="module")
def dispatch_mod(tmp_path_factory) -> Any:
    """``dispatch.py`` loaded from a planted copy of its skills, under a unique name."""
    skills = replay.TD._copy_skills(tmp_path_factory.mktemp("readiness-dispatch"))
    return replay.TD._load(skills / "work-loop" / "scripts" / "dispatch.py")


def dispatch_stdout(dispatch_mod: Any, root: pathlib.Path) -> bytes:
    """The bytes ``dispatch.py --root <root>`` prints, captured in process."""
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        code = dispatch_mod.main(["--root", str(root)])
    assert code == 0
    return captured.getvalue().encode("utf-8")


def loaded_ids(root: pathlib.Path) -> dict[str, str]:
    specs = root / "docs" / "specs"
    if not specs.is_dir():
        return {}
    return {
        f"docs/specs/{c.name}/spec.md": f"spec:{c.name}"
        for c in sorted(specs.iterdir())
        if os.path.lexists(c / "spec.md")
    }


def _is_argless_refusal(output: dict[str, Any]) -> bool:
    decision = output["decision"]
    return decision["action"] == "refuse" and not (
        output["ready"] or output["active"] or output["blocked"]
    )


def test_the_planted_invalid_toml_tree_gives_an_argless_refusal(dispatch_mod, tmp_path) -> None:
    root = tmp_path / "invalid-toml"
    (root / "docs" / "specs").mkdir(parents=True)
    (root / "workspace.toml").write_text("this is = = not toml\n", encoding="utf-8")
    data = dispatch_stdout(dispatch_mod, root)
    output = json.loads(data)
    assert output["decision"]["action"] == "refuse"
    assert [f["code"] for f in output["decision"]["findings"]] == ["invalid_workspace"]
    assert rd.member(data, {}) == {"checked": False, "reason": "bad_workspace"}


def test_every_replay_case_tree_and_the_planted_refusal_give_a_checked_member_or_bad_workspace(
    dispatch_mod, tmp_path, capsys
) -> None:
    reasons: collections.Counter[str] = collections.Counter()
    actions: collections.Counter[str] = collections.Counter()
    bad: list[str] = []
    trees: list[tuple[str, pathlib.Path]] = []
    for case in replay.CASES:
        if replay.IS_ROOT and case.name in replay.SKIP_AS_ROOT:
            continue
        root = tmp_path / case.name
        replay._plant(case, root, "header")
        trees.append((case.name, root))
    planted = tmp_path / "planted-invalid-toml"
    (planted / "docs" / "specs").mkdir(parents=True)
    (planted / "workspace.toml").write_text("[unterminated\n", encoding="utf-8")
    trees.append(("planted-invalid-toml", planted))
    try:
        for name, root in trees:
            data = dispatch_stdout(dispatch_mod, root)
            output = json.loads(data)
            path_to_id = loaded_ids(root)
            got = rd.member(data, path_to_id)
            actions[output["decision"]["action"]] += 1
            if _is_argless_refusal(output):
                assert got == {"checked": False, "reason": "bad_workspace"}, name
                reasons["bad_workspace"] += 1
                bad.append(name)
                continue
            assert got["checked"] is True, (name, got)
            reasons["checked"] += 1
            assert got["active"] == [path_to_id[i["path"]] for i in output["active"]
                                     if i["path"] in path_to_id], name
            assert got["ready"] == [path_to_id[i["path"]] for i in output["ready"]
                                    if i["path"] in path_to_id], name
            unique = dict.fromkeys(i["path"] for i in output["blocked"] if i["path"] in path_to_id)
            assert [b["id"] for b in got["blocked"]] == [path_to_id[p] for p in unique], name
    finally:
        for _, root in trees:
            for path in root.rglob("*"):
                if path.is_file() and not path.is_symlink():
                    path.chmod(0o644)
    assert bad == ["planted-invalid-toml"], bad
    with capsys.disabled():
        print(f"\nreadiness corpus: {len(trees)} trees")
        print("  per reason:", dict(sorted(reasons.items())))
        print("  per decision action:", dict(sorted(actions.items())))


def test_dispatch_over_a_hostile_workspace_toml_exports_safely(dispatch_mod, tmp_path, capsys) -> None:
    root = tmp_path / "root"
    shutil.copytree(_MIXED, root)
    shutil.copy(_HOSTILE_WORKSPACE, root / "workspace.toml")
    data = dispatch_stdout(dispatch_mod, root)
    output = data.decode("utf-8")
    present = [
        needle for needle in HOSTILE_NEEDLES
        if needle in output or json.dumps(needle)[1:-1] in output
    ]
    with capsys.disabled():
        print(f"\nhostile fixture: dispatch.py output holds {len(present)} of "
              f"{len(HOSTILE_NEEDLES)} hostile strings")
    ran = export(tmp_path, data, root=root)
    assert ran.result["status"] == "ok"
    assert ran.result["readiness"] == {"checked": True, "reason": None}
    assert ran.html is not None
    outside = outside_data_block(ran.html)
    for needle in HOSTILE_NEEDLES:
        assert needle not in outside, needle
