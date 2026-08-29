"""Cross-pack coverage checks for the reviewed skill census."""

import json
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
CENSUS = REPOSITORY / "packs" / "agent-skill-engineering" / "tests" / "fixtures" / "skill-census.json"
ROLE_OWNERS = {
    "catalogue-maintainer",
    "pack-maintainer",
    "skill-maintainer",
    "unassigned-role",
}


def _discovered_skills() -> set[str]:
    """Return each authored skill key from every pack's export source."""
    return {
        f"{path.parents[3].name}/{path.parent.name}"
        for path in REPOSITORY.glob("packs/*/.apm/skills/*/SKILL.md")
    }


def test_census_resolves_every_authored_skill() -> None:
    """Every live authored skill has a reviewed family or reviewed exception."""
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    discovered = _discovered_skills()
    entries = census["entries"]
    recorded = {f"{entry['pack']}/{entry['skill']}" for entry in entries}

    assert recorded == discovered, (
        "skill census out of date; re-take the reviewed census and update "
        "population_size with `pytest tests/roster/test_skill_census.py`"
    )
    assert census["population_size"] == len(discovered)
    assert len(entries) == len(recorded)

    for entry in entries:
        families = entry.get("families", [])
        exception = entry.get("exception")
        assert bool(families) ^ bool(exception), entry
        if exception:
            assert exception["owner"] in ROLE_OWNERS, entry
            assert exception["rationale"], entry
