#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import contextlib
import copy
import hashlib
import html
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_project_knowledge() -> Any:
    spec = importlib.util.spec_from_file_location(
        "_project_knowledge_contracts",
        SCRIPT_DIR / "project_knowledge.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("project knowledge contract module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_statelock() -> Any:
    spec = importlib.util.spec_from_file_location(
        "_project_knowledge_statelock",
        SCRIPT_DIR / "_statelock.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("project knowledge lock module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PK = _load_project_knowledge()
STATELOCK = _load_statelock()
OBSERVATIONS_ROOT = Path("docs/knowledge/observations")
TOPICS_ROOT = Path("docs/knowledge/topics")
TOPIC_MAP = Path("docs/knowledge/topics.index.json")
LEGACY_PATTERNS = Path("docs/knowledge/patterns.jsonl")
MIGRATION_STAGE = Path("docs/knowledge/.migration-stage")
_CAPTURED = "observation.captured"
_DISPOSITIONED = "observation.dispositioned"
_TERMINAL_DISPOSITIONS = {"promoted", "duplicate", "routed", "rejected", "superseded"}
_AUTOMATIC_RETRY_COUNT = 0
_TOPIC_LIFECYCLES = {"active", "needs_review", "retired"}
_RETIREMENT_REASONS = {"canonicalized", "enforced", "obsolete", "merged", "invalidated"}
_GIT_OBJECT_LENGTHS = {"sha1": 40, "sha256": 64}
_MAX_DISTILL_CANDIDATES = 12
_MAX_NAMED_SOURCES = 12
_DEADLINE: float | None = None


class KnowledgeStoreError(Exception):
    def __init__(self, diagnostic: dict[str, Any]) -> None:
        super().__init__(diagnostic["reason_code"])
        self.diagnostic = diagnostic


def _diagnostic(
    reason_code: str,
    *,
    retryable: bool = False,
    path: str | None = None,
    line: int | None = None,
    recovery_action: str | None = None,
) -> dict[str, Any]:
    return PK.render_diagnostic(
        PK.KnowledgeDiagnostic(
            reason_code=reason_code,
            retryable=retryable,
            recovery_action=recovery_action or ("retry" if retryable else "fix_request"),
            path=path,
            line=line,
        )
    )


def _refuse(reason_code: str, *, retryable: bool = False) -> None:
    raise KnowledgeStoreError(_diagnostic(reason_code, retryable=retryable))


DEADLINE_EXCEEDED = "deadline_exceeded"


def _reraise_deadline(error: KnowledgeStoreError) -> None:
    """Re-raise *error* when it is a deadline breach, otherwise return.

    Call this from every handler that converts a refusal into a fallback value.
    A deadline breach must not become `False`, a default, or another reason
    code: the caller loses both the retry advice and the true cause, and the
    fallback then re-refuses with something that reads as a different fault.
    """
    if error.diagnostic.get("reason_code") == DEADLINE_EXCEEDED:
        raise error


def _refuse_with_diagnostic(diagnostic: dict[str, Any]) -> None:
    raise KnowledgeStoreError(diagnostic)


def _assert_persistable_metadata(*values: str) -> None:
    try:
        PK.assert_persistable_text(*values)
    except PK.PrivacyRefusal:
        _refuse("privacy")


def budget_contract() -> dict[str, int]:
    return PK.budget_contract()


def observed_automatic_retry_count() -> int:
    return _AUTOMATIC_RETRY_COUNT


def set_deadline(seconds: int) -> None:
    global _DEADLINE
    if not isinstance(seconds, int) or seconds < 1:
        _refuse("strict_parse")
    _DEADLINE = time.monotonic() + seconds


def _remaining_timeout() -> float:
    """Return the remaining script deadline or refuse a retryable deadline breach."""
    if _DEADLINE is None:
        return float(budget_contract()["script_seconds"])
    remaining = _DEADLINE - time.monotonic()
    if remaining <= 0:
        _refuse("deadline_exceeded", retryable=True)
    return remaining


def _git_environment() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        _refuse("confinement")
    reparse_flag = 0x400
    return path.is_symlink() or bool(getattr(metadata, "st_file_attributes", 0) & reparse_flag)


def _assert_confined_components(root: Path, target: Path) -> None:
    try:
        relative = target.relative_to(root)
    except ValueError:
        _refuse("confinement")
    current = root
    for component in relative.parts:
        current = current / component
        if not current.exists():
            continue
        if _is_reparse_or_symlink(current):
            _refuse("confinement")
        if current != target and not current.is_dir():
            _refuse("confinement")


def _read_regular_file_bounded(
    path: Path,
    max_bytes: int,
    *,
    missing_ok: bool = False,
    reject_hard_links: bool = False,
) -> bytes | None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        _refuse("confinement")
    except OSError:
        _refuse("confinement")
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)
        or (reject_hard_links and metadata.st_nlink > 1)
    ):
        _refuse("confinement")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode) or (
                reject_hard_links and opened.st_nlink > 1
            ):
                _refuse("confinement")
            if opened.st_size > max_bytes:
                _refuse("journal_capacity")
            raw = handle.read(max_bytes + 1)
    except OSError:
        _refuse("confinement")
    if len(raw) > max_bytes:
        _refuse("journal_capacity")
    return raw


def _regular_file_size_bounded(path: Path, max_bytes: int) -> int:
    try:
        metadata = path.lstat()
    except OSError:
        _refuse("confinement")
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or bool(getattr(metadata, "st_file_attributes", 0) & 0x400)
    ):
        _refuse("confinement")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
    except OSError:
        _refuse("confinement")
    if not stat.S_ISREG(opened.st_mode):
        _refuse("confinement")
    if opened.st_size > max_bytes:
        _refuse("journal_capacity")
    return opened.st_size


def _assert_original_directory_path(candidate: Path) -> None:
    absolute = candidate.absolute()
    current = Path(absolute.anchor)
    for component in absolute.parts[1:]:
        current = current / component
        if not current.exists():
            _refuse("confinement")
        if _is_reparse_or_symlink(current) or not current.is_dir():
            _refuse("confinement")


def resolve_worktree_root(repo_root: Path | str) -> Path:
    candidate = Path(repo_root)
    try:
        _assert_original_directory_path(candidate)
        if not candidate.exists() or not candidate.is_dir() or candidate.is_symlink():
            _refuse("confinement")
        raw = subprocess.check_output(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            env=_git_environment(),
            timeout=_remaining_timeout(),
        )
        root = Path(raw.decode("utf-8", errors="strict").strip()).resolve(strict=True)
        candidate.resolve(strict=True).relative_to(root)
    except KnowledgeStoreError:
        raise
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
        subprocess.CalledProcessError,
        # A timeout stays a `confinement` refusal here, deliberately, and this is
        # the one place a deadline is not reported as one. This call IS the
        # confinement proof: if it does not finish, the root is unproven, and a
        # retryable diagnostic would invite a caller to loop against an
        # unbounded boundary check instead of stopping. Fail closed and say
        # `confinement`; every other deadline path reports `deadline_exceeded`.
        subprocess.TimeoutExpired,
    ):
        _refuse("confinement")
    if _is_reparse_or_symlink(root):
        _refuse("confinement")
    return root


def _parse_time(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError("invalid observation time") from exc


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _pretty_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _event_line(event: dict[str, Any]) -> bytes:
    return _canonical_json_bytes(event) + b"\n"


def _cursor_encode(value: dict[str, Any]) -> str:
    raw = _canonical_json_bytes(value)
    encoded = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    if len(encoded) > budget_contract()["envelope_bytes"]:
        _refuse("journal_capacity")
    return encoded


def _cursor_decode(value: Any) -> dict[str, Any]:
    try:
        if not isinstance(value, str) or len(value) > budget_contract()["envelope_bytes"]:
            raise ValueError("invalid cursor")
        padding = "=" * (-len(value) % 4)
        encoded = (value + padding).encode("ascii")
        raw = base64.b64decode(encoded, altchars=b"-_", validate=True)
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=PK._reject_duplicate_keys,
            parse_constant=PK._reject_constant,
        )
    except (
        UnicodeDecodeError,
        UnicodeEncodeError,
        TypeError,
        ValueError,
        binascii.Error,
        json.JSONDecodeError,
    ):
        _refuse("cursor_stale")
    if not isinstance(parsed, dict):
        _refuse("cursor_stale")
    return parsed


def _partition_for_request(request: dict[str, Any]) -> str:
    observed = _parse_time(request["observed_at"])
    return f"observations/{request['kind']}/{observed:%Y-%m}.jsonl"


def _is_capture_id(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 75 or not value.startswith("kco-"):
        return False
    month, separator, digest = value[4:].partition("-")
    return (
        bool(separator)
        and len(month) == 6
        and month.isdigit()
        and 1 <= int(month[4:]) <= 12
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )


def _is_reason_code(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 80
        and all(
            character in "abcdefghijklmnopqrstuvwxyz0123456789_-"
            for character in value
        )
    )


def knowledge_root(repo_root: Path | str) -> Path:
    root = Path(repo_root).resolve(strict=False)
    target = root / "docs" / "knowledge"
    _assert_confined_components(root, target)
    target.mkdir(parents=True, exist_ok=True)
    _assert_confined_components(root, target)
    return target


def knowledge_lock_path(repo_root: Path | str) -> Path:
    return STATELOCK.lock_path_for(_lock_target(repo_root))


def _lock_target(repo_root: Path | str) -> Path:
    return knowledge_root(repo_root) / ".project-knowledge.mutation"


@contextlib.contextmanager
def hold_writer_lock(
    repo_root: Path | str,
    *,
    timeout: float = 10.0,
    stale_after: float = 300.0,
) -> Iterator[Path]:
    target = _lock_target(repo_root)
    try:
        with STATELOCK.exclusive(target, timeout=timeout, stale_after=stale_after) as lock:
            yield lock
    except STATELOCK.StateLockLost:
        _refuse("lock_loss", retryable=True)
    except (STATELOCK.StateLockTimeout, STATELOCK.StateLockUnusable, STATELOCK.StateLockError):
        _refuse("lock_contention", retryable=True)


def _validate_partition_name(partition: str) -> str:
    parts = partition.split("/") if isinstance(partition, str) else []
    filename = parts[2] if len(parts) == 3 else ""
    month = filename.removesuffix(".jsonl")
    if (
        len(parts) != 3
        or parts[0] != "observations"
        or parts[1] not in {"pattern", "gotcha", "antipattern"}
        or not filename.endswith(".jsonl")
        or len(month) != 7
        or month[4] != "-"
        or not month[:4].isdigit()
        or not month[5:].isdigit()
        or not 1 <= int(month[5:]) <= 12
    ):
        _refuse("confinement")
    return partition


def _journal_path(repo_root: Path | str, partition: str) -> Path:
    _validate_partition_name(partition)
    relative = Path(*partition.split("/"))
    path = knowledge_root(repo_root) / relative
    _assert_confined_components(knowledge_root(repo_root), path)
    return path


def _validate_event(event: Any, expected_partition: str) -> dict[str, Any]:
    if not isinstance(event, dict):
        _refuse("strict_parse")
    event_type = event.get("event_type")
    if event_type == _CAPTURED:
        required = {
            "event_type",
            "schema_version",
            "capture_id",
            "partition",
            "captured_at",
            "state",
            "request",
            "request_sha256",
        }
        if set(event) != required:
            _refuse("strict_parse")
        if event["schema_version"] != "observation-event.v1":
            _refuse("strict_parse")
        if event["partition"] != expected_partition or event["state"] != "pending":
            _refuse("postimage_mismatch")
        try:
            request = PK.validate_capture_request(copy.deepcopy(event["request"]))
        except PK.PrivacyRefusal:
            _refuse("privacy")
        except ValueError:
            _refuse("strict_parse")
        if _partition_for_request(request) != expected_partition:
            _refuse("postimage_mismatch")
        if PK.derive_capture_id(request) != event["capture_id"]:
            _refuse("postimage_mismatch")
        if PK.digest_bytes(_canonical_json_bytes(request))["sha256"] != event["request_sha256"]:
            _refuse("postimage_mismatch")
        try:
            _parse_time(event["captured_at"])
        except (TypeError, ValueError):
            _refuse("strict_parse")
        return event
    if event_type == _DISPOSITIONED:
        required = {
            "event_type",
            "schema_version",
            "capture_id",
            "partition",
            "disposition",
            "reason_code",
            "recorded_at",
        }
        if (
            set(event) != required
            or event["schema_version"] != "observation-event.v1"
            or event["partition"] != expected_partition
            or not _is_capture_id(event["capture_id"])
        ):
            _refuse("strict_parse")
        if event["disposition"] not in _TERMINAL_DISPOSITIONS:
            _refuse("strict_parse")
        if not _is_reason_code(event["reason_code"]):
            _refuse("strict_parse")
        _assert_persistable_metadata(event["reason_code"])
        try:
            _parse_time(event["recorded_at"])
        except (TypeError, ValueError):
            _refuse("strict_parse")
        return event
    _refuse("strict_parse")
    raise AssertionError("unreachable")


def _validated_event_lines(
    lines: Iterator[bytes], partition: str
) -> Iterator[dict[str, Any]]:
    captured: dict[str, dict[str, Any]] = {}
    terminal: set[str] = set()
    for raw in lines:
        try:
            parsed = json.loads(
                raw.decode("utf-8", errors="strict"),
                object_pairs_hook=PK._reject_duplicate_keys,
                parse_constant=PK._reject_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            _refuse("strict_parse")
        event = _validate_event(parsed, partition)
        capture_id = event["capture_id"]
        if event["event_type"] == _CAPTURED:
            existing = captured.get(capture_id)
            if existing is not None:
                if existing != event:
                    _refuse("postimage_mismatch")
                continue
            captured[capture_id] = event
        else:
            if capture_id not in captured or capture_id in terminal:
                _refuse("postimage_mismatch")
            terminal.add(capture_id)
        yield event


def _iter_events(path: Path, partition: str) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    if not path.is_file() or _is_reparse_or_symlink(path):
        _refuse("confinement")
    try:
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_size > budget_contract()["journal_partition_bytes"]
            ):
                _refuse("journal_capacity")
            yield from _validated_event_lines(iter(handle), partition)
    except OSError:
        _refuse("confinement")


def _read_events(path: Path, partition: str) -> list[dict[str, Any]]:
    return list(_iter_events(path, partition))


def _observation_partitions(
    repo_root: Path | str,
    *,
    budgets: dict[str, int] | None = None,
) -> list[str]:
    limits = budgets or budget_contract()
    root = knowledge_root(repo_root) / "observations"
    if not root.exists():
        return []
    if not root.is_dir() or _is_reparse_or_symlink(root):
        _refuse("confinement")
    paths: list[Path] = []
    total_bytes = 0
    for kind in ("antipattern", "gotcha", "pattern"):
        kind_root = root / kind
        if not kind_root.exists():
            continue
        if not kind_root.is_dir() or _is_reparse_or_symlink(kind_root):
            _refuse("confinement")
        try:
            entries = kind_root.iterdir()
            for path in entries:
                _remaining_timeout()
                if path.suffix != ".jsonl":
                    continue
                partition = path.relative_to(knowledge_root(repo_root)).as_posix()
                _validate_partition_name(partition)
                if len(paths) >= limits["retained_partitions"]:
                    _refuse("journal_capacity")
                raw_size = _regular_file_size_bounded(
                    path,
                    limits["journal_partition_bytes"],
                )
                total_bytes += raw_size
                if total_bytes > limits["retained_journal_bytes"]:
                    _refuse("journal_capacity")
                paths.append(path)
        except OSError:
            _refuse("confinement")
    return sorted(
        path.relative_to(knowledge_root(repo_root)).as_posix() for path in paths
    )


def _partition_digests(
    repo_root: Path | str, partitions: Sequence[str]
) -> list[dict[str, Any]]:
    remaining = budget_contract()["pending_page_bytes"]
    result = []
    for partition in partitions:
        path = _journal_path(repo_root, partition)
        raw = b""
        if path.exists():
            if not path.is_file() or _is_reparse_or_symlink(path):
                _refuse("confinement")
            try:
                with path.open("rb") as handle:
                    opened = os.fstat(handle.fileno())
                    if not stat.S_ISREG(opened.st_mode) or opened.st_size > remaining:
                        _refuse("journal_capacity")
                    raw = handle.read(remaining + 1)
            except OSError:
                _refuse("confinement")
            if len(raw) > remaining:
                _refuse("journal_capacity")
            remaining -= len(raw)
        result.append({"partition": partition, "digest": PK.digest_bytes(raw)})
    return result


def _terminal_capture_ids(events: Sequence[dict[str, Any]]) -> set[str]:
    return {
        event["capture_id"]
        for event in events
        if event["event_type"] == _DISPOSITIONED
    }


def _find_capture(
    repo_root: Path | str,
    capture_id: str,
) -> tuple[str, dict[str, Any], dict[str, Any] | None]:
    found: tuple[str, dict[str, Any], dict[str, Any] | None] | None = None
    for partition in _observation_partitions(repo_root):
        events = _read_events(_journal_path(repo_root, partition), partition)
        capture = next(
            (
                event
                for event in events
                if event["event_type"] == _CAPTURED and event["capture_id"] == capture_id
            ),
            None,
        )
        if capture is None:
            continue
        disposition = next(
            (
                event
                for event in events
                if event["event_type"] == _DISPOSITIONED and event["capture_id"] == capture_id
            ),
            None,
        )
        if found is not None:
            _refuse("postimage_mismatch")
        found = (partition, capture, disposition)
    if found is None:
        _refuse("replay_required")
    return found


def _receipt(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "receipt_version": "knowledge-capture-receipt.v1",
        "capture_id": event["capture_id"],
        "partition": event["partition"],
        "event_type": event["event_type"],
        "state": event["state"],
    }


def _captured_event(
    request: dict[str, Any],
    *,
    writer_time: str,
    capture_id: str | None = None,
) -> dict[str, Any]:
    validated = PK.validate_capture_request(copy.deepcopy(request))
    event_capture_id = capture_id or PK.derive_capture_id(validated)
    return {
        "event_type": _CAPTURED,
        "schema_version": "observation-event.v1",
        "capture_id": event_capture_id,
        "partition": _partition_for_request(validated),
        "captured_at": _format_time(_parse_time(writer_time)),
        "state": "pending",
        "request": validated,
        "request_sha256": PK.digest_bytes(_canonical_json_bytes(validated))["sha256"],
    }


def captured_event_for_request(
    request: dict[str, Any],
    *,
    writer_time: str,
) -> dict[str, Any]:
    return _captured_event(request, writer_time=writer_time)


def _existing_replay(
    events: Sequence[dict[str, Any]],
    event: dict[str, Any],
) -> dict[str, Any] | None:
    for existing in events:
        if existing["event_type"] != _CAPTURED:
            continue
        if existing["capture_id"] != event["capture_id"]:
            continue
        if existing != event and existing["request"] != event["request"]:
            _refuse("postimage_mismatch")
        return _receipt(existing)
    return None


def _check_time_window(request: dict[str, Any], writer_time: str) -> None:
    observed = _parse_time(request["observed_at"])
    writer = _parse_time(writer_time)
    if observed < writer - timedelta(days=7):
        _refuse("provenance")
    if observed > writer + timedelta(minutes=5):
        _refuse("provenance")


def _check_pre_admission(request: dict[str, Any]) -> dict[str, Any]:
    try:
        return PK.validate_capture_request(copy.deepcopy(request))
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("provenance")


def _check_budgets(
    repo_root: Path | str,
    partition_path: Path,
    existing: Sequence[dict[str, Any]],
    postimage: bytes,
    event: dict[str, Any],
    budgets: dict[str, int],
) -> None:
    event_bytes = _event_line(event)
    if len(event_bytes) > budgets["capture_event_bytes"]:
        _refuse("journal_capacity")
    if len(postimage) > budgets["journal_partition_bytes"]:
        _refuse("journal_capacity")
    if len(existing) + 1 > budgets["journal_partition_events"]:
        _refuse("journal_capacity")
    partition_names = _observation_partitions(repo_root, budgets=budgets)
    partition_relative = partition_path.relative_to(knowledge_root(repo_root)).as_posix()
    if (
        partition_relative not in partition_names
        and len(partition_names) >= budgets["retained_partitions"]
    ):
        _refuse("journal_capacity")
    total = sum(
        _regular_file_size_bounded(
            _journal_path(repo_root, partition),
            budgets["journal_partition_bytes"],
        )
        for partition in partition_names
        if partition != partition_relative
    ) + len(postimage)
    if total > budgets["retained_journal_bytes"]:
        _refuse("journal_capacity")


def _replace_atomic(path: Path, postimage: bytes, *, interrupt_after: str | None = None) -> None:
    parts = path.parts
    knowledge_index = next(
        (
            index
            for index in range(len(parts) - 1)
            if parts[index : index + 2] == ("docs", "knowledge")
        ),
        None,
    )
    if knowledge_index is None:
        _refuse("confinement")
    knowledge = Path(*parts[: knowledge_index + 2])
    _assert_confined_components(knowledge, path)
    if path.exists() and (not path.is_file() or _is_reparse_or_symlink(path)):
        _refuse("confinement")
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_confined_components(knowledge, path)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.tmp-",
        dir=str(path.parent),
    )
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(postimage)
            handle.flush()
            os.fsync(handle.fileno())
        if interrupt_after == "temp_write":
            _refuse("postimage_mismatch")
        if _read_regular_file_bounded(tmp, len(postimage)) != postimage:
            _refuse("postimage_mismatch")
        if interrupt_after == "temp_verify":
            _refuse("postimage_mismatch")
        tmp.replace(path)
        if interrupt_after == "journal_replace":
            _refuse("postimage_mismatch")
        if _read_regular_file_bounded(path, len(postimage)) != postimage:
            _refuse("postimage_mismatch")
        if interrupt_after == "post_verify":
            _refuse("postimage_mismatch")
    finally:
        with contextlib.suppress(FileNotFoundError):
            tmp.unlink()


def _topic_relative_path(topic_key: str) -> Path:
    if (
        not isinstance(topic_key, str)
        or not topic_key
        or topic_key.startswith("/")
        or topic_key.endswith("/")
        or "\\" in topic_key
        or ".." in topic_key.split("/")
    ):
        _refuse("confinement")
    try:
        PK._expect_repo_path(topic_key)
        PK.assert_persistable_paths(topic_key)
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("confinement")
    parts = topic_key.split("/")
    if any(not part or not part.replace("-", "").replace("_", "").isalnum() for part in parts):
        _refuse("confinement")
    return Path(*parts).with_suffix(".json")


def topic_path_for_key(repo_root: Path | str, topic_key: str) -> Path:
    path = knowledge_root(repo_root) / "topics" / _topic_relative_path(topic_key)
    _assert_confined_components(knowledge_root(repo_root) / "topics", path)
    return path


def _map_path(repo_root: Path | str) -> Path:
    return knowledge_root(repo_root) / "topics.index.json"


def _validate_scope_list(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        _refuse("strict_parse")
    scopes: list[str] = []
    for scope in value:
        try:
            normalized = PK._expect_repo_path(scope)
            PK.assert_persistable_paths(normalized)
            scopes.append(normalized)
        except PK.PrivacyRefusal:
            _refuse("privacy")
        except ValueError:
            _refuse("confinement")
    if len(set(scopes)) != len(scopes):
        _refuse("strict_parse")
    return scopes


def _validate_source(value: Any, *, digest_required: bool) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse("strict_parse")
    required = {"path", "digest"} if digest_required else {"path"}
    optional = set() if digest_required else {"digest"}
    try:
        PK._expect_keys(value, required, optional)
        value["path"] = PK._expect_repo_path(value["path"])
        PK.assert_persistable_paths(value["path"])
        if "digest" in value:
            PK.parse_digest(value["digest"])
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("strict_parse")
    return value


def _validate_occurrence(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse("strict_parse")
    required = {
        "capture_id",
        "mutation_id",
        "producer",
        "semantic_gate",
        "source",
        "scope",
        "observed_at",
        "reviewed_disposition",
    }
    optional = {"evidence_digest", "legacy_identity", "legacy_source"}
    try:
        PK._expect_keys(value, required, optional)
        if not _is_capture_id(value["capture_id"]):
            raise ValueError("invalid capture id")
        if not isinstance(value["mutation_id"], str) or not PK._HEX64.fullmatch(
            value["mutation_id"]
        ):
            raise ValueError("invalid mutation id")
        PK._expect_slug(value["producer"])
        PK._expect_slug(value["semantic_gate"])
        _assert_persistable_metadata(value["producer"], value["semantic_gate"])
        _validate_source(value["source"], digest_required=False)
        value["scope"] = PK._expect_repo_path(value["scope"])
        PK.assert_persistable_paths(value["scope"])
        _parse_time(value["observed_at"])
        if value["reviewed_disposition"] not in {
            "promoted",
            "active_import",
            "needs_review_import",
        }:
            raise ValueError("invalid reviewed disposition")
        if "evidence_digest" in value:
            PK.parse_digest(value["evidence_digest"])
        if "legacy_source" in value:
            PK._expect_text(value["legacy_source"], 500)
            PK.assert_persistable_text(value["legacy_source"])
        has_legacy_identity = "legacy_identity" in value
        has_legacy_source = "legacy_source" in value
        legacy_disposition = value["reviewed_disposition"] in {
            "active_import",
            "needs_review_import",
        }
        if has_legacy_identity:
            PK._expect_text(value["legacy_identity"], 80)
            PK.assert_persistable_text(value["legacy_identity"])
        if (
            has_legacy_identity != has_legacy_source
            or legacy_disposition != has_legacy_identity
            or legacy_disposition
            and (
                value["producer"] != "legacy-import"
                or value["semantic_gate"] != "legacy-import"
            )
        ):
            raise ValueError("invalid legacy provenance")
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("strict_parse")
    return value


def validate_topic(topic: Any) -> dict[str, Any]:
    if not isinstance(topic, dict):
        _refuse("strict_parse")
    required = {
        "schema_version",
        "topic_key",
        "title",
        "synthesis",
        "scopes",
        "competency_facets",
        "audience",
        "lifecycle",
        "freshness",
        "owning_source",
        "supporting_sources",
        "occurrences",
    }
    optional = {"retirement"}
    try:
        PK._expect_keys(topic, required, optional)
        if topic["schema_version"] != "knowledge-topic.v1":
            raise ValueError("invalid topic schema")
        _topic_relative_path(topic["topic_key"])
        PK._expect_text(topic["title"], 200)
        if not isinstance(topic["synthesis"], dict):
            raise ValueError("invalid synthesis")
        PK._expect_keys(topic["synthesis"], {"kind", "body"}, set())
        if topic["synthesis"]["kind"] not in {"pattern", "gotcha", "antipattern"}:
            raise ValueError("invalid synthesis kind")
        PK._expect_text(topic["synthesis"]["body"], 4000)
        PK.assert_persistable_text(topic["title"], topic["synthesis"]["body"])
        topic["scopes"] = _validate_scope_list(topic["scopes"])
        facets = topic["competency_facets"]
        if (
            not isinstance(facets, list)
            or not facets
            or any(not isinstance(facet, str) for facet in facets)
            or len(set(facets)) != len(facets)
            or any(facet not in PK.COMPETENCY_QUESTIONS for facet in facets)
        ):
            raise ValueError("invalid facets")
        if topic["audience"] != "project" or topic["lifecycle"] not in _TOPIC_LIFECYCLES:
            raise ValueError("invalid lifecycle")
        _validate_freshness(topic)
        _validate_retirement(topic)
        if topic["owning_source"] is not None:
            _validate_source(topic["owning_source"], digest_required=True)
        supporting = topic["supporting_sources"]
        if not isinstance(supporting, list):
            raise ValueError("invalid supporting sources")
        for source in supporting:
            _validate_source(source, digest_required=True)
        occurrences = topic["occurrences"]
        if (
            not isinstance(occurrences, list)
            or not occurrences
            or len(occurrences) > budget_contract()["occurrences_per_topic"]
        ):
            raise ValueError("invalid occurrences")
        for occurrence in occurrences:
            _validate_occurrence(occurrence)
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("strict_parse")
    return topic


def _validate_freshness(topic: dict[str, Any]) -> None:
    freshness = topic["freshness"]
    if not isinstance(freshness, dict):
        raise ValueError("invalid freshness")
    PK._expect_keys(freshness, {"state", "checked_at"}, {"review_after"})
    if topic["lifecycle"] == "active" and freshness["state"] != "fresh":
        raise ValueError("active topic must be fresh")
    if topic["lifecycle"] == "needs_review" and freshness["state"] != "review_required":
        raise ValueError("needs_review topic must be review_required")
    if topic["lifecycle"] == "retired" and freshness["state"] != "retired":
        raise ValueError("retired topic must be retired")
    _parse_time(freshness["checked_at"])
    if "review_after" in freshness:
        _parse_time(freshness["review_after"])


def _validate_retirement(topic: dict[str, Any]) -> None:
    if topic["lifecycle"] != "retired":
        if "retirement" in topic:
            raise ValueError("non-retired topic cannot carry retirement")
        return
    retirement = topic.get("retirement")
    if not isinstance(retirement, dict):
        raise ValueError("retired topic needs retirement")
    PK._expect_keys(retirement, {"reason", "successors", "coverage_verified"}, set())
    if retirement["reason"] not in _RETIREMENT_REASONS:
        raise ValueError("invalid retirement reason")
    successors = retirement["successors"]
    if not isinstance(successors, list):
        raise ValueError("invalid retirement successors")
    normalized_successors = [PK._expect_repo_path(item) for item in successors]
    PK.assert_persistable_paths(*normalized_successors)
    retirement["successors"] = normalized_successors
    if retirement["reason"] in {"canonicalized", "enforced", "merged"}:
        if not normalized_successors:
            raise ValueError("effective retirement needs successors")
        if retirement["coverage_verified"] is not True:
            raise ValueError("retirement coverage is unverified")


def _write_topic_unlocked(repo_root: Path | str, topic: dict[str, Any]) -> Path:
    validated = validate_topic(copy.deepcopy(topic))
    postimage = _pretty_json_bytes(validated)
    if len(postimage) > budget_contract()["topic_bytes"]:
        _refuse("journal_capacity")
    path = topic_path_for_key(repo_root, validated["topic_key"])
    _replace_atomic(path, postimage)
    return path


def write_topic(repo_root: Path | str, topic: dict[str, Any]) -> Path:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        return _write_topic_unlocked(repo_root, topic)


def _read_topic_record(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular_file_bounded(path, budget_contract()["topic_bytes"])
    assert raw is not None
    try:
        parsed = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=PK._reject_duplicate_keys,
            parse_constant=PK._reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        _refuse("strict_parse")
    return validate_topic(parsed), raw


def _read_topic(path: Path) -> dict[str, Any]:
    return _read_topic_record(path)[0]


def _git_object_algorithm(repo_root: Path | str | None = None) -> str:
    if repo_root is not None:
        try:
            value = _git_read(repo_root, ["rev-parse", "--show-object-format"])
            value = value.decode("ascii").strip()
            if value in _GIT_OBJECT_LENGTHS:
                return value
        except KnowledgeStoreError as error:
            # A deadline must not become a silent sha1 default. On a sha256
            # repository that is the wrong algorithm, and it resurfaces two hops
            # later as a map or provenance refusal with no trace of the timeout.
            _reraise_deadline(error)
    return "sha1"


def _git_blob_digest(raw: bytes, *, algorithm: str = "sha1") -> dict[str, Any]:
    if algorithm not in _GIT_OBJECT_LENGTHS:
        _refuse("map_mismatch")
    preimage = f"blob {len(raw)}\0".encode("ascii") + raw
    digest = hashlib.new(algorithm)
    digest.update(preimage)
    return {
        "kind": "git-blob-v1",
        "algorithm": algorithm,
        "object_id": digest.hexdigest(),
    }


def _git_read(repo_root: Path | str, args: Sequence[str]) -> bytes:
    """Read a Git result, distinguishing timeouts from incoherent snapshots."""
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            env=_git_environment(),
            timeout=_remaining_timeout(),
        )
    except subprocess.TimeoutExpired:
        _refuse("deadline_exceeded", retryable=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        _refuse("map_mismatch")
    raise AssertionError("unreachable")


def _git_read_bounded(
    repo_root: Path | str,
    args: Sequence[str],
    *,
    max_bytes: int,
) -> bytes:
    """Read a bounded Git result without conflating deadlines and byte limits."""
    try:
        with tempfile.TemporaryFile() as output:
            completed = subprocess.run(
                ["git", *args],
                cwd=repo_root,
                stdout=output,
                stderr=subprocess.DEVNULL,
                env=_git_environment(),
                timeout=_remaining_timeout(),
                check=False,
            )
            if completed.returncode != 0 or output.tell() > max_bytes:
                _refuse("journal_capacity" if output.tell() > max_bytes else "map_mismatch")
            output.seek(0)
            raw = output.read(max_bytes + 1)
    except subprocess.TimeoutExpired:
        _refuse("deadline_exceeded", retryable=True)
    except (FileNotFoundError, OSError):
        _refuse("map_mismatch")
    if len(raw) > max_bytes:
        _refuse("journal_capacity")
    return raw


def _head_snapshot(repo_root: Path | str) -> dict[str, str]:
    commit = _git_read(repo_root, ["rev-parse", "HEAD"]).decode("ascii").strip()
    tree = _git_read(repo_root, ["rev-parse", "HEAD^{tree}"]).decode("ascii").strip()
    return {"commit_id": commit, "tree_id": tree}


def _committed_blob_id(repo_root: Path | str, commit_id: str, relative_path: str) -> str:
    try:
        PK._expect_repo_path(relative_path)
    except ValueError:
        _refuse("confinement")
    raw = _git_read(repo_root, ["ls-tree", "-z", commit_id, "--", relative_path])
    if not raw or not raw.endswith(b"\0") or raw.count(b"\0") != 1:
        _refuse("map_mismatch")
    try:
        header, encoded_path = raw[:-1].split(b"\t", 1)
        fields = header.decode("ascii", errors="strict").split()
        listed_path = encoded_path.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _refuse("map_mismatch")
    except ValueError:
        _refuse("map_mismatch")
    if (
        len(fields) != 3
        or fields[0] not in {"100644", "100755"}
        or fields[1] != "blob"
        or listed_path != relative_path
    ):
        _refuse("map_mismatch")
    return fields[2]


def _committed_blob_ids(
    repo_root: Path | str,
    commit_id: str,
    tree_path: str,
) -> dict[str, str]:
    """Map every committed blob under one tree path to its object id in a single call.

    The per-path alternative spawns one `git ls-tree` per entry, which is
    O(topics) subprocesses inside a single script budget and is why the writer
    coherence check exhausted its 30s deadline at 65 topics.

    A non-success exit means the whole batch is unusable, not that the missing
    rows are absent: `_git_read_bounded` refuses, and the caller treats the
    refusal as incoherence rather than reading a partial answer as data.
    """
    try:
        PK._expect_repo_path(tree_path)
    except ValueError:
        _refuse("confinement")
    raw = _git_read_bounded(
        repo_root,
        ["ls-tree", "-r", "-z", commit_id, "--", tree_path],
        max_bytes=budget_contract()["map_bytes"],
    )
    blobs: dict[str, str] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            header, encoded_path = record.split(b"\t", 1)
            fields = header.decode("ascii", errors="strict").split()
            listed_path = encoded_path.decode("utf-8", errors="strict")
        except (UnicodeDecodeError, ValueError):
            _refuse("map_mismatch")
        if (
            len(fields) != 3
            or fields[0] not in {"100644", "100755"}
            or fields[1] != "blob"
            or listed_path in blobs
        ):
            _refuse("map_mismatch")
        blobs[listed_path] = fields[2]
    if len(blobs) > budget_contract()["map_entries"]:
        _refuse("journal_capacity")
    return blobs


def _committed_path_exists(repo_root: Path | str, commit_id: str, relative_path: str) -> bool:
    try:
        PK._expect_repo_path(relative_path)
    except ValueError:
        _refuse("confinement")
    try:
        return bool(_git_read(repo_root, ["ls-tree", commit_id, "--", relative_path]))
    except KnowledgeStoreError as error:
        _reraise_deadline(error)
        return False


def _committed_blob_size(repo_root: Path | str, commit_id: str, relative_path: str) -> int:
    object_id = _committed_blob_id(repo_root, commit_id, relative_path)
    raw = _git_read(repo_root, ["cat-file", "-s", object_id])
    try:
        value = int(raw.decode("ascii", errors="strict").strip())
    except (UnicodeDecodeError, ValueError):
        _refuse("map_mismatch")
    if value < 0:
        _refuse("map_mismatch")
    return value


def _committed_blob(
    repo_root: Path | str,
    commit_id: str,
    relative_path: str,
    *,
    max_bytes: int,
) -> bytes:
    try:
        PK._expect_repo_path(relative_path)
    except ValueError:
        _refuse("confinement")
    if _committed_blob_size(repo_root, commit_id, relative_path) > max_bytes:
        _refuse("journal_capacity")
    return _git_read_bounded(
        repo_root,
        ["show", f"{commit_id}:{relative_path}"],
        max_bytes=max_bytes,
    )


def _committed_topic_paths(repo_root: Path | str, commit_id: str) -> set[str]:
    raw = _git_read_bounded(
        repo_root,
        ["ls-tree", "-r", "-z", "--name-only", commit_id, "--", "docs/knowledge/topics"],
        max_bytes=budget_contract()["map_bytes"],
    )
    try:
        names = raw.decode("utf-8", errors="strict").split("\0")
    except UnicodeDecodeError:
        _refuse("map_mismatch")
    paths = {name for name in names if name.endswith(".json")}
    if len(paths) > budget_contract()["map_entries"]:
        _refuse("journal_capacity")
    return paths


def _bounded_topic_records(
    root: Path,
) -> list[tuple[Path, dict[str, Any], bytes]]:
    topics_dir = root / "topics"
    try:
        topics_metadata = topics_dir.lstat()
    except FileNotFoundError:
        return []
    except OSError:
        _refuse("confinement")
    if (
        not stat.S_ISDIR(topics_metadata.st_mode)
        or stat.S_ISLNK(topics_metadata.st_mode)
        or bool(getattr(topics_metadata, "st_file_attributes", 0) & 0x400)
    ):
        _refuse("confinement")
    paths: list[Path] = []

    def refuse_walk_error(_error: OSError) -> None:
        _refuse("confinement")

    for current, directories, filenames in os.walk(
        topics_dir,
        topdown=True,
        onerror=refuse_walk_error,
        followlinks=False,
    ):
        _remaining_timeout()
        current_path = Path(current)
        _assert_confined_components(topics_dir, current_path)
        directories.sort()
        for directory in directories:
            child = current_path / directory
            if _is_reparse_or_symlink(child) or not child.is_dir():
                _refuse("confinement")
        for filename in sorted(filenames):
            if not filename.endswith(".json"):
                continue
            paths.append(current_path / filename)
            if len(paths) > min(
                budget_contract()["topic_files"], budget_contract()["map_entries"]
            ):
                _refuse("journal_capacity")
    records: list[tuple[Path, dict[str, Any], bytes]] = []
    corpus_bytes = 0
    for path in sorted(paths):
        _assert_confined_components(topics_dir, path)
        topic, raw = _read_topic_record(path)
        corpus_bytes += len(raw)
        if corpus_bytes > budget_contract()["topic_corpus_bytes"]:
            _refuse("journal_capacity")
        expected = topics_dir / _topic_relative_path(topic["topic_key"])
        if path != expected:
            _refuse("map_mismatch")
        records.append((path, topic, raw))
    return records


def _topic_map_bytes(root: Path, *, repository_root: Path | str) -> bytes:
    algorithm = _git_object_algorithm(repository_root)
    entries: list[dict[str, Any]] = []
    records = _bounded_topic_records(root)
    for path, topic, raw in sorted(records, key=lambda item: item[1]["topic_key"]):
        entries.append(
            {
                "topic_key": topic["topic_key"],
                "title": topic["title"],
                "path": path.relative_to(root).as_posix(),
                "scopes": topic["scopes"],
                "competency_facets": topic["competency_facets"],
                "audience": topic["audience"],
                "lifecycle": topic["lifecycle"],
                "freshness": topic["freshness"],
                "blob": _git_blob_digest(raw, algorithm=algorithm),
            }
        )
    postimage = _pretty_json_bytes(
        {"schema_version": "knowledge-topic-map.v1", "entries": entries}
    )
    if len(entries) > budget_contract()["map_entries"] or len(postimage) > budget_contract()[
        "map_bytes"
    ]:
        _refuse("journal_capacity")
    return postimage


def _rebuild_topic_map_unlocked(repo_root: Path | str) -> bytes:
    postimage = _topic_map_bytes(
        knowledge_root(repo_root), repository_root=repo_root
    )
    _replace_atomic(_map_path(repo_root), postimage)
    return postimage


def rebuild_topic_map(repo_root: Path | str) -> bytes:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        return _rebuild_topic_map_unlocked(repo_root)


def rebuild_map_bytes(
    knowledge_dir: Path | str,
    *,
    repository_root: Path | str | None = None,
) -> bytes:
    root = Path(knowledge_dir)
    return _topic_map_bytes(
        root,
        repository_root=repository_root or root.parent.parent,
    )


def _file_digest(path: Path, *, max_bytes: int) -> dict[str, Any] | None:
    raw = _read_regular_file_bounded(path, max_bytes, missing_ok=True)
    if raw is None:
        return None
    return PK.digest_bytes(raw)


def topic_digest_for_key(repo_root: Path | str, topic_key: str) -> dict[str, Any] | None:
    return _file_digest(
        topic_path_for_key(repo_root, topic_key),
        max_bytes=budget_contract()["topic_bytes"],
    )


def _proposal_without_derived(proposal: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(proposal)
    result.pop("proposal_digest", None)
    result.pop("mutation_id", None)
    return result


def proposal_digest_preimage_fields() -> set[str]:
    completed = complete_mutation_proposal(_sample_mutation_proposal())
    return set(_proposal_without_derived(completed))


def occurrence_digest_fields() -> set[str]:
    return {"evidence_digest"}


def occurrence_fields() -> set[str]:
    return {
        "capture_id",
        "mutation_id",
        "producer",
        "semantic_gate",
        "source",
        "evidence_digest",
        "scope",
        "observed_at",
        "reviewed_disposition",
        "legacy_identity",
        "legacy_source",
    }


def _mutation_id(proposal: dict[str, Any]) -> str:
    semantic = {
        "contract": "mutation-id-v1",
        "capture_id": proposal["capture_id"],
        "topic_key": proposal["topic_key"],
        "title": proposal["title"],
        "synthesis": proposal["synthesis"],
        "scopes": proposal["scopes"],
        "competency_facets": proposal["competency_facets"],
        "owning_source": proposal["owning_source"],
        "supporting_sources": proposal["supporting_sources"],
        "occurrence": proposal["occurrence"],
    }
    return __import__("hashlib").sha256(_canonical_json_bytes(semantic)).hexdigest()


def _topic_from_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    mutation_id = _mutation_id(proposal)
    occurrence = {
        "capture_id": proposal["capture_id"],
        "mutation_id": mutation_id,
        "producer": proposal["occurrence"]["producer"],
        "semantic_gate": proposal["occurrence"]["semantic_gate"],
        "source": proposal["occurrence"]["source"],
        "scope": proposal["occurrence"]["scope"],
        "observed_at": proposal["occurrence"]["observed_at"],
        "reviewed_disposition": "promoted",
    }
    if "evidence_digest" in proposal["occurrence"]:
        occurrence["evidence_digest"] = proposal["occurrence"]["evidence_digest"]
    return {
        "schema_version": "knowledge-topic.v1",
        "topic_key": proposal["topic_key"],
        "title": proposal["title"],
        "synthesis": proposal["synthesis"],
        "scopes": proposal["scopes"],
        "competency_facets": proposal["competency_facets"],
        "audience": "project",
        "lifecycle": "active",
        "freshness": {"state": "fresh", "checked_at": proposal["occurrence"]["observed_at"]},
        "owning_source": proposal["owning_source"],
        "supporting_sources": proposal["supporting_sources"],
        "occurrences": [occurrence],
    }


def complete_mutation_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    completed = copy.deepcopy(proposal)
    try:
        completed["scopes"] = _validate_scope_list(completed["scopes"])
        _validate_source(completed["owning_source"], digest_required=True)
        supporting = completed["supporting_sources"]
        if not isinstance(supporting, list):
            raise ValueError("invalid supporting sources")
        for source in supporting:
            _validate_source(source, digest_required=True)
        occurrence = completed["occurrence"]
        if not isinstance(occurrence, dict):
            raise ValueError("invalid occurrence")
        _validate_source(occurrence["source"], digest_required=False)
        occurrence["scope"] = PK._expect_repo_path(occurrence["scope"])
        PK.assert_persistable_paths(occurrence["scope"])
        terminal = completed["terminal_disposition"]
        if not isinstance(terminal, dict):
            raise ValueError("invalid terminal disposition")
        PK._expect_keys(
            terminal,
            {"disposition", "reason_code", "recorded_at"},
            set(),
        )
        if terminal["disposition"] != "promoted" or not _is_reason_code(
            terminal["reason_code"]
        ):
            raise ValueError("invalid terminal disposition")
        _assert_persistable_metadata(terminal["reason_code"])
        _parse_time(terminal["recorded_at"])
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except (KeyError, TypeError, ValueError):
        _refuse("strict_parse")
    mutation_id = _mutation_id(completed)
    topic = _topic_from_proposal(completed)
    topic_postimage = _pretty_json_bytes(validate_topic(topic))
    completed["topic_postimage_digest"] = PK.digest_bytes(topic_postimage)
    proposal_preimage = _proposal_without_derived(completed | {"mutation_id": mutation_id})
    completed["proposal_digest"] = PK.digest_bytes(_canonical_json_bytes(proposal_preimage))
    return completed


def _validate_mutation_proposal(proposal: Any) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        _refuse("strict_parse")
    if isinstance(proposal.get("topic_key"), list):
        _refuse("strict_parse")
    required = {
        "schema_version",
        "capture_id",
        "topic_key",
        "title",
        "synthesis",
        "scopes",
        "competency_facets",
        "owning_source",
        "supporting_sources",
        "occurrence",
        "terminal_disposition",
        "expected_topic_digest",
        "proposal_digest",
        "topic_postimage_digest",
    }
    try:
        PK._expect_keys(proposal, required, set())
        if proposal["schema_version"] != "knowledge-mutation-proposal.v1":
            raise ValueError("invalid proposal schema")
        _topic_relative_path(proposal["topic_key"])
        PK._expect_text(proposal["title"], 200)
        if not isinstance(proposal["synthesis"], dict):
            raise ValueError("invalid synthesis")
        PK._expect_keys(proposal["synthesis"], {"kind", "body"}, set())
        if proposal["synthesis"].get("kind") not in {"pattern", "gotcha", "antipattern"}:
            raise ValueError("invalid synthesis")
        PK._expect_text(proposal["synthesis"].get("body"), 4000)
        PK.assert_persistable_text(proposal["title"], proposal["synthesis"]["body"])
        proposal["scopes"] = _validate_scope_list(proposal["scopes"])
        facets = proposal["competency_facets"]
        if (
            not isinstance(facets, list)
            or not facets
            or any(not isinstance(facet, str) for facet in facets)
            or len(set(facets)) != len(facets)
            or any(facet not in PK.COMPETENCY_QUESTIONS for facet in facets)
        ):
            raise ValueError("invalid facets")
        _validate_source(proposal["owning_source"], digest_required=True)
        supporting = proposal["supporting_sources"]
        if not isinstance(supporting, list):
            raise ValueError("invalid supporting sources")
        for source in supporting:
            _validate_source(source, digest_required=True)
        occurrence = proposal["occurrence"]
        if not isinstance(occurrence, dict):
            raise ValueError("invalid occurrence")
        PK._expect_keys(
            occurrence,
            {"producer", "semantic_gate", "source", "scope", "observed_at"},
            {"evidence_digest"},
        )
        PK._expect_slug(occurrence["producer"])
        PK._expect_slug(occurrence["semantic_gate"])
        _assert_persistable_metadata(
            occurrence["producer"], occurrence["semantic_gate"]
        )
        _validate_source(occurrence["source"], digest_required=False)
        occurrence["scope"] = PK._expect_repo_path(occurrence["scope"])
        PK.assert_persistable_paths(occurrence["scope"])
        _parse_time(occurrence["observed_at"])
        if "evidence_digest" in occurrence:
            PK.parse_digest(occurrence["evidence_digest"])
        terminal = proposal["terminal_disposition"]
        if not isinstance(terminal, dict):
            raise ValueError("invalid terminal disposition")
        PK._expect_keys(
            terminal,
            {"disposition", "reason_code", "recorded_at"},
            set(),
        )
        if terminal["disposition"] != "promoted":
            raise ValueError("invalid mutation disposition")
        if not _is_reason_code(terminal["reason_code"]):
            raise ValueError("invalid mutation reason")
        _assert_persistable_metadata(terminal["reason_code"])
        _parse_time(terminal["recorded_at"])
        if proposal["expected_topic_digest"] is not None:
            PK.parse_digest(proposal["expected_topic_digest"])
        PK.parse_digest(proposal["proposal_digest"])
        PK.parse_digest(proposal["topic_postimage_digest"])
        expected = complete_mutation_proposal(_proposal_without_derived(proposal))
        if proposal["proposal_digest"] != expected["proposal_digest"]:
            raise ValueError("invalid proposal digest")
        if proposal["topic_postimage_digest"] != expected["topic_postimage_digest"]:
            raise ValueError("invalid topic postimage digest")
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("strict_parse")
    return proposal


def _ensure_expected_precondition(repo_root: Path | str, proposal: dict[str, Any]) -> None:
    expected = proposal["expected_topic_digest"]
    current = topic_digest_for_key(repo_root, proposal["topic_key"])
    if expected != current:
        _refuse("postimage_mismatch")


def _append_terminal_disposition(
    repo_root: Path | str,
    partition: str,
    capture_id: str,
    disposition: str,
    reason_code: str,
    recorded_at: str,
) -> dict[str, Any]:
    path = _journal_path(repo_root, partition)
    event = {
        "event_type": _DISPOSITIONED,
        "schema_version": "observation-event.v1",
        "capture_id": capture_id,
        "partition": partition,
        "disposition": disposition,
        "reason_code": reason_code,
        "recorded_at": recorded_at,
    }
    _validate_event(event, partition)
    existing = _read_events(path, partition)
    prior = [
        item
        for item in existing
        if item["event_type"] == _DISPOSITIONED and item["capture_id"] == capture_id
    ]
    if prior:
        if prior[0] != event:
            _refuse("postimage_mismatch")
        return event
    postimage = b"".join(_event_line(item) for item in [*existing, event])
    _replace_atomic(path, postimage)
    return event


def _write_disposition(repo_root: Path | str, proposal: dict[str, Any]) -> None:
    partition, _capture, _disposition = _find_capture(repo_root, proposal["capture_id"])
    terminal = proposal["terminal_disposition"]
    _append_terminal_disposition(
        repo_root,
        partition,
        proposal["capture_id"],
        terminal["disposition"],
        terminal["reason_code"],
        terminal["recorded_at"],
    )


def write_terminal_disposition(
    repo_root: Path | str,
    capture_id: str,
    disposition: str,
    *,
    reason_code: str,
    recorded_at: str,
    lock_timeout: float = 10.0,
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    if disposition not in _TERMINAL_DISPOSITIONS or disposition == "promoted":
        _refuse("strict_parse")
    if not _is_reason_code(reason_code):
        _refuse("strict_parse")
    _assert_persistable_metadata(reason_code)
    try:
        _parse_time(recorded_at)
    except (TypeError, ValueError):
        _refuse("strict_parse")
    with hold_writer_lock(repo_root, timeout=lock_timeout):
        _assert_v1_writer_allowed(repo_root)
        partition, _capture, _disposition = _find_capture(repo_root, capture_id)
        event = _append_terminal_disposition(
            repo_root,
            partition,
            capture_id,
            disposition,
            reason_code,
            recorded_at,
        )
    return {
        "capture_id": event["capture_id"],
        "partition": event["partition"],
        "disposition": event["disposition"],
        "reason_code": event["reason_code"],
    }


def _apply_guarded_mutation_body(
    repo_root: Path | str,
    validated: dict[str, Any],
    *,
    interrupt_after: str | None = None,
) -> dict[str, Any]:
    topic = _topic_from_proposal(validated)
    _assert_v1_writer_allowed(repo_root)
    _partition, _capture, existing_disposition = _find_capture(
        repo_root, validated["capture_id"]
    )
    if existing_disposition is not None:
        _refuse("postimage_mismatch")
    _ensure_expected_precondition(repo_root, validated)
    topic_path = topic_path_for_key(repo_root, topic["topic_key"])
    topic_postimage = _pretty_json_bytes(validate_topic(topic))
    if PK.digest_bytes(topic_postimage) != validated["topic_postimage_digest"]:
        _refuse("postimage_mismatch")
    if interrupt_after == "topic_replace":
        _replace_atomic(topic_path, topic_postimage)
        _refuse("postimage_mismatch")
    _replace_atomic(topic_path, topic_postimage)
    if interrupt_after == "topic":
        _refuse("postimage_mismatch")
    map_bytes = _rebuild_topic_map_unlocked(repo_root)
    if interrupt_after == "map":
        _refuse("postimage_mismatch")
    _write_disposition(repo_root, validated)
    if interrupt_after == "disposition":
        _refuse("postimage_mismatch")
    return {
        "mutation_id": topic["occurrences"][0]["mutation_id"],
        "topic_digest": PK.digest_bytes(topic_postimage),
        "map_digest": PK.digest_bytes(map_bytes),
    }


def apply_guarded_mutation(
    repo_root: Path | str,
    proposal: dict[str, Any],
    *,
    interrupt_after: str | None = None,
    lock_timeout: float = 10.0,
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    validated = _validate_mutation_proposal(copy.deepcopy(proposal))
    with hold_writer_lock(repo_root, timeout=lock_timeout):
        return _apply_guarded_mutation_body(
            repo_root,
            validated,
            interrupt_after=interrupt_after,
        )


def recover_guarded_mutation(repo_root: Path | str, proposal: dict[str, Any]) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    validated = _validate_mutation_proposal(copy.deepcopy(proposal))
    topic = _topic_from_proposal(validated)
    topic_path = topic_path_for_key(repo_root, topic["topic_key"])
    expected_topic = _pretty_json_bytes(validate_topic(topic))
    with hold_writer_lock(repo_root):
        _assert_committed_v1_activation(repo_root)
        _partition, _capture, existing_disposition = _find_capture(
            repo_root, validated["capture_id"]
        )
        terminal = validated["terminal_disposition"]
        if existing_disposition is not None and (
            existing_disposition["disposition"] != terminal["disposition"]
            or existing_disposition["reason_code"] != terminal["reason_code"]
            or existing_disposition["recorded_at"] != terminal["recorded_at"]
        ):
            _refuse("postimage_mismatch")
        if not topic_path.exists():
            if existing_disposition is not None:
                _refuse("postimage_mismatch")
            return _apply_guarded_mutation_body(repo_root, validated) | {
                "promoted_implies_topic_and_map": True
            }
        actual_topic = _read_regular_file_bounded(
            topic_path,
            budget_contract()["topic_bytes"],
        )
        if actual_topic != expected_topic:
            _refuse("postimage_mismatch")
        if PK.digest_bytes(expected_topic) != validated["topic_postimage_digest"]:
            _refuse("postimage_mismatch")
        map_bytes = _rebuild_topic_map_unlocked(repo_root)
        parsed_map = json.loads(map_bytes.decode("utf-8"))
        if not any(entry["topic_key"] == topic["topic_key"] for entry in parsed_map["entries"]):
            _refuse("map_mismatch")
        _write_disposition(repo_root, validated)
    return {"promoted_implies_topic_and_map": True}


def _verify_promoted_state(
    repo_root: Path | str,
    proposal: dict[str, Any],
    disposition: dict[str, Any],
) -> None:
    validated = _validate_mutation_proposal(copy.deepcopy(proposal))
    terminal = validated["terminal_disposition"]
    if any(disposition[key] != terminal[key] for key in terminal):
        _refuse("postimage_mismatch")
    topic = _topic_from_proposal(validated)
    expected = _pretty_json_bytes(validate_topic(topic))
    path = topic_path_for_key(repo_root, topic["topic_key"])
    actual_topic = _read_regular_file_bounded(
        path,
        budget_contract()["topic_bytes"],
        missing_ok=True,
    )
    if actual_topic != expected:
        _refuse("postimage_mismatch")
    if PK.digest_bytes(expected) != validated["topic_postimage_digest"]:
        _refuse("postimage_mismatch")
    map_path = _map_path(repo_root)
    expected_map = rebuild_map_bytes(knowledge_root(repo_root), repository_root=repo_root)
    actual_map = _read_regular_file_bounded(
        map_path,
        budget_contract()["map_bytes"],
        missing_ok=True,
    )
    if actual_map != expected_map:
        _refuse("map_mismatch")


def mutation_digest_vector(proposal: dict[str, Any] | None = None) -> dict[str, Any]:
    value = copy.deepcopy(proposal or _sample_mutation_proposal())
    mutation_id = _mutation_id(value)
    topic = _topic_from_proposal(value)
    topic_postimage = _pretty_json_bytes(validate_topic(topic))
    proposal_preimage = _proposal_without_derived(value | {"mutation_id": mutation_id})
    return {
        "schema_version": "mutation-proposal-vector.v1",
        "mutation_id": mutation_id,
        "topic_postimage_digest": PK.digest_bytes(topic_postimage),
        "proposal_digest": PK.digest_bytes(_canonical_json_bytes(proposal_preimage)),
    }


def load_fixed_vector(name: str) -> dict[str, Any]:
    if name != "mutation-proposal-v1":
        _refuse("strict_parse")
    fixture = SCRIPT_DIR.parent / "fixtures" / f"{name}.json"
    try:
        parsed = json.loads(
            fixture.read_text(encoding="utf-8"),
            object_pairs_hook=PK._reject_duplicate_keys,
            parse_constant=PK._reject_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        _refuse("strict_parse")
    if not isinstance(parsed, dict):
        _refuse("strict_parse")
    return parsed


def _sample_mutation_proposal() -> dict[str, Any]:
    return {
        "schema_version": "knowledge-mutation-proposal.v1",
        "capture_id": "kco-202608-" + "b" * 64,
        "topic_key": "contracts/public-contracts",
        "title": "Public contracts are the durable handoff",
        "synthesis": {
            "kind": "pattern",
            "body": "Prefer the repo-owned contract before adding a local format.",
        },
        "scopes": ["packs/core"],
        "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
        "owning_source": {
            "path": "contracts/jsonschema/knowledge-captured-observation.schema.json",
            "digest": {"kind": "sha256-bytes-v1", "sha256": "a" * 64, "byte_length": 100},
        },
        "supporting_sources": [],
        "occurrence": {
            "producer": "work-loop",
            "semantic_gate": "verified-slice",
            "source": {"path": "packs/core/.apm/skills/work-loop/SKILL.md"},
            "evidence_digest": {
                "kind": "sha256-bytes-v1",
                "sha256": "c" * 64,
                "byte_length": 42,
            },
            "scope": "packs/core",
            "observed_at": "2026-08-13T12:34:56Z",
        },
        "terminal_disposition": {
            "disposition": "promoted",
            "reason_code": "promoted_to_topic",
            "recorded_at": "2026-08-13T12:41:00Z",
        },
        "expected_topic_digest": None,
    }


def _validate_enquiry_query(query: Any) -> dict[str, Any]:
    if not isinstance(query, dict):
        _refuse("strict_parse")
    try:
        task_summary = PK._expect_text(query.get("task_summary"), 1000)
        scope = PK._expect_repo_path(query.get("scope"))
    except ValueError:
        _refuse("strict_parse")
    caller = query.get("caller", "human")
    if caller not in {"human", "skill"}:
        _refuse("strict_parse")
    risk = query.get("risk") or "consequential"
    if risk not in {"routine", "consequential"}:
        risk = "consequential"
    question = query.get("question")
    question_id = query.get("question_id")
    if caller == "skill":
        if question_id not in PK.COMPETENCY_QUESTIONS:
            _refuse("strict_parse")
        question_text = str(question_id)
    else:
        try:
            question_text = PK._expect_text(question, 1000)
        except ValueError:
            _refuse("strict_parse")
        if question_id is not None and question_id not in PK.COMPETENCY_QUESTIONS:
            _refuse("strict_parse")
    return {
        "task_summary": task_summary,
        "scope": scope,
        "caller": caller,
        "risk": risk,
        "question": question_text,
        "question_id": question_id,
    }


def _parse_committed_json(raw: bytes) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=PK._reject_duplicate_keys,
            parse_constant=PK._reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        _refuse("strict_parse")
    raise AssertionError("unreachable")


def _validate_topic_map_entry(entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        _refuse("map_mismatch")
    required = {
        "topic_key",
        "title",
        "path",
        "scopes",
        "competency_facets",
        "audience",
        "lifecycle",
        "freshness",
        "blob",
    }
    try:
        PK._expect_keys(entry, required, set())
        _topic_relative_path(entry["topic_key"])
        PK._expect_text(entry["title"], 200)
        PK._expect_repo_path(entry["path"])
        _validate_scope_list(entry["scopes"])
        if (
            not isinstance(entry["competency_facets"], list)
            or any(facet not in PK.COMPETENCY_QUESTIONS for facet in entry["competency_facets"])
        ):
            raise ValueError("invalid facets")
        if entry["audience"] != "project" or entry["lifecycle"] not in _TOPIC_LIFECYCLES:
            raise ValueError("invalid lifecycle")
        freshness_by_lifecycle = {
            "active": "fresh",
            "needs_review": "review_required",
            "retired": "retired",
        }
        if (
            not isinstance(entry["freshness"], dict)
            or entry["freshness"].get("state")
            != freshness_by_lifecycle[entry["lifecycle"]]
        ):
            raise ValueError("invalid freshness")
        blob = entry["blob"]
        PK._expect_keys(blob, {"kind", "algorithm", "object_id"}, set())
        if blob["kind"] != "git-blob-v1" or blob["algorithm"] not in _GIT_OBJECT_LENGTHS:
            raise ValueError("invalid blob")
        if (
            not isinstance(blob["object_id"], str)
            or len(blob["object_id"]) != _GIT_OBJECT_LENGTHS[blob["algorithm"]]
            or not all(character in "0123456789abcdef" for character in blob["object_id"])
        ):
            raise ValueError("invalid blob id")
    except ValueError:
        _refuse("map_mismatch")
    return entry


def _read_committed_topic_map(
    repo_root: Path | str,
    snapshot: dict[str, str],
) -> dict[str, Any]:
    raw = _committed_blob(
        repo_root,
        snapshot["commit_id"],
        TOPIC_MAP.as_posix(),
        max_bytes=budget_contract()["map_bytes"],
    )
    parsed = _parse_committed_json(raw)
    if (
        not isinstance(parsed, dict)
        or parsed.get("schema_version") != "knowledge-topic-map.v1"
        or not isinstance(parsed.get("entries"), list)
    ):
        _refuse("map_mismatch")
    entries = [_validate_topic_map_entry(entry) for entry in parsed["entries"]]
    if len(entries) > budget_contract()["map_entries"]:
        _refuse("journal_capacity")
    paths = {f"docs/knowledge/{entry['path']}" for entry in entries}
    if len(paths) != len(entries):
        _refuse("map_mismatch")
    if paths != _committed_topic_paths(repo_root, snapshot["commit_id"]):
        _refuse("map_mismatch")
    committed_blobs = _committed_blob_ids(
        repo_root, snapshot["commit_id"], "docs/knowledge/topics"
    )
    for entry in entries:
        committed_path = f"docs/knowledge/{entry['path']}"
        if committed_blobs.get(committed_path) != entry["blob"]["object_id"]:
            _refuse("map_mismatch")
    return {"schema_version": parsed["schema_version"], "entries": entries}


def _committed_v1_map_is_coherent(repo_root: Path | str) -> bool:
    try:
        snapshot = _head_snapshot(repo_root)
    except KnowledgeStoreError as error:
        _reraise_deadline(error)
        return False
    if not _committed_path_exists(repo_root, snapshot["commit_id"], TOPIC_MAP.as_posix()):
        return False
    topic_map = _read_committed_topic_map(repo_root, snapshot)
    _verify_committed_topic_headers(repo_root, snapshot, topic_map)
    return True


def _scope_matches(query_scope: str, topic_scopes: Sequence[str]) -> bool:
    if query_scope == ".":
        return True
    for topic_scope in topic_scopes:
        if topic_scope == ".":
            return True
        if query_scope == topic_scope:
            return True
        if query_scope.startswith(topic_scope + "/"):
            return True
    return False


def _entry_matches_query(
    entry: dict[str, Any],
    query: dict[str, Any],
    *,
    now: datetime,
) -> bool:
    if entry["audience"] != "project" or entry["lifecycle"] != "active":
        return False
    if entry["freshness"].get("state") != "fresh":
        return False
    review_after = entry["freshness"].get("review_after")
    if review_after is not None and _parse_time(review_after) <= now:
        return False
    if not _scope_matches(query["scope"], entry["scopes"]):
        return False
    question_id = query.get("question_id")
    return question_id is None or question_id in entry["competency_facets"]


def _committed_blobs_by_id(
    repo_root: Path | str,
    object_ids: Sequence[str],
) -> dict[str, bytes]:
    """Read many committed blobs in one `git cat-file --batch` call.

    Reading them one at a time costs three subprocesses per object -- `ls-tree`
    for the id, `cat-file -s` for the size, `show` for the bytes -- which is
    what exhausted the writer's script budget once the corpus grew.

    Any malformed record, missing object, or short read fails the whole batch:
    a partial answer here would understate the corpus and silently weaken the
    coherence check that calls this.
    """
    if not object_ids:
        return {}
    for object_id in object_ids:
        if len(object_id) not in _GIT_OBJECT_LENGTHS.values() or not all(
            character in "0123456789abcdef" for character in object_id
        ):
            _refuse("map_mismatch")
    per_object = budget_contract()["topic_bytes"]
    corpus = budget_contract()["topic_corpus_bytes"]
    try:
        with tempfile.TemporaryFile() as output:
            completed = subprocess.run(
                ["git", "cat-file", "--batch"],
                cwd=repo_root,
                input="\n".join(object_ids).encode("ascii") + b"\n",
                stdout=output,
                stderr=subprocess.DEVNULL,
                env=_git_environment(),
                timeout=_remaining_timeout(),
                check=False,
            )
            if completed.returncode != 0:
                _refuse("map_mismatch")
            if output.tell() > corpus:
                _refuse("journal_capacity")
            output.seek(0)
            raw = output.read(corpus + 1)
    except subprocess.TimeoutExpired:
        _refuse(DEADLINE_EXCEEDED, retryable=True)
    except (FileNotFoundError, OSError):
        _refuse("map_mismatch")
    blobs: dict[str, bytes] = {}
    cursor = 0
    for _ in object_ids:
        newline = raw.find(b"\n", cursor)
        if newline == -1:
            _refuse("map_mismatch")
        try:
            header = raw[cursor:newline].decode("ascii", errors="strict").split()
        except UnicodeDecodeError:
            _refuse("map_mismatch")
        if len(header) != 3 or header[1] != "blob":
            _refuse("map_mismatch")
        try:
            size = int(header[2])
        except ValueError:
            _refuse("map_mismatch")
        if size < 0 or size > per_object:
            _refuse("journal_capacity")
        start = newline + 1
        end = start + size
        if end + 1 > len(raw):
            _refuse("map_mismatch")
        blobs[header[0]] = raw[start:end]
        cursor = end + 1
    if cursor != len(raw) or len(blobs) != len(set(object_ids)):
        _refuse("map_mismatch")
    return blobs


def _validate_committed_topic(
    raw: bytes,
    entry: dict[str, Any],
    *,
    body_budget: list[int] | None = None,
    body_budget_limit: int | None = None,
) -> dict[str, Any]:
    if body_budget is not None:
        body_budget[0] += len(raw)
        limit = body_budget_limit or budget_contract()["enquiry_body_read_bytes"]
        if body_budget[0] > limit:
            _refuse("journal_capacity")
    if _git_blob_digest(raw, algorithm=entry["blob"]["algorithm"]) != entry["blob"]:
        _refuse("map_mismatch")
    topic = validate_topic(_parse_committed_json(raw))
    if topic["topic_key"] != entry["topic_key"]:
        _refuse("map_mismatch")
    return topic


def _read_committed_topic(
    repo_root: Path | str,
    snapshot: dict[str, str],
    entry: dict[str, Any],
    *,
    body_budget: list[int] | None = None,
    body_budget_limit: int | None = None,
) -> dict[str, Any]:
    raw = _committed_blob(
        repo_root,
        snapshot["commit_id"],
        f"docs/knowledge/{entry['path']}",
        max_bytes=budget_contract()["topic_bytes"],
    )
    if body_budget is not None:
        body_budget[0] += len(raw)
        limit = body_budget_limit or budget_contract()["enquiry_body_read_bytes"]
        if body_budget[0] > limit:
            _refuse("journal_capacity")
    if _git_blob_digest(raw, algorithm=entry["blob"]["algorithm"]) != entry["blob"]:
        _refuse("map_mismatch")
    topic = validate_topic(_parse_committed_json(raw))
    if topic["topic_key"] != entry["topic_key"]:
        _refuse("map_mismatch")
    return topic


def _assert_topic_matches_map_entry(
    entry: dict[str, Any], topic: dict[str, Any]
) -> None:
    expected_path = f"topics/{_topic_relative_path(topic['topic_key']).as_posix()}"
    expected_headers = {
        "topic_key": topic["topic_key"],
        "title": topic["title"],
        "path": expected_path,
        "scopes": topic["scopes"],
        "competency_facets": topic["competency_facets"],
        "audience": topic["audience"],
        "lifecycle": topic["lifecycle"],
        "freshness": topic["freshness"],
    }
    if any(entry[key] != value for key, value in expected_headers.items()):
        _refuse("map_mismatch")


def _verify_committed_topic_headers(
    repo_root: Path | str,
    snapshot: dict[str, str],
    topic_map: dict[str, Any],
) -> None:
    corpus_budget = [0]
    entries = topic_map["entries"]
    blobs = _committed_blobs_by_id(
        repo_root, [entry["blob"]["object_id"] for entry in entries]
    )
    for entry in entries:
        raw = blobs.get(entry["blob"]["object_id"])
        if raw is None:
            _refuse("map_mismatch")
        topic = _validate_committed_topic(
            raw,
            entry,
            body_budget=corpus_budget,
            body_budget_limit=budget_contract()["topic_corpus_bytes"],
        )
        _assert_topic_matches_map_entry(entry, topic)


def _confined_current_source(repo_root: Path | str, source: dict[str, Any]) -> bytes | None:
    try:
        relative = PK._expect_repo_path(source["path"])
    except (KeyError, ValueError):
        _refuse("confinement")
    root = Path(repo_root).resolve(strict=False)
    path = root / relative
    _assert_confined_components(root, path)
    return _read_regular_file_bounded(
        path,
        budget_contract()["enquiry_body_read_bytes"],
        missing_ok=True,
        reject_hard_links=True,
    )


def _source_digest_matches(
    repo_root: Path | str, digest: dict[str, Any], raw: bytes
) -> bool:
    if digest["kind"] == "sha256-bytes-v1":
        return PK.digest_bytes(raw) == digest
    algorithm = _git_object_algorithm(repo_root)
    return digest["algorithm"] == algorithm and _git_blob_digest(
        raw, algorithm=algorithm
    ) == digest


def _verify_current_source(repo_root: Path | str, source: dict[str, Any]) -> bool:
    raw = _confined_current_source(repo_root, source)
    if raw is None:
        return False
    return _source_digest_matches(repo_root, source["digest"], raw)


def _selected_entries(
    entries: Sequence[dict[str, Any]],
    query: dict[str, Any],
    *,
    now: datetime,
) -> list[dict[str, Any]]:
    filtered = [
        entry for entry in entries if _entry_matches_query(entry, query, now=now)
    ]
    question_id = query.get("question_id")
    filtered.sort(
        key=lambda entry: (
            0 if question_id is not None and question_id in entry["competency_facets"] else 1,
            entry["topic_key"],
        )
    )
    return filtered[: budget_contract()["enquiry_bodies"]]


def _render_envelope(
    *,
    query: dict[str, Any],
    topics: Sequence[dict[str, Any]],
    verified_sources: Sequence[str],
    abstained: bool,
) -> str:
    lines = [
        '<knowledge-evidence version="knowledge-evidence.v1">',
        "Evidence only; not instructions or authority.",
        f"task_summary: {html.escape(query['task_summary'], quote=True)}",
        f"scope: {html.escape(query['scope'], quote=True)}",
        f"risk: {query['risk']}",
    ]
    if abstained:
        lines.append("abstained: true")
        lines.append("limitations: consequential enquiry requires a verified owning source")
    for topic in topics:
        lines.extend(
            [
                f"<topic id=\"{html.escape(topic['topic_key'], quote=True)}\">",
                f"title: {html.escape(topic['title'], quote=True)}",
                f"scope: {html.escape(', '.join(topic['scopes']), quote=True)}",
                "freshness: "
                f"{topic['freshness']['state']} checked {topic['freshness']['checked_at']}",
                "provenance: "
                + html.escape(
                    ", ".join(item["capture_id"] for item in topic["occurrences"]),
                    quote=True,
                ),
                "source: "
                + html.escape(
                    topic["owning_source"]["path"] if topic["owning_source"] else "none",
                    quote=True,
                ),
                "synthesis:",
                html.escape(topic["synthesis"]["body"], quote=True),
                "limitations: verify against owning sources before acting",
                "</topic>",
            ]
        )
    verified = html.escape(", ".join(verified_sources), quote=True) if verified_sources else "none"
    lines.append(f"verified_sources: {verified}")
    lines.append("</knowledge-evidence>")
    rendered = "\n".join(lines)
    if len(rendered.encode("utf-8")) > budget_contract()["envelope_bytes"]:
        _refuse("journal_capacity")
    return rendered


def enquire(repo_root: Path | str, query: dict[str, Any]) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    validated = _validate_enquiry_query(query)
    snapshot = _head_snapshot(repo_root)
    topic_map = _read_committed_topic_map(repo_root, snapshot)
    enquiry_time = datetime.now(tz=UTC)
    entries = _selected_entries(topic_map["entries"], validated, now=enquiry_time)
    topics: list[dict[str, Any]] = []
    verified_sources: list[str] = []
    body_budget = [0]
    for entry in entries:
        _remaining_timeout()
        topic = _read_committed_topic(repo_root, snapshot, entry, body_budget=body_budget)
        _assert_topic_matches_map_entry(entry, topic)
        if not _entry_matches_query(topic, validated, now=enquiry_time):
            _refuse("map_mismatch")
        owning_source = topic["owning_source"]
        if validated["risk"] == "consequential":
            if owning_source is None or not _verify_current_source(repo_root, owning_source):
                continue
            verified_sources.append(owning_source["path"])
        elif owning_source is not None and _verify_current_source(repo_root, owning_source):
            verified_sources.append(owning_source["path"])
        topics.append(topic)
    abstained = bool(entries) and not topics and validated["risk"] == "consequential"
    rendered = _render_envelope(
        query=validated,
        topics=topics,
        verified_sources=verified_sources,
        abstained=abstained,
    )
    receipt = {
        "receipt_version": "knowledge-enquiry-receipt.v1",
        "question": validated["question"],
        "question_id": validated["question_id"],
        "risk": validated["risk"],
        "selected_topics": [topic["topic_key"] for topic in topics],
        "verified_sources": sorted(set(verified_sources)),
        "budget": {
            "selected_topic_limit": budget_contract()["enquiry_bodies"],
            "selected_topic_body_bytes": body_budget[0],
            "envelope_bytes": len(rendered.encode("utf-8")),
        },
        "corpus": snapshot,
        "commit_id": snapshot["commit_id"],
        "tree_id": snapshot["tree_id"],
        "abstained": abstained,
        "caller": validated["caller"],
        "opened_journals": 0,
        "mutation_path": None,
    }
    return {"receipt": receipt, "rendered": rendered}


def enquire_head(repo_root: Path | str) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    snapshot = _head_snapshot(repo_root)
    return _read_committed_topic_map(repo_root, snapshot)


def read_worktree_topic(repo_root: Path | str, topic_key: str) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    path = topic_path_for_key(repo_root, topic_key)
    if not path.exists() or not path.is_file() or _is_reparse_or_symlink(path):
        _refuse("confinement")
    if path.stat().st_size > budget_contract()["topic_bytes"]:
        _refuse("journal_capacity")
    return _read_topic(path)


def read_confined_source(repo_root: Path | str, relative_path: str) -> bytes:
    repo_root = resolve_worktree_root(repo_root)
    try:
        normalized = PK._expect_repo_path(relative_path)
    except ValueError:
        _refuse("confinement")
    raw = _confined_current_source(repo_root, {"path": normalized})
    if raw is None:
        _refuse("confinement")
    return raw


def read_committed_topic(repo_root: Path | str, topic_key: str) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    snapshot = _head_snapshot(repo_root)
    topic_map = _read_committed_topic_map(repo_root, snapshot)
    entry = next(
        (item for item in topic_map["entries"] if item["topic_key"] == topic_key),
        None,
    )
    if entry is None:
        _refuse("map_mismatch")
    topic = _read_committed_topic(repo_root, snapshot, entry, body_budget=[0])
    _assert_topic_matches_map_entry(entry, topic)
    return topic


def read_freshness_source(repo_root: Path | str, topic_key: str) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    topic = read_committed_topic(repo_root, topic_key)
    source = topic["owning_source"]
    if source is None:
        return {"topic_key": topic_key, "path": None, "verified": False}
    raw = _confined_current_source(repo_root, source)
    if raw is None:
        return {"topic_key": topic_key, "path": source["path"], "verified": False}
    return {
        "topic_key": topic_key,
        "path": source["path"],
        "verified": _source_digest_matches(repo_root, source["digest"], raw),
    }


def merge_topic_trees(
    base_dir: Path | str,
    left: Sequence[dict[str, Any]],
    right: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    target = Path(base_dir) / "merged"
    seen: set[str] = set()
    for proposal in [*left, *right]:
        key = proposal["topic_key"]
        if key in seen:
            _refuse("postimage_mismatch")
        seen.add(key)
        apply_guarded_mutation(target, proposal)
    map_bytes = rebuild_topic_map(target)
    return {"map_bytes": map_bytes}


def _legacy_path(repo_root: Path | str) -> Path:
    return Path(repo_root) / LEGACY_PATTERNS


def _stage_root(repo_root: Path | str) -> Path:
    return Path(repo_root) / MIGRATION_STAGE


def _stage_knowledge_root(repo_root: Path | str) -> Path:
    return _stage_root(repo_root) / "docs" / "knowledge"


def _safe_slug(value: str) -> str:
    lowered = value.lower()
    chars = [character if character.isalnum() else "-" for character in lowered]
    collapsed = "-".join(part for part in "".join(chars).split("-") if part)
    return collapsed[:80] or "legacy-topic"


def _legacy_line_diagnostic(reason_code: str, line: int) -> dict[str, Any]:
    return _diagnostic(
        reason_code,
        path=LEGACY_PATTERNS.as_posix(),
        line=line,
    )


def _strict_parse_legacy_lines(raw: bytes) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            parsed = PK._parse_strict_json(line)
        except ValueError:
            _refuse_with_diagnostic(_legacy_line_diagnostic("strict_parse", line_number))
        if not isinstance(parsed, dict):
            _refuse_with_diagnostic(_legacy_line_diagnostic("strict_parse", line_number))
        rows.append((line_number, parsed))
    return rows


def _validate_legacy_row(row: dict[str, Any], line_number: int) -> dict[str, Any]:
    try:
        PK._expect_keys(row, {"id", "kind", "scope", "title", "body", "source"}, set())
        PK._expect_slug(row["kind"])
        if row["kind"] not in {"pattern", "gotcha", "antipattern"}:
            raise ValueError("invalid legacy kind")
        row["scope"] = PK._expect_repo_path(row["scope"])
        PK.assert_persistable_paths(row["scope"])
        PK._expect_text(row["id"], 80)
        PK._expect_text(row["title"], 200)
        if not isinstance(row["body"], str):
            raise ValueError("invalid body")
        PK._assert_safe_unicode(row["body"])
        PK._expect_text(row["source"], 500)
        PK.assert_persistable_text(row["title"], row["body"], row["source"])
    except PK.PrivacyRefusal:
        _refuse_with_diagnostic(_legacy_line_diagnostic("privacy", line_number))
    except ValueError:
        _refuse_with_diagnostic(_legacy_line_diagnostic("strict_parse", line_number))
    return row


def _legacy_disposition(row: dict[str, Any], ambiguous: bool) -> str:
    if not row["body"].strip():
        return "refused"
    if ambiguous or row["scope"] in {"*", "**/*", "**/*.py"}:
        return "needs_review_import"
    return "active_import"


def _legacy_capture_id(legacy_id: str) -> str:
    digest = hashlib.sha256(f"legacy-knowledge-v1:{legacy_id}".encode()).hexdigest()
    return f"kco-197001-{digest}"


def _legacy_mutation_id(legacy_id: str, topic_key: str) -> str:
    return hashlib.sha256(
        _canonical_json_bytes(
            {
                "contract": "legacy-import-mutation-v1",
                "legacy_identity": legacy_id,
                "topic_key": topic_key,
            }
        )
    ).hexdigest()


def _topic_for_legacy_row(
    row: dict[str, Any],
    disposition: str,
    *,
    topic_key: str | None = None,
) -> dict[str, Any]:
    title = row["title"]
    resolved_topic_key = topic_key or _safe_slug(title)
    lifecycle = "active" if disposition == "active_import" else "needs_review"
    freshness_state = "fresh" if lifecycle == "active" else "review_required"
    return {
        "schema_version": "knowledge-topic.v1",
        "topic_key": resolved_topic_key,
        "title": title,
        "synthesis": {"kind": row["kind"], "body": row["body"]},
        "scopes": [row["scope"]],
        "competency_facets": ["CQ-ORIENT"],
        "audience": "project",
        "lifecycle": lifecycle,
        "freshness": {"state": freshness_state, "checked_at": "1970-01-01T00:00:00Z"},
        "owning_source": None,
        "supporting_sources": [],
        "occurrences": [
            {
                "capture_id": _legacy_capture_id(row["id"]),
                "mutation_id": _legacy_mutation_id(row["id"], resolved_topic_key),
                "producer": "legacy-import",
                "semantic_gate": "legacy-import",
                "source": {"path": LEGACY_PATTERNS.as_posix()},
                "scope": row["scope"],
                "observed_at": "1970-01-01T00:00:00Z",
                "reviewed_disposition": disposition,
                "legacy_identity": row["id"],
                "legacy_source": row["source"],
            }
        ],
    }


def _merge_import_topic(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(existing)
    merged["occurrences"].extend(incoming["occurrences"])
    merged["scopes"] = sorted(set(merged["scopes"]) | set(incoming["scopes"]))
    merged["competency_facets"] = sorted(
        set(merged["competency_facets"]) | set(incoming["competency_facets"])
    )
    if incoming["lifecycle"] == "needs_review":
        merged["lifecycle"] = "needs_review"
        merged["freshness"]["state"] = "review_required"
    return merged


def _clear_staged_migration_unlocked(repo_root: Path | str) -> None:
    stage = _stage_root(repo_root)
    if stage.exists():
        shutil.rmtree(stage)


def clear_staged_migration(repo_root: Path | str) -> None:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        _clear_staged_migration_unlocked(repo_root)


def staged_migration_files(repo_root: Path | str) -> list[Path]:
    stage = _stage_root(repo_root)
    if not stage.exists():
        return []
    return sorted(path for path in stage.rglob("*") if path.is_file())


def staged_topic_files(repo_root: Path | str) -> list[Path]:
    topics = _stage_knowledge_root(repo_root) / "topics"
    return sorted(topics.rglob("*.json")) if topics.exists() else []


def staged_map_bytes(repo_root: Path | str) -> bytes:
    raw = _read_regular_file_bounded(
        _stage_knowledge_root(repo_root) / "topics.index.json",
        budget_contract()["map_bytes"],
    )
    assert raw is not None
    return raw


def _write_staged_topic(stage_knowledge: Path, topic: dict[str, Any]) -> None:
    path = stage_knowledge / "topics" / _topic_relative_path(topic["topic_key"])
    path.parent.mkdir(parents=True, exist_ok=True)
    postimage = _pretty_json_bytes(validate_topic(topic))
    if len(postimage) > budget_contract()["topic_bytes"]:
        _refuse("journal_capacity")
    path.write_bytes(postimage)


def _stage_map_bytes(repo_root: Path | str, stage_knowledge: Path) -> bytes:
    return rebuild_map_bytes(stage_knowledge, repository_root=repo_root)


def stage_legacy_migration(
    repo_root: Path | str,
    *,
    inject: str | None = None,
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        return _stage_legacy_migration_locked(repo_root, inject=inject)


def _stage_legacy_migration_locked(
    repo_root: Path | str,
    *,
    inject: str | None = None,
) -> dict[str, Any]:
    if _committed_v1_map_is_coherent(repo_root) or _has_v1_observations(repo_root):
        _refuse("staged_dual_writer")
    legacy = _legacy_path(repo_root)
    source = _read_regular_file_bounded(
        legacy,
        budget_contract()["retained_journal_bytes"],
    )
    assert source is not None
    rows = [
        (line, _validate_legacy_row(row, line))
        for line, row in _strict_parse_legacy_lines(source)
    ]
    title_counts: dict[tuple[str, str], int] = {}
    slug_titles: dict[str, set[str]] = {}
    for _line, row in rows:
        key = (row["scope"], row["title"])
        title_counts[key] = title_counts.get(key, 0) + 1
        slug_titles.setdefault(_safe_slug(row["title"]), set()).add(row["title"])

    imports: dict[str, dict[str, Any]] = {}
    counts = {"input_rows": len(rows), "active_import": 0, "needs_review_import": 0, "refused": 0}
    diagnostics: list[dict[str, Any]] = []
    for line, row in rows:
        base_topic_key = _safe_slug(row["title"])
        slug_collision = len(slug_titles[base_topic_key]) > 1
        ambiguous = title_counts[(row["scope"], row["title"])] > 1 or slug_collision
        disposition = _legacy_disposition(row, ambiguous)
        counts[disposition] += 1
        if inject == "privacy" and line == 1:
            _refuse_with_diagnostic(_legacy_line_diagnostic("privacy", line))
        if disposition == "refused":
            continue
        if ambiguous and disposition == "needs_review_import":
            diagnostics.append(
                _diagnostic(
                    "ambiguous_grouping",
                    path=LEGACY_PATTERNS.as_posix(),
                    line=line,
                    recovery_action="review_topic_grouping",
                )
            )
        topic_key = base_topic_key
        if slug_collision:
            title_digest = hashlib.sha256(row["title"].encode("utf-8")).hexdigest()[:12]
            topic_key = f"{base_topic_key[:67]}-{title_digest}"
        topic = _topic_for_legacy_row(row, disposition, topic_key=topic_key)
        existing = imports.get(topic["topic_key"])
        imports[topic["topic_key"]] = (
            _merge_import_topic(existing, topic) if existing is not None else topic
        )

    if sum(counts[item] for item in ("active_import", "needs_review_import", "refused")) != counts[
        "input_rows"
    ]:
        _refuse("postimage_mismatch")
    if inject == "accounting":
        _refuse("postimage_mismatch")

    _clear_staged_migration_unlocked(repo_root)
    stage_knowledge = _stage_knowledge_root(repo_root)
    try:
        for topic in sorted(imports.values(), key=lambda item: item["topic_key"]):
            _write_staged_topic(stage_knowledge, topic)
        if inject == "interrupted_staged_write":
            _refuse("postimage_mismatch")
        map_bytes = _stage_map_bytes(repo_root, stage_knowledge)
        (stage_knowledge / "topics.index.json").write_bytes(map_bytes)
    except Exception:
        _clear_staged_migration_unlocked(repo_root)
        raise
    return {"counts": counts, "diagnostics": diagnostics, "map_digest": PK.digest_bytes(map_bytes)}


def _worktree_topic_map_path(repo_root: Path | str) -> Path:
    return Path(repo_root) / TOPIC_MAP


def _has_worktree_v1_map(repo_root: Path | str) -> bool:
    return _worktree_topic_map_path(repo_root).exists()


def _has_v1_observations(repo_root: Path | str) -> bool:
    observations = Path(repo_root) / OBSERVATIONS_ROOT
    return observations.exists() and any(observations.glob("*/*.jsonl"))


def _assert_no_staged_activation(repo_root: Path | str) -> None:
    if staged_migration_files(repo_root):
        _refuse("staged_dual_writer")


def _coherent_worktree_map(repo_root: Path | str) -> bool:
    map_path = _worktree_topic_map_path(repo_root)
    if not map_path.exists():
        return False
    expected = rebuild_map_bytes(Path(repo_root) / "docs" / "knowledge")
    actual = _read_regular_file_bounded(map_path, budget_contract()["map_bytes"])
    assert actual is not None
    if actual != expected:
        _refuse("map_mismatch")
    return True


def _legacy_source_present(repo_root: Path | str) -> bool:
    return _legacy_path(repo_root).exists()


def _assert_v1_writer_allowed(repo_root: Path | str) -> None:
    _assert_no_staged_activation(repo_root)
    committed_map = _committed_v1_map_is_coherent(repo_root)
    if not committed_map:
        if _legacy_source_present(repo_root) or _has_v1_observations(repo_root):
            _refuse("staged_dual_writer")
        _refuse("map_mismatch")
    if not _has_worktree_v1_map(repo_root):
        _refuse("map_mismatch")
    _coherent_worktree_map(repo_root)


def _assert_committed_v1_activation(repo_root: Path | str) -> None:
    _assert_no_staged_activation(repo_root)
    if not _committed_v1_map_is_coherent(repo_root):
        if _legacy_source_present(repo_root) or _has_v1_observations(repo_root):
            _refuse("staged_dual_writer")
        _refuse("map_mismatch")
    map_bytes = _read_regular_file_bounded(
        _worktree_topic_map_path(repo_root),
        budget_contract()["map_bytes"],
    )
    assert map_bytes is not None


def current_tree_snapshot(repo_root: Path | str, *, staged: bool = False) -> dict[str, Any]:
    root = _stage_knowledge_root(repo_root) if staged else Path(repo_root) / "docs" / "knowledge"
    files: dict[str, Any] = {}
    map_raw = _read_regular_file_bounded(
        root / "topics.index.json",
        budget_contract()["map_bytes"],
        missing_ok=True,
    )
    if map_raw is not None:
        files["topics.index.json"] = PK.digest_bytes(map_raw)
    for path, _topic, raw in _bounded_topic_records(root):
        files[path.relative_to(root).as_posix()] = PK.digest_bytes(raw)
    return {"snapshot_version": "knowledge-current-tree-snapshot.v1", "files": files}


def committed_knowledge_snapshot(repo_root: Path | str) -> dict[str, Any]:
    snapshot = _head_snapshot(repo_root)
    topic_map = _read_committed_topic_map(repo_root, snapshot)
    _verify_committed_topic_headers(repo_root, snapshot, topic_map)
    files: dict[str, Any] = {
        "topics.index.json": PK.digest_bytes(
            _committed_blob(
                repo_root,
                snapshot["commit_id"],
                TOPIC_MAP.as_posix(),
                max_bytes=budget_contract()["map_bytes"],
            )
        )
    }
    for entry in topic_map["entries"]:
        relative = entry["path"]
        files[relative] = PK.digest_bytes(
            _committed_blob(
                repo_root,
                snapshot["commit_id"],
                f"docs/knowledge/{relative}",
                max_bytes=budget_contract()["topic_bytes"],
            )
        )
    return {
        "snapshot_version": "knowledge-current-tree-snapshot.v1",
        "files": files,
    }


def activate_staged_migration(
    repo_root: Path | str,
    *,
    committed_snapshot: dict[str, Any],
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        stage_knowledge = _stage_knowledge_root(repo_root)
        staged_snapshot = current_tree_snapshot(repo_root, staged=True)
        actual_committed = committed_knowledge_snapshot(repo_root)
        actual_worktree = current_tree_snapshot(repo_root)
        if (
            committed_snapshot != actual_committed
            or staged_snapshot != actual_committed
            or actual_worktree != actual_committed
        ):
            _refuse("map_mismatch")
        if not (stage_knowledge / "topics.index.json").exists():
            _refuse("map_mismatch")
        _clear_staged_migration_unlocked(repo_root)
        _coherent_worktree_map(repo_root)
    return {"state": "activated", "snapshot": actual_committed}


def reverse_migration(repo_root: Path | str) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        if _has_v1_observations(repo_root):
            _refuse("forward_recovery_required")
        if _committed_v1_map_is_coherent(repo_root):
            _refuse("forward_recovery_required")
        topics = Path(repo_root) / TOPICS_ROOT
        map_path = _worktree_topic_map_path(repo_root)
        if topics.exists():
            shutil.rmtree(topics)
        with contextlib.suppress(FileNotFoundError):
            map_path.unlink()
        _clear_staged_migration_unlocked(repo_root)
    return {"state": "legacy_restored"}


def legacy_append(repo_root: Path | str, row: dict[str, Any]) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    with hold_writer_lock(repo_root):
        _assert_no_staged_activation(repo_root)
        if (
            _committed_v1_map_is_coherent(repo_root)
            or _has_worktree_v1_map(repo_root)
            or _has_v1_observations(repo_root)
        ):
            _refuse("staged_dual_writer")
        _validate_legacy_row(copy.deepcopy(row), 1)
        path = _legacy_path(repo_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = _read_regular_file_bounded(
            path,
            budget_contract()["retained_journal_bytes"],
            missing_ok=True,
        ) or b""
        row_bytes = json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")
        postimage = existing + row_bytes + b"\n"
        _replace_atomic(path, postimage)
    return {"writer": "legacy", "path": LEGACY_PATTERNS.as_posix()}


def capture_observation(
    repo_root: Path | str,
    request: dict[str, Any],
    *,
    writer_time: str | None = None,
    budgets: dict[str, int] | None = None,
    interrupt_after: str | None = None,
    lock_timeout: float = 10.0,
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    writer_time = writer_time or _format_time(datetime.now(tz=UTC))
    validated = _check_pre_admission(request)
    event = _captured_event(validated, writer_time=writer_time)
    partition_path = _journal_path(repo_root, event["partition"])
    limits = budgets or budget_contract()
    with hold_writer_lock(repo_root, timeout=lock_timeout):
        existing = _read_events(partition_path, event["partition"])
        replay = _existing_replay(existing, event)
        if replay is not None:
            return replay
        _assert_v1_writer_allowed(repo_root)
        _check_time_window(validated, writer_time)
        postimage = b"".join(_event_line(item) for item in existing) + _event_line(event)
        _check_budgets(repo_root, partition_path, existing, postimage, event, limits)
        _replace_atomic(partition_path, postimage, interrupt_after=interrupt_after)
    return _receipt(event)


def seed_previously_admitted_capture(
    repo_root: Path | str,
    request: dict[str, Any],
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    event = _captured_event(request, writer_time=request["observed_at"])
    with hold_writer_lock(repo_root):
        path = _journal_path(repo_root, event["partition"])
        existing = _read_events(path, event["partition"])
        _replace_atomic(path, b"".join(_event_line(item) for item in [*existing, event]))
    return _receipt(event)


def seed_previously_admitted_capture_with_id(
    repo_root: Path | str,
    request: dict[str, Any],
    capture_id: str,
) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    event = _captured_event(request, writer_time=request["observed_at"], capture_id=capture_id)
    with hold_writer_lock(repo_root):
        path = _journal_path(repo_root, event["partition"])
        existing = _read_events(path, event["partition"])
        _replace_atomic(path, b"".join(_event_line(item) for item in [*existing, event]))
    return _receipt(event)


def seed_corrupted_capture(repo_root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    event = _captured_event(request, writer_time=request["observed_at"])
    event["request"] = copy.deepcopy(event["request"])
    event["request"]["lesson"] = "tampered after identity derivation"
    with hold_writer_lock(repo_root):
        path = _journal_path(repo_root, event["partition"])
        _replace_atomic(path, _event_line(event))
    return _receipt(event)


def select_pending(
    repo_root: Path | str,
    partitions: Sequence[str],
    *,
    limit: int | None = None,
    scope: str | None = None,
    allowed_capture_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    if len(partitions) > budget_contract()["pending_page_partitions"]:
        _refuse("journal_capacity")
    effective_limit = limit or budget_contract()["pending_page_events"]
    if effective_limit < 1 or effective_limit > budget_contract()["pending_page_events"]:
        _refuse("strict_parse")
    loaded, complete = _load_pending_partition_window(repo_root, sorted(partitions))
    if not complete:
        _refuse("journal_capacity")
    return _pending_from_loaded_partitions(
        loaded,
        limit=effective_limit,
        scope=scope,
        allowed_capture_ids=allowed_capture_ids,
    )


def _load_pending_partition_window(
    repo_root: Path | str,
    partitions: Sequence[str],
) -> tuple[list[tuple[str, list[dict[str, Any]], bytes]], bool]:
    loaded: list[tuple[str, list[dict[str, Any]], bytes]] = []
    consumed_bytes = 0
    consumed_events = 0
    for partition in partitions:
        path = _journal_path(repo_root, partition)
        try:
            raw = _read_regular_file_bounded(
                path,
                budget_contract()["pending_page_bytes"] - consumed_bytes,
                missing_ok=True,
            )
        except KnowledgeStoreError as error:
            if error.diagnostic["reason_code"] == "journal_capacity" and loaded:
                return loaded, False
            raise
        raw = raw or b""
        events = list(_validated_event_lines(iter(raw.splitlines()), partition))
        next_bytes = consumed_bytes + len(raw)
        next_events = consumed_events + len(events)
        if next_events > budget_contract()["pending_page_events"]:
            _refuse("journal_capacity")
        if next_bytes > budget_contract()["pending_page_bytes"]:
            if loaded:
                return loaded, False
            _refuse("journal_capacity")
        loaded.append((partition, events, raw))
        consumed_bytes = next_bytes
        consumed_events = next_events
    return loaded, True


def _pending_from_loaded_partitions(
    loaded: Sequence[tuple[str, Sequence[dict[str, Any]], bytes]],
    *,
    limit: int,
    scope: str | None,
    allowed_capture_ids: set[str] | None,
) -> list[dict[str, Any]]:
    ranked: list[tuple[tuple[str, str, str], dict[str, Any]]] = []
    for _partition, events, _raw in loaded:
        terminal = _terminal_capture_ids(events)
        for event in events:
            if event["event_type"] != _CAPTURED or event["capture_id"] in terminal:
                continue
            key = (event["partition"], event["capture_id"], event["captured_at"])
            if allowed_capture_ids is not None and event["capture_id"] not in allowed_capture_ids:
                continue
            if scope is not None and not _scope_matches(
                scope, event["request"]["project_scope"]["paths"]
            ):
                continue
            ranked.append((key, event))
    ranked.sort(key=lambda item: item[0])
    if len(ranked) > limit:
        _refuse("journal_capacity")
    return [event for _key, event in ranked]


def _validate_pending_request(repo_root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        _refuse("strict_parse")
    mode = request.get("selection_mode")
    if mode == "direct-maintainer-pending":
        try:
            scope = PK._expect_repo_path(request["scope"])
        except (KeyError, ValueError):
            _refuse("strict_parse")
        all_partitions = _observation_partitions(repo_root)
        cursor = request.get("cursor")
        offset = 0
        if cursor is not None:
            parsed = _cursor_decode(cursor)
            offset = parsed.get("partition_offset")
            if not isinstance(offset, int) or offset < 0 or offset > len(all_partitions):
                _refuse("cursor_stale")
        selected = all_partitions[
            offset : offset + budget_contract()["pending_page_partitions"]
        ]
        return {
            "selection_mode": mode,
            "scope": scope,
            "partitions": selected,
            "all_partitions": all_partitions,
            "partition_offset": offset,
            "receipt_selectors": [],
            "page_event_limit": request.get("page_event_limit"),
            "cursor": cursor,
        }
    if mode == "workflow-receipts":
        receipts = request.get("receipts")
        if (
            not isinstance(receipts, list)
            or not receipts
            or request.get("cursor") is not None
            or len(receipts) > budget_contract()["pending_page_events"]
            or any(
                not isinstance(item, dict)
                or set(item) != {"capture_id", "partition"}
                or not _is_capture_id(item["capture_id"])
                or not isinstance(item["partition"], str)
                for item in receipts
            )
        ):
            _refuse("strict_parse")
        selectors = sorted(
            (
                {"capture_id": item["capture_id"], "partition": item["partition"]}
                for item in receipts
            ),
            key=lambda item: (item["partition"], item["capture_id"]),
        )
        if len({item["capture_id"] for item in selectors}) != len(selectors):
            _refuse("strict_parse")
        partitions = sorted({item["partition"] for item in selectors})
        if len(partitions) > budget_contract()["pending_page_partitions"]:
            _refuse("journal_capacity")
        return {
            "selection_mode": mode,
            "scope": None,
            "partitions": partitions,
            "all_partitions": partitions,
            "partition_offset": 0,
            "receipt_selectors": selectors,
            "page_event_limit": request.get("page_event_limit"),
            "cursor": request.get("cursor"),
        }
    _refuse("strict_parse")
    raise AssertionError("unreachable")


def pending_page(repo_root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    validated = _validate_pending_request(repo_root, request)
    limit = validated["page_event_limit"] or budget_contract()["pending_page_events"]
    if not isinstance(limit, int) or limit < 1 or limit > budget_contract()["pending_page_events"]:
        _refuse("strict_parse")
    cursor = validated.get("cursor")
    if cursor is not None:
        parsed = _cursor_decode(cursor)
        expected = {
            "version": "pending-cursor.v1",
            "selection_mode": validated["selection_mode"],
            "scope": validated["scope"],
            "receipt_selectors": validated["receipt_selectors"],
            "partition_names": validated["all_partitions"],
            "partition_offset": validated["partition_offset"],
        }
        for key, value in expected.items():
            if parsed.get(key) != value:
                _refuse("cursor_stale")
        bound_partitions = parsed.get("bound_partitions")
        if (
            not isinstance(bound_partitions, list)
            or len(bound_partitions) > budget_contract()["pending_page_partitions"]
            or any(
                not isinstance(item, dict)
                or set(item) != {"partition", "digest"}
                for item in bound_partitions
            )
        ):
            _refuse("cursor_stale")
        bound_names = [item["partition"] for item in bound_partitions]
        bound_end = validated["partition_offset"]
        bound_start = bound_end - len(bound_names)
        if (
            (bound_end > 0 and not bound_names)
            or bound_start < 0
            or validated["all_partitions"][bound_start:bound_end] != bound_names
        ):
            _refuse("cursor_stale")
        current_bound = _partition_digests(
            repo_root, bound_names
        )
        if current_bound != bound_partitions:
            _refuse("cursor_stale")
        if set(parsed) != {
            "version",
            "selection_mode",
            "scope",
            "receipt_selectors",
            "partition_names",
            "partition_offset",
            "bound_partitions",
        }:
            _refuse("cursor_stale")

    allowed: set[str] | None = None
    scope: str | None = validated["scope"]
    if validated["selection_mode"] == "workflow-receipts":
        allowed = {item["capture_id"] for item in validated["receipt_selectors"]}
        scope = None
    loaded, complete = _load_pending_partition_window(repo_root, validated["partitions"])
    processed_partitions = [partition for partition, _events, _raw in loaded]
    if validated["selection_mode"] == "workflow-receipts" and not complete:
        _refuse("journal_capacity")
    if validated["selection_mode"] == "workflow-receipts":
        found = {
            event["capture_id"]
            for _partition, events, _raw in loaded
            for event in events
            if event["event_type"] == _CAPTURED and event["capture_id"] in allowed
        }
        if found != allowed:
            _refuse("replay_required")
    pending = _pending_from_loaded_partitions(
        loaded,
        limit=limit,
        scope=scope,
        allowed_capture_ids=allowed,
    )
    partition_state = [
        {"partition": partition, "digest": PK.digest_bytes(raw)}
        for partition, _events, raw in loaded
    ]
    next_cursor = None
    cursor_offset = validated["partition_offset"] + len(processed_partitions)
    if (
        validated["selection_mode"] == "direct-maintainer-pending"
        and cursor_offset < len(validated["all_partitions"])
    ):
        next_cursor = _cursor_encode(
            {
                "version": "pending-cursor.v1",
                "selection_mode": validated["selection_mode"],
                "scope": validated["scope"],
                "receipt_selectors": validated["receipt_selectors"],
                "partition_names": validated["all_partitions"],
                "partition_offset": cursor_offset,
                "bound_partitions": partition_state,
            }
        )
    return {
        "selection_mode": validated["selection_mode"],
        "scope": validated["scope"],
        "partitions": processed_partitions,
        "pending": pending,
        "cursor": next_cursor,
    }


def distill_pending(repo_root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    if request.get("selection_mode") not in {
        "direct-maintainer-pending",
        "workflow-receipts",
    }:
        _refuse("strict_parse")
    page = pending_page(repo_root, request)
    pending_count = len(page["pending"])
    return {
        "receipt_version": "knowledge-distill-drain-receipt.v1",
        "selection_mode": page["selection_mode"],
        "scope": page["scope"],
        "partitions": page["partitions"],
        "pending": page["pending"],
        "cursor": page["cursor"],
        "counts": {"pending": pending_count, "processed": 0, "unresolved": pending_count},
        "diagnostics": [],
    }


def distill_capture(repo_root: Path | str, capture_id: str) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    root = knowledge_root(repo_root) / "observations"
    for path in sorted(root.glob("*/*.jsonl")) if root.exists() else []:
        partition = path.relative_to(knowledge_root(repo_root)).as_posix()
        for event in _read_events(path, partition):
            if event["event_type"] == _CAPTURED and event["capture_id"] == capture_id:
                return _receipt(event)
    _refuse("replay_required")
    raise AssertionError("unreachable")


def _validate_distillation_proposal(proposal: Any) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        _refuse("strict_parse")
    if proposal.get("semantic_status") in {
        "ambiguous_split",
        "contradiction",
        "ambiguous_routing",
        "privacy_uncertain",
    }:
        _refuse("strict_parse")
    required = {
        "schema_version",
        "capture_id",
        "disposition",
        "reason_code",
        "recorded_at",
        "candidate_topic_keys",
        "named_sources",
        "mutation",
    }
    optional = {"routing_suggestion"}
    try:
        PK._expect_keys(proposal, required, optional | {"semantic_status"})
        if proposal["schema_version"] != "knowledge-distillation-proposal.v1":
            raise ValueError("invalid distillation proposal")
        if not _is_capture_id(proposal["capture_id"]):
            raise ValueError("invalid capture id")
        if proposal["disposition"] not in _TERMINAL_DISPOSITIONS:
            raise ValueError("invalid disposition")
        if not _is_reason_code(proposal["reason_code"]):
            raise ValueError("invalid reason")
        _assert_persistable_metadata(proposal["reason_code"])
        _parse_time(proposal["recorded_at"])
        candidates = proposal["candidate_topic_keys"]
        if not isinstance(candidates, list) or len(candidates) > _MAX_DISTILL_CANDIDATES:
            raise ValueError("invalid candidates")
        for key in candidates:
            _topic_relative_path(key)
        sources = proposal["named_sources"]
        if not isinstance(sources, list) or len(sources) > _MAX_NAMED_SOURCES:
            raise ValueError("invalid named sources")
        for source in sources:
            normalized_source = PK._expect_repo_path(source)
            PK.assert_persistable_paths(normalized_source)
        mutation = proposal["mutation"]
        if proposal["disposition"] == "promoted":
            if not isinstance(mutation, dict):
                raise ValueError("promotion requires one mutation")
            _validate_mutation_proposal(mutation)
            if mutation["capture_id"] != proposal["capture_id"]:
                raise ValueError("mutation capture mismatch")
            if mutation["terminal_disposition"] != {
                "disposition": proposal["disposition"],
                "reason_code": proposal["reason_code"],
                "recorded_at": proposal["recorded_at"],
            }:
                raise ValueError("mutation disposition mismatch")
        elif mutation is not None:
            raise ValueError("non-promotion cannot mutate a topic")
        if "routing_suggestion" in proposal:
            suggestion = proposal["routing_suggestion"]
            if proposal["disposition"] != "routed" or not isinstance(suggestion, dict):
                raise ValueError("invalid routing suggestion")
            PK._expect_keys(
                suggestion,
                {
                    "competency_question",
                    "authoritative_start",
                    "generated_outputs",
                    "verification",
                },
                set(),
            )
            if suggestion["competency_question"] != "CQ-ROUTE":
                raise ValueError("invalid routing competency")
            authoritative_start = PK._expect_repo_path(
                suggestion["authoritative_start"]
            )
            PK.assert_persistable_paths(authoritative_start)
            outputs = suggestion["generated_outputs"]
            if not isinstance(outputs, list) or not outputs:
                raise ValueError("invalid outputs")
            for output in outputs:
                normalized_output = PK._expect_repo_path(output)
                PK.assert_persistable_paths(normalized_output)
            PK._expect_text(suggestion["verification"], 500)
            PK.assert_persistable_text(suggestion["verification"])
    except PK.PrivacyRefusal:
        _refuse("privacy")
    except ValueError:
        _refuse("strict_parse")
    return proposal


def distill_observation(repo_root: Path | str, proposal: dict[str, Any]) -> dict[str, Any]:
    repo_root = resolve_worktree_root(repo_root)
    validated = _validate_distillation_proposal(copy.deepcopy(proposal))
    if validated["disposition"] == "promoted":
        with hold_writer_lock(repo_root):
            _assert_v1_writer_allowed(repo_root)
            partition, _capture, existing = _find_capture(
                repo_root, validated["capture_id"]
            )
            if existing is not None:
                _verify_promoted_state(repo_root, validated["mutation"], existing)
                mutation_result = {"promoted_implies_topic_and_map": True}
            else:
                mutation_result = _apply_guarded_mutation_body(
                    repo_root, validated["mutation"]
                )
        result = {
            "capture_id": validated["capture_id"],
            "disposition": "promoted",
            "partition": partition,
            "mutation": mutation_result,
        }
    else:
        disposition = write_terminal_disposition(
            repo_root,
            validated["capture_id"],
            validated["disposition"],
            reason_code=validated["reason_code"],
            recorded_at=validated["recorded_at"],
        )
        result = {
            "capture_id": validated["capture_id"],
            "disposition": disposition["disposition"],
            "partition": disposition["partition"],
        }
    if "routing_suggestion" in validated:
        result["suggestion"] = copy.deepcopy(validated["routing_suggestion"])
    return result


def enquire_worktree(repo_root: Path | str, _question: dict[str, Any]) -> dict[str, Any]:
    map_path = _map_path(repo_root)
    if not map_path.exists():
        return {"selected_topic_ids": []}
    parsed = json.loads(map_path.read_text(encoding="utf-8"))
    selected = [
        entry["topic_key"]
        for entry in parsed.get("entries", [])
        if entry.get("lifecycle") == "active"
    ][: budget_contract()["enquiry_bodies"]]
    return {"selected_topic_ids": selected}


@contextlib.contextmanager
def begin_distill(repo_root: Path | str, *, lock_timeout: float = 10.0) -> Iterator[Path]:
    with hold_writer_lock(repo_root, timeout=lock_timeout) as lock:
        yield lock


def merge_journal_events(
    expected_partition: str,
    *event_groups: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    _validate_partition_name(expected_partition)
    by_capture: dict[str, dict[str, Any]] = {}
    dispositions: dict[str, dict[str, Any]] = {}
    for event in [item for group in event_groups for item in group]:
        _validate_event(event, expected_partition)
        capture_id = event["capture_id"]
        if event["event_type"] == _CAPTURED:
            existing = by_capture.get(capture_id)
            if existing is not None and existing != event:
                _refuse("postimage_mismatch")
            by_capture[capture_id] = copy.deepcopy(event)
            continue
        if capture_id not in by_capture:
            _refuse("postimage_mismatch")
        if event["partition"] != by_capture[capture_id]["partition"]:
            _refuse("postimage_mismatch")
        existing_disposition = dispositions.get(capture_id)
        if existing_disposition is not None and existing_disposition != event:
            _refuse("postimage_mismatch")
        dispositions[capture_id] = copy.deepcopy(event)
    merged = [*by_capture.values(), *dispositions.values()]
    return sorted(
        merged,
        key=lambda item: (
            item["capture_id"],
            0 if item["event_type"] == _CAPTURED else 1,
            item.get("recorded_at", item.get("captured_at", "")),
        ),
    )
