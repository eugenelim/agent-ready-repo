"""Construction tests for the design-system published contract.

The contract this pins has two halves that pull in opposite directions, so both
are asserted here rather than left to review. The pack ships no design value —
that half is already enforced mechanically over every Markdown file in the pack
by the repository's agnosticism lint, and the assertions here only pin that the
rule is *published* where a run can read it. A run resolves project-specific
values — that half has no mechanical gate at all, because the values land in an
adopter's output directory, so the assertions here pin the authority model, the
route set, and the refusal to fill an axis nothing decided.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "design-system"

SKILL = SKILL_ROOT / "SKILL.md"
TEMPLATE = SKILL_ROOT / "assets" / "token-taxonomy-template.md"
REFERENCE_ROOT = SKILL_ROOT / "references"
EVALS = SKILL_ROOT / "evals" / "evals.json"
EVAL_QUERIES = SKILL_ROOT / "evals" / "eval_queries.json"

ROUTES = ("inherit", "extend", "originate", "refine")

# The precedence rungs, highest first. Order is asserted, not just membership:
# a precedence whose rungs appear in any order is not a precedence.
RUNGS = (
    "stated-constraint",
    "approved-visual-target",
    "approved-direction",
    "incumbent-system",
    "platform-convention",
    "derivation",
)

# The fifteen axes `creative-direction` commits, verbatim. Renaming an axis
# upstream must redden here, because the map from axis to system domain is how
# a value's authority is traced.
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

# Every domain the skill may resolve. Each must be reached by at least one axis.
DOMAINS = (
    "spatial structure",
    "spacing and rhythm",
    "typography",
    "color",
    "shape and containment",
    "depth",
    "graphic language",
    "motion",
)

FAILURE_MODES = (
    "empty taxonomy",
    "universal defaults",
    "token proliferation",
    "direction drift",
    "parallel system",
    "screenshot transcription",
    "inaccessible fidelity",
    "implementation leakage",
)

# Wording from the superseded taxonomy-only contract. Any survivor means a
# reader can still find the old rule and follow it.
OBSOLETE_TERMS = (
    "the reader produces the numbers",
    "the reader supplies values",
    "reader decides",
    "it does not implement token values",
    "without choosing implementation values",
    "leave the value column as a prompt",
    "resolving it is the builder's step",
    "the resolved numbers stay with the reader",
    "holds no resolved values",
    "no values, ever",
)

# Named products the skill must not pick for an adopter. It supports every
# binding shape and names none of them as the answer.
#
# Only product names belong here. An earlier revision also banned the phrase
# "required binding", which matched the sentence stating the prohibition —
# a negative pin that fires on its own rule is worse than no pin.
IMPOSED_TECHNOLOGY_TERMS = (
    "style dictionary",
    "figma tokens",
    "must be implemented as",
    "we recommend using",
)

REQUIRED_EVAL_SCENARIOS = {
    1: "mature incumbent system",
    2: "greenfield distinctive direction",
    3: "approved visual target",
    4: "rejected category default",
    5: "brownfield conflict",
    6: "insufficient authority",
    7: "accessibility conflict",
}


def _read(path: Path) -> str:
    """Read a skill-owned text file."""
    return path.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    """Lowercase *text* with every whitespace run collapsed to one space.

    Every phrase assertion below runs against this form. Pinning a phrase
    against the raw bytes makes the suite fail on a reflowed paragraph, which
    reddens for a change that altered no rule — the loudest way to teach a
    reader to stop trusting the check.
    """
    return re.sub(r"\s+", " ", text).lower()


def _skill_text() -> str:
    """Return all contract-bearing design-system prose."""
    parts = [
        _read(SKILL),
        _read(TEMPLATE),
        _read(REFERENCE_ROOT / "value-derivation.md"),
        _read(REFERENCE_ROOT / "incumbent-systems.md"),
        _read(REFERENCE_ROOT / "token-taxonomy-derivation.md"),
        _read(REFERENCE_ROOT / "atomic-composition.md"),
    ]
    return "\n".join(parts)


# The four value shapes, spelled exactly as the repository's experience
# agnosticism lint spells them. This suite is pack-local and may not read above
# its own pack, so the patterns are copied rather than imported — and a copy
# drifts, which it already did once: an earlier revision kept the lint's
# digit-requiring hex lookahead but dropped the companion rule for `#fff`, and
# dropped `vmin`/`vmax` and the decimal-seconds rule, so `#ccc`, `0.3s` and
# `24vmin` passed here while the lint caught every one.
#
# `tests/roster/test_design_system_eval_guard_matches_the_lint.py` is what
# keeps the copy honest: it reads both sides and fails when they diverge. That
# test lives in the roster tree precisely because comparing them requires
# reading the lint, which a pack test may not do.
VALUE_SHAPE_RULES = (
    (
        "color literal",
        re.compile(
            r"#(?=[0-9a-fA-F]*[0-9])[0-9a-fA-F]{3}\b"
            r"|#(?=[0-9a-fA-F]*[0-9])[0-9a-fA-F]{6}\b"
            r"|#([0-9a-fA-F])\1{2}\b"
            r"|\brgba?\s*\(|\bhsla?\s*\("
        ),
    ),
    (
        "dimension / duration literal",
        re.compile(
            r"\b\d+(\.\d+)?\s?(px|ms|rem|em|pt|vh|vw|vmin|vmax)\b"
            r"|\b\d+\.\d+\s?s\b"
        ),
    ),
    ("ratio literal", re.compile(r"\b\d+(\.\d+)?\s*:\s*1\b")),
    (
        "named easing curve",
        re.compile(r"\bcubic-bezier\b|\bease-in-out\b|\bease-in\b|\bease-out\b"),
    ),
)


def _assert_no_value_shapes(text: str, where: str) -> None:
    """Fail when *text* carries a shipped design value in any common notation."""
    for label, pattern in VALUE_SHAPE_RULES:
        match = pattern.search(text)
        assert match is None, f"{label} {match.group(0)!r} in {where}"


def _eval_payloads() -> tuple[dict[str, object], list[dict[str, object]]]:
    """Load the design-system eval corpus and trigger queries."""
    evals = json.loads(_read(EVALS))
    queries = json.loads(_read(EVAL_QUERIES))
    assert isinstance(evals, dict)
    assert isinstance(queries, list)
    assert all(isinstance(query, dict) for query in queries)
    return evals, queries


def test_four_routes_are_published_in_one_skill() -> None:
    """AC-0001 and AC-0002 pin the route set and its selection rubric."""
    skill = _read(SKILL)

    for route in ROUTES:
        assert re.search(rf"\|\s*`?{route}`?\s*\|", skill), f"route {route} missing from the route table"

    assert re.search(r"^## Selection rubric$", skill, re.MULTILINE)

    # One skill, not several: the skill must not route a design-system domain
    # away to a sibling registration that does not exist.
    for absent in ("design-system-foundations", "typography-system", "color-system", "motion-system"):
        assert absent not in skill.lower(), f"{absent} is not a skill in this pack"


def test_the_invariant_has_both_clauses() -> None:
    """AC-0003 pins the replacement for the blanket no-values contract."""
    skill = _read(SKILL)
    lowered = _flat(skill)

    # Clause one — the pack ships nothing universal.
    assert "universal" in lowered
    assert re.search(r"do not ship universal design values", lowered)

    # Clause two — a run resolves what its authority supports.
    assert re.search(r"derive project-specific values", lowered)
    assert "authority" in lowered

    # The two clauses must sit together, so neither can be read alone.
    assert re.search(
        r"do not ship universal design values.{0,200}derive project-specific values",
        lowered,
        re.DOTALL,
    )


def test_authority_precedence_is_ordered_and_axis_scoped() -> None:
    """AC-0004 pins the rungs, their order, and the axis-scoped override rule."""
    skill = _read(SKILL)

    # Match the rung in its table-cell form. A bare substring search also hits
    # `references/incumbent-systems.md`, which put the `incumbent-system` rung
    # ahead of every other one and failed the order check for a filename.
    positions = []
    for rung in RUNGS:
        cell = re.search(rf"^\|\s*`{re.escape(rung)}`\s*\|", skill, re.MULTILINE)
        assert cell is not None, f"precedence rung {rung} is missing from the rung table"
        positions.append(cell.start())
    assert positions == sorted(positions), "precedence rungs are not in descending order"

    lowered = _flat(skill)
    assert "only on the axis it decides" in lowered
    assert "hands down every axis it left open" in _flat(skill)


def test_accessibility_is_a_floor_outside_the_ranking() -> None:
    """AC-0005 pins the floor as non-rankable, not as a low rung."""
    lowered = _flat(_skill_text())

    assert "floor" in lowered
    assert re.search(r"(never ranked|not ranked|outside the (ranking|precedence))", lowered)
    assert "adaptation" in lowered

    # The shared checklist is pointed at, not restated.
    assert "../design-review/references/quality-floor.md" in _skill_text()


def test_every_axis_maps_to_exactly_one_domain() -> None:
    """AC-0006 pins the axis-to-domain map that makes a value traceable."""
    derivation = _read(REFERENCE_ROOT / "value-derivation.md")

    for axis in AXES:
        assert axis in derivation, f"axis {axis} is absent from the derivation map"

    for domain in DOMAINS:
        assert domain in derivation.lower(), f"domain {domain} is absent from the derivation map"


def test_platform_default_is_split_before_it_is_called_unresolved() -> None:
    """AC-0007 pins both upstream meanings of `[platform-default]`.

    Upstream gives the token two jobs: `explore` marks an axis the platform
    genuinely owns, and `converge` uses the same token for undecided while
    forbidding it only on the seven structural axes. Collapsing them would
    report typography, color and motion unresolved for a normally converged
    platform-targeted direction, so the split is asserted, not the merge.
    """
    contract = _skill_text()
    lowered = _flat(contract)

    assert "[platform-default]" in contract

    # The platform-owned reading resolves rather than stalls.
    assert "platform-convention" in lowered
    assert re.search(r"target surface", lowered)

    # The undecided reading stalls rather than invents.
    assert re.search(r"(unresolved|not resolved)", lowered)
    assert re.search(r"missing authority", lowered)
    assert re.search(r"(never|not) filled", lowered) or "do not fill" in lowered

    # A structural axis left at the token is a gap in the direction upstream.
    assert "structural" in lowered


def test_a_visual_target_yields_relationships_and_never_a_value() -> None:
    """AC-0004 and AC-0008 pin the rung's no-value rule and its reading rule.

    Both the upstream writer and the downstream implementer already state that
    this rung supplies no color, type, spacing or motion value. This skill sits
    between them, so it adopts the same rule rather than ranking the target
    above the direction for values it cannot supply.
    """
    contract = _skill_text()
    lowered = _flat(contract)

    for phrase in ("relative scale", "density", "hierarchy", "graphic language"):
        assert phrase in lowered

    assert re.search(r"supplies no value|binds no value|never supplies a value", lowered)
    assert re.search(r"(not|never).{0,40}measure", lowered, re.DOTALL)
    assert "pixel" in lowered or "image extraction" in lowered


def test_the_artifact_records_authority_relationships_and_proving_set() -> None:
    """AC-0009, AC-0010, and AC-0011 pin the artifact's new sections."""
    template = _read(TEMPLATE)
    lowered = _flat(template)

    assert "## Authority" in template
    for field in ("route", "direction source", "incumbent source", "visual target"):
        assert field in lowered, f"authority field {field} missing from the template"

    assert "## Rules implementation must preserve" in template
    assert "prohibited" in lowered
    assert "## Proving set" in template
    assert "## Unresolved decisions" in template

    # The artifact identity downstream reads by literal is unchanged.
    assert "type: token-taxonomy" in template


def test_brownfield_changes_are_itemised() -> None:
    """AC-0012 pins the retained / extended / replaced record and its refusals."""
    contract = _skill_text()
    lowered = _flat(contract)

    for word in ("retained", "extended", "replaced"):
        assert word in lowered

    assert "parallel system" in lowered
    assert re.search(r"(do not|never) rename", lowered)
    assert re.search(r"inherit before extend", lowered)
    assert re.search(r"extend before replac", lowered)


def test_no_value_and_no_obsolete_contract_survives_in_pack_source() -> None:
    """AC-0003 and AC-0013 pin that the old rule left no readable survivor."""
    contract = _skill_text()
    lowered = _flat(contract)

    for term in OBSOLETE_TERMS:
        assert term not in lowered, f"obsolete contract wording survives: {term!r}"

    _assert_no_value_shapes(contract, "the skill corpus")


def test_the_eval_corpus_carries_no_value_shapes() -> None:
    """AC-0013 covers the surface the repository's agnosticism lint cannot.

    That lint collects `*.md` only, by its own documented scope, so the JSON
    eval files are never scanned. An eval that illustrates a resolved value by
    printing one would ship a universal default through the one door the gate
    does not watch.
    """
    _assert_no_value_shapes(_read(EVALS), "evals.json")
    _assert_no_value_shapes(_read(EVAL_QUERIES), "eval_queries.json")


def test_no_technology_is_imposed_as_the_binding() -> None:
    """AC-0014 pins technology-agnostic binding across the supported shapes."""
    lowered = _flat(_skill_text())

    for shape in ("theme object", "custom-propert", "constants", "design-only"):
        assert shape in lowered, f"binding shape {shape} is unsupported"

    for imposed in IMPOSED_TECHNOLOGY_TERMS:
        assert imposed not in lowered, f"a technology is imposed: {imposed!r}"


def test_the_refused_failure_modes_are_published() -> None:
    """AC-0016 pins the failure-mode inventory the skill refuses."""
    lowered = _flat(_skill_text())

    for mode in FAILURE_MODES:
        assert mode in lowered, f"failure mode {mode!r} is not published"


def test_the_entrypoint_stays_a_control_plane() -> None:
    """AC-0017 pins progressive disclosure and the retained write declaration."""
    skill = _read(SKILL)

    # The declaration lines a roster test fixes literally.
    assert "**Writes:** `<output_dir>/tokens/<slug>.md`" in skill
    assert "**Confinement:** `references/containment.md`" in skill

    # Method lives behind references the skill routes to, not inline.
    assert "references/value-derivation.md" in skill
    assert "references/incumbent-systems.md" in skill
    assert re.search(r"^## Conditional reference routing$", skill, re.MULTILINE)

    # The control plane carries no per-domain method body of its own.
    for method_heading in ("### Typography", "### Color", "### Spacing", "### Motion"):
        assert method_heading not in skill, f"{method_heading} belongs in a reference"


def test_eval_corpus_covers_every_required_scenario() -> None:
    """AC-0018 pins one eval case per scenario the contract must distinguish."""
    evals, queries = _eval_payloads()
    cases = evals.get("evals")
    assert isinstance(cases, list)
    assert evals.get("skill_name") == "design-system"

    case_text_by_id = {
        case["id"]: json.dumps(case, sort_keys=True).lower()
        for case in cases
        if isinstance(case.get("id"), int)
    }
    for case_id, scenario in REQUIRED_EVAL_SCENARIOS.items():
        assert case_id in case_text_by_id, f"eval case {case_id} ({scenario}) is missing"
        assert scenario in case_text_by_id[case_id], (
            f"eval case {case_id} does not name its scenario {scenario!r}"
        )

    # Route coverage across the corpus.
    corpus = json.dumps({"evals": cases, "queries": queries}).lower()
    for route in ROUTES:
        assert route in corpus

    # The behavioural discriminators between old contract and new.
    assert "resolved value" in corpus
    assert "unresolved" in corpus
    assert "measured" in corpus

    positive = [q["query"].lower() for q in queries if q.get("should_trigger") is True]
    negative = [q["query"].lower() for q in queries if q.get("should_trigger") is False]
    assert any("incumbent" in q for q in positive)
    assert any("concrete" in q or "resolve" in q for q in positive)
    assert any("component code" in q or "stylesheet" in q for q in negative)
    assert any("rank the aesthetic goals" in q or "emotional direction" in q for q in negative)
