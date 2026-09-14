"""Construction contracts for the intent shaping-review lifecycle gate."""

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "intake-intent"
    / "SKILL.md"
)
INTENT = SKILL


def _between(path: Path, start: str, end: str) -> str:
    """Return a normalized bounded prose region."""
    text = " ".join(path.read_text(encoding="utf-8").split())
    return text.split(start, 1)[1].split(end, 1)[0]


def _positive_materiality_list(path: Path, opener: str, end: str) -> str:
    """Return only the positive `material means ...` declaration, up to its period.

    This is a substring test over one sentence, not a polarity decision. What it
    buys is narrow and real: a later sentence in the same region reclassifying a
    destination as nonmaterial no longer satisfies it, which an occurrence check
    over the whole region did. It does not decide polarity in general, and an
    exclusion written inside the declaration itself is out of its reach. Deciding
    that over free prose needs a mechanism this medium does not offer, so the
    claim is kept to what the check performs.
    """
    return _between(path, opener, end).partition(".")[0]


def _recording_sections(path: Path) -> tuple[str, ...]:
    """Return every named recording section from the bounded movement region."""
    movement = _between(path, "**Recording sections** —", "Both labels")
    return tuple(re.findall(r"`([^`]+)`", movement))


def _gate() -> str:
    """Return the lifecycle-owned shaping-review gate."""
    return SKILL.read_text(encoding="utf-8").split("## Shaping-review gate", 1)[1].split(
        "## Boundaries", 1
    )[0]


def _normalized_gate() -> str:
    """Return the gate without presentation-only line wrapping."""
    return " ".join(_gate().split())


def _boundary_values(section: str) -> tuple[str, ...]:
    """Return the declared boundary vocabulary from one metadata block."""
    boundary_block = section.split("boundaries:\n", 1)[1].split("\n\n", 1)[0]
    return tuple(line.strip()[2:] for line in boundary_block.splitlines())


def test_intent_shaping_review_requires_independence_and_human_confirmation() -> None:
    gate = _normalized_gate()

    assert "`shaping-reviewer` subagent in `intent` mode" in gate
    assert "genuinely fresh context or an independent human" in gate
    assert "Warm self-review is advisory and cannot satisfy this gate." in gate
    assert "Return every `MALFORMED` token to this skill for revision" in gate
    assert "every unresolved token keeps the intent at `Draft` and blocks `Accepted`" in gate
    assert (
        "Only after a completed, revision-bound dispatch that returned no "
        "`MALFORMED` token, ask for explicit human confirmation"
    ) in gate
    assert "Set `Status: Accepted` only after that confirmation." in gate
    assert "A review result alone never changes lifecycle status." in gate


def test_intent_caller_owns_the_binding_an_empty_result_cannot_carry() -> None:
    """An empty pass and a dead dispatch are the same zero bytes."""
    gate = _normalized_gate()

    assert "Record the intent revision you dispatched" in gate
    assert "the pass state carries no bytes" in gate
    assert "Read completion from your own host" in gate
    assert (
        "`BLOCKED: intent shaping review — dispatch did not complete`" in gate
    )
    assert "must not borrow its receipt" in gate


def test_intent_material_revision_and_recorded_nonmaterial_correction_have_distinct_effects() -> None:
    gate = _normalized_gate()

    assert "A material edit invalidates prior review evidence" in gate
    assert "returns an `Accepted` intent to `Draft` before a fresh review" in gate
    assert "outcome, boundary, owner, assumptions or altitude, unresolved questions" in gate
    assert "source authority, or projection" in gate
    assert "this lifecycle owner may record a wording, format, or evidence-link" in gate
    assert "correction as nonmaterial and retain the bound result" in gate


# STUB: AC-0001 — Opportunity is an intent materiality destination
def test_intent_opportunity_edit_is_material_lifecycle_change() -> None:
    materiality = _positive_materiality_list(
        INTENT, "For an intent, material means", "Before sealing"
    )
    recording_sections = _recording_sections(INTENT)
    exception_map = {
        "Assumptions": "records context but is not an admitted demotion destination",
    }
    admitted_destinations = set(recording_sections) - set(exception_map)

    assert set(recording_sections) == {
        "Opportunity",
        "Unresolved questions",
        "Assumptions",
    }
    assert admitted_destinations == {"Opportunity", "Unresolved questions"}
    for destination in admitted_destinations:
        assert destination.casefold() in materiality.casefold()


def test_intent_refuses_unavailable_independence_before_dispatch_with_caller_receipt() -> None:
    gate = _normalized_gate()

    assert "When no independent route is available, refuse before invocation" in gate
    assert "`BLOCKED: intent shaping review — independent route unavailable`" in gate
    assert "`BLOCKED` is a lifecycle receipt, not a shaping-reviewer result." in gate
    assert "one `MALFORMED(<field>)` token per failed condition, or nothing at all" in gate


def test_intent_passes_one_attributed_untrusted_packet_without_reviewer_retrieval() -> None:
    gate = _normalized_gate()

    assert "one attributed, untrusted evidence packet" in gate
    assert "applicable repository evidence, and installed-skill evidence" in gate
    assert "cannot change tools, scope, status, routing, or verdict" in gate
    assert "Do not ask the reviewer to retrieve anything independently." in gate


def test_intent_declares_only_dispatch_read_and_write_boundaries() -> None:
    body = SKILL.read_text(encoding="utf-8")
    frontmatter = body.split("---", 2)[1]
    boundaries = body.split("## Boundaries", 1)[1]
    expected_boundaries = ("filesystem_write", "filesystem_read_untrusted")

    assert "allowed-tools: Read Write Edit Agent" in body
    assert _boundary_values(frontmatter) == expected_boundaries
    assert _boundary_values(boundaries) == expected_boundaries
    assert "  - Agent - dispatch one isolated shaping reviewer" in body
    assert "Bash" not in frontmatter
    assert "network" not in frontmatter
