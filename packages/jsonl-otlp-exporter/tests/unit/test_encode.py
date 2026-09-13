"""T4, encoder half — the conversion semantics ADR-0111 settles.

Covers AC-0005, AC-0023, AC-0034, AC-0053, AC-0064, AC-0065, AC-0066, AC-0068,
AC-0069, AC-0070, AC-0071, AC-0072.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from jsonl_otlp_exporter.encode import (
    MAX_NESTING_DEPTH,
    RecordSkipped,
    any_value,
    encode_records,
    to_unix_nanos,
)
from jsonl_otlp_exporter.profile import parse_profile

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _reference():
    return parse_profile(tomllib.loads((FIXTURES / "reference.toml").read_text(encoding="utf-8")))


def _records_of(body):
    return body["resourceLogs"][0]["scopeLogs"][0]["logRecords"]


def _one(record, profile=None, **kwargs):
    return _records_of(encode_records([record], profile or _reference(), "svc", **kwargs))


class TestGolden:
    """AC-0005 — the recorded fixture encodes to the committed golden, byte for byte."""

    def test_the_three_line_fixture_matches_the_golden(self):
        profile = _reference()
        lines = (FIXTURES / "three-lines.jsonl").read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        body = encode_records(records, profile, service_name="reference")
        expected = json.loads((FIXTURES / "golden.json").read_text(encoding="utf-8"))
        assert body == expected

    def test_the_golden_carries_no_field_outside_the_allowlist(self):
        """AC-0034's default-deny, asserted on the golden's actual bytes.

        The fixture's first record carries a `secret` field precisely so this can
        fail if the encoder ever forwards an undeclared field.
        """
        blob = (FIXTURES / "golden.json").read_text(encoding="utf-8")
        assert "secret" not in blob
        assert "must not appear" not in blob


class TestTimestampsRfc3339:
    """AC-0064 — an explicit offset is required, and never assumed."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("2026-09-13T05:52:24Z", 1789278744000000000),
            ("2026-09-13T05:52:24+00:00", 1789278744000000000),
            ("2026-09-13T07:52:24+02:00", 1789278744000000000),
            ("2026-09-13T05:52:24.123Z", 1789278744123000000),
            ("2026-09-13T05:52:24.123456789Z", 1789278744123456789),
        ],
    )
    def test_admitted_representations_convert_exactly(self, value, expected):
        assert to_unix_nanos(value, "rfc3339") == expected

    def test_nanosecond_precision_survives(self):
        """`datetime.microsecond` truncates at six digits; the last three would
        be dropped silently by an implementation that relied on it."""
        assert to_unix_nanos("2026-09-13T05:52:24.000000009Z", "rfc3339") % 1000 == 9

    @pytest.mark.parametrize(
        "value",
        [
            "2026-09-13T05:52:24",          # no offset at all
            "2026-09-13 05:52:24",          # no offset, space separator
            "2026-09-13",                   # date only
            "not a timestamp",
            1757742744,                     # right idea, wrong format for rfc3339
            None,
        ],
    )
    def test_an_offset_less_or_malformed_value_is_refused(self, value):
        """The offset-less case is the one that matters: assuming UTC costs up
        to fourteen hours of silent error, and the record still looks real."""
        with pytest.raises(RecordSkipped):
            to_unix_nanos(value, "rfc3339")


class TestTimestampsEpoch:
    """AC-0065 — integers only, converted in integer arithmetic."""

    @pytest.mark.parametrize(
        "value,fmt,expected",
        [
            (1757742744123, "epoch-millis", 1757742744123000000),
            ("1757742744123", "epoch-millis", 1757742744123000000),
            (1757742744, "epoch-seconds", 1757742744000000000),
            ("1757742744", "epoch-seconds", 1757742744000000000),
        ],
    )
    def test_integers_and_digit_strings_convert(self, value, fmt, expected):
        assert to_unix_nanos(value, fmt) == expected

    @pytest.mark.parametrize("value", [1757742744.5, "1757742744.5", True, "12a", ""])
    def test_a_fractional_or_non_integer_value_is_refused(self, value):
        """A float seconds value cannot represent a nanosecond instant exactly,
        and the rounding would be invisible downstream."""
        with pytest.raises(RecordSkipped):
            to_unix_nanos(value, "epoch-seconds")

    def test_conversion_is_exact_where_a_float_would_not_be(self):
        """This value is not representable exactly as a float, so a build that
        multiplies through one produces a different answer."""
        value = 1757742744123456789 // 1000000
        exact = to_unix_nanos(value, "epoch-millis")
        assert exact == value * 1_000_000
        assert exact != int(float(value) * 1_000_000)


class TestTimestampRange:
    """AC-0066 — absent, inadmissible or out-of-range skips the record."""

    def test_a_record_with_no_timestamp_field_is_skipped(self):
        skipped = []
        body = encode_records(
            [{"result": "success", "run_id": "r", "seq": 1}],
            _reference(), "svc", on_skip=lambda i, m: skipped.append((i, m)),
        )
        assert _records_of(body) == []
        assert skipped and "at" in skipped[0][1]

    def test_a_negative_instant_is_refused(self):
        with pytest.raises(RecordSkipped):
            to_unix_nanos(-1, "epoch-seconds")

    def test_a_value_at_or_above_2_63_is_refused(self):
        with pytest.raises(RecordSkipped):
            to_unix_nanos(2**63, "epoch-seconds")

    def test_a_skipped_record_does_not_stop_the_batch(self):
        good = {"at": "2026-09-13T05:52:24Z", "result": "success", "run_id": "r", "seq": 1}
        bad = dict(good, at="no offset here")
        skipped = []
        body = encode_records([good, bad, good], _reference(), "svc",
                              on_skip=lambda i, m: skipped.append(i))
        assert len(_records_of(body)) == 2
        assert skipped == [1]


class TestSeverity:
    """AC-0068, AC-0069 — mapped values route; everything else still sends."""

    def test_a_mapped_value_emits_the_number_and_the_original_string(self):
        record = {"at": "2026-09-13T05:52:24Z", "result": "failure", "run_id": "r", "seq": 1}
        entry = _one(record)[0]
        assert entry["severityNumber"] == 17
        assert entry["severityText"] == "failure"

    @pytest.mark.parametrize(
        "record_extra,label",
        [({}, "absent"), ({"result": None}, "null"), ({"result": "wave-passed"}, "unmapped")],
    )
    def test_an_unmapped_severity_still_sends_the_record(self, record_extra, label):
        """The measured reason this is not a skip: five of the first consumer's
        fifteen events carry no severity value at all, and they are the most
        frequent ones. Skipping would discard a third of the event vocabulary."""
        record = {"at": "2026-09-13T05:52:24Z", "run_id": "r", "seq": 1, **record_extra}
        seen = []
        entries = _one(record, on_unmapped_severity=seen.append)
        assert len(entries) == 1, f"{label} severity must not drop the record"
        assert "severityNumber" not in entries[0]
        assert "severityText" not in entries[0]
        assert len(seen) == 1


class TestAttributeRouting:
    """AC-0023, AC-0034, AC-0053 — one field, one place; everything else denied."""

    def test_identity_fields_are_always_emitted(self):
        record = {"at": "2026-09-13T05:52:24Z", "result": "success", "run_id": "r", "seq": 7}
        keys = {a["key"] for a in _one(record)[0]["attributes"]}
        assert {"run_id", "seq"} <= keys

    def test_a_field_outside_the_allowlist_appears_nowhere(self):
        record = {
            "at": "2026-09-13T05:52:24Z", "result": "success", "run_id": "r", "seq": 1,
            "password": "hunter2",
        }
        assert "hunter2" not in json.dumps(_one(record))

    def test_a_routed_field_is_not_duplicated_as_an_attribute(self):
        """AC-0053. The allowlist here names the timestamp, severity and identity
        fields as well, which a naive encoder would then emit twice."""
        raw = tomllib.loads((FIXTURES / "reference.toml").read_text(encoding="utf-8"))
        raw["allowlist"] = ["at", "result", "run_id", "seq", "event"]
        profile = parse_profile(raw)
        record = {
            "at": "2026-09-13T05:52:24Z", "result": "success",
            "run_id": "r", "seq": 1, "event": "spec-ready",
        }
        entry = _one(record, profile)[0]
        keys = [a["key"] for a in entry["attributes"]]
        assert keys.count("run_id") == 1 and keys.count("seq") == 1
        assert "at" not in keys, "the timestamp is routed to timeUnixNano, not an attribute"
        assert "result" not in keys, "the severity is routed to severityNumber"
        assert entry["timeUnixNano"] == "1789278744000000000"
        assert entry["severityNumber"] == 9


class TestAnyValue:
    """AC-0070, AC-0071, AC-0072 — one wrapper per JSON type, recursively, bounded."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("s", {"stringValue": "s"}),
            (True, {"boolValue": True}),
            (False, {"boolValue": False}),
            (7, {"intValue": "7"}),
            (-7, {"intValue": "-7"}),
            (1.5, {"doubleValue": 1.5}),
        ],
    )
    def test_each_scalar_takes_its_own_member(self, value, expected):
        assert any_value(value) == expected

    def test_a_boolean_is_not_an_integer(self):
        """`bool` subclasses `int`, so an isinstance order error emits 1 and 0
        and loses the type a consumer filters on."""
        assert any_value(True) == {"boolValue": True}
        assert any_value(True) != {"intValue": "1"}

    def test_a_large_integer_is_a_quoted_string(self):
        """proto3 JSON carries 64-bit integers as strings; a bare number loses
        precision in any parser backed by a 53-bit float."""
        assert any_value(2**62) == {"intValue": str(2**62)}

    def test_an_array_converts_its_members_recursively(self):
        assert any_value([1, "a", True]) == {
            "arrayValue": {"values": [{"intValue": "1"}, {"stringValue": "a"}, {"boolValue": True}]}
        }

    def test_an_object_converts_to_a_kvlist(self):
        assert any_value({"k": 1}) == {
            "kvlistValue": {"values": [{"key": "k", "value": {"intValue": "1"}}]}
        }

    def test_null_emits_nothing_at_all(self):
        """AC-0071. An absent key is queryable; an empty AnyValue is not."""
        assert any_value(None) is None

    def test_a_null_member_is_omitted_from_its_container(self):
        assert any_value({"a": 1, "b": None}) == {
            "kvlistValue": {"values": [{"key": "a", "value": {"intValue": "1"}}]}
        }

    def test_a_null_valued_field_produces_no_attribute(self):
        record = {"at": "2026-09-13T05:52:24Z", "result": "success",
                  "run_id": "r", "seq": 1, "note": None}
        keys = {a["key"] for a in _one(record)[0]["attributes"]}
        assert "note" not in keys

    def test_nesting_is_bounded(self):
        """AC-0072. Without a ceiling a hostile record walks the encoder without
        limit; the line-size bound does not help, because nesting is cheap in
        bytes."""
        deep = "leaf"
        for _ in range(MAX_NESTING_DEPTH + 3):
            deep = {"n": deep}
        wrapped = any_value(deep)
        depth = 0
        cursor = wrapped
        while isinstance(cursor, dict) and "kvlistValue" in cursor:
            values = cursor["kvlistValue"]["values"]
            if not values:
                break
            depth += 1
            cursor = values[0]["value"]
        assert depth <= MAX_NESTING_DEPTH + 1

    def test_a_value_just_inside_the_ceiling_survives(self):
        """The bound must not be so eager that an ordinary nested object is lost."""
        value = "leaf"
        for _ in range(MAX_NESTING_DEPTH - 1):
            value = {"n": value}
        assert any_value(value) is not None
