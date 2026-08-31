"""T11: the three direct suites run on Windows, and are judged by what ran."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from agentbundle.catalogue_tooling import self_host_windows

REQUIRED_TARGETS = (
    "tests/unit/test_direct_source_acquisition.py",
    "tests/unit/test_direct_admission.py",
    "tests/integration/test_direct_install.py",
)


def _steps(root: Path | None = None) -> list[str]:
    """The strings actually DISPATCHED by the curated step list.

    Walks the `steps` list literal inside `run_windows_compat` rather than every
    string constant in the module. Collecting all constants meant a docstring or
    a comment-as-string mentioning a path satisfied the registration assertion,
    so the test could pass with nothing dispatched.
    """
    import ast

    source = Path(self_host_windows.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "run_windows_compat"
    )
    assignment = next(
        node
        for node in ast.walk(function)
        if isinstance(node, ast.AnnAssign | ast.Assign)
        and "steps" in ast.dump(node.targets[0] if isinstance(node, ast.Assign) else node.target)
    )
    dispatched: list[str] = []
    for node in ast.walk(assignment.value):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            dispatched.append(node.value)
    return dispatched


def test_the_three_direct_suites_are_on_the_curated_windows_list():
    # Their Windows arms assert documented outcomes rather than skipping, so
    # they have to be dispatched at all.
    literals = _steps(Path())
    for target in REQUIRED_TARGETS:
        assert target in literals, f"{target} is not on the Windows list"


def test_performance_suites_stay_off_the_windows_list():
    # The performance suite is deliberately excluded. Checked against the
    # dispatched string literals rather than the file text, so a comment
    # explaining the exclusion does not read as the exclusion being violated.
    literals = _steps(Path())
    assert not any(literal.startswith("tests/performance/") for literal in literals)


def test_an_all_skipped_run_is_a_failure_not_a_pass(tmp_path: Path):
    # The reason the executed-count floor exists. pytest exits 0 when every
    # test skips, so a step judged by return code alone cannot tell a passing
    # Windows suite from one that never ran.
    module = tmp_path / "test_all_skipped.py"
    module.write_text(
        "import pytest\n\n"
        "@pytest.mark.skip(reason='stands in for a platform guard')\n"
        "def test_one():\n    assert True\n",
        encoding="utf-8",
    )

    # Return code alone says pass.
    plain = subprocess.run(
        [sys.executable, "-m", "pytest", str(module), "-q"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert plain.returncode == 0, "an all-skipped run exits 0 — this is the trap"

    # The executed-count floor says fail.
    rc = self_host_windows._pytest_step_with_executed_floor(
        "all skipped", [str(module)], tmp_path, sys.executable
    )
    assert rc == 1, "an all-skipped suite must not report a Windows pass"


def test_a_real_run_passes_the_floor(tmp_path: Path):
    # The positive control: without it, a floor that always failed would pass
    # the test above while blocking every Windows run.
    module = tmp_path / "test_runs.py"
    module.write_text("def test_one():\n    assert True\n", encoding="utf-8")
    rc = self_host_windows._pytest_step_with_executed_floor(
        "real run", [str(module)], tmp_path, sys.executable
    )
    assert rc == 0


def test_executed_count_reads_the_report(tmp_path: Path):
    # The counts come from pytest's own report, not from parsing its stdout.
    report = tmp_path / "report.xml"
    report.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<testsuites><testsuite name="pytest" errors="0" failures="0" '
        'skipped="3" tests="10" time="0.1"></testsuite></testsuites>\n',
        encoding="utf-8",
    )
    assert self_host_windows._executed_count(report) == 7
    assert self_host_windows._executed_count(tmp_path / "absent.xml") == 0


def test_a_failing_suite_still_fails_on_its_return_code(tmp_path: Path):
    # The floor is an additional condition, not a replacement for the exit code.
    module = tmp_path / "test_fails.py"
    module.write_text("def test_one():\n    assert False\n", encoding="utf-8")
    rc = self_host_windows._pytest_step_with_executed_floor(
        "failing run", [str(module)], tmp_path, sys.executable
    )
    assert rc != 0
