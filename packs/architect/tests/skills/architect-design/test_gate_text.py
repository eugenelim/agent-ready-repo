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

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

PACK_ROOT = Path(__file__).resolve().parents[3]
RUBRIC = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-design"
    / "references"
    / "design-doc-rubric.md"
)
SKILL = PACK_ROOT / ".apm" / "skills" / "architect-design" / "SKILL.md"
CONVERGENCE_LOOP = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-design"
    / "references"
    / "convergence-loop.md"
)
GATE_SCRIPT = (
    PACK_ROOT / ".apm" / "skills" / "architect-design" / "scripts" / "check_document_architecture.py"
)
TESTDATA = Path(__file__).resolve().parent / "testdata"
REFERENCE_DOCUMENT = TESTDATA / "telemetry-endpoint-default-design.md"
DEFECT_DOCUMENT = TESTDATA / "precheck-defects.md"

# The seven identifiers each carrying a planted defect in DEFECT_DOCUMENT —
# same set as PRECHECK_GATES below, named again here so AC-0049's own test
# does not depend on that constant existing for an unrelated reason.
DEFECT_GATES = ("DA1", "DA2", "DA4", "DA6", "DA7", "DA8", "DA9")


def _load_gate() -> ModuleType:
    """Load the DA3/DA10 gate script from its repository path, never by bare import.

    Matches `test_gate_script.py`'s loader under the same pack-unique name:
    the text/script split here is about what each suite asserts, not a bar
    on importing the module (T4a's `Tests:` in `plan.md`).
    """
    spec = importlib.util.spec_from_file_location("architect_design_gate_script", GATE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["architect_design_gate_script"] = module
    spec.loader.exec_module(module)
    return module


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


# --- Reporting (AC-0064, AC-0065, AC-0066, AC-0067) ---
#
# Scoped to the step 6 body and the convergence loop's own intro/cycle
# sections, rather than the whole file: a whole-file `assertIn` would be
# satisfied by any stray mention of a gate identifier or the word "verdict"
# living elsewhere in the document, which is not the property these
# criteria name — the closed set `DA1`-`DA10` reported with a verdict.


def _skill_step6_body() -> str:
    """Return `SKILL.md` step 6's own body, flattened, stopping at step 7."""
    text = SKILL.read_text(encoding="utf-8")
    after = text.split(
        "6. **Self-check against the rubric**", 1
    )[1]
    before = after.split("7. **Converge against review.**", 1)[0]
    return _flat(before)


def _convergence_intro_body() -> str:
    """Return the loop's opening paragraphs, before `## The cycle`."""
    text = CONVERGENCE_LOOP.read_text(encoding="utf-8")
    return _flat(text.split("## The cycle", 1)[0])


def _convergence_review_step_body() -> str:
    """Return cycle step 1 ("Review"), flattened, stopping at step 2."""
    text = CONVERGENCE_LOOP.read_text(encoding="utf-8")
    after = text.split("1. **Review.**", 1)[1]
    before = after.split("2. **Auto-resolve", 1)[0]
    return _flat(before)


def test_skill_step6_requires_every_gate_reported_by_identifier_and_verdict() -> None:
    """AC-0064: closed set `DA1`-`DA10` plus the word "verdict", not a phrase."""
    body = _skill_step6_body()
    for gate in ALL_GATES:
        assert f"`{gate}`" in body, gate
    assert "verdict" in body
    assert "before the draft is shown" in body or "before showing the draft" in body


def test_convergence_loop_review_pass_requires_every_gate_identifier_with_a_verdict() -> None:
    """AC-0065: each review pass reports the closed set, each with a verdict."""
    body = _convergence_review_step_body()
    for gate in ALL_GATES:
        assert f"`{gate}`" in body, gate
    assert "verdict" in body


def test_convergence_loop_states_it_requires_and_invokes_no_script() -> None:
    """AC-0066: pins the corrected sentence at convergence-loop.md's intro."""
    body = _convergence_intro_body()
    assert "requires and invokes no script" in body
    assert "check_document_architecture.py" in body
    assert "a human author or an adopter's CI runs it" in body
    assert "outside this loop" in body


def test_convergence_loop_states_what_the_shipped_script_costs_and_does_not_cost() -> None:
    """AC-0067: no unconditional claim that shipping a script forfeits a
    pack property; the intro instead states the property kept and the
    property the script trades."""
    body = _convergence_intro_body()
    assert "forfeit" not in body
    assert "pure-prose and zero-config" in body
    assert "costs the loop nothing" in body
    assert "it decides neither the other" in body


# --- T4a: the prechecks walked against a document, not a template ---------
#
# AC-0045, AC-0018, AC-0025 and AC-0044 are the mechanically decidable half of
# T4a. AC-0046 and AC-0051 — whether a precheck *fires* — are not decidable
# from a fixed set of tokens without also re-deciding a reviewer's judgment
# call, so they are walked by hand and recorded in
# `docs/specs/architect-design-document-gates/notes/verification-ledger.md`
# rather than asserted here.

_PLACEHOLDER_TOKEN_PATTERN = re.compile(r"<(?!!--)[^>\n]+>")


def test_reference_document_carries_no_placeholder_token() -> None:
    """AC-0045: a half-filled skeleton cannot serve as the corpus.

    Excludes an HTML comment (`<!-- ... -->`) from the scan: the template's
    own placeholder shape is a bare `<...>` slot like `<element name>`, never
    a comment marker, and the reference document's own corpus-baseline note
    is carried in one.
    """
    text = REFERENCE_DOCUMENT.read_text(encoding="utf-8")
    assert _PLACEHOLDER_TOKEN_PATTERN.findall(text) == []


def test_da3_reports_no_finding_on_the_reference_document() -> None:
    """AC-0018: the clean half of the paragraph budget, against an authored
    document rather than the shipped templates (see `plan.md`'s T2 `Tests:`
    for why the corpus moved here)."""
    gate = _load_gate()
    findings = gate.evaluate_target(PACK_ROOT, REFERENCE_DOCUMENT)
    da3_findings = [finding for finding in findings if finding.gate == "DA3"]
    assert da3_findings == []


def test_reference_document_word_count_sits_within_20_percent_of_the_derivation() -> None:
    """AC-0025: gives AC-0024's derivation an oracle independent of its own
    arithmetic."""
    gate = _load_gate()
    text = REFERENCE_DOCUMENT.read_text(encoding="utf-8")
    word_count = gate.count_words(text)
    density_figure = 2178
    assert abs(word_count - density_figure) / density_figure <= 0.20, word_count


def _reference_document_header() -> str:
    """Return the reference document's leading HTML-comment header."""
    text = REFERENCE_DOCUMENT.read_text(encoding="utf-8")
    match = re.match(r"\A<!--(.*?)-->", text, re.DOTALL)
    assert match, "reference document carries no leading HTML-comment header"
    return _flat(match.group(1))


def test_reference_document_header_states_its_corpus_purpose_governs_an_edit() -> None:
    """AC-0044: a baseline, so an edit nobody re-walks invalidates the walk."""
    header = _reference_document_header()
    assert "baseline" in header
    assert "re-walk of all seven prechecks" in header
    assert "fresh record" in header


def test_defect_document_names_all_seven_prechecks() -> None:
    """AC-0049: one planted defect per precheck; the document names all seven
    so the walk it backs is attributable rather than incidental."""
    text = DEFECT_DOCUMENT.read_text(encoding="utf-8")
    for gate_id in DEFECT_GATES:
        assert gate_id in text, gate_id
    assert set(DEFECT_GATES) == set(PRECHECK_GATES)


def test_defect_document_states_it_is_deliberately_non_conforming() -> None:
    """AC-0049's second half: the document says so in its own body."""
    text = DEFECT_DOCUMENT.read_text(encoding="utf-8")
    assert "deliberately non-conforming" in text.lower() or "Deliberately non-conforming" in text
