#!/usr/bin/env python3
"""Retire one intent and issue its successor as a recoverable transaction.

The durable record is comparison data. Live-path authority comes from the
operator request, pinned Git commit, and independently derived bytes.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import importlib.util
import json
import os
import re
import secrets
import selectors
import stat
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, NoReturn, Sequence


def _load_module(path: Path, module_name: str) -> object:
    """Load one shipped runtime script by path without a package import."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("runtime-module-unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILLS_DIR = _SCRIPT_DIR.parents[1]
_previous_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    _request = _load_module(
        _SCRIPT_DIR / "intent_rename_request.py",
        "core_work_intake_intent_rename_request_runtime",
    )
    _tombstone = _load_module(
        _SCRIPT_DIR / "intent_tombstone.py",
        "core_work_intake_intent_tombstone_runtime",
    )
    _ordinal = _load_module(
        _SCRIPT_DIR / "intent_ordinal.py", "core_work_intake_intent_ordinal_runtime"
    )
    _shape = _load_module(_SCRIPT_DIR / "intent_shape.py", "core_work_intake_intent_shape_runtime")
    _close_work = _load_module(
        _SKILLS_DIR / "close-work/scripts/close_work.py",
        "core_close_work_descriptor_runtime",
    )
finally:
    sys.dont_write_bytecode = _previous_bytecode


INTENTS_PARENT = "docs/product/intents"
WORKSPACE_FILE = "workspace.toml"
WORKSPACE_LOCK_FILE = ".workspace-repair.lock"
_STAGE_PREFIX = ".intent-rename-"
_STAGE_RE = re.compile(r"^\.intent-rename-([0-9a-f]{32})$")
_OPERATION_RE = re.compile(r"^[0-9a-f]{32}$")
_PID_RE = re.compile(rb"^[1-9][0-9]{0,19}$")
# POSIX `pid_t` is a signed 32-bit integer.
_MAX_PID = 2**31 - 1
_SOURCE_NAME_RE = re.compile(r"^(?:VISION|STRAT|CAP|FEAT)-[0-9]{4,12}-([A-Za-z0-9._-]+)\.md$")
_TYPED_NAME_RE = re.compile(r"^(VISION|STRAT|CAP|FEAT)-([0-9]{4,12})-[^/]+\.md$")
_UNTYPED_NAME_RE = re.compile(r"^([A-Za-z0-9._-]+)\.md$")
# The only path shape `resolve` prints: no delimiter, control, or space can
# reach the colon-joined operator output.
_DISPLAY_SAFE_RE = re.compile(r"[A-Za-z0-9._/-]{1,512}")
_RECORD_NAME = "record.json"
_SEAL_NAME = "complete.json"
_CLEANUP_NAME = "cleanup.json"
_LOCK_CLAIM_NAME = "lock.claim"
_RECORD_VERSION = 1
_MAX_RECORD_BYTES = 256 * 1024
_MAX_SEAL_BYTES = 64 * 1024
_MAX_CLEANUP_BYTES = 4096
_MAX_FILE_BYTES = 4 * 1024 * 1024
_MAX_WORKSPACE_BYTES = 16 * 1024 * 1024
_MAX_PREAMBLE_BYTES = 64 * 1024
_MAX_WRITES = 1024
_MAX_TRACKED_FILES = 10000
_MAX_CITING_BYTES = 32 * 1024 * 1024
_MAX_STAGE_ENTRIES = _MAX_WRITES + 4
_MAX_RECOVERY_CANDIDATES = 64
_MAX_REGISTRY_MERGE_LINES = 262144
_MAX_JSON_DEPTH = 16
_MAX_JSON_MEMBERS = 4096
_MAX_JSON_STRING = 4096
_GIT_TIMEOUT_SECONDS = 10
_MAX_REF_BYTES = 128
# `O_NONBLOCK` keeps a FIFO or device from blocking the open before the
# regular-file check can refuse it; it does not change regular-file reads.
_READ_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_NONBLOCK", 0)
)
_DIRECT_PROJECTION_RAILS = (
    (".agents/skills/", "skills", "same"),
    (".claude/skills/", "skills", "same"),
    (".claude/agents/", "agents", "same"),
    (".claude/commands/", "commands", "same"),
    (".codex/agents/", "agents", "codex-agent"),
    ("tools/hooks/", "hooks", "same"),
)
_MERGED_PROJECTION_RAILS = {
    ".claude/settings.local.json": "hook-wiring",
    ".codex/hooks.json": "hook-wiring",
}


class RenameStatus(Enum):
    """Terminal or recoverable outcome for one rename attempt."""

    COMMITTED = "committed"
    PARTIAL = "partial"
    ROLLED_BACK = "rolled_back"
    REFUSED = "refused"


@dataclass(frozen=True)
class RenameResult:
    """A closed result safe to render on the installed operator surface."""

    status: RenameStatus
    code: str
    operation_id: str | None = None


@dataclass(frozen=True)
class ResolveResult:
    """A tombstone resolution diagnostic without successor content."""

    code: str
    paths: tuple[str, ...]


class InjectedInterruption(RuntimeError):
    """A test interruption at the same checkpoint used by SIGKILL tests."""

    def __init__(self, checkpoint: str) -> None:
        super().__init__(checkpoint)
        self.checkpoint = checkpoint


class _RegistryLockPartial(RuntimeError):
    """An owned registry lock could not be released with proven identity."""

    def __init__(self, operation_id: str) -> None:
        super().__init__("lock-release-failed")
        self.operation_id = operation_id


@dataclass(frozen=True)
class _Write:
    order: int
    path: str
    action: Literal["create", "replace"]
    preimage: bytes | None
    postimage: bytes

    @property
    def stage_name(self) -> str:
        return f"{self.order:04d}.postimage"


@dataclass(frozen=True)
class _Derived:
    operation_id: str
    base_commit: str
    source: str
    target_token: str
    date: str
    successor: str
    origin_view_sha256: str
    writes: tuple[_Write, ...]


@dataclass(frozen=True)
class _PinnedAllocation:
    """One allocator answer and the origin view that produced it."""

    successor: str
    origin_view_sha256: str


@dataclass(frozen=True)
class _LoadedStage:
    derived: _Derived
    stage: Path
    record_bytes: bytes
    seal_bytes: bytes


_Checkpoint = Callable[[str], None]
_Today = Callable[[], datetime.date]


def _noop_checkpoint(_: str) -> None:
    return None


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.UTC).date()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")


def _strict_json(data: bytes) -> object:
    """Parse bounded JSON and reject shapes that can carry record authority."""
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        if len(items) > _MAX_JSON_MEMBERS:
            raise ValueError("json-shape")
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate-key")
            result[key] = value
        return result

    def validate(value: object, depth: int = 0) -> None:
        if depth > _MAX_JSON_DEPTH:
            raise ValueError("json-shape")
        if isinstance(value, dict):
            if len(value) > _MAX_JSON_MEMBERS:
                raise ValueError("json-shape")
            for key, item in value.items():
                if len(key) > _MAX_JSON_STRING:
                    raise ValueError("json-shape")
                validate(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > _MAX_JSON_MEMBERS:
                raise ValueError("json-shape")
            for item in value:
                validate(item, depth + 1)
        elif isinstance(value, str):
            if len(value) > _MAX_JSON_STRING:
                raise ValueError("json-shape")
        elif isinstance(value, (bool, float)):
            # The closed record schema has no booleans, and `True == 1` would
            # let one stand in for an integer under value comparison.
            raise ValueError("json-shape")

    try:
        parsed = json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    except RecursionError as error:
        raise ValueError("json-shape") from error
    validate(parsed)
    return parsed


def _open_parent(root: Path, directory: Path) -> int:
    return _close_work.open_validated_parent(root, directory)  # type: ignore[attr-defined]


def _read_at(
    descriptor: int,
    name: str,
    *,
    max_bytes: int,
    links: Sequence[int] = (1,),
) -> tuple[bytes, os.stat_result]:
    opened = os.open(name, _READ_FLAGS, dir_fd=descriptor)
    try:
        inspected = os.fstat(opened)
        if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink not in links:
            raise ValueError("unsafe-file")
        if inspected.st_size > max_bytes:
            raise ValueError("file-bound")
        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(opened, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            raise ValueError("file-bound")
        after = os.fstat(opened)
        if (inspected.st_dev, inspected.st_ino, inspected.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ):
            raise ValueError("identity-changed")
        # A link added while reading would make the returned bytes describe an
        # alien link state, so the allowed state is proven again at return.
        if not stat.S_ISREG(after.st_mode) or after.st_nlink not in links:
            raise ValueError("unsafe-file")
        return data, after
    finally:
        os.close(opened)


def _create_at(
    descriptor: int,
    name: str,
    data: bytes,
    *,
    mode: int = 0o600,
    exact_mode: int | None = None,
) -> None:
    """Exclusively create ``name``; ``exact_mode`` is applied regardless of umask."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    opened = os.open(name, flags, mode, dir_fd=descriptor)
    try:
        if exact_mode is not None:
            os.fchmod(opened, exact_mode)
        view = memoryview(data)
        while view:
            written = os.write(opened, view)
            if written <= 0:
                raise OSError("short-write")
            view = view[written:]
        os.fsync(opened)
        inspected = os.fstat(opened)
        if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink != 1:
            raise ValueError("unsafe-created-file")
    finally:
        os.close(opened)
    os.fsync(descriptor)


def _stat_at(descriptor: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _list_at(descriptor: int) -> set[str]:
    names: set[str] = set()
    with os.scandir(descriptor) as entries:
        for entry in entries:
            names.add(entry.name)
            if len(names) > _MAX_STAGE_ENTRIES:
                raise ValueError("stage-entry-bound")
    return names


def _remove_empty_stage(parent_descriptor: int, name: str) -> None:
    """Remove one verified-empty stage through its held parent descriptor."""
    os.rmdir(name, dir_fd=parent_descriptor)


def _git(root: Path, arguments: Sequence[str], *, max_bytes: int) -> bytes:
    """Run one Git read, refusing once stdout exceeds ``max_bytes``.

    Output is consumed incrementally so an oversized snapshot is refused
    before it is buffered, and the process is killed on any early exit.
    """
    # Only the allowlisted environment reaches Git, so no inherited variable
    # can point it at another repository, index, or configuration.
    environment = {
        name: os.environ[name]
        for name in _ordinal.GIT_ENVIRONMENT_ALLOWLIST  # type: ignore[attr-defined]
        if name in os.environ
    }
    environment.update(GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    process = subprocess.Popen(
        ["git", "--no-optional-locks", "--literal-pathspecs", *arguments],
        cwd=os.fspath(root),
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert process.stdout is not None
    deadline = time.monotonic() + _GIT_TIMEOUT_SECONDS
    chunks: list[bytes] = []
    size = 0
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise subprocess.TimeoutExpired(process.args, _GIT_TIMEOUT_SECONDS)
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("git-output-bound")
                chunks.append(chunk)
        returncode = process.wait(timeout=max(deadline - time.monotonic(), 0.001))
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
    if returncode != 0:
        raise ValueError("git-refused")
    return b"".join(chunks)


def _head(root: Path) -> str:
    value = (
        _git(root, ["rev-parse", "--verify", "HEAD"], max_bytes=_MAX_REF_BYTES)
        .decode("ascii")
        .strip()
    )
    if not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise ValueError("base-invalid")
    return value


def _git_file(
    root: Path,
    commit: str,
    relative: str,
    *,
    max_bytes: int = _MAX_FILE_BYTES,
) -> bytes:
    return _git(root, ["show", f"{commit}:{relative}"], max_bytes=max_bytes)


def _git_intent_entries(root: Path, commit: str) -> tuple[tuple[str, str], ...]:
    """Return ``(name, kind)`` for each entry directly in the pinned intents tree.

    ``kind`` is ``file``, ``symlink``, or ``directory`` (a tree or gitlink), so
    the snapshot the allocator reads keeps each entry's type rather than
    flattening everything to a regular file.
    """
    data = _git(
        root,
        ["ls-tree", "-z", commit, "--", f"{INTENTS_PARENT}/"],
        max_bytes=_MAX_FILE_BYTES,
    )
    kinds = {"100644": "file", "100755": "file", "120000": "symlink"}
    entries: list[tuple[str, str]] = []
    for record in data.split(b"\0"):
        if not record:
            continue
        header, _, path = record.decode("utf-8").partition("\t")
        mode = header.split(" ", 1)[0]
        entries.append((path.rsplit("/", 1)[-1], kinds.get(mode, "directory")))
    return tuple(entries)


_GIT_REDIRECT_ENVIRONMENT = (
    *_ordinal.GIT_REDIRECT_VARIABLES,  # type: ignore[attr-defined]
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
)


def _filesystem_unsupported() -> bool:
    """Report whether the platform lacks the descriptor semantics the transaction needs.

    Every read, create, link, and replace is no-follow and descriptor-relative.
    Without those the flags would silently fall back to following links, so the
    operation refuses instead.
    """
    # Compared by name: a wrapped `os` function is not the object the
    # support sets list, but it still reaches the same system call.
    dir_fd = {function.__name__ for function in os.supports_dir_fd}
    follow = {function.__name__ for function in os.supports_follow_symlinks}
    return (
        not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
        or not {"open", "stat", "unlink", "link", "rename", "rmdir", "mkdir"} <= dir_fd
        or not {"stat", "link"} <= follow
    )


def _git_environment_redirected() -> bool:
    """Report whether the caller's environment redirects Git's repository view.

    Sibling contract code shells out to Git with the caller's environment, so
    the operation refuses outright rather than let any read see another view.
    """
    return any(name in os.environ for name in _GIT_REDIRECT_ENVIRONMENT)


def _printable_intent_path(relative: str) -> bool:
    """Report whether ``relative`` may be printed: display-safe and lexically an intents path."""
    if _DISPLAY_SAFE_RE.fullmatch(relative) is None:
        return False
    try:
        _check_relative_path(relative)
    except ValueError:
        return False
    parent = Path(INTENTS_PARENT).parts
    return Path(relative).parts[: len(parent)] == parent


def _confined_to_intents(root: Path, relative: str) -> bool:
    """Report whether ``relative`` resolves inside the intents parent."""
    try:
        _check_relative_path(relative)
        _request._transaction.resolve_confined_target(  # type: ignore[attr-defined]
            repository_root=root,
            configured_parent=INTENTS_PARENT,
            artifact_target=relative,
        )
    except (OSError, RuntimeError, ValueError):
        # RuntimeError is how Python 3.11 and 3.12 report a symlink loop
        # during resolution; it is a confinement failure like the others.
        return False
    return True


def _recovery_request_refusal(root: Path, source_rel: str, target_token: str) -> str | None:
    """Confine a recovery request the way the request contract confines a rename.

    Recovery cannot require a live source, because a forward partial has
    already tombstoned it, but the source must still name an intent under the
    intents parent and the token must be a known namespace.
    """
    if not _confined_to_intents(root, source_rel):
        return "source-outside-root"
    try:
        _source_slug(source_rel)
    except ValueError:
        return "source-outside-root"
    if target_token not in _ordinal.NAMESPACE_TOKENS:  # type: ignore[attr-defined]
        return "token-unknown"
    return None


def _source_slug(source: str) -> str:
    """Return the filename slug the successor carries.

    A typed source keeps the slug after its token and ordinal; an untyped
    legacy source, which the request contract also admits, carries its stem.
    """
    name = Path(source).name
    match = _SOURCE_NAME_RE.fullmatch(name)
    if match is not None:
        return match.group(1)
    untyped = _UNTYPED_NAME_RE.fullmatch(name)
    if untyped is None:
        raise ValueError("source-name-invalid")
    return untyped.group(1)


def _slug_bytes(data: bytes) -> str:
    text = data.decode("utf-8")
    for name, value in _shape.read_preamble(text):  # type: ignore[attr-defined]
        if name == "Slug":
            return value
    raise ValueError("slug-missing")


def _origin_view_sha256(view: object) -> str:
    """Hash the bounded allocator-visible origin state for later comparison."""
    state = getattr(view, "state", None)
    names = getattr(view, "names", None)
    if state == "failed":
        raise ValueError("allocation-refused")
    if state not in {"absent", "ok"} or not isinstance(names, frozenset):
        raise ValueError("allocation-refused")
    if any(not isinstance(name, str) for name in names):
        raise ValueError("allocation-refused")
    return _sha256(_canonical_json({"names": sorted(names), "state": state}))


def _snapshot_successor(
    root: Path, commit: str, source: str, token: str, origin_view: object
) -> str:
    if token not in _ordinal.NAMESPACE_TOKENS:  # type: ignore[attr-defined]
        raise ValueError("token-unknown")
    with tempfile.TemporaryDirectory(
        prefix="intent-rename-ordinal-", ignore_cleanup_errors=True
    ) as snapshot:
        snapshot_path = Path(snapshot)
        for name, kind in _git_intent_entries(root, commit):
            entry = snapshot_path / name
            if kind == "file":
                entry.touch()
            elif kind == "symlink":
                entry.symlink_to("nonexistent-target")
            else:
                entry.mkdir()
        remote_view = _ordinal.remote_view  # type: ignore[attr-defined]
        try:
            _ordinal.remote_view = (  # type: ignore[attr-defined]
                lambda _directory, _deadline=None: origin_view
            )
            ordinal = _ordinal.next_typed_ordinal(snapshot_path, token)  # type: ignore[attr-defined]
        finally:
            _ordinal.remote_view = remote_view  # type: ignore[attr-defined]
    if ordinal is None:
        raise ValueError("allocation-refused")
    return f"{INTENTS_PARENT}/{token}-{ordinal:04d}-{_source_slug(source)}.md"


def _pinned_allocation(
    root: Path, commit: str, source: str, token: str
) -> _PinnedAllocation:
    """Derive one successor from the pinned HEAD and one local origin read."""
    origin_view = _ordinal.remote_view(root / INTENTS_PARENT)  # type: ignore[attr-defined]
    digest = _origin_view_sha256(origin_view)
    successor = _snapshot_successor(root, commit, source, token, origin_view)
    return _PinnedAllocation(successor, digest)


def derive_successor_path(
    source_rel: str, target_token: str, *, repository_root: Path | None = None
) -> str | None:
    """Return the allocator-selected successor for a new operation."""
    root = (repository_root or Path.cwd()).resolve()
    try:
        ordinal = _ordinal.next_typed_ordinal(  # type: ignore[attr-defined]
            root / INTENTS_PARENT, target_token
        )
        if ordinal is None:
            return None
        return f"{INTENTS_PARENT}/{target_token}-{ordinal:04d}-{_source_slug(source_rel)}.md"
    except (OSError, ValueError):
        return None


def _tracked_paths(root: Path, commit: str | None = None) -> tuple[str, ...]:
    """Return the tracked set: the pinned commit's tree, or the live index.

    A pinned derivation reads file bytes from ``commit``, so its parent set must
    come from the same snapshot; an index change absent from that commit would
    otherwise name a path the snapshot cannot read.
    """
    arguments = (
        ["ls-tree", "-r", "-z", "--name-only", "--full-tree", commit]
        if commit is not None
        else ["ls-files", "-z", "--"]
    )
    data = _git(root, arguments, max_bytes=_MAX_FILE_BYTES)
    paths = tuple(item.decode("utf-8") for item in data.split(b"\0") if item)
    if len(paths) > _MAX_TRACKED_FILES:
        raise ValueError("tracked-file-bound")
    for relative in paths:
        _check_relative_path(relative)
    return paths


def _tracked_apm_candidates(
    tracked_paths: Sequence[str], primitive: str, remainder: str | None = None
) -> tuple[str, ...]:
    """Return tracked pack sources on one closed ``.apm`` primitive rail."""
    candidates: list[str] = []
    for relative in tracked_paths:
        parts = relative.split("/", 4)
        if (
            len(parts) != 5
            or parts[0] != "packs"
            or not parts[1]
            or parts[2] != ".apm"
            or parts[3] != primitive
            or not parts[4]
        ):
            continue
        if remainder is None or parts[4] == remainder:
            candidates.append(relative)
    return tuple(candidates)


def _projection_source(
    root: Path,
    relative: str,
    tracked_paths: Sequence[str],
    source_bytes: bytes,
    base_commit: str | None,
) -> tuple[str, bytes] | None:
    """Resolve a self-host projection to one tracked authoritative source.

    A generated path never grants write authority. Direct rails must have one
    source at the corresponding pack-relative path. Merged rails must have one
    source carrying the cited literal. Anything else refuses before staging.
    """
    primitive: str | None = None
    remainder: str | None = None
    for prefix, candidate_primitive, mode in _DIRECT_PROJECTION_RAILS:
        if not relative.startswith(prefix):
            continue
        primitive = candidate_primitive
        remainder = relative[len(prefix) :]
        if mode == "codex-agent":
            if not remainder.endswith(".toml"):
                raise ValueError("projection-source-missing")
            remainder = f"{remainder[:-5]}.md"
        break

    merged_primitive = _MERGED_PROJECTION_RAILS.get(relative)
    if primitive is None and merged_primitive is None:
        return None

    candidates = _tracked_apm_candidates(
        tracked_paths,
        primitive or merged_primitive or "",
        remainder if primitive is not None else None,
    )
    if not candidates:
        raise ValueError("projection-source-missing")

    matches: list[tuple[str, bytes]] = []
    for candidate in candidates:
        data = (
            _git_file(root, base_commit, candidate)
            if base_commit is not None
            else _read_live(root, candidate, _MAX_FILE_BYTES)
        )
        if source_bytes in data:
            try:
                data.decode("utf-8")
            except UnicodeError as error:
                raise ValueError("citation-not-text") from error
            matches.append((candidate, data))

    if not matches:
        raise ValueError("projection-source-missing")
    if len(matches) != 1 or (primitive is not None and len(candidates) != 1):
        raise ValueError("projection-source-ambiguous")
    return matches[0]


def _read_optional_live(root: Path, relative: str, maximum: int) -> bytes | None:
    try:
        return _read_live(root, relative, maximum)
    except FileNotFoundError:
        return None


def _is_own_verification_ledger(relative: str) -> bool:
    """Return whether a path is this operation's own verification record."""
    parts = relative.split("/")
    operation_slug = f"{Path(__file__).stem.replace('_', '-')}-transaction"
    return (
        len(parts) == 5
        and parts[:2] == ["docs", "specs"]
        and parts[2] == operation_slug
        and parts[3:] == ["notes", "verification-ledger.md"]
    )


def derive_citing_paths(
    source_rel: str,
    successor_rel: str | None = None,
    *,
    repository_root: Path | None = None,
    created_paths: Sequence[str] = (),
    _base_commit: str | None = None,
) -> tuple[str, ...]:
    """Return files whose exact bytes cite ``source_rel`` and must be repointed."""
    del successor_rel
    root = _root(repository_root)
    _check_relative_path(source_rel)
    source_bytes = source_rel.encode()
    tracked = _tracked_paths(root, _base_commit)
    tracked_set = set(tracked)
    ordered = list(tracked)
    for relative in created_paths:
        _check_relative_path(relative)
        if relative not in tracked_set and relative not in ordered:
            ordered.append(relative)

    result: list[str] = []
    seen: set[str] = set()
    total_bytes = 0
    for relative in ordered:
        if relative in {source_rel, WORKSPACE_FILE} or _is_own_verification_ledger(
            relative
        ):
            continue
        data = (
            _git_file(root, _base_commit, relative)
            if _base_commit is not None and relative in tracked_set
            else _read_optional_live(root, relative, _MAX_FILE_BYTES)
        )
        if data is None or source_bytes not in data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeError as error:
            raise ValueError("citation-not-text") from error

        projection_source = _projection_source(
            root, relative, tracked, source_bytes, _base_commit
        )
        if projection_source is not None:
            relative, data = projection_source

        if relative in {source_rel, WORKSPACE_FILE}:
            continue
        if relative in seen:
            continue
        total_bytes += len(data)
        if len(result) >= _MAX_WRITES or total_bytes > _MAX_CITING_BYTES:
            raise ValueError("citation-bound")
        seen.add(relative)
        result.append(relative)
    return tuple(result)


def repoint_citation_bytes(data: bytes, source_rel: str, successor_rel: str) -> bytes:
    """Apply the exact path substitution used for every derived postimage."""
    return data.replace(source_rel.encode(), successor_rel.encode())


def _replace_writes(derived: _Derived) -> tuple[_Write, ...]:
    return tuple(item for item in derived.writes if item.action == "replace")


def _paths_dirty(root: Path, paths: Sequence[str]) -> bool:
    """Fail closed unless Git, run with the allowlisted environment, proves ``paths`` clean.

    Clean means every path is tracked with tag ``H`` (not assume-unchanged,
    skip-worktree, or unmerged) and ``git status`` reports nothing for it. The
    allowlisted environment keeps injected Git configuration from changing
    either answer; any Git failure counts as dirty.
    """
    try:
        listing = _git(
            root, ["ls-files", "-v", "-z", "--", *paths], max_bytes=_MAX_FILE_BYTES
        )
        tags: dict[str, list[str]] = {}
        for record in listing.decode("utf-8").split("\0"):
            if len(record) >= 3:
                tags.setdefault(record[2:], []).append(record[0])
        if any(tags.get(path) != ["H"] for path in paths):
            return True
        status_output = _git(
            root, ["status", "--porcelain", "--", *paths], max_bytes=_MAX_FILE_BYTES
        )
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        return True
    return bool(status_output.strip())


def _replacement_targets_are_dirty(root: Path, derived: _Derived) -> bool:
    """Fail closed unless Git proves the source, registry and every target clean.

    The request contract's own dirty check inherits the caller's environment,
    so this independent check covers the same source and registry again.
    """
    paths = list(
        dict.fromkeys(
            [derived.source, WORKSPACE_FILE, *(item.path for item in _replace_writes(derived))]
        )
    )
    return _paths_dirty(root, paths)


def _source_write(derived: _Derived) -> _Write:
    for item in derived.writes:
        if item.path == derived.source and item.action == "replace":
            return item
    raise ValueError("derived-set-mismatch")


def _derive(
    root: Path,
    *,
    operation_id: str,
    base_commit: str,
    source: str,
    target_token: str,
    date: str,
    successor: str | None = None,
    origin_view_sha256: str | None = None,
    pinned_allocation: _PinnedAllocation | None = None,
) -> _Derived:
    if not _OPERATION_RE.fullmatch(operation_id) or _head(root) != base_commit:
        raise ValueError("base-changed")
    allocation = pinned_allocation or _pinned_allocation(
        root, base_commit, source, target_token
    )
    if (
        origin_view_sha256 is not None
        and allocation.origin_view_sha256 != origin_view_sha256
    ):
        raise ValueError("base-changed")
    expected = allocation.successor
    if successor is not None and successor != expected:
        raise ValueError("derived-set-mismatch")
    source_before = _git_file(root, base_commit, source)
    successor_after = repoint_citation_bytes(source_before, source, expected)
    tombstone_after = _tombstone.serialize_tombstone(  # type: ignore[attr-defined]
        _slug_bytes(source_before), date, reissued_as=expected
    )
    if isinstance(tombstone_after, str):
        raise ValueError(tombstone_after)
    source_write = _Write(1, source, "replace", source_before, tombstone_after)
    citation_writes: list[_Write] = []
    for relative in derive_citing_paths(
        source, expected, repository_root=root, _base_commit=base_commit
    ):
        preimage = _git_file(root, base_commit, relative)
        citation_writes.append(
            _Write(
                source_write.order + len(citation_writes) + 1,
                relative,
                "replace",
                preimage,
                repoint_citation_bytes(preimage, source, expected),
            )
        )
    return _Derived(
        operation_id,
        base_commit,
        source,
        target_token,
        date,
        expected,
        allocation.origin_view_sha256,
        (
            _Write(0, expected, "create", None, successor_after),
            source_write,
            *citation_writes,
        ),
    )


def _record(derived: _Derived) -> dict[str, object]:
    return {
        "base_commit": derived.base_commit,
        "operation_id": derived.operation_id,
        "origin_view_sha256": derived.origin_view_sha256,
        "registry": {
            "action": "registry-edit",
            "path": WORKSPACE_FILE,
            "source": derived.source,
            "successor": derived.successor,
        },
        "request": {
            "date": derived.date,
            "source": derived.source,
            "target_token": derived.target_token,
        },
        "version": _RECORD_VERSION,
        "writes": [
            {
                "action": item.action,
                "order": item.order,
                "path": item.path,
                "postimage_sha256": _sha256(item.postimage),
                "preimage_sha256": None if item.preimage is None else _sha256(item.preimage),
            }
            for item in derived.writes
        ],
    }


def _seal(record_bytes: bytes, writes: Sequence[_Write]) -> dict[str, object]:
    return {
        "postimage_sha256": [_sha256(item.postimage) for item in writes],
        "record_sha256": _sha256(record_bytes),
        "version": _RECORD_VERSION,
    }


def _live_mode(root: Path, relative: str) -> int:
    """Return the permission bits of one confined live regular file."""
    path = root / relative
    parent = _open_parent(root, path.parent)
    try:
        inspected = _stat_at(parent, path.name)
    finally:
        os.close(parent)
    if inspected is None or not stat.S_ISREG(inspected.st_mode):
        raise ValueError("unsafe-file")
    return stat.S_IMODE(inspected.st_mode)


def _write_stage(root: Path, derived: _Derived, checkpoint: _Checkpoint) -> _LoadedStage:
    parent = root / INTENTS_PARENT
    parent_fd = _open_parent(root, parent)
    name = f"{_STAGE_PREFIX}{derived.operation_id}"
    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
        os.fsync(parent_fd)
        checkpoint("after-stage-created")
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
        try:
            record_bytes = _canonical_json(_record(derived))
            _create_at(descriptor, _RECORD_NAME, record_bytes)
            checkpoint("after-record")
            successor_mode = _live_mode(root, derived.source)
            for item in derived.writes:
                # The successor is a hard link to its staged file, so that file
                # takes the source's mode; other postimages are only staged copies.
                _create_at(
                    descriptor,
                    item.stage_name,
                    item.postimage,
                    exact_mode=successor_mode if item.action == "create" else None,
                )
                checkpoint(f"after-postimage-{item.order}")
            seal_bytes = _canonical_json(_seal(record_bytes, derived.writes))
            _create_at(descriptor, _SEAL_NAME, seal_bytes)
            checkpoint("after-seal")
        finally:
            os.close(descriptor)
    finally:
        os.close(parent_fd)
    return _LoadedStage(derived, parent / name, record_bytes, seal_bytes)


def _open_stage(root: Path, stage: Path) -> int:
    parent = _open_parent(root, stage.parent)
    try:
        return os.open(
            stage.name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent,
        )
    finally:
        os.close(parent)


def _stage_candidates(root: Path) -> tuple[Path, ...]:
    parent = root / INTENTS_PARENT
    descriptor = _open_parent(root, parent)
    try:
        result: list[Path] = []
        with os.scandir(descriptor) as entries:
            for entry in entries:
                if _STAGE_RE.fullmatch(entry.name) is None:
                    continue
                if len(result) >= _MAX_RECOVERY_CANDIDATES:
                    raise ValueError("recovery-candidate-bound")
                inspected = os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                if not stat.S_ISDIR(inspected.st_mode):
                    raise ValueError("stage-not-directory")
                result.append(parent / entry.name)
        return tuple(sorted(result))
    finally:
        os.close(descriptor)


def _record_request(value: object) -> tuple[str, str, str] | None:
    if not isinstance(value, dict):
        return None
    request = value.get("request")
    if not isinstance(request, dict) or set(request) != {"date", "source", "target_token"}:
        return None
    values = request.get("source"), request.get("target_token"), request.get("date")
    if not all(isinstance(item, str) for item in values):
        return None
    return str(values[0]), str(values[1]), str(values[2])


def _unattributed_stages(root: Path) -> tuple[Path, ...]:
    """Return stages whose own bytes name no request.

    That is an empty or cleanup-only stage, or one whose record is partial or
    invalid. A new transaction must not start beside one and leave it behind;
    the operator resolves it through recovery first.
    """
    result: list[Path] = []
    for stage in _stage_candidates(root):
        descriptor = _open_stage(root, stage)
        try:
            if _RECORD_NAME not in _list_at(descriptor):
                result.append(stage)
                continue
            try:
                data, _ = _read_at(descriptor, _RECORD_NAME, max_bytes=_MAX_RECORD_BYTES)
                if _record_request(_strict_json(data)) is None:
                    result.append(stage)
            except (OSError, UnicodeError, ValueError):
                result.append(stage)
        finally:
            os.close(descriptor)
    return tuple(result)


def _matching_stages(root: Path, source: str, token: str, date: str | None) -> tuple[Path, ...]:
    result: list[Path] = []
    for stage in _stage_candidates(root):
        descriptor = _open_stage(root, stage)
        try:
            if _RECORD_NAME not in _list_at(descriptor):
                continue
            data, _ = _read_at(descriptor, _RECORD_NAME, max_bytes=_MAX_RECORD_BYTES)
            request = _record_request(_strict_json(data))
            if (
                request is not None
                and request[:2] == (source, token)
                and (date is None or request[2] == date)
            ):
                result.append(stage)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            continue
        finally:
            os.close(descriptor)
    return tuple(result)


def _load_stage(root: Path, stage: Path, source: str, token: str, date: str) -> _LoadedStage:
    operation_match = _STAGE_RE.fullmatch(stage.name)
    if operation_match is None:
        raise ValueError("operation-id-invalid")
    descriptor = _open_stage(root, stage)
    try:
        names = _list_at(descriptor)
        record_bytes, _ = _read_at(descriptor, _RECORD_NAME, max_bytes=_MAX_RECORD_BYTES)
        value = _strict_json(record_bytes)
        if not isinstance(value, dict) or set(value) != {
            "base_commit",
            "operation_id",
            "origin_view_sha256",
            "registry",
            "request",
            "version",
            "writes",
        }:
            raise ValueError("record-mismatch")
        base = value.get("base_commit")
        origin_view_sha256 = value.get("origin_view_sha256")
        registry = value.get("registry")
        successor = registry.get("successor") if isinstance(registry, dict) else None
        if (
            not isinstance(base, str)
            or not isinstance(origin_view_sha256, str)
            or not isinstance(successor, str)
        ):
            raise ValueError("record-mismatch")
        derived = _derive(
            root,
            operation_id=operation_match.group(1),
            base_commit=base,
            source=source,
            target_token=token,
            date=date,
            successor=successor,
            origin_view_sha256=origin_view_sha256,
        )
        # Byte equality with the canonical re-derivation: value equality would
        # accept type substitutions that compare equal.
        if record_bytes != _canonical_json(_record(derived)):
            raise ValueError("record-mismatch")
        core = {_RECORD_NAME, _SEAL_NAME, *(item.stage_name for item in derived.writes)}
        runtime = names & {_LOCK_CLAIM_NAME, _CLEANUP_NAME}
        if runtime == {_LOCK_CLAIM_NAME, _CLEANUP_NAME}:
            raise ValueError("stage-entry-set")
        if _CLEANUP_NAME in names:
            allowed_states = [set(core) | {_CLEANUP_NAME}]
            remaining = set(core) | {_CLEANUP_NAME}
            for item in derived.writes:
                remaining.remove(item.stage_name)
                allowed_states.append(set(remaining))
            remaining.remove(_SEAL_NAME)
            allowed_states.append(set(remaining))
            if names not in allowed_states:
                raise ValueError("stage-entry-set")
        elif names != core and names != core | {_LOCK_CLAIM_NAME}:
            raise ValueError("stage-entry-set")
        create = derived.writes[0]
        if create.stage_name in names:
            successor = root / create.path
            parent = _open_parent(root, successor.parent)
            try:
                if (
                    _successor_identity_state(
                        descriptor, create.stage_name, parent, successor.name
                    )
                    == "alien"
                ):
                    raise ValueError("successor-conflict")
            finally:
                os.close(parent)
        for item in derived.writes:
            if item.stage_name not in names:
                continue
            links = (1, 2) if item.action == "create" else (1,)
            data, _ = _read_at(descriptor, item.stage_name, max_bytes=_MAX_FILE_BYTES, links=links)
            if data != item.postimage:
                raise ValueError("postimage-mismatch")
        expected_seal = _canonical_json(_seal(record_bytes, derived.writes))
        if _SEAL_NAME in names:
            seal_bytes, _ = _read_at(descriptor, _SEAL_NAME, max_bytes=_MAX_SEAL_BYTES)
            if seal_bytes != expected_seal:
                raise ValueError("seal-invalid")
        elif _CLEANUP_NAME in names:
            seal_bytes = expected_seal
        else:
            raise ValueError("seal-invalid")
        return _LoadedStage(derived, stage, record_bytes, seal_bytes)
    finally:
        os.close(descriptor)


def _read_live(root: Path, relative: str, maximum: int) -> bytes:
    path = root / relative
    descriptor = _open_parent(root, path.parent)
    try:
        return _read_at(descriptor, path.name, max_bytes=maximum)[0]
    finally:
        os.close(descriptor)


def _check_relative_path(relative: str) -> None:
    path = Path(relative)
    if (
        path.is_absolute()
        or not relative
        or any(ord(character) < 32 or ord(character) == 127 for character in relative)
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("path-unconfined")


def _read_preamble_text(root: Path, relative: str) -> str:
    """Read only enough of one confined regular file to classify its preamble."""
    _check_relative_path(relative)
    path = root / relative
    descriptor = _open_parent(root, path.parent)
    try:
        opened = os.open(path.name, _READ_FLAGS, dir_fd=descriptor)
        try:
            inspected = os.fstat(opened)
            if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink != 1:
                raise ValueError("unsafe-file")
            # The preamble is the run of visible lines before the first `## `
            # heading, as the shared shape reader defines it. Lines are decoded
            # one at a time and reading stops at that heading, so no byte of
            # the body is decoded or classified.
            preamble: list[str] = []
            pending = b""
            held = 0
            inside_comment = False
            finished = False
            while not finished:
                chunk = os.read(opened, 4096)
                pending += chunk
                if chunk:
                    *lines, pending = pending.split(b"\n")
                else:
                    lines, pending, finished = [pending], b"", True
                for raw in lines:
                    line = raw.decode("utf-8").removesuffix("\r")
                    visible, inside_comment = _shape._visible_line_outside_comments(  # type: ignore[attr-defined]
                        line, inside_comment
                    )
                    if visible.startswith(_shape._HEADING):  # type: ignore[attr-defined]
                        finished = True
                        break
                    preamble.append(line)
                    held += len(raw) + 1
                if held + len(pending) > _MAX_PREAMBLE_BYTES:
                    raise ValueError("preamble-bound")
            after = os.fstat(opened)
            if (inspected.st_dev, inspected.st_ino) != (after.st_dev, after.st_ino):
                raise ValueError("identity-changed")
            return "\n".join(preamble) + ("\n" if preamble else "")
        finally:
            os.close(opened)
    finally:
        os.close(descriptor)


def _registry_state(data: bytes, source: str, successor: str) -> str:
    parsed = tomllib.loads(data.decode("utf-8"))
    source_count = _request._count_registry_matches(parsed, source)  # type: ignore[attr-defined]
    successor_count = _request._count_registry_matches(parsed, successor)  # type: ignore[attr-defined]
    source_occurrences = data.count(source.encode())
    successor_occurrences = data.count(successor.encode())
    if source_count == 1 and successor_count == 0 and source_occurrences >= 1:
        return "before"
    if (
        source_count == 0
        and successor_count == 1
        and source_occurrences == 0
        and successor_occurrences >= 1
    ):
        return "after"
    return "alien"


def _merge_backward_workspace(
    data: bytes,
    pinned_preimage: bytes,
    source: str,
    successor: str,
) -> bytes:
    """Reverse only the registry edits derived from the pinned Git preimage."""
    if _registry_state(pinned_preimage, source, successor) != "before":
        raise ValueError("registry-preimage")
    source_bytes = source.encode()
    successor_bytes = successor.encode()
    pieces: list[bytes] = []
    owned_spans: list[tuple[int, int]] = []
    cursor = 0
    derived_size = 0
    while True:
        occurrence = pinned_preimage.find(source_bytes, cursor)
        if occurrence < 0:
            pieces.append(pinned_preimage[cursor:])
            break
        prefix = pinned_preimage[cursor:occurrence]
        pieces.extend((prefix, successor_bytes))
        derived_size += len(prefix)
        owned_spans.append((derived_size, derived_size + len(successor_bytes)))
        derived_size += len(successor_bytes)
        cursor = occurrence + len(source_bytes)
    if not owned_spans:
        raise ValueError("registry-preimage")
    derived_postimage = b"".join(pieces)
    if _registry_state(derived_postimage, source, successor) != "after":
        raise ValueError("registry-preimage")
    if data == derived_postimage:
        # Nothing else edited the registry after the forward edit, so the
        # pinned preimage is the exact restoration, repeated lines included.
        # The line merge below is needed only to preserve unrelated edits.
        return pinned_preimage

    derived_lines = derived_postimage.splitlines(keepends=True)
    current_lines = data.splitlines(keepends=True)
    if (
        len(derived_lines) > _MAX_REGISTRY_MERGE_LINES
        or len(current_lines) > _MAX_REGISTRY_MERGE_LINES
    ):
        raise ValueError("registry-transition")
    derived_offsets = [0]
    current_offsets = [0]
    for line in derived_lines:
        derived_offsets.append(derived_offsets[-1] + len(line))
    for line in current_lines:
        current_offsets.append(current_offsets[-1] + len(line))

    derived_counts: dict[bytes, int] = {}
    current_counts: dict[bytes, int] = {}
    for line in derived_lines:
        derived_counts[line] = derived_counts.get(line, 0) + 1
    for line in current_lines:
        current_counts[line] = current_counts.get(line, 0) + 1
    owned_lines: set[bytes] = set()
    for index, line in enumerate(derived_lines):
        line_start = derived_offsets[index]
        line_end = derived_offsets[index + 1]
        if any(start < line_end and line_start < end for start, end in owned_spans):
            owned_lines.add(line)
    if any(
        derived_counts[line] != 1 or current_counts.get(line) != 1
        for line in owned_lines
    ):
        raise ValueError("registry-transition")

    restored: set[tuple[int, int]] = set()
    merged: list[bytes] = []
    matcher = difflib.SequenceMatcher(None, derived_lines, current_lines)
    for tag, first_start, first_end, second_start, second_end in matcher.get_opcodes():
        derived_start = derived_offsets[first_start]
        derived_end = derived_offsets[first_end]
        current_start = current_offsets[second_start]
        current_end = current_offsets[second_end]
        touched = [
            span
            for span in owned_spans
            if span[0] < derived_end and derived_start < span[1]
        ]
        if tag != "equal":
            if touched:
                raise ValueError("registry-transition")
            merged.append(data[current_start:current_end])
            continue

        position = derived_start
        for span_start, span_end in touched:
            if span_start < derived_start or span_end > derived_end:
                raise ValueError("registry-transition")
            merged.append(derived_postimage[position:span_start])
            merged.append(source_bytes)
            restored.add((span_start, span_end))
            position = span_end
        merged.append(derived_postimage[position:derived_end])

    changed = b"".join(merged)
    if restored != set(owned_spans) or len(changed) > _MAX_WORKSPACE_BYTES:
        raise ValueError("registry-transition")
    return changed


def _workspace_transition(
    data: bytes,
    source: str,
    successor: str,
    direction: str,
    *,
    pinned_preimage: bytes | None = None,
) -> bytes:
    expected, wanted = ("before", "after") if direction == "forward" else ("after", "before")
    if _registry_state(data, source, successor) != expected:
        raise ValueError("registry-state")
    if direction == "forward":
        changed = data.replace(source.encode(), successor.encode())
    elif pinned_preimage is not None:
        changed = _merge_backward_workspace(data, pinned_preimage, source, successor)
    else:
        raise ValueError("registry-preimage")
    if len(changed) > _MAX_WORKSPACE_BYTES:
        raise ValueError("registry-bound")
    # A forward image must stay within what the backward merge accepts, or a
    # committed rename could not be rolled back. This also runs under the lock,
    # so a concurrent edit after admission cannot carry the image past it.
    if direction == "forward" and (
        len(changed.splitlines(keepends=True)) > _MAX_REGISTRY_MERGE_LINES
    ):
        raise ValueError("registry-bound")
    if _registry_state(changed, source, successor) != wanted:
        raise ValueError("registry-transition")
    if direction == "back" and changed.replace(source.encode(), successor.encode()) != data:
        raise ValueError("registry-transition")
    return changed


def _stage_budget_refused(derived: _Derived, workspace: bytes) -> bool:
    """Refuse before staging unless every artifact fits the bound its reader applies.

    Recovery reads the record, seal, staged postimages, live results and the
    registry under fixed ceilings. An artifact admitted past one would leave a
    sealed partial that no recovery can load, so each is checked here, with the
    record run through the same parser recovery uses.
    """
    if len(derived.writes) > _MAX_WRITES:
        return True
    record_bytes = _canonical_json(_record(derived))
    seal_bytes = _canonical_json(_seal(record_bytes, derived.writes))
    if len(record_bytes) > _MAX_RECORD_BYTES or len(seal_bytes) > _MAX_SEAL_BYTES:
        return True
    try:
        _strict_json(record_bytes)
        _workspace_transition(workspace, derived.source, derived.successor, "forward")
    except ValueError:
        return True
    postimages = [item.postimage for item in derived.writes]
    return (
        any(len(data) > _MAX_FILE_BYTES for data in postimages)
        or sum(len(data) for data in postimages) > _MAX_CITING_BYTES
    )


def _temp_name(operation_id: str, order: int) -> str:
    return f".intent-rename-{operation_id}-{order:04d}.tmp"


def _temporary_targets(derived: _Derived) -> tuple[tuple[str, int], ...]:
    """Return every exact live-parent temporary the transaction can own."""
    return (
        *((item.path, item.order) for item in _replace_writes(derived)),
        (WORKSPACE_FILE, len(derived.writes)),
    )


def _successor_identity_state(
    stage_descriptor: int,
    staged_name: str,
    live_parent_descriptor: int,
    live_name: str,
) -> Literal["before", "after", "alien"]:
    """Classify only the two identity states that grant successor authority."""
    staged = _stat_at(stage_descriptor, staged_name)
    live = _stat_at(live_parent_descriptor, live_name)
    if staged is None or not stat.S_ISREG(staged.st_mode):
        return "alien"
    if live is None:
        return "before" if staged.st_nlink == 1 else "alien"
    if (
        staged.st_nlink == 2
        and stat.S_ISREG(live.st_mode)
        and live.st_nlink == 2
        and _same_inode(staged, live)
    ):
        return "after"
    return "alien"


def _validate_targets(root: Path, loaded: _LoadedStage) -> tuple[str, str]:
    derived = loaded.derived
    replace_states: list[str] = []
    for item in _replace_writes(derived):
        data = _read_live(root, item.path, _MAX_FILE_BYTES)
        state = (
            "before"
            if data == item.preimage
            else "after"
            if data == item.postimage
            else "alien"
        )
        if state == "alien":
            raise ValueError("target-alien")
        replace_states.append(state)
    stage_fd = _open_stage(root, loaded.stage)
    successor_path = root / derived.successor
    parent = _open_parent(root, successor_path.parent)
    try:
        successor_state = _successor_identity_state(
            stage_fd,
            derived.writes[0].stage_name,
            parent,
            successor_path.name,
        )
    finally:
        os.close(parent)
        os.close(stage_fd)
    if successor_state == "alien":
        raise ValueError("successor-conflict")
    workspace = _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
    registry = _registry_state(workspace, derived.source, derived.successor)
    if registry == "alien":
        raise ValueError("registry-alien")
    for relative, order in _temporary_targets(derived):
        path = root / relative
        parent = _open_parent(root, path.parent)
        try:
            temporary = _stat_at(parent, _temp_name(derived.operation_id, order))
            if temporary is not None and (
                not stat.S_ISREG(temporary.st_mode) or temporary.st_nlink != 1
            ):
                raise ValueError("temporary-alien")
        finally:
            os.close(parent)
    terminal = (
        "before"
        if all(state == "before" for state in replace_states)
        and successor_state == registry == "before"
        else "after"
        if all(state == "after" for state in replace_states)
        and successor_state == registry == "after"
        else "partial"
    )
    return terminal, registry


def _remove_temporaries(root: Path, derived: _Derived) -> None:
    for relative, order in _temporary_targets(derived):
        path = root / relative
        parent = _open_parent(root, path.parent)
        try:
            name = _temp_name(derived.operation_id, order)
            inspected = _stat_at(parent, name)
            if inspected is not None:
                if not stat.S_ISREG(inspected.st_mode) or inspected.st_nlink != 1:
                    raise ValueError("temporary-alien")
                os.unlink(name, dir_fd=parent)
                os.fsync(parent)
        finally:
            os.close(parent)


def _replace_at(
    root: Path,
    relative: str,
    data: bytes,
    operation_id: str,
    order: int,
    checkpoint: _Checkpoint,
    *,
    before_replace: Callable[[], None] | None = None,
) -> None:
    """Replace one live file through a same-parent temporary.

    ``before_replace`` runs immediately before the live ``os.replace``, after the
    temporary is written, so a precondition is proven at the mutation point.
    """
    path = root / relative
    parent = _open_parent(root, path.parent)
    try:
        temporary = _temp_name(operation_id, order)
        # A replacement keeps the live file's permission bits, so a rename and
        # its rollback leave every affected file's mode as it was.
        existing = _stat_at(parent, path.name)
        exact_mode = (
            stat.S_IMODE(existing.st_mode)
            if existing is not None and stat.S_ISREG(existing.st_mode)
            else 0o644
        )
        _create_at(parent, temporary, data, exact_mode=exact_mode)
        checkpoint(f"after-temporary-{order}")
        if before_replace is not None:
            before_replace()
        os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
        checkpoint(f"after-replace-{order}")
    finally:
        os.close(parent)


def _pid_is_dead(payload: bytes) -> bool:
    if _PID_RE.fullmatch(payload) is None or int(payload) > _MAX_PID:
        raise ValueError("lock-pid-invalid")
    try:
        os.kill(int(payload), 0)
    except OverflowError as error:
        raise ValueError("lock-pid-invalid") from error
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False


def _normalise_old_claim(root: Path, loaded: _LoadedStage) -> None:
    stage_fd = _open_stage(root, loaded.stage)
    root_fd = _open_parent(root, root)
    try:
        claim = _stat_at(stage_fd, _LOCK_CLAIM_NAME)
        shared = _stat_at(root_fd, WORKSPACE_LOCK_FILE)
        if claim is None:
            if shared is not None:
                raise ValueError("lock-busy")
            return
        if not stat.S_ISREG(claim.st_mode) or claim.st_nlink not in (1, 2):
            raise ValueError("lock-claim-alien")
        payload, _ = _read_at(stage_fd, _LOCK_CLAIM_NAME, max_bytes=20, links=(claim.st_nlink,))
        if shared is None:
            if claim.st_nlink != 1:
                raise ValueError("lock-claim-alien")
            os.unlink(_LOCK_CLAIM_NAME, dir_fd=stage_fd)
            os.fsync(stage_fd)
            return
        if (
            not stat.S_ISREG(shared.st_mode)
            or claim.st_nlink != 2
            or not _same_inode(claim, shared)
        ):
            raise ValueError("lock-foreign")
        if not _pid_is_dead(payload):
            raise ValueError("lock-active")
        # The dead-owner check takes time. Prove the whole state again
        # immediately before the unlink, so a lock another writer took in
        # between is refused rather than removed by name.
        current_claim = _stat_at(stage_fd, _LOCK_CLAIM_NAME)
        current_shared = _stat_at(root_fd, WORKSPACE_LOCK_FILE)
        if (
            current_claim is None
            or current_shared is None
            or not stat.S_ISREG(current_claim.st_mode)
            or not stat.S_ISREG(current_shared.st_mode)
            or current_claim.st_nlink != 2
            or current_shared.st_nlink != 2
            or not _same_inode(current_claim, claim)
            or not _same_inode(current_shared, current_claim)
        ):
            raise ValueError("lock-foreign")
        current_payload, _ = _read_at(root_fd, WORKSPACE_LOCK_FILE, max_bytes=20, links=(2,))
        if current_payload != payload or not _pid_is_dead(current_payload):
            raise ValueError("lock-foreign")
        os.unlink(WORKSPACE_LOCK_FILE, dir_fd=root_fd)
        os.fsync(root_fd)
        os.unlink(_LOCK_CLAIM_NAME, dir_fd=stage_fd)
        os.fsync(stage_fd)
    finally:
        os.close(root_fd)
        os.close(stage_fd)


def _acquire_claim(root: Path, loaded: _LoadedStage, checkpoint: _Checkpoint) -> None:
    stage_fd = _open_stage(root, loaded.stage)
    root_fd = _open_parent(root, root)
    linked = False
    try:
        _create_at(stage_fd, _LOCK_CLAIM_NAME, str(os.getpid()).encode("ascii"))
        checkpoint("after-lock-claim")
        try:
            os.link(
                _LOCK_CLAIM_NAME,
                WORKSPACE_LOCK_FILE,
                src_dir_fd=stage_fd,
                dst_dir_fd=root_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            os.unlink(_LOCK_CLAIM_NAME, dir_fd=stage_fd)
            os.fsync(stage_fd)
            raise ValueError("lock-busy") from None
        linked = True
        os.fsync(root_fd)
        checkpoint("after-lock-link")
    except InjectedInterruption:
        raise
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        if linked:
            _release_claim_after_failure(root, loaded)
        raise
    finally:
        os.close(root_fd)
        os.close(stage_fd)


def _claim_is_owned(root: Path, loaded: _LoadedStage) -> bool:
    """Prove the shared lock is still this operation's: one inode, two links, our PID."""
    stage_fd = _open_stage(root, loaded.stage)
    root_fd = _open_parent(root, root)
    try:
        claim = _stat_at(stage_fd, _LOCK_CLAIM_NAME)
        shared = _stat_at(root_fd, WORKSPACE_LOCK_FILE)
        if (
            claim is None
            or shared is None
            or not stat.S_ISREG(claim.st_mode)
            or not stat.S_ISREG(shared.st_mode)
            or claim.st_nlink != 2
            or shared.st_nlink != 2
            or not _same_inode(claim, shared)
        ):
            return False
        payload, read = _read_at(root_fd, WORKSPACE_LOCK_FILE, max_bytes=20, links=(2,))
        return payload == str(os.getpid()).encode("ascii") and _same_inode(read, claim)
    except (OSError, ValueError):
        return False
    finally:
        os.close(root_fd)
        os.close(stage_fd)


def _release_claim(root: Path, loaded: _LoadedStage) -> None:
    stage_fd = _open_stage(root, loaded.stage)
    root_fd = _open_parent(root, root)
    try:
        claim = _stat_at(stage_fd, _LOCK_CLAIM_NAME)
        shared = _stat_at(root_fd, WORKSPACE_LOCK_FILE)
        if (
            claim is None
            or shared is None
            or not stat.S_ISREG(claim.st_mode)
            or not stat.S_ISREG(shared.st_mode)
            or claim.st_nlink != 2
            or shared.st_nlink != 2
            or not _same_inode(claim, shared)
        ):
            raise ValueError("lock-identity-lost")
        claim_payload, read_claim = _read_at(
            stage_fd, _LOCK_CLAIM_NAME, max_bytes=20, links=(2,)
        )
        shared_payload, read_shared = _read_at(
            root_fd, WORKSPACE_LOCK_FILE, max_bytes=20, links=(2,)
        )
        expected_payload = str(os.getpid()).encode("ascii")
        current_claim = _stat_at(stage_fd, _LOCK_CLAIM_NAME)
        current_shared = _stat_at(root_fd, WORKSPACE_LOCK_FILE)
        if (
            claim_payload != expected_payload
            or shared_payload != expected_payload
            or not _same_inode(claim, read_claim)
            or not _same_inode(shared, read_shared)
            or not _same_inode(read_claim, read_shared)
            or current_claim is None
            or current_shared is None
            or not stat.S_ISREG(current_claim.st_mode)
            or not stat.S_ISREG(current_shared.st_mode)
            or current_claim.st_nlink != 2
            or current_shared.st_nlink != 2
            or not _same_inode(current_claim, current_shared)
            or not _same_inode(read_claim, current_claim)
            or not _same_inode(read_shared, current_shared)
        ):
            raise ValueError("lock-identity-lost")
        os.unlink(WORKSPACE_LOCK_FILE, dir_fd=root_fd)
        os.fsync(root_fd)
        os.unlink(_LOCK_CLAIM_NAME, dir_fd=stage_fd)
        os.fsync(stage_fd)
    finally:
        os.close(root_fd)
        os.close(stage_fd)


def _release_claim_after_failure(root: Path, loaded: _LoadedStage) -> None:
    """Release only this operation's lock or retain recoverable partial state."""
    try:
        _release_claim(root, loaded)
    except (OSError, ValueError) as error:
        raise _RegistryLockPartial(loaded.derived.operation_id) from error


def _edit_registry(
    root: Path,
    loaded: _LoadedStage,
    direction: Literal["forward", "back"],
    checkpoint: _Checkpoint,
) -> None:
    _acquire_claim(root, loaded, checkpoint)
    try:
        data = _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
        wanted = "after" if direction == "forward" else "before"
        current = _registry_state(data, loaded.derived.source, loaded.derived.successor)
        checkpoint("before-registry")
        if current != wanted:
            changed = (
                _backward_workspace_candidate(root, loaded, data)
                if direction == "back"
                else _workspace_transition(
                    data,
                    loaded.derived.source,
                    loaded.derived.successor,
                    direction,
                )
            )

            def prove_lock_still_owned() -> None:
                # Proven at the live replace itself. If the lock is no longer
                # ours, stop with the recoverable partial and leave the registry
                # untouched; it is not released, since it may not be ours.
                if not _claim_is_owned(root, loaded):
                    raise _RegistryLockPartial(loaded.derived.operation_id)

            _replace_at(
                root,
                WORKSPACE_FILE,
                changed,
                loaded.derived.operation_id,
                len(loaded.derived.writes),
                checkpoint,
                before_replace=prove_lock_still_owned,
            )
        checkpoint("after-registry")
    except InjectedInterruption:
        raise
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        _release_claim_after_failure(root, loaded)
        raise
    _release_claim_after_failure(root, loaded)
    checkpoint("after-lock-release")


def _backward_workspace_candidate(
    root: Path, loaded: _LoadedStage, data: bytes
) -> bytes:
    """Derive a backward registry candidate without mutating the live tree."""
    pinned_preimage = _git_file(
        root,
        loaded.derived.base_commit,
        WORKSPACE_FILE,
        max_bytes=_MAX_WORKSPACE_BYTES,
    )
    return _workspace_transition(
        data,
        loaded.derived.source,
        loaded.derived.successor,
        "back",
        pinned_preimage=pinned_preimage,
    )


def _apply_forward(root: Path, loaded: _LoadedStage, checkpoint: _Checkpoint) -> None:
    derived = loaded.derived
    _, registry = _validate_targets(root, loaded)
    _remove_temporaries(root, derived)
    stage_fd = _open_stage(root, loaded.stage)
    successor = root / derived.successor
    parent = _open_parent(root, successor.parent)
    try:
        successor_state = _successor_identity_state(
            stage_fd,
            derived.writes[0].stage_name,
            parent,
            successor.name,
        )
        if successor_state == "before":
            os.link(
                derived.writes[0].stage_name,
                successor.name,
                src_dir_fd=stage_fd,
                dst_dir_fd=parent,
                follow_symlinks=False,
            )
            os.fsync(parent)
            checkpoint("after-successor")
        elif successor_state == "alien":
            raise ValueError("successor-conflict")
    finally:
        os.close(parent)
        os.close(stage_fd)
    for item in _replace_writes(derived):
        current = _read_live(root, item.path, _MAX_FILE_BYTES)
        if current == item.preimage:
            _replace_at(
                root,
                item.path,
                item.postimage,
                derived.operation_id,
                item.order,
                checkpoint,
            )
        elif current != item.postimage:
            raise ValueError("target-alien")
    if registry != "after":
        _edit_registry(root, loaded, "forward", checkpoint)
    if _validate_targets(root, loaded)[0] != "after":
        raise ValueError("terminal-validation")
    checkpoint("after-terminal-validation")


def _apply_back(root: Path, loaded: _LoadedStage, checkpoint: _Checkpoint) -> None:
    derived = loaded.derived
    _, registry = _validate_targets(root, loaded)
    if registry != "before":
        _backward_workspace_candidate(
            root, loaded, _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
        )
    # The successor goes first, by exact identity, so an alien link state is
    # refused before any other live file is rolled back.
    successor = root / derived.successor
    stage_fd = _open_stage(root, loaded.stage)
    parent = _open_parent(root, successor.parent)
    try:
        state = _successor_identity_state(
            stage_fd, derived.writes[0].stage_name, parent, successor.name
        )
        if state == "alien":
            raise ValueError("successor-conflict")
        if state == "after":
            os.unlink(successor.name, dir_fd=parent)
            os.fsync(parent)
            checkpoint("after-successor-remove")
    finally:
        os.close(parent)
        os.close(stage_fd)
    _remove_temporaries(root, derived)
    if registry != "before":
        _edit_registry(root, loaded, "back", checkpoint)
    for item in reversed(_replace_writes(derived)):
        current = _read_live(root, item.path, _MAX_FILE_BYTES)
        if current == item.postimage:
            assert item.preimage is not None
            _replace_at(
                root,
                item.path,
                item.preimage,
                derived.operation_id,
                item.order,
                checkpoint,
            )
        elif current != item.preimage:
            raise ValueError("target-alien")
    if _validate_targets(root, loaded)[0] != "before":
        raise ValueError("terminal-validation")
    checkpoint("after-terminal-validation")


def _cleanup_payload(loaded: _LoadedStage, direction: str) -> bytes:
    return _canonical_json({
        "completion_seal_sha256": _sha256(loaded.seal_bytes),
        "direction": direction,
        "operation_id": loaded.derived.operation_id,
        "record_sha256": _sha256(loaded.record_bytes),
        "version": _RECORD_VERSION,
    })


def _write_cleanup(
    root: Path, loaded: _LoadedStage, direction: str, checkpoint: _Checkpoint
) -> None:
    descriptor = _open_stage(root, loaded.stage)
    try:
        _create_at(descriptor, _CLEANUP_NAME, _cleanup_payload(loaded, direction))
    finally:
        os.close(descriptor)
    checkpoint("after-cleanup-marker")


def _existing_cleanup_direction(root: Path, loaded: _LoadedStage) -> str | None:
    """Return the valid terminal direction named by an existing marker."""
    descriptor = _open_stage(root, loaded.stage)
    try:
        if _CLEANUP_NAME not in _list_at(descriptor):
            return None
        data, _ = _read_at(descriptor, _CLEANUP_NAME, max_bytes=_MAX_CLEANUP_BYTES)
    finally:
        os.close(descriptor)
    for direction in ("forward", "back"):
        if data == _cleanup_payload(loaded, direction):
            return direction
    # A marker killed while being written names no direction. It is written
    # only after terminal validation, so the live tree is in exactly one
    # terminal state; that state, proven again here, is the direction. Any
    # other non-canonical marker is altered and refused.
    if not any(
        _is_torn(data, _cleanup_payload(loaded, direction))
        for direction in ("forward", "back")
    ):
        raise ValueError("cleanup-invalid")
    proven = [
        direction
        for direction in ("forward", "back")
        if _terminal_state_holds(root, loaded, direction)
    ]
    if len(proven) != 1:
        raise ValueError("cleanup-invalid")
    return proven[0]


def _restore_canonical_cleanup(
    root: Path, loaded: _LoadedStage, direction: str, checkpoint: _Checkpoint
) -> None:
    """Replace a torn marker with the canonical one for a proven terminal state.

    Only stage metadata changes. A kill between the two steps leaves a sealed
    stage with no marker, which recovery treats as not yet marked.
    """
    expected = _cleanup_payload(loaded, direction)
    descriptor = _open_stage(root, loaded.stage)
    try:
        current, _ = _read_at(descriptor, _CLEANUP_NAME, max_bytes=_MAX_CLEANUP_BYTES)
        if current == expected:
            return
        os.unlink(_CLEANUP_NAME, dir_fd=descriptor)
        os.fsync(descriptor)
        checkpoint("after-torn-cleanup-removed")
    finally:
        os.close(descriptor)
    _write_cleanup(root, loaded, direction, checkpoint)


def _is_torn(data: bytes | None, canonical: bytes) -> bool:
    """Report whether ``data`` is what a kill mid-write leaves: a proper prefix.

    Anything else that differs from the canonical bytes is not a torn write
    but an altered artifact, and keeps its refusal.
    """
    return data is not None and len(data) < len(canonical) and canonical.startswith(data)


def _terminal_state_holds(root: Path, loaded: _LoadedStage, direction: str) -> bool:
    try:
        _validate_terminal_bytes(root, loaded, direction)
    except (OSError, UnicodeError, ValueError):
        return False
    return True


def _validate_terminal_bytes(root: Path, loaded: _LoadedStage, direction: str) -> None:
    """Revalidate a terminal state after retained identities are disposed."""
    derived = loaded.derived
    for item in _replace_writes(derived):
        expected = item.postimage if direction == "forward" else item.preimage
        if expected is None or _read_live(root, item.path, _MAX_FILE_BYTES) != expected:
            raise ValueError("cleanup-state-invalid")
    successor = root / derived.successor
    parent = _open_parent(root, successor.parent)
    try:
        inspected = _stat_at(parent, successor.name)
        if direction == "forward":
            if inspected is None or not stat.S_ISREG(inspected.st_mode):
                raise ValueError("cleanup-state-invalid")
            successor_bytes, _ = _read_at(
                parent, successor.name, max_bytes=_MAX_FILE_BYTES, links=(1, 2)
            )
            if successor_bytes != derived.writes[0].postimage:
                raise ValueError("cleanup-state-invalid")
        elif inspected is not None:
            raise ValueError("cleanup-state-invalid")
    finally:
        os.close(parent)
    workspace = _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
    wanted = "after" if direction == "forward" else "before"
    if _registry_state(workspace, derived.source, derived.successor) != wanted:
        raise ValueError("cleanup-state-invalid")


def _dispose(root: Path, loaded: _LoadedStage, direction: str, checkpoint: _Checkpoint) -> None:
    descriptor = _open_stage(root, loaded.stage)
    try:
        cleanup, _ = _read_at(descriptor, _CLEANUP_NAME, max_bytes=_MAX_CLEANUP_BYTES)
        if cleanup != _cleanup_payload(loaded, direction):
            raise ValueError("cleanup-invalid")
        for item in loaded.derived.writes:
            if _stat_at(descriptor, item.stage_name) is not None:
                os.unlink(item.stage_name, dir_fd=descriptor)
                os.fsync(descriptor)
                checkpoint(f"after-dispose-postimage-{item.order}")
        if _stat_at(descriptor, _SEAL_NAME) is not None:
            os.unlink(_SEAL_NAME, dir_fd=descriptor)
            os.fsync(descriptor)
            checkpoint("after-dispose-seal")
        os.unlink(_RECORD_NAME, dir_fd=descriptor)
        os.fsync(descriptor)
        checkpoint("after-dispose-record")
        os.unlink(_CLEANUP_NAME, dir_fd=descriptor)
        os.fsync(descriptor)
        checkpoint("after-dispose-cleanup")
    finally:
        os.close(descriptor)
    parent = _open_parent(root, loaded.stage.parent)
    try:
        _remove_empty_stage(parent, loaded.stage.name)
        os.fsync(parent)
    finally:
        os.close(parent)
    checkpoint("after-stage-cleanup")


def _discard_unsealed_before(root: Path, stage: Path, derived: _Derived) -> bool:
    workspace = _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
    successor = root / derived.successor
    parent = _open_parent(root, successor.parent)
    try:
        all_before = (
            all(
                _read_live(root, item.path, _MAX_FILE_BYTES) == item.preimage
                for item in _replace_writes(derived)
            )
            and _stat_at(parent, successor.name) is None
            and _registry_state(workspace, derived.source, derived.successor) == "before"
        )
    finally:
        os.close(parent)
    if not all_before:
        return False
    descriptor = _open_stage(root, stage)
    try:
        names = _list_at(descriptor)
        allowed = {_RECORD_NAME, _SEAL_NAME, *(item.stage_name for item in derived.writes)}
        if not names <= allowed or _RECORD_NAME not in names:
            return False
        for name in sorted(names - {_RECORD_NAME}):
            if _read_at(descriptor, name, max_bytes=_MAX_FILE_BYTES)[1].st_nlink != 1:
                return False
        for name in sorted(names - {_RECORD_NAME}):
            os.unlink(name, dir_fd=descriptor)
        os.unlink(_RECORD_NAME, dir_fd=descriptor)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = _open_parent(root, stage.parent)
    try:
        _remove_empty_stage(parent, stage.name)
        os.fsync(parent)
    finally:
        os.close(parent)
    return True


def _root(repository_root: Path | None) -> Path:
    root = (repository_root or Path.cwd()).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root-unresolved")
    return root


def run_intent_rename(
    source_rel: str,
    target_token: str,
    *,
    repository_root: Path | None = None,
    _checkpoint: _Checkpoint = _noop_checkpoint,
    _today: _Today = _today,
) -> RenameResult:
    """Apply a rename or leave exactly one sealed operation for recovery."""
    operation_id: str | None = None
    if _filesystem_unsupported():
        return RenameResult(RenameStatus.REFUSED, "filesystem-unsupported")
    if _git_environment_redirected():
        return RenameResult(RenameStatus.REFUSED, "git-environment-redirected")
    try:
        root = _root(repository_root)
        existing = _matching_stages(root, source_rel, target_token, None)
        if len(existing) > 1:
            return RenameResult(RenameStatus.REFUSED, "recovery-ambiguous")
        if not existing:
            existing = _unattributed_stages(root)[:1]
        if existing:
            match = _STAGE_RE.fullmatch(existing[0].name)
            return RenameResult(
                RenameStatus.REFUSED, "recovery-required", match.group(1) if match else None
            )
        request = _request.validate_rename_request(source_rel, target_token, repository_root=root)  # type: ignore[attr-defined]
        if isinstance(request, str):
            return RenameResult(RenameStatus.REFUSED, request)
        date = _today().isoformat()
        base = _head(root)
        try:
            allocation = _pinned_allocation(root, base, source_rel, target_token)
        except ValueError as error:
            if str(error) != "allocation-refused":
                raise
            return RenameResult(RenameStatus.REFUSED, "allocation-refused")
        successor = allocation.successor
        successor_path = root / successor
        parent = _open_parent(root, successor_path.parent)
        try:
            if _stat_at(parent, successor_path.name) is not None:
                return RenameResult(RenameStatus.REFUSED, "successor-exists")
        finally:
            os.close(parent)
        # Absent from the working tree is not enough: a successor name staged in
        # the index or tracked at the pinned base would be overwritten or left
        # dirty by the create, so it is refused as occupied.
        if _git(
            root, ["ls-files", "-z", "--", successor], max_bytes=_MAX_FILE_BYTES
        ) or _git(
            root,
            ["ls-tree", "-z", "--name-only", base, "--", successor],
            max_bytes=_MAX_FILE_BYTES,
        ):
            return RenameResult(RenameStatus.REFUSED, "successor-exists")
        operation_id = secrets.token_hex(16)
        derived = _derive(
            root,
            operation_id=operation_id,
            base_commit=base,
            source=source_rel,
            target_token=target_token,
            date=date,
            successor=successor,
            pinned_allocation=allocation,
        )
        if _replacement_targets_are_dirty(root, derived):
            return RenameResult(RenameStatus.REFUSED, "path-dirty")
        for item in _replace_writes(derived):
            if _read_live(root, item.path, _MAX_FILE_BYTES) != item.preimage:
                return RenameResult(RenameStatus.REFUSED, "path-dirty")
        # The write set is derived from committed bytes. A dirty tracked file
        # that cites the source only in its live bytes would escape the
        # sweep, so it is refused as a dirty affected path.
        planned = {item.path for item in _replace_writes(derived)}
        if set(derive_citing_paths(source_rel, repository_root=root)) - planned:
            return RenameResult(RenameStatus.REFUSED, "path-dirty")
        workspace = _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
        if _registry_state(workspace, derived.source, derived.successor) != "before":
            return RenameResult(RenameStatus.REFUSED, "registry-ambiguous")
        # Recovery refuses outright past its candidate bound, so a new stage
        # may not be the one that crosses it.
        if _stage_budget_refused(derived, workspace) or (
            len(_stage_candidates(root)) >= _MAX_RECOVERY_CANDIDATES
        ):
            return RenameResult(RenameStatus.REFUSED, "stage-budget")
        loaded = _write_stage(root, derived, _checkpoint)
        _validate_targets(root, loaded)
        _checkpoint("before-commit")
        _apply_forward(root, loaded, _checkpoint)
        _write_cleanup(root, loaded, "forward", _checkpoint)
        _dispose(root, loaded, "forward", _checkpoint)
        return RenameResult(RenameStatus.COMMITTED, "committed", operation_id)
    except InjectedInterruption as interruption:
        return RenameResult(RenameStatus.PARTIAL, interruption.checkpoint, operation_id)
    except _RegistryLockPartial as partial:
        return RenameResult(
            RenameStatus.PARTIAL, "lock-release-failed", partial.operation_id
        )
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
        return RenameResult(RenameStatus.REFUSED, "transaction-refused", operation_id)


def _try_unsealed_cleanup(
    root: Path, stage: Path, source: str, token: str, date: str
) -> RenameResult | None:
    descriptor = _open_stage(root, stage)
    try:
        names = _list_at(descriptor)
        if _CLEANUP_NAME in names or _RECORD_NAME not in names:
            return None
        record_bytes, _ = _read_at(descriptor, _RECORD_NAME, max_bytes=_MAX_RECORD_BYTES)
        value = _strict_json(record_bytes)
        if not isinstance(value, dict):
            return None
        base = value.get("base_commit")
        operation = value.get("operation_id")
        origin_view_sha256 = value.get("origin_view_sha256")
        registry = value.get("registry")
        successor = registry.get("successor") if isinstance(registry, dict) else None
        if (
            not isinstance(base, str)
            or not isinstance(operation, str)
            or not isinstance(origin_view_sha256, str)
            or not isinstance(successor, str)
        ):
            return None
        derived = _derive(
            root,
            operation_id=operation,
            base_commit=base,
            source=source,
            target_token=token,
            date=date,
            successor=successor,
            origin_view_sha256=origin_view_sha256,
        )
        if record_bytes != _canonical_json(_record(derived)):
            return None
        stage_match = _STAGE_RE.fullmatch(stage.name)
        if stage_match is None or stage_match.group(1) != derived.operation_id:
            return None
        if _SEAL_NAME in names:
            # The seal is written before any live write, so one killed while
            # being written can only accompany an untouched tree. A torn seal
            # grants nothing: it is handled exactly like an absent seal, which
            # permits only all-before cleanup. A complete or altered seal takes
            # the normal sealed path, which refuses anything non-canonical.
            try:
                seal_bytes, _ = _read_at(descriptor, _SEAL_NAME, max_bytes=_MAX_SEAL_BYTES)
            except (OSError, ValueError):
                seal_bytes = None
            if not _is_torn(seal_bytes, _canonical_json(_seal(record_bytes, derived.writes))):
                return None
    finally:
        os.close(descriptor)
    if _discard_unsealed_before(root, stage, derived):
        return RenameResult(RenameStatus.ROLLED_BACK, "rolled-back", derived.operation_id)
    return RenameResult(RenameStatus.REFUSED, "stage-unsealed", derived.operation_id)


def _resume_terminal_cleanup(
    root: Path,
    source: str,
    token: str,
    date: str,
    checkpoint: _Checkpoint,
) -> RenameResult | None:
    """Finish a marker-only, empty, or partial-record stage.

    The first two are interrupted disposals. A stage holding only a record that
    names no request was killed while its record was being written, which is
    before any live write, so it may only be resolved backward.
    """
    candidates: list[tuple[_LoadedStage, str, bool, bool]] = []
    base = _head(root)
    for stage in _stage_candidates(root):
        match = _STAGE_RE.fullmatch(stage.name)
        if match is None:
            continue
        descriptor = _open_stage(root, stage)
        try:
            names = _list_at(descriptor)
            partial_record = False
            partial_data: bytes | None = None
            if names == {_RECORD_NAME}:
                try:
                    partial_data, _ = _read_at(
                        descriptor, _RECORD_NAME, max_bytes=_MAX_RECORD_BYTES
                    )
                    if _record_request(_strict_json(partial_data)) is not None:
                        continue
                except (OSError, UnicodeError, ValueError):
                    pass
                partial_record = True
            elif names not in (set(), {_CLEANUP_NAME}):
                continue
            cleanup = (
                _read_at(descriptor, _CLEANUP_NAME, max_bytes=_MAX_CLEANUP_BYTES)[0]
                if _CLEANUP_NAME in names
                else None
            )
        finally:
            os.close(descriptor)
        try:
            derived = _derive(
                root,
                operation_id=match.group(1),
                base_commit=base,
                source=source,
                target_token=token,
                date=date,
            )
        except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired):
            continue
        record_bytes = _canonical_json(_record(derived))
        seal_bytes = _canonical_json(_seal(record_bytes, derived.writes))
        loaded = _LoadedStage(derived, stage, record_bytes, seal_bytes)
        # Only a proper prefix of the re-derived canonical record is a record
        # killed mid-write; any other bytes are altered and keep the stage.
        if partial_record and not _is_torn(partial_data, record_bytes):
            continue
        payloads = (_cleanup_payload(loaded, "forward"), _cleanup_payload(loaded, "back"))
        marker_names_direction = cleanup is not None and cleanup in payloads
        if (
            cleanup is not None
            and not marker_names_direction
            and not any(_is_torn(cleanup, payload) for payload in payloads)
        ):
            continue
        for direction in ("back",) if partial_record else ("forward", "back"):
            # A torn marker names no direction; terminal validation decides.
            if marker_names_direction and cleanup != _cleanup_payload(loaded, direction):
                continue
            try:
                _validate_terminal_bytes(root, loaded, direction)
            except (OSError, UnicodeError, ValueError):
                continue
            candidates.append((loaded, direction, cleanup is not None, partial_record))
    if not candidates:
        return None
    if len(candidates) != 1:
        return RenameResult(RenameStatus.REFUSED, "recovery-ambiguous")
    loaded, direction, has_cleanup, has_partial_record = candidates[0]
    descriptor = _open_stage(root, loaded.stage)
    try:
        if has_partial_record:
            os.unlink(_RECORD_NAME, dir_fd=descriptor)
            os.fsync(descriptor)
            checkpoint("after-dispose-partial-record")
        if has_cleanup:
            os.unlink(_CLEANUP_NAME, dir_fd=descriptor)
            os.fsync(descriptor)
            checkpoint("after-dispose-cleanup")
        if _list_at(descriptor):
            raise ValueError("stage-entry-set")
    finally:
        os.close(descriptor)
    parent = _open_parent(root, loaded.stage.parent)
    try:
        _remove_empty_stage(parent, loaded.stage.name)
        os.fsync(parent)
    finally:
        os.close(parent)
    checkpoint("after-stage-cleanup")
    status = RenameStatus.COMMITTED if direction == "forward" else RenameStatus.ROLLED_BACK
    code = "committed" if direction == "forward" else "rolled-back"
    return RenameResult(status, code, loaded.derived.operation_id)


def recover_intent_rename(
    direction: Literal["forward", "back"] | str,
    source_rel: str,
    target_token: str,
    tombstone_date: str,
    *,
    repository_root: Path | None = None,
    _checkpoint: _Checkpoint = _noop_checkpoint,
) -> RenameResult:
    """Recover the one operation matching the operator-supplied request."""
    if direction not in {"forward", "back"}:
        return RenameResult(RenameStatus.REFUSED, "direction-invalid")
    # Once one stage is selected, every refusal names it, so the operator can
    # find the stage the fixed code is about.
    selected: str | None = None
    try:
        date_check = _tombstone.serialize_tombstone(  # type: ignore[attr-defined]
            "validation", tombstone_date, reissued_as=f"{INTENTS_PARENT}/x.md"
        )
        if isinstance(date_check, str):
            return RenameResult(RenameStatus.REFUSED, "invalid-date")
        if _filesystem_unsupported():
            return RenameResult(RenameStatus.REFUSED, "filesystem-unsupported")
        if _git_environment_redirected():
            return RenameResult(RenameStatus.REFUSED, "git-environment-redirected")
        root = _root(repository_root)
        refusal = _recovery_request_refusal(root, source_rel, target_token)
        if refusal is not None:
            return RenameResult(RenameStatus.REFUSED, refusal)
        stages = _matching_stages(root, source_rel, target_token, tombstone_date)
        if not stages:
            resumed = _resume_terminal_cleanup(
                root, source_rel, target_token, tombstone_date, _checkpoint
            )
            if resumed is not None:
                return resumed
            # A stage whose own bytes name no request is present but unusable.
            # It is reported, never treated as absent, and never trusted.
            unattributed = _unattributed_stages(root)
            if unattributed:
                match = _STAGE_RE.fullmatch(unattributed[0].name)
                return RenameResult(
                    RenameStatus.REFUSED,
                    "stage-unattributed",
                    match.group(1) if match else None,
                )
            return RenameResult(RenameStatus.REFUSED, "recovery-missing")
        if len(stages) > 1:
            return RenameResult(RenameStatus.REFUSED, "recovery-ambiguous")
        stage = stages[0]
        stage_match = _STAGE_RE.fullmatch(stage.name)
        selected = stage_match.group(1) if stage_match else None
        unsealed = _try_unsealed_cleanup(root, stage, source_rel, target_token, tombstone_date)
        if unsealed is not None:
            return unsealed
        loaded = _load_stage(root, stage, source_rel, target_token, tombstone_date)
        cleanup_direction = _existing_cleanup_direction(root, loaded)
        if cleanup_direction is not None:
            _validate_terminal_bytes(root, loaded, cleanup_direction)
            _restore_canonical_cleanup(root, loaded, cleanup_direction, _checkpoint)
            _dispose(root, loaded, cleanup_direction, _checkpoint)
            status = (
                RenameStatus.COMMITTED
                if cleanup_direction == "forward"
                else RenameStatus.ROLLED_BACK
            )
            code = "committed" if cleanup_direction == "forward" else "rolled-back"
            return RenameResult(status, code, loaded.derived.operation_id)
        _, registry = _validate_targets(root, loaded)
        if direction == "back" and registry != "before":
            _backward_workspace_candidate(
                root, loaded, _read_live(root, WORKSPACE_FILE, _MAX_WORKSPACE_BYTES)
            )
        _normalise_old_claim(root, loaded)
        _validate_targets(root, loaded)
        if direction == "forward":
            _apply_forward(root, loaded, _checkpoint)
        else:
            _apply_back(root, loaded, _checkpoint)
        _write_cleanup(root, loaded, direction, _checkpoint)
        _dispose(root, loaded, direction, _checkpoint)
        status = RenameStatus.COMMITTED if direction == "forward" else RenameStatus.ROLLED_BACK
        code = "committed" if direction == "forward" else "rolled-back"
        return RenameResult(status, code, loaded.derived.operation_id)
    except InjectedInterruption as interruption:
        return RenameResult(RenameStatus.PARTIAL, interruption.checkpoint, selected)
    except _RegistryLockPartial as partial:
        return RenameResult(
            RenameStatus.PARTIAL, "lock-release-failed", partial.operation_id
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as error:
        fixed = str(error)
        allowed = {
            "base-changed",
            "cleanup-state-invalid",
            "lock-active",
            "lock-busy",
            "lock-foreign",
            "record-mismatch",
            "registry-alien",
            "seal-invalid",
            "source-alien",
            "stage-entry-set",
            "successor-conflict",
            "target-alien",
            "temporary-alien",
        }
        return RenameResult(
            RenameStatus.REFUSED, fixed if fixed in allowed else "recovery-refused", selected
        )


def resolve_intent_path(
    intent_rel: str, *, repository_root: Path | None = None
) -> ResolveResult:
    """Resolve one intent path, stopping at the first tombstone."""
    if _filesystem_unsupported():
        return ResolveResult("resolve-refused", ())
    try:
        root = _root(repository_root)
        # Resolution is about intents: anything outside the intents parent is
        # refused rather than reported as a live intent.
        if not _printable_intent_path(intent_rel) or not _confined_to_intents(root, intent_rel):
            return ResolveResult("resolve-refused", ())
        source_text = _read_live(root, intent_rel, _MAX_FILE_BYTES).decode("utf-8")
        parsed = _tombstone.parse_tombstone(source_text)  # type: ignore[attr-defined]
        if isinstance(parsed, str):
            if parsed == "not-tombstone":
                return ResolveResult("live", (intent_rel,))
            return ResolveResult("tombstone-invalid", (intent_rel,))
        if parsed.reissued_as is None:
            return ResolveResult("tombstone-retired", (intent_rel,))
        target = parsed.reissued_as
        # The target is file content, not operator input. It is printed only
        # when it is display-safe and lexically an intents path; otherwise only
        # the tombstone's own path is named.
        if not _printable_intent_path(target):
            return ResolveResult("tombstone-target-refused", (intent_rel,))
        if not _confined_to_intents(root, target):
            return ResolveResult("tombstone-target-refused", (intent_rel, target))
        try:
            target_text = _read_preamble_text(root, target)
        except FileNotFoundError:
            return ResolveResult("tombstone-target-missing", (intent_rel, target))
        except (OSError, UnicodeError, ValueError):
            return ResolveResult("tombstone-target-refused", (intent_rel, target))
        target_parsed = _tombstone.parse_tombstone(target_text)  # type: ignore[attr-defined]
        # Every parse result except "not-tombstone" means the target carries
        # `Tombstone:`, including a malformed one; neither is a live successor.
        if target_parsed != "not-tombstone":
            return ResolveResult("tombstone-target-is-tombstone", (intent_rel, target))
        return ResolveResult("tombstone", (intent_rel, target))
    except (OSError, UnicodeError, ValueError):
        return ResolveResult("resolve-refused", ())


class _OperatorParser(argparse.ArgumentParser):
    """Refuse invalid CLI syntax without reflecting operator-controlled input."""

    def error(self, message: str) -> NoReturn:
        """Emit the one bounded syntax diagnostic for every parse failure."""
        del message
        self.exit(2, "refused:syntax-invalid\n")


def main(
    argv: list[str] | None = None,
    *,
    _checkpoint: _Checkpoint = _noop_checkpoint,
    _today: _Today = _today,
) -> int:
    """Run the installed transaction operator.

    The keyword seams exist for in-process construction tests only; the
    installed entry point passes none, so no environment can inject a kill
    or a tombstone date.
    """
    if sys.stdout is not None:
        sys.stdout.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[union-attr]
    if sys.stderr is not None:
        sys.stderr.reconfigure(  # type: ignore[union-attr]
            encoding="utf-8", errors="backslashreplace"
        )
    parser = _OperatorParser(add_help=False)
    commands = parser.add_subparsers(dest="command", required=True)
    rename = commands.add_parser("rename", add_help=False)
    rename.add_argument("source")
    rename.add_argument("target_token")
    recover = commands.add_parser("recover", add_help=False)
    recover.add_argument("direction", choices=("forward", "back"))
    recover.add_argument("source")
    recover.add_argument("target_token")
    recover.add_argument("tombstone_date")
    resolve = commands.add_parser("resolve", add_help=False)
    resolve.add_argument("intent_path")
    args = parser.parse_args(argv)
    if args.command == "rename":
        result = run_intent_rename(
            args.source,
            args.target_token,
            _checkpoint=_checkpoint,
            _today=_today,
        )
        identifier = f":{result.operation_id}" if result.operation_id else ""
        print(f"{result.status.value}:{result.code}{identifier}")
        return 0 if result.status is RenameStatus.COMMITTED else 1
    if args.command == "recover":
        result = recover_intent_rename(
            args.direction,
            args.source,
            args.target_token,
            args.tombstone_date,
            _checkpoint=_checkpoint,
        )
        identifier = f":{result.operation_id}" if result.operation_id else ""
        print(f"{result.status.value}:{result.code}{identifier}")
        return 0 if result.status in {RenameStatus.COMMITTED, RenameStatus.ROLLED_BACK} else 1
    resolved = resolve_intent_path(args.intent_path)
    print(":".join(("resolve", resolved.code, *resolved.paths)))
    return 0 if resolved.code in {"live", "tombstone"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
