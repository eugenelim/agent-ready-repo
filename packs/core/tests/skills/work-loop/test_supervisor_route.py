"""The ``route`` strings equal the routing table and stay short, detail-free and verb-scoped.

Ungated: no git repository is needed, because every string comes from a pure function and a
usage error is answered before any repository is read.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HELPER_PATH = Path(__file__).resolve().parent / "supervisor_support.py"


def _support() -> ModuleType:
    """Load the shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = "core_work_loop_supervisor_support"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATH)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


sup = _support()
cli = sup.load("work-supervisor.py")

RESUMPTION_MD = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "work-loop" / "references" / "session-resumption.md"
)
MAX_ROUTE_CHARS = 160

CAP = 5
REFUSAL = {"code": "criteria-changed", "owner": "spec-amendment owner", "detail": "SECRET-DETAIL"}
HUMAN = {"kind": "human-decision", "reason": "tests-failing"}


def _table() -> dict[tuple[str, str], str]:
    """The routing table's route strings, keyed by (order, verb); backticks stripped."""
    rows: dict[tuple[str, str], str] = {}
    for line in RESUMPTION_MD.read_text("utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0].isdigit():
            rows[(cells[0], cells[1])] = cells[3].replace("`", "")
    return rows


def test_the_table_has_the_nine_rows() -> None:
    assert len(_table()) == 9


def _cases() -> dict[tuple[str, str], tuple[str, dict[str, Any]]]:
    """For each (order, verb) table row, a verb and a payload of that shape."""
    leftover = {**REFUSAL, "code": "recovery-leftovers"}
    return {
        ("1", "status, next"): ("status", {"run": {}, "retry_count": CAP, "terminal": False,
                                           "request": None, "refusal": {}}),
        ("2", "status, next"): ("next", {"run": {}, "refusal": leftover}),
        ("4", "status"): ("status", {"run": {}, "pending_step": {"operation": "regenerate"},
                                     "retry_count": 0, "terminal": False, "request": None,
                                     "refusal": {}}),
        ("5", "status, next"): ("next", {"run": {}, "terminal": True}),
        ("6", "status, next"): ("next", {"run": {}, "request": HUMAN}),
        ("7", "status"): ("status", {"run": {}, "retry_count": 0, "terminal": False,
                                     "request": {"kind": "implement-task"}, "refusal": {}}),
        ("7", "next"): ("next", {"run": {}, "request": {"kind": "implement-task"}}),
        ("8", "status"): ("status", {"run": {}, "retry_count": 0, "terminal": False,
                                     "request": None, "refusal": {}}),
    }


@pytest.mark.parametrize("key", sorted(_cases()))
def test_each_route_equals_its_table_row(key: tuple[str, str]) -> None:
    verb, payload = _cases()[key]
    assert cli._route_for(verb, payload, CAP) == _table()[key]


def test_row_three_equals_its_table_row_with_the_refusals_own_code_and_owner() -> None:
    template = _table()[("3", "status, next")]
    expected = template.replace("<code>", REFUSAL["code"]).replace("<owner>", REFUSAL["owner"])
    for verb in ("status", "next"):
        assert cli._route_for(verb, {"run": {}, "refusal": REFUSAL}, CAP) == expected


def test_the_cap_row_is_reached_by_next_through_the_retry_cap_request() -> None:
    request = {"kind": "human-decision", "reason": "retry-cap"}
    assert cli._route_for("next", {"run": {}, "request": request}, CAP) == _table()[
        ("1", "status, next")]


def _longest_refusal_fields() -> tuple[str, str]:
    """The longest refusal code and owner literal the supervisor scripts construct."""
    # code, owner, then a detail: a two-argument call has no owner literal to read.
    pattern = re.compile(r'[Rr]efusal\(\s*"([^"]+)",\s*"([^"]+)",\s*(?:f?"|\()')
    codes: list[str] = []
    owners: list[str] = []
    for path in sorted(sup.SCRIPTS.glob("*supervisor*.py")):
        for code, owner in pattern.findall(path.read_text("utf-8")):
            codes.append(code)
            owners.append(owner)
    assert codes and owners
    return max(codes, key=len), max(owners, key=len)


def test_every_route_is_at_most_160_characters_with_the_longest_code_and_owner() -> None:
    code, owner = _longest_refusal_fields()
    long_refusal = {"code": code, "owner": owner, "detail": "x"}
    routes = [cli._route_for(v, p, CAP) for v, p in _cases().values()]
    routes += [cli._route_for(v, {"run": {}, "refusal": long_refusal}, CAP)
               for v in ("status", "next")]
    assert all(0 < len(route) <= MAX_ROUTE_CHARS for route in routes), routes
    assert all(len(route) <= MAX_ROUTE_CHARS for route in _table().values())


def test_no_route_contains_a_refusal_detail() -> None:
    for code in (REFUSAL["code"], "recovery-leftovers"):
        refusal = {**REFUSAL, "code": code}
        for verb in ("status", "next"):
            route = cli._route_for(verb, {"run": {}, "refusal": refusal}, CAP)
            assert REFUSAL["detail"] not in route


@pytest.mark.parametrize("verb", ["status", "next"])
def test_a_usage_error_carries_no_route(
        verb: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main([verb, "docs/specs/none"], cwd=tmp_path)
    payload = json.loads(out.getvalue())
    assert code == 2 and payload["error"] == "usage", payload
    assert "route" not in payload
