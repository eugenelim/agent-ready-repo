# STUB: AC4 — red until resolve_state_path is added to _common.py
# stub: true
"""Unit tests for _common.resolve_state_path."""

from pathlib import Path

import pytest


def test_resolve_state_path_repo_scope():
    from agentbundle.commands._common import resolve_state_path  # noqa: PLC0415

    result = resolve_state_path("repo", Path("/repo"))
    assert result == Path("/repo/.agentbundle-state.toml")


def test_resolve_state_path_user_scope():
    from agentbundle.commands._common import resolve_state_path  # noqa: PLC0415

    result = resolve_state_path("user", Path("/home/alice"))
    assert result == Path("/home/alice/.agentbundle/state.toml")
