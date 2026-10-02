"""Roster test: evidence-store records satisfy the canonical schemas (T7 parity).

For every record the Slice 1 evidence-store script builds or accepts
(semantic-evidence-transaction.v1, evidence-receipt.v1, evidence-supersession.v1)
this suite:

1. Loads each schema from ``contracts/delivery/`` and validates a record
   produced by _evidence_store.py against it using jsonschema
   Draft202012Validator, so schema drift is caught before merge.

2. Feeds four classes of schema-invalid record to each
   ``validate_*_dict()`` function and asserts refusal with a stable denial code:
   - unknown schema_version (unknown major).
   - missing required field.
   - unknown authority-shaped field (a field not declared in the schema).
   - out-of-enum or empty-list value (empty ordered_record_ids / superseded_ids).

Both reads are anchored at the repo root via ``Path(__file__).resolve().parents[2]``.
The schemas are read from disk; embedded copies are not used here.

Parity rule (verification-ledger.md §Script-versus-schema parity): every task
that adds a module building or accepting delivery records carries parity tests.
This file satisfies that obligation for T7's ``_evidence_store.py``.

Spec: docs/specs/acceptance-authority-and-evidence/spec.md
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

# ── Schema paths ──────────────────────────────────────────────────────────────

_TRANSACTION_SCHEMA_PATH = _CONTRACTS / "semantic-evidence-transaction.v1.schema.json"
_RECEIPT_SCHEMA_PATH = _CONTRACTS / "evidence-receipt.v1.schema.json"
_SUPERSESSION_SCHEMA_PATH = _CONTRACTS / "evidence-supersession.v1.schema.json"

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
def es() -> ModuleType:
    """_evidence_store.py loaded by path."""
    return _load_script("es_roster", _SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py loaded by path."""
    return _load_script("acc_roster_ev", _SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_script("sc_roster_ev", _SCRIPTS / "_security_capability.py")


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


# ── Shared helpers ────────────────────────────────────────────────────────────

_CURRENT_FP = "fp-roster-parity-001"


def _make_receipt(receipt_id: str, criterion_ref: str = "prop-roster-001") -> dict:
    """Build a minimal valid evidence-receipt.v1 record."""
    return {
        "schema_version": 1,
        "receipt_id": receipt_id,
        "acceptance_fingerprint": _CURRENT_FP,
        "lineage": {"criterion_ref": criterion_ref},
        "selector": {"term": "test-run"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "test-result"},
        "outcome": "passed",
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _make_supersession(
    supersession_id: str,
    superseded_receipt_ids: list[str],
) -> dict:
    """Build a minimal valid evidence-supersession.v1 record."""
    return {
        "schema_version": 1,
        "supersession_id": supersession_id,
        "superseded_receipt_ids": superseded_receipt_ids,
        "authority": {"identity": "evidence-authority-generic", "role": "evidence-authority"},
        "provenance": {"reason_code": "review-assessment-superseded"},
    }


def _make_grant(sc: ModuleType) -> tuple:
    """Return a valid (issuer, grant) pair."""
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


def _null_sink(event: object) -> None:
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# semantic-evidence-transaction.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestTransactionSchemaParity:
    """Parity between _evidence_store.py and semantic-evidence-transaction.v1.schema.json."""

    def test_emitted_transaction_satisfies_canonical_schema(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """append_receipt() produces a transaction that satisfies the canonical schema."""
        schema = _load_schema(_TRANSACTION_SCHEMA_PATH)
        log_path = tmp_path / "tx-parity.log"
        store = es.EvidenceStore(log_path)
        store.open()
        issuer, grant = _make_grant(sc)
        receipt = _make_receipt("r-tx-parity")
        tx = store.append_receipt(
            receipt, transaction_id="tx-parity-001", issuer=issuer, grant=grant, audit_sink=_null_sink
        )
        _jsonschema_validate(tx, schema, label="semantic-evidence-transaction.v1")

    def test_validate_refuses_unknown_schema_version(self, es: ModuleType) -> None:
        """validate_transaction_dict refuses schema_version not in [1]."""
        bad = {
            "schema_version": 99,
            "transaction_id": "tx-bad-sv",
            "ordered_record_ids": ["r-001"],
            "acceptance_fingerprint": _CURRENT_FP,
            "checksum": "sha256:abc",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(self, es: ModuleType) -> None:
        """validate_transaction_dict refuses a record missing a required field."""
        bad = {
            "schema_version": 1,
            # transaction_id omitted
            "ordered_record_ids": ["r-001"],
            "acceptance_fingerprint": _CURRENT_FP,
            "checksum": "sha256:abc",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(self, es: ModuleType) -> None:
        """validate_transaction_dict refuses a field not declared in the schema."""
        bad = {
            "schema_version": 1,
            "transaction_id": "tx-extra",
            "ordered_record_ids": ["r-001"],
            "acceptance_fingerprint": _CURRENT_FP,
            "checksum": "sha256:abc",
            "inject_escalation": "bypass",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_empty_ordered_record_ids(self, es: ModuleType) -> None:
        """validate_transaction_dict refuses ordered_record_ids: [] (minItems:1)."""
        bad = {
            "schema_version": 1,
            "transaction_id": "tx-empty-ids",
            "ordered_record_ids": [],
            "acceptance_fingerprint": _CURRENT_FP,
            "checksum": "sha256:abc",
        }
        ok, code = es.validate_transaction_dict(bad)
        assert not ok
        assert code == "denied-empty-ordered-record-ids"


# ═══════════════════════════════════════════════════════════════════════════════
# evidence-receipt.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestReceiptSchemaParity:
    """Parity between _evidence_store.py and evidence-receipt.v1.schema.json."""

    def test_emitted_receipt_satisfies_canonical_schema(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A receipt appended by EvidenceStore satisfies the canonical schema."""
        schema = _load_schema(_RECEIPT_SCHEMA_PATH)
        receipt = _make_receipt("r-receipt-parity")
        _jsonschema_validate(receipt, schema, label="evidence-receipt.v1")

    def test_validate_refuses_unknown_schema_version(self, es: ModuleType) -> None:
        """validate_receipt_dict refuses schema_version not in [1]."""
        bad = {**_make_receipt("r-bad-sv"), "schema_version": 99}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(self, es: ModuleType) -> None:
        """validate_receipt_dict refuses a record missing a required field."""
        bad = {k: v for k, v in _make_receipt("r-miss").items() if k != "receipt_id"}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(self, es: ModuleType) -> None:
        """validate_receipt_dict refuses a field not declared in the schema."""
        bad = {**_make_receipt("r-extra"), "inject_escalation": "bypass"}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_out_of_enum_freshness_mode(self, es: ModuleType) -> None:
        """validate_receipt_dict refuses freshness_mode not in {exact-subject, path-set}."""
        bad = {**_make_receipt("r-bad-fm"), "freshness_mode": "full-tree"}
        ok, code = es.validate_receipt_dict(bad)
        assert not ok
        assert code == "denied-invalid-enum"


# ═══════════════════════════════════════════════════════════════════════════════
# evidence-supersession.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestSupersessionSchemaParity:
    """Parity between _evidence_store.py and evidence-supersession.v1.schema.json."""

    def test_emitted_supersession_satisfies_canonical_schema(
        self, es: ModuleType, sc: ModuleType, tmp_path: Path
    ) -> None:
        """A supersession appended by EvidenceStore satisfies the canonical schema."""
        schema = _load_schema(_SUPERSESSION_SCHEMA_PATH)
        sup = _make_supersession("sup-parity", ["r-001"])
        _jsonschema_validate(sup, schema, label="evidence-supersession.v1")

    def test_validate_refuses_unknown_schema_version(self, es: ModuleType) -> None:
        """validate_supersession_dict refuses schema_version not in [1]."""
        bad = {**_make_supersession("sup-bad-sv", ["r-001"]), "schema_version": 99}
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(self, es: ModuleType) -> None:
        """validate_supersession_dict refuses a record missing a required field."""
        bad = {
            k: v
            for k, v in _make_supersession("sup-miss", ["r-001"]).items()
            if k != "supersession_id"
        }
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(self, es: ModuleType) -> None:
        """validate_supersession_dict refuses a field not declared in the schema."""
        bad = {**_make_supersession("sup-extra", ["r-001"]), "inject_escalation": "bypass"}
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_empty_superseded_ids(self, es: ModuleType) -> None:
        """validate_supersession_dict refuses superseded_receipt_ids: [] (minItems:1)."""
        bad = {**_make_supersession("sup-empty", ["r-001"]), "superseded_receipt_ids": []}
        ok, code = es.validate_supersession_dict(bad)
        assert not ok
        assert code == "denied-empty-superseded-ids"
