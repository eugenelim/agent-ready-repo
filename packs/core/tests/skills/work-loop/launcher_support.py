"""Shared setup for the concurrent-path suites: a repository, a policy, and a fixture launcher.

The fixture launcher (``fixture_launcher.py``) is a test fixture that simulates a host able
to attest containment; a test scripts it per case with ``make_launcher``.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_FIXTURE = _HERE / "fixture_launcher.py"


# Each shared helper by literal path, so every file a suite loads stays visibly inside this pack.
_HELPER_PATHS = {"supervisor_harness": _HERE / "supervisor_harness.py"}


def _helper(name: str) -> ModuleType:
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


harness = _helper("supervisor_harness")
sup = harness.sup
cli = harness.cli
admission = harness.admission
launcher_module = cli._supervisor("_supervisor_launcher.py")
concurrent_module = cli._supervisor("_supervisor_concurrent.py")
SPEC_DIR = harness.SPEC_DIR

READS = ["README.md"]
HONEST_WRITE = {"calc.py": "def answer():\n    return 42\n"}


def make_launcher(directory: Path, script: dict[str, Any]) -> tuple[Path, str]:
    """A copy of the fixture launcher scripted with *script*, and its sha256."""
    source = _FIXTURE.read_text(encoding="utf-8")
    assert "SCRIPT = None  # SCRIPT-SLOT" in source
    slot = "SCRIPT = json.loads(" + repr(json.dumps(script)) + ")"
    body = source.replace("SCRIPT = None  # SCRIPT-SLOT", slot)
    body = body.replace("#!/usr/bin/env python3", f"#!{sys.executable}", 1)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "launcher"
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def tasks(*specs: tuple[str, str, str, str]) -> str:
    """A plan of goal-based tasks: each spec is ``(number, title, reads, writes)``."""
    return sup.plan(
        *[
            sup.task(
                number, title, mode="goal-based", tests="no stub (goal-based)",
                touches=writes, reads=reads, writes=writes,
            )
            for number, title, reads, writes in specs
        ]
    )


ONE_TASK = tasks(("T1", "Calculator answers", "`README.md`", "`calc.py`"))
# Two tasks whose declared writes meet (both write calc.py): never in one request.
TWO_TASKS = tasks(
    ("T1", "Calculator answers", "`README.md`", "`calc.py`"),
    ("T2", "Plain note is written", "`README.md`", "`plain.txt`, `calc.py`"),
)
# Two tasks whose declared sets do not meet: one request names both.
DISJOINT_TASKS = tasks(
    ("T1", "Calculator answers", "`README.md`", "`calc.py`"),
    ("T2", "Plain note is written", "`README.md`", "`plain.txt`"),
)


def write_policy(directory: Path, **changes: object) -> Path:
    policy = json.loads(admission._POLICY_PATH.read_text("utf-8"))
    policy.update(changes)
    path = directory / "supervisor-policy.json"
    path.write_text(json.dumps(policy), "utf-8")
    return path


class Env:
    """One repository under a concurrent policy with a scripted fixture launcher."""

    def __init__(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        script: dict[str, Any] | None = None,
        mode: str = "enforced-allowlist",
        plan: str = ONE_TASK,
        name: bool = True,
        policy: dict[str, Any] | None = None,
        allow_fixture: bool = True,
    ) -> None:
        self.tmp_path = tmp_path
        self.monkeypatch = monkeypatch
        self.log = tmp_path / "log"
        self.log.mkdir()
        self.script = {
            "log": str(self.log), "reads": READS, "write": HONEST_WRITE, **(script or {})
        }
        self.launcher, self.sha = make_launcher(tmp_path / "launcher-dir", self.script)
        self.repo = harness.make_repo(tmp_path, plan=plan)
        self.mode = mode
        monkeypatch.setattr(
            admission, "_POLICY_PATH", write_policy(tmp_path, concurrency=mode, **(policy or {}))
        )
        monkeypatch.setattr(launcher_module, "ALLOW_FIXTURE_LAUNCHER", allow_fixture)
        self.named = name

    def run(self, *argv: str) -> tuple[int, dict[str, Any]]:
        return harness.run_cli(self.repo, *argv)

    def start(self, *extra: str) -> tuple[int, dict[str, Any]]:
        args = [
            "start", SPEC_DIR, "--intent", "code", "--code-trust", "trusted",
            "--authority-ref", "owner:0123456789ab",
            "--review-authority-ref", "plan-reviewer:0123456789ab",
            *harness.digest_args(self.repo),
        ]
        if self.named:
            args += ["--launcher-sha256", self.sha, "--launcher", str(self.launcher)]
        return self.run(*args, *extra)

    def next(self) -> dict[str, Any]:
        return self.run("next", SPEC_DIR)[1]

    def verb(self, request_id: str) -> tuple[int, dict[str, Any]]:
        return self.run("run-concurrent", SPEC_DIR, "--request", request_id)

    def report(self, request: dict[str, Any], **facts: Any) -> tuple[int, dict[str, Any]]:
        result = {
            "schema_version": 1, "request_id": request["request_id"],
            "run_id": request["run_id"], "kind": request["kind"], **facts,
        }
        path = self.tmp_path / "result.json"
        path.write_text(json.dumps(result), "utf-8")
        return self.run("report", SPEC_DIR, str(path))

    def issued(self) -> dict[str, Any]:
        """Start the run and answer ``next``'s request."""
        code, started = self.start()
        assert code == 0, started
        payload = self.next()
        assert "request" in payload, payload
        return payload["request"]  # type: ignore[no-any-return]

    def store(self) -> Path:
        base = self.repo / ".git" / "agentbundle-supervisor"
        (run,) = [p for p in base.iterdir() if p.name.startswith("run-")]
        return run

    def records(self) -> list[dict[str, Any]]:
        directory = self.store() / "consumed"
        return [json.loads(p.read_text("utf-8")) for p in sorted(directory.glob("*.json"))]

    def git(self, *args: str) -> str:
        return harness.git(self.repo, *args)

    def received(self) -> list[dict[str, Any]]:
        path = self.log / "recv.log"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]

    def output_channels(self) -> dict[str, bytes]:
        """Every file the supervisor and the launcher left behind, by name, for leak searches."""
        found: dict[str, bytes] = {}
        roots = [self.repo / ".git" / "agentbundle-supervisor"]
        roots += [self.repo / SPEC_DIR / ".supervisor", self.log, self.repo / ".loop-run"]
        for root in roots:
            if root.is_dir():
                for path in sorted(root.rglob("*")):
                    if path.is_file() and not path.is_symlink():
                        found[str(path)] = path.read_bytes()
        return found


def group_dead(pgid: int) -> bool:
    return not launcher_module.group_alive(pgid)


def kill_group(pgid: int) -> None:
    """Test cleanup: end a process group the test left running."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pgid, 9)


def git_clean(repo: Path) -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    return not out.strip()


def is_executable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IXUSR)


class StepClock:
    """A clock that jumps *step* seconds on every reading and really sleeps when asked to."""

    def __init__(self, step: float) -> None:
        self.step = step
        self.t = 0.0

    def now(self) -> float:
        self.t += self.step
        return self.t

    def sleep(self, seconds: float) -> None:
        import time

        time.sleep(seconds)


def journal(repo: Path) -> list[dict[str, Any]]:
    path = repo / SPEC_DIR / ".supervisor" / "journal.jsonl"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]


def security_events(repo: Path) -> list[dict[str, Any]]:
    path = repo / SPEC_DIR / ".supervisor" / "security-events.jsonl"
    if not path.exists():
        return []
    found = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    return [e for e in found if e.get("outcome") == "denied"]


def crash_at(point: str, *, before: Any = None) -> None:
    """Make the supervisor die (by raising ``Crash``) when it reaches kill point *point*."""

    def hook(name: str) -> None:
        if name == point:
            if before is not None:
                before()
            raise harness.Crash(name)

    harness.commit_module.set_kill_hook(hook)


def clear_kill_hook() -> None:
    harness.commit_module.set_kill_hook(None)
