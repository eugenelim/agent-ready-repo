"""Delete each required caller field without deriving contradictions from absence."""

from __future__ import annotations

import copy
import importlib.util
import json
import socket
import sys
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / ".apm/skills/generate-iac/scripts/plan_bundle.py"
EXAMPLE = Path(__file__).resolve().parents[3] / ".apm/skills/generate-iac/assets/native-adr-caller"
SPEC = importlib.util.spec_from_file_location(
    "iac_terraform_generate_iac_plan_bundle_deletions", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
DATA = MODULE.parse_json(MODULE.read_manifest(EXAMPLE, "iac-plan-bundle.v1.json"))
POLICY = MODULE.parse_json(MODULE.read_manifest(EXAMPLE, "trusted-policy.json"))
NOW = "2026-01-01T12:30:00Z"
SCHEMA_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/generate-iac/references"
SCHEMA = MODULE.parse_json(MODULE.read_manifest(SCHEMA_ROOT, "iac-plan-bundle.v1.schema.json"))
DATA["effects"]["changes"] = [{"address": "example.item", "actions": ["create"]}]
DATA["effects"]["stateful_impacts"] = [
    {"address": "example.item", "impact": "example", "reversibility": "reversible"}
]

NEW_WORKSPACE_DATA = copy.deepcopy(DATA)
NEW_WORKSPACE_DATA["state"] = {
    "backend": "local",
    "workspace": "example-workspace",
    "new_workspace": "native-decision",
}
NEW_WORKSPACE_DATA["source"] = {"repository": "example-repository", "snapshot": "native-decision"}
VARIANTS = {"existing-state": DATA, "new-workspace": NEW_WORKSPACE_DATA}


def required_paths(
    value: Any, schema: dict[str, Any], path: tuple[str | int, ...] = ()
) -> Iterator[tuple[str | int, ...]]:
    """Expand the published required field tables across every caller record."""
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[1]
        if name == "Component":
            name = "ImageComponent" if value["kind"] == "oci-image" else "PlanComponent"
        schema = SCHEMA["$defs"][name]
    if isinstance(value, dict):
        fields = list(schema["required"])
        if "revision" in value or "snapshot" in value:
            fields.append("revision" if "revision" in value else "snapshot")
        if "lineage" in value or "new_workspace" in value:
            fields.extend(["lineage", "serial"] if "lineage" in value else ["new_workspace"])
        for key in fields:
            assert key in value, (path, key)
            yield (*path, key)
            yield from required_paths(value[key], schema["properties"][key], (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from required_paths(child, schema["items"], (*path, index))


def field_path(path: tuple[str | int, ...]) -> str:
    """Render a concrete schema path for the result contract."""
    return "$" + "".join(f"[{part}]" if isinstance(part, int) else "." + part for part in path)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: Any) -> None:
    """Fail on any attempted fetch, including evidence validation."""

    def refuse(*args: Any, **kwargs: Any) -> None:
        """Refuse network access."""
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)


def validate(data: dict[str, Any]) -> dict[str, Any]:
    """Exercise the encoded reader and real local evidence."""
    raw = json.dumps(data).encode()
    return MODULE.validate_bytes(raw, root=EXAMPLE, policy=POLICY, now=NOW)


@pytest.mark.parametrize(
    "variant,path",
    [
        pytest.param(variant, path, id=variant + ":" + field_path(path))
        for variant, data in VARIANTS.items()
        for path in required_paths(data, SCHEMA)
    ],
)
def test_required_field_deletion(variant: str, path: tuple[str | int, ...]) -> None:
    """Each isolated absence yields only its own missing-field issue."""
    data = copy.deepcopy(VARIANTS[variant])
    parent = data
    for part in path[:-1]:
        parent = parent[part]
    del parent[path[-1]]
    result = validate(data)
    assert result["status"] == "incomplete", result
    expected_path = path[:-1] if path[-1] in {"revision", "snapshot"} else path
    expected_paths = (
        [("state", "lineage"), ("state", "serial")]
        if path == ("state", "new_workspace")
        else [expected_path]
    )
    assert result["issues"] == [
        {"code": "missing-field", "path": field_path(item)} for item in expected_paths
    ], result


@pytest.mark.parametrize("missing", [False, True])
def test_present_wrong_subject_stays_invalid(missing: bool) -> None:
    """Independent absence cannot mask a contradictory present identity."""
    data = copy.deepcopy(DATA)
    data["checks"][0]["subjects"][0]["id"] = "wrong-subject"
    if missing:
        del data["target"]["account"]
    result = validate(data)
    assert result["status"] == "invalid", result
    assert {"code": "subject-mismatch", "path": "$.checks[0].subjects"} in result["issues"]
    if missing:
        assert {"code": "missing-field", "path": "$.target.account"} in result["issues"]


@pytest.mark.parametrize("variant", VARIANTS)
def test_complete_table_fixture(variant: str) -> None:
    """Every expanded caller variant starts valid before deleting fields."""
    assert validate(VARIANTS[variant])["status"] == "valid"


def test_partial_subject_does_not_mask_present_contradiction() -> None:
    """Assess complete subjects even when another subject lacks its identity."""
    data = copy.deepcopy(DATA)
    data["checks"][0]["subjects"] = [
        {"sha256": data["checks"][0]["subjects"][0]["sha256"]},
        {"id": "wrong-subject", "sha256": "sha256:" + "0" * 64},
    ]
    result = validate(data)
    assert result["status"] == "invalid", result
    assert {"code": "subject-mismatch", "path": "$.checks[0].subjects"} in result["issues"]
