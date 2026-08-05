"""T1: pack.schema.json — local scope schema constraints (RFC-0080 AC1).

Verifies:
  AC1a — allowed-scopes items enum includes "local".
  AC1b — allOf constraint: allowed-scopes = ["local"] (no "repo") fails validation.
  AC1c — allOf constraint: allowed-scopes = ["user", "local"] (has "local" but not
          "repo") fails validation.
  AC1d — allowed-scopes = ["repo", "local"] passes validation.
  AC1e — existing packs (repo-only allowed-scopes) still pass.
  parity — both schema copies are byte-identical.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

REPO_ROOT = Path(__file__).resolve().parents[4]
PACK_SCHEMA_PATH = REPO_ROOT / "contracts" / "pack.schema.json"
DATA_PACK_SCHEMA_PATH = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "pack.schema.json"
)


def _load_schema() -> dict:
    return json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))


def _base_pack(allowed_scopes: list[str]) -> dict:
    """Minimal valid pack manifest with the given allowed-scopes."""
    return {
        "pack": {
            "name": "test-pack",
            "version": "0.1.0",
            "install": {
                "default-scope": "repo",
                "allowed-scopes": allowed_scopes,
            },
        }
    }


def _validate(instance: dict) -> list[str]:
    """Validate *instance* against the pack schema. Returns a list of error messages."""
    if not _HAS_JSONSCHEMA:
        pytest.skip("jsonschema not installed")
    schema = _load_schema()
    v = jsonschema.Draft202012Validator(schema)
    return [str(e.message) for e in sorted(v.iter_errors(instance), key=lambda e: str(e.path))]


def test_local_in_allowed_scopes_items():
    """AC1a: 'local' is a valid item in allowed-scopes."""
    errors = _validate(_base_pack(["repo", "local"]))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_local_without_repo_fails():
    """AC1b: allowed-scopes = ['local'] (no 'repo') fails the allOf constraint."""
    errors = _validate(_base_pack(["local"]))
    assert errors, "Expected validation error for allowed-scopes=['local'] without 'repo'"


def test_user_and_local_without_repo_fails():
    """AC1c: allowed-scopes = ['user', 'local'] (no 'repo') fails."""
    errors = _validate(_base_pack(["user", "local"]))
    assert errors, "Expected validation error for ['user', 'local'] without 'repo'"


def test_repo_and_local_passes():
    """AC1d: allowed-scopes = ['repo', 'local'] passes."""
    errors = _validate(_base_pack(["repo", "local"]))
    assert errors == [], f"Expected no errors for ['repo', 'local'], got: {errors}"


def test_repo_only_still_passes():
    """AC1e: existing repo-only packs are unaffected."""
    errors = _validate(_base_pack(["repo"]))
    assert errors == [], f"Expected no errors for existing repo-only pack, got: {errors}"


def test_schema_parity():
    """AC1: both schema copies are byte-identical."""
    assert PACK_SCHEMA_PATH.exists()
    assert DATA_PACK_SCHEMA_PATH.exists()
    assert PACK_SCHEMA_PATH.read_bytes() == DATA_PACK_SCHEMA_PATH.read_bytes(), (
        "contracts/pack.schema.json and agentbundle/_data/pack.schema.json are not byte-identical"
    )
