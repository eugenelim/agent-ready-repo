"""Tests for `agentbundle.user_config` IO: read, write, unset.

The IO layer is pure given its `path` parameter — every test passes
`tmp_path / "config.toml"` explicitly. No reliance on the conftest
isolation fixture's env-redirect — that fixture exists for tests
that call `load_user_config()` without a path.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from agentbundle.user_config import (
    UserConfig,
    read_user_config,
    unset_setting,
    write_setting,
)


# ---------------------------------------------------------------------------
# read_user_config
# ---------------------------------------------------------------------------


def test_read_missing_file_returns_empty(tmp_path: Path, capsys) -> None:
    cfg_path = tmp_path / "config.toml"
    assert read_user_config(cfg_path) == UserConfig(adapter=None)
    captured = capsys.readouterr()
    assert captured.err == ""  # no warning on a missing file


def test_read_valid_adapter(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\nadapter = "codex"\n')
    assert read_user_config(cfg_path) == UserConfig(adapter="codex")


def test_read_malformed_toml_warns_and_returns_empty(
    tmp_path: Path, capsys
) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\nadapter = "unterminated\n')  # missing close quote
    result = read_user_config(cfg_path)
    assert result == UserConfig(adapter=None)
    captured = capsys.readouterr()
    assert str(cfg_path) in captured.err
    assert "agentbundle" in captured.err.lower()


def test_read_invalid_adapter_warns_and_nullifies(
    tmp_path: Path, capsys
) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\nadapter = "obsolete-name"\n')
    result = read_user_config(cfg_path)
    assert result == UserConfig(adapter=None)
    captured = capsys.readouterr()
    assert "obsolete-name" in captured.err
    # The admissible set should be listed so the user can recover.
    assert "claude-code" in captured.err


# ---------------------------------------------------------------------------
# write_setting
# ---------------------------------------------------------------------------


def test_write_creates_parent_and_file(tmp_path: Path) -> None:
    cfg_path = tmp_path / "nested" / "dir" / "config.toml"
    write_setting(cfg_path, "adapter", "codex")
    assert cfg_path.exists()
    assert read_user_config(cfg_path) == UserConfig(adapter="codex")


def test_write_idempotent_on_repeat(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    write_setting(cfg_path, "adapter", "codex")
    first = cfg_path.read_bytes()
    write_setting(cfg_path, "adapter", "codex")
    assert cfg_path.read_bytes() == first


def test_write_refuses_unknown_adapter(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    with pytest.raises(ValueError) as excinfo:
        write_setting(cfg_path, "adapter", "not-a-real-adapter")
    assert "not-a-real-adapter" in str(excinfo.value)
    assert "claude-code" in str(excinfo.value)
    assert not cfg_path.exists()


def test_write_refuses_unknown_key(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    with pytest.raises(ValueError) as excinfo:
        write_setting(cfg_path, "future-key", "some-value")
    assert "future-key" in str(excinfo.value)
    assert "adapter" in str(excinfo.value)  # known keys listed
    assert not cfg_path.exists()


def test_write_refuses_non_settings_table(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[future]\nx = 1\n')
    original = cfg_path.read_bytes()
    with pytest.raises(ValueError) as excinfo:
        write_setting(cfg_path, "adapter", "codex")
    assert "future setting" in str(excinfo.value).lower()
    assert cfg_path.read_bytes() == original  # not mutated


def test_write_refuses_non_string_settings_value(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\ntags = ["a", "b"]\n')
    original = cfg_path.read_bytes()
    with pytest.raises(ValueError) as excinfo:
        write_setting(cfg_path, "adapter", "codex")
    assert "future setting" in str(excinfo.value).lower()
    assert cfg_path.read_bytes() == original


def test_write_refuses_nested_settings_table(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings.future]\nx = 1\n')
    original = cfg_path.read_bytes()
    with pytest.raises(ValueError) as excinfo:
        write_setting(cfg_path, "adapter", "codex")
    assert "future setting" in str(excinfo.value).lower()
    assert cfg_path.read_bytes() == original


# ---------------------------------------------------------------------------
# unset_setting
# ---------------------------------------------------------------------------


def test_unset_only_adapter_deletes_file(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    write_setting(cfg_path, "adapter", "codex")
    assert cfg_path.exists()
    unset_setting(cfg_path, "adapter")
    assert not cfg_path.exists()


def test_unset_preserves_unknown_settings_keys(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\nadapter = "codex"\nfuture_str = "x"\n')
    unset_setting(cfg_path, "adapter")
    # File still exists; future_str preserved.
    assert cfg_path.exists()
    data = cfg_path.read_text()
    assert 'future_str = "x"' in data
    assert "adapter" not in data


def test_unset_missing_key_is_noop(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    # File doesn't exist at all.
    unset_setting(cfg_path, "adapter")  # no raise
    assert not cfg_path.exists()


def test_unset_refuses_unknown_key(tmp_path: Path) -> None:
    """The N7 guard symmetrical to `write_setting`'s unknown-key
    refusal: an unknown key raises ValueError before any file IO,
    even when the file doesn't exist."""
    cfg_path = tmp_path / "config.toml"
    with pytest.raises(ValueError) as excinfo:
        unset_setting(cfg_path, "future-key")
    assert "future-key" in str(excinfo.value)
    assert "adapter" in str(excinfo.value)  # known keys listed
    assert not cfg_path.exists()


def test_unset_refuses_non_settings_table(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[future]\nx = 1\n')
    original = cfg_path.read_bytes()
    with pytest.raises(ValueError) as excinfo:
        unset_setting(cfg_path, "adapter")
    assert "future setting" in str(excinfo.value).lower()
    assert cfg_path.read_bytes() == original


def test_unset_refuses_non_string_settings_value(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\ntags = ["a", "b"]\nadapter = "codex"\n')
    original = cfg_path.read_bytes()
    with pytest.raises(ValueError) as excinfo:
        unset_setting(cfg_path, "adapter")
    assert "future setting" in str(excinfo.value).lower()
    assert cfg_path.read_bytes() == original


def test_unset_empty_settings_after_remove_deletes_file(tmp_path: Path) -> None:
    # File starts with only [settings] adapter; unset → empty → deleted.
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text('[settings]\nadapter = "codex"\n')
    unset_setting(cfg_path, "adapter")
    assert not cfg_path.exists()
