"""The spec's verification tally, checked against its own criteria list.

`docs/specs/loop-telemetry-export/spec.md` states in prose how its live
criteria divide across three verification groups: validated stub, no stub
(implementation-discovered), and goal-based. That sentence is maintained by
hand, and nothing recomputes it. Adding, retiring or re-grouping a criterion
leaves it stale and still readable, which is the failure this file exists to
make impossible.

The spec is frozen, so this control reads it and never edits it. A failure here
means the sentence and the list disagree; which of the two is wrong is a
question for whoever changed one of them.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SPEC = _REPO / "docs/specs/loop-telemetry-export/spec.md"

# A criterion is a checkbox line. The ticked and unticked forms are both live:
# ticking one at ship time must not change which criteria the tally covers.
_CRITERION = re.compile(r"^- \[[ x]\] \*\*(AC-\d{4})\.\*\*", re.M)
_RETIRED_HEADING = "## Retired identifiers"
_TOTAL = re.compile(r"Across the (\d+) live criteria:")
# Each group is a bolded count followed by prose that names its identifiers.
# The count marker is all that is matched structurally: the group labels are
# wording, and pinning wording here would make this control fail on a copy-edit
# that changed nothing. Identifiers are then read from the segment, NOT from
# the first parenthesis in it -- one group label is itself parenthesised
# (`no stub (implementation-discovered)`), and reading that span found a group
# with a count and no identifiers.
_COUNT = re.compile(r"\*\*(\d+)\*\*")


def _spec_text() -> str:
    text = _SPEC.read_text(encoding="utf-8")
    # Identifiers below this heading are retired, not live. Including them
    # would make every retirement look like a tally error.
    head, _, _ = text.partition(_RETIRED_HEADING)
    return head


@pytest.fixture(scope="module")
def spec() -> str:
    return _spec_text()


def _tally(spec: str) -> tuple[int, list[tuple[int, list[str]]]]:
    total_match = _TOTAL.search(spec)
    assert total_match, (
        "the 'Across the N live criteria:' sentence is gone from spec.md; this "
        "control cannot check a tally that is no longer stated"
    )
    sentence = spec[total_match.start() : spec.index(".", spec.index("group", total_match.end()))]
    marks = list(_COUNT.finditer(sentence))
    groups = [
        (
            int(mark.group(1)),
            re.findall(
                r"AC-\d{4}",
                sentence[mark.end() : (marks[i + 1].start() if i + 1 < len(marks) else len(sentence))],
            ),
        )
        for i, mark in enumerate(marks)
    ]
    return int(total_match.group(1)), groups


def test_the_tally_states_three_groups(spec: str) -> None:
    """Guard the parse before the counts rest on it.

    Every assertion below reads the groups this finds. If the sentence were
    reshaped so that only one group parsed, those assertions could all pass
    while covering a fraction of the criteria.
    """
    _, groups = _tally(spec)
    assert len(groups) == 3, f"expected three verification groups, parsed {len(groups)}"


def test_each_group_count_matches_the_identifiers_it_lists(spec: str) -> None:
    _, groups = _tally(spec)
    for count, ids in groups:
        assert count == len(ids), (
            f"the tally claims {count} criteria but lists {len(ids)}: {', '.join(ids)}"
        )


def test_the_groups_partition_the_live_criteria(spec: str) -> None:
    """Every live criterion in exactly one group -- the claim the spec makes.

    Checked as a partition rather than as a count, because a criterion listed
    twice and a criterion listed nowhere cancel out in a total.
    """
    total, groups = _tally(spec)
    live = set(_CRITERION.findall(spec))
    assert live, "no criteria parsed from spec.md; the checkbox format changed"

    assert total == len(live), (
        f"the tally says {total} live criteria; the criteria list has {len(live)}"
    )

    listed: list[str] = [ac for _, ids in groups for ac in ids]
    assert len(listed) == len(set(listed)), (
        "a criterion appears in more than one verification group: "
        + ", ".join(sorted({ac for ac in listed if listed.count(ac) > 1}))
    )
    assert set(listed) == live, (
        "grouped but not a live criterion: "
        f"{sorted(set(listed) - live) or 'none'}; "
        "live but ungrouped: "
        f"{sorted(live - set(listed)) or 'none'}"
    )
