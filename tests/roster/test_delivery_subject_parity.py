"""Roster test: T6 delivery-subject.v1 records satisfy the canonical schema.

For every record the T6 legacy subject provider and runtime-neutral projector
build (delivery-subject.v1) this suite:

1. Loads the schema from ``contracts/delivery/`` and validates a record produced
   by ``_subject_projection.project_delivery_subject()`` against it using
   jsonschema Draft202012Validator, so schema drift is caught before merge.

2. Feeds four classes of schema-invalid record to ``validate_subject_dict()``
   and asserts refusal with a stable denial code:
   - unknown schema_version (unknown major).
   - missing required field.
   - unknown authority-shaped field (a field not declared in the schema).
   - non-dict input (caught by the ``denied-not-a-dict`` code; delivery-subject.v1
     defines no enum constraints, so this class replaces the out-of-enum check).

Both reads are anchored at the repo root via ``Path(__file__).resolve().parents[2]``.
The schema is read from disk; embedded copies are not used here.  A broken schema
file or a module whose emitted records deviate from the schema fails this test
before any T6 writer task begins.

Parity rule (verification-ledger.md §Script-versus-schema parity): every task
that adds a module building delivery records carries parity tests.  This file
satisfies that obligation for T6's ``_subject_projection.py`` and
``_subject_source.py``.
"""

from __future__ import annotations

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

_SUBJECT_SCHEMA_PATH = _CONTRACTS / "delivery-subject.v1.schema.json"


# ── Module loader ─────────────────────────────────────────────────────────────


def _load_script(name: str, path: Path) -> ModuleType:
    """Load a work-loop script by path, unregistered, using the standard loader pattern."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sp = importlib.util.spec_from_file_location(name, str(path))
        assert sp is not None and sp.loader is not None, (
            f"cannot create import spec for {path}"
        )
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def projection() -> ModuleType:
    """_subject_projection.py — runtime-neutral projector, loaded by path."""
    return _load_script("sp_roster", _SCRIPTS / "_subject_projection.py")


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


# ── Shared valid record ────────────────────────────────────────────────────────

_VALID_MANIFEST_PAIRS: tuple[tuple[str, str], ...] = (
    ("src/main.py", "a" * 64),
    ("src/util.py", "b" * 64),
)

_VALID_EXCLUSIONS: tuple[str, ...] = (".git", "docs/specs/test-feature/")

_VALID_SUBJECT_KWARGS: dict = {
    "subject_id": "parity-roster-001",
    "base_ref": "deadbeef" * 5,
    "result_ref": "deadbeef" * 5,
    "spec_path": "docs/specs/test-feature/spec.md",
    "spec_fingerprint": "c" * 64,
    "evidence_policy_ref": "policy:v1",
    "exclusions": _VALID_EXCLUSIONS,
    "provider": "legacy-worktree-snapshot",
    "projection_version": "1.0",
    "manifest_pairs": _VALID_MANIFEST_PAIRS,
}


# ═══════════════════════════════════════════════════════════════════════════════
# delivery-subject.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeliverySubjectSchemaParity:
    """Parity between _subject_projection.py and delivery-subject.v1.schema.json."""

    def test_emitted_subject_satisfies_canonical_schema(
        self, projection: ModuleType
    ) -> None:
        """project_delivery_subject() output satisfies contracts/delivery/delivery-subject.v1.schema.json."""
        schema = _load_schema(_SUBJECT_SCHEMA_PATH)
        subject = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        _jsonschema_validate(subject, schema, label="delivery-subject.v1")

    def test_emitted_subject_with_task_provenance_satisfies_schema(
        self, projection: ModuleType
    ) -> None:
        """project_delivery_subject() with optional task-projection fields satisfies the schema."""
        schema = _load_schema(_SUBJECT_SCHEMA_PATH)
        kwargs = dict(
            **_VALID_SUBJECT_KWARGS,
            task_projection_revision="T6",
            task_projection_hash="d" * 64,
        )
        subject = projection.project_delivery_subject(**kwargs)
        _jsonschema_validate(subject, schema, label="delivery-subject.v1 (with task provenance)")

    def test_validate_refuses_non_dict_input(
        self, projection: ModuleType
    ) -> None:
        """validate_subject_dict refuses a non-dict input (denial code: denied-not-a-dict)."""
        ok, code = projection.validate_subject_dict("not a dict")
        assert not ok, "validate_subject_dict must refuse a non-dict input"
        assert code == "denied-not-a-dict"

    def test_validate_refuses_unknown_schema_version(
        self, projection: ModuleType
    ) -> None:
        """validate_subject_dict refuses an out-of-supported schema_version (unknown major)."""
        bad = {"schema_version": 99}
        ok, code = projection.validate_subject_dict(bad)
        assert not ok, "validate_subject_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, projection: ModuleType
    ) -> None:
        """validate_subject_dict refuses a record missing a required field (subject_id)."""
        subject = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        bad = {k: v for k, v in subject.items() if k != "subject_id"}
        ok, code = projection.validate_subject_dict(bad)
        assert not ok, "validate_subject_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, projection: ModuleType
    ) -> None:
        """validate_subject_dict refuses an unknown authority-shaped field."""
        subject = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        bad = {**subject, "inject_escalation": "bypass"}
        ok, code = projection.validate_subject_dict(bad)
        assert not ok, "validate_subject_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_accepts_valid_record(
        self, projection: ModuleType
    ) -> None:
        """validate_subject_dict accepts a well-formed delivery-subject.v1 record."""
        subject = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        ok, code = projection.validate_subject_dict(subject)
        assert ok, f"validate_subject_dict rejected a valid record: {code}"
        assert code == "ok"

    def test_acceptance_fingerprint_is_deterministic(
        self, projection: ModuleType
    ) -> None:
        """Identical inputs always produce the same acceptance fingerprint."""
        s1 = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        s2 = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        assert s1["acceptance_fingerprint"] == s2["acceptance_fingerprint"]

    def test_task_projection_fields_excluded_from_fingerprint(
        self, projection: ModuleType
    ) -> None:
        """task_projection_revision and task_projection_hash do not alter the acceptance fingerprint."""
        s_base = projection.project_delivery_subject(**_VALID_SUBJECT_KWARGS)
        s_with_prov = projection.project_delivery_subject(
            **_VALID_SUBJECT_KWARGS,
            task_projection_revision="T6",
            task_projection_hash="e" * 64,
        )
        assert s_base["acceptance_fingerprint"] == s_with_prov["acceptance_fingerprint"], (
            "task-projection provenance must not alter the acceptance fingerprint"
        )
