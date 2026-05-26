"""T2 unit tests for the six-step `_resolve_user_scope_target_adapter`
lookup (RFC-0011 / pack-allowed-adapters spec AC6, AC10, AC10a, AC10b,
AC15, AC21).

Each test isolates the resolver behind a stubbed `Path.home()` and (for
publisher-drift) a stubbed contract. The tests do NOT call into install
or upgrade end-to-end — those are covered by T8's integration suite.
The resolver itself is pure-functional modulo `Path.home()` and the
bundled contract read.
"""

from __future__ import annotations

import pytest

from pathlib import Path

from agentbundle.commands.install import (
    _AdapterResolutionRefused,
    _resolve_user_scope_target_adapter,
)


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Provide an empty `$HOME` and stub `Path.home()` to point at it."""
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


def _make_pack(tmp_path: Path, name: str = "demo", with_agents: bool = False) -> Path:
    pack = tmp_path / "src" / name
    (pack / ".apm").mkdir(parents=True)
    if with_agents:
        agents = pack / ".apm" / "agents"
        agents.mkdir()
        (agents / "alpha.md").write_text("dummy", encoding="utf-8")
    return pack


# ---------------------------------------------------------------------------
# CLI-home probes — each adapter populated alone
# ---------------------------------------------------------------------------


def test_probe_claude_only_returns_claude_code(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    (fake_home / ".claude").mkdir()
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
    )
    assert result == "claude-code"


def test_probe_kiro_only_returns_kiro(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    (fake_home / ".kiro").mkdir()
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
    )
    assert result == "kiro"


def test_probe_codex_dot_codex_only_returns_codex(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    (fake_home / ".codex").mkdir()
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
    )
    assert result == "codex"


def test_probe_codex_via_agents_skills_returns_codex(tmp_path, fake_home):
    """OR-probe: `.agents/skills/` alone (no `.codex/`) still resolves to codex."""
    pack = _make_pack(tmp_path)
    (fake_home / ".agents" / "skills").mkdir(parents=True)
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
    )
    assert result == "codex"


# ---------------------------------------------------------------------------
# First-match-wins (declared order)
# ---------------------------------------------------------------------------


def test_first_match_wins_declared_order(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    (fake_home / ".claude").mkdir()
    (fake_home / ".kiro").mkdir()
    # Declared order ["claude-code", "kiro", ...] → claude-code wins.
    assert _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
    ) == "claude-code"
    # Reordered → kiro wins.
    assert _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["kiro", "claude-code", "codex"],
        contract_version="0.6",
    ) == "kiro"


# ---------------------------------------------------------------------------
# Greenfield fallback — no CLI home populated
# ---------------------------------------------------------------------------


def test_greenfield_returns_default_when_default_in_pack_list(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.6",
    )
    assert result == "claude-code"  # DEFAULT_USER_SCOPE_ADAPTER


def test_greenfield_monkeypatch_default_to_kiro(tmp_path, fake_home, monkeypatch):
    pack = _make_pack(tmp_path)
    monkeypatch.setattr(
        "agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER", "kiro"
    )
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.6",
    )
    assert result == "kiro"


def test_greenfield_falls_back_to_first_when_default_not_in_pack_list(
    tmp_path, fake_home, monkeypatch
):
    pack = _make_pack(tmp_path)
    monkeypatch.setattr(
        "agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER", "codex"
    )
    # codex not in pack's list — falls back to allowed_adapters[0].
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.6",
    )
    assert result == "claude-code"


# ---------------------------------------------------------------------------
# --adapter override
# ---------------------------------------------------------------------------


def test_adapter_flag_overrides_probe(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    (fake_home / ".claude").mkdir()
    # claude-code would be the probe winner; --adapter kiro overrides.
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter="kiro",
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
    )
    assert result == "kiro"


def test_adapter_flag_refused_not_in_allowed_adapters(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        _resolve_user_scope_target_adapter(
            pack,
            adapter="codex",
            allowed_adapters=["claude-code", "kiro"],
            contract_version="0.6",
        )
    assert "--adapter codex not in pack's allowed-adapters set" in str(exc_info.value)


def test_adapter_flag_refused_not_user_scope_capable(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        # Pack omits allowed-adapters; copilot is shipped but has no user-scope.
        _resolve_user_scope_target_adapter(
            pack,
            adapter="copilot",
            allowed_adapters=None,
            contract_version="0.6",
        )
    msg = str(exc_info.value)
    assert "--adapter copilot not admitted as a user-scope-capable adapter" in msg
    assert "v0.6" in msg


# ---------------------------------------------------------------------------
# State-hint short-circuit (AC10b)
# ---------------------------------------------------------------------------


def test_state_hint_returns_recorded_adapter(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    # Both ~/.claude/ AND ~/.kiro/ populated; state recorded "claude-code".
    (fake_home / ".claude").mkdir()
    (fake_home / ".kiro").mkdir()
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro", "codex"],
        contract_version="0.6",
        state_adapter="claude-code",
    )
    assert result == "claude-code"


def test_state_hint_ignored_when_not_in_allowed_adapters(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    (fake_home / ".kiro").mkdir()
    # Pack dropped support for the recorded adapter; fall through to probe.
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["kiro", "codex"],
        contract_version="0.6",
        state_adapter="claude-code",  # not in list
    )
    assert result == "kiro"  # probe winner


def test_state_hint_with_omitted_allowed_adapters_checks_user_capable(
    tmp_path, fake_home
):
    pack = _make_pack(tmp_path)
    # Pack omits allowed-adapters; state-hint must be user-scope-capable.
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
        state_adapter="codex",  # user-scope-capable
    )
    assert result == "codex"


# ---------------------------------------------------------------------------
# Legacy heuristic (< 0.6 packs and v0.6 packs omitting allowed-adapters)
# ---------------------------------------------------------------------------


def test_legacy_v05_pack_with_agents_returns_kiro(tmp_path, fake_home):
    pack = _make_pack(tmp_path, with_agents=True)
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=None,
        contract_version="0.5",
    )
    assert result == "kiro"


def test_legacy_v05_pack_without_agents_returns_claude_code(tmp_path, fake_home):
    pack = _make_pack(tmp_path, with_agents=False)
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=None,
        contract_version="0.5",
    )
    assert result == "claude-code"


def test_v06_pack_omitting_allowed_adapters_uses_legacy_heuristic(tmp_path, fake_home):
    pack = _make_pack(tmp_path, with_agents=True)
    (fake_home / ".claude").mkdir()
    # v0.6 but no allowed-adapters → legacy heuristic, agents present.
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
    )
    assert result == "kiro"


def test_stray_allowed_adapters_on_v05_pack_uses_legacy(tmp_path, fake_home):
    """A v0.5 pack accidentally declaring allowed-adapters still falls
    through to the legacy heuristic — the contract-version gate at step 3
    keys on the version, not on field presence."""
    pack = _make_pack(tmp_path, with_agents=True)
    (fake_home / ".kiro").mkdir()
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.5",
    )
    # Legacy path with agents → kiro.
    assert result == "kiro"


# ---------------------------------------------------------------------------
# Publisher-vs-installer drift (AC15)
# ---------------------------------------------------------------------------


def test_publisher_drift_refused(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        _resolve_user_scope_target_adapter(
            pack,
            adapter=None,
            allowed_adapters=["claude-code", "windsurf"],  # windsurf not shipped
            contract_version="0.6",
        )
    msg = str(exc_info.value)
    assert "declares allowed-adapter 'windsurf'" in msg
    assert "not admitted by adapter contract" in msg


def test_publisher_drift_uses_command_name_prefix(tmp_path, fake_home):
    pack = _make_pack(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        _resolve_user_scope_target_adapter(
            pack,
            adapter=None,
            allowed_adapters=["windsurf"],
            contract_version="0.6",
            command_name="upgrade",
        )
    assert str(exc_info.value).startswith("upgrade: pack ")
