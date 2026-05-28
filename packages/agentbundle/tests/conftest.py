"""Suite-wide pytest fixtures for the agentbundle test root.

The autouse `_isolate_user_config_dir` fixture redirects the
platform env vars that `agentbundle.user_config._user_config_path`
consults, so no test can read or write the developer's real user
config file. See `docs/specs/agentbundle-config-subcommand/spec.md`
AC17.

Implementation note: this fixture sets env vars only. It does NOT
monkey-patch `Path.home()` — the existing `fake_home` fixture in
`tests/unit/test_resolve_user_scope_target_adapter.py` stubs
`Path.home()` independently for probe-detection tests. The two
compose because the user-config resolver consults env first on
Linux/Windows (XDG_CONFIG_HOME / APPDATA wins over home) and
respects `home` on macOS via the explicit parameter. Tests that
need `Path.home()` under their control use `fake_home`; tests that
exercise the user-config file rely on this env redirect.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_user_config_dir(
    tmp_path_factory: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    # Carve the sandbox out of `tmp_path_factory` rather than the
    # per-test `tmp_path` — tests like `test_write_jailed_is_atomic_*`
    # iterate `tmp_path.iterdir()` and would see our sandbox dir as a
    # spurious entry. Each test still gets a fresh sandbox because
    # tmp_path_factory.mktemp() is per-call.
    sandbox = tmp_path_factory.mktemp("user-config-sandbox")
    monkeypatch.setenv("HOME", str(sandbox))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(sandbox / ".config"))
    monkeypatch.setenv("APPDATA", str(sandbox / "AppData" / "Roaming"))
    return sandbox
