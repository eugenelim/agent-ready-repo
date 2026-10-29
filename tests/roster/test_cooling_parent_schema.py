"""The lifecycle record schema and `validate_payload` agree on `parent`."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[2]
_SCHEMA = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
_COOLING = ROOT / "packs/core/.apm/skills/close-work/scripts/cooling.py"
_NAME = "roster_cooling_parent_schema_cooling"
_SPEC = importlib.util.spec_from_file_location(_NAME, _COOLING)
assert _SPEC is not None and _SPEC.loader is not None
COOLING = importlib.util.module_from_spec(_SPEC)
sys.modules[_NAME] = COOLING
_SPEC.loader.exec_module(COOLING)
VALIDATOR = jsonschema.Draft202012Validator(json.loads(_SCHEMA.read_text(encoding="utf-8")))

_BASE: dict[str, object] = {
    "schema": "delivery-lifecycle-record.v1",
    "delivery_id": "spec-example",
    "locator": "docs/specs/example/spec.md",
    "aliases": [],
    "fingerprint": "sha256:" + "0" * 64,
    "disposition": "cool-30-days",
    "post_closeout_result": "Cooling",
    "completion_event": "merge",
    "completion_evidence_ref": "commit:" + "a" * 40,
    "completed_on": "2026-08-01",
    "timezone": "Asia/Singapore",
    "review_on": "2026-08-31",
    "authority": {
        "source": {"status": "repository-owned"},
        "write": {"status": "delegated"},
        "delete": {"status": "none"},
    },
    "confirmation_proof": "sha256:" + "1" * 64,
}
_ABSENT = object()
_VALUES: list[tuple[object, bool]] = [
    (_ABSENT, True),
    ("none", True),
    ("docs/product/briefs/example-brief.md", True),
    ("docs/product/briefs/a.md", True),
    ("docs/product/briefs/" + "a" * 128 + ".md", True),
    ("brief:example-brief", False),
    ("docs/product/briefs/sub/x.md", False),
    ("docs/product/briefs/../x.md", False),
    ("docs/product/briefs/Example.md", False),
    ("docs/product/briefs/" + "a" * 129 + ".md", False),
    ("docs/product/briefs/example.md\n", False),
    ("", False),
    ("None", False),
    ("x" * 5000, False),
    (None, False),
    (7, False),
    (["none"], False),
    (True, False),
]


@pytest.mark.parametrize(("value", "valid"), _VALUES, ids=lambda v: repr(v)[:40])
def test_schema_and_validator_agree_on_parent(value: object, valid: bool) -> None:
    payload = dict(_BASE)
    if value is not _ABSENT:
        payload["parent"] = value
    assert VALIDATOR.is_valid(payload) is valid
    assert (COOLING.validate_payload(payload).code is None) is valid


def test_parent_is_the_only_property_added() -> None:
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    assert "parent" not in schema["required"]
    assert schema["additionalProperties"] is False
    assert schema["contract_version"] == "delivery-lifecycle-record.v1"
