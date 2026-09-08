"""Cross-contract harness for work intake schemas and fixtures."""

from __future__ import annotations

import json
import math
import tempfile
import tomllib
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = ROOT / "contracts/jsonschema"
FIXTURE_ROOT = ROOT / "packs/core/tests/pack/fixtures/work-intake-contracts"
NORMALIZED_SCHEMA = CONTRACT_ROOT / "normalized-intake.schema.json"
WORKSPACE_SCHEMA = CONTRACT_ROOT / "workspace-entry.schema.json"
ADAPTER_CONTRACT = (
    ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "adapter.toml"
)
WORKSPACE_CONTEXT = FIXTURE_ROOT / "workspace/context"
WORKSPACE_FIELDS = ("path", "kind", "source", "summary", "needs")
WORKSPACE_FIELD_SET = set(WORKSPACE_FIELDS)
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


def _load_json_strict(path: Path) -> object:
    def reject_constant(value: str) -> None:
        raise ValueError(f"{path}: non-standard JSON constant {value}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def _load_schema(path: Path) -> dict[str, object]:
    schema = _load_json_strict(path)
    assert isinstance(schema, dict), f"{path}: schema must be an object"
    return schema


def _json_fixture_paths(*parts: str) -> list[Path]:
    return sorted((FIXTURE_ROOT.joinpath(*parts)).glob("*.json"))


def _toml_context_paths() -> list[Path]:
    return sorted(WORKSPACE_CONTEXT.glob("*.toml"))


def _load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _workspace_memberships(doc: dict[str, Any]) -> dict[str, list[Any]]:
    memberships: dict[str, list[Any]] = {}
    backlog = doc.get("backlog", {})
    for state in ("open", "closed"):
        memberships[f"backlog.{state}"] = backlog.get(state, [])

    for initiative, body in doc.items():
        if not initiative.startswith("ini-"):
            continue
        for table_name in ("shaping_queue", "brief_queue", "work"):
            for state, entries in body.get(table_name, {}).items():
                memberships[f"{initiative}.{table_name}.{state}"] = entries
    return memberships


def _normalize_workspace_entry(entry: Any, fixture: Path, collection: str) -> dict[str, Any]:
    assert isinstance(entry, dict), f"{fixture}:{collection}: target entry must be an object"
    assert set(entry) == WORKSPACE_FIELD_SET, (
        f"{fixture}:{collection}:{entry.get('path', '<missing>')}: "
        "target entry must normalize to exactly path/kind/source/summary/needs"
    )
    return {field: entry[field] for field in WORKSPACE_FIELDS}


def _target_entries(doc: dict[str, Any], fixture: Path) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    for collection, values in _workspace_memberships(doc).items():
        for value in values:
            if isinstance(value, dict) and set(value) == WORKSPACE_FIELD_SET:
                entries.append((collection, _normalize_workspace_entry(value, fixture, collection)))
    return entries


def _legacy_classification(collection: str, value: object) -> str:
    if collection.startswith("work.") and isinstance(value, str):
        parts = value.split("/")
        return "legacy" if len(parts) == 2 and parts[0] == "spec" and bool(parts[1]) else "invalid"

    if collection.startswith("shaping_queue."):
        if isinstance(value, str):
            return "legacy" if value and "/" not in value else "invalid"
        if isinstance(value, dict):
            legacy_types = {"shape", "research", "strategy", "signal", "design"}
            if set(value) == {"slug", "type", "needs"} and value["type"] in legacy_types:
                return "legacy" if isinstance(value["needs"], list) else "invalid"
            return "invalid"

    if collection.startswith("brief_queue.") and isinstance(value, str):
        return "legacy" if value.startswith("docs/product/briefs/") and value.endswith(".md") else "invalid"

    if collection == "backlog.open" and isinstance(value, dict):
        allowed = {"slug", "needs", "source", "summary", "type"}
        return "legacy" if "slug" in value and set(value) <= allowed else "invalid"

    return "invalid"


def _semantic_graph(doc: dict[str, Any], fixture: Path) -> list[tuple[str, str, tuple[tuple[str, str, str], ...]]]:
    graph = []
    for _collection, entry in _target_entries(doc, fixture):
        local_needs = tuple(
            sorted(
                (need["type"], need["kind"], need["path"])
                for need in entry["needs"]
                if need["type"] == "local"
            )
        )
        graph.append((entry["path"], entry["kind"], local_needs))
    return sorted(graph)


def _duplicate_paths(doc: dict[str, Any], fixture: Path) -> set[str]:
    paths = [entry["path"] for _collection, entry in _target_entries(doc, fixture)]
    return {path for path, count in Counter(paths).items() if count > 1}


def _status_for(doc: dict[str, Any], path: str) -> str | None:
    spec = doc.get("spec_artifacts", {}).get(path)
    if isinstance(spec, dict):
        return str(spec.get("Status"))
    intent = doc.get("intent_artifacts", {}).get(path)
    if isinstance(intent, dict):
        return str(intent.get("Status"))
    defect = doc.get("defect_artifacts", {}).get(path)
    if isinstance(defect, dict) and "resolution" in defect:
        return str(defect["resolution"])
    if path.endswith("ready-without-specs.md"):
        return "Ready"
    return None


def _impossible_membership(collection: str, entry: dict[str, Any], status: str | None) -> bool:
    kind = entry["kind"]
    for suffix, expected_status in WORK_STATUSES.items():
        if collection.endswith(suffix):
            return kind != "spec" or status != expected_status
    if collection.endswith("brief_queue.shipped") and kind != "brief":
        return True
    if collection.endswith("shaping_queue.active") and kind not in {"intent", "research", "design"}:
        return True
    return collection == "backlog.closed" and kind == "defect" and status not in {"fixed", "declined", "superseded"}


def _valid_work_contract(collection: str, kind: str, status: str, plan_exists: bool) -> bool:
    return kind == "spec" and status == WORK_STATUSES.get(collection) and plan_exists


def _inside_resolved(root: Path, target: Path) -> bool:
    return target.resolve().is_relative_to(root.resolve())


def _existing_confined_file(root: Path, relative_path: str) -> bool:
    try:
        resolved_root = root.resolve(strict=True)
        resolved_target = (root / relative_path).resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return resolved_target.is_file() and resolved_target.is_relative_to(resolved_root)


def _compaction_decision(case: dict[str, Any]) -> str:
    if (
        case["status"] != "Shipped"
        or case["live_needs"]
        or case["open_parents"]
        or not case["closure_evidence"]
    ):
        return "retain"
    return "remove-index"


def _temp_path_available() -> bool:
    try:
        Path(tempfile.gettempdir())
    except FileNotFoundError:
        return False
    return True


def test_both_schemas_are_valid_versioned_and_backlinked() -> None:
    expected = {
        NORMALIZED_SCHEMA: "normalized-intake.v1",
        WORKSPACE_SCHEMA: "workspace-entry.v1",
    }
    for path, version in expected.items():
        schema = _load_schema(path)
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", f"{path}: meta-schema"
        assert schema["contract_version"] == version, f"{path}: stable contract version"
        expected_specs = ["docs/specs/normalized-intake-workspace-contracts/"]
        if path == NORMALIZED_SCHEMA:
            expected_specs.append("docs/specs/shaping-intake-handoff/")
        if path == WORKSPACE_SCHEMA:
            expected_specs.append("docs/specs/semantic-surface-resolver/")
            expected_specs.append("docs/specs/dependency-scoped-completion-receipts/")
        assert schema["x-spec"] == expected_specs, f"{path}: x-spec"


def test_skill_adapters_preserve_work_intake_frontmatter() -> None:
    contract = tomllib.loads(ADAPTER_CONTRACT.read_text(encoding="utf-8"))
    skill_modes = {
        name: next(
            rule["mode"]
            for rule in adapter["projection"]
            if rule["primitive"] == "skill"
        )
        for name, adapter in contract["adapter"].items()
    }

    assert len(skill_modes) >= 7
    assert set(skill_modes.values()) == {"direct-directory"}


@pytest.mark.parametrize(
    ("schema_path", "fixture_path"),
    [
        (NORMALIZED_SCHEMA, path)
        for path in _json_fixture_paths("normalized-intake", "valid")
    ]
    + [
        (WORKSPACE_SCHEMA, path)
        for path in _json_fixture_paths("workspace", "target", "valid")
    ],
    ids=lambda item: item.name if isinstance(item, Path) else str(item),
)
def test_valid_json_fixtures_match_their_schema(schema_path: Path, fixture_path: Path) -> None:
    validator = Draft202012Validator(_load_schema(schema_path))
    payload = _load_json_strict(fixture_path)

    errors = sorted(validator.iter_errors(payload), key=lambda error: error.json_path)
    assert not errors, f"{fixture_path}: expected valid, got {[error.json_path for error in errors]}"


@pytest.mark.parametrize(
    ("schema_path", "fixture_path"),
    [
        (NORMALIZED_SCHEMA, path)
        for path in _json_fixture_paths("normalized-intake", "invalid")
    ]
    + [
        (WORKSPACE_SCHEMA, path)
        for path in _json_fixture_paths("workspace", "target", "invalid")
    ],
    ids=lambda item: item.name if isinstance(item, Path) else str(item),
)
def test_invalid_json_fixtures_fail_their_schema(schema_path: Path, fixture_path: Path) -> None:
    validator = Draft202012Validator(_load_schema(schema_path))
    payload = _load_json_strict(fixture_path)

    errors = sorted(validator.iter_errors(payload), key=lambda error: error.json_path)
    assert errors, f"{fixture_path}: expected schema failure"


@pytest.mark.parametrize(
    "fixture_path",
    _json_fixture_paths("normalized-intake", "strict-json"),
    ids=lambda path: path.name,
)
def test_strict_json_loading_rejects_non_standard_constants(fixture_path: Path) -> None:
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        _load_json_strict(fixture_path)


def test_strict_json_emission_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        json.dumps({"score": math.inf}, allow_nan=False)


@pytest.mark.parametrize("fixture_path", _toml_context_paths(), ids=lambda path: path.name)
def test_all_toml_context_fixtures_parse(fixture_path: Path) -> None:
    doc = _load_toml(fixture_path)

    assert isinstance(doc, dict), f"{fixture_path}: TOML fixture must parse to a table"


@pytest.mark.parametrize("fixture_path", _toml_context_paths(), ids=lambda path: path.name)
def test_context_target_entries_normalize_and_validate(fixture_path: Path) -> None:
    doc = _load_toml(fixture_path)
    validator = Draft202012Validator(_load_schema(WORKSPACE_SCHEMA))

    for collection, entry in _target_entries(doc, fixture_path):
        errors = sorted(validator.iter_errors(entry), key=lambda error: error.json_path)
        assert not errors, f"{fixture_path}:{collection}:{entry['path']}: {[error.json_path for error in errors]}"


def test_context_oracle_rejects_duplicate_membership() -> None:
    fixture = WORKSPACE_CONTEXT / "lifecycle.toml"
    doc = _load_toml(fixture)
    duplicate = dict(doc["ini-001"]["work"]["queue"][0])
    doc["backlog"]["open"].append(duplicate)

    assert _duplicate_paths(doc, fixture) == {duplicate["path"]}


def test_context_oracle_rejects_impossible_membership_status_pairs() -> None:
    fixture = WORKSPACE_CONTEXT / "lifecycle.toml"
    doc = _load_toml(fixture)
    draft = dict(doc["backlog"]["open"][0])
    assert draft["kind"] == "intent"
    assert _impossible_membership("ini-001.work.active", draft, _status_for(doc, draft["path"]))

    closed_without_resolution = {
        "path": "docs/product/defects/unresolved.md",
        "kind": "defect",
        "source": {"mode": "repo-origin", "ref": "docs/specs/login/spec.md"},
        "summary": "Unresolved defect in closed backlog.",
        "needs": [],
    }
    assert _impossible_membership("backlog.closed", closed_without_resolution, None)

    for case in doc["work_contract_cases"]:
        assert _valid_work_contract(
            case["collection"],
            case["kind"],
            case["status"],
            case["plan_exists"],
        ) is case["expected"]


def test_work_memberships_have_required_status_and_plan_evidence() -> None:
    fixture = WORKSPACE_CONTEXT / "lifecycle.toml"
    doc = _load_toml(fixture)
    memberships = _workspace_memberships(doc)

    for collection, expected_status in WORK_STATUSES.items():
        entry = memberships[f"ini-001.{collection}"][0]
        artifact = doc["spec_artifacts"][entry["path"]]
        assert artifact["Status"] == expected_status
        assert artifact["plan"] == Path(entry["path"]).with_name("plan.md").as_posix()
        assert _valid_work_contract(
            collection,
            entry["kind"],
            artifact["Status"],
            artifact["plan_exists"],
        )


def test_legacy_fixtures_are_scoped_non_dispatchable_and_do_not_promote() -> None:
    valid_path = WORKSPACE_CONTEXT / "legacy-valid.toml"
    valid_text = valid_path.read_text(encoding="utf-8")
    assert "# comment-rich backlog item:" in valid_text, f"{valid_path}: raw comment evidence missing"
    valid = tomllib.loads(valid_text)["legacy"]["valid"]
    invalid = _load_toml(WORKSPACE_CONTEXT / "legacy-invalid.toml")["legacy"]["invalid"]

    for collection, values in valid.items():
        for value in values:
            assert _legacy_classification(collection, value) == "legacy", f"{collection}:{value}: expected legacy"
            assert not (isinstance(value, dict) and set(value) == WORKSPACE_FIELD_SET), (
                f"{collection}:{value}: legacy shape must not be promoted to target entry"
            )
    for collection, values in invalid.items():
        for value in values:
            assert _legacy_classification(collection, value) == "invalid", f"{collection}:{value}: expected invalid"


def test_compaction_fixture_distinguishes_safe_and_unsafe_removal() -> None:
    fixture = WORKSPACE_CONTEXT / "compaction.toml"
    cases = {case["id"]: case for case in _load_toml(fixture)["compaction_cases"]}

    for case_id, case in cases.items():
        assert _compaction_decision(case) == case["expected"], f"{fixture}:{case_id}: compaction decision"
        assert case["canonical_artifact_deleted"] is False, f"{fixture}:{case_id}: never delete artifact"


def test_graph_ignores_comments_summary_and_order() -> None:
    base = _load_toml(WORKSPACE_CONTEXT / "graph-base.toml")
    variant = _load_toml(WORKSPACE_CONTEXT / "graph-variant.toml")

    assert _semantic_graph(base, WORKSPACE_CONTEXT / "graph-base.toml") == _semantic_graph(
        variant,
        WORKSPACE_CONTEXT / "graph-variant.toml",
    )


def test_minimal_intent_defect_authority_and_ready_without_spec_contracts() -> None:
    lifecycle = _load_toml(WORKSPACE_CONTEXT / "lifecycle.toml")
    authority = _load_toml(WORKSPACE_CONTEXT / "authority.toml")

    intent = lifecycle["intent_artifacts"]["docs/product/intents/workspace-routing.md"]
    assert set(intent) == {"Status", "Level", "Outcome", "Opportunity", "Assumptions", "Source"}
    assert intent["Status"] == "Draft"

    defects = lifecycle["defect_artifacts"]
    resolutions = set()
    for path, defect in defects.items():
        assert {"expected_behavior", "observed_behavior", "source", "citation"} <= set(defect), path
        assert "reproduction_evidence" in defect or "error_signature" in defect, path
        if "resolution" in defect:
            resolutions.add(defect["resolution"])
    assert resolutions == {"fixed", "declined", "superseded"}

    source_decisions = authority["artifact_source_decisions"]
    decisions = {decision["decision"] for decision in source_decisions}
    assert decisions == {"keep-local", "accept-source", "revise-both"}
    for decision in source_decisions:
        assert set(decision) == SOURCE_DECISION_FIELDS
        assert decision["source_revision"]
        assert decision["local_approver"]
        date.fromisoformat(decision["date"])
    for _collection, entry in _target_entries(authority, WORKSPACE_CONTEXT / "authority.toml"):
        assert "owned_fields" not in entry["source"]
        assert "source_decisions" not in entry["source"]

    memberships = _workspace_memberships(lifecycle)
    ready_brief = "docs/product/briefs/ready-without-specs.md"
    assert any(entry["path"] == ready_brief for entry in memberships["ini-001.brief_queue.ready"])
    assert not any(
        isinstance(entry, dict) and entry.get("source", {}).get("parent") == ready_brief
        for entries in memberships.values()
        for entry in entries
    )


@pytest.mark.skipif(not _temp_path_available(), reason="no usable temp directory for pytest tmp_path")
def test_repository_confinement_uses_resolved_paths_and_fails_closed_on_symlink_escape(tmp_path: Path) -> None:
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

    assert _inside_resolved(repo_root, in_root_target) is True
    assert _inside_resolved(repo_root, escape_link) is False


@pytest.mark.skipif(not _temp_path_available(), reason="no usable temp directory for pytest tmp_path")
def test_refresh_target_requires_an_existing_confined_file(tmp_path: Path) -> None:
    fixture = FIXTURE_ROOT / "normalized-intake/valid/refresh-repo-origin.json"
    payload = _load_json_strict(fixture)
    assert isinstance(payload, dict)
    relative_target = str(payload["refresh_target"])

    repo_root = tmp_path / "repo"
    target = repo_root / relative_target
    target.parent.mkdir(parents=True)
    target.write_text("# Existing canonical artifact\n", encoding="utf-8")
    assert _existing_confined_file(repo_root, relative_target) is True

    target.unlink()
    assert _existing_confined_file(repo_root, relative_target) is False

    external_target = tmp_path / "outside.md"
    external_target.write_text("# Outside repository\n", encoding="utf-8")
    try:
        target.symlink_to(external_target)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")
    assert _existing_confined_file(repo_root, relative_target) is False


def test_toml_non_bmp_unicode_round_trip_preserves_scalar_value() -> None:
    value = tomllib.loads('summary = "Keeps scalar 𐐷 as UTF-8"\n')["summary"]
    emitted = json.dumps({"summary": value}, ensure_ascii=False, allow_nan=False)

    assert "𐐷" in emitted
    assert "\\ud801" not in emitted
