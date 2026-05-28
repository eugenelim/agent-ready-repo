"""Tests for `_resolve_target_adapter`'s user-config pre-flight block.

The pre-flight is inserted between Step 2 (state-hint short-circuit)
and Step 3+4 (contract-version gate), only when `state_adapter is
None`. It either returns the configured candidate (admissible at
scope and in pack `allowed_adapters`) or raises
`_AdapterResolutionRefused` with the AC13 / AC14 message.

See `docs/specs/agentbundle-config-subcommand/spec.md` AC11–AC14.
Tests use the existing `fake_home` pattern from
`test_resolve_user_scope_target_adapter.py` to control `Path.home()`
and create real probe-detectable directories — no `_probes` test
seam, no monkeypatch of resolver internals.
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
    """Empty `$HOME`; `Path.home()` returns it. Mirrors the fixture in
    `test_resolve_user_scope_target_adapter.py` so the existing
    filesystem-based probe pattern applies here too."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


def _pack(tmp_path: Path, name: str = "demo") -> Path:
    """Minimal pack dir; used as the `pack_dir` positional kwarg."""
    pack = tmp_path / "src" / name
    (pack / ".apm").mkdir(parents=True)
    return pack


# ---------------------------------------------------------------------------
# Pre-flight returns when user-config is admissible
# ---------------------------------------------------------------------------


def test_preflight_returns_candidate_user_scope(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["codex", "claude-code"],
        contract_version="0.7",
        user_config=UserConfig(adapter="codex"),
    )
    assert result == "codex"


def test_preflight_returns_candidate_repo_scope(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        allowed_adapters=["codex"],
        contract_version="0.7",
        user_config=UserConfig(adapter="codex"),
    )
    assert result == "codex"


def test_preflight_returns_candidate_no_allowed_adapters(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=None,
        contract_version=None,
        user_config=UserConfig(adapter="codex"),
    )
    assert result == "codex"


# ---------------------------------------------------------------------------
# Pre-flight respects existing precedence (--adapter, state_adapter)
# ---------------------------------------------------------------------------


def test_explicit_adapter_flag_still_beats_user_config(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        adapter="claude-code",
        allowed_adapters=["claude-code"],
        contract_version="0.7",
        user_config=UserConfig(adapter="codex"),
    )
    assert result == "claude-code"


def test_state_hint_admissible_still_beats_user_config(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["kiro", "codex"],
        contract_version="0.7",
        state_adapter="kiro",
        user_config=UserConfig(adapter="codex"),
    )
    assert result == "kiro"


# ---------------------------------------------------------------------------
# Pre-flight wins over user-scope probe (when user_config explicitly set)
# ---------------------------------------------------------------------------


def test_user_config_wins_over_user_scope_probe(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    # Create .claude/ so the claude-code probe would otherwise match.
    (fake_home / ".claude").mkdir()
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["codex", "claude-code"],
        contract_version="0.7",
        user_config=UserConfig(adapter="codex"),
    )
    assert result == "codex"


def test_probe_still_wins_when_user_config_none(
    tmp_path: Path, fake_home: Path
) -> None:
    """The load-bearing regression test: when user_config is None, the
    pre-flight is a no-op and the existing probe path takes over. If
    the pre-flight ever returns DEFAULT_ADAPTER prematurely, this
    test fails."""
    pack = _pack(tmp_path)
    (fake_home / ".claude").mkdir()
    result_none = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["codex", "claude-code"],
        contract_version="0.7",
        user_config=None,
    )
    assert result_none == "claude-code"
    # Same with user_config=UserConfig(adapter=None) — also a no-op.
    result_blank = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["codex", "claude-code"],
        contract_version="0.7",
        user_config=UserConfig(adapter=None),
    )
    assert result_blank == "claude-code"


# ---------------------------------------------------------------------------
# Pre-flight refuses scope-incapable configured adapter (AC13)
# ---------------------------------------------------------------------------


def test_preflight_refuses_copilot_at_user_scope(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as excinfo:
        _resolve_target_adapter(
            pack,
            scope="user",
            allowed_adapters=None,
            contract_version=None,
            user_config=UserConfig(adapter="copilot"),
        )
    msg = str(excinfo.value)
    # AC13 message contract:
    assert "not supported at user scope" in msg
    assert "copilot" in msg
    assert "Adapters supported at user scope:" in msg
    # All four escape hatches:
    assert "--scope" in msg
    assert "--adapter" in msg
    assert "agentbundle config set adapter" in msg
    assert "agentbundle config unset adapter" in msg


# ---------------------------------------------------------------------------
# Pre-flight refuses pack-incompatible configured adapter (AC14)
# ---------------------------------------------------------------------------


def test_preflight_refuses_when_pack_excludes_user_config(
    tmp_path: Path, fake_home: Path
) -> None:
    pack = _pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as excinfo:
        _resolve_target_adapter(
            pack,
            scope="user",
            allowed_adapters=["claude-code"],
            contract_version="0.7",
            user_config=UserConfig(adapter="codex"),
        )
    msg = str(excinfo.value)
    # AC14 message contract:
    assert "not supported with your configured adapter" in msg
    assert "codex" in msg
    assert pack.name in msg  # pack name in message
    assert "claude-code" in msg  # admissible set listed
    # Three escape hatches (no --scope here, since the pack is the limit):
    assert "--adapter" in msg
    assert "agentbundle config set adapter" in msg
    assert "agentbundle config unset adapter" in msg


# ---------------------------------------------------------------------------
# state_adapter set but inadmissible: pre-flight skips entirely
# ---------------------------------------------------------------------------


def test_state_inadmissible_pre_flight_skips(
    tmp_path: Path, fake_home: Path
) -> None:
    """When state_adapter is set (admissible or not), the pre-flight
    is a no-op — user-config doesn't fire AC14 for a state-pin
    problem. Setup: no probe-detectable IDE markers under fake_home,
    so Step 4 falls through to `allowed_adapters[0]`. upgrade.py's
    cross-adapter refusal is the layer that would then raise — but
    `_resolve_target_adapter` itself returns successfully here."""
    pack = _pack(tmp_path)
    # Important: no .claude/ / .codex/ / .kiro/ created. Probe finds nothing.
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=["kiro"],
        contract_version="0.7",
        state_adapter="claude-code",
        user_config=UserConfig(adapter="codex"),
    )
    # Step 2 falls through (claude-code not in ["kiro"]).
    # Pre-flight skips (state_adapter not None).
    # Step 4: probe finds nothing → DEFAULT_ADAPTER ("claude-code")
    # not in ["kiro"] → allowed_adapters[0] = "kiro".
    assert result == "kiro"


# ---------------------------------------------------------------------------
# user_config=None and user_config defaulted to None: backward-compat
# ---------------------------------------------------------------------------


def test_default_user_config_none_matches_legacy_behavior(
    tmp_path: Path, fake_home: Path
) -> None:
    """The new kwarg defaults to None, so existing call sites that
    don't pass it see the same behavior as today."""
    pack = _pack(tmp_path)
    # No user-config argument at all → defaults to None → pre-flight
    # is a no-op → Step 5 returns DEFAULT_ADAPTER.
    result = _resolve_target_adapter(
        pack,
        scope="user",
        allowed_adapters=None,
        contract_version=None,
    )
    from agentbundle.scope import DEFAULT_ADAPTER

    assert result == DEFAULT_ADAPTER
