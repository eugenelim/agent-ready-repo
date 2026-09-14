"""Contract tests for advisory finding-response metadata."""

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP = PACK_ROOT / ".apm/skills/work-loop/SKILL.md"
VERDICT = PACK_ROOT / ".apm/skills/work-loop/references/review-verdict-record.md"

AXES = ("### Cut", "### Route", "### Fix", "### Hold")

ANSWERS_BY_AXIS = {
    "### Cut": (
        "drop-the-claim",
        "cut-the-item",
        "demote-the-claim",
        "narrow-the-claim",
    ),
    "### Route": ("route-to-owner", "bound-out-of-scope"),
    "### Fix": ("repair-the-generator", "repair-the-artifact"),
    "### Hold": ("dismiss-and-re-present", "accept-as-proportionate"),
}

EXPECTED_DISPOSITION_ROWS = (
    "| `deferred` | `nit` (and `severity` `nit`) | present | `READY_WITH_RESIDUAL_RISK` |\n"
    "| `deferred` | `nit` | **missing** | `BLOCKED` — silent suppression |\n"
    "| `deferred` | `blocker` or `concern` | any | `BLOCKED` — a promoted finding cannot be deferred as a Nit |\n"
    "| `unresolved` | `blocker` | any | `BLOCKED` |\n"
    "| `unresolved` | `concern` | any | `CHANGES_REQUIRED` |\n"
    "| `unresolved` | `nit` | any | `CHANGES_REQUIRED` — decide it: defer it or act on it |\n"
    "| `resolved` or `rejected` | any | any | nothing |"
)


def _section(path: Path | str, heading: str | None = None) -> str:
    """Return exactly one Markdown section, refusing anything ambiguous."""
    if heading is None:
        heading = str(path)
        path = WORK_LOOP
    assert isinstance(path, Path)
    text = path.read_text(encoding="utf-8")
    level = len(heading) - len(heading.lstrip("#"))
    starts = [m.start() for m in re.finditer(rf"^{re.escape(heading)}\s*$", text, re.M)]
    assert len(starts) == 1, f"{path}: {heading!r} matched {len(starts)} heading lines"
    start = starts[0]
    nxt = re.search(rf"^#{{1,{level}}} ", text[start + len(heading) :], re.M)
    return text[start:] if nxt is None else text[start : start + len(heading) + nxt.start()]


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace."""
    return " ".join(text.split())


def _answer_bodies(section: str) -> dict[str, str]:
    """Return every answer bullet and its complete body from one axis."""
    matches = re.finditer(
        r"^- `(?P<answer>[^`]+)` — (?P<body>.*?)(?=^- `|\Z)",
        section,
        re.M | re.S,
    )
    answers = {match.group("answer"): _flat(match.group("body")) for match in matches}
    assert len(answers) == sum(1 for line in section.splitlines() if line.startswith("- `"))
    return answers


def _sentences(text: str) -> list[str]:
    """Return normalized prose sentences from a bounded Markdown region."""
    return [sentence for sentence in re.split(r"(?<=\.) (?=[A-Z])", _flat(text)) if sentence]


def _prose_outside_answer_bullets(section: str) -> str:
    """Return all prose in an axis except its named answer bullets."""
    prose: list[str] = []
    in_answer = False
    for line in section.splitlines()[1:]:
        if line.startswith("- `"):
            in_answer = True
        elif in_answer and line.startswith("  "):
            continue
        else:
            in_answer = False
            if line.strip():
                prose.append(line)
    return "\n".join(prose)


def _response_metadata() -> str:
    """Return the response metadata description from the verdict record."""
    return " ".join(_section(VERDICT, "### Response metadata").split())


def _decide() -> str:
    """Return the complete DECIDE section that owns response guidance."""
    return _section(WORK_LOOP, "## Step 5. DECIDE")


def test_findings_schema_marks_response_optional() -> None:
    """Keep response optional for records that predate this metadata."""
    shapes = _section(VERDICT, "## Nested shapes")
    assert "response?" in shapes


def test_findings_schema_marks_reason_optional() -> None:
    """Keep reason optional for records that predate this metadata."""
    shapes = _section(VERDICT, "## Nested shapes")
    assert "reason?" in shapes


def test_response_points_to_decide_for_its_admitted_values() -> None:
    """Keep the answer vocabulary in its one shipped home."""
    metadata = _response_metadata()
    assert "an answer stated in [DECIDE](../SKILL.md#step-5-decide)" in metadata


def test_unrecognised_response_is_ignored_with_a_note() -> None:
    """Keep an unknown advisory response from blocking a valid record."""
    metadata = _response_metadata()
    assert "Any unrecognised `response`, a `response` without a non-empty `reason`, and a `reason` without a `response` are each ignored with a note naming what was wrong, leaving the entry and the record valid." in metadata


def test_response_without_reason_is_ignored_with_a_note() -> None:
    """Keep a response without its required explanation advisory."""
    metadata = _response_metadata()
    assert "a `response` without a non-empty `reason`" in metadata


def test_reason_without_response_is_ignored_with_a_note() -> None:
    """Keep an orphaned explanation advisory."""
    metadata = _response_metadata()
    assert "a `reason` without a `response`" in metadata


def test_response_metadata_does_not_name_status() -> None:
    """Keep the field description independent of the existing state inputs."""
    metadata = _response_metadata()
    assert "status" not in metadata


def test_response_metadata_does_not_name_effective_severity() -> None:
    """Keep the field description independent of the existing state inputs."""
    metadata = _response_metadata()
    assert "effective_severity" not in metadata


def _state_deciding_sections() -> str:
    """Return the three named regions that determine the record's state."""
    return "\n".join(
        (
            _section(VERDICT, "## State precedence"),
            _section(VERDICT, "### Finding disposition"),
            _section(VERDICT, "## Residual eligibility"),
        )
    )


def test_response_does_not_enter_state_deciding_sections() -> None:
    """Protect only the three named state-deciding sections, not every possible future gate."""
    state_sections = _state_deciding_sections()
    assert "response" not in state_sections


def test_reason_does_not_enter_state_deciding_sections() -> None:
    """Protect only the three named state-deciding sections, not every possible future gate."""
    state_sections = _state_deciding_sections()
    assert "reason" not in state_sections


def test_finding_disposition_rows_are_unchanged() -> None:
    """Keep the existing disposition inputs and outcomes intact."""
    disposition = _section(VERDICT, "### Finding disposition")
    assert EXPECTED_DISPOSITION_ROWS in disposition


def test_decide_has_every_ladder_answer() -> None:
    """Keep every response token at its single shipped statement."""
    decide = _decide()
    for answers in ANSWERS_BY_AXIS.values():
        for answer in answers:
            assert f"`{answer}`" in decide


def test_cut_answers_are_under_cut() -> None:
    """Keep cut reductions grouped under their axis."""
    cut = _section(WORK_LOOP, "### Cut")
    assert all(f"`{answer}`" in cut for answer in ANSWERS_BY_AXIS["### Cut"])


def test_route_answers_are_under_route() -> None:
    """Keep ownership routes grouped under their axis."""
    route = _section(WORK_LOOP, "### Route")
    assert all(f"`{answer}`" in route for answer in ANSWERS_BY_AXIS["### Route"])


def test_fix_answers_are_under_fix() -> None:
    """Keep repairs grouped under their axis."""
    fix = _section(WORK_LOOP, "### Fix")
    assert all(f"`{answer}`" in fix for answer in ANSWERS_BY_AXIS["### Fix"])


def test_hold_answers_are_under_hold() -> None:
    """Keep recorded holds grouped under their axis."""
    hold = _section(WORK_LOOP, "### Hold")
    assert all(f"`{answer}`" in hold for answer in ANSWERS_BY_AXIS["### Hold"])


def test_decide_orders_the_axes_as_a_ladder() -> None:
    """Keep cut before route, fix, and hold."""
    decide = _decide()
    positions = [decide.index(axis) for axis in AXES]
    assert positions == sorted(positions)


def test_decide_stops_after_the_first_applicable_answer() -> None:
    """Keep the ordered set from becoming a menu of parallel answers."""
    decide = " ".join(_decide().split())
    assert "Take the first answer that applies, then stop; do not evaluate the rest." in decide


def test_drop_the_claim_removes_only_an_unobliged_assertion() -> None:
    """Distinguish a dropped assertion from a removed obligation."""
    cut = _section(WORK_LOOP, "### Cut")
    assert "the assertion is not obliged by anything" in cut
    assert "changes no stated outcome" in cut
    assert "It operates on an assertion, not a sentence or item," in cut
    assert "applies only to an assertion no surviving contract obligation depends on" in cut
    assert "When removing it reduces a surviving obligation's reach, that is `narrow-the-claim`." in " ".join(cut.split())


def test_cut_the_item_removes_the_obligation() -> None:
    """Keep cutting an item distinct from dropping one claim within it."""
    assert "`cut-the-item` — the obligation itself stops existing." in _section(WORK_LOOP, "### Cut")


def test_demote_the_claim_relocates_an_obligation_with_a_pin() -> None:
    """Keep demotion distinct from dropping the assertion altogether."""
    cut = " ".join(_section(WORK_LOOP, "### Cut").split())
    assert "the obligation survives but stops being contract" in cut
    assert "moving to working material with a content pin" in cut


def test_drop_and_demote_are_distinguished_by_what_survives() -> None:
    """Keep dropping an assertion distinct from relocating an obligation."""
    cut = " ".join(_section(WORK_LOOP, "### Cut").split())
    assert "the assertion is not obliged by anything" in cut
    assert "the obligation survives but stops being contract" in cut


def test_narrow_the_claim_keeps_the_obligation_in_contract() -> None:
    """Keep narrowing distinct from a change of ownership or contract tier."""
    cut = " ".join(_section(WORK_LOOP, "### Cut").split())
    assert "the obligation stays contract and in place" in cut
    assert "stated reach shrinks to what a check reaches" in cut


# STUB: test_claim_check_mismatch_covers_both_reachable_and_unreachable_checks — claim reach selects strengthen or narrow
def test_claim_check_mismatch_covers_both_reachable_and_unreachable_checks() -> None:
    answers = _answer_bodies(_section("### Cut"))
    exception_map = {
        "drop-the-claim": "removes an assertion without changing a surviving claim's reach",
        "cut-the-item": "removes the obligation instead of changing its reach",
        "demote-the-claim": "changes contract tier instead of a surviving claim's reach",
    }

    assert set(answers) == set(ANSWERS_BY_AXIS["### Cut"])
    assert set(answers) - set(exception_map) == {"narrow-the-claim"}
    claim_check_rule = answers["narrow-the-claim"]
    assert "some check can reach the claimed property" in claim_check_rule
    assert "strengthen the check" in claim_check_rule
    assert "no check can reach the claimed property" in claim_check_rule
    assert "stated reach shrinks to what a check reaches" in claim_check_rule


# STUB: test_fix_requires_a_check_of_the_property_not_a_consequence — a repair check asserts the property itself
def test_fix_requires_a_check_of_the_property_not_a_consequence() -> None:
    fix = _section("### Fix")
    answer_exceptions = {
        "repair-the-generator": "selects the repair target rather than the property asserted",
        "repair-the-artifact": "selects the repair target rather than the property asserted",
    }
    answers = _answer_bodies(fix)
    check_requirements = [
        sentence
        for sentence in _sentences(_prose_outside_answer_bullets(fix))
        if re.search(r"\bcheck\b", sentence)
    ]

    assert set(answers) == set(answer_exceptions)
    assert len(check_requirements) == 1
    assert "check asserts the repaired property itself" in check_requirements[0]
    assert "not only a consequence" in check_requirements[0]


def test_demotion_or_narrowing_uses_the_completion_gate_question() -> None:
    """Keep the easily confused cut answers governed by their decisive question."""
    decide = " ".join(_decide().split())
    assert "should this still be an obligation a completion gate reads?" in decide
    assert "If yes and only its reach is wrong, narrow. If no, demote." in decide


def test_demotion_stays_unresolved_until_an_owner_authorized_amendment() -> None:
    """Keep removal of an accepted obligation from becoming a free change."""
    decide = " ".join(_decide().split())
    assert "needs owner authority and stays unresolved until that owner-authorized amendment lands" in decide


def test_every_axis_walks_its_surfaces() -> None:
    """Keep surface traversal as a precondition for every response."""
    assert "Every answer walks its surfaces before it is taken" in _decide()


def test_cut_walks_backwards() -> None:
    """Keep cut focused on references to what no longer exists."""
    assert "cut walks backwards to what referenced the removed thing" in _decide()


def test_route_walks_outwards_then_back() -> None:
    """Keep routing responsible for complete ownership and local cleanup."""
    assert "route walks outwards to confirm the owner covers the whole claim, then back to remove what still states it locally" in " ".join(_decide().split())


def test_fix_walks_sideways() -> None:
    """Keep repairs responsible for their related instances and pins."""
    assert "fix walks sideways across other instances, the companions describing them, and anything pinning those" in " ".join(_decide().split())


def test_hold_walks_forwards() -> None:
    """Keep held decisions visible to the next round."""
    assert "hold walks forwards so the next round can see the decision" in " ".join(_decide().split())


def test_every_walk_starts_with_the_required_frontier() -> None:
    """Keep the frontier broad enough to include companions and pins.

    Stated once for every axis rather than inside Fix: the frontier is the same
    wherever the walk starts, and a second copy under one axis is the duplicate
    home this ladder's own Cut answers exist to remove.
    """
    decide = " ".join(_decide().split())
    assert "Every walk starts from the cited location and expands to every other instance of the same claim, the companion statements that describe it, and anything that pins any of those." in decide


# STUB: test_post_repair_traversal_uses_literal_and_semantic_instruments — post-repair traversal has both instruments
def test_post_repair_traversal_uses_literal_and_semantic_instruments() -> None:
    decide = _section("## Step 5. DECIDE")
    traversal = decide.split("Every walk starts", 1)[1].split("\n- **Blockers**", 1)[0]
    statements = _sentences("Every walk starts" + traversal)
    exception_map = {
        "Every walk starts": "defines the initial frontier rather than an instrument",
        "Each change opens its own frontier": "defines empty-frontier termination rather than an instrument",
    }
    exceptions = [
        statement
        for statement in statements
        if any(statement.startswith(prefix) for prefix in exception_map)
    ]
    instruments = [statement for statement in statements if statement not in exceptions]

    assert len(exceptions) == len(exception_map)
    assert all(
        "walk" in statement
        or "literal sweep" in statement
        or "semantic walk" in statement
        or "After a repair, run both instruments again" in statement
        for statement in instruments
    )
    # Pin the per-round obligation as a property, not as one blessed sentence
    # opener. A guard keyed to exact phrasing reds on a faithful rewrite and
    # stays green when the same claim is reworded away — the failure this
    # section's own guidance exists to stop.
    round_scope = " ".join(statement for statement in instruments if "review round" in statement)
    assert "literal sweep" in round_scope
    assert "semantic walk" in round_scope
    repair_reruns = [
        statement for statement in instruments if "After a repair, run both instruments again" in statement
    ]
    assert len(repair_reruns) == 1
    assert "step-8a anchor-test sweep" in repair_reruns[0]
    assert "every file the repair touched" in repair_reruns[0]


def test_surface_walk_continues_until_its_frontier_is_empty() -> None:
    """Keep changes from closing traversal before their own surfaces are checked."""
    decide = " ".join(_decide().split())
    assert "Each change opens its own frontier, so continue until the frontier is empty." in decide


def test_surface_walk_informs_the_ladder_choice() -> None:
    """Keep broad claim placement evidence for a generator repair or claim drop."""
    decide = " ".join(_decide().split())
    assert "What the walk finds feeds back into the choice of rung" in decide
    assert "evidence for repairing its generator or dropping it" in decide


def test_decide_is_count_neutral() -> None:
    """Keep a changing answer set from carrying a stale adjacent count."""
    decide = _decide().lower()
    assert "eight answers" not in decide
    assert "ten answers" not in decide
    assert not re.search(r"one of the \w+ answers", decide)


def test_verdict_reference_is_count_neutral() -> None:
    """Keep the response schema from restating a stale answer-set count."""
    verdict = VERDICT.read_text(encoding="utf-8").lower()
    assert "eight answers" not in verdict
    assert "ten answers" not in verdict
    assert not re.search(r"one of the \w+ answers", verdict)


def test_decide_says_a_sustained_finding_does_not_require_an_edit() -> None:
    """Keep the guidance from turning an advisory answer into an edit obligation."""
    decide = _decide()
    assert "A sustained finding does not by itself require an edit." in " ".join(decide.split())


def test_response_metadata_may_not_feed_a_score() -> None:
    """Close the gap between deciding a verdict and scoring one.

    The spec forbids these fields from blocking, failing, downgrading OR scoring
    a review. Absence from the state-deciding sections covers the first three; a
    score is a separate route to gating by another name.
    """
    metadata = " ".join(_section(VERDICT, "### Response metadata").split())
    assert "nothing may derive a score from them" in metadata
    assert "not their values, their absence, or their being malformed or unpaired" in metadata


def test_drop_applies_only_while_the_obligation_survives() -> None:
    """Separate drop from cut when the assertion is the whole obligation."""
    decide = " ".join(_decide().split())
    assert "applies only to an assertion no surviving contract obligation depends on" in decide
    assert "When the assertion is the whole obligation, removing it removes the obligation, and that is `cut-the-item`." in decide


def test_demotion_states_its_eligibility_predicate() -> None:
    """A machine-backed obligation must not look demotable."""
    assert "It applies when the obligation's only check is that a sentence exists." in " ".join(_decide().split())


def test_demotion_reason_records_destination_pin_and_authority() -> None:
    """A demotion recorded without these is indistinguishable from a deletion."""
    assert (
        "Its reason records the destination that now owns the obligation, the pin "
        "that catches its removal, and the owner authority permitting the removal."
    ) in " ".join(_decide().split())


# STUB: AC-0001 — upstream and downstream pins stay distinct for intent demotion
# STUB: AC-0002 — upstream and downstream pins stay distinct for brief demotion
# STUB: AC-0003 — upstream and downstream pins stay distinct for brief demotion
def test_demotion_pin_guidance_distinguishes_upstream_and_downstream() -> None:
    cut = _section("### Cut")
    demotion = _answer_bodies(cut)["demote-the-claim"]
    pin_types = {
        pin_type: sentence
        for sentence in _sentences(demotion)
        for pin_type in ("upstream", "downstream")
        if pin_type in sentence.casefold()
    }
    exception_map = {
        "downstream": "downstream lifecycle material retains a content test",
    }

    assert set(pin_types) == {"upstream", "downstream"}
    assert set(pin_types) - set(exception_map) == {"upstream"}
    assert "revision-bound lifecycle invalidation" in pin_types["upstream"]
    assert "content test" in pin_types["downstream"]
