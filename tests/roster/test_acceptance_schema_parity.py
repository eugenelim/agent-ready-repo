"""Roster test: Slice 1 acceptance records satisfy the canonical schemas.

For every record the Slice 1 acceptance scripts build or accept
(reviewed-execution-envelope.v1, acceptance-property.v1, acceptance-verdict.v1,
approval-record.v1, initial-plan-review.v1) this suite:

1. Loads each schema from ``contracts/delivery/`` and validates a record
   produced by the script against it using jsonschema Draft202012Validator,
   so schema drift is caught before merge.

2. Feeds four classes of schema-invalid record to each script's own
   ``validate_*_dict()`` function and asserts refusal with a stable denial code:
   - unknown schema_version (unknown major).
   - missing required field.
   - unknown authority-shaped field (a field not declared in the schema).
   - out-of-enum value (a value outside the declared enum for a property).

Both reads are anchored at the repo root via ``Path(__file__).resolve().parents[2]``.
The schemas are read from disk; embedded copies are not used here.  A broken
schema file or a module whose emitted records deviate from the schema fails this
test before any Slice 1 writer task begins.

Parity rule (verification-ledger.md §Script-versus-schema parity): every task
that adds a module building or accepting delivery records carries parity tests.
This file satisfies that obligation for T4's ``_acceptance.py`` and T5's
``_policy_import.py``.
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

_ENVELOPE_SCHEMA_PATH = _CONTRACTS / "reviewed-execution-envelope.v1.schema.json"
_PROPERTY_SCHEMA_PATH = _CONTRACTS / "acceptance-property.v1.schema.json"
_VERDICT_SCHEMA_PATH = _CONTRACTS / "acceptance-verdict.v1.schema.json"

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
def acceptance() -> ModuleType:
    """_acceptance.py loaded by path."""
    return _load_script("acc_roster", _SCRIPTS / "_acceptance.py")


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

_VALID_REFS = {
    "spec_policy": "approval:spec-policy:v1",
    "scope_and_non_goals": "approval:scope:v1",
    "authority_and_security": "approval:authority:v1",
    "public_contracts": "approval:contracts:v1",
    "durable_outputs": "approval:outputs:v1",
    "accepted_risk": "approval:risk:v1",
}

_VALID_PROPERTY = {
    "schema_version": 1,
    "property_id": "prop-roster-001",
    "spec_ref": "fixtures/example-spec/spec.md",
    "authority_ref": "approval:spec-policy:v1",
    "subject_selector": {
        "paths_or_artifacts": ["src/"],
        "fingerprint_algorithm": "sha256",
    },
    "required_observations": [
        {
            "term": "test-run",
            "observation_type": "test-result",
            "producer_class": "ci-runner",
            "outcomes": ["passed"],
        }
    ],
    "freshness_scope": "exact-subject",
    "satisfaction_rule": {"expression": "all"},
    "contradiction_rule": {"expression": "none"},
    "policy_version": "v1",
}


# ═══════════════════════════════════════════════════════════════════════════════
# reviewed-execution-envelope.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnvelopeSchemaParity:
    """Parity between _acceptance.py and reviewed-execution-envelope.v1.schema.json."""

    def test_emitted_envelope_satisfies_canonical_schema(
        self, acceptance: ModuleType
    ) -> None:
        """derive_envelope() output satisfies contracts/delivery/reviewed-execution-envelope.v1.schema.json."""
        schema = _load_schema(_ENVELOPE_SCHEMA_PATH)
        env = acceptance.derive_envelope(_VALID_REFS)
        _jsonschema_validate(env, schema, label="reviewed-execution-envelope.v1")

    def test_validate_refuses_unknown_schema_version(
        self, acceptance: ModuleType
    ) -> None:
        """validate_envelope_dict refuses an out-of-enum schema_version (unknown major)."""
        bad = {
            "schema_version": 99,
            "envelope_fingerprint": "fp-test",
            "refs": dict(_VALID_REFS),
        }
        ok, code = acceptance.validate_envelope_dict(bad)
        assert not ok, "validate_envelope_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, acceptance: ModuleType
    ) -> None:
        """validate_envelope_dict refuses a record missing a required field (envelope_fingerprint)."""
        env = acceptance.derive_envelope(_VALID_REFS)
        bad = {k: v for k, v in env.items() if k != "envelope_fingerprint"}
        ok, code = acceptance.validate_envelope_dict(bad)
        assert not ok, "validate_envelope_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, acceptance: ModuleType
    ) -> None:
        """validate_envelope_dict refuses an unknown authority-shaped field."""
        env = acceptance.derive_envelope(_VALID_REFS)
        bad = {**env, "inject_escalation": "bypass"}
        ok, code = acceptance.validate_envelope_dict(bad)
        assert not ok, "validate_envelope_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_unknown_refs_key(self, acceptance: ModuleType) -> None:
        """validate_envelope_dict refuses an unknown key inside refs."""
        env = acceptance.derive_envelope(_VALID_REFS)
        bad_env = dict(env)
        bad_env["refs"] = {**env["refs"], "inject_escalation": "bypass"}
        ok, code = acceptance.validate_envelope_dict(bad_env)
        assert not ok, "validate_envelope_dict must refuse unknown refs key"
        assert code == "denied-unknown-authority-field"


# ═══════════════════════════════════════════════════════════════════════════════
# acceptance-property.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestPropertySchemaParity:
    """Parity between _acceptance.py and acceptance-property.v1.schema.json."""

    def test_well_formed_property_satisfies_canonical_schema(
        self, acceptance: ModuleType
    ) -> None:
        """A valid acceptance-property.v1 record satisfies the canonical schema."""
        schema = _load_schema(_PROPERTY_SCHEMA_PATH)
        _jsonschema_validate(_VALID_PROPERTY, schema, label="acceptance-property.v1")
        ok, code = acceptance.validate_property_dict(_VALID_PROPERTY)
        assert ok, f"validate_property_dict rejected a valid record: {code}"
        assert code == "ok"

    def test_validate_refuses_unknown_schema_version(
        self, acceptance: ModuleType
    ) -> None:
        """validate_property_dict refuses an out-of-enum schema_version."""
        bad = {**_VALID_PROPERTY, "schema_version": 99}
        ok, code = acceptance.validate_property_dict(bad)
        assert not ok, "validate_property_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, acceptance: ModuleType
    ) -> None:
        """validate_property_dict refuses a record missing a required field (authority_ref)."""
        bad = {k: v for k, v in _VALID_PROPERTY.items() if k != "authority_ref"}
        ok, code = acceptance.validate_property_dict(bad)
        assert not ok, "validate_property_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, acceptance: ModuleType
    ) -> None:
        """validate_property_dict refuses an unknown authority-shaped field."""
        bad = {**_VALID_PROPERTY, "inject_escalation": "bypass"}
        ok, code = acceptance.validate_property_dict(bad)
        assert not ok, "validate_property_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_out_of_enum_freshness_scope(
        self, acceptance: ModuleType
    ) -> None:
        """validate_property_dict refuses a freshness_scope outside the enum."""
        bad = {**_VALID_PROPERTY, "freshness_scope": "full-tree"}
        ok, code = acceptance.validate_property_dict(bad)
        assert not ok, "validate_property_dict must refuse out-of-enum freshness_scope"
        assert code == "denied-invalid-enum"


# ═══════════════════════════════════════════════════════════════════════════════
# acceptance-verdict.v1
# ═══════════════════════════════════════════════════════════════════════════════


class TestVerdictSchemaParity:
    """Parity between _acceptance.py and acceptance-verdict.v1.schema.json."""

    def test_emitted_verdict_satisfies_canonical_schema(
        self, acceptance: ModuleType
    ) -> None:
        """evaluate_verdict() output satisfies contracts/delivery/acceptance-verdict.v1.schema.json."""
        schema = _load_schema(_VERDICT_SCHEMA_PATH)
        current_fp = "fp-roster-parity-001"
        receipt = {
            "schema_version": 1,
            "receipt_id": "r-roster-001",
            "acceptance_fingerprint": current_fp,
            "lineage": {"criterion_ref": "prop-roster-001"},
            "selector": {"term": "test-run"},
            "freshness_mode": "exact-subject",
            "observation": {"type": "test-result"},
            "outcome": "passed",
            "producer": {"class": "ci-runner", "identity": "runner-generic"},
        }
        verdict = acceptance.evaluate_verdict(
            property_record=_VALID_PROPERTY,
            receipts=[receipt],
            current_acceptance_fingerprint=current_fp,
            adapter="sequential-reference",
        )
        _jsonschema_validate(verdict, schema, label="acceptance-verdict.v1")

    def test_validate_refuses_unknown_schema_version(
        self, acceptance: ModuleType
    ) -> None:
        """validate_verdict_dict refuses an out-of-enum schema_version (unknown major)."""
        bad = {
            "schema_version": 99,
            "evaluation_fingerprint": "fp-test",
            "verdict": "supported",
            "criteria_refs": ["prop-001"],
            "receipt_refs": [],
        }
        ok, code = acceptance.validate_verdict_dict(bad)
        assert not ok, "validate_verdict_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, acceptance: ModuleType
    ) -> None:
        """validate_verdict_dict refuses a record missing a required field (verdict)."""
        bad = {
            "schema_version": 1,
            "evaluation_fingerprint": "fp-test",
            # verdict omitted
            "criteria_refs": [],
            "receipt_refs": [],
        }
        ok, code = acceptance.validate_verdict_dict(bad)
        assert not ok, "validate_verdict_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, acceptance: ModuleType
    ) -> None:
        """validate_verdict_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "evaluation_fingerprint": "fp-test",
            "verdict": "supported",
            "criteria_refs": [],
            "receipt_refs": [],
            "inject_escalation": "bypass",
        }
        ok, code = acceptance.validate_verdict_dict(bad)
        assert not ok, "validate_verdict_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_out_of_enum_verdict(
        self, acceptance: ModuleType
    ) -> None:
        """validate_verdict_dict refuses a verdict value outside the enum."""
        bad = {
            "schema_version": 1,
            "evaluation_fingerprint": "fp-test",
            "verdict": "maybe",
            "criteria_refs": [],
            "receipt_refs": [],
        }
        ok, code = acceptance.validate_verdict_dict(bad)
        assert not ok, "validate_verdict_dict must refuse out-of-enum verdict"
        assert code == "denied-invalid-enum"


# ═══════════════════════════════════════════════════════════════════════════════
# T5: approval-record.v1 and initial-plan-review.v1
# ═══════════════════════════════════════════════════════════════════════════════
#
# Parity rule: T5's _policy_import.py builds approval-record.v1 and
# initial-plan-review.v1 records.  These classes verify:
#   (1) emitted records satisfy contracts/delivery/ schemas, and
#   (2) validate_*_dict() refuses each class of invalid input with stable codes.

_APPROVAL_SCHEMA_PATH = _CONTRACTS / "approval-record.v1.schema.json"
_INITIAL_REVIEW_SCHEMA_PATH = _CONTRACTS / "initial-plan-review.v1.schema.json"


@pytest.fixture(scope="module")
def policy_import() -> ModuleType:
    """_policy_import.py loaded by path."""
    return _load_script("pi_roster", _SCRIPTS / "_policy_import.py")


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_script("sc_roster", _SCRIPTS / "_security_capability.py")


def _make_issuer_and_grant_roster(sc: ModuleType) -> tuple:
    """Return a valid (issuer, grant) pair for roster import tests."""
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["delivery"],
        operations=["append", "write"],
        trust_class="trusted",
        writes_allowed_roots=["delivery"],
        control_denies=[],
    )
    return issuer, grant


def _null_sink_roster(event: object) -> None:
    """No-op audit sink for roster tests."""


_VALID_REFS_ROSTER = {
    "spec_policy": "approval:spec-policy:v1",
    "scope_and_non_goals": "approval:scope:v1",
    "authority_and_security": "approval:authority:v1",
    "public_contracts": "approval:contracts:v1",
    "durable_outputs": "approval:outputs:v1",
    "accepted_risk": "approval:risk:v1",
}


@pytest.fixture(scope="module")
def _imported_records(
    policy_import: ModuleType,
    security_capability: ModuleType,
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict, dict]:
    """Run import_policy once and return (approval_record, initial_plan_review)."""
    tmp = tmp_path_factory.mktemp("roster_import")
    spec_path = tmp / "spec.md"
    plan_path = tmp / "plan.md"
    spec_path.write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n- [ ] AC-0001.\n",
        encoding="utf-8",
    )
    plan_path.write_text(
        "# Plan\n\n- **Status:** Approved\n\n## Tasks\n\n### T1: Task\n\n- [ ] Done\n",
        encoding="utf-8",
    )
    store = policy_import.ImportStore()
    issuer, grant = _make_issuer_and_grant_roster(security_capability)
    approval, review = policy_import.import_policy(
        spec_path=spec_path,
        plan_path=plan_path,
        refs=_VALID_REFS_ROSTER,
        terminal_intent="code",
        writer_grant=grant,
        issuer=issuer,
        audit_sink=_null_sink_roster,
        store=store,
        approval_identity="platform-core-maintainer",
        approval_role="spec-policy-owner",
        reviewer_identity="platform-core-maintainer",
        reviewer_role="plan-review-authority",
    )
    return approval, review


class TestApprovalRecordSchemaParity:
    """Parity between _policy_import.py and approval-record.v1.schema.json."""

    def test_emitted_approval_satisfies_canonical_schema(
        self,
        _imported_records: tuple[dict, dict],
    ) -> None:
        """import_policy() approval output satisfies contracts/delivery/approval-record.v1.schema.json."""
        schema = _load_schema(_APPROVAL_SCHEMA_PATH)
        approval, _ = _imported_records
        _jsonschema_validate(approval, schema, label="approval-record.v1")

    def test_validate_refuses_unknown_schema_version(
        self, policy_import: ModuleType
    ) -> None:
        """validate_approval_dict refuses an out-of-enum schema_version (unknown major)."""
        bad = {
            "schema_version": 99,
            "approval_id": "appr-001",
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "fixtures/example-spec/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "approved",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = policy_import.validate_approval_dict(bad)
        assert not ok, "validate_approval_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, policy_import: ModuleType
    ) -> None:
        """validate_approval_dict refuses a record missing a required field (approval_id)."""
        bad = {
            "schema_version": 1,
            # approval_id omitted
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "fixtures/example-spec/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "approved",
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = policy_import.validate_approval_dict(bad)
        assert not ok, "validate_approval_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, policy_import: ModuleType
    ) -> None:
        """validate_approval_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "approval_id": "appr-001",
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "fixtures/example-spec/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "approved",
            "timestamp": "2026-10-01T00:00:00Z",
            "inject_escalation": "bypass",
        }
        ok, code = policy_import.validate_approval_dict(bad)
        assert not ok, "validate_approval_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_out_of_enum_decision(
        self, policy_import: ModuleType
    ) -> None:
        """validate_approval_dict refuses a decision value outside the enum."""
        bad = {
            "schema_version": 1,
            "approval_id": "appr-001",
            "authority": {"identity": "core", "role": "spec-policy-owner"},
            "decision_scope": "spec-policy",
            "base": {"manifest_ref": "sha256:abc"},
            "lineage": {"spec_ref": "fixtures/example-spec/spec.md"},
            "spec_policy_fingerprint": "sha256:def",
            "decision": "rejected",  # not in enum {approved, superseded}
            "timestamp": "2026-10-01T00:00:00Z",
        }
        ok, code = policy_import.validate_approval_dict(bad)
        assert not ok, "validate_approval_dict must refuse out-of-enum decision"
        assert code == "denied-invalid-enum"


class TestInitialReviewSchemaParity:
    """Parity between _policy_import.py and initial-plan-review.v1.schema.json."""

    def test_emitted_review_satisfies_canonical_schema(
        self,
        _imported_records: tuple[dict, dict],
    ) -> None:
        """import_policy() review output satisfies contracts/delivery/initial-plan-review.v1.schema.json."""
        schema = _load_schema(_INITIAL_REVIEW_SCHEMA_PATH)
        _, review = _imported_records
        _jsonschema_validate(review, schema, label="initial-plan-review.v1")

    def test_validate_refuses_unknown_schema_version(
        self, policy_import: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses an out-of-enum schema_version (unknown major)."""
        bad = {
            "schema_version": 99,
            "review_id": "rev-001",
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "accepted",
        }
        ok, code = policy_import.validate_initial_review_dict(bad)
        assert not ok, "validate_initial_review_dict must refuse unknown schema_version"
        assert code == "denied-unknown-schema-version"

    def test_validate_refuses_missing_required_field(
        self, policy_import: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses a record missing a required field (review_id)."""
        bad = {
            "schema_version": 1,
            # review_id omitted
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "accepted",
        }
        ok, code = policy_import.validate_initial_review_dict(bad)
        assert not ok, "validate_initial_review_dict must refuse missing required field"
        assert code == "denied-missing-required-field"

    def test_validate_refuses_unknown_authority_field(
        self, policy_import: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses an unknown authority-shaped field."""
        bad = {
            "schema_version": 1,
            "review_id": "rev-001",
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "accepted",
            "inject_authority": "bypass",
        }
        ok, code = policy_import.validate_initial_review_dict(bad)
        assert not ok, "validate_initial_review_dict must refuse unknown authority-shaped field"
        assert code == "denied-unknown-authority-field"

    def test_validate_refuses_out_of_enum_decision(
        self, policy_import: ModuleType
    ) -> None:
        """validate_initial_review_dict refuses a decision value outside the enum."""
        bad = {
            "schema_version": 1,
            "review_id": "rev-001",
            "envelope_fingerprint": "fp-abc",
            "plan_hash": "sha256:def",
            "authorized_terminal_intent": "code",
            "reviewer": {"identity": "core", "role": "plan-review-authority"},
            "decision": "pending",  # not "accepted"
        }
        ok, code = policy_import.validate_initial_review_dict(bad)
        assert not ok, "validate_initial_review_dict must refuse out-of-enum decision"
        assert code == "denied-invalid-enum"
