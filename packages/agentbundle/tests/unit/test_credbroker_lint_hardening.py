"""credbroker test-suite hardening — AC7 / AC8 / AC9.

AC7  — _cs_is_canonical_shim returns False for canonical bytes at a
        non-canonical parent directory.
AC8  — _cs_is_canonical_shim returns True for canonical bytes at "scripts/"
        and "shared-libs/" parent directories.
AC9  — _load_cli_module helper is available in this test suite.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

import pytest

from agentbundle.catalogue_tooling.lint import _cs_is_canonical_shim


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
    """Path-anchor requirement for _cs_is_canonical_shim (AC6 / AC7 / AC8)."""

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
        """AC7: canonical bytes at an arbitrary parent → False."""
        shim = self._write_shim("arbitrary")
        assert _cs_is_canonical_shim(shim, _SHIM_SOURCE_DIR) is False

    def test_scripts_parent_returns_true(self):
        """AC8a: canonical bytes at a scripts/ parent → True."""
        shim = self._write_shim("scripts")
        assert _cs_is_canonical_shim(shim, _SHIM_SOURCE_DIR) is True

    def test_shared_libs_parent_returns_true(self):
        """AC8b: canonical bytes at a shared-libs/ parent → True."""
        shim = self._write_shim("shared-libs")
        assert _cs_is_canonical_shim(shim, _SHIM_SOURCE_DIR) is True
