"""_supervisor_launcher — the pinned launcher: its pin, its spawn, and its protocol.

A launcher is an executable the run's owner named by sha256 when the run started. The
supervisor copies it into the run store, hashes the copy, and spawns that copy, once
per concurrent attempt, in its own process group with an empty private working
directory, no inherited descriptor but the three standard ones, and an environment of
exactly ``PATH``, ``LANG``, ``HOME``, and ``TMPDIR``. It then speaks newline-delimited
JSON over the launcher's own pipes. Every attestation is read from those pipes, inside
the process that spawned the launcher, and checked here:

* ``verify_containment`` checks a containment attestation line before any release;
* ``verify_access`` checks the one access line the launcher sends at the end;
* ``access_defect`` names why an otherwise valid access attestation cannot support
  anything but an exact-source integration;
* ``end_group`` ends a launcher's process group and confirms the end, never signalling a
  process other than the one that was recorded.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import os
import posixpath
import re
import select
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _supervisor(filename: str) -> ModuleType:
    """Load a supervisor module once per process, shared by every supervisor module."""
    tag = hashlib.sha256(str(_SCRIPTS_DIR).encode("utf-8")).hexdigest()[:12]
    alias = f"_work_supervisor_{tag}_" + filename.removesuffix(".py").strip("_").replace("-", "_")
    module = sys.modules.get(alias)
    if module is not None:
        return module
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError(f"{path.name} is not a regular file")
    spec = importlib.util.spec_from_file_location(alias, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.modules[alias] = module
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(alias, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_commit = _supervisor("_supervisor_commit.py")
_conc = _supervisor("_supervisor_concurrency.py")
_containment = _supervisor("_containment.py")
sibling = _commit.sibling
kill_point = _commit.kill_point

__all__ = [
    "ALLOW_FIXTURE_LAUNCHER",
    "Binding",
    "CLOCK",
    "FIXTURE_MARKER",
    "Grant",
    "LineReader",
    "access_defect",
    "carries_fixture_marker",
    "copy_matches",
    "end_group",
    "group_alive",
    "install",
    "process_start",
    "read_candidate",
    "send",
    "spawn",
    "verify_access",
    "verify_containment",
]

# The marker a test-only fixture launcher carries. It is built from two parts so that no
# installed file holds it whole: a scan for the marker finds only the fixture.
FIXTURE_MARKER = "agentbundle-fixture-" + "launcher:not-a-host"
# Set only by assignment in test code. No environment variable, flag, policy key, or file
# reads it.
ALLOW_FIXTURE_LAUNCHER = False

CONTAINMENT_TIMEOUT_S = 60.0
CONFIRM_TIMEOUT_S = 10.0
LINE_CAP = 4 * 1024 * 1024
MAX_LAUNCHER_BYTES = 64 * 1024 * 1024
POLL_S = 0.05
MAX_ENTRIES = 20_000
SPAWN_PATH = "/usr/bin:/bin"
SPAWN_LANG = "C.UTF-8"
DENIALS = (
    "git-common-dir", "shared-refs", "run-store", "work-trees", "sibling-trees", "sibling-ipc",
)
_HEX64 = re.compile(r"[0-9a-f]{64}")
_READ_KINDS = ("file", "missing", "listing", "walk")
_WRITE_KINDS = ("write", "delete", "rename-from", "rename-to", "mode")


class _RealClock:
    """The clock every timeout reads; a test replaces ``CLOCK`` to drive time."""

    def now(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


CLOCK: Any = _RealClock()


# ── the pin ─────────────────────────────────────────────────────────────────


def carries_fixture_marker(data: bytes) -> bool:
    """Whether *data* carries the fixture launcher's marker."""
    return FIXTURE_MARKER.encode("utf-8") in data


def read_candidate(path: str, root: Path) -> bytes | None:
    """The bytes of the named launcher file; ``None`` unless it is a plain file outside *root*."""
    try:
        real = Path(os.path.realpath(path))
        base = Path(os.path.realpath(root))
    except (OSError, ValueError):
        return None
    if real == base or base in real.parents:
        return None
    fs = sibling("_file_safety.py")
    try:
        return bytes(
            fs.read_confined_regular_file(real.parent, real, max_bytes=MAX_LAUNCHER_BYTES)
        )
    except (OSError, fs.UnsafeContentError):
        return None


def _uid() -> int:
    return int(getattr(os, "getuid", lambda: -1)())


def install(store: Path, data: bytes) -> None:
    """Copy *data* into the store's ``launcher/`` directory; an existing copy is never replaced.

    The directory is 0700 and the file 0700 with one link, both created without following
    a link.
    """
    directory = store / "launcher"
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        info = os.lstat(directory)
        if not stat.S_ISDIR(info.st_mode):
            raise OSError("launcher is not a directory") from None
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(directory / "launcher", flags, 0o700)
    except FileExistsError:
        return
    with os.fdopen(fd, "wb") as handle:
        os.fchmod(handle.fileno(), 0o700)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def copy_matches(store: Path, sha256: str) -> Path | None:
    """The store's launcher copy when it is private, single-link, regular, and hashes to *sha256*.
    """
    directory = store / "launcher"
    path = directory / "launcher"
    try:
        info = os.lstat(directory)
        if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077 or info.st_uid != _uid():
            return None
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            file_info = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(file_info.st_mode)
                or file_info.st_nlink != 1
                or file_info.st_mode & 0o077
                or file_info.st_uid != _uid()
            ):
                return None
            data = handle.read(MAX_LAUNCHER_BYTES + 1)
    except OSError:
        return None
    if len(data) > MAX_LAUNCHER_BYTES or hashlib.sha256(data).hexdigest() != sha256:
        return None
    return path


# ── processes ───────────────────────────────────────────────────────────────


def process_start(pid: int) -> str | None:
    """An opaque start-time token for process *pid*; ``None`` when no process holds that id."""
    if pid <= 0:
        return None
    if Path("/proc/self").is_dir():
        try:
            with Path(f"/proc/{pid}/stat").open("rb") as handle:
                data = handle.read()
        except OSError:
            return None
        fields = data[data.rindex(b")") + 2 :].split()
        return "proc:" + fields[19].decode("ascii", "replace")
    try:
        done = subprocess.run(
            ["/bin/ps", "-o", "lstart=", "-p", str(pid)],
            env={"LC_ALL": "C", "PATH": SPAWN_PATH},
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = done.stdout.decode("ascii", "replace").strip()
    return "ps:" + text if done.returncode == 0 and text else None


def group_alive(pgid: int) -> bool:
    """Whether any process is still in process group *pgid*."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _terminate(pgid: int, proc: subprocess.Popen[bytes] | None) -> bool:
    """Signal group *pgid* and confirm, within the confirmation window, that it ended."""
    if proc is not None:
        proc.poll()
    if group_alive(pgid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except PermissionError:
            return False
    deadline = CLOCK.now() + CONFIRM_TIMEOUT_S
    while True:
        if proc is not None:
            proc.poll()
        if not group_alive(pgid):
            return True
        if CLOCK.now() >= deadline:
            return False
        CLOCK.sleep(POLL_S)


def end_group(
    pgid: int, leader_pid: int, leader_start: str, proc: subprocess.Popen[bytes] | None = None
) -> bool:
    """End process group *pgid* and confirm it, or report that the end is not confirmed.

    A process other than the recorded leader (by id and start time) holding the leader's
    id means the group is gone: nothing is signalled and the end counts as confirmed.
    Otherwise a group that still has members is signalled and must end within the window.
    """
    holder = process_start(leader_pid)
    if holder is not None and holder != leader_start:
        return True
    return _terminate(pgid, proc)


def spawn(launcher: Path, scratch: Path) -> subprocess.Popen[bytes]:
    """Start the launcher copy in its own process group; the only process launch here.

    The working directory is an empty private directory; ``HOME`` and ``TMPDIR`` are
    private directories; the environment is exactly four variables whatever the invoking
    environment holds; only standard input, output, and error are inherited.
    """
    private = {}
    for name in ("cwd", "home", "tmp"):
        path = scratch / name
        path.mkdir(mode=0o700)
        private[name] = path
    environment = {
        "PATH": SPAWN_PATH,
        "LANG": SPAWN_LANG,
        "HOME": str(private["home"]),
        "TMPDIR": str(private["tmp"]),
    }
    return subprocess.Popen(
        [str(launcher)],
        cwd=private["cwd"],
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        start_new_session=True,
    )


# ── the protocol ────────────────────────────────────────────────────────────


class ReadTimeout(Exception):
    """No complete line arrived before the deadline."""


class LineTooLong(Exception):
    """A line passed the cap before its newline."""


class StreamClosed(Exception):
    """The stream ended before a complete line."""


def send(proc: subprocess.Popen[bytes], message: dict[str, Any]) -> bool:
    """Send one line to the launcher; ``False`` when its input is closed."""
    data = json.dumps(message, separators=(",", ":")).encode("utf-8") + b"\n"
    try:
        assert proc.stdin is not None
        proc.stdin.write(data)
        proc.stdin.flush()
    except (OSError, ValueError):
        return False
    return True


class LineReader:
    """Reads capped lines from the launcher's output, against deadlines on ``CLOCK``."""

    def __init__(self, fd: int) -> None:
        self.fd = fd
        self.buffer = bytearray()
        self.eof = False

    def _fill(self, deadline: float) -> None:
        remaining = deadline - CLOCK.now()
        if remaining <= 0:
            raise ReadTimeout
        ready, _, _ = select.select([self.fd], [], [], min(remaining, POLL_S))
        if not ready:
            return
        chunk = os.read(self.fd, 65536)
        if chunk:
            self.buffer += chunk
        else:
            self.eof = True

    def read_line(self, deadline: float) -> bytes:
        """The next line without its newline."""
        while True:
            end = self.buffer.find(b"\n")
            if end >= 0:
                line = bytes(self.buffer[:end])
                del self.buffer[: end + 1]
                if len(line) > LINE_CAP:
                    raise LineTooLong
                return line
            if len(self.buffer) > LINE_CAP:
                raise LineTooLong
            if self.eof:
                raise StreamClosed
            self._fill(deadline)

    def rest(self, deadline: float) -> tuple[bytes, bool]:
        """Everything left up to end of stream, and whether the stream ended by *deadline*."""
        while not self.eof and len(self.buffer) <= LINE_CAP:
            try:
                self._fill(deadline)
            except ReadTimeout:
                break
        return bytes(self.buffer), self.eof


# ── binding and grant ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Binding:
    """The run, attempt, grant, nonce, and launcher digest issued for one attempt."""

    run_id: str
    attempt_id: str
    grant_id: str
    nonce: str
    launcher_sha256: str

    def as_dict(self) -> dict[str, str]:
        return {
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "grant_id": self.grant_id,
            "nonce": self.nonce,
            "launcher_sha256": self.launcher_sha256,
        }


@dataclass(frozen=True)
class _Allowed:
    allowed: bool


@dataclass(frozen=True)
class Grant:
    """What an attempt may be granted: the attempt directory, no network, child processes."""

    grant_id: str
    roots: tuple[str, ...]
    product_read_proof_mode: str
    network: _Allowed = _Allowed(False)
    children: _Allowed = _Allowed(True)
    limits: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "roots": list(self.roots),
            "product_read_proof_mode": self.product_read_proof_mode,
            "network": {"allowed": self.network.allowed},
            "children": {"allowed": self.children.allowed},
        }


# ── verification ────────────────────────────────────────────────────────────

_BINDING_FIELDS = (
    ("run_id", "run-id"),
    ("attempt_id", "attempt-id"),
    ("grant_id", "grant-id"),
    ("nonce", "nonce"),
    ("launcher_sha256", "launcher"),
)


def _parse(line: bytes, kind: str) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """The envelope's binding and attestation, or ``None`` for any other shape."""
    try:
        envelope = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {"schema_version", "type", "binding", "attestation"}
        or envelope["schema_version"] != 1
        or type(envelope["schema_version"]) is not int
        or envelope["type"] != kind
        or not isinstance(envelope["binding"], dict)
        or not isinstance(envelope["attestation"], dict)
    ):
        return None
    return envelope["binding"], envelope["attestation"]


def _binding_defect(found: object, issued: Binding, prefix: str) -> str | None:
    if not isinstance(found, dict):
        return None
    expected = issued.as_dict()
    for key, name in _BINDING_FIELDS:
        if found.get(key) != expected[key]:
            return f"{prefix}-{name}"
    return None


def verify_containment(
    line: bytes,
    *,
    binding: Binding,
    mode: str,
    declared_reads: list[str],
    attempt_dir: str,
    grant: Grant,
) -> tuple[str | None, dict[str, Any] | None]:
    """Check a containment line; return ``(defect code, None)`` or ``(None, attestation)``.

    The checks run in the order the verified containment attestation lists them: schema,
    binding, read enforcement, allowlist, network, write roots, roots against the grant, and
    the six denials.
    """
    parsed = _parse(line, "containment")
    if parsed is None:
        return "containment-schema", None
    outer, att = parsed
    ok, _ = _containment.validate_attestation_dict(att)
    if not ok or not isinstance(att.get("binding"), dict):
        return "containment-schema", None
    for source in (att["binding"], outer):
        defect = _binding_defect(source, binding, "binding")
        if defect is not None:
            return defect, None
    expected = "allowlist" if mode == "enforced-allowlist" else "trace"
    if att.get("read_enforcement") != expected:
        return "read-enforcement", None
    if mode == "enforced-allowlist":
        listed = att.get("read_allowlist")
        if (
            not isinstance(listed, list)
            or len(listed) > MAX_ENTRIES
            or sorted(listed) != sorted(declared_reads)
        ):
            return "allowlist-mismatch", None
    network = att.get("network")
    if isinstance(network, dict) and network.get("allowed") is True:
        return "network-allowed", None
    roots = att.get("write_roots")
    if not isinstance(roots, list) or [posixpath.normpath(r) for r in roots] != [
        posixpath.normpath(attempt_dir)
    ]:
        return "write-roots", None
    declared = _containment.ContainmentAttestation(
        schema_version=att["schema_version"],
        host_mechanism=att["host_mechanism"],
        principal_or_sandbox=att["principal_or_sandbox"],
        roots=tuple(att["roots"]),
        limits=att["limits"],
        read_enforcement=att.get("read_enforcement"),
        trace_coverage=att.get("trace_coverage"),
        network=att.get("network"),
        children=att.get("children"),
    )
    if not _containment.check_attestation_within_grant(declared, grant)[0]:
        return "broader-than-grant", None
    if not set(DENIALS) <= set(att.get("denied", ())):
        return "denial-missing", None
    return None, att


def _entries_shape(items: object, kinds: tuple[str, ...]) -> bool:
    return isinstance(items, list) and all(
        isinstance(item, dict)
        and set(item) == {"path", "kind"}
        and isinstance(item["path"], str)
        and item["kind"] in kinds
        for item in items
    )


def _access_shape(att: dict[str, Any]) -> bool:
    keys = {
        "schema_version", "binding", "release_token", "mode", "complete",
        "processes_ended", "reads", "writes", "denied_reads",
    }
    token = att.get("release_token")
    bound = att.get("binding")
    return (
        set(att) == keys
        and att["schema_version"] == 1
        and type(att["schema_version"]) is int
        and isinstance(bound, dict)
        and set(bound) == {"run_id", "attempt_id", "grant_id", "nonce", "launcher_sha256"}
        and all(isinstance(v, str) and v for v in bound.values())
        and isinstance(token, str)
        and bool(_HEX64.fullmatch(token))
        and att["mode"] in ("allowlist", "trace")
        and isinstance(att["complete"], bool)
        and isinstance(att["processes_ended"], bool)
        and _entries_shape(att["reads"], _READ_KINDS)
        and _entries_shape(att["writes"], _WRITE_KINDS)
        and isinstance(att["denied_reads"], list)
        and all(isinstance(p, str) for p in att["denied_reads"])
    )


def verify_access(
    line: bytes, *, binding: Binding, token: str
) -> tuple[str | None, dict[str, Any] | None]:
    """Check the access line; return ``(defect code, None)`` or ``(None, attestation)``.

    A defect here fails the attempt: a line that is not the access schema, a binding other
    than the one issued, or a release token other than the one sent. The token is compared
    in constant time and never appears in a code or message.
    """
    parsed = _parse(line, "access")
    if parsed is None or not _access_shape(parsed[1]):
        return "access-schema", None
    outer, att = parsed
    for source in (att["binding"], outer):
        if _binding_defect(source, binding, "access") is not None:
            return "access-binding", None
    if not hmac.compare_digest(att["release_token"].encode(), token.encode()):
        return "access-token", None
    return None, att


def _covered(read: dict[str, str], declared: list[Any], fold: Any) -> bool:
    path = fold(read["path"])
    for entry in declared:
        base = fold(entry.path)
        if entry.kind == "walk" and (path == base or path.startswith(base + "/")):
            return True
        if entry.kind == "listing" and read["kind"] == "listing" and path == base:
            return True
        if entry.kind == "file" and read["kind"] in ("file", "missing") and path == base:
            return True
    return False


def access_defect(
    att: dict[str, Any],
    *,
    read_enforcement: str,
    declared_reads: list[str],
    changed_paths: Iterable[str],
    ignore_case: bool = False,
) -> str | None:
    """The first reason a valid access attestation is not complete, or ``None``.

    The reasons, in order: a mode that differs from the containment's read enforcement; under
    ``allowlist``, an attested read outside the declared reads; a path that is not a
    repository path; more than 20,000 entries in a list; a change the supervisor computed
    that no attested write names; and ``complete`` false. A denied read never counts as read.
    """
    if att["mode"] != read_enforcement:
        return "access-mode"
    denied = set(att["denied_reads"])
    reads = [r for r in att["reads"] if r["path"] not in denied]

    def fold(path: str) -> str:
        return _conc._key(path, ignore_case)  # type: ignore[no-any-return]

    if att["mode"] == "allowlist":
        declared = _conc.declared_reads(declared_reads)
        if any(not _covered(r, declared, fold) for r in reads):
            return "access-read-outside"
    paths = [r["path"] for r in att["reads"]] + [w["path"] for w in att["writes"]]
    paths += att["denied_reads"]
    if any(len(p) > 1024 or not _conc.is_repository_path(p) for p in paths):
        return "access-bad-path"
    if any(len(att[k]) > MAX_ENTRIES for k in ("reads", "writes", "denied_reads")):
        return "access-too-many"
    written = {fold(w["path"]) for w in att["writes"]}
    if any(fold(p) not in written for p in changed_paths):
        return "access-write-missing"
    if not att["complete"]:
        return "access-incomplete"
    return None


def attested_reads(att: dict[str, Any]) -> list[dict[str, str]]:
    """The attested read set: every attested read except one the containment denied."""
    denied = set(att["denied_reads"])
    return [r for r in att["reads"] if r["path"] not in denied]
