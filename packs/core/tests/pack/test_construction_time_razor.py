"""Content pins for the construction-time razor rules.

These are protection, not behaviour proof. The behaviour they stand behind is
model behaviour against a prose contract, which no in-repository runner can
execute: the spec verifies it with scored probe runs at delivery instead. What
these pins do is fail when an obligation is deleted, so a silent removal cannot
pass as a cosmetic edit.

Four obligations, four independent pins. A single pin over a shared heading
would pass after any one of the four disappeared, which is the failure these are
shaped to avoid. Two of them -- the declination rung and its non-rung exception
-- are the whole protection for a rule the contract carries no criterion for.

Pack-local by construction: both files live inside this pack, and the anchor
never climbs above it.
"""

from __future__ import annotations

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTER = PACK_ROOT / ".apm" / "agents" / "implementer.md"
WORK_LOOP = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"


def flat(path: Path) -> str:
    """Return ``path``'s text with whitespace collapsed to single spaces.

    The sources wrap these rules across lines, so a raw substring match would
    pin the line-break position rather than the obligation.
    """
    return " ".join(path.read_text(encoding="utf-8").split())


# The seed's razor pin identifies a ladder by these rung markers. Reuse that
# semantics rather than its numbered-list regex: a numbered list in an agent
# file is ordinary prose -- implementer.md's own "Load context first" steps are
# one -- so counting list items here would fire on a legitimate list and say
# nothing about whether the ladder was restated.
LADDER_MARKERS = (
    "not genuinely needed",
    "repository solution",
    "standard library",
    "native platform",
    "already-installed dependency",
    "one obvious line",
    "minimum correct",
)


def test_implementer_records_the_rung_it_stopped_at() -> None:
    """Pin 1: the report carries the stopping rung, so the choice is legible."""
    text = flat(IMPLEMENTER)
    # Case-stable fragment: the sentence's leading verb moves as the rule is
    # reworded, and its capitalisation is not the obligation.
    assert "the rung your implementation stopped at" in text, (
        "implementer.md no longer asks the report to record the rung the "
        "implementation stopped at; the supervisor cannot see the decision"
    )


def test_implementer_searches_before_it_writes() -> None:
    """Pin 1b: the bounded search and the reuse of a hit are the rule itself."""
    text = flat(IMPLEMENTER)
    assert "take that ladder's search rung once" in text, (
        "implementer.md no longer requires the bounded search"
    )
    assert "reuse a hit that satisfies the outcome" in text, (
        "implementer.md no longer requires reusing an adequate hit"
    )
    assert "**Report the search every time**" in text, (
        "the search receipt is no longer unconditional; a run that skips the "
        "search can satisfy a conditional receipt by saying nothing, which is "
        "the measured failure this wording replaced"
    )


def test_implementer_may_take_a_lighter_route_than_approach() -> None:
    """Pin 1c: `Approach:` is working material, and `failed` turns on `Done when:`."""
    text = flat(IMPLEMENTER)
    assert "**implement the lighter rung**" in text, (
        "implementer.md no longer directs the lighter rung; a permissive "
        "phrasing measured 1 of 2 runs and missed the two-run bar"
    )
    assert "no route you can see satisfies the task's `Done when:`" in text, (
        "the `failed` status no longer turns on `Done when:`; it has gone back "
        "to reading the task body's approach as binding"
    )


def test_declination_names_the_rung_that_killed_it() -> None:
    """Pin 2: the whole protection for a rule with no acceptance criterion."""
    text = flat(WORK_LOOP)
    assert "the `Cut before adding` rung in `AGENTS.md` that killed it" in text, (
        "work-loop's declination register no longer asks for the rung that "
        "killed each temptation, so a declination is graded against nothing. "
        "This pin is the only thing protecting that rule -- the spec retired "
        "its acceptance criteria as non-mechanizable"
    )


def test_declination_admits_a_reason_no_rung_covers() -> None:
    """Pin 3: without the exception the rule demands a fabricated label."""
    text = flat(WORK_LOOP)
    assert "where no rung covers the decline" in text, (
        "work-loop's declination register no longer admits a non-rung reason; "
        "the rule now forces a rung onto a decline no rung explains"
    )
    assert "state that reason in the rung's place rather than fitting a rung to it" in text, (
        "the non-rung exception no longer tells the author what to write instead"
    )


def test_implementer_references_the_ladder_and_carries_no_copy_of_it() -> None:
    """Pin 4: exactly two ladder copies exist, and this file is not a third."""
    raw = IMPLEMENTER.read_text(encoding="utf-8")
    assert "`Cut before adding` ladder in `AGENTS.md`" in flat(IMPLEMENTER), (
        "implementer.md no longer names the ladder it defers to, so the rule "
        "has lost the definition it depends on"
    )
    lowered = raw.lower()
    restated = [marker for marker in LADDER_MARKERS if marker in lowered]
    assert not restated, (
        "implementer.md restates the ladder's rungs instead of referencing "
        f"them; found {restated}. Exactly two copies exist, in AGENTS.md and "
        "the seed, and both are pinned to differ textually. A third copy drifts "
        "from them silently"
    )
