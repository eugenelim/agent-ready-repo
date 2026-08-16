"""Repository-level conformance for the project-knowledge capture contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

CATALOGUE_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_NAME = "knowledge-captured-observation.schema.json"
PUBLIC_SCHEMA = CATALOGUE_ROOT / "contracts" / "jsonschema" / SCHEMA_NAME
BUNDLED_SCHEMA = (
    CATALOGUE_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / SCHEMA_NAME
)


def _valid_capture_request(**overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "contract_version": "knowledge-captured-observation.v1",
        "lesson": "Prefer the repository-owned contract before adding a local format.",
        "kind": "pattern",
        "project_scope": {"paths": ["docs/architecture"], "audience": "project"},
        "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
        "destination_hint": {
            "type": "topic",
            "path": "docs/knowledge/topics/public-contracts.json",
        },
        "producer": {"workflow": "work-loop", "workflow_version": "2.5.9"},
        "semantic_gate": {
            "name": "verified-slice",
            "artifact": "docs/specs/example/plan.md",
        },
        "provenance": {
            "sources": [
                {
                    "path": "docs/architecture/overview.md",
                    "line_start": 10,
                    "line_end": 20,
                }
            ]
        },
        "freshness_anchor": {
            "path": "docs/architecture/overview.md",
            "digest": {
                "kind": "sha256-bytes-v1",
                "sha256": "a" * 64,
                "byte_length": 100,
            },
        },
        "observed_at": "2026-08-13T12:34:56Z",
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
        "friction": {
            "failed_attempts": 3,
            "summary": "The contract authority took several attempts to locate.",
        },
        "verification_route": {
            "command": "python3 tools/lint-conformance-portability.py --root .",
            "path": "tools/lint-conformance-portability.py",
        },
    }
    request.update(overrides)
    return request


def test_public_capture_contract_is_strict_versioned_and_bundled() -> None:
    schema = json.loads(PUBLIC_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    assert schema["additionalProperties"] is False
    assert schema["contract_version"] == "knowledge-captured-observation.v1"
    assert "capture_id" not in schema["properties"]
    assert list(validator.iter_errors(_valid_capture_request())) == []

    unknown_field = _valid_capture_request()
    unknown_field["extra"] = "refuse"
    assert list(validator.iter_errors(unknown_field))

    producer_capture_id = _valid_capture_request()
    producer_capture_id["capture_id"] = "kco-202608-" + ("0" * 64)
    assert list(validator.iter_errors(producer_capture_id))

    missing_provenance = _valid_capture_request()
    del missing_provenance["provenance"]
    assert list(validator.iter_errors(missing_provenance))

    assert list(validator.iter_errors(_valid_capture_request(lesson="x" * 2001)))
    assert PUBLIC_SCHEMA.read_bytes() == BUNDLED_SCHEMA.read_bytes()
