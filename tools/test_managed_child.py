"""Construction tests for the shared managed child-process runner."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

from tools.repo import frontend_runtime, managed_child
from tools.repo.managed_child import ReapDisposition


@pytest.fixture
def normal_exit_tree() -> tuple[Path, tuple[str, ...]]:
    """Provide a child command that leaves one sleeping descendant behind."""
    root = Path(tempfile.mkdtemp()).resolve()
    grandchild_pid = root / "grandchild.pid"
    child_code = (
        "import subprocess,sys;"
        "from pathlib import Path;"
        "grandchild=subprocess.Popen((sys.executable,'-c','import time; time.sleep(30)'));"
        "Path(sys.argv[1]).write_text(str(grandchild.pid));"
    )
    return root, (sys.executable, "-c", child_code, str(grandchild_pid))


@pytest.fixture
def signalable_child(tmp_path: Path) -> subprocess.Popen[str]:
    """Start one independently addressable child process group."""
    child = subprocess.Popen(
        (sys.executable, "-c", "import time; time.sleep(30)"),
        cwd=tmp_path.resolve(),
        start_new_session=True,
        text=True,
    )
    yield child
    if child.poll() is None:
        child.kill()
    child.wait()


@pytest.fixture
def group(signalable_child: subprocess.Popen[str]) -> int | None:
    """The child's process group, captured while it is certainly still alive.

    Fixtures resolve before the test body, and ``signalable_child`` sleeps, so
    this is the ordering `query_process_group` documents. Capturing inside a body
    that has already signalled the child would fail.
    """
    return managed_child.query_process_group(signalable_child)


@pytest.fixture
def managed_cwd(tmp_path: Path) -> Path:
    """Return a canonical working directory for fake and real child runs."""
    return tmp_path.resolve()


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_normal_exit_reaps_a_real_grandchild(
    normal_exit_tree: tuple[Path, tuple[str, ...]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A zero-exit child cannot leave its original process group behind."""
    root, command = normal_exit_tree
    monkeypatch.setattr(managed_child, "PROCESS_TREE_REAP_GRACE_SECONDS", 0.01)

    assert managed_child.run_child(command, {}, root) == 0

    grandchild_pid = int((root / "grandchild.pid").read_text(encoding="utf-8"))
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and managed_child.pid_is_alive(grandchild_pid):
        time.sleep(0.01)
    assert not managed_child.pid_is_alive(grandchild_pid)


@pytest.mark.skipif(os.name == "nt", reason="POSIX waitid is required")
def test_normal_exit_refuses_an_unowned_group_but_reaps_an_owned_one(
    signalable_child: subprocess.Popen[str], managed_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ownership refusal is observed through sends, with a positive control."""
    sends: list[tuple[int, int]] = []
    original_killpg = os.killpg

    def record_killpg(process_group: int, signum: int) -> None:
        sends.append((process_group, signum))
        original_killpg(process_group, signum)

    monkeypatch.setattr(managed_child.os, "killpg", record_killpg)
    monkeypatch.setattr(managed_child, "PROCESS_TREE_REAP_GRACE_SECONDS", 0.01)

    class NotOurChild:
        pid = os.getpid()

        def wait(self) -> int:
            return 0

    try:
        refusal = managed_child.reap_normal_exit_process_tree(NotOurChild(), os.getpgid(os.getpid()))
        assert refusal is managed_child.ReapDisposition.NOT_OWN_CHILD
        assert sends == []

        # Positive control. The child exits on its own and leaves a LIVE
        # grandchild, so `killpg` genuinely succeeds and a send is observable.
        #
        # It must not be signalled with Popen.send_signal to get it to exit:
        # send_signal calls poll(), poll() REAPS an already-exited child, and a
        # reaped pid makes os.waitid raise ChildProcessError -- so the ownership
        # proof would correctly refuse and emit no send. Under load the child
        # loses that race, which is what made an earlier version of this test
        # flake. Letting the child exit by itself removes the race entirely.
        owned = managed_child.spawn_child(
            (
                sys.executable,
                "-c",
                "import subprocess,sys;"
                "subprocess.Popen((sys.executable,'-c','import time; time.sleep(30)'));"
                "raise SystemExit(0)",
            ),
            dict(os.environ),
            managed_cwd,
        )
        owned_group = managed_child.query_process_group(owned)
        assert (
            managed_child.reap_normal_exit_process_tree(owned, owned_group)
            is managed_child.ReapDisposition.REAPED
        )
        assert owned.returncode == 0
        assert sends, "positive control observed no send, so the refusal proves nothing"
    finally:
        if signalable_child.poll() is None:
            signalable_child.kill()


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_an_already_reaped_child_refuses_rather_than_signalling(
    managed_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A child reaped before the call cannot be proved ours, so nothing is sent.

    This pins an invariant the production path depends on: nothing may poll or
    wait on the child before the reap runs. ``Popen.send_signal`` and
    ``Popen.poll`` both reap an exited child, and a reaped pid can be recycled,
    so the ownership proof must fail closed rather than signal a group it can no
    longer prove it owns. A future edit that polls first would otherwise
    silently disable the reap while every other test stayed green.
    """
    sends: list[int] = []
    monkeypatch.setattr(
        managed_child.os, "killpg", lambda _group, signum: sends.append(signum)
    )
    child = managed_child.spawn_child(
        (sys.executable, "-c", "raise SystemExit(0)"), dict(os.environ), managed_cwd
    )
    assert child.wait() == 0  # reaps it, exactly as a stray poll() would

    disposition = managed_child.reap_normal_exit_process_tree(child, group)

    # Two refusals are reachable and which one fires is not ours to fix. Usually
    # the pid is gone, so `os.getpgid` fails and the answer is INCONCLUSIVE. If
    # the pid has already been recycled, `os.getpgid` succeeds against a stranger
    # and the ownership proof rejects it as NOT_OWN_CHILD. Asserting one of them
    # specifically made this test fail intermittently for a reason that had
    # nothing to do with the invariant.
    #
    # The invariant is that it fails CLOSED and signals nothing, so that is what
    # is asserted. `sends == []` is the load-bearing half: a recycled pid must
    # never receive a signal.
    assert disposition is not managed_child.ReapDisposition.REAPED
    assert disposition in {
        managed_child.ReapDisposition.INCONCLUSIVE,
        managed_child.ReapDisposition.NOT_OWN_CHILD,
    }
    assert sends == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX signals are required")
@pytest.mark.parametrize("signum", (signal.SIGINT, signal.SIGTERM))
def test_signal_forwarding_reaches_the_child_group(
    signum: int,
    signalable_child: subprocess.Popen[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The interrupt path sends directly to the queried child process group."""
    observed: list[tuple[int, int]] = []

    def record_killpg(process_group: int, forwarded: int) -> None:
        observed.append((process_group, forwarded))

    monkeypatch.setattr(managed_child.os, "killpg", record_killpg)

    result = managed_child.signal_process_tree(signalable_child, signum)

    assert result.process_group == os.getpgid(signalable_child.pid)
    assert observed == [(result.process_group, signum)]


@pytest.mark.skipif(os.name == "nt", reason="POSIX signals are required")
def test_handler_only_sends_and_main_flow_escalates(
    signalable_child: subprocess.Popen[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Forwarding has no waits; the caller-owned reap performs escalation."""
    operations: list[str] = []

    original_killpg = os.killpg

    def record_killpg(process_group: int, signum: int) -> None:
        operations.append(signal.Signals(signum).name)
        if signum == signal.SIGKILL:
            original_killpg(process_group, signum)

    monkeypatch.setattr(managed_child.os, "killpg", record_killpg)
    monkeypatch.setattr(managed_child, "PROCESS_TREE_EXIT_TIMEOUT_SECONDS", 0.01)

    def refuse_wait(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("signal handler must not wait")

    with monkeypatch.context() as handler_scope:
        handler_scope.setattr(signalable_child, "wait", refuse_wait)
        signal_result = managed_child.signal_process_tree(
            signalable_child, signal.SIGTERM
        )
    assert operations == ["SIGTERM"]
    assert managed_child.reap_process_tree(signalable_child, signal_result) is None
    assert operations == ["SIGTERM", "SIGKILL"]


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_process_group_is_queried_not_assumed(
    signalable_child: subprocess.Popen[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A queried group distinct from the pid is the group sent a signal."""
    observed: list[tuple[int, int]] = []
    queried_group = 987_654

    monkeypatch.setattr(managed_child.os, "getpgid", lambda _pid: queried_group)
    monkeypatch.setattr(
        managed_child.os,
        "killpg",
        lambda group, signum: observed.append((group, signum)),
    )

    assert managed_child.signal_process_tree(signalable_child, signal.SIGTERM).process_group == queried_group
    assert observed == [(queried_group, signal.SIGTERM)]


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_reap_uses_the_queried_group_not_the_child_pid(
    signalable_child: subprocess.Popen[str],
    group: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reap signals the group it was handed, not the child's own identity.

    Substituting ``child.pid`` internally is invisible to any behavioural
    assertion on this platform, because ``start_new_session`` makes the two
    equal. Handing in a group the pid demonstrably is not, and insisting that is
    what gets signalled, is the only way to falsify the clause.
    """
    sends: list[int] = []
    sentinel_group = 987_654
    assert group != sentinel_group
    monkeypatch.setattr(
        managed_child.os, "killpg", lambda target, _signum: sends.append(target)
    )
    signalable_child.send_signal(signal.SIGTERM)

    managed_child.reap_normal_exit_process_tree(signalable_child, sentinel_group)

    assert sends and set(sends) == {sentinel_group}


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_permission_error_after_the_proof_is_success_without_escalation(
    signalable_child: subprocess.Popen[str],
    group: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EPERM reached after the ownership proof is success, with no escalation.

    The group id came from ``os.getpgid`` on our own child and that child is
    still unreaped, so the group is provably ours and EPERM means it holds no
    signalable live member. The original expectation here was INCONCLUSIVE,
    which execution disproved: the kernel answers EPERM for the ordinary
    no-descendant case, so every clean gate run reported inconclusive.
    """
    sends: list[int] = []

    def deny_killpg(_process_group: int, signum: int) -> None:
        sends.append(signum)
        raise PermissionError

    monkeypatch.setattr(managed_child.os, "killpg", deny_killpg)
    signalable_child.send_signal(signal.SIGTERM)

    assert (
        managed_child.reap_normal_exit_process_tree(signalable_child, group)
        is managed_child.ReapDisposition.REAPED
    )
    assert sends == [signal.SIGTERM]


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_a_real_childless_exit_is_reaped_with_nothing_mocked() -> None:
    """The ordinary case, against the real kernel rather than a patched killpg.

    This is the case the first implementation got wrong, and it slipped through
    because every other disposition test patches ``os.killpg``. Nothing is
    patched here on purpose: a fixture cannot testify about kernel behaviour.
    """
    child = managed_child.spawn_child(
        (sys.executable, "-c", "raise SystemExit(0)"), dict(os.environ), Path.cwd()
    )
    child_group = managed_child.query_process_group(child)
    assert child_group is not None

    assert (
        managed_child.reap_normal_exit_process_tree(child, child_group)
        is managed_child.ReapDisposition.REAPED
    )
    assert child.returncode == 0


@pytest.mark.skipif(os.name == "nt", reason="POSIX waitid is required")
def test_missing_nonreaping_wait_reports_unavailable_without_a_group_send(
    signalable_child: subprocess.Popen[str],
    group: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No ownership proof means no normal-exit process-group signal."""
    sends: list[tuple[int, int]] = []
    monkeypatch.setattr(managed_child.os, "waitid", None)
    monkeypatch.setattr(
        managed_child.os,
        "killpg",
        lambda group, signum: sends.append((group, signum)),
    )
    signalable_child.send_signal(signal.SIGTERM)

    assert (
        managed_child.reap_normal_exit_process_tree(signalable_child, group)
        is managed_child.ReapDisposition.UNAVAILABLE
    )
    assert sends == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_unqueryable_group_is_inconclusive_without_a_send(
    signalable_child: subprocess.Popen[str],
    group: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A group that could not be identified cannot be safely signalled.

    The capture happens at spawn now, so an unidentifiable group arrives as
    ``None`` rather than as a raising ``getpgid``. Verify the real capture path
    also yields ``None`` when the query fails, so this is not merely asserting
    that ``None`` is handled.
    """
    sends: list[tuple[int, int]] = []
    monkeypatch.setattr(
        managed_child.os,
        "getpgid",
        lambda _pid: (_ for _ in ()).throw(OSError("cannot query group")),
    )
    assert managed_child.query_process_group(signalable_child) is None
    monkeypatch.setattr(
        managed_child.os,
        "killpg",
        lambda group, signum: sends.append((group, signum)),
    )
    signalable_child.send_signal(signal.SIGTERM)

    assert (
        managed_child.reap_normal_exit_process_tree(signalable_child, None)
        is managed_child.ReapDisposition.INCONCLUSIVE
    )
    assert sends == []


@pytest.mark.skipif(os.name == "nt", reason="POSIX waitid is required")
def test_an_empty_owned_group_is_a_silent_success(
    signalable_child: subprocess.Popen[str],
    group: int | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ProcessLookupError represents an already-empty group, not a failure."""
    signalable_child.send_signal(signal.SIGTERM)
    monkeypatch.setattr(
        managed_child.os,
        "killpg",
        lambda _group, _signum: (_ for _ in ()).throw(ProcessLookupError),
    )

    assert (
        managed_child.reap_normal_exit_process_tree(signalable_child, group)
        is managed_child.ReapDisposition.REAPED
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups are required")
def test_a_non_reaped_disposition_is_reported_by_the_runner(
    managed_cwd: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A degraded reap must be SAID, not swallowed.

    `run_child` discarded the disposition, so every disposition test in this file
    asserted an enum the only caller threw away -- and the ordinary fast-exit path
    produced INCONCLUSIVE with no reap and no word of it. AC13 requires the runner
    to say so, so the report is what this asserts, not the enum.
    """
    monkeypatch.setattr(managed_child, "query_process_group", lambda _child: None)

    code = managed_child.run_child(
        (sys.executable, "-c", "raise SystemExit(4)"), dict(os.environ), managed_cwd
    )

    assert code == 4, "the child's verdict must survive a degraded reap"
    captured = capsys.readouterr()
    assert "normal-exit process-group reap did not complete" in captured.err
    assert ReapDisposition.INCONCLUSIVE.value in captured.err


def test_a_clean_reap_reports_nothing(
    managed_cwd: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The healthy path stays silent, so the warning above means something."""
    code = managed_child.run_child(
        (sys.executable, "-c", "raise SystemExit(0)"), dict(os.environ), managed_cwd
    )

    assert code == 0
    assert "reap did not complete" not in capsys.readouterr().err


def test_frontend_runtime_delegates_to_the_single_runner() -> None:
    """A forwarding wrapper or copied group signal is not an implementation share."""
    source = Path(frontend_runtime.__file__).read_text(encoding="utf-8")

    assert frontend_runtime._run_child is managed_child.run_child
    assert "os.killpg" not in source
