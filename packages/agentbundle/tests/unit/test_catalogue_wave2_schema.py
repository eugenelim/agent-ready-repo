"""Stub: Wave 2 schema tests (Task 1 TDD).

All tests in this file fail until contracts/pack.schema.json gains the
[[pack.integrations]] array (AC1-AC4). A passing test suite here is Task 1's
Done-when criterion.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ── Schema paths ──────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[4]
_LIVE_SCHEMA_PATH = _REPO_ROOT / "contracts" / "pack.schema.json"
_BUNDLED_SCHEMA_PATH = (
    _REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "pack.schema.json"
)


def _load_schema() -> dict:
    return json.loads(_LIVE_SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate(doc: dict) -> list:
    try:
        import jsonschema
    except ImportError:
        pytest.skip("jsonschema not installed")
    schema = _load_schema()
    v = jsonschema.Draft7Validator(schema)
    return list(v.iter_errors(doc))


def _valid_entry() -> dict:
    return {
        "id": "test-integration",
        "pack": "other-pack",
        "kind": "input",
        "role": "Test role",
        "consumers": ["skill:work-loop"],
        "providers": ["skill:other-skill"],
        "when": "When active.",
        "purpose": "For testing.",
        "fallback": "Skips gracefully.",
    }


# ── Tests ─────────────────────────────────────────────────────────────────────


# STUB: AC1 — integrations property exists and is optional
def test_integrations_property_exists_in_schema():
    schema = _load_schema()
    pack_props = schema["properties"]["pack"]["properties"]
    assert "integrations" in pack_props
    assert "integrations" not in schema["properties"]["pack"].get("required", [])


# STUB: AC2 — pack without integrations still validates
def test_pack_without_integrations_validates():
    errors = _validate({"pack": {"name": "x", "version": "1.0.0"}})
    assert errors == []


# STUB: AC3 — valid integration entry validates
def test_valid_integration_entry_validates():
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [_valid_entry()]}}
    )
    assert errors == []


# STUB: AC3 — optional version field is accepted when present
def test_integration_with_version_validates():
    entry = {**_valid_entry(), "version": "^1.0.0"}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors == []


# STUB: AC3 — missing required field fails
def test_integration_missing_id_fails():
    entry = {k: v for k, v in _valid_entry().items() if k != "id"}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC3 — invalid kind fails
def test_integration_invalid_kind_fails():
    entry = {**_valid_entry(), "kind": "unknown"}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC3 — empty consumers array fails (minItems: 1)
def test_integration_empty_consumers_fails():
    entry = {**_valid_entry(), "consumers": []}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC3 — empty providers array fails (minItems: 1)
def test_integration_empty_providers_fails():
    entry = {**_valid_entry(), "providers": []}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC8 — empty `when` string fails (minLength: 1 required)
def test_integration_empty_when_fails():
    entry = {**_valid_entry(), "when": ""}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC8 — empty `purpose` string fails
def test_integration_empty_purpose_fails():
    entry = {**_valid_entry(), "purpose": ""}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC8 — empty `fallback` string fails
def test_integration_empty_fallback_fails():
    entry = {**_valid_entry(), "fallback": ""}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC1 — id with uppercase or underscore fails the ^[a-z0-9][a-z0-9-]*$ pattern
def test_integration_invalid_id_pattern_fails():
    for bad_id in ("Bad_ID", "has space", "_leading", ""):
        entry = {**_valid_entry(), "id": bad_id}
        errors = _validate(
            {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
        )
        assert errors != [], f"Expected validation error for id={bad_id!r}"


# STUB: AC1 — additionalProperties:false rejects unknown keys (typo-safety)
def test_integration_unknown_property_fails():
    entry = {**_valid_entry(), "bogus": "x"}
    errors = _validate(
        {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
    )
    assert errors != []


# STUB: AC1 — consumers/providers without valid type prefix fail
def test_integration_malformed_ref_prefix_fails():
    for bad_ref in ("garbage", "skill:", "unknowntype:foo", "skill/foo"):
        entry = {**_valid_entry(), "consumers": [bad_ref]}
        errors = _validate(
            {"pack": {"name": "x", "version": "1.0.0", "integrations": [entry]}}
        )
        assert errors != [], f"Expected validation error for consumers=[{bad_ref!r}]"


# STUB: AC4 — bundled schema is byte-identical to live contracts/pack.schema.json
def test_parity_bytes_identical():
    live = _LIVE_SCHEMA_PATH.read_bytes()
    bundled = _BUNDLED_SCHEMA_PATH.read_bytes()
    assert live == bundled, (
        "Schema parity broken — run tools/catalogue/check_contract_parity.py to diagnose"
    )
