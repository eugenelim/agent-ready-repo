"""Manifest and layout invariants for the wicked-estate pack."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]


def load_pack() -> dict:
    return tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))["pack"]


def load_plugin() -> dict:
    return json.loads(
        (PACK_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )


def test_plugin_manifest_matches_pack_manifest() -> None:
    """The version-bump rule only holds if the two manifests cannot drift."""
    pack, plugin = load_pack(), load_plugin()
    assert plugin["name"] == pack["name"]
    assert plugin["version"] == pack["version"]
    assert plugin["description"] == pack["description"]


def test_declares_the_estate_cli_as_a_runtime_dependency() -> None:
    """The CLI is required; the MCP server is optional. Both must be declared."""
    deps = {d["package"]: d for d in load_pack()["runtime-dependencies"]}
    assert deps["wicked-estate"]["ecosystem"] == "cargo"
    assert deps["wicked-estate"]["optional"] is False
    assert deps["wicked-estate-mcp"]["optional"] is True


def test_runtime_dependency_installs_are_pinned_and_unprivileged() -> None:
    """Tier-2 installs must be pinned and must never assume sudo."""
    for dep in load_pack()["runtime-dependencies"]:
        install = dep["install"]
        assert "--version" in install, f"{dep['package']} install is not pinned"
        assert "sudo" not in install, f"{dep['package']} install assumes sudo"


def test_first_value_verification_points_at_the_preflight() -> None:
    """Setup verification must be a command, not prose the adopter interprets."""
    first_value = load_pack()["first-value"]
    assert "estate_preflight.py" in first_value["verification"]
    assert first_value["writes-to-repo"] is False


def test_declared_eval_skills_ship_their_fixtures() -> None:
    for skill in load_pack()["evals"]["skills"]:
        evals_dir = PACK_ROOT / ".apm" / "skills" / skill / "evals"
        assert (evals_dir / "eval_queries.json").is_file()
        assert (evals_dir / "evals.json").is_file()


def test_no_tests_inside_the_runtime_payload() -> None:
    """`.apm/` is the export boundary; a test there would be projected."""
    strays = [
        path
        for path in (PACK_ROOT / ".apm").rglob("*")
        if path.is_file() and path.name.startswith("test_")
    ]
    assert not strays, f"test files found under .apm/: {strays}"


def test_skill_and_agents_exist() -> None:
    assert (PACK_ROOT / ".apm/skills/code-intelligence/SKILL.md").is_file()
    for agent in ("code-investigator", "impact-analyst"):
        assert (PACK_ROOT / ".apm/agents" / f"{agent}.md").is_file()
