#!/usr/bin/env python3
"""Export a bounded, display-only projection of canonical workspace status."""

from __future__ import annotations

import json
import math
import os
import signal
import subprocess
import sys
import threading
import tomllib
from collections.abc import Mapping
from contextlib import suppress
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

STATUS_TIMEOUT_SECONDS = 20
READER_JOIN_SECONDS = 1
MAX_STDOUT_BYTES = 4 * 1024 * 1024
MAX_STDERR_BYTES = 64 * 1024
MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_WORKSPACE_BYTES = 4 * 1024 * 1024
MAX_STATUS_ITEMS = 20_000
MAX_JSON_DEPTH = 32

_STATUS_SCRIPT = Path("packs/core/.apm/skills/workspace-status/scripts/workspace_status.py")
_WORKSPACE_FILE = Path("workspace.toml")
_WORK_COLLECTIONS = ("work.queue", "work.active")

_SAFE_ERROR_MESSAGES = frozenset({
    "canonical blocked work item is malformed",
    "canonical finding collection is malformed",
    "canonical finding is malformed",
    "canonical identity is malformed",
    "canonical identity is not repository-relative",
    "canonical work collection is unsupported",
    "canonical work display join is missing",
    "canonical work identity is ambiguous",
    "canonical work item is malformed",
    "canonical work references an unknown initiative",
    "initiative display join is ambiguous",
    "initiative display join is missing",
    "initiative display metadata is malformed",
    "projection contains a malformed display field",
    "projection contains a missing or malformed field",
    "projection contains an oversized display field",
    "required repository path is unavailable or unsafe",
    "work display join is ambiguous",
    "work display metadata is malformed",
    "work-index projection exceeded its byte limit",
    "workspace display metadata exceeds its byte limit",
    "workspace display metadata is malformed",
    "workspace display metadata is unavailable",
    "workspace-status JSON exceeded its byte limit",
    "workspace-status backlog entry has no display identity",
    "workspace-status backlog entry is malformed",
    "workspace-status brief queue is malformed",
    "workspace-status did not complete successfully",
    "workspace-status exited unsuccessfully",
    "workspace-status initiative is malformed",
    "workspace-status is missing a required collection",
    "workspace-status process output exceeded its byte limit",
    "workspace-status result exceeds the data depth limit",
    "workspace-status result exceeds the item limit",
    "workspace-status returned a malformed object",
    "workspace-status returned a malformed projection",
    "workspace-status returned a non-finite value",
    "workspace-status returned an unsupported schema version",
    "workspace-status returned an unsupported value",
    "workspace-status returned invalid JSON",
    "workspace-status shaping entry is malformed",
})


class ProjectionError(ValueError):
    """Raised when a safe, complete work-index projection cannot be built."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.code = (
            message.replace(" ", "-")
            if message in _SAFE_ERROR_MESSAGES
            else "unexpected-projection-error"
        )


def repository_root() -> Path:
    """Return the repository root derived from this checked-in script."""
    return Path(__file__).resolve().parents[1]


def _confined_file(root: Path, relative: Path) -> Path:
    """Resolve an existing file and prove its real path stays under root."""
    try:
        resolved_root = root.resolve(strict=True)
        target = (resolved_root / relative).resolve(strict=True)
        target.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ProjectionError("required repository path is unavailable or unsafe") from exc
    if not target.is_file():
        raise ProjectionError("required repository path is unavailable or unsafe")
    return target


def workspace_status_argv(repo: Path) -> list[str]:
    """Return the one allowed production workspace-status invocation."""
    root = repo.resolve(strict=True)
    script = _confined_file(root, _STATUS_SCRIPT)
    _confined_file(root, _WORKSPACE_FILE)
    return [sys.executable, str(script), "status", "--root", str(root)]


def _reject_non_finite(value: str) -> None:
    raise ProjectionError("workspace-status returned invalid JSON")


def _check_data_bounds(value: object, *, depth: int = 1) -> int:
    if depth > MAX_JSON_DEPTH:
        raise ProjectionError("workspace-status result exceeds the data depth limit")
    if isinstance(value, float) and not math.isfinite(value):
        raise ProjectionError("workspace-status returned a non-finite value")
    if isinstance(value, Mapping):
        count = len(value)
        for key, child in value.items():
            if not isinstance(key, str):
                raise ProjectionError("workspace-status returned a malformed object")
            count += _check_data_bounds(child, depth=depth + 1)
    elif isinstance(value, list):
        count = len(value)
        for child in value:
            count += _check_data_bounds(child, depth=depth + 1)
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise ProjectionError("workspace-status returned an unsupported value")
    else:
        count = 1
    if count > MAX_STATUS_ITEMS:
        raise ProjectionError("workspace-status result exceeds the item limit")
    return count


def _require_mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ProjectionError("workspace-status is missing a required collection")
    return value


def _require_list(parent: Mapping[str, Any], key: str) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        raise ProjectionError("workspace-status is missing a required collection")
    return value


def _validate_status_envelope(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProjectionError("workspace-status returned a malformed projection")
    if value.get("schema_version") != 1:
        raise ProjectionError("workspace-status returned an unsupported schema version")
    _require_list(value, "initiatives")
    work = _require_mapping(value, "work")
    for collection in ("ready", "active", "blocked", "shipped"):
        _require_list(work, collection)
    shaping = _require_mapping(value, "shaping")
    for collection in (
        "ready",
        "signals",
        "blocked",
        "active_entries",
        "top_level_backlog",
    ):
        _require_list(shaping, collection)
    _require_list(_require_mapping(value, "repo_backlog"), "open")
    canonical = _require_mapping(value, "canonical")
    for collection in (
        "findings",
        "evaluations",
        "legacy_memberships",
        "ready",
        "active",
        "blocked",
    ):
        _require_list(canonical, collection)
    return value


def _drain_bounded(
    stream: BinaryIO,
    sink: bytearray,
    limit: int,
    overflow: threading.Event,
    process: subprocess.Popen[bytes],
) -> None:
    """Drain one child stream without ever retaining more than limit + 1 bytes."""
    while True:
        try:
            chunk = stream.read(64 * 1024)
        except (OSError, ValueError):
            return
        if not chunk:
            return
        remaining = limit + 1 - len(sink)
        if remaining > 0:
            sink.extend(chunk[:remaining])
        if len(sink) > limit:
            overflow.set()
            _kill_process_group(process)
            return


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate the confined child and descendants without raising details."""
    if os.name == "posix":
        with suppress(OSError):
            os.killpg(process.pid, signal.SIGKILL)
        return
    with suppress(OSError):
        process.kill()


def _join_readers(
    readers: tuple[threading.Thread, threading.Thread],
    streams: tuple[BinaryIO, BinaryIO],
    process: subprocess.Popen[bytes],
) -> None:
    """Bound pipe cleanup even when a descendant inherited an output handle."""
    for reader in readers:
        reader.join(timeout=READER_JOIN_SECONDS)
    if not any(reader.is_alive() for reader in readers):
        return
    _kill_process_group(process)
    for stream in streams:
        with suppress(OSError):
            stream.close()
    for reader in readers:
        reader.join(timeout=READER_JOIN_SECONDS)
    raise ProjectionError("workspace-status did not complete successfully")


def _run_bounded_status(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Run fixed argv while enforcing timeout and stream caps during reads."""
    try:
        process = subprocess.Popen(  # noqa: S603 - argv is fixed and shell stays disabled.
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            start_new_session=os.name == "posix",
            creationflags=(
                subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            ),
        )
    except OSError as exc:
        raise ProjectionError("workspace-status did not complete successfully") from exc
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise ProjectionError("workspace-status did not complete successfully")

    stdout = bytearray()
    stderr = bytearray()
    overflow = threading.Event()
    readers = (
        threading.Thread(
            target=_drain_bounded,
            args=(process.stdout, stdout, MAX_STDOUT_BYTES, overflow, process),
            daemon=True,
        ),
        threading.Thread(
            target=_drain_bounded,
            args=(process.stderr, stderr, MAX_STDERR_BYTES, overflow, process),
            daemon=True,
        ),
    )
    for reader in readers:
        reader.start()
    try:
        returncode = process.wait(timeout=STATUS_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        _kill_process_group(process)
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=READER_JOIN_SECONDS)
        _join_readers(readers, (process.stdout, process.stderr), process)
        raise ProjectionError("workspace-status did not complete successfully") from exc
    _join_readers(readers, (process.stdout, process.stderr), process)
    if overflow.is_set():
        raise ProjectionError("workspace-status process output exceeded its byte limit")
    return subprocess.CompletedProcess(argv, returncode, bytes(stdout), bytes(stderr))


def run_workspace_status(repo: Path) -> Mapping[str, Any]:
    """Invoke workspace-status once and return its validated public result."""
    argv = workspace_status_argv(repo)
    completed = _run_bounded_status(argv)
    if completed.returncode != 0:
        raise ProjectionError("workspace-status exited unsuccessfully")
    if len(completed.stdout) > MAX_JSON_BYTES:
        raise ProjectionError("workspace-status JSON exceeded its byte limit")
    try:
        value = json.loads(completed.stdout, parse_constant=_reject_non_finite)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProjectionError("workspace-status returned invalid JSON") from exc
    _check_data_bounds(value)
    return _validate_status_envelope(value)


def parse_workspace_display(source: str | bytes) -> Mapping[str, Any]:
    """Parse workspace TOML for display-only initiative and summary joins."""
    try:
        data = tomllib.loads(source.decode("utf-8") if isinstance(source, bytes) else source)
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ProjectionError("workspace display metadata is malformed") from exc
    if not isinstance(data, Mapping):
        raise ProjectionError("workspace display metadata is malformed")
    return data


def load_workspace_display(repo: Path) -> Mapping[str, Any]:
    """Read the confined workspace file and parse its display-only fields."""
    path = _confined_file(repo.resolve(strict=True), _WORKSPACE_FILE)
    try:
        if path.stat().st_size > MAX_WORKSPACE_BYTES:
            raise ProjectionError("workspace display metadata exceeds its byte limit")
        with path.open("rb") as source:
            data = source.read(MAX_WORKSPACE_BYTES + 1)
        if len(data) > MAX_WORKSPACE_BYTES:
            raise ProjectionError("workspace display metadata exceeds its byte limit")
        return parse_workspace_display(data)
    except OSError as exc:
        raise ProjectionError("workspace display metadata is unavailable") from exc


def _safe_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 4096:
        raise ProjectionError("canonical identity is malformed")
    if "\\" in value or (len(value) >= 2 and value[1] == ":"):
        raise ProjectionError("canonical identity is not repository-relative")
    try:
        path = PurePosixPath(value)
    except (TypeError, ValueError) as exc:
        raise ProjectionError("canonical identity is malformed") from exc
    if path.is_absolute() or path.as_posix() != value:
        raise ProjectionError("canonical identity is not repository-relative")
    if any(part in {"", ".", ".."} or part.endswith(":") for part in path.parts):
        raise ProjectionError("canonical identity is not repository-relative")
    return value


def _required_string(parent: Mapping[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value:
        raise ProjectionError("projection contains a missing or malformed field")
    if len(value.encode("utf-8")) > 16_384:
        raise ProjectionError("projection contains an oversized display field")
    return value


def _optional_string(parent: Mapping[str, Any], key: str) -> str | None:
    value = parent.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or len(value.encode("utf-8")) > 16_384:
        raise ProjectionError("projection contains a malformed display field")
    return value


def _workspace_display_index(
    workspace: Mapping[str, Any],
) -> tuple[dict[str, tuple[str, str]], dict[tuple[str, str, str], str]]:
    initiatives: dict[str, tuple[str, str]] = {}
    entries: dict[tuple[str, str, str], str] = {}
    for ini_slug, raw_ini in workspace.items():
        if not isinstance(ini_slug, str) or not ini_slug.startswith("ini-"):
            continue
        if not isinstance(raw_ini, Mapping):
            raise ProjectionError("initiative display metadata is malformed")
        name = _required_string(raw_ini, "name")
        milestone = _required_string(raw_ini, "milestone")
        if ini_slug in initiatives:
            raise ProjectionError("initiative display join is ambiguous")
        initiatives[ini_slug] = (name, milestone)
        work = raw_ini.get("work", {})
        if not isinstance(work, Mapping):
            raise ProjectionError("work display metadata is malformed")
        for list_name in ("queue", "active"):
            collection = f"work.{list_name}"
            raw_entries = work.get(list_name, [])
            if not isinstance(raw_entries, list):
                raise ProjectionError("work display metadata is malformed")
            for raw_entry in raw_entries:
                if not isinstance(raw_entry, Mapping):
                    continue
                if not all(
                    key in raw_entry for key in ("path", "kind", "source", "summary", "needs")
                ):
                    # Legacy entries remain reconciliation input for workspace-status,
                    # but they are not admitted to the display-join boundary.
                    continue
                path = _safe_path(raw_entry.get("path"))
                key = (ini_slug, collection, path)
                if key in entries:
                    raise ProjectionError("work display join is ambiguous")
                entries[key] = _required_string(raw_entry, "summary")
    return initiatives, entries


def _project_findings(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raise ProjectionError("canonical finding collection is malformed")
    findings: list[dict[str, Any]] = []
    for value in raw:
        if not isinstance(value, Mapping):
            raise ProjectionError("canonical finding is malformed")
        dispatchable = value.get("dispatchable")
        if not isinstance(dispatchable, bool):
            raise ProjectionError("canonical finding is malformed")
        findings.append({
            "code": _required_string(value, "code"),
            "path": _safe_path(value.get("path")),
            "dispatchable": dispatchable,
            "next_action": _required_string(value, "next_action"),
        })
    return findings


def _project_work_item(
    raw: object,
    display: Mapping[tuple[str, str, str], str],
) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ProjectionError("canonical work item is malformed")
    ini_slug = _required_string(raw, "ini_slug")
    collection = _required_string(raw, "collection")
    if collection not in _WORK_COLLECTIONS:
        raise ProjectionError("canonical work collection is unsupported")
    path = _safe_path(raw.get("path"))
    key = (ini_slug, collection, path)
    if key not in display:
        raise ProjectionError("canonical work display join is missing")
    dispatchable = raw.get("dispatchable")
    if not isinstance(dispatchable, bool):
        raise ProjectionError("canonical work item is malformed")
    return {
        "path": path,
        "slug": _required_string(raw, "slug"),
        "kind": _required_string(raw, "kind"),
        "collection": collection,
        "dispatchable": dispatchable,
        "findings": _project_findings(raw.get("findings")),
        "summary": display[key],
    }


def _project_context(status: Mapping[str, Any]) -> tuple[list[dict], list[dict], list[dict]]:
    briefs: list[dict[str, str]] = []
    for raw_ini in _require_list(status, "initiatives"):
        if not isinstance(raw_ini, Mapping):
            raise ProjectionError("workspace-status initiative is malformed")
        ini_slug = _required_string(raw_ini, "slug")
        brief_queue = raw_ini.get("brief_queue")
        if brief_queue is None:
            continue
        if not isinstance(brief_queue, Mapping):
            raise ProjectionError("workspace-status brief queue is malformed")
        for path in _require_list(brief_queue, "ready"):
            briefs.append({"path": _safe_path(path), "initiative": ini_slug})

    shaping: list[dict[str, str]] = []
    raw_shaping = _require_mapping(status, "shaping")
    shaping_collections = (
        ("active_entries", "active"),
        ("ready", "ready"),
        ("blocked", "blocked"),
        ("signals", "signal"),
        ("top_level_backlog", "backlog"),
    )
    for collection, state in shaping_collections:
        for raw in _require_list(raw_shaping, collection):
            if not isinstance(raw, Mapping):
                raise ProjectionError("workspace-status shaping entry is malformed")
            initiative = _optional_string(raw, "ini_slug") or "repository"
            shaping.append({
                "slug": _required_string(raw, "slug"),
                "type": _required_string(raw, "entry_type"),
                "initiative": initiative,
                "status": state,
            })

    backlog: list[dict[str, str]] = []
    for raw in _require_list(_require_mapping(status, "repo_backlog"), "open"):
        if not isinstance(raw, Mapping):
            raise ProjectionError("workspace-status backlog entry is malformed")
        slug = _optional_string(raw, "slug")
        path = _optional_string(raw, "path")
        summary = _optional_string(raw, "summary")
        label = summary or slug or path
        if label is None:
            raise ProjectionError("workspace-status backlog entry has no display identity")
        item = {"label": label}
        if slug is not None:
            item["slug"] = slug
        if path is not None:
            item["path"] = _safe_path(path)
        if summary is not None:
            item["summary"] = summary
        backlog.append(item)

    briefs.sort(key=lambda item: (item["initiative"], item["path"]))
    shaping.sort(key=lambda item: (item["status"], item["initiative"], item["slug"]))
    backlog.sort(key=lambda item: item.get("slug", item.get("path", item["label"])))
    return briefs, shaping, backlog


def _attention_work_items(
    raw_items: list[Any],
    display: Mapping[tuple[str, str, str], str],
) -> list[Mapping[str, Any]]:
    """Validate blocked entries before selecting delivery-relevant attention work."""
    selected: list[Mapping[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            raise ProjectionError("canonical blocked work item is malformed")
        collection = _required_string(item, "collection")
        if collection not in _WORK_COLLECTIONS:
            continue
        projected = _project_work_item(item, display)
        if projected["findings"]:
            selected.append(item)
    return selected


def build_projection(status: Mapping[str, Any], workspace: Mapping[str, Any]) -> dict[str, Any]:
    """Join display metadata onto canonical status without reclassification."""
    status = _validate_status_envelope(status)
    initiative_display, entry_display = _workspace_display_index(workspace)
    canonical = _require_mapping(status, "canonical")

    bucket_sources = {
        "active": _require_list(canonical, "active"),
        "ready": _require_list(canonical, "ready"),
        "attention": _attention_work_items(
            _require_list(canonical, "blocked"), entry_display
        ),
    }
    projected_by_ini: dict[str, dict[str, list[dict[str, Any]]]] = {}
    seen: set[tuple[str, str, str]] = set()
    for bucket, raw_items in bucket_sources.items():
        for raw in raw_items:
            item = _project_work_item(raw, entry_display)
            if not isinstance(raw, Mapping):
                raise ProjectionError("canonical work item is malformed")
            ini_slug = _required_string(raw, "ini_slug")
            identity = (ini_slug, item["collection"], item["path"])
            if identity in seen:
                raise ProjectionError("canonical work identity is ambiguous")
            seen.add(identity)
            projected_by_ini.setdefault(ini_slug, {"active": [], "ready": [], "attention": []})[
                bucket
            ].append(item)

    initiative_rows: list[dict[str, Any]] = []
    for raw_ini in _require_list(status, "initiatives"):
        if not isinstance(raw_ini, Mapping):
            raise ProjectionError("workspace-status initiative is malformed")
        ini_slug = _required_string(raw_ini, "slug")
        if ini_slug not in initiative_display:
            raise ProjectionError("initiative display join is missing")
        name, milestone = initiative_display[ini_slug]
        buckets = projected_by_ini.pop(ini_slug, {"active": [], "ready": [], "attention": []})
        for items in buckets.values():
            items.sort(key=lambda item: item["path"])
        initiative_rows.append({
            "slug": ini_slug,
            "name": name,
            "milestone": milestone,
            **buckets,
        })
    if projected_by_ini:
        raise ProjectionError("canonical work references an unknown initiative")
    initiative_rows.sort(key=lambda item: item["slug"])

    briefs, shaping, backlog = _project_context(status)
    counts = {
        "active": sum(len(item["active"]) for item in initiative_rows),
        "ready": sum(len(item["ready"]) for item in initiative_rows),
        "attention": sum(len(item["attention"]) for item in initiative_rows),
        "briefs": len(briefs),
        "shaping": len(shaping),
        "backlog": len(backlog),
    }
    return {
        "schema_version": 1,
        "counts": counts,
        "initiatives": initiative_rows,
        "briefs": briefs,
        "shaping": shaping,
        "backlog": backlog,
    }


def _validate_projection_targets(projection: Mapping[str, Any], repo: Path) -> None:
    root = repo.resolve(strict=True)
    for initiative in projection["initiatives"]:
        for bucket in ("active", "ready", "attention"):
            for item in initiative[bucket]:
                relative = Path(item["path"])
                candidate = root / relative
                missing_artifact = any(
                    finding.get("code") == "missing_artifact"
                    for finding in item["findings"]
                )
                if missing_artifact:
                    if bucket != "attention" or os.path.lexists(candidate):
                        raise ProjectionError(
                            "required repository path is unavailable or unsafe"
                        )
                    parent = candidate.parent
                    while not os.path.lexists(parent):
                        parent = parent.parent
                    try:
                        parent.resolve(strict=True).relative_to(root)
                    except (OSError, RuntimeError, ValueError) as exc:
                        raise ProjectionError(
                            "required repository path is unavailable or unsafe"
                        ) from exc
                    continue
                _confined_file(root, relative)
    for brief in projection["briefs"]:
        _confined_file(root, Path(brief["path"]))
    for item in projection["backlog"]:
        if "path" in item:
            _confined_file(root, Path(item["path"]))


def export_work_index(repo: Path) -> dict[str, Any]:
    """Build the production work-index projection for a repository."""
    root = repo.resolve(strict=True)
    projection = build_projection(
        run_workspace_status(root),
        load_workspace_display(root),
    )
    _validate_projection_targets(projection, root)
    return projection


def main() -> int:
    """Write deterministic projection JSON or one confined diagnostic."""
    try:
        projection = export_work_index(repository_root())
        encoded = json.dumps(
            projection,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
            raise ProjectionError("work-index projection exceeded its byte limit")
        print(encoded)
        return 0
    except ProjectionError as exc:
        print(f"work-index export failed: {exc.code}", file=sys.stderr)
        return 1
    except Exception:
        print("work-index export failed: unexpected-exporter-error", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
