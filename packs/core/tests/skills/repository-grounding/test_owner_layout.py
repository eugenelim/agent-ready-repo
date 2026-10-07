"""The path-seeded explorer has exactly one home: the grounding owner."""

from __future__ import annotations

from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"


# STUB: AC0009
def test_explorer_has_one_home_under_repository_grounding() -> None:
    """The explorer moved, and no second editable copy stayed behind."""
    owner = SKILLS / "repository-grounding" / "scripts" / "explore-grounding.py"
    former = SKILLS / "new-spec" / "scripts" / "explore-grounding.py"
    assert owner.is_file()
    assert not former.exists()
