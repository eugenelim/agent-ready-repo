"""Manifest and layout invariants for the wicked-estate pack."""

from __future__ import annotations

import json
import re
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


#: An exact semver pin. A range (`^0.16`, `~0.16`, `>=0.16`, `0.16.*`) is not a
#: pin: it resolves to whatever is newest at install time.
_EXACT_PIN = re.compile(r"--version\s+'?(\d+\.\d+\.\d+)'?(?:\s|$)")


def test_runtime_dependency_installs_are_pinned_and_unprivileged() -> None:
    """Tier-2 installs must carry an exact pin and never assume sudo.

    Asserting only that the `--version` flag is present would accept a caret
    range, which is the bug this replaced.
    """
    for dep in load_pack()["runtime-dependencies"]:
        install = dep["install"]
        assert _EXACT_PIN.search(install), (
            f"{dep['package']} install is not pinned to an exact version: {install}"
        )
        assert "sudo" not in install, f"{dep['package']} install assumes sudo"


def test_pin_guard_rejects_a_range() -> None:
    """Negative control: a caret range must not read as a pin."""
    assert _EXACT_PIN.search("cargo install foo --version '^0.16' --locked") is None
    assert _EXACT_PIN.search("cargo install foo --version 0.16.7 --locked") is not None


def test_first_value_verification_points_at_the_preflight() -> None:
    """Setup verification must be a command, not prose the adopter interprets."""
    first_value = load_pack()["first-value"]
    assert "estate_preflight.py" in first_value["verification"]
    assert first_value["writes-to-repo"] is False


#: Literal paths, not paths built from a loop variable. `lint-pack-test-boundary`
#: reads these statically and cannot prove containment for a dynamic segment, so
#: a computed path reads to it as an escape above the pack.
EVALS_DIR = PACK_ROOT / ".apm" / "skills" / "code-intelligence" / "evals"
AGENTS_DIR = PACK_ROOT / ".apm" / "agents"


def test_declared_eval_skills_ship_their_fixtures() -> None:
    """The declared set is pinned to the literal path checked below."""
    assert load_pack()["evals"]["skills"] == ["code-intelligence"]
    assert (EVALS_DIR / "eval_queries.json").is_file()
    assert (EVALS_DIR / "evals.json").is_file()


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
    assert (AGENTS_DIR / "code-investigator.md").is_file()
    assert (AGENTS_DIR / "impact-analyst.md").is_file()
