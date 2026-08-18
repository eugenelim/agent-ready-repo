"""Contract tests for SKILL.md compatibility frontmatter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[4]
CANONICAL = ROOT / "contracts" / "skill.schema.json"
PACKAGED = ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "skill.schema.json"


def _schemas() -> list[tuple[str, dict[str, Any]]]:
    schemas = []
    if CANONICAL.is_file():
        schemas.append(
            ("canonical", json.loads(CANONICAL.read_text(encoding="utf-8")))
        )
    schemas.append(("packaged", json.loads(PACKAGED.read_text(encoding="utf-8"))))
    return schemas


def _base(value: Any) -> dict[str, Any]:
    return {
        "name": "demo-skill",
        "description": "Demo skill",
        "compatibility": {"target": value},
    }


@pytest.mark.parametrize(("label", "schema"), _schemas())
def test_skill_schema_is_draft_2020_12(label: str, schema: dict[str, Any]) -> None:
    assert label
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


@pytest.mark.parametrize("value", [
    "x" * 1024,
    True,
    False,
    9007199254740991,
    -9007199254740991,
    ["x" * 1024, True, False, 9007199254740991, -9007199254740991],
])
def test_skill_compatibility_accepts_show_compatible_values(value: Any) -> None:
    for label, schema in _schemas():
        validator = Draft202012Validator(schema)
        validator.validate(_base(value)), label


@pytest.mark.parametrize("value", [
    "x" * 1025,
    9007199254740992,
    -9007199254740992,
    1.5,
    {"nested": "value"},
    ["ok", {"nested": "value"}],
    ["ok"] * 257,
])
def test_skill_compatibility_rejects_show_incompatible_values(value: Any) -> None:
    for label, schema in _schemas():
        validator = Draft202012Validator(schema)
        assert list(validator.iter_errors(_base(value))), label


def test_skill_compatibility_rejects_oversized_object_and_property_name() -> None:
    for label, schema in _schemas():
        validator = Draft202012Validator(schema)
        oversized = _base("value")
        oversized["compatibility"] = {f"k{i}": "value" for i in range(257)}
        assert list(validator.iter_errors(oversized)), label

        long_key = _base("value")
        long_key["compatibility"] = {"k" * 1025: "value"}
        assert list(validator.iter_errors(long_key)), label


def test_skill_schema_rejects_unknown_top_level_keys() -> None:
    for label, schema in _schemas():
        instance = _base("value")
        instance["unexpected"] = True
        assert list(Draft202012Validator(schema).iter_errors(instance)), label
