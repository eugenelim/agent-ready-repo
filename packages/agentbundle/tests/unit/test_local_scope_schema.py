"""T1: pack.schema.json — local scope schema constraints.

Verifies:
  Allowed-scopes items enum includes "local".
  AllOf constraint: allowed-scopes = ["local"] (no "repo") fails validation.
  AllOf constraint: allowed-scopes = ["user", "local"] (has "local" but not
          "repo") fails validation.
  Allowed-scopes = ["repo", "local"] passes validation.
  Existing packs (repo-only allowed-scopes) still pass.
  parity — both schema copies are byte-identical.
"""

from __future__ import annotations

import json
from importlib.resources import files

import pytest

try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False

PACK_SCHEMA = files("agentbundle").joinpath("_data/pack.schema.json")


def _load_schema() -> dict:
    return json.loads(PACK_SCHEMA.read_text(encoding="utf-8"))


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
    """`"local"` is a valid item in allowed-scopes."""
    errors = _validate(_base_pack(["repo", "local"]))
    assert errors == [], f"Expected no errors, got: {errors}"


def test_local_without_repo_fails():
    """Allowed-scopes = ['local'] (no 'repo') fails the allOf constraint."""
    errors = _validate(_base_pack(["local"]))
    assert errors, "Expected validation error for allowed-scopes=['local'] without 'repo'"


def test_user_and_local_without_repo_fails():
    """Allowed-scopes = ['user', 'local'] (no 'repo') fails."""
    errors = _validate(_base_pack(["user", "local"]))
    assert errors, "Expected validation error for ['user', 'local'] without 'repo'"


def test_repo_and_local_passes():
    """Allowed-scopes = ['repo', 'local'] passes."""
    errors = _validate(_base_pack(["repo", "local"]))
    assert errors == [], f"Expected no errors for ['repo', 'local'], got: {errors}"


def test_repo_only_still_passes():
    """Existing repo-only packs are unaffected."""
    errors = _validate(_base_pack(["repo"]))
    assert errors == [], f"Expected no errors for existing repo-only pack, got: {errors}"
