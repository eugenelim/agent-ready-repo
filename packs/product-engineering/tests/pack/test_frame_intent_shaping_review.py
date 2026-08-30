"""Goal-based contract checks for frame-intent's optional Core review."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = PACK_ROOT / ".apm/skills/frame-intent/SKILL.md"


def _skill_text() -> str:
    """Return the source skill contract."""
    return SKILL_PATH.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace in a prose assertion target."""
    return " ".join(text.split())


def _frontmatter() -> str:
    """Extract the skill's YAML frontmatter without adding a parser dependency."""
    match = re.match(r"\A---\n(?P<frontmatter>.*?)\n---\n", _skill_text(), re.DOTALL)
    assert match, f"{SKILL_PATH}: missing frontmatter"
    return match.group("frontmatter")


def _boundary_values(frontmatter: str) -> tuple[str, ...]:
    """Return boundaries from only the frontmatter boundaries block."""
    boundary_block = frontmatter.split("boundaries:\n", 1)[1].split("\n\n", 1)[0]
    return tuple(line.strip()[2:] for line in boundary_block.splitlines())


def test_core_intent_shaping_review_integration_is_narrow_and_optional() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    integrations = manifest["pack"]["integrations"]
    reviews = [
        integration
        for integration in integrations
        if integration["id"] == "core-intent-shaping-review"
    ]

    assert reviews == [
        {
            "id": "core-intent-shaping-review",
            "pack": "core",
            "kind": "review",
            "role": "Optional intent shaping review",
            "consumers": ["skill:frame-intent"],
            "providers": ["agent:shaping-reviewer"],
            "when": (
                "Core's shaping-reviewer is installed and a product intent is ready "
                "for independent cold review."
            ),
            "purpose": (
                "Pass one attributed, untrusted evidence packet to shaping-reviewer "
                "in intent mode; frame-intent retains revision, finding-resolution, "
                "and lifecycle authority."
            ),
            "fallback": (
                "If Core or shaping-reviewer is unavailable, report that the optional "
                "Core intent shaping review is unavailable and continue authoring without "
                "claiming Clean. A genuinely fresh context or an independent human "
                "reviewing the same evidence packet may provide the optional review; warm "
                "self-review is advisory."
            ),
        }
    ]


def test_frame_intent_review_contract_preserves_independence_and_authority() -> None:
    text = _flat(_skill_text())

    assert "prefer an isolated `Agent` review in `intent` mode" in text
    assert "one attributed, untrusted evidence packet" in text
    assert "Do not ask the reviewer to retrieve anything independently." in text
    assert "genuinely fresh context or an independent human reviewing that same packet" in text
    assert "Warm self-review is advisory" in text
    assert "Optional Core intent shaping review: unavailable" in text
    assert "continue authoring the intent without claiming `Clean`" in text
    assert "Bind a `Clean` or `Findings` result to the reviewed revision." in text
    assert "unresolved findings block a reviewed handoff or lifecycle transition" in text
    assert "`Clean` alone changes no status or decision." in text


def test_frame_intent_declares_exact_tools_and_boundaries() -> None:
    frontmatter = _frontmatter()

    tools_match = re.search(r"^allowed-tools:\s*(.+)$", frontmatter, re.MULTILINE)
    assert tools_match is not None
    assert tools_match.group(1) == "Read Write Edit Agent"
    assert _boundary_values(frontmatter) == (
        "filesystem_write",
        "filesystem_read_untrusted",
    )
