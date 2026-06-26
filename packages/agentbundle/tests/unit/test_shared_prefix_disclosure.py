"""T6 (RFC-0052 Decision 7): the install-time cross-adapter disclosure rail.

After an install that writes to a `shared` prefix, stderr names the prefix's
other shipped cohort adapters and states the skills-shared / private-needs-own-
install boundary, scope-aware.
"""

from __future__ import annotations

from agentbundle.commands.install import _shared_prefix_disclosure


def test_no_shared_prefix_touched_returns_none():
    # Only private paths written → no disclosure.
    out = _shared_prefix_disclosure(
        "research", "claude-code", "user", {".claude/skills/x/SKILL.md"}
    )
    assert out is None


def test_user_scope_codex_names_other_cohort_adapters():
    out = _shared_prefix_disclosure(
        "research", "codex", "user", {".agents/skills/x/SKILL.md"}
    )
    assert out is not None
    assert out.startswith("Installed research for codex (user).")
    # Skills line names the cohort's *other* shipped adapters (registry
    # order, minus the installed adapter).
    assert "Skills → ~/.agents/skills/ — also read by cursor, gemini, copilot." in out
    # Private boundary line, scope-aware home + native dir.
    assert "Hooks & subagents → ~/.codex/ — codex only" in out
    assert "install those" in out and "separately to get them there." in out


def test_repo_scope_renders_repo_relative_paths():
    out = _shared_prefix_disclosure(
        "research", "cursor", "repo", {".agents/skills/x/SKILL.md"}
    )
    assert out is not None
    assert "Skills → .agents/skills/ — also read by codex, gemini, copilot." in out
    # No leading ~ at repo scope.
    assert "~/" not in out
    assert "Hooks & subagents → .cursor/ — cursor only" in out


def test_copilot_native_dir_is_scope_specific():
    # copilot's native home is .github/ at repo, .copilot/ at user.
    repo = _shared_prefix_disclosure(
        "research", "copilot", "repo", {".agents/skills/x/SKILL.md"}
    )
    user = _shared_prefix_disclosure(
        "research", "copilot", "user", {".agents/skills/x/SKILL.md"}
    )
    assert "Hooks & subagents → .github/ — copilot only" in repo
    assert "Hooks & subagents → ~/.copilot/ — copilot only" in user


def test_kiro_cohort_disclosure():
    out = _shared_prefix_disclosure(
        "research", "kiro-cli", "user", {".kiro/skills/x/SKILL.md"}
    )
    assert "also read by kiro-ide." in out
