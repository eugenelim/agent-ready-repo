"""T17: scope-resolution helper + allowed-scopes refusal + ~-expansion.

Verifies AC #(RFC-0004): scope resolution precedence, the refusal text
shape on `allowed-scopes` violation, and `~`-expansion's two failure
modes.
"""

from __future__ import annotations

import pytest

from agentbundle import scope


# ---------------------------------------------------------------------------
# resolve() — precedence (CLI > pack > builtin)
# ---------------------------------------------------------------------------


def test_resolve_uses_builtin_when_pack_omits_default():
    """v0.1 pack: pack_install is None; builtin 'repo' wins."""
    assert scope.resolve(None, None) == "repo"


def test_resolve_uses_pack_default_when_no_cli_flag():
    install = {"default-scope": "user", "allowed-scopes": ["user"]}
    assert scope.resolve(None, install) == "user"


def test_resolve_cli_flag_overrides_pack_default():
    install = {"default-scope": "user", "allowed-scopes": ["repo", "user"]}
    assert scope.resolve("repo", install) == "repo"


def test_resolve_implied_allowed_scopes_from_default():
    """When allowed-scopes is omitted, the implied default is [default-scope]."""
    install = {"default-scope": "user"}  # no allowed-scopes
    # Implied allowed: ["user"]; CLI flag "user" passes; "repo" refused.
    assert scope.resolve("user", install) == "user"
    with pytest.raises(scope.ScopeRefused):
        scope.resolve("repo", install)


# ---------------------------------------------------------------------------
# resolve() — refusal shape
# ---------------------------------------------------------------------------


def test_resolve_refuses_with_pack_name_requested_and_allowed():
    install = {"default-scope": "repo", "allowed-scopes": ["repo"]}
    with pytest.raises(scope.ScopeRefused) as ei:
        scope.resolve("user", install, pack_name="demo")
    assert ei.value.pack_name == "demo"
    assert ei.value.requested == "user"
    assert ei.value.allowed == ["repo"]
    # The exception's string carries the three pieces the spec stderr names.
    msg = str(ei.value)
    assert "demo" in msg
    assert "'user'" in msg
    assert "repo" in msg


def test_resolve_v01_pack_only_accepts_repo():
    """A v0.1 pack (pack_install=None) treats allowed-scopes as ['repo']."""
    assert scope.resolve("repo", None) == "repo"
    with pytest.raises(scope.ScopeRefused) as ei:
        scope.resolve("user", None, pack_name="legacy")
    assert ei.value.allowed == ["repo"]


# ---------------------------------------------------------------------------
# resolve_user_root() — ~-expansion failure modes
# ---------------------------------------------------------------------------


def test_resolve_user_root_returns_path_when_home_set(tmp_path):
    """The happy path: home is set, returns the Path."""
    result = scope.resolve_user_root(home=tmp_path)
    assert result == tmp_path


def test_resolve_user_root_refuses_root_slash():
    """`$HOME=/`: corporate sandbox path resolves to root — refused."""
    from pathlib import Path

    with pytest.raises(scope.UserScopeUnresolvable):
        scope.resolve_user_root(home=Path("/"))


def test_resolve_user_root_refuses_literal_tilde(monkeypatch):
    """When ``expanduser`` returns literal ``~`` (no $HOME and no
    pwd entry), the helper refuses.

    On POSIX, ``Path("~").expanduser()`` falls back to
    ``pwd.getpwuid(os.getuid()).pw_dir`` when ``$HOME`` is unset, so
    unset-HOME alone won't produce a literal ``"~"``. We simulate the
    actual failure contract by both unsetting ``$HOME`` *and* forcing
    ``pwd.getpwuid`` to raise ``KeyError`` so the fallback fails and
    ``expanduser`` returns the bare ``"~"`` per Python's documented
    semantics.
    """
    import os
    import pwd

    monkeypatch.delenv("HOME", raising=False)
    monkeypatch.setattr(pwd, "getpwuid", lambda _uid: (_ for _ in ()).throw(KeyError("no entry")))

    with pytest.raises(scope.UserScopeUnresolvable):
        # Pass None so the real expanduser runs against the patched env.
        scope.resolve_user_root(home=None)


# ---------------------------------------------------------------------------
# safety.write_jailed extension: scope + allowed_prefixes
# ---------------------------------------------------------------------------


def test_write_jailed_repo_scope_unchanged(tmp_path):
    """The default scope behaviour (repo, no prefixes) is unchanged."""
    from agentbundle import safety

    safety.write_jailed(tmp_path, "AGENTS.md", "hi")
    assert (tmp_path / "AGENTS.md").read_text() == "hi"


def test_write_jailed_user_scope_requires_prefixes(tmp_path):
    from agentbundle import safety

    with pytest.raises(TypeError, match="allowed_prefixes is required"):
        safety.write_jailed(tmp_path, ".claude/foo", "hi", scope="user")


def test_write_jailed_user_scope_accepts_prefix_match(tmp_path):
    from agentbundle import safety

    safety.write_jailed(
        tmp_path,
        ".claude/skills/foo/SKILL.md",
        "hi",
        scope="user",
        allowed_prefixes=[".claude/", ".agentbundle/"],
    )
    assert (tmp_path / ".claude" / "skills" / "foo" / "SKILL.md").read_text() == "hi"


def test_write_jailed_user_scope_accepts_second_prefix(tmp_path):
    from agentbundle import safety

    safety.write_jailed(
        tmp_path,
        ".agentbundle/state.toml",
        'schema-version = "0.2"\n',
        scope="user",
        allowed_prefixes=[".claude/", ".agentbundle/"],
    )
    assert (tmp_path / ".agentbundle" / "state.toml").exists()


def test_write_jailed_user_scope_refuses_outside_prefix(tmp_path):
    """A path under ~ but outside the declared prefix list is refused."""
    from agentbundle import safety

    with pytest.raises(safety.PathJailError) as ei:
        safety.write_jailed(
            tmp_path,
            "Documents/foo.txt",
            "hi",
            scope="user",
            allowed_prefixes=[".claude/", ".agentbundle/"],
        )
    assert "not within any declared prefix zone" in str(ei.value)
    assert "scope=user" in str(ei.value)


def test_write_jailed_user_scope_prefix_directory_boundary(tmp_path):
    """`.claude/` prefix must not accidentally match `.claudefoo/...`."""
    from agentbundle import safety

    with pytest.raises(safety.PathJailError):
        safety.write_jailed(
            tmp_path,
            ".claudefoo/leak.txt",
            "hi",
            scope="user",
            allowed_prefixes=[".claude/"],
        )
