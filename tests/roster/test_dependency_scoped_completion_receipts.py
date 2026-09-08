"""Contract tests for dependency-scoped completion receipts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_SCHEMA = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
WORKSPACE_ENTRY_SCHEMA = ROOT / "contracts/jsonschema/workspace-entry.schema.json"
ENGINE_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
STATUS_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
CLOSE_WORK_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/close_work.py"
DEPENDANT = "docs/specs/dependant/spec.md"
PRUNED_DEPENDENCY = "docs/specs/pruned-dependency/spec.md"
RECEIPTLESS_DEPENDENCY = "docs/specs/receiptless-dependency/spec.md"


def _load_module(path: Path, label: str) -> ModuleType:
    """Load a workspace-status module under a collision-safe temporary name."""
    module_name = f"_completion_receipts_{label}_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


ENGINE = _load_module(ENGINE_PATH, "engine")
CLOSE_WORK = _load_module(CLOSE_WORK_PATH, "close_work")


def _write_spec(root: Path, path: str, status: str, *, plan: bool = False) -> None:
    """Write the minimum artifact metadata used by workspace-status."""
    artifact = root / path
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(f"# Spec\n\n- **Status:** {status}\n", encoding="utf-8")
    if plan:
        (artifact.parent / "plan.md").write_text(
            "# Plan\n\n- **Status:** Approved\n", encoding="utf-8"
        )


def _toml_value(value: object) -> str:
    """Render a scalar fixture value, including one deliberate TOML date."""
    if value == _UNQUOTED_DATE:
        return "2026-09-02"
    return json.dumps(value)


_UNQUOTED_DATE = object()


def _fixture(
    tmp_path: Path,
    keep_membership: bool,
    outcome: str,
    *,
    receipt_changes: dict[str, object] | None = None,
    omit_receipt_field: str | None = None,
    extra_receipt_field: bool = False,
    target_status: str | None = None,
) -> Path:
    """Build the receipt fixture; membership is the AC4/AC5 discriminator."""
    _write_spec(tmp_path, DEPENDANT, "Approved", plan=True)
    _write_spec(tmp_path, RECEIPTLESS_DEPENDENCY, "Shipped")
    if target_status is not None:
        _write_spec(tmp_path, PRUNED_DEPENDENCY, target_status)
    dependency_entry = (
        f'{{path = "{PRUNED_DEPENDENCY}", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "pruned", needs = []}'
    )
    shipped = f"[{dependency_entry}]" if keep_membership else "[]"
    receipt: dict[str, object] = {
        "delivery_id": "delivery-123",
        "outcome": outcome,
        "completion_event": "merge",
        "evidence_ref": "pr:123",
    }
    receipt.update(receipt_changes or {})
    if omit_receipt_field is not None:
        receipt.pop(omit_receipt_field)
    if extra_receipt_field:
        receipt["unexpected"] = "value"
    rendered_receipt = ", ".join(
        f"{key} = {_toml_value(value)}" for key, value in receipt.items()
    )
    receipt_need = (
        f'{{type = "local", kind = "spec", path = "{PRUNED_DEPENDENCY}", '
        f"receipt = {{{rendered_receipt}}}}}"
    )
    receiptless_need = (
        f'{{type = "local", kind = "spec", path = "{RECEIPTLESS_DEPENDENCY}"}}'
    )
    dependant_entry = (
        f'{{path = "{DEPENDANT}", kind = "spec", '
        'source = {mode = "repo-origin"}, summary = "dependant", '
        f'needs = [{receipt_need}, {receiptless_need}]}}'
    )
    workspace = "\n".join(
        [
            '["ini-001"]',
            'name = "Receipt fixture"',
            'status = "active"',
            'milestone = "receipt"',
            "",
            '["ini-001".work]',
            f"queue = [{dependant_entry}]",
            "active = []",
            f"shipped = {shipped}",
            "",
            "[backlog]",
            "open = []",
            "closed = []",
            "",
        ]
    )
    (tmp_path / "workspace.toml").write_text(workspace, encoding="utf-8")
    return tmp_path


def _run_status(root: Path) -> dict[str, Any]:
    """Run the shipped status command and return its JSON projection."""
    completed = subprocess.run(
        [sys.executable, str(STATUS_PATH), "status", "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    # Plan-owned guard: every engine fixture must remain a successful CLI run.
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert isinstance(result, dict)
    # AC14: every engine fixture also exercises an unchanged receiptless need.
    assert _codes_for(result, RECEIPTLESS_DEPENDENCY) == set()
    return result


def _codes_for(result: dict[str, Any], path: str) -> set[str]:
    """Return canonical finding codes attributed to *path*."""
    return {
        finding["code"]
        for finding in result["canonical"]["findings"]
        if finding["path"] == path
    }


def _parsed(result: dict[str, Any], path: str) -> bool:
    """Whether *path* survived parsing, wherever the entry finally lands.

    A need finding discards the whole citing entry, so an entry that vanished
    and one that resolved are indistinguishable by finding codes alone: no code
    is attributed to a dependency path that no longer has an entry citing it.
    Membership of any canonical collection is what separates them.
    """
    return any(
        entry["path"] == path
        for collection in ("ready", "blocked", "active")
        for entry in result["canonical"][collection]
    )


def _load(path: Path) -> dict[str, Any]:
    """Load one JSON object from *path*."""
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _receipt(**changes: str) -> dict[str, str]:
    """Return a valid receipt with the requested field changes."""
    receipt = {
        "delivery_id": "delivery-123",
        "outcome": "completed",
        "completion_event": "merge",
        "evidence_ref": "pr:123",
    }
    receipt.update(changes)
    return receipt


def _entry(need: dict[str, Any]) -> dict[str, Any]:
    """Wrap one local need in a valid workspace entry document."""
    return {
        "path": "docs/specs/dependant/spec.md",
        "kind": "spec",
        "source": {"mode": "repo-origin"},
        "summary": "A dependant delivery.",
        "needs": [need],
    }


def _need(*, kind: str = "spec", receipt: dict[str, str] | None = None) -> dict[str, Any]:
    """Return a local need, adding a receipt only when supplied."""
    need: dict[str, Any] = {
        "type": "local",
        "kind": kind,
        "path": "docs/specs/dependency/spec.md",
    }
    if receipt is not None:
        need["receipt"] = receipt
    return need


RECEIPT_KEYS = ("delivery_id", "outcome", "completion_event", "evidence_ref")
ADMITTED_KINDS = ("intent", "research", "design", "brief", "spec")


SCHEMA_CASES = [
    pytest.param(_entry(_need()), True, id="receipt-omitted"),
    pytest.param(_entry(_need(receipt=_receipt())), True, id="four-key-receipt"),
    *[
        pytest.param(
            _entry(_need(receipt={key: value for key, value in _receipt().items() if key != omitted})),
            False,
            id=f"missing-{omitted}",
        )
        for omitted in RECEIPT_KEYS
    ],
    pytest.param(
        _entry(_need(receipt={**_receipt(), "unexpected": "value"})),
        False,
        id="fifth-receipt-key",
    ),
    *[
        pytest.param(
            _entry(_need(receipt=_receipt(outcome=outcome))),
            True,
            id=f"outcome-{outcome}",
        )
        for outcome in ("completed", "abandoned", "superseded")
    ],
    *[
        pytest.param(
            _entry(_need(receipt=_receipt(outcome=outcome))),
            False,
            id=f"rejected-outcome-{outcome or 'empty'}",
        )
        for outcome in ("Cooling", "Retained", "Retired", "ExternalAdvisory", "")
    ],
    *[
        pytest.param(
            _entry(_need(kind=kind, receipt=_receipt())),
            True,
            id=f"receipt-kind-{kind}",
        )
        for kind in ADMITTED_KINDS
    ],
    pytest.param(_entry(_need(kind="defect", receipt=_receipt())), False, id="defect-with-receipt"),
    pytest.param(_entry(_need(kind="defect")), True, id="defect-without-receipt"),
    pytest.param(
        _entry(_need(receipt=_receipt(delivery_id="Delivery:123"))),
        False,
        id="invalid-delivery-id-grammar",
    ),
    pytest.param(
        _entry(_need(receipt=_receipt(completion_event="work-loop:gates-clean"))),
        False,
        id="invalid-completion-event-grammar",
    ),
    pytest.param(
        _entry(_need(receipt=_receipt(evidence_ref="evidence:current"))),
        False,
        id="invalid-evidence-ref-grammar",
    ),
]


@pytest.mark.parametrize(("document", "accepted"), SCHEMA_CASES)
def test_receipt_schema_acceptance_table(document: dict[str, Any], accepted: bool) -> None:  # AC1, AC2
    """The workspace schema accepts exactly the published receipt shapes."""
    validator = Draft202012Validator(_load(WORKSPACE_ENTRY_SCHEMA))
    assert validator.is_valid(document) is accepted


def test_the_receipt_grammars_equal_the_lifecycle_records() -> None:  # AC3
    """The published schema's three receipt grammars equal the lifecycle record's."""
    lifecycle = _load(LIFECYCLE_SCHEMA)
    receipt = _load(WORKSPACE_ENTRY_SCHEMA)["$defs"]["localNeed"]["properties"]["receipt"]["properties"]
    assert receipt["delivery_id"]["pattern"] == lifecycle["properties"]["delivery_id"]["pattern"]
    assert receipt["completion_event"]["enum"] == lifecycle["properties"]["completion_event"]["enum"]
    assert receipt["evidence_ref"]["pattern"] == lifecycle["$defs"]["evidenceRef"]["pattern"]


def test_the_producer_receipt_grammars_equal_the_lifecycle_records() -> None:  # AC3
    """close-work applies exactly the three lifecycle-record receipt grammars.

    This arm lives here rather than beside the other producer tests because
    `tools/lint-pack-test-boundary.py` refuses a pack test that reads a
    repository-level contract, and names `tests/roster` as its home. Keeping all
    three arms in one file also means one lifecycle read backs all of them.
    """
    lifecycle = _load(LIFECYCLE_SCHEMA)
    assert (
        lifecycle["properties"]["delivery_id"]["pattern"]
        == CLOSE_WORK._COMPLETION_RECEIPT_DELIVERY_ID_RE
    )
    assert (
        lifecycle["properties"]["completion_event"]["enum"]
        == list(CLOSE_WORK._COMPLETION_RECEIPT_EVENTS)
    )
    assert (
        lifecycle["$defs"]["evidenceRef"]["pattern"]
        == CLOSE_WORK._COMPLETION_RECEIPT_EVIDENCE_REF_RE
    )


def test_the_engine_receipt_grammars_equal_the_lifecycle_records() -> None:  # AC3
    """The engine reads exactly the three lifecycle-record receipt grammars."""
    lifecycle = _load(LIFECYCLE_SCHEMA)
    assert (
        lifecycle["properties"]["delivery_id"]["pattern"]
        == ENGINE._COMPLETION_RECEIPT_DELIVERY_ID_RE
    )
    assert lifecycle["properties"]["completion_event"]["enum"] == list(
        ENGINE._COMPLETION_RECEIPT_EVENTS
    )
    assert (
        lifecycle["$defs"]["evidenceRef"]["pattern"]
        == ENGINE._COMPLETION_RECEIPT_EVIDENCE_REF_RE
    )


def _plan_valid_receipt(**overrides: str):
    """Plan one producer receipt whose issued authority matches its evidence_ref."""
    fields = {
        "delivery_id": "delivery-wave7a",
        "outcome": "completed",
        "completion_event": "release",
        "evidence_ref": "commit:" + "a" * 40,
        **overrides,
    }
    record = {
        "authorized_actor_role": "repository-maintainer",
        "grant_source": "policy:maintainer-closeout",
        "action": "write-completion-receipt",
        "resource": "runtime-coordination:workspace",
        "evidence_ref": fields["evidence_ref"],
        "host_session_provenance": "session:current",
    }
    fact = CLOSE_WORK.resolve_mutation_authority(
        grant_record=record, authority_evidence_ref="authority:resolved-policy"
    )
    assert fact is not None
    # evidence_ref is dual-purpose: the producer folds it into the equality check
    # against the issued authority fact, so it is supplied once, by the record.
    receipt_only = {k: v for k, v in fields.items() if k != "evidence_ref"}
    return CLOSE_WORK.plan_completion_receipt(
        live_dependency=True,
        compatible_surface="runtime-coordination:workspace",
        **receipt_only,
        **record,
        authority_fact=fact,
    )


def test_the_producer_accepts_every_published_outcome() -> None:  # AC12
    """Narrowing the producer's vocabulary must redden something.

    The refusal cases alone cannot catch narrowing: they stay green while
    close-work silently rejects a legitimate `abandoned` or `superseded`
    closeout. The members are read from the published schema rather than
    restated, so a vocabulary change has one home.
    """
    published = _load(WORKSPACE_ENTRY_SCHEMA)["$defs"]["localNeed"]["properties"][
        "receipt"
    ]["properties"]["outcome"]["enum"]
    assert len(published) == 3
    for outcome in published:
        result = _plan_valid_receipt(outcome=outcome)
        assert result.code == "receipt-write-confirmation-required", outcome


def test_the_producer_accepts_every_published_completion_event() -> None:  # AC12
    """Every event the lifecycle record admits must reach confirmation."""
    published = _load(LIFECYCLE_SCHEMA)["properties"]["completion_event"]["enum"]
    assert len(published) == 3
    for event in published:
        result = _plan_valid_receipt(completion_event=event)
        assert result.code == "receipt-write-confirmation-required", event


@pytest.mark.parametrize(
    "evidence_ref", ["commit:" + "a" * 40, "pr:123", "run:456"], ids=["commit", "pr", "run"]
)
def test_the_producer_accepts_every_evidence_ref_alternative(evidence_ref: str) -> None:  # AC12
    """Each alternative is first checked against the record's own pattern.

    The pattern cannot be enumerated, so each sample is validated against the
    grammar read from the lifecycle record before it is offered to the producer.
    A sample that stopped being valid would fail here rather than silently
    weakening the acceptance claim.
    """
    pattern = _load(LIFECYCLE_SCHEMA)["$defs"]["evidenceRef"]["pattern"]
    assert re.fullmatch(pattern, evidence_ref), evidence_ref
    result = _plan_valid_receipt(evidence_ref=evidence_ref)
    assert result.code == "receipt-write-confirmation-required"


def test_the_engine_receipt_bound_equals_the_producers() -> None:
    """A receipt close-work can write is one the engine will not refuse on length.

    The producer bounds all four fields at its own MAX_TEXT_LENGTH before
    constructing a receipt. If the engine bounded them lower, close-work could
    emit a receipt the consumer then rejected — the exact asymmetry AC12 exists
    to close, in the opposite direction.
    """
    assert CLOSE_WORK.MAX_TEXT_LENGTH == ENGINE._COMPLETION_RECEIPT_MAX_FIELD_LENGTH


def test_workspace_entry_schema_fallback_digest_matches_the_shipped_schema() -> None:
    """The adopter-install fallback digest follows the shipped schema bytes."""
    digest = hashlib.sha256(WORKSPACE_ENTRY_SCHEMA.read_bytes()).hexdigest()
    assert digest == ENGINE._WORKSPACE_ENTRY_SCHEMA_DIGEST


def test_a_completed_receipt_satisfies_a_pruned_dependency(tmp_path):  # AC4
    """Entry gone and file gone: a valid completed receipt resolves the edge."""
    result = _run_status(_fixture(tmp_path, keep_membership=False, outcome="completed"))
    assert DEPENDANT in {entry["path"] for entry in result["canonical"]["ready"]}
    assert _codes_for(result, DEPENDANT) == set()


def test_the_engine_satisfies_on_every_published_completion_event(tmp_path: Path) -> None:  # AC4
    """Narrowing the engine's event rule must redden something.

    `_fixture` fixes one event, so without this every engine case proves the
    satisfying path for `merge` alone: narrowing the validator's application to
    `!= "merge"` would refuse valid `release` and `acceptance` receipts with
    `invalid_completion_receipt` while the whole suite stayed green. This is the
    consumer twin of the producer coverage, and the same asymmetry the producer
    mutation exposed. Members are read from the lifecycle record, not restated.
    """
    published = _load(LIFECYCLE_SCHEMA)["properties"]["completion_event"]["enum"]
    assert len(published) == 3
    for event in published:
        result = _run_status(
            _fixture(
                tmp_path / event,
                keep_membership=False,
                outcome="completed",
                receipt_changes={"completion_event": event},
            )
        )
        assert DEPENDANT in {e["path"] for e in result["canonical"]["ready"]}, event
        assert _codes_for(result, PRUNED_DEPENDENCY) == set(), event


@pytest.mark.parametrize(
    "evidence_ref",
    ["commit:" + "b" * 40, "pr:7", "run:99"],
    ids=["commit", "pr", "run"],
)
def test_the_engine_satisfies_on_every_evidence_ref_alternative(
    tmp_path: Path, evidence_ref: str
) -> None:  # AC4
    """Each alternative is checked against the record's grammar, then accepted.

    The pattern cannot be enumerated, so each sample is validated against the
    grammar read from the lifecycle record before the engine sees it; a sample
    that stopped being valid fails here rather than weakening the claim.
    """
    pattern = _load(LIFECYCLE_SCHEMA)["$defs"]["evidenceRef"]["pattern"]
    assert re.fullmatch(pattern, evidence_ref), evidence_ref
    result = _run_status(
        _fixture(
            tmp_path,
            keep_membership=False,
            outcome="completed",
            receipt_changes={"evidence_ref": evidence_ref},
        )
    )
    assert DEPENDANT in {e["path"] for e in result["canonical"]["ready"]}
    assert _codes_for(result, PRUNED_DEPENDENCY) == set()


# Lifecycle-valid delivery ids that do not share the `delivery-` prefix every
# other accepting fixture happens to carry. Without these, a narrowing added at
# either application site that additionally demanded that prefix would leave the
# exported constants untouched and the whole suite green.
_UNPREFIXED_DELIVERY_IDS = ["rfc0096-wave7a-ii", "x9"]


@pytest.mark.parametrize("delivery_id", _UNPREFIXED_DELIVERY_IDS)
def test_the_engine_satisfies_on_delivery_ids_without_the_common_prefix(
    tmp_path: Path, delivery_id: str
) -> None:  # AC4
    """The engine applies the record's delivery_id grammar, not a narrower one."""
    pattern = _load(LIFECYCLE_SCHEMA)["properties"]["delivery_id"]["pattern"]
    assert re.fullmatch(pattern, delivery_id), delivery_id
    result = _run_status(
        _fixture(
            tmp_path,
            keep_membership=False,
            outcome="completed",
            receipt_changes={"delivery_id": delivery_id},
        )
    )
    assert DEPENDANT in {e["path"] for e in result["canonical"]["ready"]}
    assert _codes_for(result, PRUNED_DEPENDENCY) == set()


@pytest.mark.parametrize("delivery_id", _UNPREFIXED_DELIVERY_IDS)
def test_the_producer_accepts_delivery_ids_without_the_common_prefix(
    delivery_id: str,
) -> None:  # AC12
    """close-work applies the record's delivery_id grammar, not a narrower one."""
    pattern = _load(LIFECYCLE_SCHEMA)["properties"]["delivery_id"]["pattern"]
    assert re.fullmatch(pattern, delivery_id), delivery_id
    result = _plan_valid_receipt(delivery_id=delivery_id)
    assert result.code == "receipt-write-confirmation-required"


def test_surviving_membership_refuses_before_the_receipt(tmp_path: Path) -> None:  # AC5
    """A target still registered as shipped cannot resolve through its receipt."""
    result = _run_status(_fixture(tmp_path, keep_membership=True, outcome="completed"))
    assert "unsatisfied_dependency" in _codes_for(result, PRUNED_DEPENDENCY)


@pytest.mark.parametrize("outcome", ["abandoned", "superseded"])
def test_noncompleted_receipt_does_not_satisfy_dependency(
    tmp_path: Path, outcome: str
) -> None:  # AC6
    """A valid receipt satisfies the dependency only when work completed."""
    result = _run_status(_fixture(tmp_path, keep_membership=False, outcome=outcome))
    assert "unsatisfied_dependency" in _codes_for(result, PRUNED_DEPENDENCY)


MALFORMED_RECEIPT_CASES = [
    pytest.param({"omit_receipt_field": "delivery_id"}, id="missing-field"),
    pytest.param({"extra_receipt_field": True}, id="extra-field"),
    pytest.param(
        {"receipt_changes": {"evidence_ref": _UNQUOTED_DATE}}, id="non-string-date"
    ),
    pytest.param(
        {"receipt_changes": {"delivery_id": "Delivery:123"}}, id="delivery-id-grammar"
    ),
    pytest.param(
        {"receipt_changes": {"completion_event": "work-loop:gates-clean"}},
        id="completion-event-grammar",
    ),
    pytest.param(
        {"receipt_changes": {"evidence_ref": "evidence:current"}},
        id="evidence-ref-grammar",
    ),
    pytest.param({"receipt_changes": {"outcome": "Retired"}}, id="outcome-vocabulary"),
    # Inside the pinned evidence_ref grammar — `pr:` plus digits — so the length
    # bound is the only rule that can reject it. Without that bound the value
    # reaches Dependency and is serialized into the routing identity every run.
    pytest.param(
        {"receipt_changes": {"evidence_ref": "pr:" + "9" * 600}},
        id="over-long-evidence-ref",
    ),
]


@pytest.mark.parametrize("fixture_options", MALFORMED_RECEIPT_CASES)
def test_malformed_receipt_refuses_without_removing_entry(
    tmp_path: Path, fixture_options: dict[str, object]
) -> None:  # AC7, AC10
    """Malformed completion receipts stay dependency-scoped and use their own code."""
    result = _run_status(
        _fixture(tmp_path, keep_membership=False, outcome="completed", **fixture_options)
    )
    assert DEPENDANT in {entry["path"] for entry in result["canonical"]["blocked"]}
    codes = _codes_for(result, PRUNED_DEPENDENCY)
    assert "invalid_completion_receipt" in codes
    assert "invalid_receipt" not in codes


@pytest.mark.parametrize(
    ("target_status", "ready", "expected_codes"),
    [
        pytest.param("Shipped", True, set(), id="terminal"),
        pytest.param("Approved", False, {"unsatisfied_dependency"}, id="non-terminal"),
    ],
)
def test_present_artifact_resolves_by_its_status(
    tmp_path: Path, target_status: str, ready: bool, expected_codes: set[str]
) -> None:  # AC8
    """A present dependency uses artifact status instead of its receipt."""
    result = _run_status(
        _fixture(
            tmp_path,
            keep_membership=False,
            outcome="completed",
            target_status=target_status,
        )
    )
    assert (DEPENDANT in {entry["path"] for entry in result["canonical"]["ready"]}) is ready
    assert _codes_for(result, PRUNED_DEPENDENCY) == expected_codes


def test_present_terminal_artifact_does_not_consult_receipt(tmp_path: Path) -> None:  # AC9
    """A malformed receipt is ignored while the terminal artifact exists."""
    result = _run_status(
        _fixture(
            tmp_path,
            keep_membership=False,
            outcome="completed",
            receipt_changes={"evidence_ref": "evidence:current"},
            target_status="Shipped",
        )
    )
    assert DEPENDANT in {entry["path"] for entry in result["canonical"]["ready"]}
    assert "invalid_completion_receipt" not in _codes_for(result, PRUNED_DEPENDENCY)


def test_receiptless_local_need_remains_valid(tmp_path: Path) -> None:  # AC14
    """The second local need remains optional and resolves normally."""
    result = _run_status(_fixture(tmp_path, keep_membership=False, outcome="completed"))
    # AC14 has two halves and needs both. Without the parse assertion the code
    # assertion below is vacuously true on a vanished entry, which is exactly
    # what making the receipt mandatory produces.
    assert _parsed(result, DEPENDANT)
    assert _codes_for(result, RECEIPTLESS_DEPENDENCY) == set()
