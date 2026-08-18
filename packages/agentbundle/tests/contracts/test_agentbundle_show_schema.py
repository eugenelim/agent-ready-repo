"""Contract tests for agentbundle show --format json responses."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
CANONICAL_SCHEMA = ROOT / "contracts" / "jsonschema" / "agentbundle-show.schema.json"
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "show_contract"
SCHEMA_PATH = FIXTURES / "agentbundle-show.schema.json"


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _invalid(instance: dict[str, Any]) -> list[str]:
    return [error.message for error in _validator().iter_errors(instance)]


def _set_path(instance: dict[str, Any], path: tuple[str | int, ...], value: Any) -> None:
    target: Any = instance
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value


def _delete_path(instance: dict[str, Any], path: tuple[str | int, ...]) -> None:
    target: Any = instance
    for part in path[:-1]:
        target = target[part]
    del target[path[-1]]


def test_schema_is_draft_2020_12_and_links_to_spec() -> None:
    schema = _load_schema()

    Draft202012Validator.check_schema(schema)

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert "docs/specs/okf-catalogue-discovery/" in schema["x-spec"]


def test_sdist_schema_fixture_matches_canonical_contract_when_available() -> None:
    if CANONICAL_SCHEMA.is_file():
        assert SCHEMA_PATH.read_bytes() == CANONICAL_SCHEMA.read_bytes()


@pytest.mark.parametrize("fixture_name", ["catalogue.json", "installed_state.json"])
def test_success_variants_validate(fixture_name: str) -> None:
    _validator().validate(_fixture(fixture_name))


@pytest.mark.parametrize("key", [
    "name",
    "version",
    "description",
    "skills",
    "agents",
    "integrations",
    "source",
    "pack_metadata",
    "skill_metadata",
    "knowledge",
])
def test_every_top_level_key_is_required(key: str) -> None:
    instance = _fixture("catalogue.json")
    del instance[key]

    assert _invalid(instance)


def test_top_level_response_is_closed() -> None:
    instance = _fixture("catalogue.json")
    instance["unexpected"] = "value"

    assert _invalid(instance)


@pytest.mark.parametrize(("path", "value"), [
    (("name",), ""),
    (("version",), 1),
    (("description",), 1),
    (("skills",), ["demo-router", "demo-router"]),
    (("skills", 0), 1),
    (("agents",), ["demo-agent", "demo-agent"]),
    (("integrations",), [{}]),
    (("source",), "cache"),
    (("pack_metadata", "categories"), [1]),
    (("pack_metadata", "keywords"), ["x"] * 257),
    (("pack_metadata", "license"), 1),
    (("skill_metadata", 0, "name"), 1),
    (("skill_metadata", 0, "description"), ""),
    (("skill_metadata", 0, "license"), 1),
    (("skill_metadata", 0, "profile"), "wrong-profile"),
    (("skill_metadata", 0, "digest"), "sha256:not-a-digest"),
    (("skill_metadata", 0, "generated_from"), "/absolute/path.md"),
    (("skill_metadata", 0, "boundaries"), ["x"] * 257),
    (("knowledge", 0, "format"), "markdown"),
    (("knowledge", 0, "okf_version"), "0.3"),
    (("knowledge", 0, "router_skill"), ""),
    (("knowledge", 0, "content_license"), ""),
    (("knowledge", 0, "concept_count"), -1),
    (("knowledge", 0, "digest"), "sha256:not-a-digest"),
])
def test_field_types_and_bounds_reject_drift(
    path: tuple[str | int, ...], value: Any
) -> None:
    instance = _fixture("catalogue.json")
    _set_path(instance, path, value)

    assert _invalid(instance)


@pytest.mark.parametrize("key", [
    "id",
    "pack",
    "kind",
    "role",
    "consumers",
    "providers",
    "when",
    "purpose",
    "fallback",
])
def test_integration_required_keys_except_version(key: str) -> None:
    instance = _fixture("catalogue.json")
    _delete_path(instance, ("integrations", 0, key))

    assert _invalid(instance)


def test_integration_version_is_optional_but_bounded_when_present() -> None:
    instance = _fixture("catalogue.json")
    _validator().validate(instance)

    instance["integrations"][0]["version"] = "1.0.0"
    _validator().validate(instance)

    instance["integrations"][0]["version"] = 1
    assert _invalid(instance)


@pytest.mark.parametrize("field", ["pack_metadata", "skill_metadata", "knowledge"])
def test_catalogue_source_requires_rich_metadata_objects(field: str) -> None:
    instance = _fixture("catalogue.json")
    instance[field] = None

    assert _invalid(instance)


def test_installed_state_variant_forces_degraded_metadata() -> None:
    instance = _fixture("installed_state.json")
    instance["pack_metadata"] = {"categories": [], "keywords": [], "license": None}

    assert _invalid(instance)


@pytest.mark.parametrize(("path", "value"), [
    (("version",), "1.0.0"),
    (("description",), "Installed description"),
    (("integrations",), [_fixture("catalogue.json")["integrations"][0]]),
    (("skill_metadata",), []),
    (("knowledge",), []),
])
def test_installed_state_rejects_catalogue_only_values(
    path: tuple[str | int, ...], value: Any
) -> None:
    instance = _fixture("installed_state.json")
    _set_path(instance, path, value)

    assert _invalid(instance)


@pytest.mark.parametrize("field", ["pack_metadata", "skill_metadata", "knowledge"])
def test_catalogue_empty_pack_values_are_valid(field: str) -> None:
    instance = _fixture("catalogue.json")
    if field == "pack_metadata":
        instance[field] = {"categories": [], "keywords": [], "license": None}
    else:
        instance[field] = []

    _validator().validate(instance)


@pytest.mark.parametrize("value", [
    "x" * 1024,
    True,
    False,
    9007199254740991,
    -9007199254740991,
    ["x" * 1024, True, False, 9007199254740991, -9007199254740991],
])
def test_compatibility_values_accept_allowed_scalar_and_list_shapes(value: Any) -> None:
    instance = _fixture("catalogue.json")
    instance["skill_metadata"][0]["compatibility"] = {"target": value}

    _validator().validate(instance)


@pytest.mark.parametrize("value", [
    "x" * 1025,
    9007199254740992,
    -9007199254740992,
    1.5,
    {"nested": "value"},
    ["ok", {"nested": "value"}],
    ["ok"] * 257,
])
def test_compatibility_rejects_unbounded_or_nested_values(value: Any) -> None:
    instance = _fixture("catalogue.json")
    instance["skill_metadata"][0]["compatibility"] = {"target": value}

    assert _invalid(instance)


def test_compatibility_rejects_oversized_object_and_property_name() -> None:
    instance = _fixture("catalogue.json")
    instance["skill_metadata"][0]["compatibility"] = {
        f"k{i}": "value" for i in range(257)
    }
    assert _invalid(instance)

    instance = _fixture("catalogue.json")
    instance["skill_metadata"][0]["compatibility"] = {"k" * 1025: "value"}
    assert _invalid(instance)


@pytest.mark.parametrize("field", [
    "name",
    "description",
    "license",
    "compatibility",
    "generated_from",
    "profile",
    "digest",
    "boundaries",
])
def test_skill_metadata_is_required_and_closed(field: str) -> None:
    instance = _fixture("catalogue.json")
    _delete_path(instance, ("skill_metadata", 0, field))
    assert _invalid(instance)

    instance = _fixture("catalogue.json")
    instance["skill_metadata"][0]["extra"] = "value"
    assert _invalid(instance)


@pytest.mark.parametrize("field", [
    "id",
    "format",
    "okf_version",
    "router_skill",
    "content_license",
    "concept_count",
    "digest",
])
def test_knowledge_metadata_is_required_and_closed(field: str) -> None:
    instance = _fixture("catalogue.json")
    _delete_path(instance, ("knowledge", 0, field))
    assert _invalid(instance)

    instance = _fixture("catalogue.json")
    instance["knowledge"][0]["extra"] = "value"
    assert _invalid(instance)


def test_generated_skill_marker_fields_are_all_or_none() -> None:
    instance = _fixture("catalogue.json")
    instance["skill_metadata"][0]["digest"] = None
    assert _invalid(instance)

    instance = _fixture("catalogue.json")
    instance["skill_metadata"][2]["profile"] = "agentbundle-okf/v1"
    assert _invalid(instance)
