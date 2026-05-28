"""Tests for `agentbundle.scope.configured_adapter`.

Scope-agnostic, pack-agnostic reporter. Returns the user-configured
adapter when set AND known by the bundled adapter contract; returns
None otherwise. Scope-capability and pack-`allowed_adapters`
enforcement live in `_resolve_target_adapter`, not here.
"""

from __future__ import annotations

from agentbundle.scope import configured_adapter
from agentbundle.user_config import UserConfig


def test_none_user_config_returns_none() -> None:
    assert configured_adapter(None) is None


def test_user_config_with_none_adapter_returns_none() -> None:
    assert configured_adapter(UserConfig(adapter=None)) is None


def test_known_adapter_returned() -> None:
    assert configured_adapter(UserConfig(adapter="codex")) == "codex"


def test_known_repo_only_adapter_returned() -> None:
    # `configured_adapter` does NOT enforce user-scope-capability — that
    # is the resolver's job. Copilot (repo-only) is returned here.
    assert configured_adapter(UserConfig(adapter="copilot")) == "copilot"


def test_unknown_adapter_returns_none() -> None:
    # Defense in depth — the loader already warns and nulls this case.
    assert configured_adapter(UserConfig(adapter="not-a-real-adapter")) is None
