"""credbroker test-suite hardening (fallback) / AC2 / AC3 / AC4 / AC5 / AC7 / AC8 / AC9.

_cs_check_dotfile_read retained fallback substring scan catches the literal
        keyword-arg open(file="<path>") form that the AST branch misses (defense-in-depth).
_cs_check_dotfile_read catches inline part-composition bypass.
_cs_check_dotfile_read catches inline .read_bytes() form.
_cs_check_dotfile_read suppresses findings when opt-out marker is present.
_cs_check_dotfile_read catches bare open('.agentbundle/credentials.env') form.
_cs_is_canonical_shim returns False for canonical bytes at a
        non-canonical parent directory.
_cs_is_canonical_shim returns True for canonical bytes at "scripts/"
        and "shared-libs/" parent directories.
_load_cli_module helper is available in this test suite.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

import pytest
from agentbundle.catalogue_tooling.lint import _cs_check_dotfile_read, _cs_is_canonical_shim

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_CANONICAL_SHIM_SRC = (
    REPO_ROOT
    / "packs"
    / "credential-brokers"
    / ".apm"
    / "shared-libs"
    / "credentials_shim.py"
)
_SHIM_SOURCE_DIR = _CANONICAL_SHIM_SRC.parent


# ── AC9: _load_cli_module helper ─────────────────────────────────────────────

def _load_cli_module(py_path: pathlib.Path) -> types.ModuleType:
    """Load a Python file as a module via importlib, prepending its parent
    to sys.path for the duration of the load.

    This is the same pattern as ``_load_broker_module()`` in
    ``test_sso_broker_verbs.py``, generalised to accept any path.
    """
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(py_path.parent))
    return module


_BROKER_PY = (
    REPO_ROOT
    / "packs"
    / "credential-brokers"
    / ".apm"
    / "adapter-root-bins"
    / "sso-broker.py"
)


# ── AC9: smoke-test that _load_cli_module works ───────────────────────────────


def test_load_cli_module_loads_broker():
    """AC9 exercise: _load_cli_module can load sso-broker.py and the
    returned module exposes the expected top-level names."""
    if not _BROKER_PY.is_file():
        pytest.skip("sso-broker.py not present in this checkout")
    mod = _load_cli_module(_BROKER_PY)
    # The broker defines _AGENTBUNDLE_HOME at module level; confirm it is
    # present as a smoke test that the module loaded correctly.
    assert hasattr(mod, "_AGENTBUNDLE_HOME"), (
        "_load_cli_module returned module missing _AGENTBUNDLE_HOME"
    )
    assert hasattr(mod, "_SSO_PROFILE_DIR"), (
        "_load_cli_module returned module missing _SSO_PROFILE_DIR"
    )


# ── AC7 / AC8: _is_canonical_shim path-anchor ────────────────────────────────


class TestIsCanonicalShimPathAnchor:
    """Path-anchor requirement for _cs_is_canonical_shim."""

    @pytest.fixture(autouse=True)
    def _canonical_bytes(self, tmp_path):
        if not _CANONICAL_SHIM_SRC.is_file():
            pytest.skip("credentials_shim.py not present in this checkout")
        self._bytes = _CANONICAL_SHIM_SRC.read_bytes()
        self._tmp = tmp_path

    def _write_shim(self, parent_name: str) -> pathlib.Path:
        parent = self._tmp / parent_name
        parent.mkdir(parents=True, exist_ok=True)
        shim_file = parent / "credentials_shim.py"
        shim_file.write_bytes(self._bytes)
        return shim_file

    def test_non_canonical_parent_returns_false(self):
        """Canonical bytes at an arbitrary parent → False."""
        shim = self._write_shim("arbitrary")
        assert _cs_is_canonical_shim(shim, _SHIM_SOURCE_DIR) is False

    def test_scripts_parent_returns_true(self):
        """Canonical bytes at a scripts/ parent → True."""
        shim = self._write_shim("scripts")
        assert _cs_is_canonical_shim(shim, _SHIM_SOURCE_DIR) is True

    def test_shared_libs_parent_returns_true(self):
        """Canonical bytes at a shared-libs/ parent → True."""
        shim = self._write_shim("shared-libs")
        assert _cs_is_canonical_shim(shim, _SHIM_SOURCE_DIR) is True


# ── AC2 / AC3 / AC4 / AC5: _cs_check_dotfile_read ───────────────────────────


class TestD3CheckDotfileRead:
    """D3 dotfile-read detection — AST walk and fallback scan (fallback).

    Each test writes a minimal fixture Python file to tmp_path and calls
    _cs_check_dotfile_read() directly to verify finding presence/absence.
    """

    _DOTFILE_SUBSTRING = ".agentbundle/credentials.env"

    def _run(self, tmp_path: pathlib.Path, source: str) -> list[tuple[int, str]]:
        fixture = tmp_path / "fixture.py"
        fixture.write_text(source, encoding="utf-8")
        return _cs_check_dotfile_read(fixture)

    def test_part_composition_bypass_caught(self, tmp_path: pathlib.Path) -> None:
        """Inline part-composition is caught; old substring scan would miss it.

        The fixture uses ("." + "agentbundle") so no literal
        '.agentbundle/credentials.env' substring appears on any line.
        _cs_path_chain_components() resolves BinOp(Add) inside BinOp(Div)
        and the AST walk flags the .read_text() call.
        """
        # Split across adjacent string literals to stay under 99 chars while
        # keeping the part-composition fully inline (required for _cs_path_chain_components).
        source = (
            "from pathlib import Path\n"
            "result = ("
            'Path.home() / ("." + "agentbundle") / ("credentials" + ".env")'
            ").read_text()\n"
        )
        # Prove the old substring scan would have missed this.
        assert self._DOTFILE_SUBSTRING not in source, (
            "fixture must not contain the literal dotfile substring "
            "(that would make the test a tautology for the old scan)"
        )
        # AST walk catches it on the correct line.
        findings = self._run(tmp_path, source)
        assert findings, "expected a finding for inline part-composition bypass"
        matching = [(ln, desc) for ln, desc in findings if "read_text" in desc]
        assert matching, f"expected 'read_text' in finding description; got {findings}"
        assert matching[0][0] == 2, (
            f"expected call reported on line 2; got lineno={matching[0][0]}"
        )

    def test_read_bytes_inline_caught(self, tmp_path: pathlib.Path) -> None:
        """Inline .read_bytes() form is caught by the AST walk."""
        source = (
            "from pathlib import Path\n"
            "result = (Path.home() / '.agentbundle' / 'credentials.env').read_bytes()\n"
        )
        findings = self._run(tmp_path, source)
        assert findings, "expected a finding for .read_bytes() inline form"
        assert any("read_bytes" in desc for _, desc in findings), (
            f"expected 'read_bytes' in finding description; got {findings}"
        )

    def test_optout_marker_suppresses_finding(self, tmp_path: pathlib.Path) -> None:
        """Opt-out marker on the same line as the call suppresses the finding."""
        source = (
            "from pathlib import Path\n"
            "result = (Path.home() / '.agentbundle' / 'credentials.env').read_text()"
            "  # credentialed-primitive: reads-creds-directly\n"
        )
        findings = self._run(tmp_path, source)
        assert not findings, (
            "opt-out marker on the call line must suppress the finding; "
            f"got: {findings}"
        )

    def test_fallback_substring_scan_caught(self, tmp_path: pathlib.Path) -> None:
        """AC1 defense-in-depth: keyword-arg open() evades the AST branch but is
        caught by the retained fallback substring scan.

        _cs_check_dotfile_read's AST branch requires a positional arg in node.args;
        open(file=...) uses only node.keywords so the branch never fires.
        The fallback scan catches any line whose text contains the dotfile substring
        that the AST branch did not already flag.
        """
        source = 'f = open(file=".agentbundle/credentials.env").read()\n'
        findings = self._run(tmp_path, source)
        assert findings, (
            "expected fallback scan to catch keyword-arg open(file=...) form"
        )
        assert any("skill reads" in desc for _, desc in findings), (
            f"expected fallback-branch description 'skill reads'; got {findings}"
        )

    def test_bare_open_caught(self, tmp_path: pathlib.Path) -> None:
        """Bare open('.agentbundle/credentials.env') is caught by the AST walk.

        _cs_path_chain_components() resolves the string literal to
        ("relative", [".agentbundle", "credentials.env"]); _cs_is_dotfile_chain()
        returns True. ast.walk() visits the inner open() call even when it is
        chained with .read(). Asserting the AST-branch description
        "open() reads dotfile credentials" distinguishes this from the retained
        fallback substring scan (which would produce "skill reads ... directly").
        """
        source = "data = open('.agentbundle/credentials.env').read()\n"
        findings = self._run(tmp_path, source)
        assert findings, "expected a finding for bare open('.agentbundle/credentials.env')"
        assert any("open() reads dotfile credentials" in desc for _, desc in findings), (
            f"expected AST-branch description 'open() reads dotfile credentials'; got {findings}"
        )
