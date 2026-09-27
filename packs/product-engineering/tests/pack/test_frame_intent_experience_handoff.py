"""Contract checks for frame-intent's situational experience handoff."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = PACK_ROOT / ".apm/skills/frame-intent/SKILL.md"
TEMPLATE_PATH = PACK_ROOT / ".apm/skills/frame-intent/assets/intent-template.md"


def _section(path: Path, title: str) -> str:
    """Return one level-two Markdown section from a shipped artifact."""
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(title)}\n(?P<body>.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"{path}: missing section {title!r}"
    return " ".join(match.group("body").split())


def test_handoff_activates_only_for_material_surface_effects() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    assert "`capability` or `feature`" in section
    for trigger in (
        "creates a human-facing digital surface",
        "materially changes a user journey, interaction, content hierarchy, or visible state",
        "changes what a surface must prove, explain, or allow a person to do",
    ):
        assert trigger in section
    for excluded in (
        "backend-only",
        "infrastructure",
        "internal refactors",
        "dependency changes",
        "build work",
    ):
        assert excluded in section


def test_product_altitudes_never_receive_the_handoff() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    assert "`product-vision`" in section
    assert "`product-strategy`" in section
    assert "do not offer or emit" in section.lower()


def test_optional_block_contains_only_product_facts() -> None:
    block = _section(TEMPLATE_PATH, "Product-to-experience handoff")
    for label in (
        "Affected journey or surface",
        "User outcome and first-success behavior",
        "Product mechanism or proof",
        "Evidence for user-visible claims",
        "Constraints, prohibited claims, and material unknowns",
    ):
        assert f"**{label}:**" in block
    assert "optional" in block.lower()
    assert "capability" in block and "feature" in block


def test_handoff_leaves_experience_decisions_downstream() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    for decision in (
        "engagement mode",
        "visual direction",
        "typography",
        "color",
        "layout",
        "motion",
        "first-viewport composition",
        "signature interaction",
        "implementation approach",
    ):
        assert decision in section
    assert "must not select" in section.lower()


def test_experience_design_is_optional_and_has_no_pack_wiring() -> None:
    section = _section(SKILL_PATH, "Situational product-to-experience handoff")
    assert "Experience Design is not installed" in section
    assert "must not invoke" in section
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    assert all(
        integration["pack"] != "experience-design"
        for integration in manifest["pack"].get("integrations", [])
    )
