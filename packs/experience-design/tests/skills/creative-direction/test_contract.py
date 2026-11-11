"""Construction tests for the creative-direction published contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "creative-direction"

SKILL = SKILL_ROOT / "SKILL.md"
TEMPLATE = SKILL_ROOT / "assets" / "creative-direction-template.md"
REFERENCE_ROOT = SKILL_ROOT / "references"
EVALS = SKILL_ROOT / "evals" / "evals.json"
EVAL_QUERIES = SKILL_ROOT / "evals" / "eval_queries.json"

ENGAGEMENT_MODE_DEFINITIONS = {
    "persuade": "establishing relevance, confidence, and desire",
    "operate": "supporting repeated or consequential work",
    "read": "making structured information easy to understand and navigate",
    "experience": "making exploration or immersion part of the value",
}

ROUTES = ("inherit", "extend", "originate")
OPERATIONS = ("frame", "explore", "visualize", "converge", "refine")
AXES = (
    "Grid grammar",
    "Alignment and equilibrium",
    "Spatial density",
    "Whitespace distribution",
    "Hierarchy and scale contrast",
    "Containment and boundary strength",
    "Section and scroll rhythm",
    "Type voice",
    "Type hierarchy",
    "Chromatic intensity",
    "Form",
    "Material and depth",
    "Ornament and texture",
    "Image treatment",
    "Motion character",
)
EXCLUDED_DEPENDENCY_TERMS = (
    "requires Product Engineering",
    "requires Frontend Engineering",
    "requires a comp",
    "requires browser",
    "requires image analysis",
    "requires an image-analysis",
    "downloaded binary",
    "browser extension",
    "new dependency",
    "randomly select",
    "roll a die",
    "dice",
)
UNIVERSAL_STYLE_RULE_TERMS = (
    "never use serif",
    "never use sans",
    "font blacklist",
    "fixed radius",
    "always use rounded",
    "never use rounded",
    "absolute style ban",
)


def _read(path: Path) -> str:
    """Read a skill-owned text file."""
    return path.read_text(encoding="utf-8")


def _skill_text() -> str:
    """Return all contract-bearing creative-direction prose."""
    parts = [
        _read(SKILL),
        _read(TEMPLATE),
        _read(REFERENCE_ROOT / "grounding.md"),
        _read(REFERENCE_ROOT / "explore.md"),
        _read(REFERENCE_ROOT / "visualize.md"),
        _read(REFERENCE_ROOT / "converge.md"),
        _read(REFERENCE_ROOT / "refusals.md"),
        _read(REFERENCE_ROOT / "divergence-audit.md"),
    ]
    return "\n".join(parts)


def _eval_payloads() -> tuple[dict[str, object], list[dict[str, object]]]:
    """Load the creative-direction eval corpus and trigger queries."""
    evals = json.loads(_read(EVALS))
    queries = json.loads(_read(EVAL_QUERIES))
    assert isinstance(evals, dict)
    assert isinstance(queries, list)
    assert all(isinstance(query, dict) for query in queries)
    return evals, queries


def test_creative_direction_publishes_product_specific_contract() -> None:
    """The shipped skill and artifact template expose the new contract."""
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    template = (SKILL_ROOT / "assets/creative-direction-template.md").read_text(
        encoding="utf-8"
    )
    contract = skill + template
    for required in (
        "Engagement mode",
        "Product-specific visual thesis",
        "First-viewport thesis",
        "Approved visual target",
    ):
        assert required in contract
    assert "Signature interaction" in template


def test_engagement_mode_is_defined_as_overlay_not_surface_genre() -> None:
    """AC-0001, AC-0002, and AC-0019 pin mode names and genre separation."""
    contract = _skill_text()
    lowered = contract.lower()

    assert "surface genre" in lowered
    assert "visitor posture" in lowered
    assert re.search(r"engagement mode.*overlay", lowered, re.DOTALL)
    assert re.search(r"does not (replace|overwrite)", lowered)

    for mode, definition in ENGAGEMENT_MODE_DEFINITIONS.items():
        assert mode in lowered
        assert definition in lowered
    assert "secondary mode" in lowered
    assert "distinct user job" in lowered


def test_contract_requires_specific_viewport_interaction_and_target_fields() -> None:
    """AC-0003 through AC-0007 pin the new artifact commitments."""
    contract = _skill_text()
    lowered = contract.lower()

    for phrase in (
        "audience's situation",
        "distinctive mechanism",
        "honest proof",
        "category peer",
        "first-viewport thesis",
        "opening viewport",
        "primary action",
        "continuation",
        "signature interaction",
        "decorative motion",
        "none",
        "approved visual target",
        "binding",
        "illustrative",
        "adapt responsively",
    ):
        assert phrase in lowered
    assert "hero layout" not in lowered or "not" in lowered


def test_honesty_fallback_and_contextual_craft_rules_are_published() -> None:
    """AC-0008 through AC-0012 and AC-0015 pin evidence and fallback rules."""
    contract = _skill_text()
    lowered = contract.lower()

    for phrase in (
        "available evidence",
        "available assets",
        "placeholders",
        "provenance",
        "invent testimonials",
        "customer metrics",
        "product screenshots",
        "category-default",
        "generic tropes",
        "familiar pattern",
        "product intent",
        "digital experience contract",
        "screen brief",
        "existing product",
        "direct user answers",
        "labeled assumption",
        "clean and modern",
        "product-specific evidence",
    ):
        assert phrase in lowered

    assert re.search(
        r"do not invent.*testimonials.*customer metrics.*product screenshots",
        lowered,
        re.DOTALL,
    )

    for term in UNIVERSAL_STYLE_RULE_TERMS:
        assert term not in lowered


def test_retained_routes_operations_axes_and_quality_controls_remain() -> None:
    """AC-0013, AC-0014, and AC-0017 pin retained creative-direction behavior."""
    skill = _read(SKILL)
    template = _read(TEMPLATE)
    contract = _skill_text()
    lowered = contract.lower()

    for route in ROUTES:
        assert re.search(rf"\|\s*{route}\s*\|", skill)
    for operation in OPERATIONS:
        assert re.search(rf"^### {operation}$", skill, re.MULTILINE)
    for axis in AXES:
        assert f"| {axis} |" in template
    assert template.count("| ") >= len(AXES)
    assert "six-of-fifteen minimum pairwise distance" in lowered
    assert "minimum pairwise distance" in lowered
    assert "counterfactual check" in lowered
    assert "quality floor" in lowered


def test_contract_does_not_require_excluded_capabilities_or_random_selection() -> None:
    """AC-0016 pins the browserless, dependency-free skill boundary."""
    lowered = _skill_text().lower()

    for term in EXCLUDED_DEPENDENCY_TERMS:
        assert term.lower() not in lowered


def test_eval_corpus_remains_available_for_behavior_checks() -> None:
    """AC-0017 pins eval fixtures for later behavior coverage."""
    evals, queries = _eval_payloads()
    cases = evals.get("evals")
    assert isinstance(cases, list)
    assert cases
    assert queries

    corpus = json.dumps({"evals": cases, "queries": queries}).lower()
    for retained in ("inherit", "originate", "refine"):
        assert retained in corpus
    assert "candidate" in corpus
    assert "distance" in corpus

    case_text_by_id = {
        case["id"]: json.dumps(case, sort_keys=True).lower()
        for case in cases
        if isinstance(case.get("id"), int)
    }

    assert "audience's situation" in case_text_by_id[6]
    assert "distinctive 14-day runway mechanism" in case_text_by_id[6]
    assert "honestly show" in case_text_by_id[6]
    assert "first-viewport thesis" in case_text_by_id[6]
    assert "category peer" in case_text_by_id[6]

    assert "direct answers" in case_text_by_id[7]
    assert "no product engineering pack" in case_text_by_id[7]
    assert "no product intent doc" in case_text_by_id[7]
    assert "labeled assumptions" in case_text_by_id[7]
    assert "separates available text-only evidence" in case_text_by_id[7]

    assert "clean-and-modern direction does not pass" in case_text_by_id[8]
    assert "refuses to invent customer metrics" in case_text_by_id[8]
    assert "testimonials" in case_text_by_id[8]
    assert "product screenshots" in case_text_by_id[8]
    assert "decorative motion" in case_text_by_id[8]

    positive_queries = [
        query["query"].lower()
        for query in queries
        if query.get("should_trigger") is True
    ]
    negative_queries = [
        query["query"].lower()
        for query in queries
        if query.get("should_trigger") is False
    ]
    assert any("engagement mode" in query for query in positive_queries)
    assert any("first-viewport thesis" in query for query in positive_queries)
    assert any("binding versus illustrative" in query for query in positive_queries)
    assert any("proof is real" in query for query in positive_queries)
    assert any("invent customer testimonials" in query for query in negative_queries)
    assert any("rendered ui matches the approved comp" in query for query in negative_queries)


def test_the_frame_operation_excludes_inherit_from_the_interrogation() -> None:
    """The route table promises `inherit` runs no fresh interrogation, so the
    shared `frame` operation must not instruct one unconditionally.

    Asserted at sentence granularity rather than file granularity: a qualifier
    that drifts into a neighbouring sentence leaves the instruction reading
    unconditionally where an agent meets it, which is the defect this pins.
    """
    body = re.sub(r"\s+", " ", SKILL.read_text(encoding="utf-8"))
    sentences = [s for s in re.split(r"(?<=\.) ", body) if "Run the interrogation" in s]
    assert sentences, "no sentence instructs running the interrogation"
    for sentence in sentences:
        assert "inherit" in sentence, (
            f"the interrogation instruction does not name `inherit`: {sentence!r}. "
            "The route table says `inherit` runs no fresh interrogation."
        )


# STUB: AC-0001, AC-0002, AC-0003, AC-0011  (spec: visual-target-field)
def test_template_carries_the_visual_target_disposition() -> None:
    """visual-target-field AC-0001, AC-0002, AC-0003, AC-0011.

    This module also carries creative-direction-modes criteria under
    overlapping numbers, so every AC reference here names its spec.
    """
    template = _read(TEMPLATE)
    frontmatter = template.split("---", 2)[1]
    assert re.search(
        r'^visual_target:\s*"<none \| unconfirmed \| confirmed>"\s*$',
        frontmatter,
        re.M,
    ), "AC-0001: frontmatter must carry visual_target over the closed set"

    section = template.split("## Approved visual target", 1)[1].split("\n## ", 1)[0]
    record_lines = [
        line
        for line in section.splitlines()
        if line.startswith("**Confirmation record:**")
    ]
    assert len(record_lines) == 1, "AC-0002: exactly one confirmation-record line"
    assert " ".join(record_lines[0].split()) == (
        "**Confirmation record:** <YYYY-MM-DD> — "
        "<where the confirmation was recorded>"
    ), "AC-0002: the placeholder is pinned exactly, leaving no slot for a person"

    comment = section.split("-->", 1)[0]
    assert "visual_target" in comment, "AC-0003"
    for label in ("**Target:**", "**Binding:**", "**Confirmation record:**"):
        assert label in comment, "AC-0003"
    assert "bind nothing on their own" in comment, "AC-0003"
    normalized_comment = " ".join(comment.split())
    assert (
        "An absent `visual_target` reads as `unconfirmed`" in normalized_comment
    ), (
        "AC-0011: the comment must state the absent-field reading as one "
        "contiguous phrase. Testing for `unconfirmed` beside the word `absent` "
        "reduces the criterion to whether `absent` appears at all, so a comment "
        "stating that an absent target means `none` would pass while "
        "contradicting the fail-closed default."
    )


def _unique_paragraph(path: Path, anchor: str) -> str:
    """The one blank-line-delimited block carrying `anchor`, in this file only.

    Bounding on markdown's own delimiter rather than on ". " keeps an adjacent
    period-free heading, bullet or table cell out of the unit.
    """
    blocks = [b for b in re.split(r"\n\s*\n", _read(path)) if anchor in b]
    assert len(blocks) == 1, f"{anchor!r} must occur in exactly one block of {path.name}"
    return " ".join(blocks[0].split())


# STUB: AC-0004  (spec: visual-target-field)
def test_converge_records_the_disposition() -> None:
    """visual-target-field AC-0004."""
    disposition = _unique_paragraph(
        REFERENCE_ROOT / "converge.md", "Record the approved visual target disposition"
    )
    for value in ("none", "unconfirmed", "confirmed"):
        assert f"visual_target: {value}" in disposition, f"AC-0004: {value}"


# STUB: AC-0013  (spec: visual-target-field)
def test_eval_harness_asserts_a_visual_target_disposition() -> None:
    """visual-target-field AC-0013."""
    evals, _ = _eval_payloads()
    values = ("visual_target: none", "visual_target: unconfirmed", "visual_target: confirmed")
    carrying = [
        case["id"]
        for case in evals["evals"]
        if any(
            value in assertion
            for assertion in case.get("assertions", [])
            for value in values
        )
    ]
    assert carrying, (
        "AC-0013: no eval case asserts a visual_target disposition. A mention in "
        "a prompt, an expected_output or a trigger query does not satisfy this."
    )


# `_unique_paragraph` is NOT defined here. `visual-target-field` is a hard
# predecessor and adds it to this same module, so a second definition would
# fire ruff F811 under T6's `make lint-ruff` gate. Reuse what it leaves.


# STUB: AC-0012, AC-0013, AC-0014  (spec: visual-target-rung-precondition)
def test_producing_surfaces_are_gated_on_confirmation() -> None:
    """visual-target-rung-precondition AC-0012 through AC-0014.

    This module also carries other specs' criteria under overlapping numbers,
    so every AC reference here names its spec.
    """
    commitments = _unique_paragraph(
        REFERENCE_ROOT / "converge.md",
        "write the selected direction's compositional commitments",
    )
    assert "visual_target: confirmed" in commitments, "AC-0012"

    boundaries = _unique_paragraph(
        REFERENCE_ROOT / "visualize.md", "record its identity and three boundaries"
    )
    assert "the human has confirmed" in boundaries, "AC-0013"
    assert "visual_target: confirmed" in boundaries, "AC-0013 (own requirement)"

    items = [
        block
        for block in _read(SKILL).split("\n- ")[1:]
        if block.startswith("**Approved visual target**")
    ]
    assert len(items) == 1, "AC-0014: exactly one such list item in SKILL.md"
    item = " ".join(items[0].split())
    assert "the human has confirmed" in item, "AC-0014"
    assert "visual_target: confirmed" in item, "AC-0014 (own requirement)"
