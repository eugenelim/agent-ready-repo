# STUB: AC-0003 — canonical delivery contract bundle is present and schema-valid
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

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

# Expected record names correspond to the canonical delivery record types
# defined by the shipped Slice 1 bundle and structured-review-boundary Slice 2.
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
    "review-subject.v1.schema.json",
    "review-obligation.v1.schema.json",
    "review-report.v1.schema.json",
    "finding.v1.schema.json",
    "finding-assessment.v1.schema.json",
    "finding-disposition.v1.schema.json",
    "delivery-fact-feed.v1.schema.json",
    "knowledge-observation.v1.schema.json",
})


def _load_schema(name: str) -> dict:
    """Return the parsed schema for the named delivery schema file."""
    return json.loads((_DELIVERY_ROOT / name).read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    """Return a validator for the named delivery schema."""
    resources = []
    for path in _DELIVERY_ROOT.glob("*.schema.json"):
        schema = _load_schema(path.name)
        resource = Resource.from_contents(schema, DRAFT202012)
        resources.append((schema["$id"], resource))
        resources.append((path.name, resource))
    return Draft202012Validator(
        _load_schema(name), registry=Registry().with_resources(resources)
    )


def _review_subject(subject_id: str = "subject-current") -> dict:
    """Build a valid review-subject.v1 record."""
    return {
        "schema_version": 1,
        "review_subject_id": subject_id,
        "review_subject_fingerprint": "review-subject-current",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-current",
            "acceptance_fingerprint": "acceptance-current",
        },
        "review_policy_fingerprint": "review-policy-v1",
        "normalized_paths": ["packs/core/.apm/skills/work-loop/scripts/x.py"],
        "normalized_statuses": ["modified"],
        "lineage": {"provider": "review-subject-projector", "projection_version": "v1"},
    }


def _finding(finding_id: str = "finding-1") -> dict:
    """Build a valid finding.v1 record."""
    return {
        "schema_version": 1,
        "finding_id": finding_id,
        "rule_ref": "AC-0012",
        "observation": "A report with executable content reached validation.",
        "reachable_path": "review adapter to durable review report",
        "actual_failure": "Executable reviewer content could alter procedure.",
        "affected_acceptance_criteria": ["AC-0012"],
        "evidence_refs": ["packs/core/.apm/skills/work-loop/scripts/x.py"],
        "material": True,
    }


def _review_obligation() -> dict:
    """Build a valid review-obligation.v1 record."""
    return {
        "schema_version": 1,
        "obligation_id": "obligation-1",
        "role": "adversarial-reviewer",
        "review_subject_fingerprint": "review-subject-current",
        "review_policy_fingerprint": "review-policy-v1",
        "kind": "mandatory",
        "lineage": {"selector": "core-policy", "policy_version": "v1"},
    }


def _review_report(status: str = "findings") -> dict:
    """Build a valid review-report.v1 record."""
    return {
        "schema_version": 1,
        "report_id": "report-1",
        "role": "adversarial-reviewer",
        "subject": _review_subject(),
        "terminal_status": status,
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": "review-policy-v1",
            "source_event_id": "event-1",
            "producer": "synthetic-reviewer",
        },
        "findings": [_finding()] if status == "findings" else [],
    }


def _finding_assessment() -> dict:
    """Build a valid finding-assessment.v1 record."""
    return {
        "schema_version": 1,
        "assessment_id": "assessment-1",
        "finding_id": "finding-1",
        "report_id": "report-1",
        "review_subject_fingerprint": "review-subject-current",
        "assessment": "supported",
        "evidence_refs": ["evidence-ref-1"],
        "lineage": {"predicate_version": "v1"},
    }


def _finding_disposition() -> dict:
    """Build a valid finding-disposition.v1 record."""
    return {
        "schema_version": 1,
        "disposition_id": "disposition-1",
        "finding_id": "finding-1",
        "assessment_id": "assessment-1",
        "review_subject_fingerprint": "review-subject-current",
        "disposition": "accept-risk",
        "decision_maker": {"identity": "review-owner", "role": "risk-owner"},
        "lineage": {"authority_ref": "authority-1", "source_event_id": "event-1"},
    }


# ── Schema set completeness ───────────────────────────────────────────────────

def test_delivery_bundle_has_all_17_expected_schemas() -> None:
    """The bundle contains the canonical delivery record schemas."""
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
    violations = [
        p.name for p in schemas
        if not json.loads(p.read_text(encoding="utf-8")).get("x-spec", [])
    ]
    assert not violations, (
        f"schemas missing x-spec pointer: {violations}"
    )


def test_review_schemas_accept_valid_examples() -> None:
    """Every structured-review schema accepts its canonical example."""
    examples = {
        "review-subject.v1.schema.json": _review_subject(),
        "review-obligation.v1.schema.json": _review_obligation(),
        "review-report.v1.schema.json": _review_report(),
        "finding.v1.schema.json": _finding(),
        "finding-assessment.v1.schema.json": _finding_assessment(),
        "finding-disposition.v1.schema.json": _finding_disposition(),
    }
    for schema_name, example in examples.items():
        errors = list(_validator(schema_name).iter_errors(example))
        assert not errors, f"valid {schema_name} rejected: {errors}"


def test_review_subject_schema_rejects_duplicate_paths() -> None:
    subject = _review_subject()
    subject["normalized_paths"] = ["a.py", "a.py"]
    subject["normalized_statuses"] = ["modified", "modified"]
    errors = list(_validator("review-subject.v1.schema.json").iter_errors(subject))
    assert errors, "review-subject.v1 accepted duplicate normalized paths"


def test_review_subject_schema_rejects_unknown_status() -> None:
    subject = _review_subject()
    subject["normalized_statuses"] = ["unknown"]
    errors = list(_validator("review-subject.v1.schema.json").iter_errors(subject))
    assert errors, "review-subject.v1 accepted an unknown normalized status"


def test_report_schema_requires_findings_for_findings_status() -> None:
    report = _review_report(status="findings")
    report["findings"] = []
    errors = list(_validator("review-report.v1.schema.json").iter_errors(report))
    assert errors, "review-report.v1 accepted findings status with no findings"


def test_report_schema_rejects_findings_for_clean_status() -> None:
    report = _review_report(status="clean")
    report["findings"] = [_finding()]
    errors = list(_validator("review-report.v1.schema.json").iter_errors(report))
    assert errors, "review-report.v1 accepted clean status with findings"


@pytest.mark.parametrize(
    "field",
    [
        "schema_version", "report_id", "role", "subject", "terminal_status",
        "lineage", "findings",
    ],
)
def test_report_schema_rejects_missing_required_fields(field: str) -> None:
    """Each mandatory report field has its own rejection fixture."""
    report = _review_report()
    report.pop(field)
    errors = list(_validator("review-report.v1.schema.json").iter_errors(report))
    assert errors, f"review-report.v1 accepted a missing {field!r}"


@pytest.mark.parametrize(
    "schema_name,example_factory,field",
    [
        ("review-subject.v1.schema.json", _review_subject, "review_subject_fingerprint"),
        ("review-obligation.v1.schema.json", _review_obligation, "kind"),
        ("review-report.v1.schema.json", _review_report, "terminal_status"),
        ("finding.v1.schema.json", _finding, "actual_failure"),
        ("finding-assessment.v1.schema.json", _finding_assessment, "assessment"),
        ("finding-disposition.v1.schema.json", _finding_disposition, "decision_maker"),
    ],
)
def test_each_review_schema_rejects_missing_required_field(
    schema_name: str, example_factory: object, field: str
) -> None:
    record = example_factory()
    record.pop(field)
    errors = list(_validator(schema_name).iter_errors(record))
    assert errors, f"{schema_name} accepted missing {field!r}"


@pytest.mark.parametrize(
    "schema_name,example_factory",
    [
        ("review-subject.v1.schema.json", _review_subject),
        ("review-obligation.v1.schema.json", _review_obligation),
        ("review-report.v1.schema.json", _review_report),
        ("finding.v1.schema.json", _finding),
        ("finding-assessment.v1.schema.json", _finding_assessment),
        ("finding-disposition.v1.schema.json", _finding_disposition),
    ],
)
def test_each_review_schema_rejects_unknown_field(
    schema_name: str, example_factory: object
) -> None:
    record = example_factory()
    record["_unknown_capability_grant"] = "admin"
    errors = list(_validator(schema_name).iter_errors(record))
    assert errors, f"{schema_name} accepted an unknown authority field"


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


# ── Delivery knowledge projection schemas (Slice 3) ──────────────────────────
# Parity between delivery-fact-feed.v1, knowledge-observation.v1, and the
# self-contained work-loop feed and projector. Extends this existing roster
# file, so no new CI step or roster registration is needed.

_FEED = "delivery-fact-feed.v1.schema.json"
_OBSERVATION = "knowledge-observation.v1.schema.json"
_PROJECTION_SPEC = "docs/specs/delivery-knowledge-projection/"
_WORK_LOOP_SCRIPTS = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
)


def _load_work_loop(alias: str, filename: str):  # noqa: ANN202 - test-time module loader
    import importlib.util

    spec = importlib.util.spec_from_file_location(alias, str(_WORK_LOOP_SCRIPTS / filename))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_observation() -> dict:
    """Project one real observation through the shipped projector."""
    projector = _load_work_loop("dfp_roster_projection", "_knowledge_projection.py")
    receipt = {
        "schema_version": 1,
        "receipt_id": "review-failure-sha256-" + "a" * 64,
        "acceptance_fingerprint": "acceptance-fp-1",
        "lineage": {"criterion_ref": "AC-0001"},
        "selector": {"term": "supported-review-failure"},
        "freshness_mode": "exact-subject",
        "observation": {"type": "review-failure"},
        "outcome": "review-failure",
        "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
    }
    report = _review_report()
    finding = report["findings"][0]
    projection = projector.project_record(
        "evidence-receipt.v1", receipt, spec_path="docs/specs/example",
        transaction_id="tx-1", superseded=False, report=report, finding=finding,
    )
    assert projection.observation is not None, projection.none_reason
    return projection.observation


def _sample_page(observation: dict | None = None) -> dict:
    observation = observation or _sample_observation()
    return {
        "schema_version": 1,
        "snapshot_id": "snapshot-sha256-" + "b" * 64,
        "shadow_services": "enabled",
        "first_ordinal": 0,
        "entries": [
            {
                "entry_kind": "fact",
                "ordinal": 0,
                "source": {
                    "spec_path": "docs/specs/example",
                    "transaction_id": "tx-1",
                    "record_kind": "evidence-receipt.v1",
                    "record_id": observation["source"]["receipt_id"],
                    "predecessor_schema_version": 1,
                },
                "observation": observation,
                "none_reason": None,
            },
            {"entry_kind": "unread-source", "ordinal": 1,
             "spec_path": "docs/specs/other", "reason_code": "marker-missing"},
        ],
        "continuation": None,
    }


def test_projection_schemas_point_at_their_spec_and_close_every_object() -> None:
    for name in (_FEED, _OBSERVATION):
        schema = _load_schema(name)
        assert _PROJECTION_SPEC in schema["x-spec"]
        assert schema["additionalProperties"] is False

    def walk(node: object, where: str) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                assert node.get("additionalProperties") is False, where
            for key, value in node.items():
                walk(value, f"{where}/{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{where}/{i}")

    walk(_load_schema(_FEED), _FEED)
    walk(_load_schema(_OBSERVATION), _OBSERVATION)


def test_every_string_in_the_projection_schemas_has_an_enforced_bound() -> None:
    """No annotation-only format: each string is an enum or const, or has a length and a pattern."""

    def walk(node: object, where: str) -> None:
        if isinstance(node, dict):
            assert "format" not in node or where.endswith("/properties/format"), where
            if node.get("type") == "string":
                closed = {"enum", "const"} & set(node)
                assert closed or ("maxLength" in node and "pattern" in node), where
            for key, value in node.items():
                walk(value, f"{where}/{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{where}/{i}")

    for name in (_FEED, _OBSERVATION):
        walk(_load_schema(name), name)


def test_patterns_end_with_a_lookahead_not_a_dollar() -> None:
    """Python's `$` matches before a trailing LF, so no pattern may rely on it."""

    def walk(node: object) -> None:
        if isinstance(node, dict):
            pattern = node.get("pattern")
            if isinstance(pattern, str):
                assert not pattern.endswith("$") and pattern.endswith("(?![\\s\\S])"), pattern
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(_load_schema(_FEED))
    walk(_load_schema(_OBSERVATION))


def test_free_text_fields_are_typed_as_untrusted_data() -> None:
    observation = _load_schema(_OBSERVATION)
    text_fields = ["rule_ref", "observed", "reachable_path", "actual_failure"]
    for field in text_fields:
        branches = observation["properties"][field]["allOf"]
        assert {"$ref": "#/$defs/untrustedText"} in branches
    wrapper = observation["$defs"]["untrustedText"]
    assert {"$ref": "untrusted-data.v1.schema.json"} in wrapper["allOf"]
    # The feed carries observations only through the typed schema.
    feed = _load_schema(_FEED)
    assert feed["$defs"]["factEntry"]["properties"]["observation"]["oneOf"][1] == {
        "$ref": "knowledge-observation.v1.schema.json"
    }
    assert not [k for k in observation["properties"] if k in text_fields and
                observation["properties"][k].get("type") == "string"]


def test_emitted_page_validates_and_carries_the_untrusted_typing() -> None:
    page = _sample_page()
    errors = list(_validator(_FEED).iter_errors(page))
    assert not errors, errors
    observation = page["entries"][0]["observation"]
    for field in ("rule_ref", "observed", "reachable_path", "actual_failure"):
        wrapper = observation[field]
        assert set(wrapper) == {"schema_version", "record_id", "field_path", "policy_version", "value"}
        assert wrapper["field_path"] == field
        assert not list(_validator("untrusted-data.v1.schema.json").iter_errors(wrapper))
    assert not list(_validator(_OBSERVATION).iter_errors(observation))


def _mutations() -> list[tuple[str, object]]:
    def edit(fn):  # noqa: ANN001, ANN202
        page = _sample_page()
        fn(page)
        return page

    return [
        ("plain-string-text", edit(lambda p: p["entries"][0]["observation"].__setitem__("observed", "plain"))),
        ("extra-field", edit(lambda p: p.__setitem__("extra", 1))),
        ("unknown-major", edit(lambda p: p.__setitem__("schema_version", 2))),
        ("too-many-entries", edit(lambda p: p.__setitem__("entries", [p["entries"][1]] * 1001))),
        ("newline-in-text", edit(lambda p: p["entries"][0]["observation"]["observed"].__setitem__("value", "a\nb"))),
        ("bidi-in-text", edit(lambda p: p["entries"][0]["observation"]["observed"].__setitem__("value", "a‮b"))),
        ("trailing-lf-id", edit(lambda p: p["entries"][0]["source"].__setitem__("transaction_id", "tx-1\n"))),
        ("trailing-lf-token", edit(lambda p: p.__setitem__("continuation", "dff1." + "0" * 64 + ".1\n"))),
        ("path-traversal", edit(lambda p: p["entries"][0]["observation"].__setitem__("scope_paths", ["a/../b"]))),
        ("both-observation-and-reason", edit(lambda p: p["entries"][0].__setitem__("none_reason", "superseded"))),
        ("neither", edit(lambda p: p["entries"][0].__setitem__("observation", None))),
        ("bad-unread-reason", edit(lambda p: p["entries"][1].__setitem__("reason_code", "other"))),
        ("overlong-text", edit(lambda p: p["entries"][0]["observation"]["observed"].__setitem__("value", "x" * 601))),
    ]


@pytest.mark.parametrize("label,page", _mutations(), ids=[m[0] for m in _mutations()])
def test_feed_schema_rejects_violations(label: str, page: dict) -> None:
    assert list(_validator(_FEED).iter_errors(page)), label


def test_feed_bounds_and_code_sets_match_the_runtime() -> None:
    feed_schema = _load_schema(_FEED)
    feed = _load_work_loop("dfp_roster_feed", "_delivery_feed.py")
    projector = _load_work_loop("dfp_roster_projection_b", "_knowledge_projection.py")
    assert feed_schema["properties"]["entries"]["maxItems"] == feed.MAX_ENTRIES == 1000
    assert feed_schema["x-max-page-bytes"] == feed.MAX_PAGE_BYTES == 1024 * 1024
    assert feed_schema["x-max-observation-bytes"] == projector.MAX_OBSERVATION_BYTES == 4096
    assert _load_schema(_OBSERVATION)["x-max-observation-bytes"] == 4096
    assert set(feed_schema["x-unread-source-reason-codes"]) == feed.UNREAD_REASONS
    assert set(feed_schema["x-scan-refusal-codes"]) == feed.SCAN_REFUSAL_CODES
    assert set(feed_schema["x-none-reason-codes"]) == feed.NONE_REASONS == projector.NONE_REASONS
    defs = _load_schema(_OBSERVATION)["$defs"]
    assert defs["identifier"]["pattern"] == projector.PATTERNS["identifier"]
    assert defs["repositoryPath"]["pattern"] == projector.PATTERNS["repository_path"]
    assert defs["untrustedText"]["properties"]["value"]["pattern"] == projector.PATTERNS["text"]
    observation = _load_schema(_OBSERVATION)["properties"]
    assert observation["observation_id"]["pattern"] == projector.PATTERNS["observation_id"]
    assert observation["projection_policy_version"]["pattern"] == projector.PATTERNS["version_label"]
    assert feed_schema["$defs"]["factEntry"]["properties"]["none_reason"]["oneOf"][1]["enum"] == sorted(
        feed.NONE_REASONS, key=feed_schema["x-none-reason-codes"].index
    )


def test_projection_runtime_never_reads_a_delivery_schema() -> None:
    """The runtime modules name no contracts path and import no repository package."""
    import ast

    for name in ("_delivery_feed.py", "_knowledge_projection.py", "delivery-fact-feed.py"):
        source = (_WORK_LOOP_SCRIPTS / name).read_text(encoding="utf-8")
        assert "contracts/delivery" not in source.replace("delivery schema", ""), name
        assert ".schema.json" not in source, name
        for node in ast.walk(ast.parse(source)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            assert not [m for m in modules if m.split(".")[0] in {"agentbundle", "credbroker"}], name
