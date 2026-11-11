"""The JUnit gate fails on zero tests, a skip of any kind, or an error."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parent / "require-junit-ran-without-skips.py"
_SPEC = importlib.util.spec_from_file_location("tools_require_junit_ran_without_skips", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gate)

CLEAN = (
    '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="2">'
    '<testcase classname="m" name="a"/><testcase classname="m" name="b"/>'
    "</testsuite></testsuites>"
)
ZERO = '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="0"/></testsuites>'
PER_CASE_SKIP = (
    '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="1" tests="2">'
    '<testcase classname="m" name="a"/>'
    '<testcase classname="m" name="b"><skipped message="why"/></testcase>'
    "</testsuite></testsuites>"
)
# A module-level skip can leave the suite counting a skip with no skipped child.
MODULE_SKIP_NO_ELEMENT = (
    '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="1" tests="2">'
    '<testcase classname="m" name="a"/><testcase classname="m" name="b"/>'
    "</testsuite></testsuites>"
)
MODULE_SKIP_ONLY = (
    '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="1" tests="1">'
    '<testcase classname="" name="m"><skipped message="Windows-only module"/></testcase>'
    "</testsuite></testsuites>"
)
ERROR = (
    '<testsuites><testsuite name="pytest" errors="1" failures="0" skipped="0" tests="1">'
    '<testcase classname="m" name="a"><error message="boom"/></testcase>'
    "</testsuite></testsuites>"
)
ERROR_COUNT_ONLY = (
    '<testsuites><testsuite name="pytest" errors="1" failures="0" skipped="0" tests="1">'
    '<testcase classname="m" name="a"/></testsuite></testsuites>'
)
FAILURE = (
    '<testsuites><testsuite name="pytest" errors="0" failures="1" skipped="0" tests="1">'
    '<testcase classname="m" name="a"><failure message="no"/></testcase>'
    "</testsuite></testsuites>"
)


def _run(tmp_path: Path, xml: str) -> int:
    report = tmp_path / "junit.xml"
    report.write_text(xml, encoding="utf-8")
    return gate.main(["gate", str(report)])


def test_clean_run_exits_zero(tmp_path: Path) -> None:
    assert _run(tmp_path, CLEAN) == 0


@pytest.mark.parametrize(
    "xml",
    [ZERO, PER_CASE_SKIP, MODULE_SKIP_NO_ELEMENT, MODULE_SKIP_ONLY, ERROR, ERROR_COUNT_ONLY, FAILURE],
    ids=["zero", "case-skip", "suite-skip-count", "module-skip", "error", "error-count", "failure"],
)
def test_unproven_run_exits_non_zero(tmp_path: Path, xml: str) -> None:
    assert _run(tmp_path, xml) == 1


def test_unreadable_report_exits_non_zero(tmp_path: Path) -> None:
    assert gate.main(["gate", str(tmp_path / "missing.xml")]) == 1
    (tmp_path / "bad.xml").write_text("<not-xml", encoding="utf-8")
    assert gate.main(["gate", str(tmp_path / "bad.xml")]) == 1


def test_wrong_arguments_exit_two() -> None:
    assert gate.main(["gate"]) == 2
