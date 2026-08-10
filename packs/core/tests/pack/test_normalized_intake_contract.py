"""Contract tests for normalized work-intake records."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = ROOT / "contracts/jsonschema/normalized-intake.schema.json"
FIXTURE_ROOT = (
    Path(__file__).resolve().parent
    / "fixtures/work-intake-contracts/normalized-intake"
)


def _load_json(path: Path) -> object:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard JSON constant: {value}")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def _schema() -> dict[str, object]:
    schema = _load_json(SCHEMA_PATH)
    assert isinstance(schema, dict)
    return schema


def _fixture_paths(kind: str) -> list[Path]:
    return sorted((FIXTURE_ROOT / kind).glob("*.json"))


def test_schema_is_valid_and_versioned() -> None:
    schema = _schema()

    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["contract_version"] == "normalized-intake.v1"
    assert schema["x-spec"] == [
        "docs/specs/normalized-intake-workspace-contracts/"
    ]


@pytest.mark.parametrize("fixture_path", _fixture_paths("valid"), ids=lambda p: p.stem)
def test_valid_normalized_intake_fixtures(fixture_path: Path) -> None:
    validator = Draft202012Validator(_schema())
    payload = _load_json(fixture_path)

    validator.validate(payload)


@pytest.mark.parametrize("fixture_path", _fixture_paths("invalid"), ids=lambda p: p.stem)
def test_invalid_normalized_intake_fixtures(fixture_path: Path) -> None:
    validator = Draft202012Validator(_schema())
    payload = _load_json(fixture_path)

    errors = sorted(validator.iter_errors(payload), key=lambda error: error.json_path)
    assert errors, f"{fixture_path.name} unexpectedly matched the normalized intake schema"


@pytest.mark.parametrize("fixture_path", _fixture_paths("strict-json"), ids=lambda p: p.stem)
def test_fixture_loading_rejects_non_standard_json_constants(fixture_path: Path) -> None:
    with pytest.raises(ValueError, match="non-standard JSON constant"):
        _load_json(fixture_path)


def test_json_emission_refuses_non_finite_values() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        json.dumps({"score": math.nan}, allow_nan=False)
