"""Contract tests for target workspace entries and contextual fixtures."""

from __future__ import annotations

import json
import tomllib
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "contracts/jsonschema/workspace-entry.schema.json"
FIXTURE_ROOT = ROOT / "packs/core/tests/pack/fixtures/work-intake-contracts/workspace"

SEMANTIC_FIELDS = {"path", "kind", "source", "summary", "needs"}
SOURCE_DECISION_FIELDS = {
    "artifact",
    "source_revision",
    "field",
    "decision",
    "local_approver",
    "date",
}
WORK_STATUSES = {
    "work.queue": "Approved",
    "work.active": "Implementing",
    "work.shipped": "Shipped",
}
MEMBERSHIPS = {
    "[backlog].open",
    "[backlog].closed",
    "ini-001.shaping_queue.backlog",
    "ini-001.shaping_queue.active",
    "ini-001.brief_queue.draft",
    "ini-001.brief_queue.ready",
    "ini-001.brief_queue.executing",
    "ini-001.brief_queue.shipped",
    "ini-001.work.queue",
    "ini-001.work.active",
    "ini-001.work.shipped",
}


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema() -> dict[str, object]:
    schema = _load_json(SCHEMA_PATH)
    assert isinstance(schema, dict)
    return schema


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema())


def _target_paths(kind: str) -> list[Path]:
    return sorted((FIXTURE_ROOT / "target" / kind).glob("*.json"))


def _load_toml(name: str) -> dict[str, Any]:
    return tomllib.loads((FIXTURE_ROOT / "context" / name).read_text(encoding="utf-8"))


def _workspace_memberships(doc: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    memberships: dict[str, list[dict[str, Any]]] = {}
    backlog = doc.get("backlog", {})
    for state in ("open", "closed"):
        memberships[f"[backlog].{state}"] = backlog.get(state, [])
    for initiative, body in doc.items():
        if not initiative.startswith("ini-"):
            continue
        for table_name in ("shaping_queue", "brief_queue", "work"):
            table = body.get(table_name, {})
            for state, entries in table.items():
                memberships[f"{initiative}.{table_name}.{state}"] = entries
    return memberships


def _local_need_key(need: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(need["type"]),
        str(need["kind"]),
        str(need["path"]),
    )


def _semantic_graph(doc: dict[str, Any]) -> list[tuple[str, str, tuple[tuple[str, str, str], ...]]]:
    entries = [
        entry
        for values in _workspace_memberships(doc).values()
        for entry in values
        if isinstance(entry, dict) and set(entry) >= SEMANTIC_FIELDS
    ]
    graph = []
    for entry in entries:
        local_needs = [
            _local_need_key(need)
            for need in entry["needs"]
            if need["type"] == "local"
        ]
        graph.append((entry["path"], entry["kind"], tuple(sorted(local_needs))))
    return sorted(graph)


def _classify_legacy(collection: str, value: object) -> str:
    if collection.startswith("work.") and isinstance(value, str):
        parts = value.split("/")
        return "legacy" if len(parts) == 2 and parts[0] == "spec" and parts[1] else "invalid"
    if collection.startswith("shaping_queue."):
        if isinstance(value, str):
            return "legacy" if value and "/" not in value else "invalid"
        if isinstance(value, dict):
            expected = {"slug", "type", "needs"}
            legacy_types = {"shape", "research", "strategy", "signal", "design"}
            if set(value) != expected or value["type"] not in legacy_types:
                return "invalid"
            return "legacy" if isinstance(value["needs"], list) else "invalid"
    if collection.startswith("brief_queue.") and isinstance(value, str):
        if value.startswith("docs/product/briefs/") and value.endswith(".md"):
            return "legacy"
        return "invalid"
    if collection == "backlog.open" and isinstance(value, dict):
        allowed = {"slug", "needs", "source", "summary", "type"}
        return "legacy" if "slug" in value and set(value) <= allowed else "invalid"
    return "invalid"


def _resolved_inside(root: Path, target: Path) -> bool:
    return target.resolve().is_relative_to(root.resolve())


def _compaction_decision(case: dict[str, Any]) -> str:
    if (
        case["status"] != "Shipped"
        or case["live_needs"]
        or case["open_parents"]
        or not case["closure_evidence"]
    ):
        return "retain"
    return "remove-index"


def _valid_work_contract(collection: str, kind: str, status: str, plan_exists: bool) -> bool:
    return kind == "spec" and status == WORK_STATUSES.get(collection) and plan_exists


def test_schema_is_valid_and_versioned() -> None:
    schema = _schema()

    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["contract_version"] == "workspace-entry.v1"
    assert schema["x-spec"] == [
        "docs/specs/normalized-intake-workspace-contracts/"
    ]


@pytest.mark.parametrize("fixture_path", _target_paths("valid"), ids=lambda p: p.stem)
def test_valid_target_entries(fixture_path: Path) -> None:
    payload = _load_json(fixture_path)
    assert isinstance(payload, dict)
    assert set(payload) == SEMANTIC_FIELDS

    _validator().validate(payload)


@pytest.mark.parametrize("fixture_path", _target_paths("invalid"), ids=lambda p: p.stem)
def test_invalid_target_entries(fixture_path: Path) -> None:
    errors = sorted(_validator().iter_errors(_load_json(fixture_path)), key=lambda error: error.json_path)

    assert errors, f"{fixture_path.name} unexpectedly matched the workspace entry schema"


def test_lifecycle_fixture_covers_memberships_minimal_intents_and_defects() -> None:
    doc = _load_toml("lifecycle.toml")
    memberships = _workspace_memberships(doc)
    validator = _validator()

    assert {name for name, entries in memberships.items() if entries} >= MEMBERSHIPS
    for entries in memberships.values():
        for entry in entries:
            validator.validate(entry)

    spec_artifacts = doc["spec_artifacts"]
    for collection, expected_status in WORK_STATUSES.items():
        entry = memberships[f"ini-001.{collection}"][0]
        artifact = spec_artifacts[entry["path"]]
        assert artifact["Status"] == expected_status
        assert artifact["plan"] == Path(entry["path"]).with_name("plan.md").as_posix()
        assert _valid_work_contract(
            collection,
            entry["kind"],
            artifact["Status"],
            artifact["plan_exists"],
        )

    for case in doc["work_contract_cases"]:
        assert _valid_work_contract(
            case["collection"],
            case["kind"],
            case["status"],
            case["plan_exists"],
        ) is case["expected"]

    ready_brief = "docs/product/briefs/ready-without-specs.md"
    assert any(entry["path"] == ready_brief for entry in memberships["ini-001.brief_queue.ready"])
    assert not any(
        entry["source"].get("parent") == ready_brief
        for entry in memberships["ini-001.work.queue"]
    )

    intent = doc["intent_artifacts"]["docs/product/intents/workspace-routing.md"]
    assert set(intent) == {"Status", "Level", "Outcome", "Opportunity", "Assumptions", "Source"}
    assert intent["Status"] == "Draft"

    defects = doc["defect_artifacts"]
    resolutions = set()
    for defect in defects.values():
        assert {"expected_behavior", "observed_behavior", "source", "citation"} <= set(defect)
        assert "reproduction_evidence" in defect or "error_signature" in defect
        if "resolution" in defect:
            resolutions.add(defect["resolution"])
    assert resolutions == {"fixed", "declined", "superseded"}


def test_authority_fixture_keeps_field_ownership_and_decisions_out_of_workspace() -> None:
    doc = _load_toml("authority.toml")
    source_decisions = doc["artifact_source_decisions"]
    decisions = {decision["decision"] for decision in source_decisions}

    assert decisions == {"keep-local", "accept-source", "revise-both"}
    for decision in source_decisions:
        assert set(decision) == SOURCE_DECISION_FIELDS
        assert decision["source_revision"]
        assert decision["local_approver"]
        date.fromisoformat(decision["date"])
    for entries in _workspace_memberships(doc).values():
        for entry in entries:
            _validator().validate(entry)
            assert "owned_fields" not in entry["source"]
            assert "source_decisions" not in entry["source"]


def test_legacy_shapes_are_collection_scoped_and_non_dispatchable() -> None:
    fixture_text = (FIXTURE_ROOT / "context" / "legacy-valid.toml").read_text(encoding="utf-8")
    assert "# comment-rich backlog item:" in fixture_text

    valid = tomllib.loads(fixture_text)["legacy"]["valid"]
    invalid = _load_toml("legacy-invalid.toml")["legacy"]["invalid"]

    for collection, values in valid.items():
        for value in values:
            assert _classify_legacy(collection, value) == "legacy"
            assert not (collection.startswith("work.") and isinstance(value, dict))
    for collection, values in invalid.items():
        for value in values:
            assert _classify_legacy(collection, value) == "invalid"


def test_compaction_fixture_retains_unsafe_cases_and_keeps_artifacts() -> None:
    doc = _load_toml("compaction.toml")
    outcomes = {case["id"]: case for case in doc["compaction_cases"]}

    for case in outcomes.values():
        assert _compaction_decision(case) == case["expected"]
        assert case["canonical_artifact_deleted"] is False


def test_summary_comments_and_order_do_not_change_semantic_graph() -> None:
    base = _load_toml("graph-base.toml")
    variant = _load_toml("graph-variant.toml")

    assert _semantic_graph(base) == _semantic_graph(variant)


def test_path_confinement_oracle_rejects_symlink_escape(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    in_root_target = repo_root / "docs/specs/ok/spec.md"
    external_target = tmp_path / "outside/spec.md"
    escape_link = repo_root / "docs/specs/escape/spec.md"

    in_root_target.parent.mkdir(parents=True)
    in_root_target.write_text("in root\n", encoding="utf-8")
    external_target.parent.mkdir(parents=True)
    external_target.write_text("outside root\n", encoding="utf-8")
    escape_link.parent.mkdir(parents=True)

    try:
        escape_link.symlink_to(external_target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    assert _resolved_inside(repo_root, in_root_target) is True
    assert _resolved_inside(repo_root, escape_link) is False
