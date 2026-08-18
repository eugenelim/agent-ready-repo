"""Contract fixtures for the OKF authoring JSON Schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[5]
SCHEMA_ROOT = ROOT / "contracts" / "jsonschema"
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "contracts"
SCHEMAS = {
    "extension": SCHEMA_ROOT / "okf-agentbundle-extension-v1.schema.json",
    "pack": SCHEMA_ROOT / "okf-pack-profile-v1.schema.json",
}


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_validator(name: str) -> Draft202012Validator:
    schema = _load_json(SCHEMAS[name])
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _fixture_schema_name(path: Path) -> str:
    if path.name.startswith("extension-"):
        return "extension"
    if path.name.startswith("pack-"):
        return "pack"
    raise AssertionError(f"fixture name must start with pack- or extension-: {path}")


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_okf_contract_schemas_are_draft_2020_12(name: str) -> None:
    _schema_validator(name)


@pytest.mark.parametrize("fixture", sorted((FIXTURE_ROOT / "valid").glob("*.json")))
def test_okf_contract_positive_examples_validate(fixture: Path) -> None:
    validator = _schema_validator(_fixture_schema_name(fixture))

    errors = sorted(validator.iter_errors(_load_json(fixture)), key=str)

    assert errors == []


@pytest.mark.parametrize("fixture", sorted((FIXTURE_ROOT / "invalid").glob("*.json")))
def test_okf_contract_negative_examples_reject(fixture: Path) -> None:
    validator = _schema_validator(_fixture_schema_name(fixture))

    errors = sorted(validator.iter_errors(_load_json(fixture)), key=str)

    assert errors, f"{fixture.name} unexpectedly validated"
