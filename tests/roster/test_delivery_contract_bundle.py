# STUB: AC-0003 — canonical delivery contract bundle is present and schema-valid
import json
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_delivery_contract_bundle_contains_valid_schemas() -> None:
    delivery_root = REPO_ROOT / "contracts" / "delivery"
    schemas = sorted(delivery_root.glob("*.schema.json"))
    assert schemas, "the canonical delivery contract bundle is missing"
    for schema_path in schemas:
        Draft202012Validator.check_schema(
            json.loads(schema_path.read_text(encoding="utf-8"))
        )


# ── Additional T1 construction tests ─────────────────────────────────────────
# AC-0001 through AC-0017, AC-0020, AC-0021: schema validity, rejection of
# unknown or incomplete authority-shaped records, registry coverage, and
# no-copy-outside-contracts/delivery assertion.
#
# Roster-owned: reads contracts/ and docs/specs/, both above any pack tree.
# Placed above the bulk tests/ step in build-check.yml for named attribution.


_DELIVERY_ROOT = REPO_ROOT / "contracts" / "delivery"
_README = REPO_ROOT / "contracts" / "README.md"
_REGISTRY = REPO_ROOT / "contracts" / "REGISTRY.md"

# Expected record names correspond to the 17 canonical delivery record types
# defined in docs/specs/acceptance-authority-and-evidence/plan.md § Data & schema.
_EXPECTED_SCHEMA_NAMES: frozenset[str] = frozenset({
    "delivery-subject.v1.schema.json",
    "acceptance-property.v1.schema.json",
    "approval-record.v1.schema.json",
    "reviewed-execution-envelope.v1.schema.json",
    "initial-plan-review.v1.schema.json",
    "semantic-evidence-transaction.v1.schema.json",
    "evidence-receipt.v1.schema.json",
    "evidence-supersession.v1.schema.json",
    "acceptance-verdict.v1.schema.json",
    "security-capability.v1.schema.json",
    "confined-file.v1.schema.json",
    "safe-process.v1.schema.json",
    "containment-attestation.v1.schema.json",
    "security-event.v1.schema.json",
    "content-safety-policy.v1.schema.json",
    "content-safety-decision.v1.schema.json",
    "untrusted-data.v1.schema.json",
})


def _load_schema(name: str) -> dict:
    """Return the parsed schema for the named delivery schema file."""
    return json.loads((_DELIVERY_ROOT / name).read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    """Return a validator for the named delivery schema."""
    return Draft202012Validator(_load_schema(name))


# ── Schema set completeness ───────────────────────────────────────────────────

def test_delivery_bundle_has_all_17_expected_schemas() -> None:
    """The bundle contains exactly the 17 canonical delivery record schemas."""
    found = frozenset(p.name for p in _DELIVERY_ROOT.glob("*.schema.json"))
    missing = _EXPECTED_SCHEMA_NAMES - found
    extra = found - _EXPECTED_SCHEMA_NAMES
    assert not missing, f"schemas missing from contracts/delivery/: {sorted(missing)}"
    assert not extra, (
        f"unexpected schemas in contracts/delivery/ (update _EXPECTED_SCHEMA_NAMES "
        f"or remove the file): {sorted(extra)}"
    )


# ── Schema structural invariants ─────────────────────────────────────────────

def test_every_delivery_schema_closes_unknown_properties() -> None:
    """Every schema has additionalProperties: false — closes unknown authority-shaped fields."""
    schemas = sorted(_DELIVERY_ROOT.glob("*.schema.json"))
    assert schemas
    violations = [
        p.name for p in schemas
        if json.loads(p.read_text(encoding="utf-8")).get("additionalProperties") is not False
    ]
    assert not violations, (
        f"schemas without additionalProperties:false (unknown fields not closed): {violations}"
    )


def test_every_delivery_schema_requires_schema_version() -> None:
    """Every schema requires schema_version — implements unknown-major refusal."""
    schemas = sorted(_DELIVERY_ROOT.glob("*.schema.json"))
    assert schemas
    violations = []
    for p in schemas:
        schema = json.loads(p.read_text(encoding="utf-8"))
        required = schema.get("required", [])
        props = schema.get("properties", {})
        sv = props.get("schema_version", {})
        # schema_version must be required and pinned to [1] via enum
        if "schema_version" not in required or sv.get("enum") != [1]:
            violations.append(p.name)
    assert not violations, (
        f"schemas lacking required schema_version pinned to enum:[1] "
        f"(unknown-major refusal not declared): {violations}"
    )


def test_every_delivery_schema_carries_x_spec() -> None:
    """Every schema carries x-spec pointing to the owning spec."""
    schemas = sorted(_DELIVERY_ROOT.glob("*.schema.json"))
    assert schemas
    spec = "docs/specs/acceptance-authority-and-evidence/"
    violations = [
        p.name for p in schemas
        if spec not in json.loads(p.read_text(encoding="utf-8")).get("x-spec", [])
    ]
    assert not violations, (
        f"schemas missing x-spec pointer to {spec!r}: {violations}"
    )


# ── Rejection of unknown or incomplete authority-shaped records ───────────────

def test_delivery_schemas_reject_empty_record() -> None:
    """Every schema rejects an empty record (missing required identity fields)."""
    schemas = sorted(_DELIVERY_ROOT.glob("*.schema.json"))
    assert schemas
    accepted = [
        p.name for p in schemas
        if not list(Draft202012Validator(
            json.loads(p.read_text(encoding="utf-8"))
        ).iter_errors({}))
    ]
    assert not accepted, (
        f"schemas that accepted an empty record (required fields not enforced): {accepted}"
    )


def test_delivery_schemas_reject_unknown_authority_field() -> None:
    """Every schema rejects a record carrying an unknown authority-shaped field."""
    schemas = sorted(_DELIVERY_ROOT.glob("*.schema.json"))
    assert schemas
    # An injected field that looks like an authority grant but is not in any schema.
    injected = {"_unknown_capability_grant": "injected-authority-value"}
    accepted = []
    for p in schemas:
        validator = Draft202012Validator(json.loads(p.read_text(encoding="utf-8")))
        if not list(validator.iter_errors(injected)):
            accepted.append(p.name)
    assert not accepted, (
        f"schemas that accepted a record with unknown authority-shaped field: {accepted}"
    )


# ── Stable identity examples ──────────────────────────────────────────────────

def test_reviewed_execution_envelope_accepts_stable_example() -> None:
    """A well-formed reviewed-execution-envelope.v1 record passes validation.

    AC-0003: the envelope deterministically fingerprints ordered references;
    a valid record must satisfy all required fields.
    """
    example = {
        "schema_version": 1,
        "envelope_fingerprint": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
        "refs": {
            "spec_policy": "approval:spec-policy-2026-10-01",
            "scope_and_non_goals": "approval:scope-2026-10-01",
            "authority_and_security": "approval:authority-2026-10-01",
            "public_contracts": "approval:contracts-2026-10-01",
            "durable_outputs": "approval:outputs-2026-10-01",
            "accepted_risk": "approval:risk-2026-10-01",
        },
    }
    errors = list(_validator("reviewed-execution-envelope.v1.schema.json").iter_errors(example))
    assert not errors, f"valid reviewed-execution-envelope.v1 was rejected: {errors}"


def test_reviewed_execution_envelope_rejects_missing_ref() -> None:
    """A reviewed-execution-envelope.v1 record missing a required ref is rejected.

    AC-0003: a missing reference refuses derivation.
    """
    example = {
        "schema_version": 1,
        "envelope_fingerprint": "sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
        "refs": {
            # accepted_risk is omitted — must fail
            "spec_policy": "approval:spec-policy-2026-10-01",
            "scope_and_non_goals": "approval:scope-2026-10-01",
            "authority_and_security": "approval:authority-2026-10-01",
            "public_contracts": "approval:contracts-2026-10-01",
            "durable_outputs": "approval:outputs-2026-10-01",
        },
    }
    errors = list(_validator("reviewed-execution-envelope.v1.schema.json").iter_errors(example))
    assert errors, "reviewed-execution-envelope.v1 with missing ref was accepted (should be rejected)"


def test_approval_record_accepts_stable_example() -> None:
    """A well-formed approval-record.v1 record passes validation."""
    example = {
        "schema_version": 1,
        "approval_id": "approval:spec-policy-2026-10-01",
        "authority": {"identity": "platform-core-owner", "role": "spec-policy-owner"},
        "decision_scope": "spec-policy",
        "base": {"manifest_ref": "git:abc123"},
        "lineage": {"spec_ref": "docs/specs/acceptance-authority-and-evidence/"},
        "spec_policy_fingerprint": "sha256:deadbeef",
        "decision": "approved",
        "timestamp": "2026-10-01T00:00:00Z",
    }
    errors = list(_validator("approval-record.v1.schema.json").iter_errors(example))
    assert not errors, f"valid approval-record.v1 was rejected: {errors}"


def test_approval_record_rejects_unknown_major_version() -> None:
    """approval-record.v1 rejects schema_version: 2 (unknown-major refusal)."""
    example = {
        "schema_version": 2,  # unknown future major
        "approval_id": "approval:spec-policy-2026-10-01",
        "authority": {"identity": "platform-core-owner", "role": "spec-policy-owner"},
        "decision_scope": "spec-policy",
        "base": {"manifest_ref": "git:abc123"},
        "lineage": {"spec_ref": "docs/specs/acceptance-authority-and-evidence/"},
        "spec_policy_fingerprint": "sha256:deadbeef",
        "decision": "approved",
        "timestamp": "2026-10-01T00:00:00Z",
    }
    errors = list(_validator("approval-record.v1.schema.json").iter_errors(example))
    assert errors, "approval-record.v1 accepted unknown major version 2 (should be rejected)"


def test_acceptance_verdict_accepts_stable_example() -> None:
    """A well-formed acceptance-verdict.v1 record passes validation."""
    example = {
        "schema_version": 1,
        "evaluation_fingerprint": "sha256:cafebabe",
        "verdict": "supported",
        "criteria_refs": ["property:AC-0003"],
        "receipt_refs": ["receipt:r001"],
    }
    errors = list(_validator("acceptance-verdict.v1.schema.json").iter_errors(example))
    assert not errors, f"valid acceptance-verdict.v1 was rejected: {errors}"


def test_acceptance_verdict_rejects_unknown_verdict_value() -> None:
    """acceptance-verdict.v1 rejects a verdict value not in the allowed enum."""
    example = {
        "schema_version": 1,
        "evaluation_fingerprint": "sha256:cafebabe",
        "verdict": "maybe",  # not in enum
        "criteria_refs": [],
        "receipt_refs": [],
    }
    errors = list(_validator("acceptance-verdict.v1.schema.json").iter_errors(example))
    assert errors, "acceptance-verdict.v1 accepted unknown verdict value (should be rejected)"


# ── Registry coverage ─────────────────────────────────────────────────────────

def test_every_delivery_schema_is_listed_in_readme() -> None:
    """Every contracts/delivery/*.schema.json is mentioned in contracts/README.md.

    An unregistered schema fails this check.
    """
    readme = _README.read_text(encoding="utf-8")
    schemas = sorted(p.name for p in _DELIVERY_ROOT.glob("*.schema.json"))
    assert schemas, "no delivery schemas found"
    missing = [name for name in schemas if name not in readme]
    assert not missing, (
        f"delivery schemas not listed in contracts/README.md: {missing}"
    )


def test_registry_md_has_delivery_backward_pointer() -> None:
    """contracts/REGISTRY.md has a backward pointer for contracts/delivery/.

    The spec's Contract: header is contracts/delivery/, which cannot carry x-spec
    because it is a directory, so it needs a REGISTRY.md row.
    """
    registry = _REGISTRY.read_text(encoding="utf-8")
    assert "contracts/delivery" in registry, (
        "contracts/REGISTRY.md missing backward pointer token 'contracts/delivery'"
    )
    assert "docs/specs/acceptance-authority-and-evidence/" in registry, (
        "contracts/REGISTRY.md missing spec directory for acceptance-authority-and-evidence"
    )


# ── No-copy assertion ─────────────────────────────────────────────────────────

def test_no_delivery_schema_copy_outside_contracts_delivery() -> None:
    """No delivery schema file exists outside contracts/delivery/.

    AC-0001 through AC-0017: the canonical source is contracts/delivery/ and
    no copy ships anywhere else in the repository (the T1 Constraints confirm
    no schema copy ships in the Core pack either).
    """
    schema_names = {p.name for p in _DELIVERY_ROOT.glob("*.schema.json")}
    assert schema_names, "no delivery schemas found"
    copies = []
    for name in sorted(schema_names):
        for found in REPO_ROOT.rglob(name):
            if found.parent.resolve() != _DELIVERY_ROOT.resolve():
                copies.append(str(found.relative_to(REPO_ROOT)))
    assert not copies, (
        f"delivery schema copies found outside contracts/delivery/: {copies}"
    )
