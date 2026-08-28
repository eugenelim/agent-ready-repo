"""Pure record, calendar, and validation helpers for thirty-day cooling."""

import errno
import importlib.util
import json
import os
import re
import stat
import sys
from contextlib import suppress
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
_TRANSITIONS = frozenset(
    {
        (("cool-30-days", "Cooling"), ("cool-30-days", "Retired")),
        (("cool-30-days", "Cooling"), ("retain-exception", "Retained")),
        (("retain-exception", "Retained"), ("retain-exception", "Retained")),
        (("retain-exception", "Retained"), ("cool-30-days", "Cooling")),
        (("retain-exception", "Retained"), ("retain-exception", "Retired")),
        (("retain-exception", "Retained"), ("retain-exception", "ExternalAdvisory")),
    }
)
_REVIEW_FIELDS = frozenset(
    {"completion", "outputs", "active_use", "obligations", "identity", "authority"}
)
_REVIEW_ANSWERS = frozenset({"approve", "refuse", "uncertain"})
_CLOSE_WORK: object | None = None


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

    def as_dict(self) -> dict[str, object]:
        """Return a diagnostic-free public result payload."""
        payload: dict[str, object] = {
            "due": self.due,
            "permission_granted": self.permission_granted,
            "mutated": self.mutated,
        }
        if self.code is not None:
            payload["code"] = self.code
        if self.record is not None:
            payload["record"] = self.record.as_payload()
        return payload


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
    payload = record.as_payload() if hasattr(record, "as_payload") else record
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


def verify_identity(root: Path, record: CoolingRecord) -> CoolingResult:
    """Reconfirm a record's content identity at its current locator or an alias."""
    file_safety = _close_work().file_safety()
    for locator in (record.locator, *record.aliases):
        try:
            path = Path(root) / locator
            file_safety.read_confined_regular_file(
                Path(root), path, max_bytes=MAX_ARTIFACT_BYTES
            )
            fingerprint = "sha256:" + file_safety.sha256_confined_regular_file(
                Path(root), path
            )
        except (OSError, ValueError):
            continue
        if fingerprint != record.fingerprint:
            return CoolingResult(code="fingerprint-drift", record=record)
        return CoolingResult(code="identity-verified", record=record)
    return CoolingResult(code="locator-unresolved", record=record)


def record_rename(record: CoolingRecord, new_locator: str) -> CoolingRecord:
    """Return a renamed record while retaining its immediately prior locator."""
    payload = record.as_payload()
    payload["locator"] = new_locator
    payload["aliases"] = [*record.aliases, record.locator][-16:]
    return CoolingRecord.from_payload(payload)


def deletion_allowed(
    *,
    root: Path,
    record: CoolingRecord,
    completion_evidence_resolver: object,
    live_grant: object,
    authority_evidence_ref: object,
) -> CoolingResult:
    """Permit deletion only when each independently resolved proof is current."""
    if not callable(completion_evidence_resolver):
        return CoolingResult(code="missing-history", record=record)
    try:
        completion_resolved = completion_evidence_resolver(record.completion_evidence_ref)
    except Exception:
        completion_resolved = False
    if not completion_resolved:
        return CoolingResult(code="missing-history", record=record)

    identity = verify_identity(root, record)
    if identity.code != "identity-verified":
        return identity

    delete_authority = dict(dict(record.authority).get("delete", ()))
    if (
        delete_authority.get("status") != "delegated"
        or not isinstance(delete_authority.get("evidence_ref"), str)
    ):
        return CoolingResult(code="authority-uncertain", record=record)
    try:
        authority_fact = _close_work().resolve_mutation_authority(
            grant_record=live_grant, authority_evidence_ref=authority_evidence_ref
        )
    except (ImportError, ValueError):
        authority_fact = None
    if (
        authority_fact is None
        or authority_fact.action != "delete-confirmed-file-set"
        or authority_fact.resource != record.locator
        or authority_fact.evidence_ref != delete_authority["evidence_ref"]
    ):
        return CoolingResult(code="authority-uncertain", record=record)
    return CoolingResult(
        code="deletion-permitted", record=record, permission_granted=True
    )


def _close_work() -> object:
    """Load the co-located close-work authority seam without package imports."""
    global _CLOSE_WORK
    if _CLOSE_WORK is None:
        path = Path(__file__).with_name("close_work.py")
        existing = sys.modules.get("cooling_close_work")
        if existing is not None and getattr(existing, "__file__", None) == str(path):
            _CLOSE_WORK = existing
            return _CLOSE_WORK
        spec = importlib.util.spec_from_file_location("cooling_close_work", path)
        if spec is None or spec.loader is None:
            raise ImportError("close-work authority seam is unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(spec.name, None)
            raise
        _CLOSE_WORK = module
    return _CLOSE_WORK


def _record_path(root: Path, destination: Path, record: CoolingRecord) -> Path:
    """Return the sole permitted lifecycle path for a validated record."""
    return destination / f"{record.delivery_id}.json"


def _write_effect_supported() -> bool:
    """Require the no-follow descriptor operations used by the writer."""
    return (
        {os.open, os.stat, os.rename} <= os.supports_dir_fd
        and bool(getattr(os, "O_NOFOLLOW", 0))
        and bool(getattr(os, "O_DIRECTORY", 0))
    )


def _write_refusal(error: OSError) -> str:
    """Map filesystem failures to the closed, non-diagnostic result set."""
    if error.errno in {errno.ELOOP, errno.ENOTDIR}:
        return "unsafe-target"
    return "lifecycle-state-unwritable"


def _binding_is_issued(binding: object, resource: str) -> bool:
    """Require a registered authority fact to reproduce this exact binding."""
    close_work = _close_work()
    binding_type = close_work.MutationBinding
    if not isinstance(binding, binding_type) or binding.resource != resource:
        return False
    authorities = close_work._ISSUED_COORDINATION_AUTHORITIES
    for fact in authorities.values():
        expected = close_work._mutation_binding(
            authority_fact=fact,
            authorized_actor_role=binding.authorized_actor_role,
            grant_source=binding.grant_source,
            action=binding.action,
            resource=binding.resource,
            evidence_ref=binding.evidence_ref,
            host_session_provenance=binding.host_session_provenance,
            expected_action="write-lifecycle-record",
        )
        if expected == binding:
            return True
    return False


def _write_record(
    root: Path, destination: Path, record: CoolingRecord, binding: object
) -> CoolingResult:
    """Atomically replace one confined lifecycle record through a directory fd."""
    if not _write_effect_supported():
        return CoolingResult(code="lifecycle-state-unwritable")
    try:
        final_path = _record_path(root, destination, record)
        resource = final_path.relative_to(root).as_posix()
    except ValueError:
        return CoolingResult(code="unsafe-target")
    if not _binding_is_issued(binding, resource):
        return CoolingResult(code="authority-uncertain")
    descriptor: int | None = None
    temporary: str | None = None
    try:
        descriptor = _close_work().open_validated_parent(root, destination)
        final_name = final_path.name
        try:
            target = os.stat(final_name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            target = None
        if target is not None and not stat.S_ISREG(target.st_mode):
            return CoolingResult(code="unsafe-target")
        for index in range(32):
            candidate = f".{record.delivery_id}.tmp-{index}"
            try:
                temporary_fd = os.open(
                    candidate,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=descriptor,
                )
            except FileExistsError:
                continue
            temporary = candidate
            try:
                with os.fdopen(temporary_fd, "wb") as handle:
                    handle.write(canonical_bytes(record))
                os.replace(temporary, final_name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
                temporary = None
                return CoolingResult(code="enrolled", record=record, mutated=(final_path,))
            except OSError as error:
                return CoolingResult(code=_write_refusal(error))
        return CoolingResult(code="lifecycle-state-unwritable")
    except ValueError:
        return CoolingResult(code="unsafe-target")
    except OSError as error:
        return CoolingResult(code=_write_refusal(error))
    finally:
        if temporary is not None and descriptor is not None:
            with suppress(OSError):
                os.unlink(temporary, dir_fd=descriptor)
        if descriptor is not None:
            os.close(descriptor)


def _resolve_destination(root: Path, candidates: object) -> Path | str:
    """Resolve a confirmed runtime-coordination destination, or name the refusal.

    Returns the destination path, or the refusal code to report. An absent or
    unconfirmed candidate is a different failure from a candidate the resolver
    rejects for an unsafe path, and collapsing both into one sentinel reported a
    human-confirmation failure for an escaping symlink.
    """
    if not isinstance(candidates, (list, tuple)) or not candidates:
        return "destination-unconfirmed"
    if not all(
        any(
            item.kind == "destination-selection" and item.status == "confirmed"
            for item in candidate.confirmations
        )
        for candidate in candidates
    ):
        return "destination-unconfirmed"
    close_work = _close_work()
    result = close_work.surface_resolver().resolve_surface(
        root, "runtime-coordination", candidates
    )
    if result.status != "resolved" or result.physical_locator is None:
        # The resolver realpath-resolves and refuses a locator that leaves the
        # root, so its refusal here is a path-safety fact, not a missing
        # confirmation.
        return "unsafe-target" if result.code == "unsafe_repository_path" else (
            "destination-unconfirmed"
        )
    if result.physical_locator.kind != "repository-path":
        return "unsafe-target"
    # The physical locator is the one the resolver path-validates: it rejects a
    # leading separator, a drive letter, a backslash, and any empty, "." or ".."
    # segment. The logical locator is an identity string checked only as bounded
    # safe text, so joining it would let a candidate name a destination outside
    # the root and rely on the descriptor walk to catch it afterwards.
    try:
        return root / result.physical_locator.value
    except TypeError:
        return "unsafe-target"


def enrol(
    *,
    root: Path,
    record: CoolingRecord,
    delivered: bool,
    closed: bool,
    persisted: bool,
    completion_event: object,
    candidates: object,
    authority_binding: object,
) -> CoolingResult:
    """Persist one eligible delivery record through the guarded writer."""
    if not delivered:
        return CoolingResult(code="not-delivered")
    if not closed:
        return CoolingResult(code="not-closed")
    if not persisted:
        return CoolingResult(code="no-persistent-record")
    if completion_event not in {"merge", "release", "acceptance"}:
        return CoolingResult(code="completion-event-required")
    destination = _resolve_destination(root, candidates)
    if isinstance(destination, str):
        return CoolingResult(code=destination)
    try:
        return _write_record(root, destination, record, authority_binding)
    except (ImportError, OSError, ValueError):
        return CoolingResult(code="lifecycle-state-unwritable")


def load_record(root: Path, path: Path) -> CoolingResult:
    """Load a record and ensure its filename carries its unmodified delivery ID."""
    try:
        root = Path(root)
        path = Path(path)
        raw = _close_work().file_safety().read_confined_regular_file(
            root, path, max_bytes=MAX_RECORD_BYTES
        )
        result = parse_record_bytes(raw)
    except (ImportError, OSError, ValueError):
        return CoolingResult(code="record-invalid")
    if (
        result.code is not None
        or result.record is None
        or path.stem != result.record.delivery_id
        or compute_review_on(result.record.completed_on, result.record.timezone)
        != result.record.review_on
    ):
        return CoolingResult(code="record-invalid")
    return result


def update_record(
    *,
    root: Path,
    prior: CoolingRecord,
    proposed: CoolingRecord,
    candidates: object,
    authority_binding: object,
) -> CoolingResult:
    """Persist an allowed lifecycle transition using the same guarded writer."""
    transition = (
        (prior.disposition, prior.post_closeout_result),
        (proposed.disposition, proposed.post_closeout_result),
    )
    if transition not in _TRANSITIONS or prior.delivery_id != proposed.delivery_id:
        return CoolingResult(code="record-invalid")
    destination = _resolve_destination(root, candidates)
    if isinstance(destination, str):
        return CoolingResult(code=destination)
    result = _write_record(root, destination, proposed, authority_binding)
    if result.code == "enrolled":
        return CoolingResult(code="accepted", record=proposed, mutated=result.mutated)
    return result


def _review_is_complete(checks: object, attestation: object) -> bool:
    """Require a second party's exact, complete day-30 review response."""
    if not isinstance(checks, dict) or set(checks) != _REVIEW_FIELDS:
        return False
    if any(answer not in _REVIEW_ANSWERS for answer in checks.values()):
        return False
    if not isinstance(attestation, dict):
        return False
    answers = attestation.get("answers")
    proposer = attestation.get("proposer_role")
    approver = attestation.get("approver_role")
    evidence_ref = attestation.get("human_evidence_ref")
    return (
        isinstance(answers, dict)
        and answers == checks
        and isinstance(proposer, str)
        and _ROLE_RE.fullmatch(proposer) is not None
        and isinstance(approver, str)
        and _ROLE_RE.fullmatch(approver) is not None
        and approver != proposer
        and isinstance(evidence_ref, str)
        and _EVIDENCE_RE.fullmatch(evidence_ref) is not None
    )


def _proposed_record(
    record: CoolingRecord,
    *,
    disposition: str,
    post_closeout_result: str,
    exception: dict[str, str] | None,
) -> CoolingRecord:
    """Return a validated transition target with its required exception shape."""
    payload = record.as_payload()
    payload["disposition"] = disposition
    payload["post_closeout_result"] = post_closeout_result
    if exception is None:
        payload.pop("exception", None)
    else:
        payload["exception"] = exception
    return CoolingRecord.from_payload(payload)


def review(
    record: CoolingRecord,
    checks: object,
    attestation: object,
    now: datetime,
    exception: object = None,
    *,
    root: Path,
    candidates: object,
    authority_binding: object,
) -> CoolingResult:
    """Persist a due day-30 retirement or retained-exception decision."""
    if not _review_is_complete(checks, attestation):
        return CoolingResult(code="review-incomplete")
    due = is_due(record, now)
    if due.code is not None:
        return due
    if not due.due:
        return CoolingResult(code="not-due", record=record)
    assert isinstance(checks, dict)
    if any(answer in {"refuse", "uncertain"} for answer in checks.values()):
        if not _exception_is_valid(exception):
            return CoolingResult(code="exception-envelope-invalid")
        proposed = _proposed_record(
            record,
            disposition="retain-exception",
            post_closeout_result="Retained",
            exception=exception,
        )
    else:
        proposed = _proposed_record(
            record,
            disposition="cool-30-days",
            post_closeout_result="Retired",
            exception=None,
        )
    return update_record(
        root=root,
        prior=record,
        proposed=proposed,
        candidates=candidates,
        authority_binding=authority_binding,
    )


def review_exception(
    record: CoolingRecord,
    outcome: object,
    attestation: object,
    now: datetime,
    *,
    root: Path,
    candidates: object,
    authority_binding: object,
) -> CoolingResult:
    """Persist one closed exception-review outcome without deleting anything."""
    targets = {
        "confirm-deletion": ("retain-exception", "Retired"),
        "renew": ("retain-exception", "Retained"),
        "choose-cooling": ("cool-30-days", "Cooling"),
        "advisory": ("retain-exception", "ExternalAdvisory"),
    }
    if not isinstance(outcome, str) or outcome not in targets:
        return CoolingResult(code="exception-envelope-invalid")
    due = is_due(record, now)
    if due.code is not None:
        return due
    if not due.due:
        return CoolingResult(code="not-due", record=record)
    disposition, post_closeout_result = targets[outcome]
    exception: dict[str, str] | None
    if disposition == "cool-30-days":
        exception = None
    elif outcome == "renew":
        if not isinstance(attestation, dict):
            return CoolingResult(code="exception-envelope-invalid")
        supplied = attestation.get("exception", attestation)
        if not _exception_is_valid(supplied):
            return CoolingResult(code="exception-envelope-invalid")
        exception = supplied
    else:
        exception = dict(record.exception or ())
    try:
        proposed = _proposed_record(
            record,
            disposition=disposition,
            post_closeout_result=post_closeout_result,
            exception=exception,
        )
    except (TypeError, ValueError):
        return CoolingResult(code="exception-envelope-invalid")
    return update_record(
        root=root,
        prior=record,
        proposed=proposed,
        candidates=candidates,
        authority_binding=authority_binding,
    )
