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

import re
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

# Calibration. `ADMITTED_SIX_WORD_RUNS` is the recorded measurement, and
# `test_the_calibration_record_matches_the_measurement` compares it to the tree
# with the guard's own matcher — flattened text, `---` runs excluded, membership
# by substring containment. Containment is the load-bearing detail: an earlier
# record held two runs because it intersected six-word *windows* from both
# files instead, and windowing splits a run wherever the two files align
# differently, while containment does not.
#
# What containment does not buy is punctuation tolerance. The comparison is
# byte-exact over whitespace-normalised text, so a restatement that changes one
# quote, dash or comma inside the run is not found — the same wording with a
# curly apostrophe is a different string here. That is a blind spot of the
# matcher, not of the record: this guard catches verbatim drift and nothing
# weaker, which is the failure that actually recurred.
#
# One case is worth naming because it has moved twice. The rubric's § 5 heading
# was a third shared run while the brief quoted it by name; the brief now cites
# `§ 5` by number, so it is not shared today. If a future edit quotes any rubric
# heading by name, that heading returns as a shared run — and a heading of seven
# words or more would red this guard on correct text. The exact set comparison
# below is what surfaces that, in either direction, instead of a prose count
# that has now been wrong three times.
#
# No run of seven or more is shared, so seven is the shortest length that reds
# only on restatement. An earlier revision set it to eight while the two
# substantive restatements were seven words long — one word above the
# duplication it existed to catch, which is why the number and its evidence are
# recorded here rather than asserted.
ADMITTED_SIX_WORD_RUNS = (
    "an implementation loop with gates between",
    "authored where an owner already exists,",
)
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


def test_the_calibration_record_matches_the_measurement() -> None:
    """The record is the only evidence for the threshold, so check it exactly.

    Three earlier revisions of this record were wrong: one set the threshold a
    word above the duplication it existed to catch; one recorded two shared runs
    where the guard's matcher finds three, having measured by intersecting word
    windows rather than by containment; and one asserted the count through a
    string substitution that rewrote the record to match the measurement, so it
    could not fail when the record *over*-counted.

    An exact set comparison fails in both directions.
    """
    rubric_words = flattened(RUBRIC).split()
    brief = flattened(BRIEF)
    n = RESTATEMENT_RUN_WORDS - 1
    measured = {
        run
        for i in range(len(rubric_words) - n + 1)
        if "---" not in (run := " ".join(rubric_words[i : i + n])) and run in brief
    }
    assert measured == set(ADMITTED_SIX_WORD_RUNS), (
        "the calibration record no longer matches the tree; "
        f"measured {sorted(measured)}, recorded {sorted(ADMITTED_SIX_WORD_RUNS)}"
    )


def test_the_brief_restates_no_run_of_the_rubrics_text() -> None:
    """Enforce the cut, not just perform it.

    Named blind spots: a paraphrase, or any verbatim run shorter than the
    threshold, passes -- the admitted six-word runs are recorded in
    `ADMITTED_SIX_WORD_RUNS` above. A restatement in any file other than these two
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


def _brief_section(title: str) -> str:
    """Return one `###` section of the brief, heading excluded."""
    body = BRIEF.read_text(encoding="utf-8")
    start = body.index(f"### {title}\n")
    rest = body[start + len(f"### {title}\n"):]
    end = rest.find("\n### ")
    return rest if end == -1 else rest[:end]


def test_the_corpus_section_publishes_an_instrument_not_a_snapshot() -> None:
    """The one growing-corpus figure set is the brief's own decay case.

    Three revisions of these percentiles went stale or failed to reproduce
    inside a week, each caught by a review round rather than by a check. Rubric
    class 4's move is to ship the derivation rather than the value, so § "Corpus"
    carries the instrument and no snapshot.

    The predicate is comma-grouped digits, which is what a spec count, a
    criteria count or a word percentile looks like here. Dates (`2026-09-08`)
    and the status regex carry no comma, so they pass; re-adding
    "421 specs, 6,465 criteria" or a "median 1,607" reds.
    """
    corpus = _brief_section("Corpus")
    grouped = sorted(set(re.findall(r"\b\d{1,3},\d{3}\b", corpus)))
    assert not grouped, (
        f"§ Corpus publishes a snapshot figure again: {grouped}. "
        "Class 4's move is the derivation, not the value."
    )
    assert "publishes an instrument, not a snapshot" in " ".join(corpus.split())


def test_the_repo_derived_bound_states_a_percentile_not_a_value() -> None:
    """The only band row reading this corpus must not store a number.

    Stated as a value it decayed within a week of each measurement; stated as
    the derivation it means the current corpus whenever it is read. A digit in
    the Bound cell is the regression.
    """
    band = _brief_section("Band")
    rows = [r for r in band.splitlines() if r.startswith("| Spec body ")]
    assert len(rows) == 1, f"expected one Spec body row, found {len(rows)}"
    bound = rows[0].split("|")[2]
    # A percentile *name* legitimately carries digits, in either spelling
    # (`p75`, `75th percentile`), so strip both before looking for a magnitude.
    # Two earlier versions red on correct text: one forbade any digit at all,
    # and one stripped only the `pNN` spelling, so rewriting the same bound in
    # words would have failed it. Both are the mirror of a control that cannot
    # fail, and the mirror is what a repair produces.
    magnitudes = re.sub(r"\bp\d{1,3}\b|\b\d{1,3}(st|nd|rd|th) percentile", "", bound)
    assert not re.search(r"\d", magnitudes), (
        f"the spec-body bound stores a value rather than naming a percentile: {bound.strip()!r}"
    )
    # Green in either spelling; red when the row stores a number instead.
    assert "median" in bound
    assert "p75" in bound or "percentile" in bound
