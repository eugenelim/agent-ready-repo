"""Tests for `agentbundle.commands.config.run`.

In-process tests against the handler. The conftest fixture has
already redirected HOME / XDG_CONFIG_HOME / APPDATA to a per-test
sandbox, so the handler's file IO lands under tmp.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agentbundle.commands.config import run
from agentbundle.user_config import _user_config_path


def _args(action: str, key: str | None = None, value: str | None = None):
    return argparse.Namespace(config_action=action, key=key, value=value)


# ---------------------------------------------------------------------------
# `path`
# ---------------------------------------------------------------------------


def test_path_prints_resolved_path(capsys) -> None:
    exit_code = run(_args("path"))
    captured = capsys.readouterr()
    assert exit_code == 0
    assert str(_user_config_path()) == captured.out.strip()


# ---------------------------------------------------------------------------
# `get`
# ---------------------------------------------------------------------------


def test_get_no_key_on_missing_file_reports_builtin(capsys) -> None:
    exit_code = run(_args("get"))
    captured = capsys.readouterr()
    assert exit_code == 0
    # One line per known key. Today only `adapter`.
    out = captured.out.strip()
    parts = out.split("\t")
    assert parts[0] == "adapter"
    assert parts[2] == "(builtin)"


def test_get_adapter_after_set_reports_file(capsys) -> None:
    run(_args("set", "adapter", "codex"))
    capsys.readouterr()  # drain
    exit_code = run(_args("get", "adapter"))
    captured = capsys.readouterr()
    assert exit_code == 0
    out = captured.out.strip()
    assert out == "adapter\tcodex\t(file)"


def test_get_unknown_key_exits_nonzero(capsys) -> None:
    exit_code = run(_args("get", "future-key"))
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "adapter" in captured.err  # known keys listed


# ---------------------------------------------------------------------------
# `set`
# ---------------------------------------------------------------------------


def test_set_adapter_creates_file(capsys) -> None:
    exit_code = run(_args("set", "adapter", "codex"))
    assert exit_code == 0
    cfg_path = _user_config_path()
    assert cfg_path.exists()
    assert 'adapter = "codex"' in cfg_path.read_text()


def test_set_adapter_idempotent(capsys) -> None:
    run(_args("set", "adapter", "codex"))
    cfg_path = _user_config_path()
    first = cfg_path.read_bytes()
    run(_args("set", "adapter", "codex"))
    assert cfg_path.read_bytes() == first


def test_set_unknown_adapter_refuses(capsys) -> None:
    exit_code = run(_args("set", "adapter", "not-a-real-adapter"))
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "not-a-real-adapter" in captured.err
    assert "claude-code" in captured.err  # admissible names listed
    assert not _user_config_path().exists()


def test_set_unknown_key_refuses(capsys) -> None:
    exit_code = run(_args("set", "future-key", "value"))
    captured = capsys.readouterr()
    assert exit_code != 0
    assert "future-key" in captured.err
    assert "adapter" in captured.err  # known keys listed
    assert not _user_config_path().exists()


# ---------------------------------------------------------------------------
# `unset`
# ---------------------------------------------------------------------------


def test_unset_only_key_deletes_file(capsys) -> None:
    run(_args("set", "adapter", "codex"))
    cfg_path = _user_config_path()
    assert cfg_path.exists()
    exit_code = run(_args("unset", "adapter"))
    assert exit_code == 0
    assert not cfg_path.exists()


def test_unset_missing_key_is_noop(capsys) -> None:
    # No file at all.
    exit_code = run(_args("unset", "adapter"))
    assert exit_code == 0
    assert not _user_config_path().exists()


def test_unset_preserves_other_settings(capsys) -> None:
    cfg_path = _user_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text('[settings]\nadapter = "codex"\nfuture_str = "x"\n')
    exit_code = run(_args("unset", "adapter"))
    assert exit_code == 0
    assert cfg_path.exists()
    data = cfg_path.read_text()
    assert 'future_str = "x"' in data
    assert "adapter" not in data
