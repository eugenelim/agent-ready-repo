"""Contract tests for what a rendered-page inspection records.

Two halves. What the evidence manifest carries, read from `SKILL.md` because the
manifest is the adopter-facing surface. And how a skipped or failed run stays
distinguishable from a completed one, read from the reference's result tables.
"""

from __future__ import annotations

import pytest
from frontend_engineering_rendered_page_rules import (
    is_completed_inspection,
    manifest_fields,
    observations_rules,
    observations_value_is_acceptable,
    read_rules,
    read_skill,
    result_states,
    result_surfaces,
)

# The three families the contract names separately, alongside the skip.
FAILURE_STATES = ["failed-navigation", "failed-capture", "failed-judgement"]
SKIP_STATE = "skipped-no-browser"


@pytest.fixture(scope="module")
def rules_markdown() -> str:
    return read_rules()


@pytest.fixture(scope="module")
def skill_markdown() -> str:
    return read_skill()


# ── the manifest ────────────────────────────────────────────────────────────

def test_the_manifest_carries_an_observations_field_distinct_from_screenshots(
    skill_markdown: str, rules_markdown: str
) -> None:
    """Verifies: the evidence manifest records what was observed in the
    captures."""
    fields = manifest_fields(skill_markdown)
    expected = observations_rules(rules_markdown)["field-name"]

    assert expected in fields, (
        f"the manifest has no {expected!r} field; it carries {fields}"
    )
    assert "screenshots" in fields, (
        "the screenshots field disappeared — the observations field is meant to "
        "sit alongside it, not replace it"
    )
    assert expected != "screenshots"
    assert observations_rules(rules_markdown)["distinct-from"] == "screenshots"


def test_the_manifest_field_count_matches_the_table(skill_markdown: str) -> None:
    """The manifest states how many required fields it has. Adding a field
    without moving that number leaves the surface contradicting itself."""
    fields = manifest_fields(skill_markdown)
    assert f"**Required fields (all {len(fields)} must be present):**" in skill_markdown, (
        f"the manifest table holds {len(fields)} fields but its heading claims a "
        f"different count"
    )


@pytest.mark.parametrize(
    "value",
    [
        "short-at-rest.png",
        "short-at-rest.png tall-at-rest.png",
        "short-at-rest.png, short-scrolled.png, tall-at-rest.png, tall-scrolled.png",
        "a.jpg b.webp",
    ],
)
def test_a_value_naming_only_filenames_does_not_satisfy_the_field(
    rules_markdown: str, value: str
) -> None:
    """Verifies: a value naming only capture filenames does not satisfy that
    observations field."""
    assert not observations_value_is_acceptable(rules_markdown, value), (
        f"{value!r} is a filename list and was accepted as an observation"
    )


@pytest.mark.parametrize(
    "value",
    [
        "completed — nav covers the h1 at 600px at rest (occlusion, Blocker)",
        "completed — nothing reader-visible wrong across all four captures",
        "skipped-no-browser — no Chromium reachable",
    ],
)
def test_a_real_observation_satisfies_the_field(
    rules_markdown: str, value: str
) -> None:
    """The green path. Without it, a rule rejecting every value would satisfy
    the filename-rejection assertion above."""
    assert observations_value_is_acceptable(rules_markdown, value)


def test_an_empty_value_does_not_satisfy_the_field(rules_markdown: str) -> None:
    assert not observations_value_is_acceptable(rules_markdown, "   ")


# ── degradation ─────────────────────────────────────────────────────────────

def test_the_no_browser_result_names_the_missing_capability(
    rules_markdown: str, skill_markdown: str
) -> None:
    """Verifies: when no browser is reachable, the recorded result names the
    missing capability."""
    assert not is_completed_inspection(rules_markdown, SKIP_STATE)

    # Asserted against table rows, not the prose around them. A sentence gets
    # rewrapped; a row does not.
    for source, label in ((rules_markdown, "reference"), (skill_markdown, "skill")):
        row = next(
            (
                line
                for line in source.splitlines()
                if line.strip().startswith(f"| {SKIP_STATE} ")
            ),
            None,
        )
        assert row is not None, f"the {label} has no {SKIP_STATE} row"
        assert "missing capability" in row.lower(), (
            f"the {label}'s {SKIP_STATE} row does not say it names the missing "
            f"capability: {row}"
        )


def test_a_skip_is_distinguishable_from_a_completed_run_in_all_three_surfaces(
    rules_markdown: str,
) -> None:
    """Verifies: a skipped inspection is distinguishable from a completed one in
    each of the three surfaces a result reaches."""
    surfaces = result_surfaces(rules_markdown)
    assert sorted(surfaces) == [
        "acceptance-gate-input",
        "evidence-manifest",
        "step-output",
    ], f"the three result surfaces changed: {sorted(surfaces)}"

    for surface, carries in surfaces.items():
        assert carries == "yes", (
            f"{surface} does not carry the result state, so a skip cannot be "
            f"told from a completed run there"
        )

    assert is_completed_inspection(rules_markdown, "completed")
    assert not is_completed_inspection(rules_markdown, SKIP_STATE)


@pytest.mark.parametrize("state", FAILURE_STATES)
def test_a_failure_cannot_satisfy_a_completed_inspection(
    rules_markdown: str, state: str
) -> None:
    """Verifies: a navigation failure, a capture failure, or a judgement failure
    yields a result that cannot satisfy a completed inspection."""
    assert not is_completed_inspection(rules_markdown, state)


@pytest.mark.parametrize("state", FAILURE_STATES)
def test_each_failure_family_records_its_own_distinguishable_state(
    rules_markdown: str, state: str
) -> None:
    """Verifies the other half: each failure family records a state
    distinguishable from a completed inspection — and from each other.

    A single "unverified" bucket would satisfy the assertion above while losing
    which thing went wrong, so distinctness is asserted rather than assumed.
    """
    states = result_states(rules_markdown)
    assert state in states, f"{state} is not a declared result state"

    # Distinctness is read from the shipped table, not from this module's own
    # constants: a list built from distinct literals is distinct by
    # construction and proves nothing about what the pack ships.
    declared = [s for s in (*FAILURE_STATES, SKIP_STATE) if s in states]
    assert len(declared) == 4, (
        f"the skip and the three failure families are not four distinct rows in "
        f"the shipped Result states table; it declares {sorted(states)}"
    )
    assert not is_completed_inspection(rules_markdown, state)


def test_exactly_one_result_state_is_a_completed_inspection(
    rules_markdown: str,
) -> None:
    """`completed` is the only pass. If a second state ever reads as completed,
    every degradation assertion above becomes routable around."""
    states = result_states(rules_markdown)
    completed = [s for s, v in states.items() if v == "yes"]
    assert completed == ["completed"], (
        f"states reading as a completed inspection: {completed}"
    )


# ── the criterion-bearing result states, pinned by name ────────────────────
#
# A sweep deleting every rule row in the reference found `incomplete` and
# `unusable-capture` removable with the suite green, because the evaluators
# return those literals regardless of whether the table declares them. Both
# carry acceptance criteria, so both must be declared.
#
# `clipped` and `illegible` are also removable and that is CORRECT: no criterion
# requires those classes to exist. The one-severity-per-class rule governs the
# rows that are present, not which classes a pack chooses to ship.

CRITERION_BEARING_STATES = {
    "completed": "yes",
    "incomplete": "no",
    "unusable-capture": "no",
    "skipped-no-browser": "no",
    "failed-navigation": "no",
    "failed-capture": "no",
    "failed-judgement": "no",
}


def test_every_criterion_bearing_result_state_is_declared(rules_markdown: str) -> None:
    """Each of these is named by an acceptance criterion, so the shipped table
    has to declare it — and declare whether it is a completed inspection."""
    states = result_states(rules_markdown)
    for name, expected in CRITERION_BEARING_STATES.items():
        assert name in states, (
            f"the shipped Result states table no longer declares {name!r}, which "
            f"an acceptance criterion names"
        )
        assert states[name] == expected, (
            f"{name!r} is declared {states[name]!r}, expected {expected!r}"
        )


@pytest.mark.parametrize("state", sorted(CRITERION_BEARING_STATES))
def test_dropping_a_criterion_bearing_state_is_caught(
    rules_markdown: str, state: str
) -> None:
    mutated = "\n".join(
        ln for ln in rules_markdown.splitlines()
        if not ln.strip().startswith(f"| {state} |")
    )
    assert mutated != rules_markdown
    with pytest.raises(AssertionError, match="no longer declares"):
        test_every_criterion_bearing_result_state_is_declared(mutated)
