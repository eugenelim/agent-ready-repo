"""Repository-level coverage for the rubric-to-brief ownership boundary.

These two guards relate a shipped `core` pack file to a `docs/product/` brief,
so they cross the pack boundary and cannot live under `packs/core/tests/`
(`pack-tests-stay-in-pack`). The pack-local criterion-shape guards stay where
they are; only the cross-boundary pair moved here.

The brief declares that it describes no part of the rubric's content. Six review
rounds produced repeated findings about which document owned or described which
rule, because each repair moved text and left a sentence describing where it
went. These make the declaration checkable rather than another claim that can go
stale.
"""

from __future__ import annotations

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

# Calibration, measured 2026-09-08 after the restatements were cut, excluding
# Markdown table delimiters (`| --- | --- |` runs match trivially and carry no
# prose): the two files share 2 six-word runs and 0 of seven or more. Both are
# `an implementation loop with gates between`, incidental shared phrasing about
# the same benchmark caveat, and `authored where an owner already exists,`,
# class 1's subject named in the brief's Outcome. Neither extends to seven in
# either direction, so seven is the shortest run length that reds only on
# restatement.
#
# An earlier revision set this to eight while the two substantive restatements
# were seven words long -- a threshold calibrated one word above the duplication
# it existed to catch, which is why the number and its evidence are recorded
# here rather than asserted.
#
# One structural caveat the threshold does not cover: a rubric *heading* of
# seven words or more, quoted by name in the brief, would red this guard on
# correct text. An earlier revision had exactly that case and it disappeared
# when the section was renamed, which is why it is recorded rather than assumed
# absent.
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
    clause list is present in the rubric, and the brief describes no part of the
    rubric's content, so the tell text must not appear there at all. Truncating
    the rubric reds the first assertion; pasting the tell back into the brief
    reds the second.
    """
    assert ALTITUDE_TELL in flattened(RUBRIC), (
        "the altitude tell lost a clause in its own home"
    )
    assert ALTITUDE_TELL not in flattened(BRIEF), (
        "the brief restates the rubric's tell; it must cite the class, not its text"
    )


def test_the_brief_restates_no_run_of_the_rubrics_text() -> None:
    """Enforce the cut, not just perform it.

    Named blind spots: a paraphrase, or any verbatim run shorter than the
    threshold, passes -- two six-word runs are admitted today and recorded in
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
