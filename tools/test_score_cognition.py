"""Tests for tools/score-cognition.py.

The load-bearing cases are the ones a reviewer established by execution: the
table confound the shipped readability tool hides, densities inventing a clean
score for a reply with no denominator, and one token counted twice when it is
both an inline span and a dotted name.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_score_cognition", _TOOLS / "score-cognition.py")
scorer = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(scorer)

# The shipped tool refuses to score below a 30-word floor, so fixtures clear it.
PROSE = (
    "The cat sat on the mat. The dog ran to the park. Birds sang in the trees. "
    "Rain fell on the roof all night. We walked to the shop and back again. "
    "The bread was warm and the tea was hot. She read a book by the fire. "
    "Snow covered the hill by the old church. The bus was late once more. "
    "He found his keys under the chair. The room was quiet after they left.\n"
)
TABLE_HEAVY = PROSE + "\n| one | two |\n| --- | --- |\n| a | b |\n| c | d |\n"


def test_table_rows_are_counted_but_never_scored_as_prose() -> None:
    """The confound the shipped readability tool cannot report."""
    plain = scorer.score(PROSE)
    tabled = scorer.score(TABLE_HEAVY)
    assert plain["table_rows"] == 0
    assert tabled["table_rows"] == 4
    # Table words raise the raw count without reaching the scored count, so the
    # share of the reply the reading score describes falls.
    assert tabled["scored_pct"] < plain["scored_pct"]


def test_a_token_that_is_both_an_inline_span_and_a_dotted_name_counts_once() -> None:
    once = scorer.score(PROSE + "\nSee `agentbundle.lint` for the rule.\n")
    bare = scorer.score(PROSE + "\nSee agentbundle.lint for the rule.\n")
    # Wrapping a dotted name in backticks must not double its contribution.
    assert once["jargon_density"] == bare["jargon_density"]


def test_a_reply_with_no_words_reports_absent_densities_not_clean_ones() -> None:
    """Zero is the best possible density; absent is the truth."""
    for empty in ("", "1234 5678", "|a|b|\n|-|-|\n"):
        values = scorer.score(empty)
        if values["raw_words"] == 0:
            assert values["table_density"] is None
            assert values["jargon_density"] is None
            assert values["scored_pct"] is None


def test_digits_and_non_latin_text_count_as_words() -> None:
    assert scorer.score("2026 2027 2028")["raw_words"] == 3
    assert scorer.score("これは日本語です")["raw_words"] > 0
    # A bare apostrophe run is not a word.
    assert scorer.score("''' ''' '''")["raw_words"] == 0


def test_an_unscorable_reply_reports_no_reading_level_rather_than_a_number() -> None:
    short = scorer.score("Four.")
    assert short["scorable"] is False
    assert short["ease"] is None and short["grade"] is None


def test_pair_delta_asserts_no_direction_and_names_the_coupled_dimension() -> None:
    delta = scorer.pair_delta(scorer.score(TABLE_HEAVY), scorer.score(PROSE))
    # Removing tables lowers table_density; the tool reports the movement and
    # does not call it an improvement, because the rule never said fewer is
    # better -- only that a table must earn its place.
    assert delta["table_density"] < 0
    assert delta["scored_pct"] > 0
    assert "signals_improved" not in delta
    assert delta["coupled_dimension"] == ["ease", "grade"]


def test_pair_delta_records_a_signal_it_could_not_measure() -> None:
    delta = scorer.pair_delta(scorer.score("Four."), scorer.score(PROSE))
    assert delta["ease"] is None
    assert "ease" in delta["unmeasured"]


def test_spread_reports_a_descriptive_range_and_not_the_comparator() -> None:
    samples = [scorer.score(PROSE), scorer.score(TABLE_HEAVY), scorer.score(PROSE + PROSE)]
    result = scorer.spread(samples)
    assert result["samples"] == 3
    assert result["table_density"] > 0
    # One sample cannot establish a range.
    assert scorer.spread([scorer.score(PROSE)])["ease"] is None


def test_a_path_outside_the_repository_is_refused(tmp_path) -> None:
    """The one property here on a trust boundary.

    The scorer reads untrusted model output. Its root is the repository it ships
    in, resolved from its own location -- not the caller's cwd, which would read
    whatever tree the tool is invoked from.
    """
    outside = tmp_path / "secret.md"
    outside.write_text(PROSE, encoding="utf-8")
    # Matched by name, not by type: `_file_safety()` re-execs the module on every
    # call, so its exception classes are not identity-stable across callers and
    # `pytest.raises(UnsafeContentError)` would never match.
    with pytest.raises(Exception, match="outside its declared root") as caught:
        scorer._read([str(outside)])
    assert type(caught.value).__name__ == "UnsafeContentError"


def test_two_distinct_names_inside_one_span_count_twice() -> None:
    """Span identity is not token identity."""
    one_span = scorer.score(PROSE + "\nSee `agentbundle.lint and agentbundle.build` now.\n")
    two_spans = scorer.score(PROSE + "\nSee `agentbundle.lint` and `agentbundle.build` now.\n")
    assert one_span["jargon_density"] == two_spans["jargon_density"]


def test_pooled_sd_and_standard_error_match_the_recorded_pilot() -> None:
    """Pinned against the pilot the spec records, because hand-computation failed.

    The first computation reported a mean of the six arm standard deviations
    where the pre-registration named the pooled figure, then compared a
    difference of means against the spread of single observations.
    """
    arms = [
        [66.92, 63.57, 57.27],
        [70.65, 59.66, 71.38],
        [51.33, 43.45, 51.32],
        [53.39, 56.11, 50.12],
        [61.82, 60.31, 55.39],
        [48.13, 60.77, 55.14],
    ]
    result = scorer.arm_stats(arms)
    assert result["pooled_sd"] == 4.97
    assert result["se_of_difference"] == 4.06
    assert result["df"] == 12
    assert result["sum_of_squares"] == 296.38


def test_arm_stats_reports_absent_rather_than_zero_when_no_arm_has_spread() -> None:
    assert scorer.arm_stats([[61.0], [62.0]])["pooled_sd"] is None
