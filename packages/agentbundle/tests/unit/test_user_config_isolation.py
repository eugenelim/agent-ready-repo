"""Verify the autouse `_isolate_user_config_dir` fixture sandboxes
real user-config-dir lookups under the per-test tmp_path.

The contract is narrow: no test reads or writes the developer's
real `~/.config/agentbundle/config.toml` (or its macOS / Windows
equivalent). This is the only test that proves the contract by
construction; every other test inherits it.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.user_config import _user_config_path


def test_path_resolver_lands_under_sandbox(
    _isolate_user_config_dir: Path,
) -> None:
    # `_user_config_path()` with all defaults consults sys.platform +
    # os.environ + Path.home(). Under the autouse fixture, HOME and
    # XDG_CONFIG_HOME and APPDATA all point inside the sandbox dir
    # the fixture yields.
    resolved = _user_config_path()
    sandbox = _isolate_user_config_dir
    assert sandbox in resolved.parents, (
        f"Expected {resolved} to be under sandbox {sandbox}, "
        f"but the resolver consulted a non-sandboxed location."
    )
