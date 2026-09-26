"""The pack's release surface agrees with itself.

`packs/AGENTS.md` makes three things obligatory for a non-cosmetic pack change:
`pack.toml` and `.claude-plugin/plugin.json` carry the same bumped version, the
pack's eval harness covers the change, and the aggregated
`.claude-plugin/marketplace.json` — which `make build-self` regenerates from
every pack's plugin manifest — carries that same version.

Each is checked here rather than by eye. A version bumped in one manifest and
not the other reads as correct in either file alone; only a comparison catches
it.

Tests are not shipped pack content, so any citation above is in scope here and
would not be in a `SKILL.md`.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACK_ROOT.parents[1]

PACK_TOML = PACK_ROOT / "pack.toml"
PLUGIN_JSON = PACK_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_JSON = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SKILLS_ROOT = PACK_ROOT / ".apm" / "skills"

PACK_NAME = "atlassian"

# The skill this slice adds. Named explicitly: "the harness covers the new
# skill" is the assertion, and deriving the name from the harness list would
# make it circular.
NEW_SKILL = "jira-epic-outcome-view"


def _pack_manifest() -> dict:
    with PACK_TOML.open("rb") as handle:
        return tomllib.load(handle)


def _pack_version() -> str:
    return _pack_manifest()["pack"]["version"]


def _plugin_version() -> str:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]


def _eval_skills() -> list[str]:
    return _pack_manifest()["pack"]["evals"]["skills"]


def test_both_manifests_carry_the_same_version() -> None:
    """The rule a single-file read cannot check."""
    pack_version = _pack_version()
    plugin_version = _plugin_version()

    assert pack_version, "pack.toml declares no version"
    assert pack_version == plugin_version, (
        f"pack.toml carries {pack_version!r} but "
        f".claude-plugin/plugin.json carries {plugin_version!r}"
    )


def test_the_marketplace_aggregate_carries_that_same_version() -> None:
    """`marketplace.json` is generated from the plugin manifests, so a stale
    aggregate means the regeneration was skipped or its output was edited."""
    marketplace = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    entries = [p for p in marketplace["plugins"] if p.get("name") == PACK_NAME]

    assert len(entries) == 1, f"expected one {PACK_NAME} entry, found {len(entries)}"
    assert entries[0]["version"] == _pack_version()


def test_the_eval_harness_covers_the_new_skill() -> None:
    """A non-cosmetic pack update also updates that pack's eval harness."""
    assert (SKILLS_ROOT / NEW_SKILL).is_dir(), f"{NEW_SKILL} ships no skill directory"
    assert NEW_SKILL in _eval_skills()


def test_every_covered_skill_ships_the_queries_the_runner_reads() -> None:
    """A name in the allowlist with no `evals/eval_queries.json` behind it is
    coverage the runner cannot measure."""
    missing = [
        skill
        for skill in _eval_skills()
        if not (SKILLS_ROOT / skill / "evals" / "eval_queries.json").is_file()
    ]

    assert missing == [], f"covered skills with no eval_queries.json: {missing}"


def test_every_covered_skill_is_a_skill_this_pack_ships() -> None:
    """A name with no directory behind it declares nothing about this pack."""
    shipped = {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir()}
    unknown = sorted(set(_eval_skills()) - shipped)

    assert unknown == [], f"covered skills with no directory: {unknown}"
