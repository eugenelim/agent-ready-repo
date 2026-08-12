"""Core seed invariants."""

from __future__ import annotations

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
CORE_SEEDS = PACK_ROOT / "seeds"


def test_agents_md_has_no_legacy_skill_delimiters() -> None:
    text = (CORE_SEEDS / "AGENTS.md").read_text(encoding="utf-8")
    assert "<!-- agent-skills:start -->" not in text
    assert "<!-- agent-skills:end -->" not in text


def test_reference_md_is_not_preplaced() -> None:
    assert not (CORE_SEEDS / "docs" / "architecture" / "reference.md").exists()
