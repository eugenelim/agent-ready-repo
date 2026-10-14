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
    "task-contract.v1.schema.json",
    "execution-request.v1.schema.json",
    "execution-result.v1.schema.json",
    "mechanical-journal.v1.schema.json",
    "effect-resolution.v1.schema.json",
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


def _all_patterns() -> list[tuple[str, str]]:
    """Return ``(location, pattern)`` for every `pattern` in the two projection schemas."""
    found: list[tuple[str, str]] = []

    def walk(node: object, where: str) -> None:
        if isinstance(node, dict):
            pattern = node.get("pattern")
            if isinstance(pattern, str):
                found.append((where, pattern))
            for key, value in node.items():
                walk(value, f"{where}/{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{where}/{index}")

    for name in (_FEED, _OBSERVATION):
        walk(_load_schema(name), name)
    return found


# `\d`, `\D`, `\w`, `\W` are Unicode classes in Python `re` and ASCII-only in ECMA-262, and a
# bare `\s` covers different sets, so none is admitted. `[\s\S]` (any character) is the one
# exact idiom both engines read alike; it is replaced before the escape scan.
_ECMA_ANY_CHARACTER = r"[\s\S]"
_ECMA_PORTABLE_ESCAPE = r"\\(?:u[0-9a-fA-F]{4}|[.\\/\-\[\](){}+*?|^$])"


def test_every_schema_pattern_uses_only_ecma_and_python_portable_syntax() -> None:
    """JSON Schema 2020-12 reads `pattern` as ECMA 262; Python `re` must read it alike.

    Allowed: BMP `\\uXXXX`, the exact `[\\s\\S]` any-character idiom, escaped punctuation
    (`\\-` only inside a class),
    `(?:`, `(?=`, `(?!`. Refused: `\\d`, `\\D`, `\\w`, `\\W` and a bare `\\s` or `\\S` (the two
    engines read them differently), `\\U`, `\\A`, `\\Z`, `\\z`, named groups, atomic or
    possessive forms.
    """
    import re

    patterns = _all_patterns()
    assert len(patterns) >= 10
    for where, pattern in patterns:
        stripped = re.sub(_ECMA_PORTABLE_ESCAPE, "E", pattern.replace(_ECMA_ANY_CHARACTER, "A"))
        assert "\\" not in stripped, (where, "escape outside the portable set", pattern)
        for group in re.finditer(r"\(\?(.?)", stripped):
            assert group.group(1) in (":", "=", "!"), (where, "non-portable group", pattern)
        no_classes = re.sub(r"\[(?:\\.|[^\]\\])*\]", "C", pattern)
        # ECMA `u` mode allows `\-` only inside a character class.
        assert "\\-" not in no_classes, (where, "bare escaped hyphen", pattern)
        assert re.search(r"(?<!\\)[*+?}]\+", no_classes) is None, (where, "possessive", pattern)
    assert not [w for w, p in patterns if "\\U" in p or "(?P" in p]


_ECMA_NODE_SCRIPT = """
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const out = {compiled: [], text: []};
for (const [where, p] of input.patterns) {
  for (const flags of ['', 'u']) {
    try { new RegExp(p, flags); out.compiled.push([where, flags, true]); }
    catch (e) { out.compiled.push([where, flags, false, String(e)]); }
  }
}
for (const flags of ['', 'u']) {
  const re = new RegExp(input.text, flags);
  for (const s of input.accept) out.text.push([flags, 'accept', s, re.test(s)]);
  for (const s of input.refuse) out.text.push([flags, 'refuse', s, re.test(s)]);
  // Astral text: the pattern is defined under `u` (code points); without `u` the
  // surrogate range in the class refuses every astral character.
  for (const s of input.astral) out.text.push([flags, flags === 'u' ? 'accept' : 'refuse', s, re.test(s)]);
}
process.stdout.write(JSON.stringify(out));
"""


def test_every_schema_pattern_compiles_and_behaves_under_an_ecma_engine() -> None:
    """Compile each pattern with and without `u` in Node and test the text pattern.

    The BMP samples behave the same in both modes. The pattern's behaviour is defined under
    `u`: there an astral character such as an emoji is accepted, while without `u` the
    surrogate range in the class refuses every astral character.
    """
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not on PATH, so the ECMA 262 engine check cannot run")
    text_pattern = _load_schema(_OBSERVATION)["$defs"]["untrustedText"]["properties"]["value"]["pattern"]
    accept = ["Step 2 failed", "ABC UXYZ 0123456789 Under U+0041", "plain text, with: punctuation (ok)"]
    refuse = [
        "a\u0000b", "a\u007fb", "a\u0085b", "a\u00adb", "a\u034fb", "a\u061cb", "a\u115fb",
        "a\u17b4b", "a\u180eb", "a\u200bb", "a\u2028b", "a\u202eb", "a\u2060b", "a\u3164b",
        "a\ud800b", "a\ufe0fb", "a\ufeffb", "a\uffa0b", "a\ufff9b", "a\n",
    ]
    astral = ["ok \U0001f600 done", "\U00020000"]
    payload = json.dumps(
        {
            "patterns": _all_patterns(),
            "text": text_pattern,
            "accept": accept,
            "refuse": refuse,
            "astral": astral,
        }
    )
    result = subprocess.run(
        [node, "-e", _ECMA_NODE_SCRIPT], input=payload, capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    bad_compile = [entry for entry in out["compiled"] if not entry[2]]
    assert not bad_compile, bad_compile
    assert len(out["compiled"]) == 2 * len(_all_patterns())
    wrong = [
        (flags, kind, sample)
        for flags, kind, sample, matched in out["text"]
        if matched != (kind == "accept")
    ]
    assert not wrong, wrong
    assert len(out["text"]) == 2 * (len(accept) + len(refuse) + len(astral))


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
        ("bidi-in-text", edit(lambda p: p["entries"][0]["observation"]["observed"].__setitem__("value", "a\u202eb"))),
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
    assert set(feed_schema["x-none-reason-codes"]) == projector.NONE_REASONS
    defs = _load_schema(_OBSERVATION)["$defs"]
    assert defs["identifier"]["pattern"] == projector.PATTERNS["identifier"]
    assert defs["repositoryPath"]["pattern"] == projector.PATTERNS["repository_path"]
    assert defs["untrustedText"]["properties"]["value"]["pattern"] == projector.PATTERNS["text"]
    observation = _load_schema(_OBSERVATION)["properties"]
    assert observation["observation_id"]["pattern"] == projector.PATTERNS["observation_id"]
    assert observation["projection_policy_version"]["pattern"] == projector.PATTERNS["version_label"]
    assert feed_schema["$defs"]["factEntry"]["properties"]["none_reason"]["oneOf"][1]["enum"] == sorted(
        projector.NONE_REASONS, key=feed_schema["x-none-reason-codes"].index
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


# ── Candidate-mode validator parity (Slice 3, task T2) ───────────────────────
# The project-knowledge candidate mode validates a feed page in self-contained
# code. These tests run one differential corpus through `jsonschema` and through
# that validator, and pin the validator's constants to the canonical schemas.

_PROJECT_KNOWLEDGE_SCRIPT = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "project-knowledge" / "scripts" / "project_knowledge.py"
)


def _load_candidate_validator():  # noqa: ANN202 - test-time module loader
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("dfp_roster_project_knowledge", str(_PROJECT_KNOWLEDGE_SCRIPT))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # the module defines dataclasses
    spec.loader.exec_module(module)
    return module


def _corpus_base_page() -> dict:
    """One valid page: a fact with an observation, a fact with none, and an unread source."""
    page = _sample_page()
    observation = page["entries"][0]["observation"]
    page["entries"].insert(
        1,
        {
            "entry_kind": "fact",
            "ordinal": 1,
            "source": {
                "spec_path": "docs/specs/example",
                "transaction_id": "tx-2",
                "record_kind": "evidence-receipt.v1",
                "record_id": "receipt-2",
                "predecessor_schema_version": 1,
            },
            "observation": None,
            "none_reason": "superseded",
        },
    )
    page["entries"][2]["ordinal"] = 2
    page["continuation"] = "dff1." + "c" * 64 + ".3"
    assert observation is page["entries"][0]["observation"]
    return page


def _walk(node: object, path: tuple = ()):  # noqa: ANN202
    """Yield (path, value) for every node of a JSON value."""
    yield path, node
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk(value, (*path, key))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk(value, (*path, index))


def _at(page: dict, path: tuple) -> object:
    node: object = page
    for key in path:
        node = node[key]  # type: ignore[index]
    return node


def _corpus() -> list[tuple[str, dict]]:
    """The valid page plus one violation per schema constraint, generated over the valid page.

    For each node: delete a key (required), add a key (additionalProperties),
    swap its type (type, null, boolean), and, by type, break each bound the
    schema states: string length and pattern, integer range and fractions, array
    length and uniqueness. Named cases cover the keyword combinations that need
    a coordinated edit (oneOf arms, if/then/else, const and enum members).
    """
    import copy

    base = _corpus_base_page()
    cases: list[tuple[str, dict]] = [("valid", copy.deepcopy(base))]

    def add(label: str, path: tuple, replacement: object) -> None:
        page = copy.deepcopy(base)
        if path:
            parent = _at(page, path[:-1])
            parent[path[-1]] = replacement  # type: ignore[index]
        else:
            page = replacement  # type: ignore[assignment]
        cases.append((f"{label}:{'/'.join(map(str, path)) or '<root>'}", page))

    for path, value in _walk(base):
        add("to-string", path, "x")
        add("to-integer", path, 7)
        add("to-boolean", path, True)
        add("to-list", path, [])
        add("to-object", path, {})
        if path:
            add("to-null", path, None)
        if isinstance(value, dict):
            for key in value:
                page = copy.deepcopy(base)
                del _at(page, path)[key]  # type: ignore[arg-type]
                cases.append((f"missing-key:{'/'.join(map(str, (*path, key)))}", page))
            page = copy.deepcopy(base)
            _at(page, path)["extra_key"] = 1  # type: ignore[index]
            cases.append((f"extra-key:{'/'.join(map(str, path)) or '<root>'}", page))
        elif isinstance(value, str):
            add("empty-string", path, "")
            add("trailing-lf", path, value + "\n")
            add("leading-space", path, " " + value)
            add("overlong", path, value + "x" * 700)
            add("control-char", path, value + "\x07")
            add("zero-width", path, value + "\u200b")
            add("bidi", path, value + "\u202e")
            add("nel", path, value + "\u0085")
            add("soft-hyphen", path, value + "\u00ad")
            add("combining-grapheme-joiner", path, value + "\u034f")
            add("hangul-choseong-filler", path, value + "\u115f")
            add("hangul-jungseong-filler", path, value + "\u1160")
            add("khmer-inherent-vowel", path, value + "\u17b4")
            add("khmer-inherent-aa", path, value + "\u17b5")
            add("mongolian-selector", path, value + "\u180b")
            add("mongolian-vowel-separator", path, value + "\u180e")
            add("mongolian-selector-last", path, value + "\u180f")
            add("hangul-filler", path, value + "\u3164")
            add("variation-selector", path, value + "\ufe00")
            add("variation-selector-last", path, value + "\ufe0f")
            add("halfwidth-hangul-filler", path, value + "\uffa0")
            add("tag-first", path, value + "\U000e0000")
            add("tag-latin-a", path, value + "\U000e0041")
            add("tag-last", path, value + "\U000e0fff")
            add("line-separator", path, value + " ")
            add("not-a-member", path, "not-a-member")
        elif isinstance(value, bool):
            continue
        elif isinstance(value, int):
            add("below-range", path, -1)
            add("above-range", path, 10**10)
            add("fraction", path, 0.5)
            add("integral-float", path, float(value))
            add("string-number", path, str(value))
        elif isinstance(value, list):
            add("too-many-items", path, [value[0] if value else "a"] * 1001)
            if value:
                add("duplicate-item", path, [*value, value[0]])
                add("append-null", path, [*value, None])
    # Combinations a per-node edit cannot reach.
    for label, edit in (
        ("oneof-both-arms", lambda p: p["entries"][2].update({"observation": None, "none_reason": "superseded", "source": {}})),
        ("observation-with-reason", lambda p: p["entries"][0].update({"none_reason": "superseded"})),
        ("none-without-reason", lambda p: p["entries"][1].update({"none_reason": None})),
        ("none-with-bad-reason", lambda p: p["entries"][1].update({"none_reason": "other"})),
        ("unread-with-fact-keys", lambda p: p["entries"][2].update({"observation": None})),
        ("fact-kind-on-unread", lambda p: p["entries"][2].update({"entry_kind": "fact"})),
        ("unread-kind-on-fact", lambda p: p["entries"][0].update({"entry_kind": "unread-source"})),
        ("wrong-field-path", lambda p: p["entries"][0]["observation"]["observed"].update({"field_path": "rule_ref"})),
        ("rule-ref-121", lambda p: p["entries"][0]["observation"]["rule_ref"].update({"value": "r" * 121})),
        ("rule-ref-120", lambda p: p["entries"][0]["observation"]["rule_ref"].update({"value": "r" * 120})),
        ("text-600", lambda p: p["entries"][0]["observation"]["observed"].update({"value": "t" * 600})),
        ("text-601", lambda p: p["entries"][0]["observation"]["observed"].update({"value": "t" * 601})),
        ("ten-paths", lambda p: p["entries"][0]["observation"].update({"scope_paths": [f"a/{i}" for i in range(10)]})),
        ("eleven-paths", lambda p: p["entries"][0]["observation"].update({"scope_paths": [f"a/{i}" for i in range(11)]})),
        ("path-dot-segment", lambda p: p["entries"][0]["observation"].update({"scope_paths": ["a/./b"]})),
        ("path-trailing-dot", lambda p: p["entries"][0]["observation"].update({"scope_paths": ["a/b."]})),
        ("path-leading-slash", lambda p: p["entries"][0]["observation"].update({"scope_paths": ["/a/b"]})),
        ("spec-path-dotdot", lambda p: p["entries"][0]["source"].update({"spec_path": "docs/specs/.."})),
        ("spec-path-nested", lambda p: p["entries"][0]["source"].update({"spec_path": "docs/specs/a/b"})),
        ("snapshot-uppercase", lambda p: p.update({"snapshot_id": "snapshot-sha256-" + "A" * 64})),
        ("continuation-null", lambda p: p.update({"continuation": None})),
        ("continuation-short", lambda p: p.update({"continuation": "dff1." + "c" * 63 + ".3"})),
        ("continuation-ten-digits", lambda p: p.update({"continuation": "dff1." + "c" * 64 + ".1234567890"})),
        ("ordinal-max", lambda p: p["entries"][0].update({"ordinal": 999_999_999})),
        ("ordinal-over-max", lambda p: p["entries"][0].update({"ordinal": 1_000_000_000})),
        ("predecessor-version-1000", lambda p: p["entries"][0]["source"].update({"predecessor_schema_version": 1000})),
        ("predecessor-version-1001", lambda p: p["entries"][0]["source"].update({"predecessor_schema_version": 1001})),
        ("predecessor-version-zero", lambda p: p["entries"][0]["source"].update({"predecessor_schema_version": 0})),
        ("identifier-128", lambda p: p["entries"][0]["source"].update({"transaction_id": "a" * 128})),
        ("identifier-129", lambda p: p["entries"][0]["source"].update({"transaction_id": "a" * 129})),
        ("identifier-leading-dash", lambda p: p["entries"][0]["source"].update({"transaction_id": "-a"})),
        ("1000-entries", lambda p: p.update({"entries": [p["entries"][2]] * 1000})),
        ("1001-entries", lambda p: p.update({"entries": [p["entries"][2]] * 1001})),
        ("empty-entries", lambda p: p.update({"entries": []})),
        ("shadow-disabled", lambda p: p.update({"shadow_services": "disabled"})),
        ("kind-pattern", lambda p: p["entries"][0]["observation"].update({"kind": "pattern"})),
        ("observation-schema-version-2", lambda p: p["entries"][0]["observation"].update({"schema_version": 2})),
        ("wrapper-schema-version-2", lambda p: p["entries"][0]["observation"]["observed"].update({"schema_version": 2})),
        ("version-label-33", lambda p: p["entries"][0]["observation"].update({"projection_policy_version": "a" * 33})),
        ("version-label-upper", lambda p: p["entries"][0]["observation"].update({"content_policy_version": "V1"})),
        ("lone-surrogate", lambda p: p["entries"][0]["observation"]["observed"].update({"value": "a\ud800b"})),
    ):
        page = copy.deepcopy(base)
        edit(page)
        cases.append((label, page))
    return cases


def _observation_at(page: dict, path: str) -> dict:
    """Return the entry observation a corpus path (`...entries/N/observation/...`) lies in."""
    entries = path.split("entries/", 1)[1].split("/", 1)[0]
    return page["entries"][int(entries)]["observation"]


def _consumer_accepts(module, page: object) -> bool:  # noqa: ANN001
    try:
        raw = json.dumps(page, ensure_ascii=True).encode("ascii")
        module.parse_feed_page(raw)
    except (ValueError, TypeError):
        return False
    return True


def test_the_candidate_validator_agrees_with_jsonschema_on_every_corpus_page() -> None:
    module = _load_candidate_validator()
    validator = _validator(_FEED)
    cases = _corpus()
    assert len(cases) > 500
    disagreements = []
    accepted_tags: list[str] = []
    rejected = 0
    for label, page in cases:
        schema_ok = not list(validator.iter_errors(page))
        consumer_ok = _consumer_accepts(module, page)
        rejected += not schema_ok
        if label.startswith("tag-"):
            # The one documented asymmetry: a JSON Schema pattern cannot express the
            # astral tag range portably, so `jsonschema` accepts a tag character in
            # free text. The validator accepts the page too and omits that candidate
            # per candidate (`unsafe_character`); a path field still refuses the page.
            _, path = label.split(":", 1)
            if "/observation/" in path and path.endswith("/value"):
                assert schema_ok and consumer_ok, label
                assert module.candidate_omission_reason(_observation_at(page, path)) == "unsafe_character", label
                accepted_tags.append(label)
            else:
                assert schema_ok == consumer_ok, label
        elif schema_ok != consumer_ok:
            disagreements.append((label, schema_ok, consumer_ok))
    assert not disagreements, disagreements[:10]
    text_fields = ("rule_ref", "observed", "reachable_path", "actual_failure")
    for label in accepted_tags:
        _, path = label.split(":", 1)
        assert path.split("/")[-2] in text_fields, label
    assert accepted_tags, "the tag-character case must be exercised on free text"
    assert rejected > 400, "the corpus must exercise many refusals, not only acceptances"
    assert _consumer_accepts(module, cases[0][1]) and not list(validator.iter_errors(cases[0][1]))


def test_the_corpus_exercises_every_constraint_keyword_in_the_schemas() -> None:
    """Each keyword the two schemas use is broken by at least one corpus page the schema rejects."""
    wanted = {"required", "additionalProperties", "type", "enum", "const", "minLength", "maxLength",
              "pattern", "minimum", "maximum", "maxItems", "uniqueItems", "oneOf", "if"}
    used: set[str] = set()

    def keywords(node: object) -> None:
        if isinstance(node, dict):
            used.update(k for k in node if k in wanted)
            for value in node.values():
                keywords(value)
        elif isinstance(node, list):
            for value in node:
                keywords(value)

    for name in (_FEED, _OBSERVATION, "untrusted-data.v1.schema.json"):
        keywords(_load_schema(name))
    seen: set[str] = set()
    validator = _validator(_FEED)

    def collect(error) -> None:  # noqa: ANN001 - jsonschema ValidationError
        seen.add(error.validator)
        for inner in error.context or ():
            collect(inner)

    for _label, page in _corpus()[1:]:
        for error in validator.iter_errors(page):
            collect(error)
    assert used <= wanted
    # `if` is exercised through its then and else arms, which report their own keywords.
    assert used - {"if"} <= seen, used - seen


def test_no_constraint_the_consumer_enforces_relies_on_annotation_only_format() -> None:
    for name in (_FEED, _OBSERVATION):
        assert '"format"' not in json.dumps(_load_schema(name)), name


def test_the_candidate_validator_constants_match_the_canonical_schemas() -> None:
    import re

    module = _load_candidate_validator()
    feed = _load_schema(_FEED)
    observation = _load_schema(_OBSERVATION)
    defs = observation["$defs"]

    def normalize(pattern: str) -> str:
        return re.sub(
            r"\\u([0-9a-fA-F]{4})",
            lambda m: chr(int(m.group(1), 16)),
            pattern,
        )

    expected = {
        "identifier": defs["identifier"]["pattern"],
        "spec_path": defs["specPath"]["pattern"],
        "repository_path": defs["repositoryPath"]["pattern"],
        "text": defs["untrustedText"]["properties"]["value"]["pattern"],
        "field_path": defs["untrustedText"]["properties"]["field_path"]["pattern"],
        "snapshot_id": feed["properties"]["snapshot_id"]["pattern"],
        "continuation": feed["properties"]["continuation"]["oneOf"][1]["pattern"],
        "observation_id": observation["properties"]["observation_id"]["pattern"],
        "version_label": observation["properties"]["projection_policy_version"]["pattern"],
    }
    assert set(module.FEED_PATTERNS) == set(expected)
    for name, pattern in expected.items():
        assert normalize(module.FEED_PATTERNS[name]) == normalize(pattern), name
    assert defs["untrustedText"]["properties"]["policy_version"]["pattern"] == expected["version_label"]
    assert observation["properties"]["content_policy_version"]["pattern"] == expected["version_label"]
    assert defs["untrustedText"]["properties"]["record_id"]["pattern"] == expected["identifier"]

    assert module.FEED_PAGE_MAX_BYTES == feed["x-max-page-bytes"] == 1024 * 1024
    assert module.FEED_PAGE_MAX_ENTRIES == feed["properties"]["entries"]["maxItems"] == 1000
    assert module.FEED_OBSERVATION_MAX_BYTES == feed["x-max-observation-bytes"] == observation["x-max-observation-bytes"]
    assert set(module.FEED_NONE_REASONS) == set(feed["x-none-reason-codes"])
    assert set(module.FEED_UNREAD_REASONS) == set(feed["x-unread-source-reason-codes"])
    assert tuple(module.FEED_RECORD_KINDS) == tuple(
        feed["$defs"]["factEntry"]["properties"]["source"]["properties"]["record_kind"]["enum"]
    )
    assert observation["properties"]["scope_paths"]["maxItems"] == 10
    assert observation["properties"]["rule_ref"]["allOf"][1]["properties"]["value"]["maxLength"] == 120
    assert defs["untrustedText"]["properties"]["value"]["maxLength"] == 600
    assert module.CANDIDATE_OUTPUT_MAX_BYTES == 32 * 1024


def test_the_observation_byte_bound_is_a_consumer_rule_the_schema_cannot_state() -> None:
    """A page the schema accepts but whose observation exceeds 4 KiB is refused by the consumer."""
    module = _load_candidate_validator()
    page = _corpus_base_page()
    observation = page["entries"][0]["observation"]
    for field in ("observed", "reachable_path", "actual_failure"):
        observation[field]["value"] = "y" * 600
    observation["scope_paths"] = [f"packs/core/example/{'z' * 200}/{i}.py" for i in range(10)]
    assert not list(_validator(_FEED).iter_errors(page))
    assert not _consumer_accepts(module, page)


# ── Execution supervisor core contracts ──────────────────────────────────────
# One valid and one invalid fixture per supervisor schema, and one request per
# request kind. Emitted-record parity for the shipped supervisor lives in the
# work-loop supervisor suites, which validate every record a run writes.

_SUPERVISOR_SPEC = "docs/specs/execution-supervisor-core/"
_HEX = "0" * 64
_REQUEST_KINDS = (
    "implement-task", "write-stub", "run-gates", "review-role", "assess-finding",
    "external-effect", "effect-query", "regenerate", "human-decision",
)


def _task_contract() -> dict:
    return {
        "schema_version": 1,
        "task_id": "calculator-answers",
        "title": "Calculator answers",
        "position": "T1",
        "revision": _HEX,
        "depends_on": [],
        "touches": ["calc.py"],
        "done_when": "the calculator test passes",
        "effects": [],
        "verification_mode": "TDD",
        "stubs": [{"path": "test_calc.py", "run": "python -m pytest {path}",
                   "red_exit": [1], "digest": _HEX}],
        "stub_digest": _HEX,
        "no_stub": False,
    }


def _request(kind: str) -> dict:
    base = {"schema_version": 1, "request_id": f"{kind}:1", "run_id": "run-1",
            "spec": "docs/specs/example", "kind": kind, "stage": "implementing"}
    task = {"task_id": "calculator-answers", "title": "Calculator answers", "revision": _HEX}
    effect = {"operation_key": "run-1:push", "name": "push", "scope": "task", "dispatch": 1}
    extra = {
        "implement-task": {"task": task, "attempt": 1},
        "write-stub": {"task": task, "stubs": _task_contract()["stubs"]},
        "run-gates": {"stage": "gating", "acceptance_fingerprint": "fp", "criteria": ["AC-0001"]},
        "review-role": {"stage": "reviewing", "role": "adversarial-reviewer",
                        "review_subject_fingerprint": "subject-1",
                        "review_subject": _review_subject()},
        "assess-finding": {"stage": "reviewing", "role": "adversarial-reviewer",
                           "review_subject_fingerprint": "subject-1",
                           "report_id": "report-1", "finding_id": "finding-1"},
        "external-effect": {"effect": effect},
        "effect-query": {"effect": effect},
        "regenerate": {"stage": "gating"},
        "human-decision": {"stage": "awaiting-human", "reason": "retry-cap",
                           "question": "The retry cap is reached. How should the run continue?"},
    }[kind]
    return {**base, **extra}


def _result() -> dict:
    return {"schema_version": 1, "request_id": "implement-task:1", "run_id": "run-1",
            "kind": "implement-task", "gate": {"passed": True}}


def _journal_line() -> dict:
    return {"schema_version": 1, "run_id": "run-1", "at": "2026-10-13T00:00:00Z",
            "head": "a" * 40, "stage": "implementing", "kind": "implement-task",
            "request_id": "impl:calculator-answers:" + _HEX + ":1"}


def _effect_resolution() -> dict:
    return {"schema_version": 1, "entry": "decision", "operation_key": "run-1:push",
            "run_id": "run-1", "effect": "push", "scope": "task", "task_id": "release",
            "resolution_id": "resolution-1", "decision": "retry-authorized",
            "authority_ref": "effect-authority:0123456789ab", "at": "2026-10-13T00:00:00Z"}


_SUPERVISOR_VALID = {
    "task-contract.v1.schema.json": _task_contract,
    "execution-request.v1.schema.json": lambda: _request("implement-task"),
    "execution-result.v1.schema.json": _result,
    "mechanical-journal.v1.schema.json": _journal_line,
    "effect-resolution.v1.schema.json": _effect_resolution,
}


def _drop(field: str):  # noqa: ANN202 - fixture mutator factory
    def mutate(record: dict) -> dict:
        record.pop(field)
        return record
    return mutate


def _set(path: tuple[str, ...], value: object):  # noqa: ANN202 - fixture mutator factory
    def mutate(record: dict) -> dict:
        target = record
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        return record
    return mutate


_SUPERVISOR_INVALID = {
    "task-contract.v1.schema.json": _set(("position",), "Task one"),
    "execution-request.v1.schema.json": _drop("attempt"),
    "execution-result.v1.schema.json": _drop("gate"),
    "mechanical-journal.v1.schema.json": _set(("kind",), "lease"),
    "effect-resolution.v1.schema.json": _set(("authority_ref",), "owner:0123456789ab"),
}


def test_supervisor_schemas_point_at_the_core_spec() -> None:
    for name in _SUPERVISOR_VALID:
        assert _SUPERVISOR_SPEC in _load_schema(name)["x-spec"], name


@pytest.mark.parametrize("name", sorted(_SUPERVISOR_VALID))
def test_supervisor_schema_accepts_its_valid_fixture(name: str) -> None:
    errors = list(_validator(name).iter_errors(_SUPERVISOR_VALID[name]()))
    assert not errors, f"valid {name} rejected: {errors}"


@pytest.mark.parametrize("name", sorted(_SUPERVISOR_INVALID))
def test_supervisor_schema_rejects_its_invalid_fixture(name: str) -> None:
    record = _SUPERVISOR_INVALID[name](_SUPERVISOR_VALID[name]())
    assert list(_validator(name).iter_errors(record)), f"invalid {name} accepted"


@pytest.mark.parametrize("kind", _REQUEST_KINDS)
def test_one_request_per_request_kind_validates(kind: str) -> None:
    errors = list(_validator("execution-request.v1.schema.json").iter_errors(_request(kind)))
    assert not errors, f"{kind} request rejected: {errors}"


def test_request_kinds_are_exactly_the_closed_set() -> None:
    enum = _load_schema("execution-request.v1.schema.json")["properties"]["kind"]["enum"]
    assert tuple(enum) == _REQUEST_KINDS
