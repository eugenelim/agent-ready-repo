"""Contract tests for semantic-surface resolution results."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT / "contracts/jsonschema/semantic-surface-resolution.schema.json"
)
FIXTURE_ROOT = (
    ROOT / "packs/core/tests/pack/fixtures/semantic-surface-resolution"
)
RESOLVER_PATH = (
    ROOT / "packs/core/.apm/skills/work-intake/scripts/surface_resolver.py"
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema() -> dict[str, object]:
    schema = _load_json(SCHEMA_PATH)
    assert isinstance(schema, dict)
    return schema


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema())


def _fixture_paths(kind: str) -> list[Path]:
    return sorted((FIXTURE_ROOT / kind).glob("*.json"))


def test_schema_is_valid_versioned_and_backlinked() -> None:
    schema = _schema()
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["contract_version"] == "semantic-surface-resolution.v1"
    assert schema["x-spec"] == ["docs/specs/semantic-surface-resolver/"]


def test_schema_and_runtime_share_the_exact_role_vocabulary() -> None:
    spec = importlib.util.spec_from_file_location(
        "semantic_surface_contract_runtime", RESOLVER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert tuple(_schema()["$defs"]["surfaceRole"]["enum"]) == module.SURFACE_ROLES


def test_resolver_source_matches_self_host_projections() -> None:
    source = RESOLVER_PATH.read_bytes()
    for adapter_root in (".agents", ".claude"):
        projected = (
            ROOT
            / adapter_root
            / "skills/work-intake/scripts/surface_resolver.py"
        )
        assert projected.read_bytes() == source


@pytest.mark.parametrize("fixture_path", _fixture_paths("valid"), ids=lambda p: p.stem)
def test_valid_resolution_fixtures(fixture_path: Path) -> None:
    _validator().validate(_load_json(fixture_path))


@pytest.mark.parametrize("fixture_path", _fixture_paths("invalid"), ids=lambda p: p.stem)
def test_invalid_resolution_fixtures(fixture_path: Path) -> None:
    errors = list(_validator().iter_errors(_load_json(fixture_path)))
    assert errors, f"{fixture_path.name} unexpectedly matched the schema"


def test_completion_matrix_expected_results_match_the_contract() -> None:
    matrix = _load_json(FIXTURE_ROOT / "completion-matrix.json")
    assert matrix["contract_version"] == "semantic-surface-resolution-fixtures.v1"
    assert len(matrix["cases"]) == 12
    for case in matrix["cases"]:
        _validator().validate(case["expected"])
