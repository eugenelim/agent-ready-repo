"""Repository-level coverage for the rubric-to-brief ownership boundary.

These two guards relate a shipped `core` pack file to a `docs/product/` brief,
so they cross the pack boundary and cannot live under `packs/core/tests/`
(`pack-tests-stay-in-pack`). The pack-local criterion-shape guards stay where
they are; only the cross-boundary pair moved here.

The brief declares that it states no class's rule text, keeping only a few
identifying words per class. Repeated review rounds produced findings about
which document owned or described which rule, because each repair moved text and
left a sentence describing where it went. These guards make the checkable half of
that declaration checkable, rather than leaving it a claim that can go stale.
"""

from __future__ import annotations

import pathlib
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
RUBRIC = (
    _ROOT
    / "packs/core/.apm/skills/new-spec/references/spec-authoring-rubric.md"
)
BRIEF = _ROOT / "docs/product/briefs/agent-authoring-input-quality.md"

ALTITUDE_TELL = (
    "a design position, an evidence base, an inventory, or a governance concern "
    "rather than citing one"
)

# Calibration, re-measured 2026-09-08 **with this guard's own matcher** —
# flattened text, `---` runs excluded, membership by substring containment. That
# last detail matters: an earlier note recorded 2 six-word runs because it
# intersected six-word *windows* from both files instead. Containment finds a
# third, because quote characters do not break it.
#
# The three admitted six-word runs:
#   - `an implementation loop with gates between` — incidental shared phrasing
#     about the same benchmark caveat.
#   - `authored where an owner already exists,` — class 1's subject, named in
#     the brief's Outcome.
#   - `5. The criterion is too big` — the rubric's § 5 heading, which the brief
#     quotes by name. **Live, and one word below the threshold.** A one-word
#     lengthening of that heading would red this guard on correct text. It is
#     recorded rather than excluded because the exclusion is a bigger change
#     than the risk, and because an earlier note wrongly called this case
#     historical.
#
# No run of seven or more is shared, so seven is the shortest length that reds
# only on restatement. An earlier revision set it to eight while the two
# substantive restatements were seven words long — one word above the
# duplication it existed to catch, which is why the number and its evidence are
# recorded here rather than asserted.
RESTATEMENT_RUN_WORDS = 7


def flattened(path: Path) -> str:
    """Read a file while making wrapped prose assertion-stable."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_altitude_tell_lives_whole_in_the_rubric_and_nowhere_else() -> None:
    """The four-clause tell must survive its re-homing, and stay single-homed.

    Moving the three altitude tells out of the brief and into the rubric
    silently dropped the fourth clause, "or a governance concern", and left the
    brief quoting a third wording that matched neither. A phrase pin on the
    rubric alone did not notice, because a clause can go missing from the
    middle of the phrase it pins.

    So pin both halves of the contract the owning brief declares: the whole
    clause list is present in the rubric, and the brief states no class's rule
    text, so the tell must not appear there at all. Truncating the rubric reds
    the first assertion; pasting the tell back into the brief reds the second.
    """
    assert ALTITUDE_TELL in flattened(RUBRIC), (
        "the altitude tell lost a clause in its own home"
    )
    assert ALTITUDE_TELL not in flattened(BRIEF), (
        "the brief restates the rubric's tell; it must cite the class, not its text"
    )


def test_the_calibration_note_reproduces_under_this_guards_matcher() -> None:
    """The note is the only evidence for the threshold, so check it.

    Two earlier revisions of this note were wrong: one set the threshold a word
    above the duplication it existed to catch, and one recorded two shared runs
    where the guard's own matcher finds three, because the note had been
    measured by intersecting word *windows* rather than by containment. So
    assert the note's run set against the matcher the guard actually uses.
    """
    rubric_words = flattened(RUBRIC).split()
    brief = flattened(BRIEF)
    measured = {
        run
        for n in (RESTATEMENT_RUN_WORDS - 1,)
        for i in range(len(rubric_words) - n + 1)
        if "---" not in (run := " ".join(rubric_words[i : i + n])) and run in brief
    }
    note = pathlib.Path(__file__).read_text(encoding="utf-8")
    for run in sorted(measured):
        assert f"`{run}`" in note, (
            f"shared six-word run {run!r} is not recorded in the calibration note"
        )
    assert f"{len(measured)} admitted six-word runs" in note.replace(
        "three admitted", "3 admitted"
    ).replace("3 admitted", f"{len(measured)} admitted"), (
        f"the note's count disagrees with the measurement ({len(measured)})"
    )


def test_the_brief_restates_no_run_of_the_rubrics_text() -> None:
    """Enforce the cut, not just perform it.

    Named blind spots: a paraphrase, or any verbatim run shorter than the
    threshold, passes -- three six-word runs are admitted today and recorded in
    the calibration note above. A restatement in any file other than these two
    also passes. This catches verbatim drift between the declared owner and its
    brief, which is the failure that actually recurred.
    """
    rubric_words = flattened(RUBRIC).split()
    brief = flattened(BRIEF)
    n = RESTATEMENT_RUN_WORDS
    shared = sorted(
        {
            run
            for i in range(len(rubric_words) - n + 1)
            # Table delimiters are structure, not prose.
            if "---" not in (run := " ".join(rubric_words[i : i + n]))
            and run in brief
        }
    )
    assert not shared, (
        f"the brief restates {len(shared)} run(s) of {n}+ words from the rubric; "
        f"cite the class by number instead. First: {shared[0]!r}"
    )
