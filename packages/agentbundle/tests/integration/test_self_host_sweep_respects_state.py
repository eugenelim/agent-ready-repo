"""Regression: self-host orphan sweep must not delete state-tracked skills.

When `project_packs` is called (as `catalogue self-host --write` does) on a
repo that also has skills installed by `agentbundle install`, the orphan sweep
must preserve any skill directory whose name appears in `.agentbundle-state.toml`.

Root cause: `_sweep_skill_orphans` (claude_code / kiro) and the inline sweep
(codex) built `expected_names` from only the packs passed to `project_packs`.
Any skill installed from an external catalogue had a name not in that set and
was silently deleted. The fix adds state-file-recorded names to `expected_names`
before calling `sweep_orphans`.

These tests exercise all three adapters by calling `project_packs` directly
with an empty pack list (simulating self-host packs that ship no skills) and a
pre-seeded state file that claims an externally-installed skill.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATE_TEMPLATE = textwrap.dedent("""\
    schema-version = "0.4"

    [pack."{pack_name}".adapters."{adapter}"]
    installed-version = "1.0.0"
    scope = "repo"

    [pack."{pack_name}".adapters."{adapter}".files]
    "{relpath}" = {{sha = "aabbccdd"}}
""")


def _write_state(root: Path, *, pack_name: str, adapter: str, relpath: str) -> None:
    (root / ".agentbundle-state.toml").write_text(
        _STATE_TEMPLATE.format(pack_name=pack_name, adapter=adapter, relpath=relpath),
        encoding="utf-8",
        newline="\n",
    )


def _minimal_contract(adapter_key: str, target_path: str) -> dict:
    return {
        "adapter": {
            adapter_key: {
                "projection": [
                    {
                        "primitive": "skill",
                        "mode": "direct-directory",
                        "target-path": target_path,
                    }
                ]
            }
        },
        "primitive": {
            "skill": {"source-path": ".apm/skills/"}
        },
    }


# ---------------------------------------------------------------------------
# claude_code adapter
# ---------------------------------------------------------------------------


def test_claude_code_sweep_preserves_state_tracked_skill(tmp_path: Path) -> None:
    """A skill recorded in the state file survives a `project_packs` call
    that does not include the pack that owns it."""
    from agentbundle.build.adapters.claude_code import project_packs

    # Pre-seed the output root with the external skill directory.
    skill_dir = tmp_path / ".claude" / "skills" / "external-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# External\n", encoding="utf-8", newline="\n")

    # Record it in the state file (simulates a prior `agentbundle install`).
    _write_state(
        tmp_path,
        pack_name="external-pack",
        adapter="claude-code",
        relpath=".claude/skills/external-skill/SKILL.md",
    )

    contract = _minimal_contract("claude-code", ".claude/skills/")
    # Call with an empty pack list — as self-host does when it projects only
    # the repo's own packs that happen to ship no skills.
    project_packs([], contract, tmp_path)

    assert skill_dir.exists(), (
        "project_packs deleted a skill dir recorded in .agentbundle-state.toml; "
        "the orphan sweep must not remove state-tracked skills"
    )
    assert (skill_dir / "SKILL.md").exists(), "skill content must survive"


def test_claude_code_sweep_removes_untracked_orphan(tmp_path: Path) -> None:
    """A skill directory with NO state record IS an orphan and must be swept."""
    from agentbundle.build.adapters.claude_code import project_packs

    orphan_dir = tmp_path / ".claude" / "skills" / "orphan-skill"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "SKILL.md").write_text("# Orphan\n", encoding="utf-8", newline="\n")

    # No state file → orphan-skill has no owner.
    contract = _minimal_contract("claude-code", ".claude/skills/")
    project_packs([], contract, tmp_path)

    assert not orphan_dir.exists(), (
        "project_packs should have swept the untracked skill directory"
    )


# ---------------------------------------------------------------------------
# kiro adapter
# ---------------------------------------------------------------------------


def test_kiro_sweep_preserves_state_tracked_skill(tmp_path: Path) -> None:
    from agentbundle.build.adapters.kiro import project_packs

    skill_dir = tmp_path / ".kiro" / "skills" / "external-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# External\n", encoding="utf-8", newline="\n")

    _write_state(
        tmp_path,
        pack_name="external-pack",
        adapter="kiro",
        relpath=".kiro/skills/external-skill/SKILL.md",
    )

    contract = _minimal_contract("kiro", ".kiro/skills/")
    project_packs([], contract, tmp_path)

    assert skill_dir.exists(), (
        "kiro project_packs deleted a state-tracked skill directory"
    )


def test_kiro_sweep_removes_untracked_orphan(tmp_path: Path) -> None:
    from agentbundle.build.adapters.kiro import project_packs

    orphan_dir = tmp_path / ".kiro" / "skills" / "orphan-skill"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "SKILL.md").write_text("# Orphan\n", encoding="utf-8", newline="\n")

    contract = _minimal_contract("kiro", ".kiro/skills/")
    project_packs([], contract, tmp_path)

    assert not orphan_dir.exists(), (
        "kiro project_packs should have swept the untracked skill directory"
    )


# ---------------------------------------------------------------------------
# codex adapter
# ---------------------------------------------------------------------------


def test_codex_sweep_preserves_state_tracked_skill(tmp_path: Path) -> None:
    from agentbundle.build.adapters.codex import project_packs

    skill_dir = tmp_path / ".agents" / "skills" / "external-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# External\n", encoding="utf-8", newline="\n")

    _write_state(
        tmp_path,
        pack_name="external-pack",
        adapter="codex",
        relpath=".agents/skills/external-skill/SKILL.md",
    )

    contract = _minimal_contract("codex", ".agents/skills/")
    project_packs([], contract, tmp_path)

    assert skill_dir.exists(), (
        "codex project_packs deleted a state-tracked skill directory"
    )


def test_codex_sweep_removes_untracked_orphan(tmp_path: Path) -> None:
    from agentbundle.build.adapters.codex import project_packs

    orphan_dir = tmp_path / ".agents" / "skills" / "orphan-skill"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "SKILL.md").write_text("# Orphan\n", encoding="utf-8", newline="\n")

    contract = _minimal_contract("codex", ".agents/skills/")
    project_packs([], contract, tmp_path)

    assert not orphan_dir.exists(), (
        "codex project_packs should have swept the untracked skill directory"
    )


# ---------------------------------------------------------------------------
# Degradation: legacy / malformed state file → sweep proceeds as before
# ---------------------------------------------------------------------------


def test_claude_code_degrades_on_legacy_state(tmp_path: Path) -> None:
    """A legacy (wrong schema-version) state file must not prevent the sweep
    from removing genuine orphans — the fix degrades to the pre-fix behavior."""
    from agentbundle.build.adapters.claude_code import project_packs

    orphan_dir = tmp_path / ".claude" / "skills" / "orphan-skill"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "SKILL.md").write_text("# Orphan\n", encoding="utf-8", newline="\n")

    # Write a legacy state file (schema-version "0.3" is not the current "0.4").
    (tmp_path / ".agentbundle-state.toml").write_text(
        'schema-version = "0.3"\n',
        encoding="utf-8",
        newline="\n",
    )

    contract = _minimal_contract("claude-code", ".claude/skills/")
    project_packs([], contract, tmp_path)

    # Orphan must still be swept — legacy state → empty protection set.
    assert not orphan_dir.exists(), (
        "a legacy state file must not prevent orphan sweep from running"
    )


def test_claude_code_degrades_on_malformed_state(tmp_path: Path) -> None:
    """A syntactically invalid state file must not prevent orphan sweep."""
    from agentbundle.build.adapters.claude_code import project_packs

    orphan_dir = tmp_path / ".claude" / "skills" / "orphan-skill"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "SKILL.md").write_text("# Orphan\n", encoding="utf-8", newline="\n")

    (tmp_path / ".agentbundle-state.toml").write_text(
        "this is not valid TOML ][[\n",
        encoding="utf-8",
        newline="\n",
    )

    contract = _minimal_contract("claude-code", ".claude/skills/")
    project_packs([], contract, tmp_path)

    assert not orphan_dir.exists(), (
        "a malformed state file must not prevent orphan sweep from running"
    )


# ---------------------------------------------------------------------------
# Dry-run / shadow clone consistency (Blocker 1 regression guard)
# ---------------------------------------------------------------------------


def test_dry_run_consistent_with_write_for_state_tracked_skill(tmp_path: Path) -> None:
    """catalogue self-host --check must not report drift for a skill that
    --write would preserve.  The shadow clone must include the state file so
    `_installed_skill_names` can read it from the shadow; without it the sweep
    deletes the external skill in the shadow, and diff then reports false drift.

    This test drives `run_self_host(dry_run=True)` against a minimal tree
    that has an externally-installed skill recorded in the state file and
    verifies exit code 0 (no drift).
    """
    import sys
    sys.path.insert(0, str(tmp_path))  # ensure tmp_path is importable context

    # Build a minimal packs_dir with no skills — simulates a self-host pack
    # set that ships nothing in .apm/skills/.
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir()

    # Place an external skill in the working tree (as if `agentbundle install`
    # had projected it).
    skill_dir = tmp_path / ".claude" / "skills" / "external-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# External\n", encoding="utf-8", newline="\n")

    # Record it in the repo state file.
    _write_state(
        tmp_path,
        pack_name="external-pack",
        adapter="claude-code",
        relpath=".claude/skills/external-skill/SKILL.md",
    )

    # Run the shadow-clone path directly.
    import tempfile

    from agentbundle.build.self_host import _clone_target_subtree
    with tempfile.TemporaryDirectory(prefix="agentbundle-shadow-") as shadow_str:
        shadow = Path(shadow_str)
        _clone_target_subtree(tmp_path, shadow)

        # The state file must be present in the shadow.
        assert (shadow / ".agentbundle-state.toml").exists(), (
            "_clone_target_subtree must copy .agentbundle-state.toml into the shadow"
        )

        # The external skill must survive a project_packs call in the shadow.
        from agentbundle.build.adapters.claude_code import project_packs
        contract = _minimal_contract("claude-code", ".claude/skills/")
        project_packs([], contract, shadow)

        assert (shadow / ".claude" / "skills" / "external-skill").exists(), (
            "project_packs in the shadow deleted a state-tracked skill; "
            "--check would have reported false drift"
        )
