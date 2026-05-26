"""Unit tests for the six-step (0–5) ``_resolve_target_adapter``
lookup (RFC-0011 substrate; RFC-0012 widens to scope-branched form).
Covers spec AC6, AC10, AC10a, AC10b, AC15, AC21 from RFC-0011 plus
the new RFC-0012 cases (probe asymmetry at repo scope, scope-conditional
step-1 subcheck, etc.).

The module's filename is preserved at its pre-RFC-0012 name (the
rename of the file itself is gated by *Ask first* in the spec's
*Boundaries* section); the production function it tests is now
``_resolve_target_adapter`` with an explicit ``scope`` kwarg. A
module-local shim pins ``scope="user"`` so the user-scope test
bodies keep their pre-rename shape.

Each test isolates the resolver behind a stubbed ``Path.home()`` and
(for publisher-drift) a stubbed contract. The tests do NOT call into
install or upgrade end-to-end — those are covered by T8's integration
suite. The resolver itself is pure-functional modulo ``Path.home()``
and the bundled contract read.
"""

from __future__ import annotations

import pytest

from pathlib import Path

from agentbundle.commands.install import (
    _AdapterResolutionRefused,
    _resolve_target_adapter,
)


def _resolve_user_scope_target_adapter(*args, **kwargs):
    """Test-local shim. RFC-0012 renamed the production helper to
    ``_resolve_target_adapter`` with an explicit ``scope`` kwarg; the
    test module's filename preserves the pre-rename function name
    (gated by *Ask first* in the spec's *Boundaries* section), so we
    pin ``scope="user"`` here so existing test bodies keep their pre-
    rename shape. The new ``scope="repo"`` parametrise cases call
    ``_resolve_target_adapter`` directly so the scope is visible at
    the call site."""
    return _resolve_target_adapter(*args, scope="user", **kwargs)


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
    assert result == "claude-code"  # DEFAULT_ADAPTER


def test_greenfield_monkeypatch_default_to_kiro(tmp_path, fake_home, monkeypatch):
    pack = _make_pack(tmp_path)
    monkeypatch.setattr(
        "agentbundle.scope.DEFAULT_ADAPTER", "kiro"
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
        "agentbundle.scope.DEFAULT_ADAPTER", "codex"
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
            contract_version="0.7",
        )
    msg = str(exc_info.value)
    assert "--adapter copilot not admitted as a user-scope-capable adapter" in msg
    # Message references the bundled contract version, which RFC-0012 +
    # RFC-0013 co-bumped to v0.7.
    assert "v0.7" in msg


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


def test_legacy_v05_pack_with_agents_returns_default_adapter(tmp_path, fake_home):
    """Step 5 returns ``DEFAULT_ADAPTER`` uniformly — the pre-fix
    agents-presence ``"kiro"`` hardcode assumed a single-IDE world
    and ignored downstream-rebranded constants."""
    pack = _make_pack(tmp_path, with_agents=True)
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=None,
        contract_version="0.5",
    )
    assert result == "claude-code"


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
    """v0.6 pack omitting allowed-adapters drops to step 5, which now
    returns ``DEFAULT_ADAPTER`` regardless of `.apm/agents/` presence."""
    pack = _make_pack(tmp_path, with_agents=True)
    (fake_home / ".claude").mkdir()
    result = _resolve_user_scope_target_adapter(
        pack,
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
    )
    assert result == "claude-code"


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


# ---------------------------------------------------------------------------
# RFC-0012: repo-scope branches (steps 0, 1, 4, 5)
# ---------------------------------------------------------------------------


def _make_pack_v07(tmp_path: Path, name: str = "demo", with_agents: bool = False) -> Path:
    """Materialise a pack.toml carrying [pack.adapter-contract] version
    = "0.7" — the resolver consults the pack directory through callers,
    but the directory itself just needs the .apm/ structure for the
    legacy-heuristic path; tests pass contract_version explicitly so
    no on-disk pack.toml read is required.
    """
    return _make_pack(tmp_path, name=name, with_agents=with_agents)


@pytest.mark.parametrize(
    "adapter,expected",
    [
        ("claude-code", "claude-code"),
        ("kiro", "kiro"),
        ("codex", "codex"),
        ("copilot", "copilot"),
    ],
)
def test_repo_scope_adapter_flag_admits_all_shipped_adapters(
    tmp_path, fake_home, adapter, expected
):
    """At repo scope, every shipped adapter is admissible via --adapter
    (no user-scope-capability subcheck). Copilot is the load-bearing
    case — admissible at repo scope, refused at user scope."""
    pack = _make_pack_v07(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter=adapter,
        allowed_adapters=None,
        contract_version="0.7",
    )
    assert result == expected


def test_step1_copilot_admitted_at_repo_user_refused(tmp_path, fake_home):
    """Spec AC9 / AC30 — scope-conditional subcheck at step 1.
    Same pack at both scopes: copilot admits at repo, refuses at user
    with pinned v0.7 wording."""
    pack = _make_pack_v07(tmp_path)
    # Repo scope: admitted.
    assert (
        _resolve_target_adapter(
            pack,
            scope="repo",
            adapter="copilot",
            allowed_adapters=None,
            contract_version="0.7",
        )
        == "copilot"
    )
    # User scope: refused with pinned wording.
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        _resolve_target_adapter(
            pack,
            scope="user",
            adapter="copilot",
            allowed_adapters=None,
            contract_version="0.7",
        )
    msg = str(exc_info.value)
    assert "--adapter copilot not admitted as a user-scope-capable adapter" in msg
    assert "v0.7" in msg


def test_repo_scope_does_not_probe_dot_claude(tmp_path, fake_home):
    """Load-bearing asymmetry — RFC-0012 § *Alternatives* #4 rejects
    symmetric probing. Even with `<repo>/.claude/` populated, an
    explicit `--adapter kiro` at repo scope returns kiro."""
    pack = _make_pack_v07(tmp_path)
    # Note: probe is keyed off Path.home() (user-scope semantics); at
    # repo scope the resolver doesn't probe at all. We populate the
    # fake home anyway as a regression guard against accidental
    # probe-at-repo-scope re-introductions.
    (fake_home / ".claude").mkdir()
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter="kiro",
        allowed_adapters=None,
        contract_version="0.7",
    )
    assert result == "kiro"


@pytest.mark.parametrize("scope", ["user", "repo"])
def test_step0_publisher_drift_scope_uniform(tmp_path, fake_home, scope):
    """Spec AC9 step 0 — publisher-vs-installer drift refusal is
    scope-uniform modulo the <verb> prefix; the user-scope-capability
    subcheck does NOT fire at repo scope (Copilot is admissible there).
    Here we assert the shipped-adapter check fires at both scopes."""
    pack = _make_pack_v07(tmp_path)
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        _resolve_target_adapter(
            pack,
            scope=scope,
            adapter=None,
            allowed_adapters=["nonexistent-adapter"],
            contract_version="0.7",
        )
    msg = str(exc_info.value)
    assert "allowed-adapter 'nonexistent-adapter'" in msg
    assert "not admitted by adapter contract" in msg


def test_step0_copilot_admitted_at_repo_in_allowed_adapters(tmp_path, fake_home):
    """RFC-0012: at repo scope, a pack declaring copilot in
    allowed-adapters passes step 0's user-scope-capability subcheck
    skip (the subcheck doesn't fire). At user scope the same input
    refuses."""
    pack = _make_pack_v07(tmp_path)
    # Repo scope: declared copilot survives step 0; --adapter selects.
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter="copilot",
        allowed_adapters=["claude-code", "copilot"],
        contract_version="0.7",
    )
    assert result == "copilot"
    # User scope: step 0's subcheck fires.
    with pytest.raises(_AdapterResolutionRefused) as exc_info:
        _resolve_target_adapter(
            pack,
            scope="user",
            adapter="copilot",
            allowed_adapters=["claude-code", "copilot"],
            contract_version="0.7",
        )
    assert "does not declare a user-scope root" in str(exc_info.value)


def test_repo_scope_greenfield_returns_default_adapter(tmp_path, fake_home):
    """Spec AC9 step 4 (repo branch) — no --adapter, no probe; returns
    DEFAULT_ADAPTER if in allowed_adapters."""
    pack = _make_pack_v07(tmp_path)
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.7",
    )
    assert result == "claude-code"


def test_repo_scope_greenfield_falls_back_to_first_when_default_absent(
    tmp_path, fake_home, monkeypatch
):
    """When DEFAULT_ADAPTER isn't in the pack's set, repo
    scope returns allowed_adapters[0] (same shape as user scope)."""
    pack = _make_pack_v07(tmp_path)
    monkeypatch.setattr("agentbundle.scope.DEFAULT_ADAPTER", "codex")
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.7",
    )
    assert result == "claude-code"


def test_repo_scope_legacy_heuristic_for_pre_v07_pack(tmp_path, fake_home):
    """Spec AC9 step 5 — `< v0.7` pack omitting allowed-adapters falls
    through to the legacy heuristic at repo scope. Returns
    ``DEFAULT_ADAPTER`` regardless of `.apm/agents/` presence so a
    downstream-rebranded constant is honored uniformly."""
    pack = _make_pack_v07(tmp_path, with_agents=True)
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
    )
    assert result == "claude-code"

    pack_no_agents = _make_pack_v07(tmp_path / "alt", with_agents=False)
    result_no_agents = _resolve_target_adapter(
        pack_no_agents,
        scope="repo",
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
    )
    assert result_no_agents == "claude-code"


def test_repo_scope_legacy_heuristic_honors_monkey_patched_default(
    tmp_path, fake_home, monkeypatch
):
    """Step 5 must follow a downstream-rebranded ``DEFAULT_ADAPTER``
    uniformly — both with and without `.apm/agents/`. Regression test
    for the pre-fix hardcodes that returned ``"claude-code"`` /
    ``"kiro"`` literally and ignored the monkey-patch documented at
    ``agentbundle.scope:45-47``."""
    import agentbundle.scope as scope_mod

    monkeypatch.setattr(scope_mod, "DEFAULT_ADAPTER", "kiro")

    pack_no_agents = _make_pack_v07(tmp_path, with_agents=False)
    result_no_agents = _resolve_target_adapter(
        pack_no_agents,
        scope="repo",
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
    )
    assert result_no_agents == "kiro"

    monkeypatch.setattr(scope_mod, "DEFAULT_ADAPTER", "codex")
    pack_with_agents = _make_pack_v07(tmp_path / "alt", with_agents=True)
    result_with_agents = _resolve_target_adapter(
        pack_with_agents,
        scope="repo",
        adapter=None,
        allowed_adapters=None,
        contract_version="0.6",
    )
    assert result_with_agents == "codex"


def test_repo_scope_state_hint_short_circuit(tmp_path, fake_home):
    """Spec AC9 step 2 — state-hint short-circuit (AC10b parity at
    repo scope). Install under kiro; populate `<repo>/.claude/`;
    upgrade with state_adapter=kiro returns kiro (no cross-adapter
    refusal)."""
    pack = _make_pack_v07(tmp_path)
    # Populate ~/.claude/ as a sanity probe — irrelevant at repo
    # scope per the asymmetry, but matches RFC-0011's upgrade-side
    # scenario.
    (fake_home / ".claude").mkdir()
    result = _resolve_target_adapter(
        pack,
        scope="repo",
        adapter=None,
        allowed_adapters=["claude-code", "kiro"],
        contract_version="0.7",
        state_adapter="kiro",
        command_name="upgrade",
    )
    assert result == "kiro"


# ---------------------------------------------------------------------------
# RFC-0012: DEFAULT_ADAPTER rename + deprecation alias (AC18-AC19)
# ---------------------------------------------------------------------------


def test_default_adapter_value_unchanged():
    """The renamed constant carries the same value (claude-code)."""
    from agentbundle.scope import DEFAULT_ADAPTER

    assert DEFAULT_ADAPTER == "claude-code"


def test_deprecation_alias_fires_warning():
    """Accessing the old name via getattr raises DeprecationWarning
    and returns the new constant's value."""
    import warnings

    import agentbundle.scope as scope_mod

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = getattr(scope_mod, "DEFAULT_USER_SCOPE_ADAPTER")
    assert value == scope_mod.DEFAULT_ADAPTER
    assert any(issubclass(w.category, DeprecationWarning) for w in caught), (
        "expected DeprecationWarning on access of DEFAULT_USER_SCOPE_ADAPTER"
    )


def test_default_adapter_direct_access_does_not_warn():
    """Direct access to DEFAULT_ADAPTER must NOT warn (PEP 562
    ``__getattr__`` fires only on missing attributes)."""
    import warnings

    import agentbundle.scope as scope_mod

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = scope_mod.DEFAULT_ADAPTER
    assert not any(
        issubclass(w.category, DeprecationWarning) for w in caught
    ), "DEFAULT_ADAPTER access raised an unexpected DeprecationWarning"
