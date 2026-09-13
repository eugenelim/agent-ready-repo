"""Contract tests for the rendered-page inspection severity rules.

The rules the inspection step turns on are held as tables in
`references/rendered-page-inspection.md` rather than as skill prose, so that a
check can assert the rule without pinning the sentences around it. These tests
read that file and nothing else: they are the executable reading of what it
states.
"""

from __future__ import annotations

import pytest

from frontend_engineering_rendered_page_rules import (
    SEVERITIES,
    read_rules,
    resolution_rules,
    resolve_severity,
    severity_by_class,
    table_rows,
)


@pytest.fixture(scope="module")
def rules_markdown() -> str:
    return read_rules()


def check_every_class_has_one_severity(markdown: str) -> None:
    """The completeness rule, callable on any markdown so the mutation test
    below can drive it against a deliberately malformed copy."""
    rows = table_rows(markdown, "Severity by finding class")
    assert rows, "the severity mapping is empty"

    classes = [row[0] for row in rows]
    assert len(classes) == len(set(classes)), (
        f"a finding class appears more than once: {classes}"
    )

    for row in rows:
        finding_class, severity = row[0], row[1]
        assert finding_class, f"a mapping row has no finding class: {row}"
        assert severity, (
            f"finding class {finding_class!r} has no severity — every class "
            f"must map to exactly one"
        )
        assert severity in SEVERITIES, (
            f"finding class {finding_class!r} maps to {severity!r}, which is "
            f"not one of the pack's severities {sorted(SEVERITIES)}"
        )


def test_every_finding_class_has_exactly_one_severity(rules_markdown: str) -> None:
    """Verifies: a finding's severity is derived from its finding class by the
    mapping the pack states."""
    check_every_class_has_one_severity(rules_markdown)


def test_at_rest_top_clipping_maps_to_blocking(rules_markdown: str) -> None:
    """Verifies: content clipped or covered at the top of the content area in an
    at-rest capture maps to blocking."""
    mapping = severity_by_class(rules_markdown)
    assert "clipped-at-rest-top" in mapping, (
        "the at-rest top-clipping class is absent from the severity mapping"
    )
    assert mapping["clipped-at-rest-top"] == "Blocker", (
        f"at-rest top clipping maps to {mapping['clipped-at-rest-top']!r}; the "
        f"contract requires it to map to blocking"
    )


def test_judge_supplied_severity_does_not_determine_the_result(
    rules_markdown: str,
) -> None:
    """Verifies: a severity supplied by a judge does not determine the result —
    where a supplied label conflicts with the mapping, the result carries the
    mapped severity."""
    mapping = severity_by_class(rules_markdown)

    for finding_class, mapped in mapping.items():
        conflicting = next(s for s in sorted(SEVERITIES) if s != mapped)
        resolved = resolve_severity(rules_markdown, finding_class, conflicting)
        assert resolved == mapped, (
            f"judge said {conflicting!r} for {finding_class!r}; result carried "
            f"{resolved!r}, expected the mapped {mapped!r}"
        )

    rules = resolution_rules(rules_markdown)
    assert rules.get("judge-supplied-severity") == "discarded"
    assert rules.get("severity-source") == "finding-class"


def test_a_class_row_without_a_severity_fails_the_completeness_check(
    rules_markdown: str,
) -> None:
    """The mutation that proves the completeness check can fail.

    The malformed row is spelled out rather than derived from the mapping's own
    keys: if the class set were the mapping's key set, "a class added without a
    severity" would be unrepresentable and the check could never fail.
    """
    mutated = rules_markdown.replace("| crowding | Minor |", "| crowding |  |", 1)
    assert mutated != rules_markdown, (
        "the mutation did not apply — the row it targets has changed shape, so "
        "this test is no longer exercising the completeness check"
    )

    with pytest.raises(AssertionError, match="has no severity"):
        check_every_class_has_one_severity(mutated)
