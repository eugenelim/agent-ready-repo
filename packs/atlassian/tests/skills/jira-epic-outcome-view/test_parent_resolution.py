"""Resolving each issue's parent chain up to the Epic rung.

A flow per-issue row carries no Epic and no parent, so this walk is the
whole join. Jira Software nests Epic above Story above Subtask, so a
one-hop lookup silently loses every subtask -- and a lost subtask is a
row that lands in the unattributed group instead of its Epic.
"""
from __future__ import annotations

import pytest

# PROJ-400 is the Epic; PROJ-2 a Story under it; PROJ-3 a subtask under
# that Story, two hops away. PROJ-8's chain leaves the queried scope and
# PROJ-9 and PROJ-10 point at each other.
LINKS = {
    "PROJ-400": None,
    "PROJ-1": "PROJ-400",
    "PROJ-2": "PROJ-400",
    "PROJ-3": "PROJ-2",
    "PROJ-7": None,
    "PROJ-8": "PROJ-900",
    "PROJ-9": "PROJ-10",
    "PROJ-10": "PROJ-9",
}
EPICS = ["PROJ-400"]


@pytest.fixture
def parents(load_module):
    return load_module("parents")


def test_a_subtask_reaches_its_epic_in_two_hops(parents):
    """The case a one-hop lookup loses: PROJ-3's immediate parent is a
    Story, and stopping there attributes it to nothing."""
    assert parents.resolve_epics(LINKS, EPICS)["PROJ-3"] == "PROJ-400"


def test_a_story_reaches_its_epic_in_one_hop(parents):
    assert parents.resolve_epics(LINKS, EPICS)["PROJ-1"] == "PROJ-400"


def test_an_epic_resolves_to_itself(parents):
    """An Epic can carry work directly, and must not be reported as an
    issue whose chain never reached an Epic."""
    assert parents.resolve_epics(LINKS, EPICS)["PROJ-400"] == "PROJ-400"


@pytest.mark.parametrize(
    ("key", "why"),
    [
        ("PROJ-7", "no parent link at all"),
        ("PROJ-8", "a parent outside the queried scope"),
        ("PROJ-9", "a chain that loops back on itself"),
    ],
)
def test_a_chain_that_never_reaches_an_in_scope_epic_resolves_to_nothing(
    parents, key, why
):
    """Each of these is rendered in the unattributed group rather than
    dropped, so resolving them to anything else would hide the issue."""
    assert parents.resolve_epics(LINKS, EPICS)[key] is None, why


def test_a_chain_longer_than_the_hop_limit_is_not_walked_forever(parents):
    """A deeper hierarchy than Jira models is treated as unresolvable
    rather than guessed at, and the walk still terminates."""
    deep = {f"PROJ-{n}": f"PROJ-{n + 1}" for n in range(1, 40)}
    deep["PROJ-40"] = "PROJ-400"

    assert parents.resolve_epics(deep, EPICS)["PROJ-1"] is None
