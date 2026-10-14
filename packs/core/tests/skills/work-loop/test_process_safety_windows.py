"""Windows launches run in a breakaway-denied Job Object.

VI-5001 (AC-0021, AC-0022), VI-5002 (AC-0023), VI-5003 (AC-0024). Runs only on
Windows; the POSIX launch path is covered, unchanged, by test_process_safety.py.
Every child is this interpreter, so no other binary is needed.
"""

from __future__ import annotations

import ctypes
import hashlib
import importlib.util
import json
import os
import stat
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows Job Object launch path")

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
PYTHON = str(Path(sys.executable).resolve())
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259


def _load() -> ModuleType:
    path = SCRIPTS / "_process_safety.py"
    assert stat.S_ISREG(os.lstat(path).st_mode)
    name = "core_work_loop_process_safety_windows"
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


@pytest.fixture(scope="module")
def ps() -> ModuleType:
    return _load()


def _python_hash() -> str:
    digest = hashlib.sha256()
    with Path(PYTHON).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _spec(cwd: Path, code: str, *args: str, timeout: int = 20) -> dict:
    return {
        "schema_version": 1, "executable": PYTHON, "executable_identity": _python_hash(),
        "argv": ["-c", code, *args], "grant_id": "windows-job-test", "cwd": str(cwd),
        "environment_allowlist": ["SYSTEMROOT"], "stdin_mode": "closed",
        "process_tree_timeout_s": timeout, "output_bound_bytes": 65536,
    }


EVENTS: list[object] = []


def _sink(event: object) -> None:
    EVENTS.append(event)


def _launch(ps: ModuleType, tmp_path: Path, code: str, *args: str, timeout: int = 20,
            **kw: object) -> object:
    return ps.launch_safe_process(
        _spec(tmp_path, code, *args, timeout=timeout), cwd_roots=(str(tmp_path),),
        env_values={"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows")},
        audit_sink=_sink, **kw)


def _alive(pid: int) -> bool:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = ctypes.c_void_p
    handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong(0)
        k32.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code))
        return code.value == STILL_ACTIVE
    finally:
        k32.CloseHandle(ctypes.c_void_p(handle))


def _wait_gone(pids: list[int], seconds: float = 10.0) -> list[int]:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        survivors = [pid for pid in pids if _alive(pid)]
        if not survivors:
            return []
        time.sleep(0.1)
    return [pid for pid in pids if _alive(pid)]


# The child reports its own job's limits, read before it does anything else.
JOB_REPORT = r"""
import ctypes, json
from ctypes import wintypes
class Basic(ctypes.Structure):
    _fields_ = [("a", ctypes.c_int64), ("b", ctypes.c_int64), ("LimitFlags", wintypes.DWORD),
                ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("e", wintypes.DWORD),
                ("f", ctypes.c_size_t), ("g", wintypes.DWORD), ("h", wintypes.DWORD)]
class Extended(ctypes.Structure):
    _fields_ = [("Basic", Basic), ("io", ctypes.c_uint64 * 6), ("m", ctypes.c_size_t * 4)]
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
in_job = wintypes.BOOL()
k32.IsProcessInJob(ctypes.c_void_p(-1), None, ctypes.byref(in_job))
info = Extended()
ok = k32.QueryInformationJobObject(None, 9, ctypes.byref(info), ctypes.sizeof(info), None)
print(json.dumps({"in_job": bool(in_job.value), "ok": bool(ok),
                  "flags": info.Basic.LimitFlags}))
"""


def test_child_is_in_a_kill_on_close_job_without_breakaway(ps: ModuleType,
                                                           tmp_path: Path) -> None:
    result = _launch(ps, tmp_path, JOB_REPORT)
    assert result.exit_code == 0, result.stderr_redacted
    report = json.loads(result.stdout_redacted)
    assert report["in_job"] and report["ok"]
    assert report["flags"] & 0x2000, "kill-on-close is set"
    assert not report["flags"] & 0x800, "breakaway is not allowed"
    assert not report["flags"] & 0x1000, "silent breakaway is not allowed"


def test_assignment_failure_refuses_and_ends_the_process(ps: ModuleType, tmp_path: Path) -> None:
    marker = tmp_path / "ran.txt"
    code = f"open({str(marker)!r}, 'w').write('ran')"
    ps._JOB_ASSIGN_FAULT = lambda: False
    try:
        with pytest.raises(ps.ProcessDenied) as info:
            _launch(ps, tmp_path, code)
    finally:
        ps._JOB_ASSIGN_FAULT = None
    assert info.value.denial_code == "denied-job-object"
    time.sleep(0.5)
    assert not marker.exists(), "the suspended process never ran"


# Spawns descendants that write their pids, then sleeps past the timeout.
TREE = r"""
import subprocess, sys, time, os
mode, out = sys.argv[1], sys.argv[2]
py = sys.executable
sleeper = "import time, os, sys; open(sys.argv[1], 'a').write(str(os.getpid()) + chr(10)); time.sleep(120)"
if mode == "orphan":
    # An intermediate starts a grandchild and exits at once.
    middle = ("import subprocess, sys; subprocess.Popen([sys.executable, '-c', %r, %r]); "
              "sys.exit(0)") % (sleeper, out)
    subprocess.run([py, "-c", middle])
elif mode == "breakaway":
    try:
        subprocess.Popen([py, "-c", sleeper, out], creationflags=0x01000000)
        open(out + ".breakaway", "w").write("allowed")
    except OSError:
        open(out + ".breakaway", "w").write("refused")
        subprocess.Popen([py, "-c", sleeper, out])
else:
    subprocess.Popen([py, "-c", sleeper, out])
open(out, "a").write(str(os.getpid()) + chr(10))
time.sleep(120)
"""


@pytest.mark.parametrize("mode", ["orphan", "breakaway", "plain"])
def test_timeout_leaves_no_survivor(ps: ModuleType, tmp_path: Path, mode: str) -> None:
    pids_file = tmp_path / "pids.txt"
    with pytest.raises(ps.ProcessDenied) as info:
        _launch(ps, tmp_path, TREE, mode, str(pids_file), timeout=8)
    assert info.value.denial_code == "denied-timeout"
    pids = [int(line) for line in pids_file.read_text().split()]
    assert len(pids) >= 2, pids
    assert _wait_gone(pids) == []
    if mode == "breakaway":
        assert (tmp_path / "pids.txt.breakaway").read_text() == "refused"


def test_launch_contract_cases(ps: ModuleType, tmp_path: Path) -> None:
    # Stdin bytes are redacted from output too, so the child reports their length.
    echo = "import sys, os; sys.stdout.write(str(len(sys.stdin.read())) + ':' + os.environ['TOKEN']); sys.stderr.write('e')"
    spec = _spec(tmp_path, echo)
    spec["stdin_mode"] = "bounded-bytes"
    spec["environment_allowlist"] = ["SYSTEMROOT", "TOKEN"]
    result = ps.launch_safe_process(
        spec, cwd_roots=(str(tmp_path),), stdin_bytes=b"in:",
        env_values={"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
                    "TOKEN": "s3cret-value"}, audit_sink=_sink)
    assert result.exit_code == 0
    assert result.stdout_redacted == b"3:[REDACTED]"
    assert result.stderr_redacted == b"e" and result.output_was_redacted
    exit_three = _launch(ps, tmp_path, "import sys; sys.exit(3)")
    assert exit_three.exit_code == 3
    noisy = _spec(tmp_path, "import sys; sys.stdout.write('x' * 5000)")
    noisy["output_bound_bytes"] = 100
    bounded = ps.launch_safe_process(
        noisy, cwd_roots=(str(tmp_path),),
        env_values={"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows")},
        audit_sink=_sink)
    assert bounded.output_was_truncated and len(bounded.stdout_redacted) <= 100
    flood = _spec(tmp_path, "import sys, time\nwhile True: sys.stdout.write('x' * 65536)")
    flood["output_bound_bytes"] = 100
    with pytest.raises(ps.ProcessDenied) as info:
        ps.launch_safe_process(
            flood, cwd_roots=(str(tmp_path),),
            env_values={"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows")},
        audit_sink=_sink)
    assert info.value.denial_code == "denied-output-cap-exceeded"


PROBE_HANDLE = r"""
import ctypes, sys
k32 = ctypes.WinDLL("kernel32", use_last_error=True)
k32.GetFileType.argtypes = [ctypes.c_void_p]
kind = k32.GetFileType(ctypes.c_void_p(int(sys.argv[1])))
print("usable" if kind == 1 else "unusable")
"""


def test_an_inheritable_parent_handle_does_not_reach_the_child(ps: ModuleType,
                                                               tmp_path: Path) -> None:
    import msvcrt

    path = tmp_path / "secret.txt"
    path.write_text("parent only")
    fd = os.open(path, os.O_RDONLY)
    try:
        os.set_inheritable(fd, True)
        handle = msvcrt.get_osfhandle(fd)
        result = _launch(ps, tmp_path, PROBE_HANDLE, str(handle))
        assert result.stdout_redacted.strip() == b"unusable"
    finally:
        os.close(fd)


@pytest.mark.parametrize("tail", ["", ".", " ", ". ."], ids=["plain", "dot", "space", "mixed"])
def test_a_batch_file_is_refused_before_launch(ps: ModuleType, tmp_path: Path,
                                              tail: str) -> None:
    script = tmp_path / "tool.cmd"
    marker = tmp_path / "ran.txt"
    script.write_text(f"@echo ran> {marker}\r\n")
    digest = hashlib.sha256(script.read_bytes()).hexdigest()
    spec = _spec(tmp_path, "unused")
    spec.update({"executable": str(script) + tail, "executable_identity": digest,
                 "argv": ["a&echo injected"]})
    with pytest.raises(ps.ProcessDenied) as info:
        ps.launch_safe_process(spec, cwd_roots=(str(tmp_path),),
                               env_values={"SYSTEMROOT": os.environ.get("SYSTEMROOT", "")},
                               audit_sink=_sink)
    assert info.value.denial_code == "denied-non-native-executable"
    assert not marker.exists()
