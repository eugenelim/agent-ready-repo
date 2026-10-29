"""Preservation records through the shipped acceptance evaluator.

Proves that the Slice 1 acceptance contracts represent and decide the six
preservation properties a shared-substrate change can disturb, without a
grounding-specific schema or authority path. Valid samples, rejections,
single-change mutations, and the evaluator's observed limits all run through
the shipped validators, evidence store, and evaluator.

Spec: docs/specs/grounding-preservation-contract-proof/spec.md
"""

from __future__ import annotations

import copy
import importlib.util
import os
import stat
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchors ──────────────────────────────────────────────────────────────

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module via importlib."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = prev


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py loaded by path."""
    return _load_module("core_work_loop_acc_preservation", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def es() -> ModuleType:
    """_evidence_store.py loaded by path."""
    return _load_module("core_work_loop_es_preservation", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_module("core_work_loop_sc_preservation", SCRIPTS / "_security_capability.py")


# ── Samples ───────────────────────────────────────────────────────────────────

CURRENT_FP = "fp-subject-current"
EARLIER_FP = "fp-subject-earlier"
OTHER_SUBJECT_FP = "fp-other-subject"
REVIEW_FAILURE = "supported-review-failure"


@dataclass(frozen=True)
class Sample:
    """One preservation property: its identity, observation type, terms, and passing outcome."""

    property_id: str
    observation_type: str
    terms: tuple[str, ...]
    passing_outcome: str


SAMPLES: tuple[Sample, ...] = (
    Sample(
        "ordinary-calls-no-synthetic-targets", "test-result", ("differential-resolver",), "pass"
    ),
    Sample(
        "default-search-excludes-synthetic", "test-result", ("default-and-explicit-query",), "pass"
    ),
    Sample(
        "full-incremental-semantic-equivalence", "test-result", ("equivalence-harness",), "pass"
    ),
    # Bounded work: a goal-based check projects to command-result.
    Sample(
        "one-file-edit-invalidation-budget",
        "command-result",
        ("invalidation-count",),
        "within-budget",
    ),
    Sample(
        "added-values-lifecycle", "test-result", ("create", "update", "delete", "rebuild"), "pass"
    ),
    Sample(
        "supported-rust-consumers-compile", "command-result", ("downstream-compile",), "exit-0"
    ),
)
SAMPLE_IDS = [s.property_id for s in SAMPLES]
ORDINARY_CALLS = SAMPLES[0]
BOUNDED_WORK = SAMPLES[3]
LIFECYCLE = SAMPLES[4]


def _property(sample: Sample, *, contradiction: str = REVIEW_FAILURE) -> dict:
    """Build the acceptance-property.v1 record for *sample*."""
    return {
        "schema_version": 1,
        "property_id": sample.property_id,
        "spec_ref": "docs/specs/shared-substrate-change/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {
            "paths_or_artifacts": ["src/model/"],
            "fingerprint_algorithm": "sha256",
        },
        "required_observations": [
            {
                "term": term,
                "observation_type": sample.observation_type,
                "producer_class": "ci-runner",
                "outcomes": [sample.passing_outcome],
            }
            for term in sample.terms
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": contradiction},
        "policy_version": "v1",
    }


def _receipt(
    sample: Sample,
    term: str,
    *,
    receipt_id: str | None = None,
    fingerprint: str = CURRENT_FP,
    outcome: str | None = None,
    observation_type: str | None = None,
    criterion_ref: str | None = None,
) -> dict:
    """Build an evidence-receipt.v1 record for one term of *sample*."""
    return {
        "schema_version": 1,
        "receipt_id": receipt_id or f"{sample.property_id}:{term}",
        "acceptance_fingerprint": fingerprint,
        "lineage": {"criterion_ref": criterion_ref or sample.property_id},
        "selector": {"term": term},
        "freshness_mode": "exact-subject",
        "observation": {"type": observation_type or sample.observation_type},
        "outcome": outcome or sample.passing_outcome,
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _receipts(sample: Sample, **overrides: str) -> list[dict]:
    """One passing receipt per required term of *sample*."""
    return [_receipt(sample, term, **overrides) for term in sample.terms]


def _review_failure(sample: Sample) -> dict:
    """A fresh supported-review-failure receipt against *sample*."""
    return {
        **_receipt(sample, REVIEW_FAILURE, outcome="sustained"),
        "observation": {"type": "review-failure"},
        "producer": {"class": "reviewer", "identity": "reviewer-generic"},
    }


# ── Store helpers ─────────────────────────────────────────────────────────────


def _null_sink(event: object) -> None:
    """Audit sink that accepts and drops every event."""


def _store_verdict(
    es: ModuleType,
    sc: ModuleType,
    acc: ModuleType,
    log_path: Path,
    prop: dict,
    receipts: list[dict],
    *,
    current_fp: str = CURRENT_FP,
    adapter: str = "sequential-reference",
) -> dict:
    """Append *receipts* through the evidence store and return the store verdict for *prop*."""
    store = es.EvidenceStore(log_path)
    store.open()
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    for index, receipt in enumerate(receipts):
        store.append_receipt(
            receipt,
            transaction_id=f"tx-{index:03d}",
            issuer=issuer,
            grant=grant,
            audit_sink=_null_sink,
        )
    [verdict] = store.evaluate_verdicts([prop], current_fp, acc, adapter=adapter)
    return verdict


def _direct_verdict(acc: ModuleType, prop: dict, receipts: list[dict]) -> dict:
    """Evaluate *prop* straight through evaluate_verdict, bypassing store routing."""
    return acc.evaluate_verdict(
        property_record=prop,
        receipts=receipts,
        current_acceptance_fingerprint=CURRENT_FP,
        adapter="sequential-reference",
    )


def _ids(receipts: list[dict]) -> set[str]:
    return {r["receipt_id"] for r in receipts}


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0001: valid samples
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_valid_sample_is_supported_on_every_adapter(
    sample: Sample, acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0001: each sample passes the shipped validators and is supported."""
    prop = _property(sample)
    receipts = _receipts(sample)

    assert acc.validate_property_dict(prop) == (True, "ok")
    for receipt in receipts:
        assert es.validate_receipt_dict(receipt) == (True, "ok")

    for index, adapter in enumerate(acc.SUPPORTED_ADAPTERS):
        verdict = _store_verdict(
            es, sc, acc, tmp_path / f"evidence-{index}.log", prop, receipts, adapter=adapter
        )
        assert verdict["verdict"] == "supported", adapter
        assert acc.validate_verdict_dict(verdict) == (True, "ok")


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0002 to AC-0006: rejections
# ═══════════════════════════════════════════════════════════════════════════════


def test_missing_required_term_is_insufficient(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0002: the lifecycle sample without its delete receipt is insufficient."""
    receipts = [r for r in _receipts(LIFECYCLE) if r["selector"]["term"] != "delete"]
    assert len(receipts) == 3

    verdict = _store_verdict(
        es, sc, acc, tmp_path / "evidence.log", _property(LIFECYCLE), receipts
    )

    assert verdict["verdict"] == "insufficient"


def test_receipt_for_another_criterion_is_routed_away(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0003: a passing receipt bound to a different property never reaches this one."""
    receipts = _receipts(ORDINARY_CALLS, criterion_ref=SAMPLES[1].property_id)

    verdict = _store_verdict(
        es, sc, acc, tmp_path / "evidence.log", _property(ORDINARY_CALLS), receipts
    )

    assert verdict["verdict"] == "insufficient"
    assert verdict["receipt_refs"] == []


def test_receipt_for_another_subject_is_not_fresh(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0003: a passing receipt bound to another subject's fingerprint is not fresh."""
    receipts = _receipts(ORDINARY_CALLS, fingerprint=OTHER_SUBJECT_FP)

    verdict = _store_verdict(
        es, sc, acc, tmp_path / "evidence.log", _property(ORDINARY_CALLS), receipts
    )

    assert verdict["verdict"] == "insufficient"
    assert verdict["receipt_refs"] == []


@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_stale_receipts_are_insufficient(
    sample: Sample, acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0004: receipts from an earlier fingerprint of the same subject are stale."""
    receipts = _receipts(sample, fingerprint=EARLIER_FP)

    verdict = _store_verdict(es, sc, acc, tmp_path / "evidence.log", _property(sample), receipts)

    assert verdict["verdict"] == "insufficient"
    assert verdict["receipt_refs"] == []


def test_unsupported_outcome_is_fresh_but_insufficient(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0005: an unlisted outcome leaves a fresh receipt that satisfies nothing."""
    receipts = _receipts(ORDINARY_CALLS, outcome="unknown")

    verdict = _store_verdict(
        es, sc, acc, tmp_path / "evidence.log", _property(ORDINARY_CALLS), receipts
    )

    assert verdict["verdict"] == "insufficient"
    assert set(verdict["receipt_refs"]) == _ids(receipts)


def test_review_failure_contradicts_a_satisfied_property(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0006: a fresh supported-review-failure outranks a satisfying receipt."""
    receipts = [*_receipts(ORDINARY_CALLS), _review_failure(ORDINARY_CALLS)]

    verdict = _store_verdict(
        es, sc, acc, tmp_path / "evidence.log", _property(ORDINARY_CALLS), receipts
    )

    assert verdict["verdict"] == "contradicted"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0007: one change at a time moves each valid sample off `supported`
# ═══════════════════════════════════════════════════════════════════════════════

# Each mutation takes (property, receipts) and returns (property, receipts,
# current fingerprint, expected verdict, expected receipt_refs).
Mutated = tuple[dict, list[dict], str, str, set[str]]


def _mutate_outcome(prop: dict, receipts: list[dict]) -> Mutated:
    receipts[0]["outcome"] = "unknown"
    return prop, receipts, CURRENT_FP, "insufficient", _ids(receipts)


def _mutate_term(prop: dict, receipts: list[dict]) -> Mutated:
    receipts[0]["selector"]["term"] = "unnamed-term"
    return prop, receipts, CURRENT_FP, "insufficient", _ids(receipts)


def _mutate_current_fingerprint(prop: dict, receipts: list[dict]) -> Mutated:
    return prop, receipts, "fp-subject-changed", "insufficient", set()


def _mutate_authority(prop: dict, receipts: list[dict]) -> Mutated:
    prop["authority_ref"] = ""
    return prop, receipts, CURRENT_FP, "unapproved", set()


def _add_review_failure(prop: dict, receipts: list[dict]) -> Mutated:
    sample = next(s for s in SAMPLES if s.property_id == prop["property_id"])
    receipts.append(_review_failure(sample))
    return prop, receipts, CURRENT_FP, "contradicted", _ids(receipts)


MUTATIONS: dict[str, Callable[[dict, list[dict]], Mutated]] = {
    "outcome-unlisted": _mutate_outcome,
    "term-unnamed": _mutate_term,
    "current-fingerprint-changed": _mutate_current_fingerprint,
    "authority-emptied": _mutate_authority,
    "review-failure-added": _add_review_failure,
}


@pytest.mark.parametrize("mutation", list(MUTATIONS), ids=list(MUTATIONS))
@pytest.mark.parametrize("sample", SAMPLES, ids=SAMPLE_IDS)
def test_single_change_moves_sample_off_supported(
    sample: Sample,
    mutation: str,
    acc: ModuleType,
    es: ModuleType,
    sc: ModuleType,
    tmp_path: Path,
) -> None:
    """AC-0007: each change alone yields its named verdict and receipt_refs."""
    baseline = _store_verdict(
        es, sc, acc, tmp_path / "baseline.log", _property(sample), _receipts(sample)
    )
    assert baseline["verdict"] == "supported"

    prop, receipts, current_fp, expected, expected_refs = MUTATIONS[mutation](
        copy.deepcopy(_property(sample)), copy.deepcopy(_receipts(sample))
    )
    verdict = _store_verdict(
        es, sc, acc, tmp_path / "mutated.log", prop, receipts, current_fp=current_fp
    )

    assert verdict["verdict"] == expected
    assert set(verdict["receipt_refs"]) == expected_refs


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0008: bounded work
# ═══════════════════════════════════════════════════════════════════════════════


def test_bounded_work_uses_command_result_and_fails_over_budget(
    acc: ModuleType, es: ModuleType, sc: ModuleType, tmp_path: Path
) -> None:
    """AC-0008: the invalidation budget is a command-result term with within-budget."""
    prop = _property(BOUNDED_WORK)
    [observation] = prop["required_observations"]
    assert observation["observation_type"] == "command-result"
    assert observation["outcomes"] == ["within-budget"]

    verdict = _store_verdict(
        es,
        sc,
        acc,
        tmp_path / "evidence.log",
        prop,
        _receipts(BOUNDED_WORK, outcome="over-budget"),
    )

    assert verdict["verdict"] == "insufficient"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0009: observed limits — pinned so an enforcing change fails here first
# ═══════════════════════════════════════════════════════════════════════════════


class TestObservedLimits:
    """AC-0009: what evaluate_verdict does not read today."""

    def test_producer_class_is_not_read(self, acc: ModuleType) -> None:
        receipts = _receipts(ORDINARY_CALLS)
        receipts[0]["producer"] = {"class": "unlisted-producer", "identity": "producer-generic"}
        verdict = _direct_verdict(acc, _property(ORDINARY_CALLS), receipts)
        assert verdict["verdict"] == "supported"

    def test_observation_type_is_not_read(self, acc: ModuleType) -> None:
        receipts = _receipts(ORDINARY_CALLS, observation_type="manual-observation")
        verdict = _direct_verdict(acc, _property(ORDINARY_CALLS), receipts)
        assert verdict["verdict"] == "supported"

    def test_count_is_not_read(self, acc: ModuleType) -> None:
        prop = _property(ORDINARY_CALLS)
        prop["required_observations"][0]["count"] = 2
        assert acc.validate_property_dict(prop) == (True, "ok")
        verdict = _direct_verdict(acc, prop, _receipts(ORDINARY_CALLS))
        assert verdict["verdict"] == "supported"

    def test_criterion_ref_is_not_read(self, acc: ModuleType) -> None:
        receipts = _receipts(ORDINARY_CALLS, criterion_ref=SAMPLES[1].property_id)
        verdict = _direct_verdict(acc, _property(ORDINARY_CALLS), receipts)
        assert verdict["verdict"] == "supported"

    def test_failing_required_term_is_insufficient_not_contradicted(self, acc: ModuleType) -> None:
        receipts = _receipts(ORDINARY_CALLS, outcome="fail")
        verdict = _direct_verdict(acc, _property(ORDINARY_CALLS), receipts)
        assert verdict["verdict"] == "insufficient"

    @pytest.mark.parametrize("expression", ["none", "regression-detected"])
    def test_reserved_term_counts_only_when_named(self, acc: ModuleType, expression: str) -> None:
        prop = _property(ORDINARY_CALLS, contradiction=expression)
        assert acc.validate_property_dict(prop) == (True, "ok")
        receipts = [*_receipts(ORDINARY_CALLS), _review_failure(ORDINARY_CALLS)]
        verdict = _direct_verdict(acc, prop, receipts)
        assert verdict["verdict"] == "supported"
