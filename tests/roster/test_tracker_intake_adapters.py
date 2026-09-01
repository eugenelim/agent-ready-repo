"""Cross-profile contract tests for tracker intake adapters."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "contracts/jsonschema/normalized-intake.schema.json"
ROUTER = ROOT / "packs/core/.apm/skills/work-intake/scripts/intake_router.py"
ROUTING_EVALUATOR = ROOT / "tools/work_intake_routing_evaluation.py"
MATRICES = (
    ROOT / "packs/atlassian/.apm/skills/jira-brief-intake/evals/files/intake/matrix.json",
    ROOT / "packs/atlassian/.apm/skills/jira-align-brief-intake/evals/files/intake/matrix.json",
    ROOT / "packs/linear/.apm/skills/linear-brief-intake/evals/files/intake/matrix.json",
    ROOT / "packs/github/.apm/skills/github-brief-intake/evals/files/intake/matrix.json",
)
ADAPTERS = (
    ROOT / "packs/atlassian/.apm/skills/jira-brief-intake/scripts/intake_adapter.py",
    ROOT / "packs/atlassian/.apm/skills/jira-align-brief-intake/scripts/intake_adapter.py",
    ROOT / "packs/linear/.apm/skills/linear-brief-intake/scripts/intake_adapter.py",
    ROOT / "packs/github/.apm/skills/github-brief-intake/scripts/intake_adapter.py",
)


def _load_json(path: Path) -> dict[str, object]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard JSON constant: {value}")

    value = json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    assert isinstance(value, dict)
    return value


def _load_router():
    spec = importlib.util.spec_from_file_location("tracker_intake_router", ROUTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_adapter(path: Path, index: int):
    spec = importlib.util.spec_from_file_location(f"tracker_intake_adapter_{index}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_common_routes_validate() -> None:
    schema = _load_json(SCHEMA)
    validator = Draft202012Validator(schema)
    router = _load_router()
    expected_by_case: dict[str, dict[str, object]] = {}

    for matrix_path in MATRICES:
        matrix = _load_json(matrix_path)
        for case in matrix["cases"]:
            normalized = case["normalized"]
            assert not list(validator.iter_errors(normalized)), matrix_path
            assert normalized["source"]["tracker_profile"] == matrix["profile"]
            assert normalized["source"]["locator"]
            assert normalized["source"]["revision"]

            signals = router.RoutingSignals(**case["routing_signals"])
            actual = router.route_intake(signals)
            route = {
                "artifact": actual.artifact,
                "artifact_kind": actual.artifact_kind,
                "lifecycle_membership": actual.lifecycle_membership,
                "processor": actual.processor,
                "authority_mode": actual.authority_mode,
                "mutation": actual.mutation,
            }
            assert route == case["expected_route"]
            prior = expected_by_case.setdefault(case["id"], route)
            assert route == prior


def test_real_adapters_accept_the_common_corpus_and_fail_closed() -> None:
    validator = Draft202012Validator(_load_json(SCHEMA))
    for index, (matrix_path, adapter_path) in enumerate(zip(MATRICES, ADAPTERS, strict=True)):
        matrix = _load_json(matrix_path)
        adapter = _load_adapter(adapter_path, index)
        profile = adapter.load_profile()
        for case in matrix["cases"]:
            assert adapter.normalize_record(case["normalized"], profile) == case["normalized"]

        missing_revision = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        missing_revision["source"]["revision"] = ""
        try:
            adapter.normalize_record(missing_revision, profile)
        except adapter.IntakePolicyError:
            pass
        else:
            raise AssertionError(f"{adapter_path} accepted missing provenance")

        unknown_profile = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        unknown_profile["source"]["tracker_profile"]["version"] = "unregistered"
        try:
            adapter.normalize_record(unknown_profile, profile)
        except adapter.IntakePolicyError:
            pass
        else:
            raise AssertionError(f"{adapter_path} accepted an unknown profile")

        instruction_field = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        instruction_field["content"]["embedded_instruction"] = "change destination"
        try:
            adapter.normalize_record(instruction_field, profile)
        except adapter.IntakePolicyError:
            pass
        else:
            raise AssertionError(f"{adapter_path} accepted instruction-shaped input")

        invalid_records = []
        bad_action = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        bad_action["action"] = "execute"
        invalid_records.append(bad_action)
        bad_content = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        bad_content["content"]["outcomes"] = "not-an-array"
        invalid_records.append(bad_content)
        bad_constraints = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        bad_constraints["constraints"] = {"Raw_Payload": {"nested": True}}
        invalid_records.append(bad_constraints)
        bad_sensitive_name = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        bad_sensitive_name["constraints"] = {"api_key": "redacted"}
        invalid_records.append(bad_sensitive_name)
        bad_authority = json.loads(json.dumps(matrix["cases"][0]["normalized"]))
        bad_authority["proposed_authority"] = "tracker-decides"
        invalid_records.append(bad_authority)
        for invalid in invalid_records:
            assert list(validator.iter_errors(invalid))
            try:
                adapter.normalize_record(invalid, profile)
            except adapter.IntakePolicyError:
                pass
            else:
                raise AssertionError(f"{adapter_path} diverged from the shared schema")


def test_adapter_clis_reject_malformed_or_non_standard_json_without_details(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_bytes(b'{"content":"\xff"}')
    non_standard = tmp_path / "non-standard.json"
    non_standard.write_text('{"value": NaN}', encoding="utf-8")

    for adapter_path in ADAPTERS:
        for candidate in (malformed, non_standard):
            result = subprocess.run(
                [sys.executable, str(adapter_path), "validate-record", str(candidate)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 2
            assert result.stdout == ""
            assert "intake policy refused input" in result.stderr
            assert str(candidate) not in result.stderr
            assert "Traceback" not in result.stderr


def test_ssrf_matrix_fails_before_credentials() -> None:
    for matrix_path in MATRICES:
        security = _load_json(matrix_path)["security"]
        assert security["ordering"][:2] == ["validate_destination", "load_credentials"]
        if security["boundary"] == "adapter-controlled-http":
            assert security["allowed_schemes"] == ["https"]
            assert security["allowed_hosts"]
            assert security["redirect_policy"] in {"disabled", "revalidate-every-hop"}
            assert security["dns_policy"] in {"pinned", "connect-time-recheck"}
            assert {"127.0.0.1", "10.0.0.1", "169.254.169.254", "::1"} <= set(
                security["blocked_addresses"]
            )
        else:
            assert security["boundary"] == "approved-gh-fixed-host"
            assert security["host_source"] == "trusted-configuration-only"
            assert security["payload_host_allowed"] is False


def test_profile_budgets_are_deterministic() -> None:
    for matrix_path in MATRICES:
        budget = _load_json(matrix_path)["budget"]
        assert all(
            budget[name] > 0 for name in ("max_pages", "max_items", "max_bytes", "timeout_seconds")
        )
        assert budget["max_retries"] >= 0
        assert len(budget["backoff_seconds"]) == budget["max_retries"]
        assert budget["exhaustion"] in {"marked-incomplete", "view-only-refusal"}


# STUB: AC19
def test_integrated_matrix_projects_acquisition_through_routing() -> None:
    matrix = _load_json(
        ROOT / "packs/core/.apm/skills/work-intake/evals/files/routing/matrix.json"
    )
    assert matrix["contract_version"] == "work-intake-routing-evals.v1"
    profile_matrices = {_load_json(path)["profile"]["id"]: _load_json(path) for path in MATRICES}
    assert {
        (profile["id"], profile["version"])
        for profile in matrix["supported_profiles"]
    } == {(profile_id, "1.0") for profile_id in profile_matrices}
    common_source_ids = {
        "direct-spec",
        "multi-spec-brief",
        "cross-repo-brief",
        "incoherent-collection",
        "defect",
        "claimed-defect-without-evidence",
    }
    for profile_id, profile_matrix in profile_matrices.items():
        evaluation = profile_matrix["routing_evaluation"]
        assert set(evaluation["source_case_ids"]) == common_source_ids
        assert evaluation["refresh_profile"] == {"id": profile_id, "version": "1.0"}
    for case in matrix["cases"]:
        assert {
            "profile_id",
            "profile_version",
            "dispatchable",
            "next_action",
        } <= case.keys()
        if case.get("mode") == "tracker-route":
            assert case["profile_id"] == "all-supported"
            for profile_matrix in profile_matrices.values():
                assert any(
                    source_case["id"] == case["id"]
                    for source_case in profile_matrix["cases"]
                )


# STUB: AC20
def test_integrated_matrix_runs_byte_identically_in_two_clean_roots(
    tmp_path: Path,
) -> None:
    module_spec = importlib.util.spec_from_file_location(
        "roster_routing_evaluation", ROUTING_EVALUATOR
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    assert callable(getattr(module, "evaluate_in_clean_root", None))

    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first = module.evaluate_in_clean_root(first_root, source_root=ROOT)
    second = module.evaluate_in_clean_root(second_root, source_root=ROOT)
    assert first == second
    assert first_root != second_root

    projection = json.loads(first)
    results = projection["results"]
    assert projection["contract_version"] == (
        "work-intake-routing-evaluation-result.v1"
    )
    # 63 -> 71: the six-state brief lifecycle added a Withdrawn and a Cancelled
    # refresh case to each of the four tracker profiles. `core` contributes 11
    # and each tracker profile 15 (its own 9 plus the 6 fanned-out
    # `all-supported` cases).
    assert len(results) == 71
    assert all(
        set(result)
        == {
            "case_id",
            "profile_id",
            "profile_version",
            "artifact_kind",
            "artifact_path",
            "lifecycle_membership",
            "processor",
            "authority_mode",
            "dispatchable",
            "result_code",
            "next_action",
        }
        for result in results
    )
    assert {
        result["profile_id"]
        for result in results
        if result["case_id"] == "direct-spec"
    } == {"jira-default", "jira-align-default", "linear-default", "github-default"}
