"""Every gate enumeration that must name `jsonl-otlp-exporter` actually does.

AC-0031 of `docs/specs/loop-telemetry-export`. Each site below is a literal
list, so adding the package to one adds it to none of the others, and `make
test` still reports green while the package's suite and type checks are not
run by anything. The point of this module is that the failure is loud.

AC-0031 names four sites. A fifth is asserted here because the four do not
achieve what the criterion's own purpose clause states -- see
`docs/specs/loop-telemetry-export/notes/verification-ledger.md`.

Structured config is parsed, never grepped: `grep '^pythonpath' pyproject.toml`
matches the key under every table, not the one table that governs.
"""
from __future__ import annotations

import ast
import re
import tomllib
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_PACKAGE_DIR = "packages/jsonl-otlp-exporter"
_MODULE_DIR = f"{_PACKAGE_DIR}/jsonl_otlp_exporter"


def _pyproject() -> dict:
    return tomllib.loads((_REPO / "pyproject.toml").read_text(encoding="utf-8"))


def _makefile() -> str:
    return (_REPO / "Makefile").read_text(encoding="utf-8")


def _run_test_suite_body() -> str:
    """The define `make test` expands, with comment lines stripped.

    Asserting against the whole file would pass on a line in a target nothing
    invokes; asserting against the raw define would pass on a line someone
    commented out. A `#` line in a Makefile recipe is not executed, so it
    cannot satisfy a claim that a suite runs.
    """
    match = re.search(r"override define run-test-suite(.*?)^endef", _makefile(), re.S | re.M)
    assert match, "run-test-suite define not found — Makefile structure changed"
    return "\n".join(
        line for line in match.group(1).splitlines() if not line.lstrip().startswith("#")
    )


def test_package_is_on_the_root_pytest_pythonpath() -> None:
    pythonpath = _pyproject()["tool"]["pytest"]["ini_options"]["pythonpath"]
    assert _PACKAGE_DIR in pythonpath, f"{_PACKAGE_DIR} missing from pythonpath: {pythonpath}"


def test_package_is_in_mypys_files() -> None:
    """AC-0031's named site. Necessary, and on its own it checks nothing.

    `tools/lint-mypy.py` passes its own package list as positional arguments,
    and mypy's positional arguments override `files` from the config. So this
    assertion can hold while the gate type-checks nothing in the package --
    which is exactly what happened. The next test is the one with teeth.
    """
    files = _pyproject()["tool"]["mypy"]["files"]
    assert _MODULE_DIR in files, f"{_MODULE_DIR} missing from mypy files: {files}"


def test_package_is_in_the_list_the_mypy_gate_actually_reads() -> None:
    """The sixth site: what `make lint-mypy` really checks.

    Measured -- with the package in `files` but not here, the gate reported
    "no issues found in 139 source files" and checked none of the package.
    With it here: 146 files, and it found a real annotation defect.
    """
    # Parsed, not grepped. Searching the file's text would let a comment or a
    # docstring mentioning the path satisfy this while TYPED_PACKAGES itself
    # omits the package and the gate skips it -- a control that cannot fail.
    tree = ast.parse((_REPO / "tools" / "lint-mypy.py").read_text(encoding="utf-8"))
    declared: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "TYPED_PACKAGES"
            for target in node.targets
        ):
            continue
        assert isinstance(node.value, (ast.List, ast.Tuple)), (
            "TYPED_PACKAGES is no longer a literal list -- this control can no "
            "longer read it and must be rewritten rather than left passing"
        )
        declared = [
            element.value
            for element in node.value.elts
            if isinstance(element, ast.Constant) and isinstance(element.value, str)
        ]
    assert declared, "TYPED_PACKAGES not found in tools/lint-mypy.py"
    assert _MODULE_DIR in declared, (
        f"{_MODULE_DIR} missing from tools/lint-mypy.py TYPED_PACKAGES "
        f"(declared: {declared}) -- mypy's positional arguments override the "
        "config's files list, so the gate would silently skip the package"
    )


def test_package_suite_is_invoked_by_the_define_make_test_expands() -> None:
    body = _run_test_suite_body()
    assert re.search(rf"pytest\s+{re.escape(_PACKAGE_DIR)}/", body), (
        f"no pytest invocation for {_PACKAGE_DIR} inside run-test-suite"
    )


def test_package_build_backend_is_audited() -> None:
    # Comment lines stripped first: a commented-out `--build-system` argument
    # audits nothing, and a regex over raw text cannot tell the difference.
    makefile = "\n".join(
        line for line in _makefile().splitlines() if not line.lstrip().startswith("#")
    )
    leg = re.search(r"--build-system\s*\\?\s*\n((?:.*\\\n)*.*)", makefile)
    assert leg, "pip-audit --build-system leg not found"
    assert f"{_PACKAGE_DIR}/pyproject.toml" in leg.group(1), (
        f"{_PACKAGE_DIR}/pyproject.toml missing from the pip-audit build-system leg"
    )


def test_package_is_on_the_makefile_pythonpath() -> None:
    """The fifth site, and the only one that makes the suite runnable.

    Each `packages/*/` suite carries its own `[tool.pytest.ini_options]`, which
    is the nearer configfile for its own run, so the root `pythonpath` above
    does not reach it. Without this entry the package's tests raise
    `ModuleNotFoundError: No module named 'jsonl_otlp_exporter'` at collection.
    """
    assignment = re.search(r"^PYTHONPATH\s*:=\s*(.+)$", _makefile(), re.M)
    assert assignment, "PYTHONPATH assignment not found in Makefile"
    assert _PACKAGE_DIR in assignment.group(1), (
        f"{_PACKAGE_DIR} missing from Makefile PYTHONPATH: {assignment.group(1)}"
    )


@pytest.mark.parametrize("relative", ["pyproject.toml", "jsonl_otlp_exporter/__init__.py"])
def test_the_package_this_module_guards_still_exists(relative: str) -> None:
    """A guard naming a deleted package passes by asserting about nothing."""
    assert (_REPO / _PACKAGE_DIR / relative).is_file(), (
        f"{_PACKAGE_DIR}/{relative} is missing — this module's other assertions "
        "would then be pinning a package that no longer ships"
    )
