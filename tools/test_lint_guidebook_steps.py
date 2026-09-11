"""Construction tests for the guidebook step contract and its lint.

The contract lives in `guides/AGENTS.md` § The guidebook step contract. That
file is the single source of the obligation identifiers, the closed set of
judgement kinds, and the prohibited vocabulary — this module never restates
them, because a check that carries its own copy of what it checks cannot
detect the two drifting apart.

Covers AC-0001 (the contract is stated and binding) for
`docs/specs/pack-guidebook-walkability/spec.md`. The lint's own cases
(AC-0002, AC-0003, AC-0014, AC-0022) arrive with the lint in T2.
"""

from __future__ import annotations

import re
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = REPO_ROOT / "guides" / "AGENTS.md"

_LINT_SPEC = importlib.util.spec_from_file_location(
    "lint_guidebook_steps", REPO_ROOT / "tools" / "lint-guidebook-steps.py"
)
assert _LINT_SPEC is not None and _LINT_SPEC.loader is not None
lint_guidebook_steps = importlib.util.module_from_spec(_LINT_SPEC)
sys.modules[_LINT_SPEC.name] = lint_guidebook_steps
_LINT_SPEC.loader.exec_module(lint_guidebook_steps)

SECTION_HEADING = "## The guidebook step contract"

# The normative sentence makes the list binding rather than merely present.
# Matched on its load-bearing clause, not on exact prose, so an editorial
# rewording does not red while a deletion does.
NORMATIVE = re.compile(r"every guidebook step must carry every obligation", re.I)

JUDGEMENT_HEADING = "### Judgement kinds"
VOCABULARY_HEADING = "### Prohibited vocabulary"


def _contract_section() -> str:
    """The contract section's text, or "" when the section is absent."""
    text = CONTRACT.read_text(encoding="utf-8")
    if SECTION_HEADING not in text:
        return ""
    body = text.split(SECTION_HEADING, 1)[1]
    # Ends at the next same-level heading.
    return body.split("\n## ", 1)[0]


def obligation_ids() -> tuple[str, ...]:
    """Identifiers from the contract's obligation table, in document order.

    Scoped to the section's preamble — the text before its first `###`
    subheading — because the how-a-step-is-written table below also opens each
    row with a backticked identifier. A whole-section parse read both tables
    and reported every obligation twice; the duplicate assertion caught it.
    """
    return lint_guidebook_steps.obligation_ids_from_contract(
        CONTRACT.read_text(encoding="utf-8")
    )


def judgement_kinds() -> tuple[str, ...]:
    """The closed set of judgement kinds the contract admits."""
    return lint_guidebook_steps.judgement_kinds_from_contract(
        CONTRACT.read_text(encoding="utf-8")
    )


def prohibited_terms() -> tuple[str, ...]:
    """The lexical terms no guidebook step may contain."""
    return lint_guidebook_steps.prohibited_terms_from_contract(
        CONTRACT.read_text(encoding="utf-8")
    )


# --------------------------------------------------------------------------
# AC-0001 — the contract is stated, binding, and carries its four parts.
#
# Both halves fail independently: identifiers without the normative statement,
# and the statement without the identifiers. An earlier draft of the spec had
# this oracle compare the identifiers against the spec's own obligation table;
# that table is numbered rather than identified, so the comparison was not
# implementable. The obligation set's agreement with the *lint* is AC-0003's,
# which is where the real drift risk sits.
# --------------------------------------------------------------------------

def test_ac0001_the_contract_section_exists() -> None:
    assert _contract_section(), f"{CONTRACT} carries no {SECTION_HEADING!r}"


def test_ac0001_the_contract_is_binding_not_merely_present() -> None:
    assert NORMATIVE.search(_contract_section()), (
        "the contract enumerates obligations without stating that every step "
        "must carry them — a list with no normative force"
    )


def test_ac0001_the_contract_enumerates_obligations_by_identifier() -> None:
    ids = obligation_ids()
    assert ids, "the contract states no obligation identifiers"
    assert len(set(ids)) == len(ids), f"duplicate obligation identifier: {ids}"


def test_ac0001_the_contract_declares_its_judgement_kinds() -> None:
    kinds = judgement_kinds()
    assert kinds, f"the contract carries no {JUDGEMENT_HEADING!r} closed set"
    # AC-0014 rests on this: a judgement kind naming a structural obligation
    # would let a human check restate a machine-owned one by construction.
    overlap = set(kinds) & set(obligation_ids())
    assert not overlap, (
        f"judgement kind(s) name a machine-owned obligation: {sorted(overlap)}"
    )


def test_ac0001_the_contract_declares_its_prohibited_vocabulary() -> None:
    assert prohibited_terms(), (
        f"the contract carries no {VOCABULARY_HEADING!r} terms, so AC-0009, "
        "AC-0013 and AC-0020 have nothing lexical to scan for"
    )


# --------------------------------------------------------------------------
# T2 — construction tests for the executable contract enforcement.
# --------------------------------------------------------------------------

def _obligation_with(contract, label_fragment: str) -> str:
    """Find an obligation through its contract label, never a local id list."""
    return next(
        obligation
        for obligation, label in contract.labels.items()
        if label_fragment in label
    )


def _primary_label(contract, obligation: str) -> str:
    """Return the first literal label declared by one contract table row."""
    return lint_guidebook_steps._label_variants(contract.labels[obligation])[0]


def _complete_step(tmp_path: Path) -> tuple[Path, object]:
    """Build one valid step and its local concept/outline sources."""
    contract = lint_guidebook_steps.parse_contract(CONTRACT)
    guidebook = tmp_path / "guidebook"
    guidebook.mkdir()
    (guidebook / "concept.md").write_text("# Concept\n", encoding="utf-8")
    (guidebook / "outline-source.md").write_text(
        "# Overview\n\n## Decision\n", encoding="utf-8"
    )
    position = _obligation_with(contract, "Step N of M")
    prerequisite = _obligation_with(contract, "You need:")
    concepts = _obligation_with(contract, "Concepts:")
    next_step = _obligation_with(contract, "Next:")
    utterance = _obligation_with(contract, "You type:")
    response = _obligation_with(contract, "Agent returns:")
    variability = _obligation_with(contract, "Output varies")
    decision = _obligation_with(contract, "You decide:")
    judgement = _obligation_with(contract, "Check (<kind>)")
    failure = _obligation_with(contract, "If it fails:")
    location = _obligation_with(contract, "You now hold:")
    outline = _obligation_with(contract, "Expect these headings:")
    lines = [
        "---", "order: 1", "---", "",
        "**Step 1 of 1 — Fixture**",
        _primary_label(contract, prerequisite),
        "*Skipping costs:* a missing prerequisite makes the result unreliable.",
        _primary_label(contract, concepts),
        "- Fixture concept: [explanation](concept.md)",
        _primary_label(contract, next_step) + " [Continue](concept.md)",
        "", "#### Run `fixture-skill`", "",
        _primary_label(contract, utterance), "Use the fixture skill.",
        _primary_label(contract, response), "> The fixture result.",
        _primary_label(contract, variability) + " with your inputs.",
        _primary_label(contract, decision), "Choose whether to continue.",
        f"**Check ({contract.judgement_kinds[0]}):** The result fits this fixture.",
        _primary_label(contract, failure), "Fix locally, then retry the failing case.",
        _primary_label(contract, location) + " `artifacts/fixture.md`",
        _primary_label(contract, outline),
        "*Source:* `outline-source.md`", "- Overview", "- Decision", "",
    ]
    step = guidebook / "step.md"
    step.write_text("\n".join(lines), encoding="utf-8")
    return step, contract


def _remove_label(step: Path, contract, obligation: str) -> None:
    """Mutation: remove precisely the selected obligation's opening label."""
    lines = step.read_text(encoding="utf-8").splitlines()
    index = lint_guidebook_steps._line_with_label(lines, contract.labels[obligation])
    assert index is not None, f"fixture does not declare {obligation}"
    del lines[index]
    step.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_ac0002_missing_obligation_reports_step_and_identifier(tmp_path: Path) -> None:
    step, contract = _complete_step(tmp_path)
    obligation = _obligation_with(contract, "You need:")
    _remove_label(step, contract, obligation)
    findings = lint_guidebook_steps.lint([step.parent], contract)
    finding = next(finding for finding in findings if finding.obligation == obligation)
    assert finding.step == step.stem
    assert obligation in finding.render()
    assert step.stem in finding.render()


@pytest.mark.parametrize("obligation", obligation_ids())
def test_ac0003_each_contract_obligation_detects_its_omission(
    tmp_path: Path, obligation: str
) -> None:
    """Mutation proof: each contract id gets its own removed-label fixture."""
    seed, contract = _complete_step(tmp_path)
    assert set(lint_guidebook_steps.registered_checks(contract)) == set(contract.obligations)
    _remove_label(seed, contract, obligation)
    findings = lint_guidebook_steps.lint([seed.parent], contract)
    assert obligation in {finding.obligation for finding in findings}


def test_ac0003_artifact_outline_detects_divergence_from_its_source(tmp_path: Path) -> None:
    """Mutation proof: retain the label but make its stated outline diverge."""
    step, contract = _complete_step(tmp_path)
    obligation = _obligation_with(contract, "Expect these headings:")
    step.write_text(
        step.read_text(encoding="utf-8").replace("- Decision", "- Different heading"),
        encoding="utf-8",
    )
    findings = lint_guidebook_steps.lint([step.parent], contract)
    assert obligation in {finding.obligation for finding in findings}


def test_ac0014_judgement_kind_is_required_and_closed(tmp_path: Path) -> None:
    step, contract = _complete_step(tmp_path)
    obligation = _obligation_with(contract, "Check (<kind>)")
    text = step.read_text(encoding="utf-8")
    text = re.sub(r"\*\*Check \([^)]+\):\*\*", "**Check:**", text)
    step.write_text(text, encoding="utf-8")
    findings = lint_guidebook_steps.lint([step.parent], contract)
    assert any(
        finding.obligation == obligation and "declares no judgement kind" in finding.detail
        for finding in findings
    )
    step.write_text(
        re.sub(r"\*\*Check:\*\*", f"**Check ({contract.obligations[0]}):**", text),
        encoding="utf-8",
    )
    findings = lint_guidebook_steps.lint([step.parent], contract)
    assert any(
        finding.obligation == obligation and contract.obligations[0] in finding.detail
        for finding in findings
    )


def test_ac0022_unresolved_named_concept_fails(tmp_path: Path) -> None:
    step, contract = _complete_step(tmp_path)
    obligation = _obligation_with(contract, "Concepts:")
    step.write_text(
        step.read_text(encoding="utf-8").replace("concept.md", "missing-concept.md"),
        encoding="utf-8",
    )
    assert obligation in {f.obligation for f in lint_guidebook_steps.lint([step.parent], contract)}


def test_help_docstring_names_contract_labels_flags_and_exit_codes() -> None:
    """The executable's help source stays an adopter-facing complete contract."""
    contract = lint_guidebook_steps.parse_contract(CONTRACT)
    help_text = lint_guidebook_steps.__doc__ or ""
    for obligation in contract.obligations:
        assert _primary_label(contract, obligation) in help_text
    assert "--contract" in help_text
    assert "Exit 0" in help_text
    assert "Exit 1" in help_text
    assert "Exit 2" in help_text


# --------------------------------------------------------------------------
# AC-0003 — an obligation the contract names but does not implement fails, and
# the failure names it.
#
# The lint derives each obligation's label-presence check from the contract's
# label table, so "registered but no-op" cannot arise for a label-presence
# obligation: no label, no check, and `parse_contract` refuses. This case pins
# that the refusal names the obligation, because the alternative — every other
# case failing for an unstated reason — is a wall of red a maintainer has to
# diagnose.
#
# Residual, stated rather than claimed closed: an obligation whose enforcement
# needs semantics *beyond* label presence — as `artifact_outline`,
# `judgement_check` and `concept_resolved` all do — would receive only the
# generic label check if it were added without bespoke logic. Nothing here
# detects that, and it is recorded in the verification ledger.
# --------------------------------------------------------------------------

def test_ac0003_an_obligation_with_no_label_form_is_refused_by_name(
    tmp_path: Path,
) -> None:
    original = CONTRACT.read_text(encoding="utf-8")
    invented = "invented_obligation"
    mutated = original.replace(
        "| `concept_resolved` |",
        f"| `{invented}` | An obligation with no label form | step |\n"
        "| `concept_resolved` |",
        1,
    )
    assert mutated != original, "mutation did not apply"
    contract = tmp_path / "AGENTS.md"
    contract.write_text(mutated, encoding="utf-8")

    try:
        lint_guidebook_steps.parse_contract(contract)
    except ValueError as error:
        assert invented in str(error), (
            f"the refusal does not name the unimplemented obligation: {error}"
        )
    else:
        raise AssertionError(
            "an obligation with no label form was accepted; a future obligation "
            "could then ship with no enforcement behind it"
        )


def test_no_prohibited_term_is_silently_dropped_by_line_wrapping() -> None:
    """Every backticked span in the vocabulary section must reach the parser.

    Two terms were unenforced for exactly this reason: written in prose, they
    wrapped across a newline, so the backtick span was not one token and the
    parser skipped them without complaint. The section is a list now, which
    makes wrapping structurally impossible per item — this case is what stops
    a future edit from returning it to prose and losing a term again.
    """
    section = _contract_section()
    body = section.split(VOCABULARY_HEADING, 1)[1].split("\n### ", 1)[0]
    spans = re.findall(r"`([^`]+)`", body)
    parsed = set(prohibited_terms())
    dropped = [s for s in spans if s not in parsed]
    assert not dropped, (
        f"backticked span(s) in the vocabulary section never reach the parser, "
        f"so the term is not enforced: {dropped}"
    )
