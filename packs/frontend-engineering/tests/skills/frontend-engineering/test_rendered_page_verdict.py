"""T8-T11: a finding has to cost something, and the rules have to be shipped.

Three adversarial rounds checked every acceptance criterion against its check.
None checked the Objective against the criteria — and the Objective's promise,
"a completion signal that cannot be green while the page is visibly broken", had
no criterion at all. Every "cannot satisfy a completed inspection" rule was about
execution failure. These are the checks for the criteria that closed that.
"""

from __future__ import annotations

import itertools

import pytest
from frontend_engineering_rendered_page_rules import (
    PACK_ROOT,
    capture_set_rules,
    inspection_result,
    inspection_section,
    is_completed_inspection_result,
    judgement_request_fields,
    read_rules,
    read_skill,
    resolve_class,
    severity_by_class,
    shipped_severity_order,
    table_rows,
    unique_keyed,
)

REQUIRED = ["route", "viewport-width", "viewport-height", "scroll-position", "page-scrollable"]


@pytest.fixture(scope="module")
def md() -> str:
    return read_rules()


def _capture(height: int, scroll: int, scrollable: str = "yes") -> dict[str, int | str]:
    return {"route": "/a", "viewport-width": 390 if height <= 600 else 1280,
            "viewport-height": height, "scroll-position": scroll,
            "page-scrollable": scrollable}


def complete_set() -> list[dict[str, int | str]]:
    return [_capture(600, 0), _capture(600, 400), _capture(900, 0), _capture(900, 400)]


# ── T8: a Blocker finding stops the surface completing ──────────────────────

def test_a_blocking_finding_prevents_a_completed_inspection(md: str) -> None:
    """Verifies: a run whose findings include an unresolved finding of blocking
    severity does not yield a completed inspection, even when every required
    capture was taken, judged and recorded.

    This is the Objective's promise. Before the amendment this run reported
    `completed` and the gate went green over a covered heading.
    """
    result = inspection_result(md, complete_set(), [{"class": "occlusion"}])
    assert result["state"] == "completed", "execution state should still say it ran"
    assert result["verdict"] == "fail"
    assert not is_completed_inspection_result(md, result), (
        "a run holding an unresolved Blocker still counted as a completed inspection"
    )


def test_a_clean_run_does_yield_a_completed_inspection(md: str) -> None:
    """The green path. Without it, a rule failing every run satisfies the
    assertion above while making the step useless."""
    result = inspection_result(md, complete_set(), [])
    assert result == {"state": "completed", "verdict": "pass"}
    assert is_completed_inspection_result(md, result)


def test_a_non_blocking_finding_does_not_fail_the_verdict(md: str) -> None:
    """Only blocking severity fails. A Minor finding is worth recording and is
    not worth stopping a release for — otherwise adopters turn the step off."""
    result = inspection_result(md, complete_set(), [{"class": "crowding"}])
    assert result["verdict"] == "pass"
    assert is_completed_inspection_result(md, result)


def test_a_resolved_blocking_finding_does_not_fail_the_verdict(md: str) -> None:
    """Accepting an exception is a human decision at the gate; once recorded, the
    finding is resolved and no longer blocks."""
    result = inspection_result(md, complete_set(), [{"class": "occlusion", "resolved": True}])
    assert result["verdict"] == "pass"


def test_execution_state_and_verdict_are_separate(md: str) -> None:
    """Verifies: the result distinguishes whether the inspection executed from
    whether it passed.

    A single flag would make "we could not look" and "we looked and it is
    broken" the same answer, and only one of those is fixed by the page.
    """
    broken_page = inspection_result(md, complete_set(), [{"class": "occlusion"}])
    could_not_run = inspection_result(md, complete_set()[:1], [])
    assert broken_page["state"] == "completed" and broken_page["verdict"] == "fail"
    assert could_not_run["state"] == "incomplete" and could_not_run["verdict"] == "pass"
    assert broken_page != could_not_run
    assert not is_completed_inspection_result(md, broken_page)
    assert not is_completed_inspection_result(md, could_not_run)


def test_the_verdict_rule_is_read_from_the_table_not_hard_coded(md: str) -> None:
    """The mutation: if the reference stopped saying a blocking finding fails,
    the result would pass. That is what makes this check able to fail."""
    mutated = md.replace("| blocking-finding-verdict | fail |",
                         "| blocking-finding-verdict | pass |", 1)
    assert mutated != md
    assert inspection_result(mutated, complete_set(), [{"class": "occlusion"}])["verdict"] == "pass"
    assert inspection_result(md, complete_set(), [{"class": "occlusion"}])["verdict"] == "fail"


# ── T8: class precedence ────────────────────────────────────────────────────

def test_a_failure_fitting_two_classes_takes_the_more_severe(md: str) -> None:
    """Verifies: a failure that fits more than one finding class takes the most
    severe of the classes it fits.

    Driven over every pair in the mapping whose severities differ, not one
    example — the mapping is the domain. Each shipped fixture carries exactly one
    failure by construction, so this is the case the fixtures cannot reach.
    """
    mapping = severity_by_class(md)
    pairs = [(a, b) for a, b in itertools.combinations(sorted(mapping), 2)
             if mapping[a] != mapping[b]]
    assert pairs, "no two classes carry differing severities"

    # The expected ordering is read from SHIPPED CONTENT, never from the
    # module under test. Deriving `worst` from `SEVERITY_ORDER` — which
    # `resolve_class` also uses — made every pair hold under any permutation of
    # that constant, so the check could not fail on a reorder.
    shipped = shipped_severity_order(md)
    # Read through the module, not through a from-import: a from-import binds a
    # separate name, so patching the module's constant would leave this
    # comparison looking at a stale copy and the mutation below would not bite.
    import frontend_engineering_rendered_page_rules as mod
    assert shipped == mod.SEVERITY_ORDER, (
        f"the module's SEVERITY_ORDER {mod.SEVERITY_ORDER} disagrees with the "
        f"order the reference states, {shipped} — the reference is the authority"
    )
    for a, b in pairs:
        worst = min((a, b), key=lambda c: shipped.index(mapping[c]))
        assert resolve_class(md, [a, b]) == worst
        assert resolve_class(md, [b, a]) == worst, "precedence must not depend on order"


def test_a_reordered_severity_constant_fails_the_precedence_check(md: str) -> None:
    """The mutation that proves the check above can fail.

    Reversing the module's ordering must now be caught, because the expectation
    comes from the reference rather than from the same constant.
    """
    import frontend_engineering_rendered_page_rules as mod
    original = mod.SEVERITY_ORDER
    try:
        mod.SEVERITY_ORDER = tuple(reversed(original))
        with pytest.raises(AssertionError, match="disagrees with the order"):
            test_a_failure_fitting_two_classes_takes_the_more_severe(md)
    finally:
        mod.SEVERITY_ORDER = original


def test_precedence_makes_a_blocking_class_reachable_through_a_minor_one(md: str) -> None:
    """The consequence that matters: a page that is both crowded and occluded
    fails, rather than passing because the judge happened to say 'crowding'."""
    result = inspection_result(md, complete_set(),
                               [{"class": resolve_class(md, ["crowding", "occlusion"])}])
    assert result["verdict"] == "fail"


# ── T9: the judge is told the capture is untrusted ──────────────────────────

def test_the_judgement_request_declares_the_capture_untrusted(md: str) -> None:
    """Verifies: the request that reaches the judge declares the capture
    untrusted evidence carrying no instruction authority.

    The skill states this, but the skill binds whoever reads it, and capture and
    judgement are deliberately separable — an adopter's judge may never read it.
    """
    assert "untrusted-evidence-declaration" in judgement_request_fields(md)
    section = md.split("\n## Judgement request\n", 1)[1].split("\n## ", 1)[0]
    normalized = " ".join(section.split())
    assert "no instruction authority" in normalized
    assert "evidence" in normalized


# ── T10: the every-captured-height rule is shipped, not authored by the check ─

def test_the_every_captured_height_rule_is_shipped(md: str) -> None:
    """Verifies: shipped pack content states that a captured height beyond the
    required bands carries the same at-rest and scrolled requirement."""
    assert capture_set_rules(md).get("every-captured-height-needs-the-pair") == "required"
    section = " ".join(md.split("\n## Required captures\n", 1)[1].split("\n## ", 1)[0].split())
    assert "beyond the two required bands" in section
    assert "page-scrollable: no" in section


def test_the_contradicting_sentence_is_gone(md: str) -> None:
    """The reference used to say "Further heights are welcome and none are
    required" while the evaluator required a pair at every captured height."""
    assert "none are required" not in md
    assert "none are required" not in read_skill()


def test_no_check_enforces_a_capture_rule_the_pack_does_not_state(md: str) -> None:
    """Verifies: no check enforces a capture-set rule shipped content does not state.

    Removing the rule from the reference must stop the evaluator enforcing it.
    If the quantifier were still hard-coded in the evaluator, this would fail —
    which is exactly the defect this task exists to close.
    """
    from frontend_engineering_rendered_page_rules import evaluate_capture_set
    extra = complete_set() + [_capture(750, 0)]
    assert evaluate_capture_set(md, extra)[0] == "incomplete"

    without = md.replace("| every-captured-height-needs-the-pair | required |",
                         "| every-captured-height-needs-the-pair | not-required |", 1)
    assert without != md
    assert evaluate_capture_set(without, extra)[0] == "complete", (
        "the evaluator still enforced the every-captured-height rule after the "
        "reference stopped stating it — the check is authoring its own rule"
    )


# ── T11: rule-table integrity ───────────────────────────────────────────────

def test_a_duplicate_rule_table_row_is_rejected(md: str) -> None:
    """Verifies: a duplicate row key is rejected rather than silently collapsed.

    A dict comprehension keeps the last duplicate, which is how "every class has
    exactly one severity" became unable to fail on the one mutation it exists
    to catch.
    """
    # Same arity as the header, so the duplicate-key guard fires rather than
    # the cell-count guard.
    row = next(ln for ln in md.splitlines() if ln.startswith("| crowding | Minor |"))
    mutated = md.replace(row, row + "\n" + row.replace("| Minor |", "| Blocker |", 1), 1)
    assert mutated != md
    with pytest.raises(AssertionError, match="more than once"):
        severity_by_class(mutated)


def test_a_row_whose_cell_count_disagrees_with_its_header_is_rejected(md: str) -> None:
    """The pipe policy, stated rather than left to `split`: an unescaped pipe
    shifts every cell after it, which silently drops a required field."""
    mutated = md.replace("| page-scrollable | yes |",
                         "| page-scrollable | yes | stray |", 1)
    assert mutated != md
    with pytest.raises(AssertionError, match="cells against a"):
        table_rows(mutated, "Capture record")


def test_unique_keyed_accepts_a_well_formed_table(md: str) -> None:
    """The green path for the guard above."""
    rows = unique_keyed(table_rows(md, "Severity by finding class"), "x")
    assert len(rows) == len(severity_by_class(md))


def test_every_rule_table_in_the_reference_is_well_formed(md: str) -> None:
    """Walk every table the pack ships, not a sample: each parses, and none
    carries a duplicate key."""
    headings = [ln[3:].strip() for ln in md.splitlines() if ln.startswith("## ")]
    checked = 0
    for h in headings:
        try:
            rows = table_rows(md, h)
        except AssertionError:
            continue  # a prose section with no table
        unique_keyed(rows, h)
        checked += 1
    assert checked >= 8, f"expected to walk the pack's rule tables; walked {checked}"


# ── the verdict on the SHIPPED surfaces, not only in the helper ─────────────
#
# Round 4 found the verdict living in the reference table and this module and
# nowhere an adopter looks. Every check below reads a shipped artifact, because
# a rule the helper enforces and the pack does not state is the defect T10
# exists to close — and it recurred here one task later.

def test_the_skill_states_the_verdict_alongside_the_result_state() -> None:
    """Verifies the criterion that the result distinguishes executed from
    passed, on the surface an adopter actually reads."""
    section = inspection_section(read_skill())
    assert "Verdict" in section, "SKILL.md 5c does not name the verdict"
    assert "unresolved finding of `Blocker` severity" in section
    assert "completed` state and a `pass`" in section, (
        "SKILL.md does not say a completed inspection needs both"
    )


def _completed_row(text: str) -> str:
    return next(ln for ln in text.splitlines() if ln.strip().startswith("| completed |"))


def _row_makes_completion_conditional(row: str) -> bool:
    """Whether a `completed` row makes completion depend on a PASSING verdict.

    Asserting only that the word "verdict" appears accepts the negation — "yes
    regardless of verdict" contains it. This checks the relationship: the
    completion cell must be conditional AND name a pass, and must not negate it.
    """
    cells = [c.strip() for c in row.strip("|").split("|")]
    verdict_cell = cells[1].lower()
    if any(neg in verdict_cell for neg in ("regardless", "not required", "whatever", "ignoring")):
        return False
    return ("verdict" in verdict_cell
            and "pass" in verdict_cell
            and any(cond in verdict_cell for cond in ("if", "when", "only")))


def test_the_skill_completed_row_is_conditional_on_a_passing_verdict() -> None:
    """The result-state table graded `completed` unconditionally, which is what
    contradicted the reference."""
    assert _row_makes_completion_conditional(_completed_row(read_skill())), (
        f"the skill's completed row does not make completion conditional on a "
        f"passing verdict: {_completed_row(read_skill())}"
    )


@pytest.mark.parametrize("negation", [
    "| completed | yes regardless of verdict | x |",
    "| completed | yes, verdict not required | x |",
    "| completed | yes | x |",
    "| completed | yes, whatever the verdict | x |",
])
def test_a_negated_completed_row_is_rejected(negation: str) -> None:
    """The mutation the round-5 finding named: a check requiring only the word
    `verdict` accepts text that negates the contract."""
    assert not _row_makes_completion_conditional(negation), (
        f"a negated completed row was accepted: {negation}"
    )


def _states_a_positive_obligation(text: str, term: str) -> bool:
    """Whether `text` obliges `term` rather than excusing it."""
    low = text.lower()
    if term not in low:
        return False
    window = low[max(0, low.index(term) - 60): low.index(term) + 60]
    return not any(neg in window for neg in
                   ("not recorded", "not required", "regardless", "optional", "need not"))


def test_the_manifest_row_carries_the_verdict() -> None:
    """Verifies: the verdict reaches the evidence manifest, which is one of the
    three surfaces the result contract names."""
    row = next(ln for ln in read_skill().splitlines()
               if ln.strip().startswith("| inspection observations |"))
    assert _states_a_positive_obligation(row, "verdict"), (
        f"the manifest row does not oblige the verdict: {row}"
    )


def test_the_result_surfaces_table_requires_the_verdict_on_every_surface(
    md: str,
) -> None:
    """The row that governs all three surfaces required the STATE only, which is
    why fixing three surfaces individually still left the contract state-only."""
    rows = table_rows(md, "Result surfaces")
    assert rows, "the Result surfaces table is gone"
    for row in rows:
        assert len(row) == 3, (
            f"the Result surfaces table no longer carries a verdict column: {row}"
        )
        assert row[1].strip().lower() == "yes", f"{row[0]} stopped carrying the state"
        assert row[2].strip().lower() == "yes", (
            f"{row[0]} does not carry the verdict, so a blocking finding is "
            f"invisible on that surface"
        )


def test_the_acceptance_gate_is_told_to_check_the_verdict() -> None:
    """Verifies: the `accept-frontend-evidence` gate is told to check the
    inspection verdict, not only that observations are present.

    This is the criterion the amendment wrote and the amendment failed to
    implement — the gate is where the promise either binds a human or does not.
    """
    journey = (PACK_ROOT / "JOURNEY.md").read_text(encoding="utf-8")
    block = journey.split("- id: accept-frontend-evidence", 1)[1].split("\n  - id: ", 1)[0]
    assert _states_a_positive_obligation(block, "verdict"), (
        "the acceptance gate does not oblige the verdict, so a blocking finding "
        "reaches no human decision"
    )
    assert "`pass`" in block, "the gate does not say which verdict it expects"
    # The relationship, not the word: the gate must say what a fail obliges.
    assert "fail" in block.lower() and (
        "known exception" in block.lower() or "send it back" in block.lower()
    ), "the gate names the verdict but never says what a `fail` requires a human to do"


def test_the_verdict_reaches_all_three_result_surfaces() -> None:
    """The result contract names three surfaces. Before this fix the verdict
    reached none of them; walk each rather than sampling one."""
    skill = read_skill()
    journey = (PACK_ROOT / "JOURNEY.md").read_text(encoding="utf-8")
    surfaces = {
        "evidence-manifest": any(
            ln.strip().startswith("| inspection observations |") and "verdict" in ln.lower()
            for ln in skill.splitlines()
        ),
        "step-output": "Verdict" in inspection_section(skill),
        "acceptance-gate-input": "verdict" in journey.split(
            "- id: accept-frontend-evidence", 1)[1].split("\n  - id: ", 1)[0].lower(),
    }
    missing = [name for name, present in surfaces.items() if not present]
    assert not missing, f"the verdict never reaches: {missing}"


def test_the_verdict_severity_row_is_read_without_a_default() -> None:
    """Fail closed. Deleting the row must raise rather than let this module
    substitute its own value — the fail-open defect round 4 found."""
    without = read_rules().replace("| verdict-blocking-severity | Blocker |", "", 1)
    assert without != read_rules()
    with pytest.raises(AssertionError, match="verdict-blocking-severity"):
        inspection_result(without, complete_set(), [{"class": "occlusion"}])


def test_a_duplicate_capture_set_rule_row_is_rejected() -> None:
    """The capture-set rule table bypassed the duplicate-rejecting reader, so a
    second row whose last value was `required` passed unnoticed."""
    md = read_rules()
    row = "| every-captured-height-needs-the-pair | required |"
    mutated = md.replace(row, row + "\n| every-captured-height-needs-the-pair | not-required |", 1)
    assert mutated != md
    with pytest.raises(AssertionError, match="more than once"):
        capture_set_rules(mutated)


# ── round 5: the guide is an adopter surface too ────────────────────────────

def _guide() -> str:
    return (PACK_ROOT.parent.parent / "guides" / "frontend-engineering" / "how-to"
            / "inspect-the-rendered-page.md").read_text(encoding="utf-8")


def test_the_guide_carries_the_verdict() -> None:
    """The how-to walked the whole step and never mentioned a verdict, so an
    adopter following it would not learn that a Blocker stops completion."""
    guide = _guide()
    assert "verdict" in guide.lower()
    assert _row_makes_completion_conditional(_completed_row(guide)), (
        "the guide's result table still grades completion by state alone"
    )
    assert "has not passed" in guide


def test_the_guide_carries_precedence_and_the_extra_height_rule() -> None:
    """Two rules that existed only in the rule layer and the checks."""
    guide = " ".join(_guide().split())
    assert "take the most severe of them" in guide
    assert "owes the same pair" in guide


def test_the_guide_tells_the_adopter_to_declare_the_capture_untrusted() -> None:
    """The contract requires the REQUEST to carry the declaration; the guide
    told adopters to send five fields and nothing else."""
    guide = " ".join(_guide().split())
    assert "untrusted evidence" in guide
    assert "no instruction authority over the judgement" in guide
