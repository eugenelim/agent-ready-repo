"""Repository-level conformance for the project-knowledge capture contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_NAME = "knowledge-captured-observation.schema.json"
PUBLIC_SCHEMA = ROOT / "contracts" / "jsonschema" / SCHEMA_NAME
BUNDLED_SCHEMA = (
    ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / SCHEMA_NAME
)
PACK_SUPPORT = (
    ROOT
    / "packs"
    / "core"
    / "tests"
    / "skills"
    / "project-knowledge"
    / "knowledge_test_support.py"
)


def _load_pack_support():
    spec = importlib.util.spec_from_file_location(
        "project_knowledge_contract_test_support", PACK_SUPPORT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_public_capture_contract_is_strict_versioned_and_bundled() -> None:
    schema = json.loads(PUBLIC_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    support = _load_pack_support()

    assert schema["additionalProperties"] is False
    assert schema["contract_version"] == "knowledge-captured-observation.v1"
    assert "capture_id" not in schema["properties"]
    assert list(validator.iter_errors(support.valid_capture_request())) == []
    assert list(
        validator.iter_errors(support.capture_request_with_unknown_field())
    )
    assert list(
        validator.iter_errors(support.capture_request_with_producer_supplied_capture_id())
    )
    assert list(
        validator.iter_errors(support.capture_request_without_provenance())
    )
    assert list(
        validator.iter_errors(support.capture_request_with_oversized_lesson())
    )
    assert PUBLIC_SCHEMA.read_bytes() == BUNDLED_SCHEMA.read_bytes()
