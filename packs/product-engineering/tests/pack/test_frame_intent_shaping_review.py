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
                "in intent mode, which returns one MALFORMED(field) token per failed "
                "well-formedness condition or nothing at all; frame-intent retains "
                "revision, token-resolution, and lifecycle authority."
            ),
            "fallback": (
                "If Core or shaping-reviewer is unavailable, report that the optional "
                "Core intent shaping review is unavailable and continue authoring, "
                "claiming no review result. A genuinely fresh context or an independent "
                "human reviewing the same evidence packet may provide the optional "
                "review; warm self-review is advisory."
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
    assert "continue authoring the intent and claim no review result" in text
    assert "one `MALFORMED(<field>)` token per failed condition, or nothing at all" in text
    assert "Record the intent revision you dispatched" in text
    assert "read completion from your own host" in text
    assert "an unresolved token blocks a reviewed handoff or lifecycle transition" in text
    assert "a review result alone changes no status or decision" in text
    assert (
        "`Optional Core intent shaping review: dispatch did not complete`" in text
    )


def _section(title: str) -> str:
    """One `##` section of the skill, bounded by the next `##` heading.

    Whole-file scope cannot see a section boundary. Deleting the heading below
    merged this advisory branch into the lifecycle-bearing shaping-review
    section above it -- so "establishes nothing" would have read as governing
    the review that *does* block a handoff -- and every assertion here stayed
    green. The bound is the control.
    """
    body = _skill_text()
    start = body.index(f"## {title}")
    following = re.search(r"^## ", body[start + len(title) + 3 :], re.MULTILINE)
    end = start + len(title) + 3 + following.start() if following else len(body)
    return body[start:end]


def test_frame_intent_may_dispatch_the_adversarial_intent_read() -> None:
    """The optional second read is advisory and owns no lifecycle effect."""
    text = _flat(_section("Optional adversarial read of the bet"))

    assert "`adversarial-reviewer` in `intent` mode" in text
    assert "riskiest assumption" in text and "non-goals" in text
    assert "open question with a named decider" in text
    assert "kill condition plus the real-world activity" in text
    assert "advisory and establishes nothing" in text
    assert "no status or handoff rests on it" in text
    # de-risk-intent authors the kill condition, so it never dispatches the
    # reviewer that emits hooks -- stating it here keeps the boundary visible
    # at the one skill that may dispatch it.
    assert "never dispatches this reviewer" in text


def test_frame_intent_declares_exact_tools_and_boundaries() -> None:
    frontmatter = _frontmatter()

    tools_match = re.search(r"^allowed-tools:\s*(.+)$", frontmatter, re.MULTILINE)
    assert tools_match is not None
    assert tools_match.group(1) == "Read Write Edit Agent"
    assert _boundary_values(frontmatter) == (
        "filesystem_write",
        "filesystem_read_untrusted",
    )
