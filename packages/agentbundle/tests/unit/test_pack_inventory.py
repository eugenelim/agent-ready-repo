"""T1: the shared ``.apm/`` walk primitive (``agentbundle.pack_inventory``).

Pure functions over a fixture pack tree — no catalogue, no state, no I/O
beyond the tree the test builds. Covers spec AC2 (skill = a
``.apm/skills/<name>/`` dir containing ``SKILL.md``; agent =
``.apm/agents/<name>.md``) and AC4 (missing dirs → empty list, no raise).
"""

from __future__ import annotations

from pathlib import Path


def _make_pack(root: Path) -> Path:
    """Build a fixture pack tree under *root* and return the pack dir."""
    pack = root / "demo"
    skills = pack / ".apm" / "skills"
    agents = pack / ".apm" / "agents"
    # Two well-formed skills (out of alphabetical order on disk).
    for name in ("zeta", "alpha"):
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    # A directory with no SKILL.md — not a skill (AC2).
    (skills / "not-a-skill").mkdir(parents=True)
    (skills / "not-a-skill" / "README.md").write_text("x\n", encoding="utf-8")
    # Agents: two .md files, plus a non-.md file and a subdir to ignore.
    agents.mkdir(parents=True)
    (agents / "beta.md").write_text("# agent\n", encoding="utf-8")
    (agents / "aardvark.md").write_text("# agent\n", encoding="utf-8")
    (agents / "notes.txt").write_text("ignore me\n", encoding="utf-8")
    (agents / "nested").mkdir()
    return pack


# ---------------------------------------------------------------------------
# skill_names (AC2)
# ---------------------------------------------------------------------------


def test_skill_names_sorted_and_skill_md_gated(tmp_path):
    from agentbundle.pack_inventory import skill_names

    pack = _make_pack(tmp_path)
    # Sorted ascending; "not-a-skill" excluded (no SKILL.md).
    assert skill_names(pack) == ["alpha", "zeta"]


def test_skill_dir_without_skill_md_excluded(tmp_path):
    from agentbundle.pack_inventory import skill_names

    pack = tmp_path / "p"
    (pack / ".apm" / "skills" / "empty").mkdir(parents=True)
    assert skill_names(pack) == []


# ---------------------------------------------------------------------------
# agent_names (AC2)
# ---------------------------------------------------------------------------


def test_agent_names_sorted_md_only(tmp_path):
    from agentbundle.pack_inventory import agent_names

    pack = _make_pack(tmp_path)
    # Sorted; non-.md file and subdir ignored.
    assert agent_names(pack) == ["aardvark", "beta"]


# ---------------------------------------------------------------------------
# Missing dirs → [] (AC4)
# ---------------------------------------------------------------------------


def test_missing_skills_dir_returns_empty(tmp_path):
    from agentbundle.pack_inventory import skill_names

    pack = tmp_path / "no-apm"
    pack.mkdir()
    assert skill_names(pack) == []


def test_missing_agents_dir_returns_empty(tmp_path):
    from agentbundle.pack_inventory import agent_names

    pack = tmp_path / "no-apm"
    pack.mkdir()
    assert agent_names(pack) == []


# ---------------------------------------------------------------------------
# Raw shared primitive (AC9) — returns sorted Path entries, [] when absent
# ---------------------------------------------------------------------------


def test_apm_entries_returns_sorted_paths(tmp_path):
    from agentbundle.pack_inventory import apm_entries

    pack = _make_pack(tmp_path)
    skill_entries = apm_entries(pack, "skills")
    assert [p.name for p in skill_entries] == ["alpha", "not-a-skill", "zeta"]
    assert all(isinstance(p, Path) for p in skill_entries)


def test_apm_entries_absent_dir_returns_empty(tmp_path):
    from agentbundle.pack_inventory import apm_entries

    pack = tmp_path / "no-apm"
    pack.mkdir()
    assert apm_entries(pack, "skills") == []
    assert apm_entries(pack, "agents") == []


def test_lint_packs_enumerates_through_shared_primitive():
    """AC9: the ``.apm/`` walk lives in one place — both the ``show`` command
    (via ``pack_inventory``) and ``build/lint_packs`` reach the tree through the
    same :func:`apm_entries` function object (an identity assertion, not a
    behavioral-equivalence one), so a re-inlined copy of the traversal would
    trip this test."""
    from agentbundle import pack_inventory
    from agentbundle.build import lint_packs

    assert lint_packs.apm_entries is pack_inventory.apm_entries
