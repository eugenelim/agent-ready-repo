"""Ownership boundary between repository anchoring and API contracts."""

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/contract-acquisition/SKILL.md"


def test_contract_acquisition_excludes_repository_dialect_and_layout() -> None:
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    assert "Repository coding dialect, file layout, and local implementation idioms" in text
    assert "belong to repository anchoring" in text
    assert "signatures, lifecycle, version-specific behavior, schemas" in text
