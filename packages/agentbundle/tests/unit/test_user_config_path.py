"""Tests for `agentbundle.user_config._user_config_path`.

Pure function over `(platform, env, home)` → `Path`. Branch coverage
matters; each platform has its own contract.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.user_config import _user_config_path


def test_macos_path_uses_application_support() -> None:
    home = Path("/Users/alice")
    result = _user_config_path(platform="darwin", env={}, home=home)
    assert result == home / "Library" / "Application Support" / "agentbundle" / "config.toml"


def test_linux_xdg_unset_falls_back_to_dot_config() -> None:
    home = Path("/home/alice")
    result = _user_config_path(platform="linux", env={}, home=home)
    assert result == home / ".config" / "agentbundle" / "config.toml"


def test_linux_xdg_set_overrides_home() -> None:
    home = Path("/home/alice")
    result = _user_config_path(
        platform="linux", env={"XDG_CONFIG_HOME": "/custom"}, home=home
    )
    assert result == Path("/custom") / "agentbundle" / "config.toml"


def test_windows_appdata_set() -> None:
    home = Path("C:/Users/alice")
    result = _user_config_path(
        platform="win32",
        env={"APPDATA": "C:/Users/alice/AppData/Roaming"},
        home=home,
    )
    assert result == Path("C:/Users/alice/AppData/Roaming") / "agentbundle" / "config.toml"


def test_windows_appdata_unset_uses_home_fallback() -> None:
    home = Path("C:/Users/alice")
    result = _user_config_path(platform="win32", env={}, home=home)
    assert result == home / "AppData" / "Roaming" / "agentbundle" / "config.toml"
