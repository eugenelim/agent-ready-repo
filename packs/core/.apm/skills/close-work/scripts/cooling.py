"""Pure record, calendar, and validation helpers for thirty-day cooling."""

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_RECORD_BYTES = 64 * 1024
MAX_RECORD_DEPTH = 8
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
REFUSAL_CODES = frozenset(
    {
        "not-delivered", "not-closed", "no-persistent-record",
        "completion-event-required", "destination-unconfirmed",
        "lifecycle-state-unwritable", "unsafe-target", "authority-uncertain",
        "record-invalid", "naive-clock", "unknown-timezone", "not-due",
        "review-incomplete", "fingerprint-drift", "locator-unresolved",
        "missing-history", "exception-envelope-invalid",
    }
)

_DELIVERY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_EVIDENCE_RE = re.compile(r"^(?:commit:[0-9a-f]{40}|pr:[0-9]+|run:[0-9]+)$")
_ROLE_RE = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_STATUS_RE = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
_REQUIRED = frozenset(
    {
        "schema", "delivery_id", "locator", "aliases", "fingerprint",
        "disposition", "post_closeout_result", "completion_event",
        "completion_evidence_ref", "completed_on", "timezone", "review_on",
        "authority", "confirmation_proof",
    }
)


@dataclass(frozen=True)
class CoolingRecord:
    """One validated delivery lifecycle record."""

    schema: str
    delivery_id: str
    locator: str
    aliases: tuple[str, ...]
    fingerprint: str
    disposition: str
    post_closeout_result: str
    completion_event: str
    completion_evidence_ref: str
    completed_on: date
    timezone: str
    review_on: date
    authority: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]
    confirmation_proof: str
    exception: tuple[tuple[str, str], ...] | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "CoolingRecord":
        """Construct an immutable record from a previously validated payload."""
        authority = payload["authority"]
        exception = payload.get("exception")
        if not isinstance(authority, dict):
            raise ValueError("authority must be an object")
        if exception is not None and not isinstance(exception, dict):
            raise ValueError("exception must be an object")
        return cls(
            schema=str(payload["schema"]),
            delivery_id=str(payload["delivery_id"]),
            locator=str(payload["locator"]),
            aliases=tuple(payload["aliases"]),  # type: ignore[arg-type]
            fingerprint=str(payload["fingerprint"]),
            disposition=str(payload["disposition"]),
            post_closeout_result=str(payload["post_closeout_result"]),
            completion_event=str(payload["completion_event"]),
            completion_evidence_ref=str(payload["completion_evidence_ref"]),
            completed_on=date.fromisoformat(str(payload["completed_on"])),
            timezone=str(payload["timezone"]),
            review_on=date.fromisoformat(str(payload["review_on"])),
            authority=tuple(
                (name, tuple((key, str(value)) for key, value in fact.items()))
                for name, fact in authority.items()
                if isinstance(fact, dict)
            ),
            confirmation_proof=str(payload["confirmation_proof"]),
            exception=(
                tuple((key, str(value)) for key, value in exception.items())
                if exception is not None else None
            ),
        )

    def as_payload(self) -> dict[str, object]:
        """Return the portable JSON payload represented by this record."""
        payload: dict[str, object] = {
            "schema": self.schema,
            "delivery_id": self.delivery_id,
            "locator": self.locator,
            "aliases": list(self.aliases),
            "fingerprint": self.fingerprint,
            "disposition": self.disposition,
            "post_closeout_result": self.post_closeout_result,
            "completion_event": self.completion_event,
            "completion_evidence_ref": self.completion_evidence_ref,
            "completed_on": self.completed_on.isoformat(),
            "timezone": self.timezone,
            "review_on": self.review_on.isoformat(),
            "authority": {name: dict(fact) for name, fact in self.authority},
            "confirmation_proof": self.confirmation_proof,
        }
        if self.exception is not None:
            payload["exception"] = dict(self.exception)
        return payload


@dataclass(frozen=True)
class CoolingResult:
    """Mutation-free result with a stable refusal code when applicable."""

    code: str | None = None
    record: CoolingRecord | None = None
    due: bool = False
    permission_granted: bool = False
    mutated: tuple[object, ...] = ()


def _is_locator(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 1000:
        return False
    if value.startswith("/") or "\\" in value or "//" in value:
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def _is_date(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _depth(value: object, level: int = 1) -> int:
    if isinstance(value, dict):
        return max([level] + [_depth(item, level + 1) for item in value.values()])
    if isinstance(value, list):
        return max([level] + [_depth(item, level + 1) for item in value])
    return level


def _authority_is_valid(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {"source", "write", "delete"}:
        return False
    for fact in value.values():
        if not isinstance(fact, dict) or set(fact) - {"status", "evidence_ref"}:
            return False
        if "status" not in fact or not _STATUS_RE.fullmatch(str(fact["status"])):
            return False
        if "evidence_ref" in fact and not _EVIDENCE_RE.fullmatch(str(fact["evidence_ref"])):
            return False
    return True


def _exception_is_valid(value: object) -> bool:
    permitted = {"reason", "owner_role", "review_on", "evidence_ref"}
    if not isinstance(value, dict) or set(value) - permitted:
        return False
    if set(value) < {"reason", "owner_role", "review_on"}:
        return False
    reasons = {
        "audit-obligation", "dependency-obligation", "legal-obligation",
        "operational-obligation", "retention-obligation",
    }
    return (
        value["reason"] in reasons
        and _ROLE_RE.fullmatch(str(value["owner_role"])) is not None
        and _is_date(value["review_on"])
        and (
            "evidence_ref" not in value
            or _EVIDENCE_RE.fullmatch(str(value["evidence_ref"])) is not None
        )
    )


def validate_payload(payload: object) -> CoolingResult:
    """Validate the closed lifecycle shape without raising on untrusted input."""
    if (
        not isinstance(payload, dict)
        or set(payload) - (_REQUIRED | {"exception"})
        or not set(payload) >= _REQUIRED
    ):
        return CoolingResult(code="record-invalid")
    if payload["schema"] != "delivery-lifecycle-record.v1":
        return CoolingResult(code="record-invalid")
    if (
        not _DELIVERY_ID_RE.fullmatch(str(payload["delivery_id"]))
        or not _is_locator(payload["locator"])
    ):
        return CoolingResult(code="record-invalid")
    aliases = payload["aliases"]
    if (
        not isinstance(aliases, list)
        or len(aliases) > 16
        or not all(_is_locator(alias) for alias in aliases)
    ):
        return CoolingResult(code="record-invalid")
    if (
        not _DIGEST_RE.fullmatch(str(payload["fingerprint"]))
        or not _DIGEST_RE.fullmatch(str(payload["confirmation_proof"]))
    ):
        return CoolingResult(code="record-invalid")
    if (
        payload["disposition"] not in {"cool-30-days", "retain-exception"}
        or payload["post_closeout_result"]
        not in {"Cooling", "Retained", "Retired", "ExternalAdvisory"}
    ):
        return CoolingResult(code="record-invalid")
    if (
        payload["completion_event"] not in {"merge", "release", "acceptance"}
        or not _EVIDENCE_RE.fullmatch(str(payload["completion_evidence_ref"]))
    ):
        return CoolingResult(code="record-invalid")
    if (
        not _is_date(payload["completed_on"])
        or not _is_date(payload["review_on"])
        or not _authority_is_valid(payload["authority"])
    ):
        return CoolingResult(code="record-invalid")
    try:
        ZoneInfo(str(payload["timezone"]))
    except (ZoneInfoNotFoundError, ValueError):
        return CoolingResult(code="record-invalid")
    has_exception = "exception" in payload
    if (payload["disposition"] == "retain-exception") != has_exception:
        return CoolingResult(code="record-invalid")
    if has_exception and not _exception_is_valid(payload["exception"]):
        return CoolingResult(code="record-invalid")
    try:
        record = CoolingRecord.from_payload(payload)
    except (KeyError, TypeError, ValueError):
        return CoolingResult(code="record-invalid")
    return CoolingResult(record=record)


def parse_record_bytes(raw: bytes) -> CoolingResult:
    """Parse bounded JSON and reject malformed, non-finite, or deep records."""
    if not isinstance(raw, bytes) or len(raw) > MAX_RECORD_BYTES:
        return CoolingResult(code="record-invalid")
    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError, RecursionError):
        return CoolingResult(code="record-invalid")
    if _depth(payload) > MAX_RECORD_DEPTH:
        return CoolingResult(code="record-invalid")
    return validate_payload(payload)


def canonical_bytes(record: CoolingRecord | dict[str, object]) -> bytes:
    """Serialize a record in the published stable JSON representation."""
    payload = record.as_payload() if isinstance(record, CoolingRecord) else record
    rendered = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return rendered.encode("ascii") + b"\n"


def compute_review_on(completed_on: date, timezone: str) -> date | CoolingResult:
    """Return the calendar date thirty days after a completion date."""
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return CoolingResult(code="unknown-timezone")
    return completed_on + timedelta(days=30)


def is_due(record: CoolingRecord, moment: datetime) -> CoolingResult:
    """Compare an injected aware instant with the record's local review date."""
    if moment.tzinfo is None or moment.utcoffset() is None:
        return CoolingResult(code="naive-clock")
    try:
        zone = ZoneInfo(record.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        return CoolingResult(code="unknown-timezone")
    return CoolingResult(record=record, due=moment.astimezone(zone).date() >= record.review_on)


def load_record(root: Path, path: Path) -> CoolingResult:
    """Load a record and ensure its filename carries its unmodified delivery ID."""
    del root
    try:
        result = parse_record_bytes(path.read_bytes())
    except OSError:
        return CoolingResult(code="record-invalid")
    if result.code is not None or result.record is None or path.stem != result.record.delivery_id:
        return CoolingResult(code="record-invalid")
    return result
