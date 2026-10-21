"""Construction tests for the readiness bridge.

``intent_readiness.py`` reads untrusted ``workspace-status`` bytes.  The first
half drives its ``read``, ``check``, ``start`` and ``project`` with named byte
streams and read descriptors.  The second half drives ``export --readiness -``
through ``run_export`` and child interpreters.  The oracle for each case is the
reason or value the spec names; no expected reason is read from the module.
"""

from __future__ import annotations

import ast
import atexit
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


def finding(code: str = "unsatisfied_dependency", action: str = DEP_ACTION, **extra: Any):
    return {"code": code, "dispatchable": False, "next_action": action, **extra}


def entry(path: str, dispatchable: bool = True, findings: list | None = None, **extra: Any):
    return {"path": path, "dispatchable": dispatchable, "findings": findings or [], **extra}


def status(ready=None, active=None, blocked=None, findings=None) -> dict[str, Any]:
    """Return a status object holding one ready, one active and one blocked entry by default."""
    return {
        "schema_version": 1,
        "mode": "status",
        "workspace_present": True,
        "workspace_root": ".",
        "canonical": {
            "performed": True,
            "bounded": True,
            "findings": [] if findings is None else findings,
            "ready": [entry(READY)] if ready is None else ready,
            "active": [entry(ACTIVE)] if active is None else active,
            "blocked": ([entry(BLOCKED, False, [finding()])] if blocked is None else blocked),
        },
    }


def encode(obj: Any) -> bytes:
    return json.dumps(obj).encode("utf-8")


BASE = {
    "schema_version": 1,
    "mode": "status",
    "workspace_present": True,
    "workspace_root": ".",
    "canonical": {
        "performed": True,
        "bounded": True,
        "findings": [],
        "ready": [],
        "active": [],
        "blocked": [],
    },
}
BASE_BYTES = encode(BASE)


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


# --- AC-0006 to AC-0011: the table of named byte streams ------------------------------


def mutated(mutate: Callable[[dict], None], obj: dict | None = None) -> bytes:
    data = copy.deepcopy(
        obj if obj is not None else status(blocked=[entry(BLOCKED, False, [finding()])])
    )
    mutate(data)
    return encode(data)


def canonical_set(key: str, value: Any) -> Callable[[dict], None]:
    def apply(data: dict) -> None:
        if value is _ABSENT:
            del data["canonical"][key]
        else:
            data["canonical"][key] = value

    return apply


def top_set(key: str, value: Any) -> Callable[[dict], None]:
    def apply(data: dict) -> None:
        if value is _ABSENT:
            del data[key]
        else:
            data[key] = value

    return apply


def blocked_finding_set(key: str, value: Any) -> Callable[[dict], None]:
    def apply(data: dict) -> None:
        item = data["canonical"]["blocked"][0]["findings"][0]
        if value is _ABSENT:
            del item[key]
        else:
            item[key] = value

    return apply


def blocked_entry_set(key: str, value: Any) -> Callable[[dict], None]:
    def apply(data: dict) -> None:
        item = data["canonical"]["blocked"][0]
        if value is _ABSENT:
            del item[key]
        else:
            item[key] = value

    return apply


def top_finding_set(key: str, value: Any) -> Callable[[dict], None]:
    def apply(data: dict) -> None:
        data["canonical"]["findings"] = [finding()]
        if value is _ABSENT:
            del data["canonical"]["findings"][0][key]
        else:
            data["canonical"]["findings"][0][key] = value

    return apply


_ABSENT = object()


def with_extra_member(raw: str) -> bytes:
    """Return the base status with ``"x": <raw>`` appended as a raw JSON text member."""
    text = BASE_BYTES.decode("utf-8")
    return (text[:-1] + ', "x": ' + raw + "}").encode("utf-8")


NESTED = "[" * 100_000 + "]" * 100_000

CHECK_CASES: list[tuple[str, bytes, str]] = [
    # AC-0007
    ("zero_bytes", b"", "empty"),
    ("only_whitespace", b" \t\r\n \n", "empty"),
    # AC-0008
    ("invalid_utf8", b"\xff\xfe" + BASE_BYTES, "not_json"),
    ("byte_order_mark", b"\xef\xbb\xbf" + BASE_BYTES, "not_json"),
    ("array_top_level", b"[1, 2]", "not_json"),
    ("string_top_level", b'"status"', "not_json"),
    ("number_top_level", b"1", "not_json"),
    ("null_top_level", b"null", "not_json"),
    ("truncated_object", BASE_BYTES[:-5], "not_json"),
    (
        "repeated_name_top",
        BASE_BYTES[:-1] + b', "mode": "status"}',
        "not_json",
    ),
    (
        "repeated_name_nested",
        BASE_BYTES.replace(b'"performed": true', b'"performed": true, "performed": true'),
        "not_json",
    ),
    ("nan", with_extra_member("NaN"), "not_json"),
    ("infinity", with_extra_member("Infinity"), "not_json"),
    ("negative_infinity", with_extra_member("-Infinity"), "not_json"),
    ("second_value", BASE_BYTES + b" " + BASE_BYTES, "not_json"),
    ("second_value_adjacent", BASE_BYTES + b"{}", "not_json"),
    ("nested_100000_deep", with_extra_member(NESTED), "not_json"),
    # AC-0012: a repeated name wins over a wrong schema_version
    (
        "repeated_name_and_schema_version_2",
        b'{"schema_version": 2, "schema_version": 2, "mode": "status"}',
        "not_json",
    ),
    # AC-0009
    (
        "workspace_absent_output",
        b'{"mode": "status", "schema_version": 1, "workspace_present": false,'
        b' "workspace_root": "."}',
        "no_workspace",
    ),
    ("workspace_present_false_only", b'{"workspace_present": false}', "no_workspace"),
    (
        "workspace_present_false_error_mode",
        b'{"schema_version": 2, "mode": "error", "workspace_present": false}',
        "no_workspace",
    ),
    # AC-0010
    ("workspace_present_absent", mutated(top_set("workspace_present", _ABSENT)), "wrong_schema"),
    ("workspace_present_string", mutated(top_set("workspace_present", "true")), "wrong_schema"),
    ("workspace_present_null", mutated(top_set("workspace_present", None)), "wrong_schema"),
    ("workspace_present_one", mutated(top_set("workspace_present", 1)), "wrong_schema"),
    ("schema_version_true", mutated(top_set("schema_version", True)), "wrong_schema"),
    ("schema_version_float", mutated(top_set("schema_version", 1.0)), "wrong_schema"),
    ("schema_version_string", mutated(top_set("schema_version", "1")), "wrong_schema"),
    ("schema_version_2", mutated(top_set("schema_version", 2)), "wrong_schema"),
    ("schema_version_absent", mutated(top_set("schema_version", _ABSENT)), "wrong_schema"),
    ("mode_reconcile", mutated(top_set("mode", "reconcile")), "wrong_schema"),
    ("mode_explain", mutated(top_set("mode", "explain")), "wrong_schema"),
    ("mode_error", mutated(top_set("mode", "error")), "wrong_schema"),
    ("mode_absent", mutated(top_set("mode", _ABSENT)), "wrong_schema"),
    ("workspace_root_other", mutated(top_set("workspace_root", "/repo")), "wrong_schema"),
    ("workspace_root_absent", mutated(top_set("workspace_root", _ABSENT)), "wrong_schema"),
    ("canonical_absent", mutated(top_set("canonical", _ABSENT)), "wrong_schema"),
    ("canonical_list", mutated(top_set("canonical", [])), "wrong_schema"),
    ("performed_false", mutated(canonical_set("performed", False)), "wrong_schema"),
    ("performed_absent", mutated(canonical_set("performed", _ABSENT)), "wrong_schema"),
    ("performed_one", mutated(canonical_set("performed", 1)), "wrong_schema"),
    *[
        (f"{key}_{label}", mutated(canonical_set(key, value)), "wrong_schema")
        for key in ("ready", "active", "blocked", "findings")
        for label, value in (("absent", _ABSENT), ("object", {}), ("null", None))
    ],
    ("entry_not_object", mutated(canonical_set("ready", ["x"])), "wrong_schema"),
    ("entry_path_absent", mutated(blocked_entry_set("path", _ABSENT)), "wrong_schema"),
    ("entry_path_number", mutated(blocked_entry_set("path", 7)), "wrong_schema"),
    (
        "entry_dispatchable_absent",
        mutated(blocked_entry_set("dispatchable", _ABSENT)),
        "wrong_schema",
    ),
    (
        "entry_dispatchable_string",
        mutated(blocked_entry_set("dispatchable", "false")),
        "wrong_schema",
    ),
    ("entry_dispatchable_zero", mutated(blocked_entry_set("dispatchable", 0)), "wrong_schema"),
    ("entry_findings_absent", mutated(blocked_entry_set("findings", _ABSENT)), "wrong_schema"),
    ("entry_findings_object", mutated(blocked_entry_set("findings", {})), "wrong_schema"),
    ("finding_not_object", mutated(blocked_entry_set("findings", ["x"])), "wrong_schema"),
    ("top_finding_not_object", mutated(canonical_set("findings", [3])), "wrong_schema"),
    ("finding_code_absent", mutated(blocked_finding_set("code", _ABSENT)), "wrong_schema"),
    ("finding_code_number", mutated(blocked_finding_set("code", 3)), "wrong_schema"),
    ("finding_code_empty", mutated(blocked_finding_set("code", "")), "wrong_schema"),
    ("finding_code_uppercase_start", mutated(blocked_finding_set("code", "Bad")), "wrong_schema"),
    ("finding_code_digit_start", mutated(blocked_finding_set("code", "1bad")), "wrong_schema"),
    (
        "finding_code_65_chars",
        mutated(blocked_finding_set("code", "a" * 65)),
        "wrong_schema",
    ),
    (
        "finding_code_plus_space",
        mutated(blocked_finding_set("code", "missing_plan ")),
        "wrong_schema",
    ),
    (
        "finding_code_plus_dash",
        mutated(blocked_finding_set("code", "missing_plan-")),
        "wrong_schema",
    ),
    (
        "finding_code_plus_uppercase",
        mutated(blocked_finding_set("code", "missing_planX")),
        "wrong_schema",
    ),
    (
        "finding_code_plus_non_ascii",
        mutated(blocked_finding_set("code", "missing_plan\u00e9")),
        "wrong_schema",
    ),
    (
        "finding_code_plus_line_feed",
        mutated(blocked_finding_set("code", "missing_plan\n")),
        "wrong_schema",
    ),
    (
        "top_finding_code_plus_line_feed",
        mutated(top_finding_set("code", "missing_plan\n")),
        "wrong_schema",
    ),
    (
        "finding_dispatchable_absent",
        mutated(blocked_finding_set("dispatchable", _ABSENT)),
        "wrong_schema",
    ),
    (
        "finding_dispatchable_string",
        mutated(blocked_finding_set("dispatchable", "no")),
        "wrong_schema",
    ),
    (
        "top_finding_dispatchable_null",
        mutated(top_finding_set("dispatchable", None)),
        "wrong_schema",
    ),
    ("next_action_absent", mutated(blocked_finding_set("next_action", _ABSENT)), "wrong_schema"),
    ("next_action_number", mutated(blocked_finding_set("next_action", 1)), "wrong_schema"),
    ("next_action_501", mutated(blocked_finding_set("next_action", "x" * 501)), "wrong_schema"),
    (
        "next_action_lone_high_surrogate",
        mutated(blocked_finding_set("next_action", "a\ud800b")),
        "wrong_schema",
    ),
    (
        "next_action_lone_low_surrogate",
        mutated(blocked_finding_set("next_action", "\udfff")),
        "wrong_schema",
    ),
    (
        "top_next_action_absent",
        mutated(top_finding_set("next_action", _ABSENT)),
        "wrong_schema",
    ),
    (
        "ready_item_not_ready_has_finding",
        mutated(canonical_set("ready", [entry(READY, True, [finding()])])),
        "wrong_schema",
    ),
    (
        "ready_item_not_dispatchable",
        mutated(canonical_set("ready", [entry(READY, False)])),
        "wrong_schema",
    ),
    (
        "active_item_has_finding",
        mutated(canonical_set("active", [entry(ACTIVE, True, [finding()])])),
        "wrong_schema",
    ),
    (
        "blocked_item_without_finding",
        mutated(canonical_set("blocked", [entry(BLOCKED, False)])),
        "wrong_schema",
    ),
    (
        "blocked_item_dispatchable",
        mutated(canonical_set("blocked", [entry(BLOCKED, True, [finding()])])),
        "wrong_schema",
    ),
    (
        "path_in_ready_and_active",
        mutated(canonical_set("active", [entry(READY)])),
        "wrong_schema",
    ),
    (
        "path_in_ready_and_blocked",
        mutated(canonical_set("blocked", [entry(READY, False, [finding()])])),
        "wrong_schema",
    ),
    (
        "path_in_active_and_blocked",
        mutated(canonical_set("blocked", [entry(ACTIVE, False, [finding()])])),
        "wrong_schema",
    ),
    # AC-0011: the three workspace failure codes, as workspace-status prints them
    *[
        (
            f"workspace_failure_{code}",
            mutated(
                canonical_set(
                    "blocked",
                    [
                        entry(
                            "workspace.toml",
                            False,
                            [finding(code, "Fix it.", path="workspace.toml")],
                        )
                    ],
                )
            ),
            "bad_workspace",
        )
        for code in ("invalid_workspace", "configuration_mismatch", "unsafe_path")
    ],
    (
        "workspace_failure_top_level_only",
        mutated(canonical_set("findings", [finding("unsafe_path", "Replace it.")])),
        "bad_workspace",
    ),
    # a lone failure code beats nothing else: wrong schema is checked first (AC-0012)
    (
        "wrong_schema_beats_bad_workspace",
        mutated(
            lambda d: (
                d.update(schema_version=2),
                d["canonical"].update(findings=[finding("unsafe_path", "Replace it.")]),
            )
        ),
        "wrong_schema",
    ),
    # accepted inputs
    ("base_status", BASE_BYTES, "checked"),
    ("populated_status", encode(status()), "checked"),
    ("leading_and_trailing_whitespace", b" \r\n" + BASE_BYTES + b"\n\t ", "checked"),
    (
        "extra_members_ignored",
        encode({**BASE, "scan": {"x": 1}, "locator": {"kind": "path"}}),
        "checked",
    ),
    ("next_action_500", mutated(blocked_finding_set("next_action", "x" * 500)), "checked"),
    ("finding_code_64_chars", mutated(blocked_finding_set("code", "a" * 64)), "checked"),
    (
        "lawful_repeat_in_blocked",
        mutated(
            canonical_set(
                "blocked",
                [entry(BLOCKED, False, [finding()]), entry(BLOCKED, False, [finding()])],
            )
        ),
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


def test_surrogate_pair_next_action_is_not_a_lone_surrogate() -> None:
    data = mutated(blocked_finding_set("next_action", "\U0001f600"))
    assert isinstance(rd.check(data), tuple)


def test_check_never_raises_on_hostile_json_shapes() -> None:
    for raw in (b"{}", b"[]", b'{"canonical": 1}', b'{"workspace_present": true}', b"0"):
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


# --- AC-0021 and AC-0049: the argless work-loop mark ----------------------------------


def checked_of(obj: dict) -> Any:
    checked = rd.check(encode(obj))
    assert not isinstance(checked, str), checked
    return checked


def test_start_is_decided_before_an_unloaded_first_ready_is_dropped() -> None:
    obj = status(
        ready=[entry("docs/specs/absent-spec/spec.md"), entry(READY)], active=[], blocked=[]
    )
    checked = checked_of(obj)
    projection = rd.project(checked, PATH_TO_ID)
    assert projection["start"] == {"rule": "start", "id": None, "held": False, "active_count": 0}
    assert projection["ready"] == ["spec:bravo-spec"]


def test_one_active_entry_resumes() -> None:
    checked = checked_of(status(ready=[entry(READY)], active=[entry(ACTIVE)], blocked=[]))
    assert rd.start(checked, PATH_TO_ID) == {
        "rule": "resume",
        "id": "spec:charlie-spec",
        "held": False,
        "active_count": 1,
    }


def test_one_active_entry_outside_the_export_resumes_nothing_marked() -> None:
    checked = checked_of(status(ready=[entry(READY)], active=[entry("elsewhere.md")], blocked=[]))
    assert rd.start(checked, PATH_TO_ID) == {
        "rule": "resume",
        "id": None,
        "held": False,
        "active_count": 1,
    }


def test_two_active_entries_ask_even_when_one_path_is_unloaded() -> None:
    checked = checked_of(
        status(ready=[entry(READY)], active=[entry(ACTIVE), entry("elsewhere.md")], blocked=[])
    )
    assert rd.start(checked, PATH_TO_ID) == {
        "rule": "ask",
        "id": None,
        "held": False,
        "active_count": 2,
    }
    assert rd.project(checked, PATH_TO_ID)["active"] == ["spec:charlie-spec"]


def test_first_ready_entry_starts() -> None:
    checked = checked_of(status(ready=[entry(READY), entry(BLOCKED)], active=[], blocked=[]))
    assert rd.start(checked, PATH_TO_ID) == {
        "rule": "start",
        "id": "spec:bravo-spec",
        "held": False,
        "active_count": 0,
    }


def test_nothing_ready_or_active_is_none() -> None:
    checked = checked_of(status(ready=[], active=[]))
    assert rd.start(checked, PATH_TO_ID) == {
        "rule": "none",
        "id": None,
        "held": False,
        "active_count": 0,
    }


def test_a_top_level_finding_about_the_ready_path_holds_the_mark() -> None:
    obj = status(
        ready=[entry(READY)],
        active=[],
        blocked=[],
        findings=[finding("unsatisfied_dependency", DEP_ACTION, path=READY)],
    )
    projection = rd.project(checked_of(obj), PATH_TO_ID)
    assert projection["start"] == {"rule": "start", "id": None, "held": True, "active_count": 0}
    assert projection["ready"] == ["spec:bravo-spec"]


def test_a_finding_in_another_entrys_findings_holds_the_mark() -> None:
    obj = status(
        ready=[entry(READY)],
        active=[],
        blocked=[entry(BLOCKED, False, [finding(path=READY)])],
    )
    assert rd.start(checked_of(obj), PATH_TO_ID) == {
        "rule": "start",
        "id": None,
        "held": True,
        "active_count": 0,
    }


def test_a_finding_about_the_active_path_holds_a_resume() -> None:
    obj = status(
        ready=[],
        active=[entry(ACTIVE)],
        blocked=[entry(BLOCKED, False, [finding(path=ACTIVE)])],
    )
    start = rd.start(checked_of(obj), PATH_TO_ID)
    assert (start["rule"], start["id"], start["held"]) == ("resume", None, True)


def test_a_finding_about_another_path_does_not_hold_the_mark() -> None:
    obj = status(ready=[entry(READY)], active=[], blocked=[], findings=[finding(path=ACTIVE)])
    start = rd.start(checked_of(obj), PATH_TO_ID)
    assert (start["rule"], start["id"], start["held"]) == ("start", "spec:bravo-spec", False)


def test_ask_and_none_are_never_held() -> None:
    obj = status(
        ready=[],
        active=[entry(ACTIVE), entry(READY)],
        blocked=[],
        findings=[finding(path=ACTIVE)],
    )
    start = rd.start(checked_of(obj), PATH_TO_ID)
    assert (start["rule"], start["id"], start["held"]) == ("ask", None, False)


# --- AC-0014, AC-0017, AC-0018: the projection ----------------------------------------


def test_projection_has_exactly_the_allowlisted_members() -> None:
    obj = status(
        ready=[entry(READY, slug="s", locator={"value": "/home/u/marker"})],
        active=[entry(ACTIVE, refresh={"available": False})],
        blocked=[entry(BLOCKED, False, [finding(path="marker-path", detail="marker")])],
        findings=[finding(path="marker")],
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
    assert set(projection["start"]) == {"rule", "id", "held", "active_count"}
    assert "marker" not in json.dumps(projection)


def test_only_exact_loaded_paths_are_kept() -> None:
    dropped = [
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
    as_ready = status(ready=[entry(p) for p in dropped], active=[], blocked=[])
    as_active = status(ready=[], active=[entry(p) for p in dropped], blocked=[])
    as_blocked = status(
        ready=[], active=[], blocked=[entry(p, False, [finding()]) for p in dropped]
    )
    assert rd.project(checked_of(as_ready), PATH_TO_ID)["ready"] == []
    assert rd.project(checked_of(as_active), PATH_TO_ID)["active"] == []
    assert rd.project(checked_of(as_blocked), PATH_TO_ID)["blocked"] == []


def test_lists_keep_input_order() -> None:
    obj = status(ready=[entry(BLOCKED), entry(READY)], active=[], blocked=[])
    assert rd.project(checked_of(obj), PATH_TO_ID)["ready"] == ["spec:golf-new", "spec:bravo-spec"]


def test_a_repeated_blocked_path_appears_once_with_codes_in_input_order() -> None:
    blocked = [
        entry(
            BLOCKED,
            False,
            [finding("missing_plan", "Create and approve the plan before dispatch.")],
        ),
        entry(OTHER, False, [finding()]),
        entry(
            BLOCKED,
            False,
            [
                finding("unsatisfied_dependency"),
                finding("missing_plan", "Create and approve the plan before dispatch."),
            ],
        ),
        entry(
            BLOCKED,
            False,
            [finding("dependency_cycle", "Break the cycle through an explicit plan change.")],
        ),
    ]
    projection = rd.project(checked_of(status(ready=[], active=[], blocked=blocked)), PATH_TO_ID)
    assert [b["id"] for b in projection["blocked"]] == ["spec:golf-new", "intent:bravo-feat"]
    codes = [f["code"] for f in projection["blocked"][0]["findings"]]
    assert codes == ["missing_plan", "unsatisfied_dependency", "dependency_cycle"]


def test_known_is_true_only_for_a_pair_in_the_finding_table() -> None:
    table = rd._KNOWN_FINDINGS
    assert table
    # The two workspace-failure codes refuse the whole input, so they never project.
    pairs = [
        (code, action)
        for code, action in table.items()
        if code not in {"invalid_workspace", "configuration_mismatch"}
    ]
    blocked = [
        entry(BLOCKED, False, [finding(code, action) for code, action in pairs]),
        entry(READY, False, [finding(pairs[0][0], "another sentence")]),
        entry(ACTIVE, False, [finding("brand_new_code", pairs[0][1])]),
    ]
    projection = rd.project(checked_of(status(ready=[], active=[], blocked=blocked)), PATH_TO_ID)
    by_id = {b["id"]: b["findings"] for b in projection["blocked"]}
    assert all(f["known"] is True for f in by_id["spec:golf-new"])
    assert [f["code"] for f in by_id["spec:golf-new"]] == [c for c, _ in pairs]
    assert by_id["spec:bravo-spec"][0]["known"] is False
    assert by_id["spec:charlie-spec"][0]["known"] is False
    assert by_id["spec:bravo-spec"][0]["next_action"] == "another sentence"


def test_member_wraps_a_refusal_and_a_projection_failure() -> None:
    assert rd.member(b"", PATH_TO_ID) == {"checked": False, "reason": "empty"}
    assert rd.member(encode(status()), PATH_TO_ID)["checked"] is True
    assert rd.member(encode(status()), None) == {  # type: ignore[arg-type]
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
        "no_workspace",
        "wrong_schema",
        "bad_workspace",
        "page_too_big",
    )
    assert max(map(len, rd.REASONS)) <= len("not_requested")


# --- AC-0018: the finding vocabulary copy ---------------------------------------------


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
    """A checked status whose not-known next actions are multi-byte text."""
    action = "\u2192 \u00e9\u00e8 " * 40
    return encode(status(blocked=[entry(BLOCKED, False, [finding("custom_code", action)])]))


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
    ran = export(tmp_path, encode(status()))
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
    findings = [{"code": f"c{i}", "dispatchable": False, "next_action": "x"} for i in range(count)]
    status = copy.deepcopy(BASE)
    status["canonical"]["blocked"] = [{"path": path, "dispatchable": False, "findings": findings}]
    started = time.monotonic()
    got = rd.member(encode(status), {path: "spec:bravo-spec"})
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


def test_entries_naming_nothing_loaded_are_dropped_from_data_and_text(tmp_path) -> None:
    obj = status(
        ready=[entry(p) for p in DROPPED] + [entry(READY)],
        active=[],
        blocked=[entry(f"{p}#b", False, [finding()]) for p in DROPPED]
        + [entry(BLOCKED, False, [finding()])],
    )
    ran = export(tmp_path, encode(obj))
    assert ran.payload is not None and ran.html is not None
    member = ran.payload["readiness"]
    assert member["checked"] is True
    assert member["ready"] == ["spec:bravo-spec"]
    assert [b["id"] for b in member["blocked"]] == ["spec:golf-new"]
    # the first ready entry, /etc/passwd, is dropped, so the mark names nothing
    assert member["start"] == {"rule": "start", "id": None, "held": False, "active_count": 0}
    block = json.dumps(member)
    text = visible_text(ran.html)
    for path in DROPPED:
        assert path not in block, path
        assert path not in text, path
    # the static text does not depend on the status input at all
    assert visible_text(export(tmp_path).html or "") == text


def test_a_loaded_path_outside_the_from_scope_is_dropped(tmp_path) -> None:
    ran = export(tmp_path, encode(status(active=[], blocked=[])), from_id="intent:india-none")
    assert ran.payload is not None and ran.html is not None
    member = ran.payload["readiness"]
    assert member["checked"] is True
    assert member["ready"] == [] and member["active"] == [] and member["blocked"] == []
    assert member["start"] == {"rule": "start", "id": None, "held": False, "active_count": 0}
    assert "docs/specs/bravo-spec/spec.md" not in json.dumps(member)


def test_extra_members_never_reach_the_html(tmp_path) -> None:
    def extras(level: str) -> dict[str, Any]:
        out: dict[str, Any] = {
            name: f"marker-{level}-{name}"
            for name in ("slug", "summary", "refresh", "ini_slug", "collection", "initiatives")
        }
        out["locator"] = {"kind": "path", "value": f"/home/user/marker-{level}-locator"}
        return out

    obj = status(
        ready=[entry(READY, **extras("ready"))],
        active=[entry(ACTIVE, **extras("active"))],
        blocked=[
            entry(BLOCKED, False, [finding(path="marker-finding-path", **extras("finding"))],
                  **extras("blocked"))
        ],
        findings=[finding("top_code", "top", path="marker-top-finding-path", **extras("top"))],
    )
    obj.update(extras("top"))
    obj["canonical"].update(extras("canonical"))
    ran = export(tmp_path, encode(obj))
    assert ran.html is not None and ran.payload is not None
    assert ran.payload["readiness"]["checked"] is True
    assert "marker-" not in ran.html


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
    data = encode(status(blocked=[entry(BLOCKED, False, findings)]))
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
    data = encode(status())
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


# --- AC-0038: hostile workspace.toml through the real workspace-status -----------------------

_STATUS_SCRIPT = _PACK / ".apm" / "skills" / "workspace-status" / "scripts" / "workspace_status.py"


def test_real_workspace_status_over_a_hostile_workspace_toml_exports_safely(tmp_path) -> None:
    root = tmp_path / "root"
    shutil.copytree(_MIXED, root)
    shutil.copy(_HOSTILE_WORKSPACE, root / "workspace.toml")
    ws = _load(_STATUS_SCRIPT, "core_workspace_status_readiness_t")
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        code = ws.main(["status", "--root", str(root)])
    output = captured.getvalue()
    assert code == 0
    # The fixture must keep exercising the drop: every hostile string is in the real output
    # (JSON writes the control characters as escapes, so match their escaped form).
    for needle in HOSTILE_NEEDLES:
        assert needle in output or json.dumps(needle)[1:-1] in output, needle
    ran = export(tmp_path, output.encode("utf-8"), root=root)
    assert ran.result["status"] == "ok"
    assert ran.result["readiness"] == {"checked": True, "reason": None}
    assert ran.payload is not None and ran.html is not None
    assert len(ran.payload["readiness"]["blocked"]) >= 1
    # The whole file, data block included: no hostile string reaches the page at all.
    assert ran.html is not None
    for needle in HOSTILE_NEEDLES:
        assert needle not in ran.html, needle
        assert json.dumps(needle)[1:-1] not in ran.html, needle


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
         encode(status()).decode("utf-8")],
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


_SKILL_MD = _PACK / ".apm" / "skills" / "navigate-intents" / "SKILL.md"


def _skill_section(title: str) -> str:
    """The text of one ``## <title>`` section of the skill's instructions."""
    text = _SKILL_MD.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    assert match is not None, f"section {title!r} is missing"
    return " ".join(match.group(1).split())


def test_skill_export_section_gives_the_pipe_command_with_the_status_subcommand() -> None:
    section = _skill_section("Export an offline view")
    assert re.search(r"workspace_status\.py'? status --root \S+ \\ \| python3 scripts/navigate_intents\.py "
                     r"export --root \S+ --readiness -", section)
    assert "never runs `workspace-status`" in section


def test_skill_safety_section_allows_only_status_piped_and_unread() -> None:
    section = _skill_section("Safety controls")
    assert "Pipe only `workspace-status`'s ``status`` subcommand" in section
    assert "Never pipe any other `workspace-status` subcommand" in section
    assert "straight into the export without reading it or acting on its contents" in section
    assert "never runs `workspace-status`" in section
