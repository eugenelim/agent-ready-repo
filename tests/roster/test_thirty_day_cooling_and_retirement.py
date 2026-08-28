"""RFC-0096 Wave 5 — cooling engine construction tests."""

import ast
import importlib.util
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parents[2]
COOLING_PATH = ROOT / "packs/core/.apm/skills/close-work/scripts/cooling.py"
SCHEMA_PATH = ROOT / "contracts/jsonschema/delivery-lifecycle-record.schema.json"
SG = "Asia/Singapore"
REQUIRED = (
    "schema", "delivery_id", "locator", "aliases", "fingerprint", "disposition",
    "post_closeout_result", "completion_event", "completion_evidence_ref",
    "completed_on", "timezone", "review_on", "authority", "confirmation_proof",
)


def _load():
    spec = importlib.util.spec_from_file_location("wave5_cooling", COOLING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _payload(**overrides) -> dict:
    payload = {
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
        "timezone": SG,
        "review_on": "2026-08-31",
        "authority": {
            "source": {"status": "repository-owned"},
            "write": {"status": "delegated"},
            "delete": {"status": "none"},
        },
        "confirmation_proof": "sha256:" + "1" * 64,
    }
    payload.update(overrides)
    return payload


def _record(cooling, **overrides):
    return cooling.CoolingRecord.from_payload(_payload(**overrides))


def _called_attributes(path: Path) -> set[tuple[str, str]]:
    """Alias-resolved (receiver, attribute) pairs for every call in a module.

    Receiver-typed calls (`p.unlink()`) are included by attribute name under the
    receiver's local name, so the matcher sees the form a real implementation
    would use. Shared by AC6 and AC36.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            value = func.value
            root = value.id if isinstance(value, ast.Name) else (
                value.attr if isinstance(value, ast.Attribute) else "<expr>"
            )
            seen.add((root, func.attr))
            seen.add(("<any>", func.attr))
        elif isinstance(func, ast.Name):
            seen.add(("<bare>", func.id))
    return seen


# STUB: AC1
@pytest.mark.parametrize(
    ("start", "zone"),
    [
        (date(2027, 2, 25), "America/New_York"),
        (date(2027, 10, 25), "America/New_York"),
        (date(2028, 2, 14), "UTC"),
        (date(2026, 8, 1), SG),
    ],
)
def test_offset_is_always_thirty_calendar_days(start: date, zone: str) -> None:
    cooling = _load()
    assert (cooling.compute_review_on(start, zone) - start).days == 30


# STUB: AC2
@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 8, 30, 23, 59, tzinfo=ZoneInfo(SG)), False),
        (datetime(2026, 8, 31, 0, 0, tzinfo=ZoneInfo(SG)), True),
        (datetime(2026, 9, 1, 0, 0, tzinfo=ZoneInfo(SG)), True),
    ],
)
@pytest.mark.parametrize("reader", ["UTC", "America/New_York", "Australia/Sydney"])
def test_dueness_flips_at_local_midnight_for_every_reader(
    moment: datetime, expected: bool, reader: str
) -> None:
    cooling = _load()
    seen = moment.astimezone(ZoneInfo(reader))
    assert cooling.is_due(_record(cooling), seen).due is expected


# STUB: AC3
def test_late_closeout_keeps_the_supplied_event_date() -> None:
    cooling = _load()
    record = _record(cooling, completed_on="2026-06-01", review_on="2026-07-01")
    result = cooling.is_due(record, datetime(2026, 7, 11, 12, 0, tzinfo=ZoneInfo(SG)))
    assert record.completed_on == date(2026, 6, 1)
    assert result.due is True


# STUB: AC4
def test_a_due_record_carries_no_permission() -> None:
    cooling = _load()
    result = cooling.is_due(_record(cooling), datetime(2026, 9, 30, tzinfo=ZoneInfo(SG)))
    assert (result.due, result.permission_granted, result.mutated) == (True, False, ())


# STUB: AC5
def test_invalid_temporal_input_returns_a_named_code() -> None:
    cooling = _load()
    assert cooling.is_due(_record(cooling), datetime(2026, 9, 30, 12, 0)).code == "naive-clock"
    assert cooling.compute_review_on(date(2026, 8, 1), "Not/AZone").code == "unknown-timezone"


# STUB: AC6
def test_cooling_module_calls_no_clock() -> None:
    called = _called_attributes(COOLING_PATH)
    for receiver, attribute in (
        ("datetime", "now"), ("datetime", "utcnow"), ("datetime", "today"),
        ("date", "today"), ("time", "time"), ("time", "monotonic"),
        ("time", "perf_counter"), ("os", "times"),
    ):
        assert (receiver, attribute) not in called
        assert ("<bare>", attribute) not in called


# STUB: AC7
def test_schema_requires_the_rfc_field_set_and_closes_every_level() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["contract_version"] == "delivery-lifecycle-record.v1"
    assert schema["x-spec"] == ["docs/specs/thirty-day-cooling-and-retirement/"]
    assert set(schema["required"]) == set(REQUIRED)

    def walk(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert node.get("required")
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(schema)


# STUB: AC8
def test_a_valid_payload_is_accepted() -> None:
    cooling = _load()
    assert cooling.validate_payload(_payload()).code is None


# STUB: AC8
@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p.update(surprise="x"),
        lambda p: p["authority"]["write"].update(surprise="x"),
        lambda p: p["exception"].update(surprise="x"),
    ],
)
def test_an_undeclared_key_refuses_at_every_level(mutate) -> None:
    cooling = _load()
    payload = _payload(
        disposition="retain-exception",
        post_closeout_result="Retained",
        exception={"reason": "audit-obligation", "owner_role": "release-manager",
                   "review_on": "2026-12-01"},
    )
    mutate(payload)
    assert cooling.validate_payload(payload).code == "record-invalid"


# STUB: AC9
@pytest.mark.parametrize("key", REQUIRED)
def test_a_missing_required_key_refuses(key: str) -> None:
    cooling = _load()
    payload = _payload()
    del payload[key]
    assert cooling.validate_payload(payload).code == "record-invalid"


# STUB: AC10
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("delivery_id", "a/b"),
        ("delivery_id", ".."),
        ("completion_evidence_ref", "author:jane-doe"),
        ("completion_evidence_ref", "owner:j.doe"),
        ("confirmation_proof", "approved by a.person@example.com"),
    ],
)
def test_a_value_outside_its_pattern_refuses(field: str, value: str) -> None:
    cooling = _load()
    assert cooling.validate_payload(_payload(**{field: value})).code == "record-invalid"


# STUB: AC11
def test_the_filename_must_equal_the_delivery_id(tmp_path) -> None:
    cooling = _load()
    path = tmp_path / "spec-a.json"
    path.write_bytes(json.dumps(_payload(delivery_id="spec-b")).encode() + b"\n")
    assert cooling.load_record(tmp_path, path).code == "record-invalid"


# STUB: AC12
def test_serialization_is_canonical_not_merely_deterministic() -> None:
    cooling = _load()
    ordered = _payload()
    shuffled = dict(reversed(list(ordered.items())))
    assert cooling.canonical_bytes(cooling.CoolingRecord.from_payload(shuffled)) == (
        cooling.canonical_bytes(cooling.CoolingRecord.from_payload(ordered))
    )
    assert cooling.canonical_bytes(_record(cooling)).endswith(b"\n")


# STUB: AC12
def test_a_non_finite_value_refuses() -> None:
    cooling = _load()
    assert cooling.parse_record_bytes(b'{"completed_on": NaN}').code == "record-invalid"


# STUB: AC13
def test_canonical_bytes_are_accepted_by_the_parser() -> None:
    cooling = _load()
    assert cooling.parse_record_bytes(cooling.canonical_bytes(_record(cooling))).code is None


# STUB: AC13
def test_oversized_and_over_nested_input_refuses_without_raising() -> None:
    cooling = _load()
    oversized = _payload(aliases=["docs/specs/x/" + "a" * 200 + ".md"] * 400)
    assert cooling.parse_record_bytes(
        json.dumps(oversized).encode() + b"\n"
    ).code == "record-invalid"

    nested: dict = {"authority": {}}
    cursor = nested["authority"]
    for _ in range(12):
        cursor["source"] = {}
        cursor = cursor["source"]
    assert cooling.parse_record_bytes(
        json.dumps(_payload(**nested)).encode() + b"\n"
    ).code == "record-invalid"
