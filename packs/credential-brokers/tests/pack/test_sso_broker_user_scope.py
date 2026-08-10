"""SSO broker backend loading under the user-scope layout."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
PACK = REPO_ROOT / "packs" / "credential-brokers" / ".apm"


def _clean_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP"}
    }
    env.pop("PYTHONPATH", None)
    return env


def test_sso_broker_tier2_backend_loads_under_user_scope_layout(
    tmp_path: Path,
) -> None:
    source = PACK / "adapter-root-bins"
    shim_source = PACK / "shared-libs"
    if not (source / "sso-broker.py").is_file():
        pytest.skip("sso-broker.py not present")
    staged = tmp_path / "bin"
    staged.mkdir()
    for entry in source.iterdir():
        if entry.is_file() and entry.suffix == ".py":
            shutil.copy(entry, staged / entry.name)
    shutil.copy(shim_source / "credentials_shim.py", staged / "credentials_shim.py")
    assert not (staged / "__init__.py").exists()
    assert not (staged / "_keychain_macos.py").exists()
    assert not (staged / "_credman_windows.py").exists()
    result = subprocess.run(
        [sys.executable, "bin/sso-broker.py", "show-tier2-backend"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    if sys.platform == "darwin":
        assert "_sso_keychain_macos" in result.stdout
    elif sys.platform == "win32":
        assert "_sso_credman_windows" in result.stdout
    else:
        assert "None" in result.stdout
