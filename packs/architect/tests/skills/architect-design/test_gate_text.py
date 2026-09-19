"""`DA1`-`DA10` construction tests for the authoring rubric's gate text.

`design-doc-rubric.md` states the ten document-architecture gates ADR-0118
`D5` fixes, under its existing `## Cross-cutting` heading (a `##` heading is
frozen by `test_design_scope_routing.py`'s `AUTHOR_EXTRA`; the gates sit in a
new `###`/`####` sub-structure instead — see `plan.md`'s Design (LLD)).

Every assertion below is scoped to **one gate's own section body**, sliced on
the `#### `DA<n>`` boundaries the rubric ships. A whole-file
``assertIn("3,300", text)`` would pass on any second mention of the bound, and
seven prechecks living in one file would cross-satisfy each other; slicing on
the gate boundary is what keeps each criterion attributable to its own gate.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
RUBRIC = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-design"
    / "references"
    / "design-doc-rubric.md"
)

# The seven hybrids that carry a precheck. `DA5` is judgment-only and carries
# none; `DA3` and `DA10` are mechanical and the script decides them directly.
PRECHECK_GATES = ("DA1", "DA2", "DA4", "DA6", "DA7", "DA8", "DA9")
ALL_GATES = tuple(f"DA{n}" for n in range(1, 11))


def _text() -> str:
    return RUBRIC.read_text(encoding="utf-8")


def _flat(fragment: str) -> str:
    """Collapse a fragment's whitespace so a wrapped line still matches."""
    return " ".join(fragment.split())


def _gate_bodies() -> dict[str, str]:
    """Split the rubric into one body per `#### `DA<n>`` sub-heading.

    Bounded to the `#### ` markers this file ships, so a criterion asserted
    against one gate's body cannot be satisfied by a second gate's text or by
    prose living anywhere else in the rubric.
    """
    text = _text()
    pattern = re.compile(r"^#### `(DA\d{1,2})`\s*$", re.M)
    any_heading = re.compile(r"^#{2,4} ", re.M)
    matches = list(pattern.finditer(text))
    assert matches, "no `#### `DA<n>`` gate sub-headings found in the rubric"
    bodies: dict[str, str] = {}
    for match in matches:
        start = match.end()
        following = any_heading.search(text, start)
        end = following.start() if following else len(text)
        gate_id = match.group(1)
        assert gate_id not in bodies, f"duplicate gate sub-heading: {gate_id}"
        bodies[gate_id] = _flat(text[start:end])
    return bodies


def _cross_cutting_body() -> str:
    """Return the `## Cross-cutting` section, flattened, stopping at `## `."""
    text = _text()
    after = text.split("## Cross-cutting", 1)[1]
    end = len(after)
    match = re.search(r"^## ", after, re.M)
    if match:
        end = match.start()
    return _flat(after[:end])


def _implementation_mapping_body() -> str:
    """Return the `## Implementation Mapping` section, flattened."""
    text = _text()
    after = text.split("## Implementation Mapping", 1)[1]
    end = len(after)
    match = re.search(r"^## ", after, re.M)
    if match:
        end = match.start()
    return _flat(after[:end])


# --- All ten gates carry an identifier and a severity (AC-0028, AC-0031, AC-0032) ---


def test_the_rubric_states_every_gate_identifier() -> None:
    text = _text()
    for gate in ALL_GATES:
        assert f"`{gate}`" in text, gate


SEVERITY_BY_GATE = {
    "DA1": "🟨",
    "DA2": "🟧",
    "DA3": "🟨",
    "DA4": "🟧",
    "DA5": "🟥",
    "DA6": "🟨",
    "DA7": "🟧",
    "DA8": "🟥",
    "DA9": "🟨",
    "DA10": "🟧",
}

TAG_BY_GATE = {
    "DA1": "🧭",
    "DA2": "🧭",
    "DA3": "🔧",
    "DA4": "🧭",
    "DA5": "🧭",
    "DA6": "🧭",
    "DA7": "🧭",
    "DA8": "🧭",
    "DA9": "🧭",
    "DA10": "🔧",
}


def test_every_gate_carries_its_fixed_severity_and_tag() -> None:
    """Severity assignment is fixed (AC-0032); tag follows mechanizability (AC-0031)."""
    text = _text()
    table_row = re.compile(r"\|\s*`(DA\d{1,2})`\s*\|\s*(🧭|🔧)\s*\|\s*(🟥|🟧|🟨)\s*\|")
    seen = {}
    for match in table_row.finditer(text):
        gate, tag, severity = match.group(1), match.group(2), match.group(3)
        seen[gate] = (tag, severity)
    assert set(seen) == set(ALL_GATES), sorted(set(ALL_GATES) - set(seen))
    for gate in ALL_GATES:
        tag, severity = seen[gate]
        assert tag == TAG_BY_GATE[gate], (gate, tag)
        assert severity == SEVERITY_BY_GATE[gate], (gate, severity)


def test_da7_carries_its_identifier_severity_and_tag_on_its_existing_item() -> None:
    """AC-0036: identifier/severity/tag land on the existing Cross-cutting item."""
    body = _cross_cutting_body()
    assert "`DA7` 🟧 🧭" in body
    assert "one named question" in body


def test_da8_carries_its_identifier_severity_and_tag_on_its_existing_item() -> None:
    """AC-0037: identifier/severity/tag land on the existing Implementation Mapping item."""
    body = _implementation_mapping_body()
    assert "`DA8` 🟥 🧭" in body
    assert "the complete model set" in body


def test_the_rubric_states_what_a_severity_means_for_an_author() -> None:
    """AC-0033: orders pre-draft fixes, in the vocabulary the reviewer applies."""
    # The severity-meaning statement is the intro prose immediately above the
    # first `#### `DA1`` sub-heading, inside the new `### Document-architecture
    # gates` block — not any single gate's own body.
    text = _text()
    intro = _flat(
        text.split("### Document-architecture gates", 1)[1].split(
            "#### `DA1`", 1
        )[0]
    )
    assert "before a draft is shown" in intro
    assert "same vocabulary the reviewer" in intro
    assert "never disagree about which failure matters more" in intro


# --- DA10 — size trigger (AC-0024, AC-0026, AC-0027) ---


def test_da10_derivation_recomputes_to_the_stated_bound() -> None:
    """AC-0024: the stated arithmetic, recomputed, reaches the stated bound."""
    body = _gate_bodies()["DA10"]

    def _int(pattern: str) -> int:
        match = re.search(pattern, body)
        assert match, pattern
        return int(match.group(1).replace(",", ""))

    def _float(pattern: str) -> float:
        match = re.search(pattern, body)
        assert match, pattern
        return float(match.group(1))

    scaffolding = _int(r"(\d[\d,]*) words of scaffolding")
    table_count = _int(r"(\d+) model tables at")
    table_rows = _int(r"model tables at (\d+) rows of")
    table_words = _int(r"model tables at \d+ rows of (\d+) words")
    diagram_count = _int(r"(\d+) diagrams at")
    diagram_words = _int(r"diagrams at (\d+) words of labels")
    section_count = _int(r"(\d+) sections at")
    section_sentences = _int(r"sections at (\d+) sentences of")
    section_words = _int(r"sentences of (\d+) words")
    density = _int(r"([\d,]+) words at intended density")
    headroom = _float(r"headroom factor of ([\d.]+)")
    bound = _int(r"bound of \*\*([\d,]+) words\*\*")

    computed_density = (
        scaffolding
        + table_count * table_rows * table_words
        + diagram_count * diagram_words
        + section_count * section_sentences * section_words
    )
    assert computed_density == density, (computed_density, density)
    assert round(computed_density * headroom, -2) == bound, (
        computed_density * headroom,
        bound,
    )
    assert bound == 3300


def test_da10_states_the_scaffolding_reproduction_command() -> None:
    body = _gate_bodies()["DA10"]
    assert "strip frontmatter" in body
    assert "strip HTML-comment spans" in body
    assert "[A-Za-z0-9]" in body


def test_da10_hands_a_document_over_the_bound_to_decomposition_and_decides_no_split() -> None:
    """AC-0026."""
    body = _gate_bodies()["DA10"]
    assert "references/decomposition-rubric.md" in body
    assert "decides no split itself" in body


def test_da10_states_the_companion_views_remedy() -> None:
    """AC-0027."""
    body = _gate_bodies()["DA10"]
    assert "moves detail to companion views and evidence links" in body


# --- Prechecks (AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041) ---


def test_da1_precheck_rejects_future_tense_or_prior_state() -> None:
    body = _gate_bodies()["DA1"]
    for token in ("will be", "previously", "used to", "deprecation date"):
        assert token in body, token


def test_da2_precheck_rejects_an_unnamed_cross_reference_against_the_closed_list() -> None:
    body = _gate_bodies()["DA2"]
    for token in (
        "see above",
        "see below",
        "as described above",
        "as described below",
        "the previous section",
        "the following section",
        "the table below",
        "the diagram above",
    ):
        assert token in body, token
    assert "the structural model above" in body


def test_da4_precheck_requires_a_table_or_diagram_before_prose() -> None:
    body = _gate_bodies()["DA4"]
    assert "table or a fenced diagram" in body
    assert "never prose" in body


def test_da6_precheck_rejects_revision_history_or_decision_log() -> None:
    body = _gate_bodies()["DA6"]
    assert "Revision History" in body
    assert "Decision Log" in body


def test_da9_precheck_rejects_headings_that_accumulate_evidence() -> None:
    body = _gate_bodies()["DA9"]
    for token in ("Appendix", "References", "Evidence"):
        assert token in body, token


def test_da9_precheck_is_scoped_to_a_routed_document() -> None:
    """AC-0047's worked case: the unrouted `assets/design-doc.md` never fires."""
    body = _gate_bodies()["DA9"]
    assert "authored document that has been routed to a scope" in body
    assert "assets/*.md" in body
    assert "assets/design-doc.md" in body


def test_da7_precheck_names_no_second_differently_worded_obligation() -> None:
    """AC-0036: the gate's own body points at the existing item, not a new one."""
    body = _gate_bodies()["DA7"]
    assert "Cross-cutting checklist item" in body
    assert "one named question" in body


def test_da8_precheck_requires_every_mapping_row_to_resolve_to_a_named_element() -> None:
    """AC-0037's second sentence."""
    body = _gate_bodies()["DA8"]
    assert "every implementation-mapping row" in body
    assert "resolve to an element the document's models name" in body


def test_each_precheck_states_its_verdict_is_the_reviewers() -> None:
    """AC-0042."""
    bodies = _gate_bodies()
    for gate in PRECHECK_GATES:
        assert "verdict is the reviewer's" in bodies[gate], gate


def test_each_precheck_states_it_applies_to_an_authored_document() -> None:
    """AC-0047."""
    bodies = _gate_bodies()
    for gate in PRECHECK_GATES:
        assert "applies to an authored document" in bodies[gate], gate


def test_exactly_seven_prechecks_exist_and_da5_carries_none() -> None:
    """AC-0048: the count is what keeps judgment-only textually distinct."""
    bodies = _gate_bodies()
    precheck_gates = [
        gate
        for gate in ALL_GATES
        if "precheck" in bodies[gate].lower() and "carries no precheck" not in bodies[gate]
    ]
    assert set(precheck_gates) == set(PRECHECK_GATES), sorted(
        set(PRECHECK_GATES) ^ set(precheck_gates)
    )
    assert len(precheck_gates) == 7
    assert "carries no precheck" in bodies["DA5"]


def test_da5_names_no_automated_measure_and_no_forbidden_tripwire_token() -> None:
    """AC-0034 (this home): the obligation rests on the positive statement."""
    body = _gate_bodies()["DA5"]
    assert "no automated measure" in body
    assert "similarity score" not in body
    assert "distance metric" not in body
