#!/usr/bin/env python3
"""Run the frontend browser gate with shared browser and port coordination.

Lease ownership uses a PID plus a unique token. PID identity is approximate because
operating systems can reuse process IDs, so leases older than 24 hours are reclaimable
even when that PID is live. This bounds a PID-reuse wedge without another dependency.

Participating wrappers cannot select the same leased port. The availability probe is
necessarily closed before Astro binds, however, so an unrelated machine-local process
can still take the port in that interval. This known TOCTOU residual is not presented
as an absolute reservation guarantee.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Any, Callable, Iterator, Mapping, Sequence

# Imported two ways, so both must work: as a script (`python3
# tools/repo/frontend_runtime.py`, where sys.path[0] is tools/repo) and as
# `tools.repo.frontend_runtime` -- tools/repo has no __init__.py but is a PEP 420
# namespace package, which is how tools/test_frontend_runtime.py:16 imports it.
# Dropping either branch breaks one of those callers at collection time.
if __package__:
    from . import worktree_hygiene
else:
    import worktree_hygiene

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GATE_COMMAND = ("npm", "run", "test:e2e:gate", "--prefix", "web")
DEFAULT_PREVIEW_PORT = 4321
LEASE_DIRECTORY = "agent-ready-repo-port-leases"
LEASE_MAX_AGE_SECONDS = 24 * 60 * 60
LEASE_RETRY_LIMIT = 20
LEASE_RETRY_DELAY_SECONDS = 0.05
PROCESS_TREE_EXIT_TIMEOUT_SECONDS = 5.0
PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV = "PLAYWRIGHT_FAILURE_EVIDENCE_MAX_AGE_SECONDS"
SignalHandler = Callable[[int, FrameType | None], Any] | int | None


class FrontendRuntimeError(RuntimeError):
    """An actionable frontend-runtime configuration or execution error."""


def playwright_evidence_max_age(environ: Mapping[str, str]) -> int:
    """Read the optional bounded-retention age budget for failed test evidence."""
    raw = environ.get(PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV)
    if raw is None:
        return worktree_hygiene.DEFAULT_PLAYWRIGHT_EVIDENCE_MAX_AGE_SECONDS
    try:
        value = int(raw)
    except ValueError as error:
        raise FrontendRuntimeError(
            f"{PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV} must be a whole number of seconds"
        ) from error
    if value < 0:
        raise FrontendRuntimeError(
            f"{PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV} must not be negative"
        )
    return value


@dataclass(frozen=True)
class BrowserCache:
    """A resolved Playwright browser cache and the rule that selected it."""

    path: Path
    source: str
    warning: str | None = None


def _platform_browser_cache(environ: Mapping[str, str]) -> Path:
    """Return Playwright's documented cache directory for this platform."""
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    if os.name == "nt":
        profile = environ.get("USERPROFILE")
        home = Path(profile).expanduser() if profile else Path.home()
        return home / "AppData" / "Local" / "ms-playwright"
    return Path.home() / ".cache" / "ms-playwright"


def _external_cache_path(raw: str, repo_root: Path) -> Path:
    """Resolve a cache path and reject browser binaries inside the repository."""
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    path = path.resolve()
    root = repo_root.resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return path
    raise FrontendRuntimeError(
        f"browser cache {path} is inside the repository; choose a shared external path"
    )


def resolve_browser_cache(
    explicit: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    repo_root: Path = REPO_ROOT,
) -> BrowserCache:
    """Resolve the browser cache using the documented precedence rules."""
    values = os.environ if environ is None else environ
    warning = None
    if values.get("PLAYWRIGHT_BROWSERS_PATH") == "0":
        warning = (
            "PLAYWRIGHT_BROWSERS_PATH=0 enables hermetic browser installs under "
            "each worktree's node_modules; using the shared platform default instead"
        )

    if explicit is not None:
        if not explicit:
            raise FrontendRuntimeError("--browsers-path must not be empty")
        return BrowserCache(
            _external_cache_path(explicit, repo_root), "explicit --browsers-path", warning
        )

    arr_path = values.get("ARR_PLAYWRIGHT_BROWSERS_PATH")
    if arr_path:
        return BrowserCache(
            _external_cache_path(arr_path, repo_root),
            "ARR_PLAYWRIGHT_BROWSERS_PATH",
            warning,
        )

    playwright_path = values.get("PLAYWRIGHT_BROWSERS_PATH")
    if playwright_path and playwright_path != "0":
        return BrowserCache(
            _external_cache_path(playwright_path, repo_root),
            "PLAYWRIGHT_BROWSERS_PATH",
        )

    default = _external_cache_path(str(_platform_browser_cache(values)), repo_root)
    return BrowserCache(default, "platform default", warning)


def announce_browser_cache(cache: BrowserCache) -> None:
    """Print the selected browser cache and any hermetic-mode warning."""
    print(f"Playwright browser cache: {cache.path} (source: {cache.source})", flush=True)
    if cache.warning:
        print(f"WARNING: {cache.warning}", file=sys.stderr, flush=True)


def parse_port(raw: str, source: str) -> int:
    """Parse a user-supplied TCP port without silently changing invalid input."""
    if not raw.isascii() or not raw.isdecimal():
        raise FrontendRuntimeError(
            f"{source} has invalid value {raw!r}; expected an integer from 1 to 65535"
        )
    port = int(raw)
    if port <= 0 or port > 65535:
        raise FrontendRuntimeError(
            f"{source} has invalid value {raw!r}; expected an integer from 1 to 65535"
        )
    return port


def _pid_is_alive(pid: int) -> bool:
    """Return whether a process id still identifies a live process."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@contextlib.contextmanager
def _port_coordination_lock(lease_dir: Path, port: int) -> Iterator[None]:
    """Serialize stale inspection and reclamation for one port across processes."""
    path = lease_dir / f"preview-{port}.lock"
    with path.open("a+b") as handle:
        if os.name == "nt":
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            windows_locking: Any = importlib.import_module("msvcrt")

            def windows_acquire() -> None:
                windows_locking.locking(
                    handle.fileno(), windows_locking.LK_NBLCK, 1
                )

            def windows_release() -> None:
                windows_locking.locking(handle.fileno(), windows_locking.LK_UNLCK, 1)

            acquire = windows_acquire
            release = windows_release
        else:
            posix_locking: Any = importlib.import_module("fcntl")

            def posix_acquire() -> None:
                posix_locking.flock(
                    handle.fileno(), posix_locking.LOCK_EX | posix_locking.LOCK_NB
                )

            def posix_release() -> None:
                posix_locking.flock(handle.fileno(), posix_locking.LOCK_UN)

            acquire = posix_acquire
            release = posix_release

        for attempt in range(LEASE_RETRY_LIMIT):
            try:
                acquire()
                break
            except OSError:
                if attempt + 1 < LEASE_RETRY_LIMIT:
                    time.sleep(LEASE_RETRY_DELAY_SECONDS)
        else:
            raise FrontendRuntimeError(
                f"could not acquire coordination lock for preview port {port}"
            )
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                handle.seek(0)
                release()


def _lease_age_seconds(path: Path, existing: Mapping[str, object] | None) -> float:
    """Return lease age from its payload, falling back to filesystem modification time."""
    created_at = existing.get("created_at") if existing is not None else None
    try:
        if isinstance(created_at, (int, float, str)):
            created = float(created_at)
        else:
            created = path.stat().st_mtime
    except (OSError, TypeError, ValueError):
        return 0.0
    return max(0.0, time.time() - created)


def _lease_reclaimable(path: Path) -> bool | None:
    """Return stale status, or ``None`` while an unreadable lease is still young."""
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
        owner = int(existing["pid"])
    except (KeyError, OSError, UnicodeError, ValueError, TypeError):
        age = _lease_age_seconds(path, None)
        return True if age > LEASE_MAX_AGE_SECONDS else None
    age = _lease_age_seconds(path, existing)
    return not _pid_is_alive(owner) or age > LEASE_MAX_AGE_SECONDS


def _publish_lease_candidate(lease_dir: Path, path: Path, payload: str) -> None:
    """Publish a complete lease without exposing a partially written destination."""
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".preview-{path.stem}-", dir=lease_dir
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as candidate:
            candidate.write(payload)
        os.link(temporary, path)
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()


@dataclass
class PortLease:
    """An atomically claimed preview-port coordination file."""

    port: int
    path: Path
    token: str

    @classmethod
    def try_acquire(cls, common_dir: Path, port: int) -> PortLease | None:
        """Claim a port lease, reclaiming a lease whose owner is dead."""
        lease_dir = common_dir / LEASE_DIRECTORY
        lease_dir.mkdir(parents=True, exist_ok=True)
        path = lease_dir / f"preview-{port}.json"

        for attempt in range(LEASE_RETRY_LIMIT):
            token = uuid.uuid4().hex
            payload = json.dumps(
                {
                    "pid": os.getpid(),
                    "token": token,
                    "port": port,
                    "created_at": time.time(),
                }
            )
            try:
                _publish_lease_candidate(lease_dir, path, payload)
            except FileExistsError:
                with _port_coordination_lock(lease_dir, port):
                    reclaimable = _lease_reclaimable(path)
                    if reclaimable is False:
                        return None
                    if reclaimable is True:
                        with contextlib.suppress(OSError):
                            path.unlink()
                if attempt + 1 < LEASE_RETRY_LIMIT:
                    time.sleep(LEASE_RETRY_DELAY_SECONDS)
                continue
            return cls(port=port, path=path, token=token)
        raise FrontendRuntimeError(
            f"could not acquire preview port {port}: lease remained unreadable"
        )

    def release(self) -> None:
        """Remove this lease without deleting a replacement owner's lease."""
        with _port_coordination_lock(self.path.parent, self.port):
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return
            if existing.get("token") != self.token:
                return
            with contextlib.suppress(OSError):
                self.path.unlink()


def _port_is_available(port: int) -> bool:
    """Bind-test a localhost port to detect unrelated listeners."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", port))
    except OSError:
        return False
    finally:
        probe.close()
    return True


def lease_preview_port(common_dir: Path, requested: int | None) -> PortLease:
    """Lease an explicit port or the first free coordinated port from 4321."""
    if requested is not None:
        lease = PortLease.try_acquire(common_dir, requested)
        if lease is None:
            raise FrontendRuntimeError(
                f"preview port {requested} is already leased by another gate"
            )
        if not _port_is_available(requested):
            lease.release()
            raise FrontendRuntimeError(
                f"preview port {requested} is already occupied by another process"
            )
        return lease

    candidates = range(DEFAULT_PREVIEW_PORT, 65536)
    for port in candidates:
        lease = PortLease.try_acquire(common_dir, port)
        if lease is None:
            continue
        if _port_is_available(port):
            return lease
        lease.release()
    raise FrontendRuntimeError("no available preview port could be leased")


def git_common_dir(repo_root: Path = REPO_ROOT) -> Path:
    """Ask Git for the local directory shared by all linked worktrees."""
    try:
        result = subprocess.run(
            ("git", "rev-parse", "--git-common-dir"),
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise FrontendRuntimeError(
            "git is required to locate the shared worktree lease directory"
        ) from error
    if result.returncode != 0:
        detail = result.stderr.strip() or "not inside a Git worktree"
        raise FrontendRuntimeError(f"could not resolve Git common directory: {detail}")
    raw = Path(result.stdout.strip())
    return raw.resolve() if raw.is_absolute() else (repo_root / raw).resolve()


def _require_npm() -> None:
    """Fail before spawning when npm is unavailable."""
    if shutil.which("npm") is None:
        raise FrontendRuntimeError(
            "npm was not found; install Node.js/npm and bootstrap the web profile"
        )


def _spawn_child(
    command: Sequence[str], env: Mapping[str, str], cwd: Path
) -> subprocess.Popen[Any]:
    """Spawn the gate in a process group dedicated to its complete descendant tree."""
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        return subprocess.Popen(
            tuple(command),
            cwd=cwd,
            env=dict(env),
            creationflags=creation_flags,
        )
    return subprocess.Popen(
        tuple(command),
        cwd=cwd,
        env=dict(env),
        start_new_session=True,
    )


@dataclass(frozen=True)
class _ProcessTreeSignal:
    """Information the main flow needs after a handler signals the process tree."""

    process_group: int | None = None
    taskkill: subprocess.Popen[Any] | None = None


def _signal_process_tree(
    child: subprocess.Popen[Any], signum: int
) -> _ProcessTreeSignal:
    """Signal the gate tree without waiting, polling, or sleeping."""
    if os.name == "nt":
        try:
            taskkill = subprocess.Popen(
                ("taskkill", "/T", "/F", "/PID", str(child.pid)),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return _ProcessTreeSignal(taskkill=taskkill)
        except OSError:
            pass
    else:
        try:
            process_group = os.getpgid(child.pid)
            os.killpg(process_group, signum)
            return _ProcessTreeSignal(process_group=process_group)
        except ProcessLookupError:
            return _ProcessTreeSignal()
        except OSError:
            pass
    with contextlib.suppress(OSError):
        child.send_signal(signum)
    return _ProcessTreeSignal()


def _reap_process_tree(
    child: subprocess.Popen[Any], tree_signal: _ProcessTreeSignal
) -> None:
    """Wait for a signalled tree and escalate from the main flow only."""
    if tree_signal.taskkill is not None:
        try:
            tree_signal.taskkill.wait(timeout=PROCESS_TREE_EXIT_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            tree_signal.taskkill.kill()
            tree_signal.taskkill.wait()
    try:
        child.wait(timeout=PROCESS_TREE_EXIT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        if tree_signal.process_group is not None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(tree_signal.process_group, signal.SIGKILL)
        else:
            with contextlib.suppress(OSError):
                child.kill()
        child.wait()

    if tree_signal.process_group is None:
        return
    try:
        os.killpg(tree_signal.process_group, 0)
    except ProcessLookupError:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(tree_signal.process_group, signal.SIGKILL)


def _run_child(command: Sequence[str], env: Mapping[str, str], cwd: Path) -> int:
    """Run a gate child, forwarding supported termination signals."""
    interrupted: list[int] = []
    tree_signals: list[_ProcessTreeSignal] = []
    previous_handlers: dict[int, SignalHandler] = {}
    child: subprocess.Popen[Any] | None = None

    def forward(signum: int, _frame: FrameType | None) -> None:
        interrupted.append(signum)
        if child is not None:
            tree_signals.append(_signal_process_tree(child, signum))

    if threading.current_thread() is threading.main_thread():
        for name in ("SIGINT", "SIGTERM"):
            signum = getattr(signal, name, None)
            if signum is not None:
                previous_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, forward)

    try:
        if interrupted:
            return 128 + interrupted[0]
        try:
            child = _spawn_child(command, env, cwd)
        except FileNotFoundError as error:
            raise FrontendRuntimeError(
                f"gate executable {command[0]!r} was not found"
            ) from error
        if interrupted:
            if not tree_signals:
                tree_signals.append(_signal_process_tree(child, interrupted[0]))
            _reap_process_tree(child, tree_signals[-1])
            return 128 + interrupted[0]
        try:
            returncode = child.wait()
        except KeyboardInterrupt:
            tree_signal = _signal_process_tree(child, signal.SIGINT)
            _reap_process_tree(child, tree_signal)
            return 130
        if interrupted:
            _reap_process_tree(child, tree_signals[-1])
            return 128 + interrupted[0]
        return returncode
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


@contextlib.contextmanager
def _release_lease_on_signals(lease: PortLease) -> Iterator[None]:
    """Cover the short setup/teardown windows around the signal-aware child."""
    previous_handlers: dict[int, SignalHandler] = {}

    def release(signum: int, _frame: FrameType | None) -> None:
        lease.release()
        raise SystemExit(128 + signum)

    if threading.current_thread() is threading.main_thread():
        for name in ("SIGINT", "SIGTERM"):
            signum = getattr(signal, name, None)
            if signum is not None:
                previous_handlers[signum] = signal.getsignal(signum)
                signal.signal(signum, release)
    try:
        yield
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)


def run_gate(
    *,
    port: str | None = None,
    browsers_path: str | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path = REPO_ROOT,
    common_dir: Path | None = None,
    gate_command: Sequence[str] | None = None,
) -> int:
    """Lease a port, configure the browser cache, and run the pinned gate."""
    values = dict(os.environ if environ is None else environ)
    raw_port = port if port is not None else values.get("ARR_PREVIEW_PORT")
    source = "--port" if port is not None else "ARR_PREVIEW_PORT"
    requested = parse_port(raw_port, source) if raw_port is not None else None
    cache = resolve_browser_cache(browsers_path, environ=values, repo_root=repo_root)
    command = GATE_COMMAND if gate_command is None else tuple(gate_command)
    if gate_command is None:
        _require_npm()

    lease = lease_preview_port(
        git_common_dir(repo_root) if common_dir is None else common_dir,
        requested,
    )
    try:
        values["ARR_PREVIEW_PORT"] = str(lease.port)
        values["PLAYWRIGHT_BROWSERS_PATH"] = str(cache.path)
        announce_browser_cache(cache)
        print(f"Preview port lease: {lease.port}", flush=True)
        with _release_lease_on_signals(lease):
            returncode = _run_child(command, values, repo_root)
    finally:
        lease.release()
    evidence = worktree_hygiene.manage_playwright_failure_evidence(
        repo_root,
        gate_returncode=returncode,
        max_age_seconds=playwright_evidence_max_age(values),
    )
    for line in evidence.receipt:
        print(line, flush=True)
    return returncode


def install_browsers(
    *,
    browsers_path: str | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path = REPO_ROOT,
) -> int:
    """Install only the Chromium browser required by the quality gate."""
    values = dict(os.environ if environ is None else environ)
    cache = resolve_browser_cache(browsers_path, environ=values, repo_root=repo_root)
    executable_name = "playwright.cmd" if os.name == "nt" else "playwright"
    executable = repo_root / "web" / "node_modules" / ".bin" / executable_name
    if not executable.is_file():
        raise FrontendRuntimeError(
            "Playwright is not installed under web/node_modules; run "
            "python tools/repo/bootstrap.py web first"
        )
    values["PLAYWRIGHT_BROWSERS_PATH"] = str(cache.path)
    announce_browser_cache(cache)
    try:
        result = subprocess.run(
            (str(executable), "install", "chromium"),
            cwd=repo_root,
            env=values,
            check=False,
        )
    except FileNotFoundError as error:
        raise FrontendRuntimeError(
            "the local Playwright executable could not be started; verify Node.js is installed"
        ) from error
    return result.returncode


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    gate = subparsers.add_parser("gate", help="run the browser quality gate")
    gate.add_argument("--port", help="explicit preview port")
    gate.add_argument("--browsers-path", help="shared Playwright browser cache")

    browsers = subparsers.add_parser("browsers", help="show browser cache resolution")
    browsers.add_argument("--browsers-path", help="shared Playwright browser cache")

    install = subparsers.add_parser(
        "install-browsers", help="install the gate's Chromium browser"
    )
    install.add_argument("--browsers-path", help="shared Playwright browser cache")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the frontend-runtime command-line interface."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "gate":
            return run_gate(port=args.port, browsers_path=args.browsers_path)
        if args.command == "install-browsers":
            return install_browsers(browsers_path=args.browsers_path)
        cache = resolve_browser_cache(args.browsers_path)
        announce_browser_cache(cache)
        return 0
    except FrontendRuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
