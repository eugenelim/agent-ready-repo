"""_delivery_feed — read-only, reproducible snapshot feed over evidence logs.

``feed_page`` scans ``docs/specs/<feature>/.shadow-acceptance/shadow-evidence.log``
under a repository root and returns one ``delivery-fact-feed.v1`` page of
committed delivery facts, each with its ``knowledge-observation.v1`` projection
or an explicit ``none`` with a closed reason.

Read only.  The feed never writes, locks for writing, truncates, repairs, or
appends to a log, and it never calls ``EvidenceStore.open()`` (which truncates a
torn final frame).  Every log read goes through ``file_safety.py``'s confined,
no-follow, single-link, regular-file, bounded helpers rooted at the repository,
and only when the log's directory holds the writer's exact self-ignoring
``.gitignore`` marker.  Admission matches the store's replay
(``_evidence_store.replay_admitted_frames``) except that a torn final frame stays
invisible and unrepaired.

Snapshot: the first page fixes the source set, that is the ``docs/specs/``
listing plus each log's state, byte length, and sha256.  A continuation
re-enumerates and refuses, with no partial page, on any difference.  Nothing is
cached: the token is the whole cursor.

With ``WORK_LOOP_SHADOW_SERVICES`` unset the feed returns a complete, empty
snapshot without touching the filesystem.

Self-contained: standard library plus sibling work-loop modules loaded by path.
It never opens, copies, or loads a delivery schema.

Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import stat
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any, Final, NamedTuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "MAX_ENTRIES",
    "MAX_PAGE_BYTES",
    "SCAN_REFUSAL_CODES",
    "SHADOW_ENV_VAR",
    "UNREAD_REASONS",
    "ScanRefused",
    "feed_page",
    "render_page",
]

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent

SHADOW_ENV_VAR: Final[str] = "WORK_LOOP_SHADOW_SERVICES"
_SHADOW_SUBDIR: Final[str] = ".shadow-acceptance"
_EVIDENCE_LOG: Final[str] = "shadow-evidence.log"
_MARKER_NAME: Final[str] = ".gitignore"
# The exact bytes _compat_facade writes to make the directory self-ignoring.
_MARKER_BYTES: Final[bytes] = b"*\n"

# Page bounds, stated once in delivery-fact-feed.v1 and pinned to it by a test.
MAX_ENTRIES: Final[int] = 1000
MAX_PAGE_BYTES: Final[int] = 1024 * 1024
_MAX_RECORD_SCHEMA_VERSION: Final[int] = 1000

UNREAD_REASONS: Final[frozenset[str]] = frozenset({
    "shadow-dir-unsafe",
    "marker-missing",
    "marker-invalid",
    "marker-unsafe",
    "log-unsafe",
    "log-oversized",
    "log-corrupt",
    "log-identity-invalid",
})
SCAN_REFUSAL_CODES: Final[frozenset[str]] = frozenset({
    "root-invalid",
    "specs-root-refused",
    "specs-entry-refused",
    "specs-entry-name-invalid",
    "token-invalid",
    "snapshot-changed",
    "scan-failed",
})

_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"dff1\.([0-9a-f]{64})\.([0-9]{1,9})")
_SPEC_NAME_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9_.][A-Za-z0-9_.-]{0,79}")


class ScanRefused(Exception):
    """The whole scan is refused with a closed reason code and no partial result."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


# ── Sibling loaders (by path, unregistered) ────────────────────────────────────

_modules: dict[str, ModuleType] = {}


def _sibling(alias: str, filename: str) -> ModuleType:
    """Load a sibling work-loop module by path once, without registering it."""
    cached = _modules.get(alias)
    if cached is not None:
        return cached
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    _modules[alias] = module
    return module


def _file_safety() -> ModuleType:
    return _sibling("_df_file_safety", "file_safety.py")


def _evidence_store() -> ModuleType:
    return _sibling("_df_evidence_store", "_evidence_store.py")


def _projection() -> ModuleType:
    return _sibling("_df_knowledge_projection", "_knowledge_projection.py")


# ── Snapshot model ─────────────────────────────────────────────────────────────


class _LogView(NamedTuple):
    """The admitted content of one readable log."""

    frames: list[tuple[dict, list[dict]]]
    semantic_records: dict[str, dict[str, dict]]
    superseded: frozenset[str]


class _SpecSource(NamedTuple):
    """One spec directory's contribution to the snapshot."""

    spec_path: str
    state: str  # "ok", "absent", or an unread reason code
    length: int | None = None
    sha256: str | None = None
    view: _LogView | None = None


class _Slot(NamedTuple):
    """One stream position: a fact to project, or an unread source to report."""

    spec_path: str
    reason_code: str | None = None
    record_kind: str = ""
    record_id: str = ""
    transaction_id: str = ""
    schema_version: int = 1
    record: dict | None = None
    view: _LogView | None = None


def _missing(exc: BaseException) -> bool:
    """Return True when a confined read failed because a path component is absent."""
    return isinstance(exc.__cause__, FileNotFoundError)


def _shadow_dir_state(shadow_dir: Path) -> str:
    """Diagnose a failed marker read without reading: absent, unsafe, or a plain directory."""
    try:
        info = os.lstat(shadow_dir)
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "shadow-dir-unsafe"
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return "shadow-dir-unsafe"
    return "directory"


def _marker_refusal(root: Path, shadow_dir: Path) -> str | None:
    """Return None when the exact marker is present, else ``absent`` or a reason code."""
    fs = _file_safety()
    try:
        marker = fs.read_confined_regular_file(
            root, shadow_dir / _MARKER_NAME, max_bytes=len(_MARKER_BYTES)
        )
    except fs.BoundExceeded:
        return "marker-invalid"
    except fs.UnsafeContentError as exc:
        state = _shadow_dir_state(shadow_dir)
        if state != "directory":
            return state
        return "marker-missing" if _missing(exc) else "marker-unsafe"
    except OSError:
        return "marker-unsafe"
    return None if marker == _MARKER_BYTES else "marker-invalid"


def _admit(raw: bytes) -> _LogView | str:
    """Replay the log's complete frames as the store does, or return a refusal reason.

    A record id or transaction id the feed's identifier pattern cannot hold does
    not refuse the log: ``_feed_identifier`` gives it a stable stand-in, so the
    log's other facts stay listed.
    """
    es = _evidence_store()
    try:
        replay = es.replay_admitted_frames(raw)
    except es.EvidenceStoreError:
        return "log-corrupt"
    for _tx, records in replay["frames"]:
        for record in records:
            version = record.get("schema_version")
            if (
                es._semantic_record_kind(record) is None
                or type(version) is not int
                or not 1 <= version <= _MAX_RECORD_SCHEMA_VERSION
            ):
                return "log-identity-invalid"
    return _LogView(
        frames=replay["frames"],
        semantic_records=replay["semantic_records"],
        superseded=replay["superseded"],
    )


def _feed_identifier(value: object) -> str:
    """Return *value* when the identifier pattern holds it, else a stable stand-in.

    The stand-in is ``digest-sha256:`` plus the SHA-256 of the identifier's UTF-8
    bytes, so one id maps to one stand-in in every process and the entry still
    validates.  Only the shown identity changes; the record is read by its own id.
    """
    kp = _projection()
    if kp.is_identifier(value):
        return str(value)
    digest = hashlib.sha256(str(value).encode("utf-8", errors="surrogatepass")).hexdigest()
    return "digest-sha256:" + digest


def _read_spec_source(root: Path, spec_dir: Path, spec_path: str, log_cap: int) -> _SpecSource:
    """Read one spec's log through the confined helpers, or report why it is unread."""
    fs = _file_safety()
    shadow_dir = spec_dir / _SHADOW_SUBDIR
    refusal = _marker_refusal(root, shadow_dir)
    if refusal == "absent":
        return _SpecSource(spec_path, "absent")
    if refusal is not None:
        return _SpecSource(spec_path, refusal)
    try:
        raw = fs.read_confined_regular_file(root, shadow_dir / _EVIDENCE_LOG, max_bytes=log_cap)
    except fs.BoundExceeded:
        return _SpecSource(spec_path, "log-oversized")
    except fs.UnsafeContentError as exc:
        return _SpecSource(spec_path, "absent" if _missing(exc) else "log-unsafe")
    except OSError:
        return _SpecSource(spec_path, "log-unsafe")
    digest = hashlib.sha256(raw).hexdigest()
    # A torn final frame (bytes after the last newline) is invisible and left
    # unrepaired; the digest above still covers it, so completing it changes the snapshot.
    view = _admit(raw[: raw.rfind(b"\n") + 1])
    if isinstance(view, str):
        return _SpecSource(spec_path, view, len(raw), digest)
    return _SpecSource(spec_path, "ok", len(raw), digest, view)


def _list_specs(root: Path) -> list[Path]:
    """List the directories directly under ``docs/specs/``, refusing the scan when unsafe."""
    fs = _file_safety()
    specs_root = root / "docs" / "specs"
    try:
        fs.validate_confined_directory(root, specs_root)
    except fs.UnsafeContentError as exc:
        if _missing(exc):
            return []  # a repository with no docs/specs/ has no specs to scan
        raise ScanRefused("specs-root-refused") from None
    try:
        directories = fs.list_confined_directories(root, specs_root)
    except fs.UnsafeContentError:
        raise ScanRefused("specs-entry-refused") from None
    except OSError:
        raise ScanRefused("specs-entry-refused") from None
    for directory in directories:
        if _SPEC_NAME_RE.fullmatch(directory.name) is None:
            raise ScanRefused("specs-entry-name-invalid")
    return directories


def _snapshot_id(shadow_services: str, sources: list[_SpecSource]) -> str:
    """Return the digest that fixes the source set."""
    kp = _projection()
    payload = kp.canonical_json({
        "content_policy_version": kp.content_policy_version(),
        "projection_policy_version": kp.PROJECTION_POLICY_VERSION,
        "shadow_services": shadow_services,
        "sources": [
            [source.spec_path, source.state, source.length, source.sha256]
            for source in sources
        ],
    })
    return "snapshot-sha256-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _slots(sources: list[_SpecSource]) -> list[_Slot]:
    """Flatten the source set into stream positions: spec order, then frame and record order."""
    es = _evidence_store()
    slots: list[_Slot] = []
    for source in sources:
        if source.state == "ok" and source.view is not None:
            for tx, records in source.view.frames:
                for record in records:
                    slots.append(_Slot(
                        spec_path=source.spec_path,
                        record_kind=es._semantic_record_kind(record) or "",
                        record_id=str(es._semantic_record_id(record)),
                        transaction_id=tx["transaction_id"],
                        schema_version=record["schema_version"],
                        record=record,
                        view=source.view,
                    ))
        elif source.state != "absent":
            slots.append(_Slot(spec_path=source.spec_path, reason_code=source.state))
    return slots


def _entry(slot: _Slot, ordinal: int) -> dict[str, Any]:
    """Build the feed entry for one stream position."""
    if slot.reason_code is not None:
        return {
            "entry_kind": "unread-source",
            "ordinal": ordinal,
            "spec_path": slot.spec_path,
            "reason_code": slot.reason_code,
        }
    es = _evidence_store()
    kp = _projection()
    record = slot.record or {}
    superseded = slot.record_id in (slot.view.superseded if slot.view else frozenset())
    report = finding = None
    if (
        slot.record_kind == "evidence-receipt.v1"
        and kp.is_review_failure_receipt(record)
        and slot.view is not None
    ):
        report_id, finding_id = es._find_receipt_source(slot.view.semantic_records, record)
        if report_id is not None and finding_id is not None:
            report, finding = es._find_report_finding(
                slot.view.semantic_records, report_id, finding_id
            )
    projection = kp.project_record(
        slot.record_kind,
        record,
        spec_path=slot.spec_path,
        transaction_id=slot.transaction_id,
        superseded=superseded,
        report=report,
        finding=finding,
    )
    return {
        "entry_kind": "fact",
        "ordinal": ordinal,
        "source": {
            "spec_path": slot.spec_path,
            "transaction_id": _feed_identifier(slot.transaction_id),
            "record_kind": slot.record_kind,
            "record_id": _feed_identifier(slot.record_id),
            "predecessor_schema_version": slot.schema_version,
        },
        "observation": projection.observation,
        "none_reason": projection.none_reason,
    }


def _parse_token(token: str) -> tuple[str, int]:
    """Return ``(snapshot digest, position)`` from a continuation token, or refuse."""
    match = _TOKEN_RE.fullmatch(token)
    if match is None:
        raise ScanRefused("token-invalid")
    return "snapshot-sha256-" + match.group(1), int(match.group(2))


def _compose(
    shadow_services: str,
    snapshot: str,
    first: int,
    entries: list[dict[str, Any]],
    continuation: str | None,
) -> dict[str, Any]:
    """Assemble one page object."""
    return {
        "schema_version": 1,
        "snapshot_id": snapshot,
        "shadow_services": shadow_services,
        "first_ordinal": first,
        "entries": entries,
        "continuation": continuation,
    }


def render_page(page: dict[str, Any]) -> bytes:
    """Serialize a page as canonical ASCII JSON plus one newline."""
    return (_projection().canonical_json(page) + "\n").encode("ascii")


def feed_page(
    root: Path,
    *,
    continuation: str | None = None,
    environ: Mapping[str, str] | None = None,
    log_max_bytes: int | None = None,
) -> dict[str, Any]:
    """Return one ``delivery-fact-feed.v1`` page, or raise ``ScanRefused``.

    *root* is the repository root every read is confined to.  *continuation* is
    the token from the previous page, or ``None`` for the first page.
    *log_max_bytes* overrides the store's 256 MiB per-log cap, for tests.
    """
    kp = _projection()
    env = os.environ if environ is None else environ
    if env.get(SHADOW_ENV_VAR, "") != "1":
        # Complete and empty, decided before any listing or read.
        snapshot = _snapshot_id("disabled", [])
        if continuation is not None:
            digest, _ = _parse_token(continuation)
            if digest != snapshot:
                raise ScanRefused("snapshot-changed")
            raise ScanRefused("token-invalid")
        return _compose("disabled", snapshot, 0, [], None)

    token_digest, position = (None, 0) if continuation is None else _parse_token(continuation)
    cap = _evidence_store()._EVIDENCE_LOG_MAX_BYTES if log_max_bytes is None else log_max_bytes
    try:
        root_info = os.lstat(root)
    except OSError:
        raise ScanRefused("root-invalid") from None
    if not stat.S_ISDIR(root_info.st_mode) or stat.S_ISLNK(root_info.st_mode):
        raise ScanRefused("root-invalid")

    sources = [
        _read_spec_source(root, directory, f"docs/specs/{directory.name}", cap)
        for directory in _list_specs(root)
    ]
    snapshot = _snapshot_id("enabled", sources)
    if token_digest is not None and token_digest != snapshot:
        raise ScanRefused("snapshot-changed")
    slots = _slots(sources)
    if position >= max(len(slots), 1) and continuation is not None:
        raise ScanRefused("token-invalid")

    # Page size is counted exactly: the empty page (continuation null) plus each
    # entry and its comma, plus the token's extra bytes when more entries remain.
    used = len(render_page(_compose("enabled", snapshot, position, [], None)))
    digest = snapshot.rsplit("-", 1)[1]
    entries: list[dict[str, Any]] = []
    index = position
    while index < len(slots) and len(entries) < MAX_ENTRIES:
        entry = _entry(slots[index], index)
        size = len(kp.canonical_json(entry)) + (1 if entries else 0)
        following = index + 1
        token_extra = 0 if following >= len(slots) else len(f"dff1.{digest}.{following}") + 2 - 4
        if entries and used + size + token_extra > MAX_PAGE_BYTES:
            break
        entries.append(entry)
        used += size
        index += 1
    next_token = None if index >= len(slots) else f"dff1.{digest}.{index}"
    page = _compose("enabled", snapshot, position, entries, next_token)
    if len(render_page(page)) > MAX_PAGE_BYTES:
        raise ScanRefused("scan-failed")
    return page
