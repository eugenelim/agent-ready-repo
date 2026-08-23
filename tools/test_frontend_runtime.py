from __future__ import annotations

import concurrent.futures
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from tools.repo import coordination_lease
from tools.repo import frontend_runtime as runtime


def _python_gate(output: Path, delay: float = 0.0) -> tuple[str, ...]:
    code = (
        "import os,sys,time;"
        "from pathlib import Path;"
        "Path(sys.argv[1]).write_text(os.environ['ARR_PREVIEW_PORT']);"
        "time.sleep(float(sys.argv[2]))"
    )
    return (sys.executable, "-c", code, str(output), str(delay))


def test_concurrent_gates_lease_different_ports(tmp_path: Path) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    outputs = (tmp_path / "first-port", tmp_path / "second-port")

    def invoke(output: Path) -> int:
        return runtime.run_gate(
            environ={},
            repo_root=tmp_path,
            common_dir=common_dir,
            gate_command=_python_gate(output, 0.4),
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(invoke, outputs))

    assert results == [0, 0]
    assert outputs[0].read_text() != outputs[1].read_text()
    assert not list((common_dir / runtime.LEASE_DIRECTORY).glob("*.json"))


def test_concurrent_acquirers_publish_one_complete_lease_per_port(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    lease_dir = common_dir / runtime.LEASE_DIRECTORY
    lease_dir.mkdir()
    stale_path = lease_dir / "preview-4321.json"
    stale_path.write_text(
        json.dumps(
            {
                "pid": 999_999_999,
                "token": "stale-owner",
                "port": runtime.DEFAULT_PREVIEW_PORT,
                "created_at": time.time() - runtime.LEASE_MAX_AGE_SECONDS - 1,
            }
        ),
        encoding="utf-8",
    )
    barrier = threading.Barrier(2)
    counter_lock = threading.Lock()
    link_calls = 0
    real_link = runtime.os.link

    def coordinated_link(source: Path, destination: Path) -> None:
        nonlocal link_calls
        if Path(destination).name == "preview-4321.json":
            payload = json.loads(Path(source).read_text(encoding="utf-8"))
            assert payload["token"]
            assert payload["created_at"]
            with counter_lock:
                link_calls += 1
            barrier.wait(timeout=2)
        real_link(source, destination)

    monkeypatch.setattr(runtime.os, "link", coordinated_link)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(runtime.lease_preview_port, common_dir, None)
            for _ in range(2)
        ]
        leases = [future.result() for future in futures]

    try:
        assert len({lease.port for lease in leases}) == 2
        assert link_calls >= 2
        lease_files = list(lease_dir.glob("*.json"))
        assert {path.name for path in lease_files} == {
            f"preview-{lease.port}.json" for lease in leases
        }
        for lease in leases:
            payload = json.loads(lease.path.read_text(encoding="utf-8"))
            assert payload["token"] == lease.token
    finally:
        for lease in leases:
            lease.release()


def test_young_empty_lease_is_not_stolen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lease_dir = tmp_path / runtime.LEASE_DIRECTORY
    lease_dir.mkdir()
    path = lease_dir / f"preview-{runtime.DEFAULT_PREVIEW_PORT}.json"
    path.touch()
    monkeypatch.setattr(runtime, "LEASE_RETRY_LIMIT", 2)
    monkeypatch.setattr(runtime, "LEASE_RETRY_DELAY_SECONDS", 0)

    with pytest.raises(runtime.FrontendRuntimeError, match="remained unreadable"):
        runtime.PortLease.try_acquire(tmp_path, runtime.DEFAULT_PREVIEW_PORT)

    assert path.exists()
    assert path.read_bytes() == b""


def test_old_empty_lease_is_reclaimable(tmp_path: Path) -> None:
    lease_dir = tmp_path / runtime.LEASE_DIRECTORY
    lease_dir.mkdir()
    path = lease_dir / f"preview-{runtime.DEFAULT_PREVIEW_PORT}.json"
    path.touch()
    old = time.time() - runtime.LEASE_MAX_AGE_SECONDS - 1
    os.utime(path, (old, old))

    lease = runtime.PortLease.try_acquire(tmp_path, runtime.DEFAULT_PREVIEW_PORT)

    assert lease is not None
    try:
        assert json.loads(path.read_text(encoding="utf-8"))["token"] == lease.token
    finally:
        lease.release()


def test_live_pid_lease_is_reclaimed_after_age_threshold(tmp_path: Path) -> None:
    lease = runtime.PortLease.try_acquire(tmp_path, runtime.DEFAULT_PREVIEW_PORT)
    assert lease is not None
    payload = json.loads(lease.path.read_text(encoding="utf-8"))
    payload["pid"] = os.getpid()
    payload["created_at"] = time.time() - runtime.LEASE_MAX_AGE_SECONDS - 1
    lease.path.write_text(json.dumps(payload), encoding="utf-8")

    replacement = runtime.PortLease.try_acquire(
        tmp_path, runtime.DEFAULT_PREVIEW_PORT
    )

    assert replacement is not None
    try:
        assert replacement.token != lease.token
        assert json.loads(replacement.path.read_text(encoding="utf-8"))[
            "created_at"
        ]
    finally:
        replacement.release()


def test_occupied_default_port_is_not_leased(tmp_path: Path) -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        try:
            listener.bind(("127.0.0.1", runtime.DEFAULT_PREVIEW_PORT))
            listener.listen()
        except OSError:
            pass

        lease = runtime.lease_preview_port(tmp_path, requested=None)
        try:
            assert lease.port != runtime.DEFAULT_PREVIEW_PORT
        finally:
            lease.release()
    finally:
        listener.close()


@pytest.mark.parametrize("value", ["bad", "1.5", "0", "-1", "65536", ""])
def test_invalid_arr_preview_port_has_no_fallback_or_lease(
    tmp_path: Path, value: str
) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()

    with pytest.raises(runtime.FrontendRuntimeError, match="ARR_PREVIEW_PORT"):
        runtime.run_gate(
            environ={"ARR_PREVIEW_PORT": value},
            repo_root=tmp_path,
            common_dir=common_dir,
            gate_command=(sys.executable, "-c", "raise SystemExit(0)"),
        )

    assert not (common_dir / runtime.LEASE_DIRECTORY).exists()


def test_valid_arr_preview_port_is_honoured(tmp_path: Path) -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = int(probe.getsockname()[1])
    probe.close()
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    output = tmp_path / "selected-port"

    result = runtime.run_gate(
        environ={"ARR_PREVIEW_PORT": str(port)},
        repo_root=tmp_path,
        common_dir=common_dir,
        gate_command=_python_gate(output),
    )

    assert result == 0
    assert output.read_text() == str(port)


def test_gate_failure_exit_code_is_propagated_and_lease_released(
    tmp_path: Path,
) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()

    result = runtime.run_gate(
        environ={},
        repo_root=tmp_path,
        common_dir=common_dir,
        gate_command=(sys.executable, "-c", "raise SystemExit(23)"),
    )

    assert result == 23
    assert not list((common_dir / runtime.LEASE_DIRECTORY).glob("*.json"))


def test_signal_handlers_are_installed_before_spawn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    signum = getattr(signal, "SIGTERM", None)
    if signum is None:
        pytest.skip("SIGTERM is unavailable on this platform")
    previous = signal.getsignal(signum)
    observed: dict[str, object] = {}

    class FakeChild:
        pid = 12345

        def wait(self) -> int:
            return 0

    def fake_popen(*_args: object, **kwargs: object) -> FakeChild:
        assert signal.getsignal(signum) is not previous
        observed.update(kwargs)
        return FakeChild()

    monkeypatch.setattr(runtime.subprocess, "Popen", fake_popen)

    assert runtime._run_child(("gate",), {}, tmp_path) == 0
    assert signal.getsignal(signum) is previous
    if os.name == "nt":
        assert observed["creationflags"]
    else:
        assert observed["start_new_session"] is True


def test_spawn_failure_restores_signal_handlers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    signum = getattr(signal, "SIGTERM", None)
    if signum is None:
        pytest.skip("SIGTERM is unavailable on this platform")
    previous = signal.getsignal(signum)

    def fail_spawn(*_args: object, **_kwargs: object) -> None:
        assert signal.getsignal(signum) is not previous
        raise FileNotFoundError

    monkeypatch.setattr(runtime.subprocess, "Popen", fail_spawn)

    with pytest.raises(runtime.FrontendRuntimeError, match="was not found"):
        runtime._run_child(("missing-gate",), {}, tmp_path)
    assert signal.getsignal(signum) is previous


@pytest.mark.skipif(os.name == "nt", reason="Windows SIGTERM forcibly ends subprocesses")
def test_gate_sigterm_terminates_descendants_and_releases_lease(
    tmp_path: Path,
) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    repo_root = Path(__file__).resolve().parent.parent
    grandchild_pid_path = tmp_path / "grandchild-pid"
    child_code = (
        "import subprocess,sys,time;"
        "from pathlib import Path;"
        "child=subprocess.Popen((sys.executable,'-c','import time; time.sleep(30)'));"
        "Path(sys.argv[1]).write_text(str(child.pid));"
        "time.sleep(30)"
    )
    wrapper_code = (
        "import sys;"
        "from pathlib import Path;"
        "from tools.repo.frontend_runtime import run_gate;"
        "raise SystemExit(run_gate("
        f"environ={{}},repo_root=Path({str(repo_root)!r}),"
        f"common_dir=Path({str(common_dir)!r}),"
        f"gate_command=(sys.executable,'-c',{child_code!r},"
        f"{str(grandchild_pid_path)!r})))"
    )
    wrapper = subprocess.Popen(
        (sys.executable, "-c", wrapper_code),
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    lease_dir = common_dir / runtime.LEASE_DIRECTORY
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (
        not list(lease_dir.glob("*.json")) or not grandchild_pid_path.exists()
    ):
        time.sleep(0.02)
    assert list(lease_dir.glob("*.json")), "wrapper did not acquire a lease"
    assert grandchild_pid_path.exists(), "gate parent did not spawn its child"
    grandchild_pid = int(grandchild_pid_path.read_text())

    wrapper.send_signal(signal.SIGTERM)
    wrapper.communicate(timeout=5)

    assert wrapper.returncode == 128 + signal.SIGTERM
    assert not list(lease_dir.glob("*.json"))
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and runtime._pid_is_alive(grandchild_pid):
        time.sleep(0.02)
    assert not runtime._pid_is_alive(grandchild_pid)


def test_stale_dead_owner_lease_is_reclaimed(tmp_path: Path) -> None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = int(probe.getsockname()[1])
    probe.close()
    lease_dir = tmp_path / runtime.LEASE_DIRECTORY
    lease_dir.mkdir()
    path = lease_dir / f"preview-{port}.json"
    path.write_text(
        json.dumps(
            {
                "pid": 999_999_999,
                "token": "stale-owner",
                "port": port,
            }
        ),
        encoding="utf-8",
    )

    lease = runtime.lease_preview_port(tmp_path, requested=port)
    try:
        assert json.loads(path.read_text(encoding="utf-8"))["token"] == lease.token
    finally:
        lease.release()
    assert not path.exists()


def test_release_preserves_replacement_owner_lease(tmp_path: Path) -> None:
    lease = runtime.PortLease.try_acquire(tmp_path, runtime.DEFAULT_PREVIEW_PORT)
    assert lease is not None
    replacement_token = "replacement-owner"
    lease.path.write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "token": replacement_token,
                "port": lease.port,
            }
        ),
        encoding="utf-8",
    )

    lease.release()

    assert lease.path.exists()
    assert json.loads(lease.path.read_text(encoding="utf-8"))["token"] == (
        replacement_token
    )

    replacement = runtime.PortLease(
        port=lease.port,
        path=lease.path,
        token=replacement_token,
    )
    replacement.release()
    assert not lease.path.exists()


def test_missing_npm_is_actionable_and_creates_no_lease(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    monkeypatch.setenv("PATH", "")

    with pytest.raises(runtime.FrontendRuntimeError, match="npm was not found"):
        runtime.run_gate(environ=os.environ, repo_root=tmp_path, common_dir=common_dir)

    assert not (common_dir / runtime.LEASE_DIRECTORY).exists()


def test_missing_playwright_is_actionable(tmp_path: Path) -> None:
    with pytest.raises(runtime.FrontendRuntimeError, match="Playwright is not installed"):
        runtime.install_browsers(environ={}, repo_root=tmp_path)


def test_install_browsers_runs_only_chromium(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "repo"
    executable_name = "playwright.cmd" if os.name == "nt" else "playwright"
    executable = repo_root / "web" / "node_modules" / ".bin" / executable_name
    executable.parent.mkdir(parents=True)
    log = tmp_path / "playwright-log"
    if os.name == "nt":
        executable.write_text(
            "@echo off\r\n"
            'echo %*^|%PLAYWRIGHT_BROWSERS_PATH%>"%PLAYWRIGHT_TEST_LOG%"\r\n'
            "exit /b 0\r\n",
            encoding="utf-8",
        )
    else:
        executable.write_text(
            f"#!{sys.executable}\n"
            "import os, sys\n"
            "from pathlib import Path\n"
            "Path(os.environ['PLAYWRIGHT_TEST_LOG']).write_text(\n"
            "    '|'.join(sys.argv[1:]) + '|' + "
            "os.environ['PLAYWRIGHT_BROWSERS_PATH'], encoding='utf-8'\n"
            ")\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
    monkeypatch.setenv("PLAYWRIGHT_TEST_LOG", str(log))
    cache = tmp_path / "shared-browser-cache"

    result = runtime.install_browsers(
        browsers_path=str(cache), environ=os.environ, repo_root=repo_root
    )

    assert result == 0
    assert log.read_text(encoding="utf-8") == f"install|chromium|{cache}"


def test_production_gate_command_remains_pinned() -> None:
    assert runtime.GATE_COMMAND == (
        "npm",
        "run",
        "test:e2e:gate",
        "--prefix",
        "web",
    )


def test_browser_cache_cli_path_has_highest_precedence(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cache = runtime.resolve_browser_cache(
        str(tmp_path / "explicit"),
        environ={
            "ARR_PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "arr"),
            "PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "playwright"),
        },
        repo_root=repo_root,
    )

    assert cache.path == (tmp_path / "explicit").resolve()
    assert cache.source == "explicit --browsers-path"


def test_browser_cache_arr_path_precedes_playwright_path(tmp_path: Path) -> None:
    cache = runtime.resolve_browser_cache(
        environ={
            "ARR_PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "arr"),
            "PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "playwright"),
        },
        repo_root=tmp_path / "repo",
    )

    assert cache.path == (tmp_path / "arr").resolve()
    assert cache.source == "ARR_PLAYWRIGHT_BROWSERS_PATH"


def test_browser_cache_uses_non_hermetic_playwright_path(tmp_path: Path) -> None:
    cache = runtime.resolve_browser_cache(
        environ={"PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "playwright")},
        repo_root=tmp_path / "repo",
    )

    assert cache.path == (tmp_path / "playwright").resolve()
    assert cache.source == "PLAYWRIGHT_BROWSERS_PATH"


def test_browser_cache_uses_platform_default(tmp_path: Path) -> None:
    cache = runtime.resolve_browser_cache(environ={}, repo_root=tmp_path)

    assert cache.path == runtime._platform_browser_cache({}).resolve()
    assert cache.source == "platform default"


def test_hermetic_playwright_path_warns_and_uses_default(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cache = runtime.resolve_browser_cache(
        environ={"PLAYWRIGHT_BROWSERS_PATH": "0"}, repo_root=tmp_path
    )
    runtime.announce_browser_cache(cache)
    captured = capsys.readouterr()

    assert cache.source == "platform default"
    assert "PLAYWRIGHT_BROWSERS_PATH=0" in captured.err
    assert "node_modules" in captured.err


def test_repository_local_browser_cache_is_rejected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"

    with pytest.raises(runtime.FrontendRuntimeError, match="inside the repository"):
        runtime.resolve_browser_cache(
            str(repo_root / ".cache"), environ={}, repo_root=repo_root
        )

    assert not repo_root.exists()


def test_empty_explicit_browser_cache_is_rejected_without_mutation(
    tmp_path: Path,
) -> None:
    with pytest.raises(runtime.FrontendRuntimeError, match="must not be empty"):
        runtime.resolve_browser_cache("", environ={}, repo_root=tmp_path)

    assert not list(tmp_path.iterdir())


def _port_reporting_gate(output: Path) -> tuple[str, ...]:
    """A gate that tolerates an absent port, so the unleased path is observable."""
    code = (
        "import os,sys;"
        "from pathlib import Path;"
        "Path(sys.argv[1]).write_text(os.environ.get('ARR_PREVIEW_PORT','unset'))"
    )
    return (sys.executable, "-c", code, str(output))


def test_an_unresolvable_worktree_warns_and_still_runs_the_gate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC9 names an unresolvable worktree a warn-and-run case, not an exit 2.

    Resolution ran above the fail-open handler, so a missing git or a failing
    rev-parse raised FrontendRuntimeError straight past it and failed a job the lease
    is forbidden to fail. A temporary directory is not a Git repository, so this is
    the real `git rev-parse` refusing rather than a patched one.
    """
    output = tmp_path / "reported-port"
    assert runtime.run_gate(
        environ={},
        repo_root=tmp_path,
        gate_command=_port_reporting_gate(output),
    ) == 0

    assert output.read_text(encoding="utf-8") == "unset"
    captured = capsys.readouterr()
    assert "unleased" in captured.err


def test_an_explicit_port_survives_an_unresolvable_worktree(tmp_path: Path) -> None:
    """Degrading the lease must not also discard the caller's own choice."""
    output = tmp_path / "reported-port"
    assert runtime.run_gate(
        port="4399",
        environ={},
        repo_root=tmp_path,
        gate_command=_port_reporting_gate(output),
    ) == 0

    assert output.read_text(encoding="utf-8") == "4399"


def test_the_browser_gate_holds_activity_and_takes_no_run_slot(tmp_path: Path) -> None:
    """The participant matrix's disposition for this entry point, made falsifiable.

    The matrix says the browser gate publishes an `activity` claim and takes no
    admission slot, and that removing the claim must redden its own test. Nothing
    asserted it, so the disposition was a description. Observed from inside the
    running child, because a claim released on exit is invisible afterwards.
    """
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    observed = tmp_path / "claims-during-the-run"
    lease_dir = common_dir / coordination_lease.LEASE_DIRECTORY
    reporter = (
        "import sys;"
        "from pathlib import Path;"
        "d = Path(sys.argv[1]);"
        "names = sorted(p.name for p in d.glob('*.lease')) if d.is_dir() else [];"
        "Path(sys.argv[2]).write_text('\\n'.join(names))"
    )

    assert runtime.run_gate(
        environ={},
        repo_root=tmp_path,
        common_dir=common_dir,
        gate_command=(sys.executable, "-c", reporter, str(lease_dir), str(observed)),
    ) == 0

    names = [line for line in observed.read_text(encoding="utf-8").splitlines() if line]
    assert any(name.startswith("activity-") for name in names), names
    assert not any(name.startswith("run-slot-") for name in names), names
