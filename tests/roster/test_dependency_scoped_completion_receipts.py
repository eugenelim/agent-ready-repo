"""Contract tests for dependency-scoped completion receipts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
LIFECYCLE_SCHEMA = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
WORKSPACE_ENTRY_SCHEMA = ROOT / "contracts/jsonschema/workspace-entry.schema.json"


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
