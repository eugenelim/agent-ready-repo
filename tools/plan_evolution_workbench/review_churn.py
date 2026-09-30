"""Validate and summarize the frozen real-corpus review-churn evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

DEFAULT_RESULTS = Path(
    "docs/product/research/plan-evolution-experiments/review-churn-results.json"
)
RELATION_FIELDS = (
    "initial_new",
    "repeated",
    "same_invariant_distinct",
    "later_new",
    "indeterminate",
)


class ReviewChurnValidationError(ValueError):
    """Raised when review-churn evidence violates its frozen contract."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting ambiguous duplicate names."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewChurnValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_finite(value: str) -> None:
    """Reject the non-standard NaN and infinity JSON constants."""
    raise ReviewChurnValidationError(f"non-finite JSON number: {value}")


def _load_strict_json(path: Path) -> dict[str, Any]:
    """Load one JSON object with duplicate and non-finite checks."""
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewChurnValidationError(f"cannot read JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ReviewChurnValidationError(f"JSON root must be an object: {path}")
    return data


def _require_exact_fields(
    record: dict[str, Any],
    required: set[str],
    optional: set[str],
    label: str,
) -> None:
    """Reject missing and unknown fields on one versioned evidence object."""
    missing = required - record.keys()
    unknown = record.keys() - required - optional
    if missing:
        raise ReviewChurnValidationError(f"{label} missing fields: {sorted(missing)}")
    if unknown:
        raise ReviewChurnValidationError(f"{label} unknown fields: {sorted(unknown)}")


def _require_int(record: dict[str, Any], field: str) -> int:
    """Return a non-negative integer field or reject the record."""
    if field not in record:
        raise ReviewChurnValidationError(f"missing integer field: {field}")
    value = record[field]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReviewChurnValidationError(f"{field} must be a non-negative integer")
    return value


def _read_regular_file(root: Path, relative_path: str) -> bytes:
    """Read one repository-confined regular file without following a leaf link."""
    candidate = root / relative_path
    resolved_root = root.resolve(strict=True)
    resolved_candidate = candidate.resolve(strict=True)
    if not resolved_candidate.is_relative_to(resolved_root):
        raise ReviewChurnValidationError(f"source escapes repository: {relative_path}")
    if candidate.is_symlink() or not candidate.is_file():
        raise ReviewChurnValidationError(f"source is not a regular file: {relative_path}")
    return candidate.read_bytes()


def _validate_source(
    root: Path, source: dict[str, Any], *, require_rounds: bool = False
) -> None:
    """Validate one frozen source digest, permitting declared ephemeral absence."""
    required_fields = {"path", "sha256", "required"}
    if require_rounds:
        required_fields.add("rounds")
    _require_exact_fields(source, required_fields, set(), "source")
    relative_path = source.get("path")
    expected = source.get("sha256")
    required = source.get("required")
    if not isinstance(relative_path, str) or not relative_path:
        raise ReviewChurnValidationError("source path must be a non-empty string")
    if not isinstance(expected, str) or len(expected) != 64:
        raise ReviewChurnValidationError(f"invalid source digest: {relative_path}")
    if not isinstance(required, bool):
        raise ReviewChurnValidationError(f"source required flag must be boolean: {relative_path}")
    if require_rounds:
        rounds = source.get("rounds")
        if (
            not isinstance(rounds, list)
            or not rounds
            or any(
                isinstance(value, bool) or not isinstance(value, int) or value < 1
                for value in rounds
            )
            or len(rounds) != len(set(rounds))
        ):
            raise ReviewChurnValidationError(f"source rounds are invalid: {relative_path}")
    candidate = root / relative_path
    if not candidate.exists() and not required:
        return
    actual = hashlib.sha256(_read_regular_file(root, relative_path)).hexdigest()
    if actual != expected:
        raise ReviewChurnValidationError(
            f"source digest mismatch: {relative_path}: expected {expected}, got {actual}"
        )


def validate_current_case(
    current: dict[str, Any], summary: dict[str, Any], source_digests: dict[str, str]
) -> None:
    """Reconcile the durable current-case normalization with its summary."""
    _require_exact_fields(
        current,
        {
            "schema_version",
            "captured_at",
            "run_id",
            "subject",
            "source_digests",
            "broad_invariant_families",
            "strict_clusters",
            "rounds",
            "supplemental_security",
            "classification",
            "limitations",
        },
        set(),
        "current-case normalization",
    )
    if current["schema_version"] != "review-churn-current-case.v1":
        raise ReviewChurnValidationError("unsupported current-case schema")
    for field in ("captured_at", "run_id", "subject"):
        if not isinstance(current[field], str) or not current[field]:
            raise ReviewChurnValidationError(f"current-case {field} must be non-empty")

    digests = current["source_digests"]
    if not isinstance(digests, dict):
        raise ReviewChurnValidationError("current-case source_digests must be an object")
    required_digest_keys = {
        *(f"adversarial_round_{index}" for index in range(1, 7)),
        "security_round_1",
        "security_round_2",
    }
    _require_exact_fields(digests, required_digest_keys, set(), "current-case source_digests")
    if any(not isinstance(value, str) or len(value) != 64 for value in digests.values()):
        raise ReviewChurnValidationError("current-case source digest is invalid")
    if source_digests.keys() != required_digest_keys:
        raise ReviewChurnValidationError(
            "current-case source digests lack declared source evidence"
        )
    for key, digest in source_digests.items():
        if digests.get(key) != digest:
            raise ReviewChurnValidationError(f"current-case source digest disagrees: {key}")

    families = current["broad_invariant_families"]
    if not isinstance(families, list):
        raise ReviewChurnValidationError("current-case families must be a list")
    family_ids: set[str] = set()
    family_cluster_ids: set[str] = set()
    for family in families:
        if not isinstance(family, dict):
            raise ReviewChurnValidationError("current-case family must be an object")
        _require_exact_fields(
            family,
            {"id", "fingerprint", "strict_clusters"},
            set(),
            "current-case family",
        )
        family_id = family["id"]
        clusters = family["strict_clusters"]
        if (
            not isinstance(family_id, str)
            or family_id in family_ids
            or not isinstance(family["fingerprint"], str)
            or not isinstance(clusters, list)
            or not clusters
            or any(not isinstance(cluster, str) for cluster in clusters)
        ):
            raise ReviewChurnValidationError("current-case family is invalid")
        family_ids.add(family_id)
        family_cluster_ids.update(clusters)

    clusters = current["strict_clusters"]
    if not isinstance(clusters, list):
        raise ReviewChurnValidationError("current-case strict_clusters must be a list")
    cluster_ids: set[str] = set()
    for cluster in clusters:
        if not isinstance(cluster, dict):
            raise ReviewChurnValidationError("current-case cluster must be an object")
        _require_exact_fields(
            cluster,
            {"id", "first_round", "fingerprint"},
            set(),
            "current-case cluster",
        )
        cluster_id = cluster["id"]
        if (
            not isinstance(cluster_id, str)
            or cluster_id in cluster_ids
            or not isinstance(cluster["fingerprint"], str)
        ):
            raise ReviewChurnValidationError("current-case cluster is invalid")
        _require_int(cluster, "first_round")
        cluster_ids.add(cluster_id)
    if cluster_ids != family_cluster_ids:
        raise ReviewChurnValidationError("current-case family-to-cluster coverage is incomplete")

    rounds = current["rounds"]
    summary_rounds = summary["rounds"]
    if not isinstance(rounds, list) or len(rounds) != len(summary_rounds):
        raise ReviewChurnValidationError("current-case round count disagrees with summary")
    relation_map = {
        "initial_new": "initial_new",
        "repeated": "repeated",
        "same_invariant_distinct": "same_invariant_distinct",
        "new": "later_new",
        "indeterminate": "indeterminate",
    }
    total_findings = 0
    repair_origin = 0
    for index, (round_record, summary_round) in enumerate(
        zip(rounds, summary_rounds, strict=True), start=1
    ):
        if not isinstance(round_record, dict):
            raise ReviewChurnValidationError("current-case round must be an object")
        _require_exact_fields(
            round_record,
            {"round", "verdict", "findings"},
            set(),
            f"current-case round {index}",
        )
        findings = round_record["findings"]
        if round_record["round"] != index or not isinstance(round_record["verdict"], str):
            raise ReviewChurnValidationError("current-case round identity is invalid")
        if not isinstance(findings, list) or len(findings) != summary_round["raw"]:
            raise ReviewChurnValidationError(
                f"current-case round {index} finding count disagrees with summary"
            )
        observed_relations = dict.fromkeys(RELATION_FIELDS, 0)
        for finding in findings:
            if not isinstance(finding, dict):
                raise ReviewChurnValidationError("current-case finding must be an object")
            _require_exact_fields(
                finding,
                {"id", "severity", "cluster", "relation", "origin", "disposition"},
                set(),
                "current-case finding",
            )
            if finding["cluster"] not in cluster_ids or finding["relation"] not in relation_map:
                raise ReviewChurnValidationError(
                    "current-case finding relation or cluster is invalid"
                )
            observed_relations[relation_map[finding["relation"]]] += 1
            if finding["origin"] == "prior_round_repair":
                repair_origin += 1
        for field, observed in observed_relations.items():
            if summary_round[field] != observed:
                raise ReviewChurnValidationError(
                    f"current-case round {index} {field} disagrees with summary"
                )
        total_findings += len(findings)

    classification = current["classification"]
    if not isinstance(classification, dict):
        raise ReviewChurnValidationError("current-case classification must be an object")
    _require_exact_fields(
        classification,
        {
            "independent_classifiers",
            "agreement",
            "raw_findings",
            "strict_clusters",
            "broad_invariant_families",
            "later_relations",
            "proven_repair_origin",
        },
        set(),
        "current-case classification",
    )
    if (
        _require_int(classification, "raw_findings") != total_findings
        or _require_int(classification, "strict_clusters") != len(cluster_ids)
        or _require_int(classification, "broad_invariant_families") != len(family_ids)
        or _require_int(classification, "proven_repair_origin") != repair_origin
        or total_findings != summary["raw_findings"]
        or len(cluster_ids) != summary["strict_clusters"]
        or len(family_ids) != summary["broad_invariant_families"]
        or repair_origin != summary["proven_repair_origin"]
    ):
        raise ReviewChurnValidationError("current-case classification disagrees with summary")
    expected_later = {
        "repeated": sum(round_record["repeated"] for round_record in summary_rounds[1:]),
        "same_invariant_distinct": sum(
            round_record["same_invariant_distinct"] for round_record in summary_rounds[1:]
        ),
        "new": sum(round_record["later_new"] for round_record in summary_rounds[1:]),
        "indeterminate": sum(
            round_record["indeterminate"] for round_record in summary_rounds[1:]
        ),
    }
    if classification["later_relations"] != expected_later:
        raise ReviewChurnValidationError("current-case later relations disagree with summary")
    if (
        _require_int(classification, "independent_classifiers") != 2
        or classification["agreement"]
        != "exact on counts, clusters, later relations, and causal labels"
    ):
        raise ReviewChurnValidationError(
            "current-case independent-classification evidence is invalid"
        )
    if not isinstance(current["limitations"], list) or any(
        not isinstance(item, str) or not item for item in current["limitations"]
    ):
        raise ReviewChurnValidationError("current-case limitations must be strings")
    supplemental = current["supplemental_security"]
    if not isinstance(supplemental, dict):
        raise ReviewChurnValidationError("current-case supplemental_security must be an object")
    _require_exact_fields(
        supplemental,
        {"round_1_clusters", "round_1_sustained", "round_2_verdict"},
        set(),
        "current-case supplemental_security",
    )
    security_clusters = supplemental["round_1_clusters"]
    if (
        not isinstance(security_clusters, list)
        or _require_int(supplemental, "round_1_sustained") != len(security_clusters)
        or not isinstance(supplemental["round_2_verdict"], str)
    ):
        raise ReviewChurnValidationError("current-case supplemental security is invalid")
    summary_security = summary.get("supplemental_security")
    if not isinstance(summary_security, dict):
        raise ReviewChurnValidationError("current-case summary lacks supplemental security")
    if (
        _require_int(summary_security, "rounds") != 2
        or _require_int(summary_security, "raw_findings") != len(security_clusters)
        or summary_security.get("clean_final_round") is not True
        or supplemental["round_2_verdict"] != "clean"
    ):
        raise ReviewChurnValidationError(
            "current-case supplemental security disagrees with summary"
        )


def validate_results(data: dict[str, Any], root: Path) -> dict[str, int | float]:
    """Validate source integrity and recompute the Tier A aggregate."""
    _require_exact_fields(
        data,
        {
            "schema_version",
            "frozen_at",
            "scope",
            "tier_a_cases",
            "tier_a_aggregate",
            "tier_b_cases",
            "repository_aggregate_observations",
            "prior_experiment_sources",
            "unavailable_measures",
        },
        set(),
        "results",
    )
    if data.get("schema_version") != "review-churn-results.v1":
        raise ReviewChurnValidationError("unsupported review-churn schema")
    if not isinstance(data.get("frozen_at"), str) or not isinstance(data.get("scope"), str):
        raise ReviewChurnValidationError("frozen_at and scope must be strings")
    cases = data.get("tier_a_cases")
    if not isinstance(cases, list) or not cases:
        raise ReviewChurnValidationError("tier_a_cases must be a non-empty list")

    aggregate = {
        "cases": len(cases),
        "raw_findings": 0,
        "initial_round_findings": 0,
        "later_round_findings": 0,
        "within_case_strict_clusters": 0,
        "within_case_broad_invariant_families": 0,
        "repeated": 0,
        "same_invariant_distinct": 0,
        "new": 0,
        "indeterminate": 0,
        "proven_repair_origin": 0,
        "nonclean_report_words": 0,
        "later_report_words": 0,
        "nonclean_report_bytes": 0,
        "later_report_bytes": 0,
    }

    seen_ids: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ReviewChurnValidationError("each Tier A case must be an object")
        _require_exact_fields(
            case,
            {
                "id",
                "source_retention",
                "rounds",
                "raw_findings",
                "strict_clusters",
                "broad_invariant_families",
                "proven_repair_origin",
                "classification",
                "sources",
            },
            {
                "possible_repair_origin_upper_bound",
                "supplemental_security",
                "dispositions",
            },
            "Tier A case",
        )
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen_ids:
            raise ReviewChurnValidationError(f"invalid or duplicate case id: {case_id!r}")
        seen_ids.add(case_id)
        if case.get("source_retention") not in {"durable", "session-local-normalized"}:
            raise ReviewChurnValidationError(f"{case_id}: invalid source_retention")
        if not isinstance(case.get("classification"), str) or not case["classification"]:
            raise ReviewChurnValidationError(f"{case_id}: classification must be non-empty")
        rounds = case.get("rounds")
        if not isinstance(rounds, list) or not rounds:
            raise ReviewChurnValidationError(f"{case_id}: rounds must be non-empty")

        case_raw = 0
        for index, round_record in enumerate(rounds, start=1):
            if not isinstance(round_record, dict) or round_record.get("round") != index:
                raise ReviewChurnValidationError(f"{case_id}: rounds must be contiguous from 1")
            _require_exact_fields(
                round_record,
                {
                    "round",
                    "raw",
                    "initial_new",
                    "repeated",
                    "same_invariant_distinct",
                    "later_new",
                    "indeterminate",
                    "proven_repair_origin",
                    "words",
                    "bytes",
                },
                {"clean"},
                f"{case_id} round {index}",
            )
            raw = _require_int(round_record, "raw")
            relation_total = sum(_require_int(round_record, field) for field in RELATION_FIELDS)
            if raw != relation_total and not (raw == 0 and round_record.get("clean") is True):
                raise ReviewChurnValidationError(
                    f"{case_id} round {index}: relation counts {relation_total} != raw {raw}"
                )
            repair_origin = _require_int(round_record, "proven_repair_origin")
            if repair_origin > raw:
                raise ReviewChurnValidationError(
                    f"{case_id} round {index}: repair-origin count exceeds raw findings"
                )
            case_raw += raw
            aggregate["proven_repair_origin"] += repair_origin
            if raw:
                aggregate["nonclean_report_words"] += _require_int(round_record, "words")
                aggregate["nonclean_report_bytes"] += _require_int(round_record, "bytes")
            if index == 1:
                aggregate["initial_round_findings"] += raw
            else:
                aggregate["later_round_findings"] += raw
                aggregate["repeated"] += _require_int(round_record, "repeated")
                aggregate["same_invariant_distinct"] += _require_int(
                    round_record, "same_invariant_distinct"
                )
                aggregate["new"] += _require_int(round_record, "later_new")
                aggregate["indeterminate"] += _require_int(round_record, "indeterminate")
                if raw:
                    aggregate["later_report_words"] += _require_int(round_record, "words")
                    aggregate["later_report_bytes"] += _require_int(round_record, "bytes")

        source_rounds: set[int] = set()

        if case_raw != _require_int(case, "raw_findings"):
            raise ReviewChurnValidationError(f"{case_id}: round total does not match raw_findings")
        aggregate["raw_findings"] += case_raw
        aggregate["within_case_strict_clusters"] += _require_int(case, "strict_clusters")
        aggregate["within_case_broad_invariant_families"] += _require_int(
            case, "broad_invariant_families"
        )
        sources = case.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ReviewChurnValidationError(f"{case_id}: sources must be non-empty")
        current_case_path: Path | None = None
        current_source_digests: dict[str, str] = {}
        for source in sources:
            if not isinstance(source, dict):
                raise ReviewChurnValidationError(f"{case_id}: source must be an object")
            _validate_source(root, source, require_rounds=True)
            source_rounds.update(source["rounds"])
            source_path = source["path"]
            if source_path.endswith("review-churn-current-case.json"):
                current_case_path = root / source_path
            for round_index in range(1, 7):
                if source_path.endswith(
                    f"/{round_index}-pre-execute-adversarial-reviewer-raw.md"
                ):
                    current_source_digests[f"adversarial_round_{round_index}"] = source[
                        "sha256"
                    ]
            for round_index in range(1, 3):
                if source_path.endswith(
                    f"/{round_index}-pre-execute-security-reviewer-raw.md"
                ):
                    current_source_digests[f"security_round_{round_index}"] = source["sha256"]
        expected_rounds = set(range(1, len(rounds) + 1))
        if not expected_rounds.issubset(source_rounds):
            missing_source_rounds = sorted(expected_rounds - source_rounds)
            raise ReviewChurnValidationError(
                f"{case_id}: rounds lack source bindings: {missing_source_rounds}"
            )
        if case_id == "plan-evolution-current":
            if current_case_path is None:
                raise ReviewChurnValidationError(
                    "plan-evolution-current lacks its durable normalized source"
                )
            validate_current_case(
                _load_strict_json(current_case_path), case, current_source_digests
            )
        if "possible_repair_origin_upper_bound" in case:
            _require_int(case, "possible_repair_origin_upper_bound")
        if "supplemental_security" in case:
            supplemental = case["supplemental_security"]
            if not isinstance(supplemental, dict):
                raise ReviewChurnValidationError(
                    f"{case_id}: supplemental_security must be an object"
                )
            _require_exact_fields(
                supplemental,
                {"rounds", "raw_findings", "clean_final_round"},
                set(),
                f"{case_id} supplemental_security",
            )
            _require_int(supplemental, "rounds")
            _require_int(supplemental, "raw_findings")
            if not isinstance(supplemental["clean_final_round"], bool):
                raise ReviewChurnValidationError(
                    f"{case_id}: clean_final_round must be boolean"
                )
        if "dispositions" in case:
            dispositions = case["dispositions"]
            if not isinstance(dispositions, dict):
                raise ReviewChurnValidationError(f"{case_id}: dispositions must be an object")
            _require_exact_fields(
                dispositions,
                {"sustained_resolved", "refuted"},
                set(),
                f"{case_id} dispositions",
            )
            _require_int(dispositions, "sustained_resolved")
            _require_int(dispositions, "refuted")

    later_total = (
        aggregate["repeated"]
        + aggregate["same_invariant_distinct"]
        + aggregate["new"]
        + aggregate["indeterminate"]
    )
    if later_total != aggregate["later_round_findings"]:
        raise ReviewChurnValidationError("aggregate later relation counts do not balance")
    recurrence = aggregate["repeated"] + aggregate["same_invariant_distinct"]
    recurrence_share = recurrence / aggregate["later_round_findings"]

    expected = data.get("tier_a_aggregate")
    if not isinstance(expected, dict):
        raise ReviewChurnValidationError("tier_a_aggregate must be an object")
    _require_exact_fields(
        expected,
        {
            "cases",
            "raw_findings",
            "initial_round_findings",
            "later_round_findings",
            "within_case_strict_clusters",
            "within_case_broad_invariant_families",
            "later_relations",
            "later_recurrence_family_findings",
            "later_recurrence_family_share",
            "proven_repair_origin",
            "nonclean_report_words",
            "later_report_words",
            "nonclean_report_bytes",
            "later_report_bytes",
        },
        set(),
        "tier_a_aggregate",
    )
    exact_fields = {
        "cases": aggregate["cases"],
        "raw_findings": aggregate["raw_findings"],
        "initial_round_findings": aggregate["initial_round_findings"],
        "later_round_findings": aggregate["later_round_findings"],
        "within_case_strict_clusters": aggregate["within_case_strict_clusters"],
        "within_case_broad_invariant_families": aggregate[
            "within_case_broad_invariant_families"
        ],
        "later_recurrence_family_findings": recurrence,
        "proven_repair_origin": aggregate["proven_repair_origin"],
        "nonclean_report_words": aggregate["nonclean_report_words"],
        "later_report_words": aggregate["later_report_words"],
        "nonclean_report_bytes": aggregate["nonclean_report_bytes"],
        "later_report_bytes": aggregate["later_report_bytes"],
    }
    for field, value in exact_fields.items():
        if _require_int(expected, field) != value:
            raise ReviewChurnValidationError(
                f"tier_a_aggregate.{field} is {expected.get(field)!r}, expected {value}"
            )
    expected_relations = expected.get("later_relations")
    if not isinstance(expected_relations, dict):
        raise ReviewChurnValidationError("tier_a_aggregate.later_relations must be an object")
    _require_exact_fields(
        expected_relations,
        {"repeated", "same_invariant_distinct", "new", "indeterminate"},
        set(),
        "tier_a_aggregate.later_relations",
    )
    for field in ("repeated", "same_invariant_distinct", "new", "indeterminate"):
        _require_int(expected_relations, field)
    actual_relations = {
        "repeated": aggregate["repeated"],
        "same_invariant_distinct": aggregate["same_invariant_distinct"],
        "new": aggregate["new"],
        "indeterminate": aggregate["indeterminate"],
    }
    if expected_relations != actual_relations:
        raise ReviewChurnValidationError("tier_a_aggregate.later_relations does not match cases")
    share = expected.get("later_recurrence_family_share")
    if not isinstance(share, int | float) or isinstance(share, bool) or not math.isfinite(share):
        raise ReviewChurnValidationError("later recurrence-family share must be finite")
    if abs(float(share) - recurrence_share) > 0.0001:
        raise ReviewChurnValidationError("later recurrence-family share does not match cases")

    tier_b_cases = data["tier_b_cases"]
    if not isinstance(tier_b_cases, list) or len(tier_b_cases) != 2:
        raise ReviewChurnValidationError("tier_b_cases must contain the two frozen cases")
    tier_b_fields = {
        "install-to-ship-walkthrough": {
            "id",
            "trajectory",
            "raw_findings",
            "proven_repair_origin_in_rounds_2_3",
            "source",
        },
        "occasioning-nonconvergence-loop": {
            "id",
            "rounds",
            "sustained_findings",
            "proven_repair_origin",
            "findings_in_two_families",
            "last_eight_round_findings",
            "source",
        },
    }
    seen_tier_b: set[str] = set()
    for case in tier_b_cases:
        if not isinstance(case, dict) or case.get("id") not in tier_b_fields:
            raise ReviewChurnValidationError("invalid Tier B case")
        tier_b_id = case["id"]
        if tier_b_id in seen_tier_b:
            raise ReviewChurnValidationError(f"duplicate Tier B case: {tier_b_id}")
        seen_tier_b.add(tier_b_id)
        _require_exact_fields(case, tier_b_fields[tier_b_id], set(), f"Tier B {tier_b_id}")
        source = case["source"]
        if not isinstance(source, dict):
            raise ReviewChurnValidationError(f"Tier B {tier_b_id}: source must be an object")
        _validate_source(root, source)
        if tier_b_id == "install-to-ship-walkthrough":
            trajectory = case["trajectory"]
            if (
                not isinstance(trajectory, list)
                or not trajectory
                or any(
                    isinstance(value, bool) or not isinstance(value, int) or value < 0
                    for value in trajectory
                )
            ):
                raise ReviewChurnValidationError("install-to-ship trajectory is invalid")
            if sum(trajectory) != _require_int(case, "raw_findings"):
                raise ReviewChurnValidationError("install-to-ship trajectory does not balance")
            if _require_int(case, "proven_repair_origin_in_rounds_2_3") > sum(
                trajectory[1:3]
            ):
                raise ReviewChurnValidationError("install-to-ship repair-origin count is invalid")
        else:
            for field in (
                "rounds",
                "sustained_findings",
                "proven_repair_origin",
                "findings_in_two_families",
                "last_eight_round_findings",
            ):
                _require_int(case, field)
    repository_observations = data["repository_aggregate_observations"]
    if not isinstance(repository_observations, dict):
        raise ReviewChurnValidationError("repository_aggregate_observations must be an object")
    _require_exact_fields(
        repository_observations,
        {
            "session_transcripts",
            "merged_pull_requests",
            "spec_plan_pairs",
            "numbered_acceptance_criteria",
            "runs_with_review_artifacts",
            "runs_exceeding_five_review_ordinals",
            "plan_nonblank_line_unconsumed_share",
            "full_mode_spec_plan_only_finding_share",
            "light_mode_record_only_finding_share",
            "goal_vs_spec_plan_repair_rate_after_size_control",
            "full_mode_acceptance_criterion_to_code_findings",
            "source",
        },
        set(),
        "repository_aggregate_observations",
    )
    repository_source = repository_observations["source"]
    if not isinstance(repository_source, dict):
        raise ReviewChurnValidationError("repository aggregate source must be an object")
    _validate_source(root, repository_source)
    for field in (
        "session_transcripts",
        "merged_pull_requests",
        "spec_plan_pairs",
        "numbered_acceptance_criteria",
        "runs_with_review_artifacts",
        "runs_exceeding_five_review_ordinals",
        "full_mode_acceptance_criterion_to_code_findings",
    ):
        _require_int(repository_observations, field)
    for field in (
        "plan_nonblank_line_unconsumed_share",
        "full_mode_spec_plan_only_finding_share",
        "light_mode_record_only_finding_share",
    ):
        value = repository_observations[field]
        if (
            not isinstance(value, int | float)
            or isinstance(value, bool)
            or not math.isfinite(value)
            or not 0 <= value <= 1
        ):
            raise ReviewChurnValidationError(f"repository aggregate {field} is invalid")
    goal_comparison = repository_observations[
        "goal_vs_spec_plan_repair_rate_after_size_control"
    ]
    if not isinstance(goal_comparison, str):
        raise ReviewChurnValidationError("goal-versus-spec/plan result must be a string")
    prior_sources = data["prior_experiment_sources"]
    if not isinstance(prior_sources, list) or len(prior_sources) != 2:
        raise ReviewChurnValidationError("prior_experiment_sources must contain two sources")
    for source in prior_sources:
        if not isinstance(source, dict):
            raise ReviewChurnValidationError("prior experiment source must be an object")
        _validate_source(root, source)
    unavailable = data["unavailable_measures"]
    if not isinstance(unavailable, list) or not unavailable or any(
        not isinstance(item, str) or not item for item in unavailable
    ):
        raise ReviewChurnValidationError("unavailable_measures must be non-empty strings")
    return {**aggregate, "later_recurrence_family_share": recurrence_share}


def load_and_validate(results_path: Path, root: Path) -> dict[str, int | float]:
    """Load one results file and validate it against repository sources."""
    return validate_results(_load_strict_json(results_path), root)


def main() -> int:
    """Validate the frozen corpus and print its recomputed aggregate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    summary = load_and_validate(args.root / args.results, args.root)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
