"""Construction tests for the proof-by-run predicate.

Mode: TDD (proof-by-run-evidence plan T1). The suite loads the shipped
work-loop script by literal path and calls the predicate directly.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)
COMMIT = "a" * 40
OTHER_COMMIT = "b" * 40


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path for pack-boundary tests."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def review_assessment() -> ModuleType:
    """Load the assessment module under a unique name."""
    return _load_module(
        "review_assessment_proof_by_run", SCRIPTS / "_review_assessment.py"
    )


@pytest.fixture(scope="module")
def review_contracts() -> ModuleType:
    """Load the review contract validators."""
    return _load_module("review_contracts_proof_by_run", SCRIPTS / "_review_contracts.py")


def _review_subject() -> dict:
    """Build the current review subject."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-pbr",
        "review_subject_fingerprint": "review-subject-fp-pbr",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-pbr",
            "acceptance_fingerprint": "acceptance-fp-pbr",
        },
        "normalized_paths": ["packs/core/.apm/skills/work-loop/scripts/_review_assessment.py"],
        "normalized_statuses": ["added"],
        "review_policy_fingerprint": "review-policy-pbr",
        "lineage": {"provider": "proof-by-run-test", "projection_version": "1.0"},
    }


def _finding() -> dict:
    """Build a valid structured finding."""
    return {
        "schema_version": 1,
        "finding_id": "finding-pbr",
        "rule_ref": "AC-0001",
        "observation": "A command reproduces the failure.",
        "reachable_path": "command to failing exit",
        "actual_failure": "The command exits non-zero before the fix.",
        "affected_acceptance_criteria": ["AC-0001"],
        "evidence_refs": ["evidence:observation"],
        "material": True,
    }


def _report(subject: dict, finding: dict) -> dict:
    """Build a findings report containing one finding."""
    return {
        "schema_version": 1,
        "report_id": "report-pbr",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": "source-report-pbr",
            "producer": "synthetic-reviewer",
        },
        "findings": [copy.deepcopy(finding)],
    }


def _sha(text: str) -> str:
    """Return the SHA-256 hex digest of text."""
    return hashlib.sha256(text.encode()).hexdigest()


def _envelope(commit: str = COMMIT, exit_status: int = 1) -> dict:
    """Build a run envelope bound to a commit."""
    return {
        "command_sha256": _sha("pytest -q"),
        "exit_status": exit_status,
        "stderr_sha256": _sha("err"),
        "stdout_sha256": _sha("out"),
        "subject_commit": commit,
    }


def _call(module: ModuleType, **overrides: object) -> dict:
    """Call the predicate with a consistent fixture, applying overrides."""
    subject = _review_subject()
    report = _report(subject, _finding())
    kwargs: dict = {
        "assessment_id": "assessment-pbr",
        "report_id": report["report_id"],
        "finding_id": report["findings"][0]["finding_id"],
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "observed": "fail",
        "envelope": _envelope(),
        "current_subject_commit": COMMIT,
        "judgment_authority": "authority:controller",
    }
    kwargs.update(overrides)
    return module.proof_by_run_assessment(**kwargs)


def _digest(envelope: dict) -> str:
    """Recompute the envelope digest independently of the implementation."""
    text = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode()).hexdigest()


def test_t1_fail_is_supported_with_one_recomputable_reference(
    review_assessment: ModuleType, review_contracts: ModuleType
) -> None:
    """AC-0001: a bound fail maps to supported with one proof-run reference."""
    envelope = _envelope()
    record = _call(review_assessment, envelope=envelope)
    ok, code = review_contracts.validate_finding_assessment_dict(record)
    assert ok, code
    assert record["assessment"] == "supported"
    assert record["lineage"] == {
        "predicate_version": "proof-by-run.v1",
        "judgment_authority": "authority:controller",
    }
    assert record["evidence_refs"] == [f"proof-run:v1:{COMMIT}:fail:{_digest(envelope)}"]


def test_t1_envelope_digest_ignores_key_order_and_covers_five_fields(
    review_assessment: ModuleType,
) -> None:
    """AC-0001: the digest is canonical over exactly the five fields."""
    envelope = _envelope()
    reordered = dict(reversed(list(envelope.items())))
    ref = review_assessment.proof_run_reference("fail", reordered)
    assert ref == f"proof-run:v1:{COMMIT}:fail:{_digest(envelope)}"
    changed = review_assessment.proof_run_reference("fail", _envelope(exit_status=2))
    assert changed != ref


def test_t1_pass_is_unsupported_opinion(
    review_assessment: ModuleType, review_contracts: ModuleType
) -> None:
    """AC-0002: a bound pass maps to unsupported-opinion, never supported."""
    envelope = _envelope(exit_status=0)
    record = _call(review_assessment, observed="pass", envelope=envelope)
    ok, code = review_contracts.validate_finding_assessment_dict(record)
    assert ok, code
    assert record["assessment"] == "unsupported-opinion"
    assert record["evidence_refs"] == [f"proof-run:v1:{COMMIT}:pass:{_digest(envelope)}"]


def test_t1_stale_envelope_is_refused(review_assessment: ModuleType) -> None:
    """AC-0003: an envelope for another commit is refused as stale."""
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=_envelope(OTHER_COMMIT))
    assert caught.value.denial_code == "denied-proof-run-stale"


@pytest.mark.parametrize("observed", ["", "FAIL", "error", None, True])
def test_t1_invalid_observation_is_refused(
    review_assessment: ModuleType, observed: object
) -> None:
    """AC-0004: only fail or pass are accepted observations."""
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, observed=observed)
    assert caught.value.denial_code == "denied-invalid-proof-run-observation"


@pytest.mark.parametrize("commit", ["a" * 39, "A" * 40, "g" * 40, "a" * 41, "", "a" * 40 + "\n"])
def test_t1_invalid_commit_is_refused_on_either_side(
    review_assessment: ModuleType, commit: str
) -> None:
    """AC-0004: both commits must be 40 or 64 lowercase hex characters."""
    for overrides in (
        {"current_subject_commit": commit},
        {"envelope": _envelope(commit), "current_subject_commit": commit},
    ):
        with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
            _call(review_assessment, **overrides)
        assert caught.value.denial_code == "denied-invalid-proof-run-commit"


def test_t1_sha256_length_commit_is_accepted(review_assessment: ModuleType) -> None:
    """AC-0004: a 64-character lowercase hex commit is valid."""
    commit = "c" * 64
    record = _call(
        review_assessment, envelope=_envelope(commit), current_subject_commit=commit
    )
    assert record["assessment"] == "supported"


@pytest.mark.parametrize(
    "field",
    ["command_sha256", "exit_status", "stderr_sha256", "stdout_sha256", "subject_commit"],
)
def test_t1_envelope_missing_field_is_refused(
    review_assessment: ModuleType, field: str
) -> None:
    """AC-0004: an envelope missing any of its five fields is refused."""
    envelope = _envelope()
    del envelope[field]
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=envelope)
    assert caught.value.denial_code == "denied-invalid-proof-run-envelope"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e.update(extra="x"),
        lambda e: e.update(exit_status="1"),
        lambda e: e.update(exit_status=True),
        lambda e: e.update(stdout_sha256="nothex"),
        lambda e: e.update(subject_commit=7),
    ],
)
def test_t1_envelope_extra_or_mistyped_field_is_refused(
    review_assessment: ModuleType, mutate: object
) -> None:
    """AC-0004: extra fields and wrong types are refused."""
    envelope = _envelope()
    mutate(envelope)  # type: ignore[operator]
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=envelope)
    assert caught.value.denial_code == "denied-invalid-proof-run-envelope"


def test_t1_non_dict_envelope_is_refused(review_assessment: ModuleType) -> None:
    """AC-0004: a non-mapping envelope is refused."""
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=[])
    assert caught.value.denial_code == "denied-invalid-proof-run-envelope"


# --- Supervisor consistency check (plan T2, integration) -------------------

_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")


def _result(request: dict, **fields: object) -> dict:
    """Wrap a controller result for a request."""
    return {
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": request["kind"],
        **fields,
    }


def _next(repo: Path) -> dict:
    """Return the current request."""
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0, payload
    return payload["request"]


def _assess_request(tmp_path: Path) -> tuple[Path, object, dict]:
    """Drive a real run to its first assess-finding request."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    request: dict = {}
    for _ in range(60):
        request = _next(repo)
        if request["kind"] == "review-role":
            break
        if request["kind"] == "external-effect":
            controller.handle_effect(request)
            continue
        code, admitted = controller.report(controller.work(request))
        assert code == 0, admitted
    assert request["kind"] == "review-role"
    code, admitted = controller.report(
        _result(request, selection=h.select_none(request))
    )
    assert code == 0, admitted
    role_request = _next(repo)
    report = h.report_review("adversarial-reviewer", role_request["review_subject"], 1)
    report["findings"][0]["material"] = True
    code, admitted = controller.report(_result(role_request, report=report))
    assert code == 0, admitted
    assess = _next(repo)
    assert assess["kind"] == "assess-finding"
    return repo, controller, assess


def _pbr(review_assessment: ModuleType, request: dict, observed: str, commit: str) -> dict:
    """Build a proof-by-run assessment for a request."""
    return review_assessment.proof_by_run_assessment(
        assessment_id="assessment-pbr",
        report_id=request["report_id"],
        finding_id=request["finding_id"],
        review_subject_fingerprint=request["review_subject_fingerprint"],
        observed=observed,
        envelope=_envelope(commit, 1 if observed == "fail" else 0),
        current_subject_commit=commit,
        judgment_authority="reviewer:test",
    )


def _ref(observed: str, commit: str) -> str:
    """Build a well-formed proof-run reference."""
    return f"proof-run:v1:{commit}:{observed}:{'c' * 64}"


def _bad_none(a: dict, head: str) -> None:
    a["evidence_refs"] = ["calc.py"]


def _bad_two(a: dict, head: str) -> None:
    a["evidence_refs"] = [a["evidence_refs"][0], _ref("fail", head)]


def _bad_commit(a: dict, head: str) -> None:
    a["evidence_refs"] = [_ref("fail", OTHER_COMMIT)]


def _bad_fail_unsupported(a: dict, head: str) -> None:
    a["evidence_refs"] = [_ref("fail", head)]
    a["assessment"] = "unsupported-opinion"


def _bad_pass_supported(a: dict, head: str) -> None:
    a["evidence_refs"] = [_ref("pass", head)]
    a["assessment"] = "supported"


@sup.INTEGRATION
@pytest.mark.parametrize(
    "corrupt",
    [_bad_none, _bad_two, _bad_commit, _bad_fail_unsupported, _bad_pass_supported],
)
def test_t2_inconsistent_proof_by_run_assessment_is_refused(
    tmp_path: Path, review_assessment: ModuleType, corrupt: object
) -> None:
    """An inconsistent proof-by-run assessment is refused and writes nothing."""
    repo, controller, assess = _assess_request(tmp_path)
    head = h.git(repo, "rev-parse", "HEAD").strip()
    record = _pbr(review_assessment, assess, "fail", head)
    corrupt(record, head)  # type: ignore[operator]
    code, refused = controller.report(_result(assess, assessment=record))
    assert code == 1, refused
    assert refused["refusal"]["code"] == "review-record-refused", refused
    assert h.git(repo, "rev-parse", "HEAD").strip() == head


@sup.INTEGRATION
def test_t2_consistent_proof_by_run_assessment_is_admitted(
    tmp_path: Path, review_assessment: ModuleType
) -> None:
    """A consistent supported proof-by-run assessment is admitted and repair is requested."""
    repo, controller, assess = _assess_request(tmp_path)
    head = h.git(repo, "rev-parse", "HEAD").strip()
    record = _pbr(review_assessment, assess, "fail", head)
    code, admitted = controller.report(_result(assess, assessment=record))
    assert code == 0, admitted
    assert h.git(repo, "rev-parse", "HEAD").strip() != head
    evidence = h.git(repo, "show", f"HEAD:{h.SPEC_DIR}/delivery/evidence.jsonl")
    assert "repair-request" in evidence


@sup.INTEGRATION
def test_t2_default_v1_assessment_is_admitted_unchanged(tmp_path: Path) -> None:
    """The harness's predicate_version v1 assessment still passes the check."""
    repo, controller, assess = _assess_request(tmp_path)
    code, admitted = controller.report(_result(assess, assessment=h.assessment(assess)))
    assert code == 0, admitted
