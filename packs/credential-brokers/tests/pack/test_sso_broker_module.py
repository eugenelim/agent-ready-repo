"""Credential-brokers SSO broker module smoke test."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
BROKER = (
    REPO_ROOT
    / "packs"
    / "credential-brokers"
    / ".apm"
    / "adapter-root-bins"
    / "sso-broker.py"
)


def test_sso_broker_module_loads() -> None:
    if not BROKER.is_file():
        pytest.skip("sso-broker.py not present in this checkout")
    spec = importlib.util.spec_from_file_location(BROKER.stem, BROKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(BROKER.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(BROKER.parent))
    assert hasattr(module, "_AGENTBUNDLE_HOME")
    assert hasattr(module, "_SSO_PROFILE_DIR")
