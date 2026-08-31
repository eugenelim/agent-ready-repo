"""Construction contracts for architect-design's justified-surface guidance."""

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "architect-design" / "SKILL.md"
RUBRIC = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-design"
    / "references"
    / "design-doc-rubric.md"
)


def _flat(path: Path) -> str:
    """Return whitespace-normalized portable skill text."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_author_reuses_existing_answers_and_stops_before_full_design() -> None:
    """Adequate prior work ends authoring without a new design artifact."""
    text = _flat(SKILL)

    assert "adequate prior design or existing capability" in text
    assert "Reuse it when it resolves the current question." in text
    assert "If no real choice remains, create no new artifact." in text
    assert "Stage 0 is a valid stopping point" in text
    assert "Create a full design only when unresolved trade-offs still require it." in text


def test_full_design_justifies_its_surface_and_claims() -> None:
    """Every added design element and necessary external claim has a basis."""
    text = _flat(SKILL)
    rubric = _flat(RUBRIC)

    for required in (
        "For every component and boundary, name the current goal, constraint, or prioritized quality attribute that justifies it.",
        "Remove unsupported future-proofing and unnecessary claims.",
        "one bounded check of its named target",
        "assumption or discovery predicate",
    ):
        assert required in text
    assert "Every component and boundary names the current goal, constraint, or prioritized quality attribute that justifies it." in rubric
    assert "Removes unsupported future-proofing." in rubric
    assert "Each necessary cross-document assertion has one bounded check" in rubric


def test_author_save_contract_is_confined_to_the_configured_output_root() -> None:
    """The author guidance refuses unsafe destinations before a directed save."""
    text = _flat(SKILL)

    for required in (
        "A Stage-0 or full-design save stays inside the resolved configured output root.",
        "Before any mutation, refuse an unsafe, link-like, identity-changing, or out-of-root target.",
        "does not add a runtime save gate",
    ):
        assert required in text


def test_direct_architecture_requests_stay_with_the_architecture_author() -> None:
    """Direct design work neither needs synthetic intent nor shaping review."""
    text = _flat(SKILL)

    assert "A direct architecture request needs no synthetic intent" in text
    assert "does not dispatch shaping review" in text
    assert "shaping-review" not in text


def test_author_authority_is_exactly_the_declared_baseline() -> None:
    """The author has no tool list and only its declared metadata boundaries."""
    frontmatter = SKILL.read_text(encoding="utf-8").split("---", 2)[1]

    assert "allowed-tools:" not in frontmatter
    assert frontmatter.splitlines() == [
        "",
        "name: architect-design",
        "description: Use when the user is framing a problem, weighing a technical choice, or designing a system or integration without a diagram as the headline ask. Triggers on \"how should we\", \"we need to\", \"what's the right way to build X\", tech-selection, integration design, NFR trade-offs. Shapes a one-page concept first, then produces a Google-style design doc (TL;DR, context, goals/non-goals, proposal, alternatives, risks, rollout, open questions), 2-5 pages, with Mermaid inline, and converges it against review. Cloud well-architected by construction (AWS/Azure/GCP and primitives providers like Hetzner). Do NOT use when the ask is a diagram (use `architect-diagram`) or a critique (use `architect-review`).",
        "metadata:",
        "  boundaries: [filesystem_read_untrusted, filesystem_write, network_fetch]",
    ]
