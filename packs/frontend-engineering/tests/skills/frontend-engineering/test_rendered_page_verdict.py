"""T8-T11: a finding has to cost something, and the rules have to be shipped.

Three adversarial rounds checked every acceptance criterion against its check.
None checked the Objective against the criteria — and the Objective's promise,
"a completion signal that cannot be green while the page is visibly broken", had
no criterion at all. Every "cannot satisfy a completed inspection" rule was about
execution failure. These are the checks for the criteria that closed that.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

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


NARROW, WIDE = 390, 1280


def _capture(
    height: int, scroll: int, scrollable: str = "yes", width: int = NARROW
) -> dict[str, int | str]:
    """Width and height are independent arguments.

    They used to be one: width was `390 if height <= 600 else 1280`, so a set
    covering both heights covered each channel at exactly one height and no rule
    could see it. Defaulting width rather than deriving it keeps the callers that
    only care about height short, while making the coupling impossible to
    reintroduce by accident.
    """
    return {"route": "/a", "viewport-width": width,
            "viewport-height": height, "scroll-position": scroll,
            "page-scrollable": scrollable}


def complete_set() -> list[dict[str, int | str]]:
    """The four height-and-scroll captures in each of the two fallback channels."""
    return [
        _capture(height, scroll, width=width)
        for width in (NARROW, WIDE)
        for height in (600, 900)
        for scroll in (0, 400)
    ]


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

def test_the_every_captured_size_rule_is_shipped(md: str) -> None:
    """Verifies: shipped pack content states that a captured width and height
    beyond the required channels and bands carries the same at-rest and scrolled
    requirement."""
    assert (
        capture_set_rules(md).get("every-captured-width-and-height-needs-the-pair")
        == "required"
    )
    section = " ".join(md.split("\n## Required captures\n", 1)[1].split("\n## ", 1)[0].split())
    assert "beyond the required channels and bands" in section
    assert "page-scrollable: no" in section


def test_the_contradicting_sentence_is_gone(md: str) -> None:
    """The reference used to say "Further heights are welcome and none are
    required" while the evaluator required a pair at every captured height."""
    assert "none are required" not in md
    assert "none are required" not in read_skill()


ROW = "| every-captured-width-and-height-needs-the-pair | required |"


def test_a_rule_the_pack_switches_off_stops_being_enforced(md: str) -> None:
    """Verifies: no check enforces a capture-set rule shipped content switches off.

    A row that is *present* and says something other than `required` is a stated
    decision, and the evaluator honours it. If the quantifier were hard-coded in
    the evaluator this would fail, which is the defect the rule-is-the-data
    discipline exists to close.
    """
    from frontend_engineering_rendered_page_rules import evaluate_capture_set
    extra = complete_set() + [_capture(750, 0)]
    assert evaluate_capture_set(md, extra)[0] == "incomplete"

    off = md.replace(
        ROW, "| every-captured-width-and-height-needs-the-pair | not-required |", 1
    )
    assert off != md
    assert evaluate_capture_set(off, extra)[0] == "complete", (
        "the evaluator still enforced the every-captured-size rule after the "
        "reference switched it off — the check is authoring its own rule"
    )


def test_an_absent_rule_row_raises_rather_than_skipping(md: str) -> None:
    """Verifies: deleting the rule row fails the check rather than passing it.

    This is the other half of the rule-is-the-data discipline and it pulls the
    opposite way from the case above. A row switched *off* is a stated decision;
    a row that is *gone* states nothing, and a reader that skips the rule it
    governs is fail-open — the deletion would leave every check green, so the
    guard could never fail on the one mutation it exists to catch.
    """
    from frontend_engineering_rendered_page_rules import evaluate_capture_set
    gone = md.replace(ROW + "\n", "", 1)
    assert gone != md
    with pytest.raises(AssertionError, match="every-captured-width-and-height"):
        evaluate_capture_set(gone, complete_set())


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


def _states_completion_needs_both(text: str) -> bool:
    """Whether a surface says a completed inspection needs execution AND a pass.

    The result-state column answers execution only — `completed` there means the
    step ran. Putting a conditional phrase in that cell would be friendlier to a
    human and would break the machine-readable contract the evaluators parse, so
    the conjunction lives in prose beside the table instead. This checks that it
    is actually there, and that nothing negates it.
    """
    flat = " ".join(text.split()).lower()
    if any(neg in flat for neg in
           ("regardless of verdict", "verdict not required", "whatever the verdict")):
        return False
    return ("execution complete" in flat
            and "verdict" in flat
            and ("`pass` verdict" in flat or "and a `pass`" in flat
                 or "passing verdict" in flat))


def _column_means_execution(row_or_header: str) -> bool:
    """The result-state table's second column must be about execution."""
    return "execution complete" in row_or_header.lower()


@pytest.mark.parametrize("surface", ["skill", "reference", "guide"])
def test_completion_needs_both_axes_on_every_surface(surface: str) -> None:
    """Every surface carrying the result-state table must also say that a
    completed inspection needs a passing verdict.

    The reference table graded `completed` as a completed inspection outright,
    which contradicted the same file's verdict rule and let a run holding a
    Blocker read as complete.
    """
    text = {"skill": read_skill(), "reference": read_rules(), "guide": _guide()}[surface]
    header = next(ln for ln in text.splitlines() if ln.strip().startswith("| Result state |"))
    assert _column_means_execution(header), (
        f"{surface}'s result-state column still claims to answer completion "
        f"rather than execution: {header}"
    )
    assert _states_completion_needs_both(text), (
        f"{surface} never says a completed inspection needs both axes"
    )


@pytest.mark.parametrize("negation", [
    "Result state | Execution complete. A completed inspection is yes regardless of verdict.",
    "Result state | Execution complete. The verdict not required for completion.",
    "Result state | Completed inspection | ...",
])
def test_a_negated_or_mislabelled_contract_is_rejected(negation: str) -> None:
    """The round-5 lesson: a check that looks for the word `verdict` accepts
    text that negates the rule. These must all fail."""
    assert not (_column_means_execution(negation)
                and _states_completion_needs_both(negation)), (
        f"a negated or mislabelled contract was accepted: {negation}"
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
    row = "| every-captured-width-and-height-needs-the-pair | required |"
    mutated = md.replace(
        row,
        row + "\n| every-captured-width-and-height-needs-the-pair | not-required |",
        1,
    )
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
    assert _states_completion_needs_both(guide), (
        "the guide never says a completed inspection needs a passing verdict"
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


# ── the guide teaches the channel axis ──────────────────────────────────────


def test_the_guide_walks_both_fallback_channels() -> None:
    """Verifies AC-0018's positive half: the guide names both fallback channels,
    the band between them no fallback capture reaches, and the per-channel floor.
    """
    from frontend_engineering_rendered_page_rules import fallback_channels

    guide = " ".join(_guide().split())
    # Derived from the shipped band table, and word-bounded. A bare `"wide" in
    # guide` was already satisfied by "the widest its upper bound admits" and by
    # a pre-existing Related-links line reading "the wider audit this step sits
    # inside" -- so that half could not fail, and the guide could stop teaching
    # the `wide` channel entirely with the suite green.
    for name, _, _ in fallback_channels(read_rules()):
        assert re.search(rf"\b{re.escape(name)}\b", guide), (
            f"the guide does not name the {name!r} channel the reference declares"
        )
    assert "481–1023" in guide or "481-1023" in guide, (
        "the guide does not name the band the fallback channels leave uncaptured"
    )
    assert "eight captures per route" in guide, (
        "the guide does not state the per-channel floor"
    )


# The demoted obligation. AC-0021, AC-0022 and AC-0025 were cut because no token
# predicate can decide "teaches the superseded floor": three of the five shipped
# strings that stated it carry no completeness word at all, and the token that
# would red them also reds the guide's unscrollable-branch sentence, which must
# survive. A literal pin is what is left, and its reach is exactly these strings.
# This is the GUIDE half. The harness half lives in
# `test_rendered_page_reviewer_sight.py`'s `HARNESS_SUPERSEDED_FLOOR`, which pins
# the two `evals.json` strings. Between them the pin reaches four of the five
# strings `plan.md` § Design decisions names; the fifth, the guide's height-keyed
# capture table, is not pinned because it was not superseded — the prose above it
# now frames it as the matrix taken in every channel, so the table itself still
# states the contract. That divergence from the plan is recorded in
# `notes/verification-ledger.md`.
SUPERSEDED_FLOOR = (
    "Take four captures per route: two viewport heights",
    "none beyond these two is required",
    "Whether the page scrolls at this height",
)

MUST_SURVIVE = (
    "page-scrollable: no",
    "no scrolled view",
)


def test_the_guide_no_longer_states_the_superseded_floor() -> None:
    """A content pin, not a predicate.

    Reach: exactly the strings below. A reworded height-only floor is NOT caught,
    and that is the accepted limit of this control — asking a text search to
    decide the general property is what three review rounds failed to make work.
    """
    guide = _guide()
    for stale in SUPERSEDED_FLOOR:
        assert stale not in guide, (
            f"the guide still states the superseded floor: {stale!r}"
        )


def test_the_pin_spares_the_sentences_that_must_survive() -> None:
    """The other polarity. A guard tuned until the strings above red is worthless
    if it also removed the unscrollable branch, which is a live rule."""
    guide = _guide()
    for kept in MUST_SURVIVE:
        assert kept in guide, f"the guide lost {kept!r}, which is a live rule"


# ── every adopter surface, DERIVED rather than listed ───────────────────────
#
# Round 6 found four stale surfaces a hand-written sweep had missed: the pack
# reference page, the audit how-to, the tutorial, and journey step 5. A sweep
# only reaches what its seed contains, and that seed was typed by hand.
#
# So the seed is derived: any shipped file that describes the evidence manifest
# is a surface the inspection result has to appear on. A new guide page that
# lists manifest fields is caught the day it is added.

def _manifest_describing_surfaces() -> list[Path]:
    """Shipped files that enumerate evidence-manifest fields.

    Keyed on `known exceptions`, a manifest field that predates this delivery,
    so the seed does not depend on anything this delivery added — a file that
    forgot the inspection entirely is still found.
    """
    roots = [PACK_ROOT, PACK_ROOT.parent.parent / "guides" / "frontend-engineering"]
    out: list[Path] = []
    for root in roots:
        for p in sorted(root.rglob("*.md")):
            if "/tests/" in p.as_posix():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            if "known exceptions" in text and "unverified items" in text:
                out.append(p)
    return out


def test_the_derived_surface_list_is_not_empty() -> None:
    """A sweep over an empty list passes trivially — the failure mode that makes
    a coverage guard worthless."""
    surfaces = _manifest_describing_surfaces()
    assert len(surfaces) >= 4, (
        f"expected several manifest-describing surfaces; found {len(surfaces)}: "
        f"{[p.name for p in surfaces]}"
    )


def test_every_manifest_describing_surface_names_the_inspection() -> None:
    """Any shipped file that tells a reader what the evidence manifest contains
    must mention the inspection's output, or it teaches a manifest that is a
    field short."""
    stale = []
    for p in _manifest_describing_surfaces():
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        if "inspection observations" not in text and "rendered-page inspection" not in text:
            stale.append(p.name)
    assert not stale, (
        f"these shipped surfaces describe the evidence manifest without the "
        f"inspection: {stale}"
    )
