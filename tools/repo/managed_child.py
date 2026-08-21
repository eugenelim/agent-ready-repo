"""Spawn, forward signals to, and reap one managed child process tree."""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import FrameType
from typing import Any, Callable, Mapping, Sequence

PROCESS_TREE_EXIT_TIMEOUT_SECONDS = 5.0
# A best-effort flush window before escalation, NOT a guarantee, and NOT free on
# every platform.
#
# Measured on macOS, 6 runs of 6: with the child exited but deliberately unreaped,
# `killpg` on its group answers EPERM, so the no-descendant case returns before
# this sleep and a healthy run pays nothing. That is a macOS observation. On Linux
# a zombie is a signalable member of its own group under the same uid, so `killpg`
# is expected to SUCCEED there and this sleep to fire on every wrapped target --
# which an earlier version of this comment wrongly claimed was impossible. It was
# not verified on Linux; nothing here should be read as measured on that platform.
#
# The budget is therefore kept short. The descendants this reap exists to clean up
# are servers still holding a leased port, so the trade is a brief flush window
# against seconds added to every gate run, on a host that has run at load 160.
PROCESS_TREE_REAP_GRACE_SECONDS = 0.5
SignalHandler = Callable[[int, FrameType | None], Any] | int | None


class ManagedChildError(RuntimeError):
    """An actionable error while starting a managed child process."""


class ReapDisposition(Enum):
    """The explicit result of a normal-exit process-group reap attempt."""

    REAPED = "reaped"
    NOT_OWN_CHILD = "not-own-child"
    UNAVAILABLE = "unavailable"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class ProcessTreeSignal:
    """Information the main flow needs after a handler signals the process tree."""

    process_group: int | None = None
    taskkill: subprocess.Popen[Any] | None = None


def pid_is_alive(pid: int) -> bool:
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


def spawn_child(
    command: Sequence[str], env: Mapping[str, str], cwd: Path
) -> subprocess.Popen[Any]:
    """Spawn a child in a dedicated process group for its descendant tree."""
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        return subprocess.Popen(
            tuple(command), cwd=cwd, env=dict(env), creationflags=creation_flags
        )
    return subprocess.Popen(tuple(command), cwd=cwd, env=dict(env), start_new_session=True)


def query_process_group(child: subprocess.Popen[Any]) -> int | None:
    """Query a live child's process group, or return ``None`` if it cannot be.

    This MUST be called while the child is still running. Measured on macOS,
    15 runs of 15: once a child has exited, `os.getpgid` raises
    ProcessLookupError even though the pid is still allocated as an unreaped
    zombie. Querying after exit therefore fails for exactly the fast-exiting
    child the normal-exit reap exists to clean up after, which is why the group
    is captured at spawn and carried rather than looked up later.

    Queried immediately after spawn it is reliable: 20 of 20, and equal to the
    child's pid, as `start_new_session` implies. It is still a query rather than
    an assumption, because a wrong assumption here would signal a group we never
    established we own.
    """
    try:
        return os.getpgid(child.pid)
    except OSError:
        return None


def signal_process_tree(
    child: subprocess.Popen[Any], signum: int
) -> ProcessTreeSignal:
    """Send a signal to the child tree without waiting, polling, or sleeping."""
    if os.name == "nt":
        try:
            taskkill = subprocess.Popen(
                ("taskkill", "/T", "/F", "/PID", str(child.pid)),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return ProcessTreeSignal(taskkill=taskkill)
        except OSError:
            pass
    else:
        try:
            process_group = os.getpgid(child.pid)
            os.killpg(process_group, signum)
            return ProcessTreeSignal(process_group=process_group)
        except ProcessLookupError:
            return ProcessTreeSignal()
        except OSError:
            pass
    with contextlib.suppress(OSError):
        child.send_signal(signum)
    return ProcessTreeSignal()


def reap_process_tree(child: subprocess.Popen[Any], tree_signal: ProcessTreeSignal) -> None:
    """Wait for an interrupted tree and escalate only from the main flow."""
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
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.killpg(tree_signal.process_group, signal.SIGKILL)
        else:
            with contextlib.suppress(OSError):
                child.kill()
        child.wait()


def reap_normal_exit_process_tree(
    child: subprocess.Popen[Any], process_group: int | None
) -> ReapDisposition:
    """Reap a normal-exit child group without risking recycled process identities.

    ``process_group`` must have been captured by `query_process_group` while the
    child was still alive. It is a parameter rather than a lookup so that the
    ordering requirement is visible in the signature: a group looked up here,
    after the child has exited, is unobtainable on macOS.
    """
    waitid = getattr(os, "waitid", None)
    wnowait = getattr(os, "WNOWAIT", None)
    if os.name == "nt" or waitid is None or wnowait is None:
        child.wait()
        return ReapDisposition.UNAVAILABLE

    if process_group is None:
        child.wait()
        return ReapDisposition.INCONCLUSIVE

    try:
        waitid(os.P_PID, child.pid, os.WEXITED | wnowait)
    except ChildProcessError:
        child.wait()
        return ReapDisposition.NOT_OWN_CHILD

    # EPERM here is the ORDINARY no-descendant case, not an error and not an
    # ambiguity. Measured on macOS, 8 runs of 8: with the child exited but
    # deliberately unreaped, the group's only member is that zombie and
    # `killpg` answers EPERM; with a live grandchild present it succeeds, 4 of
    # 4. Reading EPERM as inconclusive therefore reported every clean gate run
    # as inconclusive.
    #
    # It is sound to read it as success ONLY because the ownership proof above
    # already succeeded: `process_group` came from `os.getpgid` on our own
    # child, and that child is still unreaped, so the group is definitionally
    # ours and cannot have been recycled. A descendant that changed user id is
    # the one case this would misreport; it is named in the spec's Limitations
    # rather than silently assumed away.
    try:
        os.killpg(process_group, signal.SIGTERM)
    except ProcessLookupError:
        child.wait()
        return ReapDisposition.REAPED
    except PermissionError:
        child.wait()
        return ReapDisposition.REAPED

    time.sleep(PROCESS_TREE_REAP_GRACE_SECONDS)
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(process_group, signal.SIGKILL)
    child.wait()
    return ReapDisposition.REAPED


def run_child(command: Sequence[str], env: Mapping[str, str], cwd: Path) -> int:
    """Run a child, forwarding supported termination signals to its process group."""
    interrupted: list[int] = []
    tree_signals: list[ProcessTreeSignal] = []
    previous_handlers: dict[int, SignalHandler] = {}
    child: subprocess.Popen[Any] | None = None

    def forward(signum: int, _frame: FrameType | None) -> None:
        interrupted.append(signum)
        if child is not None:
            tree_signals.append(signal_process_tree(child, signum))

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
            child = spawn_child(command, env, cwd)
        except FileNotFoundError as error:
            raise ManagedChildError(f"gate executable {command[0]!r} was not found") from error
        # Captured here, while the child is certainly alive, and never looked up
        # again -- see query_process_group for why a later lookup cannot work.
        process_group = query_process_group(child)
        if interrupted:
            if not tree_signals:
                tree_signals.append(signal_process_tree(child, interrupted[0]))
            reap_process_tree(child, tree_signals[-1])
            return 128 + interrupted[0]
        try:
            disposition = reap_normal_exit_process_tree(child, process_group)
            if disposition is not ReapDisposition.REAPED:
                # AC13 requires the runner to SAY SO rather than degrade silently.
                # The return value used to be discarded, so every disposition test
                # asserted an enum the only caller threw away -- and the ordinary
                # fast-exit path (`query_process_group` returning None once the
                # child has already gone) produced INCONCLUSIVE with no reap and no
                # word of it.
                print(
                    "WARNING: normal-exit process-group reap did not complete "
                    f"({disposition.value}); a descendant may still hold resources "
                    "the child was using",
                    file=sys.stderr,
                    flush=True,
                )
        except KeyboardInterrupt:
            tree_signal = signal_process_tree(child, signal.SIGINT)
            reap_process_tree(child, tree_signal)
            return 130
        if interrupted:
            reap_process_tree(child, tree_signals[-1])
            return 128 + interrupted[0]
        return child.wait()
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
