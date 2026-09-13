"""AC-0006 — a conforming receiver records what we emit, with the right names.

This is the only check in the suite that can see whether the attribute *names*
are right. A payload with correct structure and wrong names returns HTTP 200 and
is stored: the failure mode is wrong data, not absent data, so neither the golden
(which the encoder produced) nor a response assertion can catch it.

So this test does not assert a 200. It reads back what the receiver actually
stored and checks each field reached the destination the profile declares.

Skipped unless a Collector is reachable AND its export file is readable, because
a test needing Docker must not fail a developer who does not have it running.
Both skips name what is missing rather than failing silently.
"""

from __future__ import annotations

import http.client
import json
import os
import socket
import time
import tomllib
from pathlib import Path

import pytest

from jsonl_otlp_exporter.encode import encode_records
from jsonl_otlp_exporter.profile import parse_profile
from jsonl_otlp_exporter.transport import batch_records, resolve_destination, send_batches

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
ENDPOINT = os.environ.get("JSONL_OTLP_TEST_ENDPOINT", "http://127.0.0.1:4318/v1/logs")
EXPORT = Path(
    os.environ.get(
        "JSONL_OTLP_TEST_EXPORT",
        Path(__file__).resolve().parents[4] / ".otelcol-tmp" / "export" / "logs.json",
    )
)


def _reachable(url: str) -> bool:
    host = url.split("//", 1)[1].split("/", 1)[0]
    hostname, _, port = host.partition(":")
    try:
        with socket.create_connection((hostname, int(port or 4318)), timeout=2):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _reachable(ENDPOINT),
    reason=f"no OTLP receiver reachable at {ENDPOINT}; start one to run the round trip",
)


def _connection_factory(scheme, connect_host, port, timeout, context):
    if scheme == "https":  # pragma: no cover - the local fixture is plaintext
        return http.client.HTTPSConnection(connect_host, port, timeout=timeout, context=context)
    return http.client.HTTPConnection(connect_host, port, timeout=timeout)


def _require_export_configured() -> None:
    """Answer the ENVIRONMENT question before sending, never after.

    Asked afterwards, "the file exporter is not configured" and "the run sent
    nothing" look identical -- so a build whose batching yields no batch returns
    status 0 and the only check that observes attribute naming downgrades itself
    to a skip. The environment is knowable up front; the outcome is not.
    """
    if not EXPORT.parent.exists():
        pytest.skip(f"no export directory at {EXPORT.parent}; configure the file exporter")


def _stored_records(before_bytes: int, run_id: str) -> list[dict]:
    """Read back only what this test wrote, by offset and by run_id."""
    for _ in range(40):  # the exporter flushes asynchronously
        if EXPORT.exists() and EXPORT.stat().st_size > before_bytes:
            break
        time.sleep(0.25)
    else:
        raise AssertionError(
            f"the send reported success but nothing was stored at {EXPORT}. "
            "The receiver accepted a request that carried no record, or the "
            "exporter produced no request at all."
        )

    with EXPORT.open("rb") as handle:
        handle.seek(before_bytes)
        tail = handle.read().decode("utf-8")

    records: list[dict] = []
    for line in tail.splitlines():
        if not line.strip():
            continue
        for resource in json.loads(line).get("resourceLogs", []):
            for scope in resource.get("scopeLogs", []):
                records.extend(scope.get("logRecords", []))
    return [
        record
        for record in records
        if any(
            attribute["key"] == "run_id" and attribute["value"].get("stringValue") == run_id
            for attribute in record.get("attributes", [])
        )
    ]


def test_each_field_reaches_the_destination_its_profile_declares():
    profile = parse_profile(
        tomllib.loads((FIXTURES / "reference.toml").read_text(encoding="utf-8"))
    )
    lines = (FIXTURES / "three-lines.jsonl").read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    run_id = records[0]["run_id"]

    def encode(batch):
        return json.dumps(encode_records(batch, profile, service_name="reference")).encode("utf-8")

    _require_export_configured()
    before = EXPORT.stat().st_size if EXPORT.exists() else 0
    destination = resolve_destination(ENDPOINT)
    outcome = send_batches(batch_records(records, encode), destination, _connection_factory)
    assert outcome.status == 0, f"receiver refused the payload: {outcome.reason}"
    assert outcome.rejected_records == 0

    stored = _stored_records(before, run_id)
    assert len(stored) == 3, f"expected three records back, got {len(stored)}"

    # The timestamp field reached timeUnixNano, to the nanosecond. The second
    # fixture line carries nine fractional digits precisely so a build that
    # rounds through microseconds fails here rather than in review.
    assert [record["timeUnixNano"] for record in stored] == [
        "1789278744000000000",
        "1789278790123456789",
        "1789271640000000000",
    ]

    # The severity field reached severityNumber -- and the third record, whose
    # value the profile does not map, is STILL HERE with no severity at all.
    assert stored[0]["severityNumber"] == 9 and stored[0]["severityText"] == "success"
    assert stored[1]["severityNumber"] == 17 and stored[1]["severityText"] == "failure"
    assert "severityNumber" not in stored[2] and "severityText" not in stored[2]

    # Each allowlisted field is a log-record attribute, under its own name.
    first = {a["key"]: a["value"] for a in stored[0]["attributes"]}
    assert first["event"] == {"stringValue": "spec-ready"}
    assert first["phase_s"] == {"doubleValue": 12.5}
    assert first["seq"] == {"intValue": "1"}
    assert "kvlistValue" in first["budgets"], "a nested object must survive as a kvlist"
    assert {"key": "review", "value": {"intValue": "3"}} in first["budgets"]["kvlistValue"]["values"]

    # A null-valued field produced no attribute; the same field with a value did.
    assert "note" not in first
    assert {a["key"] for a in stored[1]["attributes"]} >= {"note"}

    # Default-deny, proven against what the receiver stored rather than against
    # what we intended to send.
    blob = json.dumps(stored)
    assert "secret" not in blob and "must not appear" not in blob
