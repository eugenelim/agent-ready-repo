"""Pi-hosted conformance: Core's named supervisor suites pass under Pi's shell tool.

An opt-in test. With Pi installed it starts ``pi --mode rpc`` offline from an
allowlisted environment, sends Pi one RPC ``bash`` command that runs the twelve
named Core suites under ``WORK_SUPERVISOR_INTEGRATION=1``, and passes only when
every case ran, none skipped, and the suites ran as a descendant of that Pi
process. No model is called and none of the maintainer's Pi configuration or
credentials reach Pi or pytest.

Run it (the opt-in variable is ``AGENT_READY_PI_CONFORMANCE``)::

    AGENT_READY_PI_CONFORMANCE=1 python -m pytest tests/roster/test_pi_hosted_conformance.py -q -rsP

On a passing run the output shows the ``pi`` path, ``pi --version`` and the
passed and collected counts. Without the variable, or without ``pi`` on
``PATH``, the real run skips and starts no process. The remaining tests are
pins: they drive the same launch, watcher and cleanup code against stub ``pi``
scripts and never touch a real Pi. CI runs the pins.

Roster-owned: it reads the pack tree. Placed above the bulk ``pytest tests/``
step in build-check.yml.

Spec: docs/specs/pi-runtime-compatibility/spec.md
"""

from __future__ import annotations

import contextlib
import json
import os
import queue
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITE_DIR = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop"

OPT_IN_VAR = "AGENT_READY_PI_CONFORMANCE"
RPC_ID = "conformance"

# Six hours, measured from sending the RPC command to receiving its response.
# The serial run took 8,508 s on a loaded machine; Pi's bash has no timeout.
DEADLINE_S = 21_600
WATCH_INTERVAL_S = 0.5  # the spec requires at least one sample a second
MAX_SAMPLE_GAP_S = 1.0  # a longer gap between watcher samples fails the run
PS_TIMEOUT_S = 5.0
TERM_GRACE_S = 10.0
PUMP_JOIN_S = 10.0  # bound on waiting for Pi's stdout to reach EOF after cleanup

PI_FLAGS = (
    "--mode",
    "rpc",
    "--offline",
    "--no-session",
    "--no-extensions",
    "--no-skills",
    "--no-context-files",
    "--no-mcp",
    "--no-approve",
)

SUITE_FILES = (
    "test_supervisor_step_loop.py",
    "test_supervisor_product_ref.py",
    "test_supervisor_crash_corpus.py",
    "test_supervisor_admission.py",
    "test_policy_import.py",
    "test_supervisor_attempt.py",
    "test_containment_broker.py",
    "test_supervisor_untrusted_unsafe_host.py",
    "test_security_primitives.py",
    "test_audit_boundary_invariant.py",
    "test_review_persistence.py",
    "test_review_bridge.py",
)

# ═══════════════════════════════════════════════════════════════════════════════
# Environment, command and pass criteria (pure)
# ═══════════════════════════════════════════════════════════════════════════════


def child_env(base: Mapping[str, str], home: Path, tmpdir: Path) -> dict[str, str]:
    """Return the child environment: the allowlist and nothing else."""
    env = {
        "PATH": base.get("PATH", os.defpath),
        "HOME": str(home),
        "TMPDIR": str(tmpdir),
        "LANG": base.get("LANG", "C"),
        "WORK_SUPERVISOR_INTEGRATION": "1",
    }
    env.update({k: v for k, v in base.items() if k.startswith("LC_")})
    return env


def build_command(python: str, suite_dir: Path, files: Sequence[str], results: Path) -> str:
    """Build the shell command Pi runs.

    It first records the variable names and ``PATH`` its shell sees (before
    ``cd``, which would add ``OLDPWD``), the shell's parent PID and the collected
    case count, then runs exactly ``<python> -m pytest -p no:cacheprovider -q --junitxml=...``.
    """
    names = " ".join(shlex.quote(f) for f in files)
    py = shlex.quote(python)
    ppid = shlex.quote(str(results / "ppid"))
    collected = shlex.quote(str(results / "collected"))
    junit = shlex.quote(f"--junitxml={results / 'junit.xml'}")
    env_names = shlex.quote(str(results / "env-names"))
    path_file = shlex.quote(str(results / "path"))
    return (
        f"env | cut -d= -f1 > {env_names}"
        f' && printf %s "$PATH" > {path_file}'
        f" && cd {shlex.quote(str(suite_dir))}"
        f" && ps -o ppid= -p $$ | tr -d ' ' > {ppid}"
        f" && {py} -m pytest -p no:cacheprovider --collect-only -q {names}"
        f" | tail -n 1 > {collected}"
        f" && {py} -m pytest -p no:cacheprovider -q {junit} {names}"
    )


@dataclass(frozen=True)
class JunitSummary:
    """Totals and the files seen in one JUnit report."""

    total: int
    failures: int
    errors: int
    skipped: int
    modules: frozenset[str]


def read_junit(xml_text: str) -> JunitSummary:
    """Count cases, failures, errors and skips straight from the case elements."""
    root = ET.fromstring(xml_text)
    total = failures = errors = skipped = 0
    modules: set[str] = set()
    for suite in root.iter("testsuite"):
        # A report whose summary attributes disagree with its cases is not clean.
        for attr in ("failures", "errors", "skipped"):
            value = int(suite.get(attr, "0"))
            if attr == "failures":
                failures += value
            elif attr == "errors":
                errors += value
            else:
                skipped += value
    attr_failures, attr_errors, attr_skipped = failures, errors, skipped
    failures = errors = skipped = 0
    for case in root.iter("testcase"):
        total += 1
        failures += len(case.findall("failure"))
        errors += len(case.findall("error"))
        skipped += len(case.findall("skipped"))
        modules.update(Path(case.get("file", "")).name.removesuffix(".py").split())
        modules.update(case.get("classname", "").split("."))
    return JunitSummary(
        total=total,
        failures=max(failures, attr_failures),
        errors=max(errors, attr_errors),
        skipped=max(skipped, attr_skipped),
        modules=frozenset(modules),
    )


def parse_collected(text: str) -> int | None:
    """Read the case count from pytest's ``N tests collected`` line or a bare integer."""
    found = re.search(r"(\d+)\s+tests?\s+collected", text)
    if found:
        return int(found.group(1))
    bare = text.strip()
    return int(bare) if bare.isdigit() else None


def check_junit(xml_text: str, files: Sequence[str], collected: int | None) -> list[str]:
    """Return the reasons a JUnit report does not meet AC-0003 (empty when it does)."""
    try:
        summary = read_junit(xml_text)
    except (ET.ParseError, ValueError) as exc:
        return [f"junit.xml unreadable: {exc}"]
    problems: list[str] = []
    if summary.total == 0:
        problems.append("junit.xml holds no cases")
    if summary.failures:
        problems.append(f"{summary.failures} failure(s)")
    if summary.errors:
        problems.append(f"{summary.errors} error(s)")
    if summary.skipped:
        problems.append(f"{summary.skipped} skip(s)")
    for name in files:
        if name.removesuffix(".py") not in summary.modules:
            problems.append(f"no case from {name}")
    if collected is None:
        problems.append("collected count missing or unreadable")
    elif summary.total != collected:
        problems.append(f"{summary.total} cases ran but {collected} were collected")
    return problems


def check_ppid(text: str, pi_pid: int) -> list[str]:
    """Return a problem unless the recorded parent PID is the Pi process the harness started."""
    if text.strip() != str(pi_pid):
        return [f"shell parent PID {text.strip()!r} is not the Pi PID {pi_pid}"]
    return []


# What the shell adds to its own environment, and what Pi itself sets.
SHELL_OWN_NAMES = frozenset({"PWD", "SHLVL", "_", "__CF_USER_TEXT_ENCODING"})
PI_ADDED_NAMES = frozenset({"AI_AGENT", "PI_CODING_AGENT", "PI_OFFLINE", "PI_SKIP_VERSION_CHECK"})


def check_shell_env(
    names_text: str, path_text: str, env: Mapping[str, str], home: Path
) -> list[str]:
    """Return the reasons the variables Pi's shell saw are not the child environment.

    Every name must be a child-environment name, one the shell adds, or one Pi
    adds; ``PATH`` must be the child ``PATH``, optionally behind Pi's
    ``<HOME>/.pi/agent/bin``.
    """
    problems: list[str] = []
    allowed = set(env) | SHELL_OWN_NAMES | PI_ADDED_NAMES
    extra = sorted({n for n in names_text.splitlines() if n.strip() and n not in allowed})
    if extra:
        problems.append(f"Pi's shell saw variables outside the child environment: {extra}")
    child_path = env.get("PATH", "")
    pi_bin = str(home / ".pi" / "agent" / "bin")
    if path_text not in (child_path, f"{pi_bin}{os.pathsep}{child_path}"):
        problems.append(
            f"Pi's shell PATH {path_text!r} is not the child PATH {child_path!r}"
            f" optionally behind {pi_bin!r}"
        )
    return problems


# ═══════════════════════════════════════════════════════════════════════════════
# Process watcher
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class Proc:
    """One process-table row: identity is the PID plus its start time."""

    pid: int
    ppid: int
    start: datetime
    zombie: bool = False


def parse_ps(text: str) -> list[Proc]:
    """Parse ``ps -A -o pid=,ppid=,stat=,lstart=`` output taken under ``LC_ALL=C``."""
    rows: list[Proc] = []
    for line in text.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        try:
            start = datetime.strptime(" ".join(parts[3].split()), "%a %b %d %H:%M:%S %Y")
            rows.append(Proc(int(parts[0]), int(parts[1]), start, parts[2].startswith("Z")))
        except ValueError:
            continue
    return rows


@dataclass
class RunSet:
    """The recorded run processes, keyed by (PID, start time)."""

    root_pid: int
    harness_pid: int
    recorded: dict[tuple[int, datetime], Proc] = field(default_factory=dict)

    def observe(self, sample: Sequence[Proc]) -> list[Proc]:
        """Record every sampled process whose parent is a recorded run process.

        A parent counts only when its PID and start time both match a recorded
        process in this same sample, and the child started no earlier than it.
        Returns the processes newly recorded.
        """
        new: list[Proc] = []
        grew = True
        while grew:
            grew = False
            for proc in sample:
                key = (proc.pid, proc.start)
                if key in self.recorded:
                    continue
                if self._is_run_child(proc, sample):
                    self.recorded[key] = proc
                    new.append(proc)
                    grew = True
        return new

    def _is_run_child(self, proc: Proc, sample: Sequence[Proc]) -> bool:
        if proc.pid == self.root_pid and proc.ppid == self.harness_pid:
            return not any(pid == self.root_pid for pid, _ in self.recorded)
        for parent in sample:
            if parent.pid == proc.ppid and (parent.pid, parent.start) in self.recorded:
                return proc.start >= parent.start
        return False

    def alive(self, sample: Sequence[Proc]) -> list[Proc]:
        """Return recorded processes present in ``sample`` with their recorded start time."""
        return [p for p in sample if (p.pid, p.start) in self.recorded and not p.zombie]


def _ps_binary() -> str:
    return shutil.which("ps") or "/bin/ps"


class ProcessWatcher:
    """Polls the process table and records run processes until stopped."""

    def __init__(
        self, root_pid: int, ps_env: Mapping[str, str], interval_s: float = WATCH_INTERVAL_S
    ) -> None:
        self.runs = RunSet(root_pid=root_pid, harness_pid=os.getpid())
        self._ps_env = dict(ps_env)
        self._interval_s = interval_s
        self._lock = threading.Lock()
        self.cleaning = False  # set when cleanup starts
        self._last_sample: float | None = None
        self.unreadable: str | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="pi-process-watcher", daemon=True)

    def start(self) -> None:
        """Take a first sample, then keep sampling on a thread."""
        self.sample_now()
        self._thread.start()

    def stop(self) -> None:
        """Stop the sampling thread."""
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=60)

    def _loop(self) -> None:
        while not self._stop.wait(self._interval_s):
            self.sample_now()

    def _note_unreadable(self, reason: str) -> None:
        """Keep the first bad read from launch to the end of cleanup; any one fails the run."""
        if self.unreadable is None:
            self.unreadable = reason

    def snapshot(self) -> list[Proc]:
        """Read the process table once; a bad read, or a gap over the sampling bound, is noted."""
        now = time.monotonic()
        if self._last_sample is not None and now - self._last_sample > MAX_SAMPLE_GAP_S:
            self._note_unreadable(f"no sample for {now - self._last_sample:.1f} s")
        self._last_sample = now
        try:
            done = subprocess.run(
                [_ps_binary(), "-A", "-o", "pid=,ppid=,stat=,lstart="],
                env=self._ps_env,
                capture_output=True,
                text=True,
                timeout=PS_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self._note_unreadable(f"ps could not run: {exc}")
            return []
        rows = parse_ps(done.stdout)
        shown = sum(1 for line in done.stdout.splitlines() if line.strip())
        if done.returncode != 0:
            self._note_unreadable(f"ps exited {done.returncode}: {done.stderr.strip()[:200]!r}")
        elif not rows or len(rows) != shown:
            self._note_unreadable(f"ps output unparseable: {done.stdout[:200]!r}")
        return rows

    def sample_now(self) -> list[Proc]:
        """Sample once and record; return the newly recorded processes."""
        sample = self.snapshot()
        with self._lock:
            return self.runs.observe(sample)

    def live(self) -> list[Proc]:
        """Return recorded run processes alive now."""
        return self.runs.alive(self.snapshot())

    def signal_live(self, sig: signal.Signals) -> None:
        """Signal each recorded process alive now with its recorded start time."""
        for proc in self.live():
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(proc.pid, sig)


def end_popen(proc: subprocess.Popen[bytes]) -> None:
    """End Pi through its own handle: terminate, wait, kill, wait."""
    if proc.poll() is not None:
        return
    with contextlib.suppress(OSError):
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(OSError):
            proc.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=30)


def cleanup(
    proc: subprocess.Popen[bytes], watcher: ProcessWatcher, term_grace_s: float
) -> list[Proc]:
    """End every run process and the watcher; return recorded processes still alive.

    Pi is always ended through its own handle, whatever the process table says.
    """
    survivors: list[Proc] = []
    watcher.cleaning = True
    try:
        if proc.poll() is None:
            with contextlib.suppress(OSError):
                proc.terminate()
        watcher.signal_live(signal.SIGTERM)
        end = time.monotonic() + term_grace_s
        while time.monotonic() < end and (watcher.live() or proc.poll() is None):
            watcher.sample_now()
            time.sleep(0.1)
        end_popen(proc)
        for _ in range(50):
            watcher.signal_live(signal.SIGKILL)
            if not watcher.sample_now() and not watcher.live():
                break
        for _ in range(50):  # a killed process may stay in the table briefly
            survivors = watcher.live()
            if not survivors:
                break
            watcher.signal_live(signal.SIGKILL)
            time.sleep(0.1)
    finally:
        end_popen(proc)
        watcher.stop()
    return survivors


# ═══════════════════════════════════════════════════════════════════════════════
# The launch
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class RunOutcome:
    """What one launch produced."""

    pi_pid: int
    results: Path
    response: dict[str, Any] | None
    failure: str | None
    survivors: list[Proc]
    recorded: int
    env: Mapping[str, str]
    home: Path


def _fresh_dir(root: Path, name: str) -> Path:
    path = root / name
    path.mkdir()
    return path


def _pump(stream: Any, lines: queue.Queue[str | None]) -> None:
    try:
        for raw in stream:
            lines.put(raw.decode("utf-8", errors="replace"))
    finally:
        lines.put(None)


def _exchange(
    proc: subprocess.Popen[bytes],
    command: str,
    deadline_s: float,
    lines: queue.Queue[str | None],
) -> tuple[dict[str, Any] | None, str | None]:
    """Send the one RPC command and read until its response, a bad line, EOF or the deadline.

    ``lines`` is fed by the pump thread; the deadline starts once the command is sent.
    """
    assert proc.stdin is not None
    request = json.dumps({"id": RPC_ID, "type": "bash", "command": command})
    try:
        try:
            proc.stdin.write(request.encode() + b"\n")
            proc.stdin.flush()
        except OSError as exc:
            return None, f"could not send the command to Pi: {exc}"
        deadline_at = time.monotonic() + deadline_s
        while True:
            try:
                line = lines.get(timeout=max(deadline_at - time.monotonic(), 0.0))
            except queue.Empty:
                return None, f"deadline of {deadline_s} s passed without a response line"
            if line is None:
                return None, "Pi closed stdout before sending a response"
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError:
                return None, f"non-JSON line from Pi: {line!r}"
            if not isinstance(message, dict):
                return None, f"non-object JSON line from Pi: {line!r}"
            if message.get("type") == "response" and message.get("id") == RPC_ID:
                return message, None
    finally:
        with contextlib.suppress(OSError):
            proc.stdin.close()


def run_harness(
    pi: str,
    root: Path,
    deadline_s: float,
    *,
    base_env: Mapping[str, str] | None = None,
    repo_root: Path = REPO_ROOT,
    interval_s: float = WATCH_INTERVAL_S,
    term_grace_s: float = TERM_GRACE_S,
    before_send: Callable[[], None] | None = None,
) -> RunOutcome:
    """Start one Pi launch, send one RPC command, then clean up every run process.

    ``root`` is an existing empty directory; the launch's working directory,
    ``HOME``, ``TMPDIR`` and results directory are fresh children of it.
    ``before_send`` runs after Pi starts and before the command is sent, so a
    caller can wait for readiness without spending the deadline.
    """
    base = os.environ if base_env is None else base_env
    cwd = _fresh_dir(root, "cwd")
    home = _fresh_dir(root, "home")
    scratch = _fresh_dir(root, "scratch")
    results = _fresh_dir(root, "results")
    env = child_env(base, home, scratch)
    ps_env = {**env, "LC_ALL": "C"}  # a fixed-format lstart; no credentials
    command = build_command(
        sys.executable, repo_root / SUITE_DIR.relative_to(REPO_ROOT), SUITE_FILES, results
    )
    response: dict[str, Any] | None = None
    failure: str | None = None
    with (results / "pi.stderr").open("wb") as stderr:
        proc = subprocess.Popen(
            [pi, *PI_FLAGS],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            start_new_session=True,
        )
        assert proc.stdout is not None
        lines: queue.Queue[str | None] = queue.Queue()
        pump = threading.Thread(target=_pump, args=(proc.stdout, lines), daemon=True)
        pump.start()
        watcher = ProcessWatcher(proc.pid, ps_env, interval_s)
        watcher.start()
        survivors: list[Proc] = []
        try:
            if before_send is not None:
                before_send()
            response, failure = _exchange(proc, command, deadline_s, lines)
        finally:
            survivors = cleanup(proc, watcher, term_grace_s)
            # Pi and its run processes are gone, so the pipe reaches EOF; if a
            # survivor still holds it, leave the daemon pump rather than block.
            pump.join(timeout=PUMP_JOIN_S)
            if not pump.is_alive():
                proc.stdout.close()
    if watcher.unreadable:
        failure = "; ".join(
            filter(None, [failure, f"process table unreadable: {watcher.unreadable}"])
        )
    return RunOutcome(
        pi_pid=proc.pid,
        results=results,
        response=response,
        failure=failure,
        survivors=survivors,
        recorded=len(watcher.runs.recorded),
        env=env,
        home=home,
    )


def evaluate(outcome: RunOutcome, files: Sequence[str] = SUITE_FILES) -> list[str]:
    """Return every reason the run does not meet AC-0003, AC-0004 and AC-0006."""
    problems: list[str] = []
    if outcome.failure:
        problems.append(outcome.failure)
    for proc in outcome.survivors:
        problems.append(f"run process {proc.pid} still alive after cleanup")
    response = outcome.response
    if response is not None:
        data = response.get("data")
        data = data if isinstance(data, dict) else {}
        if response.get("success") is not True or data.get("exitCode") != 0:
            tail = str(data.get("output", ""))[-2000:]
            problems.append(
                f"response success={response.get('success')!r} "
                f"exitCode={data.get('exitCode')!r}; output tail:\n{tail}"
            )
    results = outcome.results
    junit, collected, ppid = (results / n for n in ("junit.xml", "collected", "ppid"))
    if not junit.is_file():
        problems.append("junit.xml was not written")
    else:
        count = parse_collected(collected.read_text()) if collected.is_file() else None
        problems += check_junit(junit.read_text(encoding="utf-8"), files, count)
    names, path_file = results / "env-names", results / "path"
    if not (names.is_file() and path_file.is_file()):
        problems.append("the shell environment files were not written")
    else:
        problems += check_shell_env(
            names.read_text(encoding="utf-8"),
            path_file.read_text(encoding="utf-8"),
            outcome.env,
            outcome.home,
        )
    if not ppid.is_file():
        problems.append("the shell parent PID file was not written")
    else:
        problems += check_ppid(ppid.read_text(), outcome.pi_pid)
    return problems


def version_of(pi: str, root: Path, base_env: Mapping[str, str] | None = None) -> str:
    """Return ``pi --version`` output, run with the child environment and its own fresh HOME."""
    base = os.environ if base_env is None else base_env
    home = _fresh_dir(root, "version-home")
    scratch = _fresh_dir(root, "version-scratch")
    done = subprocess.run(
        [pi, "--version"],
        cwd=home,
        env=child_env(base, home, scratch),
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    return (done.stdout + done.stderr).strip()


def require_opt_in() -> str:
    """Return the absolute ``pi`` path, or skip naming the missing opt-in or ``pi``."""
    if os.environ.get(OPT_IN_VAR) != "1":
        pytest.skip(f"set {OPT_IN_VAR}=1 to run the Pi-hosted conformance harness")
    found = shutil.which("pi")
    if found is None:
        pytest.skip("no `pi` executable on PATH")
    return str(Path(found).resolve())


# ═══════════════════════════════════════════════════════════════════════════════
# The real run (opt-in)
# ═══════════════════════════════════════════════════════════════════════════════


def test_pi_hosted_conformance(tmp_path: Path) -> None:
    """Run Core's named suites through Pi's RPC bash command; skip unless opted in."""
    pi = require_opt_in()
    version = version_of(pi, tmp_path)
    outcome = run_harness(pi, tmp_path, DEADLINE_S)
    problems = evaluate(outcome)
    assert not problems, "\n".join(problems)
    summary = read_junit((outcome.results / "junit.xml").read_text(encoding="utf-8"))
    collected = parse_collected((outcome.results / "collected").read_text())
    print(f"pi: {pi}")
    print(f"pi --version: {version}")
    print(f"passed: {summary.total} collected: {collected}")


# ═══════════════════════════════════════════════════════════════════════════════
# Pins (stub `pi`, no real Pi)
# ═══════════════════════════════════════════════════════════════════════════════

_STUB = r"""
import json, os, signal, subprocess, sys, time

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "out")
os.makedirs(out, exist_ok=True)
SLEEP = ["/bin/sleep", "600"]
PYQ = __PYQ__



def note(name, text):
    with open(os.path.join(out, name), "w") as fh:
        fh.write(str(text))


def snapshot():
    return {"argv": sys.argv[1:], "env": dict(os.environ), "cwd": os.getcwd(),
            "cwd_entries": os.listdir("."), "home": os.environ.get("HOME"),
            "home_entries": os.listdir(os.environ.get("HOME", "."))}


note("ran", "1")
if len(sys.argv) > 2 and sys.argv[1] == "--role":
    if sys.argv[2] == "child":
        gc = subprocess.Popen(SLEEP, start_new_session=True)
        note("grandchild.pid", gc.pid)
        time.sleep(float(sys.argv[3]))
        sys.exit(0)
    sys.exit(0)
if sys.argv[1:] == ["--version"]:
    note("version.json", json.dumps(snapshot()))
    print("stub-pi 9.9.9")
    sys.exit(0)

mode = open(os.path.join(here, "mode")).read().strip()
note("rpc.json", json.dumps(snapshot()))
note("stub.pid", os.getpid())


def wait_for(name):
    path = os.path.join(out, name)
    while not os.path.exists(path):
        time.sleep(0.05)


if mode in ("echo", "garbage", "eof") or mode.startswith("shell"):
    note("ready", "1")  # before reading stdin: the harness may now send
    line = sys.stdin.readline()
    note("rpc.line", line)
if mode == "echo":
    print(json.dumps({"type": "bash_execution_update", "id": "conformance"}), flush=True)
    print(json.dumps({"type": "response", "id": "other", "success": False}), flush=True)
    print(json.dumps({"type": "response", "id": "conformance", "command": "bash",
                      "success": True, "data": {"output": "", "exitCode": 0}}), flush=True)
    sys.stdin.read()
elif mode.startswith("shell"):
    # Run the harness's command in a shell, as Pi's bash tool does, with the
    # python it names swapped for a fake pytest; the variant tampers with the env.
    variant = mode.partition(":")[2]
    env = dict(os.environ)
    if variant == "extra":
        env["PLANTED_NAME"] = "1"
    elif variant == "path":
        env["PATH"] = "/planted/bin" + os.pathsep + env["PATH"]
    elif variant == "pibin":
        env["PATH"] = os.path.join(env["HOME"], ".pi", "agent", "bin") + os.pathsep + env["PATH"]
        env["AI_AGENT"] = "pi"
    fake = os.path.join(here, "fakepy")
    command = json.loads(line)["command"].replace(PYQ, fake)
    done = subprocess.run(["/bin/sh", "-c", command], env=env, capture_output=True, text=True)
    print(json.dumps({"type": "response", "id": "conformance", "command": "bash",
                      "success": True, "data": {"output": done.stderr,
                                                "exitCode": done.returncode}}), flush=True)
    sys.stdin.read()
elif mode == "garbage":
    print("not json at all", flush=True)
    time.sleep(600)
elif mode == "eof":
    sys.exit(0)
elif mode == "chain":
    child = subprocess.Popen([sys.executable, __file__, "--role", "child", "6"],
                             start_new_session=True)
    note("child.pid", child.pid)
    wait_for("grandchild.pid")
    note("ready", "1")
    time.sleep(600)
elif mode == "term_spawn":
    def on_term(signum, frame):
        spawned = subprocess.Popen(SLEEP, start_new_session=True)
        note("spawned.pid", spawned.pid)
    signal.signal(signal.SIGTERM, on_term)
    note("ready", "1")
    while True:
        time.sleep(0.2)
"""


def _make_stub(tmp_path: Path, mode: str) -> tuple[str, Path]:
    """Write a stub ``pi`` into ``tmp_path/bin``; return its path and its record directory."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "stub.py").write_text(
        _STUB.replace("__PYQ__", repr(shlex.quote(sys.executable))), encoding="utf-8"
    )
    fake = bin_dir / "fakepy"
    fake_body = (
        "#!/bin/sh\n"
        'case "$*" in *--collect-only*) echo "__COUNT__ tests collected in 0.01s"; exit 0;; esac\n'
        'for a in "$@"; do case "$a" in --junitxml=*) out="${a#--junitxml=}";; esac; done\n'
        'cat "$(dirname "$0")/junit.tmpl" > "$out"\n'
    )
    fake.write_text(fake_body.replace("__COUNT__", str(len(SUITE_FILES))), encoding="utf-8")
    fake.chmod(0o755)
    (bin_dir / "junit.tmpl").write_text(_junit(SUITE_FILES), encoding="utf-8")
    (bin_dir / "mode").write_text(mode, encoding="utf-8")
    pi = bin_dir / "pi"
    pi.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" "{bin_dir / "stub.py"}" "$@"\n', encoding="utf-8"
    )
    pi.chmod(pi.stat().st_mode | stat.S_IXUSR)
    return str(pi), bin_dir / "out"


def _run_root(tmp_path: Path) -> Path:
    root = tmp_path / "run"
    root.mkdir()
    return root


def _pid_alive(pid: int) -> bool:
    done = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True, check=False
    )
    state = done.stdout.strip()
    return bool(state) and not state.startswith("Z")


def _wait_gone(pid: int, timeout_s: float = 15.0) -> bool:
    end = time.monotonic() + timeout_s
    while time.monotonic() < end:
        if not _pid_alive(pid):
            return True
        time.sleep(0.1)
    return not _pid_alive(pid)


def _pid_from(out: Path, name: str) -> int:
    assert (out / name).is_file(), (
        f"the stub never recorded {name}; its files: {sorted(out.iterdir())}"
    )
    return int((out / name).read_text())


def _wait_ready(out: Path, timeout_s: float = 120.0) -> Callable[[], None]:
    """Return a hook that waits for the stub's ready file, so the deadline starts after it."""

    def wait() -> None:
        end = time.monotonic() + timeout_s
        while not (out / "ready").exists():
            assert time.monotonic() < end, f"the stub did not signal ready within {timeout_s} s"
            time.sleep(0.05)

    return wait


# Variables the stub's own /bin/sh and interpreter add after launch.
_SHELL_NOISE = {"PWD", "OLDPWD", "SHLVL", "_", "__CF_USER_TEXT_ENCODING"}
_T0 = datetime(2026, 11, 5, 12, 0, 0)


def _p(pid: int, ppid: int, offset_s: int, zombie: bool = False) -> Proc:
    return Proc(pid, ppid, _T0 + timedelta(seconds=offset_s), zombie)


JUNIT_OK = (
    '<testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="{n}">'
    "{cases}</testsuite></testsuites>"
)


def _junit(files: Sequence[str], extra: str = "", skip_file: str | None = None) -> str:
    cases = "".join(
        f'<testcase classname="{f.removesuffix(".py")}.TestX" name="t"/>'
        for f in files
        if f != skip_file
    )
    cases += extra
    return JUNIT_OK.format(n=cases.count("<testcase"), cases=cases)


class TestJunitReader:
    """AC-0003: the JUnit reader reds on each unclean report."""

    def test_clean_report_is_green(self) -> None:
        n = len(SUITE_FILES)
        assert check_junit(_junit(SUITE_FILES), SUITE_FILES, n) == []

    @pytest.mark.parametrize(
        ("child", "named"), [("failure", "failure"), ("error", "error"), ("skipped", "skip")]
    )
    def test_failure_error_skip_red(self, child: str, named: str) -> None:
        extra = f'<testcase classname="test_review_bridge.TestX" name="bad"><{child}/></testcase>'
        problems = check_junit(_junit(SUITE_FILES, extra), SUITE_FILES, len(SUITE_FILES) + 1)
        assert problems == [f"1 {named}(s)"]

    def test_missing_named_file_red(self) -> None:
        xml = _junit(SUITE_FILES, skip_file="test_policy_import.py")
        problems = check_junit(xml, SUITE_FILES, len(SUITE_FILES) - 1)
        assert any("test_policy_import.py" in p for p in problems)

    def test_empty_report_red(self) -> None:
        assert check_junit("<testsuites/>", SUITE_FILES, 0)
        assert check_junit("", SUITE_FILES, 0)

    def test_total_below_collected_red(self) -> None:
        problems = check_junit(_junit(SUITE_FILES), SUITE_FILES, len(SUITE_FILES) + 5)
        assert any("collected" in p for p in problems)

    def test_unreadable_collected_red(self) -> None:
        assert check_junit(_junit(SUITE_FILES), SUITE_FILES, None)

    def test_collected_parser(self) -> None:
        assert parse_collected("875 tests collected in 1.20s\n") == 875
        assert parse_collected("1 test collected in 0.01s") == 1
        assert parse_collected("12\n") == 12
        assert parse_collected("error: nothing") is None


class TestAncestry:
    """AC-0004: the ancestry check reds on a foreign parent PID."""

    def test_matching_pid_green(self) -> None:
        assert check_ppid("4242\n", 4242) == []

    def test_foreign_pid_red(self) -> None:
        assert check_ppid("1\n", 4242)
        assert check_ppid("", 4242)


class TestRunSet:
    """AC-0006: the watcher's parent check uses PID and start time together."""

    def test_records_descendants_across_samples(self) -> None:
        runs = RunSet(root_pid=100, harness_pid=1)
        runs.observe([_p(100, 1, 0), _p(200, 100, 1), _p(300, 200, 2)])
        assert {pid for pid, _ in runs.recorded} == {100, 200, 300}

    def test_reused_pid_parent_is_not_a_run_process(self) -> None:
        runs = RunSet(root_pid=100, harness_pid=1)
        runs.observe([_p(100, 1, 0), _p(200, 100, 1)])
        # Pid 100 now belongs to a foreign process with a different start time.
        foreign = _p(100, 7, 50)
        orphan = _p(300, 100, 51)
        assert runs.observe([foreign, orphan]) == []
        assert 300 not in {pid for pid, _ in runs.recorded}
        assert runs.alive([foreign, orphan]) == []

    def test_child_started_before_parent_is_not_recorded(self) -> None:
        runs = RunSet(root_pid=100, harness_pid=1)
        runs.observe([_p(100, 1, 10), _p(200, 100, 5)])
        assert 200 not in {pid for pid, _ in runs.recorded}

    def test_unrelated_process_is_not_recorded(self) -> None:
        runs = RunSet(root_pid=100, harness_pid=1)
        runs.observe([_p(100, 1, 0), _p(900, 1, 1)])
        assert 900 not in {pid for pid, _ in runs.recorded}

    def test_parse_ps_reads_lstart(self) -> None:
        text = "  12   1 Ss   Thu Nov  5 12:00:00 2026\n  13  12 Z    Thu Nov  5 12:00:01 2026\n"
        rows = parse_ps(text)
        assert rows[0] == _p(12, 1, 0)
        assert rows[1].zombie and rows[1].ppid == 12


class TestLaunch:
    """AC-0001, AC-0002, AC-0016, AC-0007: the launch against a stub `pi`."""

    def test_argv_env_cwd_and_command(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pi, out = _make_stub(tmp_path, "echo")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "planted-secret")
        monkeypatch.setenv("PI_CODING_AGENT_DIR", "/planted")
        monkeypatch.setenv("LC_TIME", "C")
        monkeypatch.setenv("LANG", "en_US.UTF-8")
        outcome = run_harness(pi, _run_root(tmp_path), 60, term_grace_s=3)
        assert outcome.failure is None and outcome.survivors == []
        record = json.loads((out / "rpc.json").read_text())
        assert record["argv"] == list(PI_FLAGS)
        expected = {"PATH", "HOME", "TMPDIR", "LANG", "WORK_SUPERVISOR_INTEGRATION"}
        expected |= {k for k in os.environ if k.startswith("LC_")}
        assert set(record["env"]) - _SHELL_NOISE == expected
        assert record["env"]["WORK_SUPERVISOR_INTEGRATION"] == "1"
        assert "planted-secret" not in json.dumps(record["env"])
        assert record["cwd_entries"] == [] and record["home_entries"] == []
        assert Path(record["cwd"]).resolve() == (tmp_path / "run" / "cwd").resolve()
        assert Path(record["home"]) == tmp_path / "run" / "home"
        rpc = json.loads((out / "rpc.line").read_text())
        assert set(rpc) == {"id", "type", "command"}
        assert rpc["id"] == RPC_ID and rpc["type"] == "bash"
        results = tmp_path / "run" / "results"
        suite = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop"
        assert rpc["command"] == build_command(sys.executable, suite, SUITE_FILES, results)
        assert (out / "stub.pid").read_text() == str(outcome.pi_pid)

    def test_command_shape(self, tmp_path: Path) -> None:
        results = tmp_path / "res dir"
        command = build_command("/py thon", tmp_path / "suite", SUITE_FILES, results)
        names = " ".join(SUITE_FILES)
        run = (
            f"'/py thon' -m pytest -p no:cacheprovider -q '--junitxml={results}/junit.xml' {names}"
        )
        assert command.endswith(run)
        assert (
            command.index("ppid") < command.index("--collect-only") < command.index("--junitxml")
        )

    def test_command_writes_ppid_and_count_before_pytest(self, tmp_path: Path) -> None:
        suite, results = tmp_path / "suite", tmp_path / "results"
        suite.mkdir()
        results.mkdir()
        log = tmp_path / "calls.log"
        fake = tmp_path / "fakepy"
        fake.write_text(
            "#!/bin/sh\n"
            f'echo "ppid_file=$(test -f {shlex.quote(str(results / "ppid"))} && echo yes || echo no)'
            f" collected_file=$(test -s {shlex.quote(str(results / 'collected'))}"
            f' && echo yes || echo no) args=$*" >> {shlex.quote(str(log))}\n'
            'case "$*" in *--collect-only*) echo "3 tests collected in 0.01s";; esac\n',
            encoding="utf-8",
        )
        fake.chmod(0o755)
        command = build_command(str(fake), suite, ("a.py", "b.py"), results)
        done = subprocess.run(["/bin/sh", "-c", command], check=False)
        assert done.returncode == 0
        first, second = log.read_text().splitlines()
        assert "ppid_file=yes" in first and "--collect-only -q a.py b.py" in first
        assert "ppid_file=yes collected_file=yes" in second
        assert second.endswith(
            f"args=-m pytest -p no:cacheprovider -q --junitxml={results}/junit.xml a.py b.py"
        )
        assert (results / "ppid").read_text().strip() == str(os.getpid())
        assert parse_collected((results / "collected").read_text()) == 3

    def test_version_call_gets_child_env_and_fresh_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pi, out = _make_stub(tmp_path, "echo")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "planted-secret")
        monkeypatch.setenv("PI_PACKAGE_DIR", "/planted")
        root = _run_root(tmp_path)
        assert version_of(pi, root) == "stub-pi 9.9.9"
        record = json.loads((out / "version.json").read_text())
        assert record["argv"] == ["--version"]
        expected = {"PATH", "HOME", "TMPDIR", "LANG", "WORK_SUPERVISOR_INTEGRATION"}
        expected |= {k for k in os.environ if k.startswith("LC_")}
        assert set(record["env"]) - _SHELL_NOISE == expected
        assert Path(record["home"]) == root / "version-home"
        assert record["home_entries"] == []

    def test_non_json_line_fails_quoting_it(self, tmp_path: Path) -> None:
        pi, _ = _make_stub(tmp_path, "garbage")
        outcome = run_harness(pi, _run_root(tmp_path), 60, term_grace_s=2)
        assert outcome.failure is not None and "not json at all" in outcome.failure
        assert outcome.survivors == []

    def test_early_eof_fails(self, tmp_path: Path) -> None:
        pi, _ = _make_stub(tmp_path, "eof")
        outcome = run_harness(pi, _run_root(tmp_path), 60, term_grace_s=2)
        assert outcome.failure is not None and "closed stdout" in outcome.failure


class TestCleanup:
    """AC-0005, AC-0006: deadline and cleanup of run processes in their own sessions."""

    def test_deadline_kills_stub_child_and_grandchild(self, tmp_path: Path) -> None:
        pi, out = _make_stub(tmp_path, "chain")
        # The child outlives the 5-second sampling gap the spec tolerates, so the
        # grandchild is recorded before its parent exits.
        outcome = run_harness(
            pi,
            _run_root(tmp_path),
            8,
            interval_s=0.25,
            term_grace_s=2,
            before_send=_wait_ready(out),
        )
        assert outcome.failure is not None and "deadline" in outcome.failure
        assert evaluate(outcome)  # the run is a failure on the deadline
        assert outcome.survivors == []
        assert outcome.recorded >= 3
        for name in ("stub.pid", "child.pid", "grandchild.pid"):
            assert _wait_gone(_pid_from(out, name)), f"{name} still running"

    def test_process_started_on_sigterm_is_also_ended(self, tmp_path: Path) -> None:
        pi, out = _make_stub(tmp_path, "term_spawn")
        outcome = run_harness(
            pi,
            _run_root(tmp_path),
            2,
            interval_s=0.25,
            term_grace_s=4,
            before_send=_wait_ready(out),
        )
        assert outcome.failure is not None and "deadline" in outcome.failure
        assert outcome.survivors == []
        for name in ("stub.pid", "spawned.pid"):
            assert _wait_gone(_pid_from(out, name)), f"{name} still running"

    def test_missing_record_file_fails_readably(self, tmp_path: Path) -> None:
        with pytest.raises(AssertionError, match="never recorded nothing.pid"):
            _pid_from(tmp_path, "nothing.pid")

    @pytest.mark.parametrize(
        "ps_body",
        ["#!/bin/sh\nexit 1\n", "#!/bin/sh\necho 'garbage that is no table'\n", "#!/bin/sh\n"],
        ids=["exits-non-zero", "prints-garbage", "prints-nothing"],
    )
    def test_unreadable_process_table_fails_and_still_ends_pi(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ps_body: str
    ) -> None:
        pi, out = _make_stub(tmp_path, "garbage")  # Pi stays alive after the bad line
        fake_ps = tmp_path / "fake-ps"
        fake_ps.write_text(ps_body, encoding="utf-8")
        fake_ps.chmod(0o755)
        monkeypatch.setattr(sys.modules[__name__], "_ps_binary", lambda: str(fake_ps))
        started = time.monotonic()
        outcome = run_harness(
            pi,
            _run_root(tmp_path),
            120,
            interval_s=0.25,
            term_grace_s=2,
            before_send=_wait_ready(out),
        )
        assert time.monotonic() - started < 100, "run_harness blocked on Pi"
        assert outcome.failure is not None
        assert "process table unreadable" in outcome.failure
        assert any("process table unreadable" in p for p in evaluate(outcome))
        assert _wait_gone(_pid_from(out, "stub.pid")), "Pi still running after cleanup"

    def test_unreadable_read_before_cleanup_fails_the_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ps failure confined to the run phase still fails the run (qe2-1)."""
        pi, out = _make_stub(tmp_path, "echo")
        flag = tmp_path / "ps-fails"
        flag.write_text("", encoding="utf-8")
        fake_ps = tmp_path / "fake-ps"
        fake_ps.write_text(
            f'#!/bin/sh\n[ -e "{flag}" ] && exit 1\nexec {shutil.which("ps")} "$@"\n',
            encoding="utf-8",
        )
        fake_ps.chmod(0o755)
        monkeypatch.setattr(sys.modules[__name__], "_ps_binary", lambda: str(fake_ps))

        def heal_then_ready() -> None:
            _wait_ready(out)()
            flag.unlink()  # ps reads cleanly from here, through cleanup

        outcome = run_harness(
            pi,
            _run_root(tmp_path),
            120,
            interval_s=0.25,
            term_grace_s=2,
            before_send=heal_then_ready,
        )
        assert outcome.failure is not None
        assert "process table unreadable: ps exited 1" in outcome.failure
        assert any("process table unreadable" in p for p in evaluate(outcome))

    def test_sample_gap_over_bound_fails_the_run(self) -> None:
        """A watcher sample later than the bound is recorded as a failure."""
        watcher = ProcessWatcher(os.getpid(), dict(os.environ))
        watcher.snapshot()
        watcher._last_sample = time.monotonic() - (MAX_SAMPLE_GAP_S + 1)
        watcher.snapshot()
        assert watcher.unreadable is not None and watcher.unreadable.startswith("no sample for")


class TestShellEnvironment:
    """AC-0001 (sec-2): the variables Pi's shell sees are the child environment, plus known additions."""

    def test_green_clean_run_through_a_shell(self, tmp_path: Path) -> None:
        pi, out = _make_stub(tmp_path, "shell")
        outcome = run_harness(
            pi, _run_root(tmp_path), 120, term_grace_s=3, before_send=_wait_ready(out)
        )
        assert evaluate(outcome) == []

    def test_green_with_pi_added_names_and_path_prefix(self, tmp_path: Path) -> None:
        pi, out = _make_stub(tmp_path, "shell:pibin")
        outcome = run_harness(
            pi, _run_root(tmp_path), 120, term_grace_s=3, before_send=_wait_ready(out)
        )
        assert evaluate(outcome) == []

    def test_extra_variable_name_reds(self, tmp_path: Path) -> None:
        pi, out = _make_stub(tmp_path, "shell:extra")
        outcome = run_harness(
            pi, _run_root(tmp_path), 120, term_grace_s=3, before_send=_wait_ready(out)
        )
        problems = evaluate(outcome)
        assert len(problems) == 1 and "PLANTED_NAME" in problems[0]

    def test_rewritten_path_reds(self, tmp_path: Path) -> None:
        pi, out = _make_stub(tmp_path, "shell:path")
        outcome = run_harness(
            pi, _run_root(tmp_path), 120, term_grace_s=3, before_send=_wait_ready(out)
        )
        problems = evaluate(outcome)
        assert len(problems) == 1 and "PATH" in problems[0] and "/planted/bin" in problems[0]

    def test_check_names_and_path(self, tmp_path: Path) -> None:
        env = {"PATH": "/a:/b", "HOME": str(tmp_path)}
        assert check_shell_env("PATH\nHOME\nPWD\nSHLVL\n_\n", "/a:/b", env, tmp_path) == []
        assert check_shell_env("PATH\nTOKEN\n", "/a:/b", env, tmp_path)
        assert check_shell_env("PATH\n", "/a", env, tmp_path)
        behind = f"{tmp_path}/.pi/agent/bin:/a:/b"
        assert check_shell_env("PATH\n", behind, env, tmp_path) == []
        assert check_shell_env("PATH\n", f"/x:{behind}", env, tmp_path)


class TestEvaluateResponse:
    """AC-0003: a failing response reds even with an otherwise clean result directory."""

    def _outcome(self, tmp_path: Path, response: dict[str, Any]) -> RunOutcome:
        results = tmp_path / "results"
        results.mkdir()
        home = tmp_path / "home"
        env = {"PATH": "/a", "HOME": str(home)}
        (results / "junit.xml").write_text(_junit(SUITE_FILES), encoding="utf-8")
        (results / "collected").write_text(f"{len(SUITE_FILES)} tests collected in 1s\n")
        (results / "ppid").write_text("4242\n")
        (results / "env-names").write_text("PATH\nHOME\n")
        (results / "path").write_text("/a")
        return RunOutcome(4242, results, response, None, [], 1, env, home)

    def test_clean_response_is_green(self, tmp_path: Path) -> None:
        ok = {"success": True, "data": {"exitCode": 0, "output": ""}}
        assert evaluate(self._outcome(tmp_path, ok)) == []

    def test_success_false_reds(self, tmp_path: Path) -> None:
        bad = {"success": False, "data": {"exitCode": 0, "output": "boom"}}
        problems = evaluate(self._outcome(tmp_path, bad))
        assert len(problems) == 1 and "success=False" in problems[0] and "boom" in problems[0]

    def test_non_zero_exit_code_reds(self, tmp_path: Path) -> None:
        bad = {"success": True, "data": {"exitCode": 3, "output": "tail"}}
        problems = evaluate(self._outcome(tmp_path, bad))
        assert len(problems) == 1 and "exitCode=3" in problems[0]


class TestOptInSkips:
    """AC-0008, AC-0009: the real run skips with a reason and starts nothing."""

    def _skip(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, var: bool, on_path: bool):
        _, out = _make_stub(tmp_path, "echo")
        base = os.environ.get("PATH", os.defpath)
        monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}{os.pathsep}{base}" if on_path else base)
        if var:
            monkeypatch.setenv(OPT_IN_VAR, "1")
        else:
            monkeypatch.delenv(OPT_IN_VAR, raising=False)
        with pytest.raises(pytest.skip.Exception) as info:
            test_pi_hosted_conformance(tmp_path / "unused")
        assert not (out / "ran").exists()
        return str(info.value)

    def test_variable_unset_with_pi_on_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert OPT_IN_VAR in self._skip(tmp_path, monkeypatch, var=False, on_path=True)

    def test_variable_unset_without_pi(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        if shutil.which("pi"):
            monkeypatch.setenv("PATH", "/nonexistent")
        assert OPT_IN_VAR in self._skip(tmp_path, monkeypatch, var=False, on_path=False)

    def test_variable_set_without_pi(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _make_stub(tmp_path, "echo")
        monkeypatch.setenv(OPT_IN_VAR, "1")
        monkeypatch.setenv("PATH", "/nonexistent")
        with pytest.raises(pytest.skip.Exception) as info:
            test_pi_hosted_conformance(tmp_path / "unused")
        assert "pi" in str(info.value) and OPT_IN_VAR not in str(info.value)
        assert not (tmp_path / "bin" / "out" / "ran").exists()
