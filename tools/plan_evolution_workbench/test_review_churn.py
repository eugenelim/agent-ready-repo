"""Tests for the frozen real-corpus review-churn evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from tools.plan_evolution_workbench.review_churn import (
    DEFAULT_RESULTS,
    ReviewChurnValidationError,
    load_and_validate,
    validate_current_case,
    validate_results,
)

ROOT = Path(__file__).resolve().parents[2]


def _load_results() -> dict[str, object]:
    """Load a fresh mutable copy of the checked-in results."""
    return json.loads((ROOT / DEFAULT_RESULTS).read_text(encoding="utf-8"))


def test_frozen_review_churn_results_validate() -> None:
    """The durable sources and every published aggregate remain aligned."""
    summary = validate_results(_load_results(), ROOT)

    assert summary["raw_findings"] == 75
    assert summary["later_round_findings"] == 38
    assert summary["later_recurrence_family_share"] == pytest.approx(32 / 38)


def test_round_relation_drift_fails_closed() -> None:
    """A changed finding count cannot leave the published total stale."""
    data = copy.deepcopy(_load_results())
    data["tier_a_cases"][0]["rounds"][1]["repeated"] = 0

    with pytest.raises(ReviewChurnValidationError, match="relation counts"):
        validate_results(data, ROOT)


def test_source_digest_drift_fails_closed() -> None:
    """A durable review artifact cannot change behind the frozen result."""
    data = copy.deepcopy(_load_results())
    data["tier_a_cases"][1]["sources"][0]["sha256"] = "0" * 64

    with pytest.raises(ReviewChurnValidationError, match="source digest mismatch"):
        validate_results(data, ROOT)


def test_every_round_requires_a_bound_source() -> None:
    """A retained count cannot outlive the source binding for its round."""
    data = copy.deepcopy(_load_results())
    portfolio = data["tier_a_cases"][2]
    portfolio["sources"][3]["rounds"] = [3]

    with pytest.raises(ReviewChurnValidationError, match="rounds lack source bindings"):
        validate_results(data, ROOT)


@pytest.mark.parametrize(
    ("source_group", "source_index"),
    [
        ("tier_b_cases", 0),
        ("tier_b_cases", 1),
        ("repository_aggregate_observations", None),
        ("prior_experiment_sources", 0),
        ("prior_experiment_sources", 1),
    ],
)
def test_non_tier_a_source_digest_drift_fails_closed(
    source_group: str, source_index: int | None
) -> None:
    """Every quantitative supporting source remains integrity-bound."""
    data = copy.deepcopy(_load_results())
    if source_group == "tier_b_cases":
        assert source_index is not None
        source = data[source_group][source_index]["source"]
    elif source_group == "repository_aggregate_observations":
        source = data[source_group]["source"]
    else:
        assert source_index is not None
        source = data[source_group][source_index]
    source["sha256"] = "0" * 64

    with pytest.raises(ReviewChurnValidationError, match="source digest mismatch"):
        validate_results(data, ROOT)


def test_current_case_normalization_must_match_summary_and_raw_digests() -> None:
    """The durable substitute for prunable reports is structurally reconciled."""
    results = _load_results()
    summary = results["tier_a_cases"][0]
    current_path = (
        ROOT
        / "docs/product/research/plan-evolution-experiments/review-churn-current-case.json"
    )
    current = json.loads(current_path.read_text(encoding="utf-8"))
    raw_digests = {
        f"adversarial_round_{index}": summary["sources"][index - 1]["sha256"]
        for index in range(1, 7)
    }
    raw_digests.update(
        {
            "security_round_1": summary["sources"][6]["sha256"],
            "security_round_2": summary["sources"][7]["sha256"],
        }
    )

    wrong_count = copy.deepcopy(current)
    wrong_count["classification"]["raw_findings"] = 9
    with pytest.raises(ReviewChurnValidationError, match="classification disagrees"):
        validate_current_case(wrong_count, summary, raw_digests)

    wrong_digest = copy.deepcopy(current)
    wrong_digest["source_digests"]["adversarial_round_2"] = "0" * 64
    with pytest.raises(ReviewChurnValidationError, match="source digest disagrees"):
        validate_current_case(wrong_digest, summary, raw_digests)

    wrong_security = copy.deepcopy(current)
    wrong_security["supplemental_security"]["round_1_sustained"] = 3
    with pytest.raises(ReviewChurnValidationError, match="supplemental security"):
        validate_current_case(wrong_security, summary, raw_digests)

    wrong_agreement = copy.deepcopy(current)
    wrong_agreement["classification"]["independent_classifiers"] = 0
    wrong_agreement["classification"]["agreement"] = ""
    with pytest.raises(ReviewChurnValidationError, match="independent-classification"):
        validate_current_case(wrong_agreement, summary, raw_digests)


def test_current_case_requires_declared_security_sources() -> None:
    """The durable security summary cannot outlive its raw-source declaration."""
    data = copy.deepcopy(_load_results())
    current = data["tier_a_cases"][0]
    current["sources"] = [
        source for source in current["sources"] if "security-reviewer" not in source["path"]
    ]

    with pytest.raises(ReviewChurnValidationError, match="lack declared source evidence"):
        validate_results(data, ROOT)


def test_missing_and_unknown_fields_fail_closed() -> None:
    """Versioned result objects reject both schema drift directions."""
    missing = copy.deepcopy(_load_results())
    del missing["tier_a_cases"][0]["rounds"][0]["words"]
    with pytest.raises(ReviewChurnValidationError, match="missing fields"):
        validate_results(missing, ROOT)

    unknown = copy.deepcopy(_load_results())
    unknown["tier_a_cases"][0]["rounds"][0]["estimated_tokens"] = 1
    with pytest.raises(ReviewChurnValidationError, match="unknown fields"):
        validate_results(unknown, ROOT)


def test_duplicate_keys_and_non_finite_numbers_fail_closed(tmp_path: Path) -> None:
    """The JSON boundary rejects ambiguous keys and non-standard numbers."""
    original = (ROOT / DEFAULT_RESULTS).read_text(encoding="utf-8")
    duplicate = original.replace(
        '"schema_version": "review-churn-results.v1",',
        '"schema_version": "review-churn-results.v1",\n'
        '  "schema_version": "review-churn-results.v1",',
        1,
    )
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(duplicate, encoding="utf-8")
    with pytest.raises(ReviewChurnValidationError, match="duplicate JSON key"):
        load_and_validate(duplicate_path, ROOT)

    non_finite = original.replace(
        '"later_recurrence_family_share": 0.8421',
        '"later_recurrence_family_share": NaN',
        1,
    )
    non_finite_path = tmp_path / "non-finite.json"
    non_finite_path.write_text(non_finite, encoding="utf-8")
    with pytest.raises(ReviewChurnValidationError, match="non-finite JSON number"):
        load_and_validate(non_finite_path, ROOT)
