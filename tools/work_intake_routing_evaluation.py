"""Evaluation-only composition of work-intake routing seams.

This module deliberately does not define a runtime result contract. It stages
versioned inputs in a clean root, invokes the owning Group 2-6 implementations,
and projects their observable outputs into canonical JSON for regression tests.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

_RESULT_FIELDS = (
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
)
_PROFILE_INPUTS = {
    "jira-default": (
        "packs/atlassian/.apm/skills/jira-brief-intake",
        "packs/atlassian/.apm/skills/jira-refresh",
    ),
    "jira-align-default": (
        "packs/atlassian/.apm/skills/jira-align-brief-intake",
        "packs/atlassian/.apm/skills/jira-align-refresh",
    ),
    "linear-default": (
        "packs/linear/.apm/skills/linear-brief-intake",
        "packs/linear/.apm/skills/linear",
    ),
    "github-default": (
        "packs/github/.apm/skills/github-brief-intake",
        "packs/github/.apm/skills/github-refresh",
    ),
}


def _load(path: Path, name: str) -> ModuleType:
    """Load one staged module without relying on repository imports."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("routing evaluation module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _copy_tree(source_root: Path, clean_root: Path, relative: str) -> None:
    """Copy one declared evaluation input tree into an isolated root."""
    source = source_root / relative
    target = clean_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def _stage_inputs(source_root: Path, clean_root: Path) -> None:
    """Stage byte-identical engines and fixtures in a new empty root."""
    source_root = source_root.resolve(strict=True)
    if not (source_root / "packs/core/pack.toml").is_file():
        raise ValueError("routing evaluation source root is invalid")
    if clean_root.is_symlink() or (clean_root.exists() and not clean_root.is_dir()):
        raise ValueError("routing evaluation root must be a directory")
    resolved_clean = clean_root.resolve(strict=False)
    if resolved_clean == source_root or resolved_clean.is_relative_to(source_root):
        raise ValueError("routing evaluation root must be outside the source repository")
    if clean_root.exists() and any(clean_root.iterdir()):
        raise ValueError("routing evaluation root must be empty")
    clean_root.mkdir(parents=True, exist_ok=True)
    for relative in (
        "packs/core/.apm/skills/work-intake",
        "packs/core/.apm/skills/workspace-status",
        "packs/core/tests/pack/fixtures/work-intake-contracts",
    ):
        _copy_tree(source_root, clean_root, relative)
    for intake, refresh in _PROFILE_INPUTS.values():
        _copy_tree(source_root, clean_root, intake)
        _copy_tree(source_root, clean_root, refresh)


def _canonical(value: object) -> bytes:
    """Serialize one evaluation projection with stable UTF-8 bytes."""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _record(
    case: dict[str, Any],
    *,
    profile_id: str,
    profile_version: str,
    artifact: str,
    artifact_kind: str,
    lifecycle_membership: str,
    processor: str,
    authority_mode: str,
    dispatchable: bool,
    result_code: str,
    next_action: str,
) -> dict[str, object]:
    """Project independently owned outputs into the evaluation-only shape."""
    return {
        "case_id": case["id"],
        "profile_id": profile_id,
        "profile_version": profile_version,
        "artifact_kind": artifact_kind,
        "artifact_path": artifact,
        "lifecycle_membership": lifecycle_membership,
        "processor": processor,
        "authority_mode": authority_mode,
        "dispatchable": dispatchable,
        "result_code": result_code,
        "next_action": next_action,
    }


def _assert_expected(case: dict[str, Any], result: dict[str, object]) -> None:
    """Fail when the actual seam output diverges from canonical expectations."""
    expected_names = {
        "artifact_path": "artifact",
        "artifact_kind": "artifact_kind",
        "lifecycle_membership": "lifecycle_membership",
        "processor": "processor",
        "authority_mode": "authority_mode",
        "dispatchable": "dispatchable",
        "result_code": "result_code",
        "next_action": "next_action",
    }
    for actual_name, expected_name in expected_names.items():
        if result[actual_name] != case[expected_name]:
            raise AssertionError(f"{case['id']} diverged at {actual_name}")


def _route_outcome(case: dict[str, Any], route: object) -> tuple[bool, str, str]:
    """Normalize one actual core route into stable evaluation fields."""
    signals = case["signals"]
    action = signals["action"]
    if action == "status":
        next_action = (
            "triage-workspace-findings"
            if case["id"] == "status-triage"
            else "inspect-workspace-status"
        )
        return False, "status-ready", next_action
    if action == "remember":
        return False, "remembered", "inspect-workspace-status"
    if action == "refresh":
        return False, "refresh-unavailable", "configure-compatible-refresh-processor"
    processor = str(route.processor)
    if route.lifecycle_membership == "draft-with-gaps":
        return False, "clarification-required", "route-separate-units-or-view-only"
    if processor == "none":
        return False, "routed", "shape-intent"
    return True, "routed", "start-work-loop" if processor == "work-loop" else processor


def _evaluate_route(
    staged_root: Path,
    case: dict[str, Any],
    engine: ModuleType,
    router: ModuleType,
) -> dict[str, object]:
    """Invoke Group 2 validation and the actual Group 4 router."""
    fixture_name = case["fixture"]
    if fixture_name.startswith("normalized-intake/"):
        fixture = (
            staged_root
            / "packs/core/tests/pack/fixtures/work-intake-contracts"
            / fixture_name
        )
        parsed, findings = engine.validate_normalized_intake(
            json.loads(fixture.read_text(encoding="utf-8"))
        )
        if parsed is None or findings:
            raise AssertionError(f"{case['id']} Group 2 validation failed")
    elif fixture_name.startswith("evals/"):
        fixture = staged_root / "packs/core/.apm/skills/work-intake" / fixture_name
        parsed, findings = engine.validate_normalized_intake(
            json.loads(fixture.read_text(encoding="utf-8"))
        )
        if parsed is None or findings:
            raise AssertionError(f"{case['id']} Group 2 validation failed")
    elif case["signals"]["action"] == "status":
        fixture = (
            staged_root
            / "packs/core/tests/pack/fixtures/work-intake-contracts"
            / fixture_name
        )
        workspace = engine.parse_workspace(fixture)
        engine.run_canonical_reconciliation(workspace, staged_root)
    signals = router.RoutingSignals(**case["signals"])
    route = router.route_intake(signals)
    dispatchable, result_code, next_action = _route_outcome(case, route)
    result = _record(
        case,
        profile_id=case["profile_id"],
        profile_version=case["profile_version"],
        artifact=route.artifact,
        artifact_kind=route.artifact_kind,
        lifecycle_membership=route.lifecycle_membership,
        processor=route.processor,
        authority_mode=route.authority_mode,
        dispatchable=dispatchable,
        result_code=result_code,
        next_action=next_action,
    )
    if route.mutation != case["mutation"]:
        raise AssertionError(f"{case['id']} diverged at mutation")
    _assert_expected(case, result)
    return result


def _tracker_case(
    staged_root: Path,
    case: dict[str, Any],
    profile_id: str,
    index: int,
    engine: ModuleType,
    router: ModuleType,
) -> dict[str, object]:
    """Acquire provenance, normalize, validate, and route one profile fixture."""
    intake_relative, _refresh_relative = _PROFILE_INPUTS[profile_id]
    intake_root = staged_root / intake_relative
    matrix = json.loads(
        (intake_root / "evals/files/intake/matrix.json").read_text(encoding="utf-8")
    )
    if case["id"] not in matrix["routing_evaluation"]["source_case_ids"]:
        raise AssertionError(f"{case['id']} is not declared by {profile_id}")
    profile_case = next(item for item in matrix["cases"] if item["id"] == case["id"])
    adapter = _load(
        intake_root / "scripts/intake_adapter.py",
        f"routing_evaluation_adapter_{index}",
    )
    profile = adapter.load_profile()
    normalized = adapter.normalize_record(profile_case["normalized"], profile)
    if adapter.trusted_source(profile_case["raw"], profile) != normalized["source"]:
        raise AssertionError(f"{case['id']} provenance diverged for {profile_id}")
    parsed, findings = engine.validate_normalized_intake(normalized)
    if parsed is None or findings:
        raise AssertionError(f"{case['id']} Group 2 validation failed for {profile_id}")
    route = router.route_intake(router.RoutingSignals(**profile_case["routing_signals"]))
    if route.mutation != case["mutation"]:
        raise AssertionError(f"{case['id']} mutation diverged for {profile_id}")
    dispatchable = route.processor != "none"
    result_code = "routed" if dispatchable else "clarification-required"
    if case["id"] == "claimed-defect-without-evidence":
        next_action = "supply-expected-behavior-evidence"
    elif case["id"] == "incoherent-collection":
        next_action = "route-separate-units-or-view-only"
    else:
        next_action = route.processor
    result = _record(
        case,
        profile_id=profile["id"],
        profile_version=profile["version"],
        artifact=route.artifact,
        artifact_kind=route.artifact_kind,
        lifecycle_membership=route.lifecycle_membership,
        processor=route.processor,
        authority_mode=route.authority_mode,
        dispatchable=dispatchable,
        result_code=result_code,
        next_action=next_action,
    )
    _assert_expected(case, result)
    return result


def _registry(
    staged_root: Path, profile_id: str, index: int, refresh: ModuleType
) -> object:
    """Register the actual Group 6 processor for one exact profile version."""
    _intake_relative, refresh_relative = _PROFILE_INPUTS[profile_id]
    refresh_root = staged_root / refresh_relative
    processor = _load(
        refresh_root / "scripts" / (
            "linear.py" if profile_id == "linear-default" else "processor.py"
        ),
        f"routing_evaluation_refresh_{index}",
    )
    registry = refresh.RefreshProcessorRegistry()
    profile = json.loads(
        (refresh_root / "references/refresh-profile.json").read_text(encoding="utf-8")
    )
    if (
        profile["id"] != profile_id
        or profile["version"] != "1.0"
        or "acquire" not in profile["capabilities"]
    ):
        raise AssertionError(f"invalid refresh evaluation profile: {profile_id}")

    def unreached(_locator: str, _revision: str) -> dict[str, object]:
        raise AssertionError("lifecycle evaluation must not acquire remote data")

    if profile_id in {"jira-default", "jira-align-default"}:
        processor.register(registry, refresh, acquire=unreached)
    elif profile_id == "linear-default":
        registry.register(processor.linear_refresh_registration(refresh, acquire=unreached))
    else:
        registry.register(processor.github_refresh_registration(refresh, acquire=unreached))
    return registry


def _evaluate_refresh(
    staged_root: Path,
    case: dict[str, Any],
    index: int,
    router: ModuleType,
    refresh: ModuleType,
) -> dict[str, object]:
    """Invoke configured routing plus the shared Group 6 lifecycle evaluator."""
    profile_id = case["profile_id"]
    registry = _registry(staged_root, profile_id, index, refresh)
    signals = router.RoutingSignals(
        action="refresh",
        artifact=case["artifact"],
        artifact_kind=case["artifact_kind"],
        authority_mode=case["authority_mode"],
        profile_id=profile_id,
        profile_version=case["profile_version"],
    )
    route = router.route_intake(signals, registry)
    lifecycle = case["lifecycle"]
    accepted = lifecycle != "Draft"
    authority = refresh.SourceAuthority(
        source_ref="tracker:item-1",
        source_revision="revision-1",
        accepted_revision="revision-1",
        owned_fields={"Outcome": "local" if accepted else "source"},
        acceptance=(
            refresh.Approval(
                identity="evaluation-approver",
                role="product",
                decided_at="2026-08-21T11:59:00Z",
                authorization_source="current-human-session",
            )
            if accepted
            else None
        ),
    )
    comparison = refresh.RefreshComparison(
        artifact_path=case["artifact"],
        artifact_kind=case["artifact_kind"],
        lifecycle=lifecycle,
        authority_mode=case["authority_mode"],
        current_revision="revision-1",
        compared_revision="revision-2",
        profile_id=profile_id,
        profile_version=case["profile_version"],
        changed_fields=(refresh.ChangedField("Outcome", "local", "source"),),
    )
    outcome = refresh.evaluate_refresh(
        comparison=comparison,
        authority=authority,
        policy=refresh.RefreshAuthorizationPolicy(("product",), ("product",), ("product",)),
        approver=refresh.ApproverEvidence(
            identity="evaluation-approver",
            role="product",
            confirmed_at="2026-08-21T12:00:00Z",
            authorization_source="current-human-session",
        ),
        decisions={"Outcome": "keep-local" if accepted else "accept-source"},
        now=datetime(2026, 8, 21, 12, 0, tzinfo=UTC),
    )
    dispatchable = outcome.code == "ready"
    next_action = "review-refresh-diff" if dispatchable else "preserve-local-requirements"
    result = _record(
        case,
        profile_id=profile_id,
        profile_version=case["profile_version"],
        artifact=route.artifact,
        artifact_kind=route.artifact_kind,
        lifecycle_membership=route.lifecycle_membership,
        processor=route.processor,
        authority_mode=route.authority_mode,
        dispatchable=dispatchable,
        result_code=outcome.code,
        next_action=next_action,
    )
    if outcome.local_mutation != case["mutation"]:
        raise AssertionError(f"{case['id']} refresh mutation diverged")
    _assert_expected(case, result)
    return result


def _evaluate_migration(
    staged_root: Path, case: dict[str, Any], engine: ModuleType
) -> dict[str, object]:
    """Invoke T2's actual read-only planner with a reviewed versioned fixture."""
    fixture_root = (
        staged_root / "packs/core/.apm/skills/work-intake/evals/files/routing"
    )
    workspace = staged_root / "workspace.toml"
    shutil.copy2(fixture_root / "migration-workspace.toml", workspace)
    artifact = staged_root / case["artifact"]
    artifact.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fixture_root / "migration-target-spec.md", artifact)
    shutil.copy2(fixture_root / "migration-target-plan.md", artifact.with_name("plan.md"))
    selection = json.loads((fixture_root / "migration-selection.json").read_text())
    before = {
        path.relative_to(staged_root): path.read_bytes()
        for path in staged_root.rglob("*")
        if path.is_file()
    }
    plan = engine.compute_migration_plan(staged_root, workspace, selection)
    after = {
        path.relative_to(staged_root): path.read_bytes()
        for path in staged_root.rglob("*")
        if path.is_file()
    }
    if before != after:
        raise AssertionError("migration routing evaluation performed a write")
    operation = plan.proposed_operation
    if operation is None:
        raise AssertionError(
            "migration routing evaluation did not produce a plan: "
            + str(plan.result.get("result_code"))
        )
    if plan.result["next_action"] != "confirm-migration":
        raise AssertionError("migration planner returned an unexpected next action")
    result = _record(
        case,
        profile_id=case["profile_id"],
        profile_version=case["profile_version"],
        artifact=operation["artifact_receipt"]["path"],
        artifact_kind=operation["target_entry"]["kind"],
        lifecycle_membership=operation["target_membership"]["collection"],
        processor=operation["owning_processor"],
        authority_mode=operation["target_entry"]["source"]["mode"],
        dispatchable=False,
        result_code=plan.result["result_code"],
        next_action="review-migration-plan",
    )
    _assert_expected(case, result)
    return result


def evaluate_in_clean_root(
    clean_root: Path, *, source_root: Path | None = None
) -> bytes:
    """Run actual seams in an independent root and return canonical result bytes."""
    source = source_root or Path(__file__).resolve().parents[1]
    _stage_inputs(source, clean_root)
    core = clean_root / "packs/core/.apm/skills"
    engine = _load(
        core / "workspace-status/scripts/workspace_status_engine.py",
        f"routing_evaluation_engine_{id(clean_root)}",
    )
    router = _load(
        core / "work-intake/scripts/intake_router.py",
        f"routing_evaluation_router_{id(clean_root)}",
    )
    refresh = _load(
        core / "work-intake/scripts/refresh.py",
        f"routing_evaluation_refresh_runtime_{id(clean_root)}",
    )
    matrix = json.loads(
        (core / "work-intake/evals/files/routing/matrix.json").read_text(encoding="utf-8")
    )
    results: list[dict[str, object]] = []
    profile_ids = [profile["id"] for profile in matrix["supported_profiles"]]
    for index, case in enumerate(matrix["cases"]):
        if case["mode"] == "route":
            results.append(_evaluate_route(clean_root, case, engine, router))
        elif case["mode"] == "tracker-route":
            results.extend(
                _tracker_case(clean_root, case, profile_id, index * 10 + offset, engine, router)
                for offset, profile_id in enumerate(profile_ids)
            )
        elif case["mode"] == "refresh":
            results.append(_evaluate_refresh(clean_root, case, index, router, refresh))
        elif case["mode"] == "migration":
            results.append(_evaluate_migration(clean_root, case, engine))
        else:
            raise AssertionError(f"unsupported routing evaluation mode: {case['mode']}")
    results.sort(key=lambda item: tuple(str(item[name]) for name in _RESULT_FIELDS))
    return _canonical(
        {"contract_version": "work-intake-routing-evaluation-result.v1", "results": results}
    )
