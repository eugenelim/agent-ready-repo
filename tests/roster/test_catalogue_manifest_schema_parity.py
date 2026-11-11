"""The published manifest JSON Schema agrees with the archive verifier."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.archive import _check_manifest_schema
from jsonschema import Draft202012Validator
from tests.unit.test_catalogue_manifest_schema import AGREEMENT_CASES

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads(
    (ROOT / "contracts/catalogue-manifest.schema.json").read_text(encoding="utf-8")
)


def _verifier_accepts(manifest: object) -> bool:
    """True when the verifier yields no manifest-schema rejection."""
    return not any(
        d.code in {"CAT-V-ARC-011", "CAT-V-ARC-019"} for d in _check_manifest_schema(manifest)
    )


@pytest.mark.parametrize("name", sorted(AGREEMENT_CASES))
def test_json_schema_agrees_with_verifier(name: str) -> None:
    manifest = AGREEMENT_CASES[name]
    schema_accepts = not list(Draft202012Validator(SCHEMA).iter_errors(manifest))
    assert schema_accepts == _verifier_accepts(manifest)
