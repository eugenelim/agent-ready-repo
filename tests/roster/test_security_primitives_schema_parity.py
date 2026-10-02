"""Roster test: Slice 1 security-primitive records satisfy the canonical schemas.

For every record the Slice 1 scripts build or accept
(security-capability.v1, confined-file.v1, security-event.v1) this suite:

1. Loads each schema from ``contracts/delivery/`` and validates a record
   produced by the script against it using jsonschema Draft202012Validator,
   so schema drift is caught before merge.

2. Feeds four classes of schema-invalid record to each script's own
   ``validate_*_dict()`` function and asserts refusal with a stable denial code:
   - unknown authority-shaped field (a field not declared in the schema).
   - missing required field.
   - unknown schema_version major (a version the script does not recognise).
   - out-of-enum value (a value outside the declared enum for a property).

Both reads are anchored at the repo root via ``Path(__file__).resolve().parents[2]``.
The schemas are read from disk; embedded copies are not used here.  A broken
schema file or a module whose emitted records deviate from the schema fails this
test before any Slice 1 writer task begins.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_SCRIPTS = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)

_CONTRACTS = REPO_ROOT / "contracts" / "delivery"

# ── Schema paths ──────────────────────────────────────────────────────────────

_CAPABILITY_SCHEMA_PATH = _CONTRACTS / "security-capability.v1.schema.json"
_CONFINED_FILE_SCHEMA_PATH = _CONTRACTS / "confined-file.v1.schema.json"
_EVENT_SCHEMA_PATH = _CONTRACTS / "security-event.v1.schema.json"

# ── Module loader ─────────────────────────────────────────────────────────────


def _load_script(name: str, path: Path) -> ModuleType:
    """Load a work-loop script by path, unregistered, using the standard loader pattern."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None, (
            f"cannot create import spec for {path}"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_script("sc_roster", _SCRIPTS / "_security_capability.py")


@pytest.fixture(scope="module")
def confined_mutation() -> ModuleType:
    """_confined_mutation.py loaded by path."""
    return _load_script("cm_roster", _SCRIPTS / "_confined_mutation.py")


@pytest.fixture(scope="module")
def security_events() -> ModuleType:
    """_security_events.py loaded by path."""
    return _load_script("se_roster", _SCRIPTS / "_security_events.py")


# ── Schema loader ─────────────────────────────────────────────────────────────


def _load_schema(path: Path) -> dict:
    """Read and parse a JSON Schema from disk."""
    assert path.is_file(), f"schema not found: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonschema_validate(record: dict, schema: dict, *, label: str) -> None:
    """Validate record against schema; fail with a diagnostic on any error."""
    import jsonschema  # test-time only
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(record))
    assert not errors, (
        f"jsonschema validation failed for {label}:\n"
        + "\n".join(str(e.message) for e in errors)
    )


# ═══════════════════════════════════════════════════════════════════════════════
# security-capability.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestCapabilitySchemaParity:
    """Parity between _security_capability.py and security-capability.v1.schema.json."""

    def test_emitted_grant_satisfies_canonical_schema(
        self, security_capability: ModuleType
    ) -> None:
        """CapabilityGrant.as_dict() satisfies contracts/delivery/security-capability.v1.schema.json."""
        sc = security_capability
        schema = _load_schema(_CAPABILITY_SCHEMA_PATH)
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/work"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/work"],
            control_denies=[],
        )
        record = grant.as_dict()
        _jsonschema_validate(record, schema, label="security-capability.v1")

    def test_validate_refuses_unknown_schema_version(
        self, security_capability: ModuleType
    ) -> None:
        """validate_grant_dict refuses an out-of-enum schema_version (unknown major)."""
        sc = security_capability
        bad = {
            "schema_version": 99,  # not in enum [1]
            "grant_id": "g-unknown-ver",
            "roots": ["/work"],
            "operations": ["read"],
            "trust_class": "trusted-adapter",
            "writes": {"allowed_roots": []},
            "control_denies": [],
            "limits": {},
        }
        ok, code = sc.validate_grant_dict(bad)
        assert not ok, "validate_grant_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, security_capability: ModuleType
    ) -> None:
        """validate_grant_dict refuses a record missing a required field (grant_id)."""
        sc = security_capability
        bad = {
            "schema_version": 1,
            # grant_id omitted
            "roots": ["/work"],
            "operations": ["read"],
            "trust_class": "trusted-adapter",
            "writes": {"allowed_roots": []},
            "control_denies": [],
            "limits": {},
        }
        ok, code = sc.validate_grant_dict(bad)
        assert not ok, "validate_grant_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, security_capability: ModuleType
    ) -> None:
        """validate_grant_dict refuses an unknown authority-shaped field."""
        sc = security_capability
        bad = {
            "schema_version": 1,
            "grant_id": "g-extra-field",
            "roots": ["/work"],
            "operations": ["read"],
            "trust_class": "trusted-adapter",
            "writes": {"allowed_roots": []},
            "control_denies": [],
            "limits": {},
            "inject_escalation": "admin",  # not declared in schema
        }
        ok, code = sc.validate_grant_dict(bad)
        assert not ok, "validate_grant_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_empty_operations_enum(
        self, security_capability: ModuleType
    ) -> None:
        """validate_grant_dict refuses an empty operations list (schema: minItems=1)."""
        sc = security_capability
        bad = {
            "schema_version": 1,
            "grant_id": "g-empty-ops",
            "roots": ["/work"],
            "operations": [],  # violates schema minItems: 1
            "trust_class": "trusted-adapter",
            "writes": {"allowed_roots": []},
            "control_denies": [],
            "limits": {},
        }
        ok, code = sc.validate_grant_dict(bad)
        assert not ok, "validate_grant_dict must refuse empty operations"
        assert code == "denied-empty-operations"


# ═══════════════════════════════════════════════════════════════════════════════
# confined-file.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfinedFileSchemaParity:
    """Parity between _confined_mutation.py and confined-file.v1.schema.json."""

    def test_well_formed_record_satisfies_canonical_schema(
        self, confined_mutation: ModuleType
    ) -> None:
        """A valid confined-file.v1 record satisfies the canonical schema."""
        schema = _load_schema(_CONFINED_FILE_SCHEMA_PATH)
        record = {
            "schema_version": 1,
            "canonical_root": "/work",
            "relative_path": "subdir/audit.jsonl",
        }
        _jsonschema_validate(record, schema, label="confined-file.v1")
        ok, code = confined_mutation.validate_confined_file_dict(record)
        assert ok, f"validate_confined_file_dict rejected a valid record: {code}"
        assert code == "ok"

    def test_validate_refuses_unknown_schema_version(
        self, confined_mutation: ModuleType
    ) -> None:
        """validate_confined_file_dict refuses an out-of-enum schema_version."""
        bad = {
            "schema_version": 2,  # not in enum [1]
            "canonical_root": "/work",
            "relative_path": "file.txt",
        }
        ok, code = confined_mutation.validate_confined_file_dict(bad)
        assert not ok, "validate_confined_file_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, confined_mutation: ModuleType
    ) -> None:
        """validate_confined_file_dict refuses a record missing a required field."""
        bad = {
            "schema_version": 1,
            # canonical_root omitted
            "relative_path": "file.txt",
        }
        ok, code = confined_mutation.validate_confined_file_dict(bad)
        assert not ok, "validate_confined_file_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, confined_mutation: ModuleType
    ) -> None:
        """validate_confined_file_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "canonical_root": "/work",
            "relative_path": "file.txt",
            "inject_escalation": "bypass",  # additionalProperties: false in schema
        }
        ok, code = confined_mutation.validate_confined_file_dict(bad)
        assert not ok, "validate_confined_file_dict must refuse unknown authority field"
        assert code == "denied-unknown-authority-field"


# ═══════════════════════════════════════════════════════════════════════════════
# security-event.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityEventSchemaParity:
    """Parity between _security_events.py and security-event.v1.schema.json."""

    def test_emitted_event_satisfies_canonical_schema(
        self, security_events: ModuleType
    ) -> None:
        """SecurityEvent serialized with dataclasses.asdict satisfies the canonical schema."""
        se = security_events
        schema = _load_schema(_EVENT_SCHEMA_PATH)
        event = se.SecurityEvent(
            schema_version=1,
            operation_id="op-roster-parity-001",
            correlation_id="grant-roster-parity",
            event_type="capability-check",
            outcome="allowed",
            reason_code="allowed-file-write",
            timestamp="2026-10-01T00:00:00Z",
        )
        record = dataclasses.asdict(event)
        _jsonschema_validate(record, schema, label="security-event.v1")

    def test_validate_refuses_unknown_schema_version(
        self, security_events: ModuleType
    ) -> None:
        """validate_event_dict refuses an out-of-enum schema_version (unknown major)."""
        se = security_events
        bad = {
            "schema_version": 5,  # not in enum [1]
            "operation_id": "op-bad-version",
            "correlation_id": "c1",
            "event_type": "capability-check",
            "outcome": "allowed",
            "reason_code": "allowed-file-write",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = se.validate_event_dict(bad)
        assert not ok, "validate_event_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, security_events: ModuleType
    ) -> None:
        """validate_event_dict refuses a record missing a required field."""
        se = security_events
        bad = {
            "schema_version": 1,
            # operation_id omitted
            "correlation_id": "c1",
            "event_type": "capability-check",
            "outcome": "allowed",
            "reason_code": "allowed-file-write",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = se.validate_event_dict(bad)
        assert not ok, "validate_event_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, security_events: ModuleType
    ) -> None:
        """validate_event_dict refuses an unknown authority-shaped field."""
        se = security_events
        bad = {
            "schema_version": 1,
            "operation_id": "op-extra-field",
            "correlation_id": "c1",
            "event_type": "capability-check",
            "outcome": "allowed",
            "reason_code": "allowed-file-write",
            "timestamp": "2026-10-01T00:00:00Z",
            "inject_escalation": "bypass",  # additionalProperties: false in schema
        }
        ok, code = se.validate_event_dict(bad)
        assert not ok, "validate_event_dict must refuse unknown authority field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_out_of_enum_outcome(
        self, security_events: ModuleType
    ) -> None:
        """validate_event_dict refuses an outcome value outside the enum ["allowed","denied"]."""
        se = security_events
        bad = {
            "schema_version": 1,
            "operation_id": "op-bad-enum",
            "correlation_id": "c1",
            "event_type": "capability-check",
            "outcome": "maybe",  # not in enum ["allowed", "denied"]
            "reason_code": "allowed-file-write",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = se.validate_event_dict(bad)
        assert not ok, "validate_event_dict must refuse out-of-enum outcome"
        assert code == "denied-invalid-enum"
