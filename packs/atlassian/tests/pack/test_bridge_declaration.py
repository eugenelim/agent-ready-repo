"""The pack declares its bridge skills, and the declaration matches reality.

ADR-0126 D4 makes `[pack.metadata].bridge-skills` in `pack.toml` the contract
for which of this pack's skills may couple to the repository's delivery
machinery, and says in the same breath that the `-brief-intake` / `-refresh`
naming is a convention rather than the contract. `[pack.metadata]` is the pack
schema's open extension table (`additionalProperties` intentionally
unrestricted), so `agentbundle catalogue lint` accepts any shape there — an
empty list included. These assertions are what the lint cannot make: membership
is derived here by scanning each skill for the coupled machinery itself, so a
suffix-derived list cannot pass while a coupled skill sits outside it.

Tests are not shipped pack content, so the ADR citations above are in scope
here and would not be in a `SKILL.md`.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
PACK_TOML = PACK_ROOT / "pack.toml"
SKILLS_ROOT = PACK_ROOT / ".apm" / "skills"

# The machinery ADR-0126 D2 confines to bridge skills, in the same terms the
# ADR's own 2026-09-24 measurement used. Lower-cased before matching.
COUPLED_MACHINERY = (
    "docs/product/",
    "workspace.toml",
    "work-intake",
    "intent tree",
    "canonical intent",
    "delivery brief",
)

# The standalone skill this slice adds. Named explicitly rather than derived,
# because "absent from the list" is the assertion, and deriving it from the
# same scan that builds the list would make it circular.
STANDALONE_SKILL_UNDER_TEST = "jira-epic-outcome-view"


def _skill_directories() -> set[str]:
    return {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir()}


def _carries_coupled_machinery(skill_dir: Path) -> bool:
    """True when any file under the skill mentions the confined machinery.

    The whole skill is scanned, not only `SKILL.md`: a skill whose coupling
    lives in a script or a manifest is coupled just the same, and a scan of the
    front matter alone would miss it.
    """
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(token in text for token in COUPLED_MACHINERY):
            return True
    return False


def _coupled_skills() -> set[str]:
    return {
        path.name
        for path in sorted(SKILLS_ROOT.iterdir())
        if path.is_dir() and _carries_coupled_machinery(path)
    }


def _declared_bridges() -> list[str]:
    with PACK_TOML.open("rb") as handle:
        manifest = tomllib.load(handle)
    return manifest["pack"]["metadata"]["bridge-skills"]


def test_bridge_skills_is_declared_as_a_list_of_unique_names() -> None:
    """The key exists, under the table the ADR names, with a usable shape."""
    declared = _declared_bridges()

    assert isinstance(declared, list)
    assert all(isinstance(name, str) and name for name in declared)
    assert len(set(declared)) == len(declared), f"duplicate names: {declared}"


def test_every_declared_bridge_is_a_skill_this_pack_ships() -> None:
    """A name with no directory behind it declares nothing about this pack."""
    unknown = sorted(set(_declared_bridges()) - _skill_directories())

    assert unknown == [], f"declared bridges with no skill directory: {unknown}"


def test_every_skill_carrying_the_coupled_machinery_is_declared() -> None:
    """The assertion the lint cannot make, and the one an empty list fails.

    Derived from the sources rather than from the naming convention, so a
    coupled skill named outside the `-refresh` / `-brief-intake` pattern
    cannot sit quietly outside the declaration.
    """
    coupled = _coupled_skills()

    # Guard against a silently broken scan: if the patterns stopped matching,
    # the subset assertion below would pass vacuously against any list at all.
    assert coupled, "no skill matched the coupled machinery — the scan is broken"

    undeclared = sorted(coupled - set(_declared_bridges()))
    assert undeclared == [], f"coupled skills absent from the declaration: {undeclared}"


def test_the_epic_outcome_view_is_not_declared_a_bridge() -> None:
    """The view returns value with no repository artifact present, so it is
    standalone and must not appear in the bridge list."""
    assert STANDALONE_SKILL_UNDER_TEST in _skill_directories()
    assert STANDALONE_SKILL_UNDER_TEST not in _declared_bridges()
