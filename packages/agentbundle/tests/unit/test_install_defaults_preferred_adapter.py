"""Tests for step 2.75 of `_resolve_target_adapter` — the org preferred-adapter
hint from packaged `_data/install-defaults.toml`.

Step 2.75 fires only when `state_adapter is None` and `preferred_adapter is not
None`, slotting between user-config step 2.5 and the probe/default step 3+4 in
the six-step chain.  Precedence: --adapter (step 1) > state-hint (step 2) >
user-config (step 2.5) > org hint (step 2.75) > probe/default (step 3+4).

See `docs/specs/install-defaults-preferred-adapter-hint/spec.md`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentbundle.commands.install import (
    _AdapterResolutionRefused,
    _resolve_target_adapter,
)
from agentbundle.user_config import UserConfig


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Empty `$HOME`; `Path.home()` returns it.  No probe-detectable dirs are
    present, so user-scope probes always fall through to defaults."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


def _pack(tmp_path: Path, name: str = "demo") -> Path:
    """Minimal pack dir; used as the `pack_dir` positional kwarg."""
    pack = tmp_path / "src" / name
    (pack / ".apm").mkdir(parents=True)
    return pack


# ---------------------------------------------------------------------------
# Step 2.75 fires — preferred_adapter returned
# ---------------------------------------------------------------------------


def test_org_hint_returned_when_no_other_signal(fake_home: Path, tmp_path: Path) -> None:
    """Org hint is used when --adapter is absent, state_adapter is None, and
    user_config has no adapter set."""
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter="cursor",
    )
    assert result == "cursor"


def test_org_hint_works_at_repo_scope(fake_home: Path, tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter="cursor",
    )
    assert result == "cursor"


def test_org_hint_works_without_allowed_adapters(fake_home: Path, tmp_path: Path) -> None:
    """No `allowed-adapters` declared — hint is still returned when valid at scope."""
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=None,
        contract_version="0.7",
        preferred_adapter="claude-code",
    )
    assert result == "claude-code"


# ---------------------------------------------------------------------------
# Precedence — higher-priority steps win over org hint
# ---------------------------------------------------------------------------


def test_explicit_adapter_flag_wins_over_org_hint(fake_home: Path, tmp_path: Path) -> None:
    """--adapter (step 1) takes precedence over org preferred_adapter (step 2.75)."""
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        adapter="claude-code",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter="cursor",
    )
    assert result == "claude-code"


def test_state_hint_wins_over_org_hint(fake_home: Path, tmp_path: Path) -> None:
    """state_adapter (step 2) wins over org preferred_adapter (step 2.75)."""
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "codex", "claude-code"],
        contract_version="0.7",
        state_adapter="codex",
        preferred_adapter="cursor",
    )
    assert result == "codex"


def test_user_config_wins_over_org_hint(fake_home: Path, tmp_path: Path) -> None:
    """user_config adapter (step 2.5) takes precedence over org preferred_adapter (step 2.75)."""
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        user_config=UserConfig(adapter="claude-code"),
        preferred_adapter="cursor",
    )
    assert result == "claude-code"


def test_state_hint_suppresses_org_hint_even_when_inadmissible(
    fake_home: Path, tmp_path: Path
) -> None:
    """When state_adapter is set (non-None but NOT in allowed_adapters), step 2
    falls through — but step 2.75 must also be skipped because the guard is
    `state_adapter is None`, not an admissibility check.

    If this invariant broke (guard changed to admissibility-based), the org hint
    would leak into upgrades where the prior adapter changed: `preferred_adapter`
    would be returned instead of falling through to probe/DEFAULT_ADAPTER.
    """
    pack = _pack(tmp_path)
    from agentbundle.scope import DEFAULT_ADAPTER
    # state_adapter="codex" is NOT in allowed_adapters=["cursor","claude-code"]
    # → step 2 falls through (inadmissible); step 2.75 must also be skipped.
    # Steps 3+4: no probe hits in empty fake_home → DEFAULT_ADAPTER.
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        state_adapter="codex",         # NOT in allowed_adapters
        preferred_adapter="cursor",    # would be returned if 2.75 fires (wrong)
    )
    assert result == DEFAULT_ADAPTER   # 2.75 was skipped; probe/default won


# ---------------------------------------------------------------------------
# Failure paths — org hint refused
# ---------------------------------------------------------------------------


def test_org_hint_refused_when_not_in_allowed_adapters(
    fake_home: Path, tmp_path: Path
) -> None:
    """Org hint is refused when the pack's allowed-adapters doesn't include it."""
    pack = _pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused, match="allowed-adapters"):
        _resolve_target_adapter(
            pack,
            scope="user",
            allowed_adapters=["claude-code"],
            contract_version="0.7",
            preferred_adapter="cursor",
        )


def test_org_hint_refused_when_not_admissible_at_scope(
    fake_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Org hint is refused when the adapter is not admissible at the given scope.

    This is a defensive guard: if a future contract revision removes an adapter
    from user scope, an org fork still shipping that value in install-defaults.toml
    will be caught here with a clear error.  We manufacture the scenario by
    patching the scope function to exclude 'cursor' from user_capable so the test
    doesn't rely on current contract contents.
    """
    import agentbundle.scope as _scope
    original_user_capable = _scope.user_scope_capable_adapters_from_contract
    monkeypatch.setattr(
        _scope,
        "user_scope_capable_adapters_from_contract",
        lambda: tuple(a for a in original_user_capable() if a != "cursor"),
    )
    pack = _pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused, match="scope"):
        _resolve_target_adapter(
            pack,
            scope="user",
            allowed_adapters=None,
            contract_version="0.7",
            preferred_adapter="cursor",
        )


# ---------------------------------------------------------------------------
# None preferred_adapter is a no-op
# ---------------------------------------------------------------------------


def test_none_preferred_adapter_leaves_behavior_unchanged(
    fake_home: Path, tmp_path: Path
) -> None:
    """preferred_adapter=None is a clean no-op: step 2.75 is skipped and the
    resolver falls through to step 3+4 (probe + DEFAULT_ADAPTER)."""
    pack = _pack(tmp_path)
    from agentbundle.scope import DEFAULT_ADAPTER
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
        preferred_adapter=None,
    )
    # No probe hits in the empty fake_home, so DEFAULT_ADAPTER wins.
    assert result == DEFAULT_ADAPTER


def test_default_preferred_adapter_is_none(fake_home: Path, tmp_path: Path) -> None:
    """The `preferred_adapter` parameter defaults to None — callers that don't
    pass it see identical behavior to the pre-feature baseline."""
    pack = _pack(tmp_path)
    from agentbundle.scope import DEFAULT_ADAPTER
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["cursor", "claude-code"],
        contract_version="0.7",
    )
    assert result == DEFAULT_ADAPTER


# ---------------------------------------------------------------------------
# AC7: invalid packaged hint causes install.run() to exit 1 before any write
# ---------------------------------------------------------------------------


def test_run_returns_1_on_invalid_packaged_preferred_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC7: install.run() exits 1 before any write when the packaged preferred_adapter
    is invalid.  The CatalogueError is caught at the top of run(), before any
    catalogue fetch or filesystem write.
    """
    import argparse
    import contextlib
    import io

    import agentbundle.source_defaults as _sd
    from agentbundle.catalogue import CatalogueError
    from agentbundle.commands import install as _install

    def _raise_invalid():
        raise CatalogueError(
            "install-defaults.toml: [organization].preferred_adapter 'bad' is "
            "not in the shipped adapter contract."
        )

    monkeypatch.setattr(_sd, "read_packaged_preferred_adapter", _raise_invalid)

    # Provide a catalogue so resolve_catalogue_uri succeeds before our check.
    args = argparse.Namespace(
        pack="core",
        catalogue="git+https://github.com/placeholder/catalogue",
        output=str(tmp_path),
        scope=None,
        force=False,
        profile=None,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = _install.run(args)

    assert rc == 1
    assert "install-defaults.toml" in buf.getvalue()
    # Nothing was written — the error fired before any catalogue fetch or I/O.
    assert not any(tmp_path.iterdir())


# ---------------------------------------------------------------------------
# AC9: render helpers thread preferred_adapter to _resolve_target_adapter
# ---------------------------------------------------------------------------


def test_render_for_user_scope_threads_preferred_adapter(
    fake_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC9: _render_for_user_scope passes preferred_adapter through to
    _resolve_target_adapter.  A dropped kwarg at that call site would make this
    test fail even though the unit tests on _resolve_target_adapter still pass.
    """
    import agentbundle.commands.install as _install

    captured_kwargs: dict = {}

    def _spy(*args, **kwargs):
        captured_kwargs.update(kwargs)
        raise _install._AdapterResolutionRefused("spy: stop here")

    monkeypatch.setattr(_install, "_resolve_target_adapter", _spy)
    pack = _pack(tmp_path)
    with pytest.raises(_install._AdapterResolutionRefused):
        _install._render_for_user_scope(
            pack,
            allowed_adapters=["cursor", "claude-code"],
            contract_version="0.7",
            preferred_adapter="cursor",
        )
    assert captured_kwargs.get("preferred_adapter") == "cursor"


def test_render_for_repo_scope_threads_preferred_adapter(
    fake_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC9: _render_for_repo_scope passes preferred_adapter through to
    _resolve_target_adapter."""
    import agentbundle.commands.install as _install

    captured_kwargs: dict = {}

    def _spy(*args, **kwargs):
        captured_kwargs.update(kwargs)
        raise _install._AdapterResolutionRefused("spy: stop here")

    monkeypatch.setattr(_install, "_resolve_target_adapter", _spy)
    pack = _pack(tmp_path)
    with pytest.raises(_install._AdapterResolutionRefused):
        _install._render_for_repo_scope(
            pack,
            allowed_adapters=["cursor", "claude-code"],
            contract_version="0.7",
            preferred_adapter="cursor",
        )
    assert captured_kwargs.get("preferred_adapter") == "cursor"
