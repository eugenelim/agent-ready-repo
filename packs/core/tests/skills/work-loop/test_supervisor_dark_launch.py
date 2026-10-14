"""The core stays dark (T8).

VI-4060 (AC-0027) and VI-4061 (AC-0028). AC-0029 (VI-4062) is a one-time check
against the merge-base and is recorded in the spec's verification ledger, not
kept as a standing test that later legitimate changes would break.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")

SKILL = sup.SCRIPTS.parent

# Runs one verb with the standard library and the skill's scripts directory as
# the only importable code (-I -S), then fails if any other module was loaded.
_ISOLATED = """
import runpy, sys, sysconfig
script, stdlib, scripts = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [script, *sys.argv[4:]]
code = 0
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else 1
foreign = sorted({
    getattr(m, "__file__", None) for m in list(sys.modules.values())
    if getattr(m, "__file__", None)
    and not m.__file__.startswith((stdlib, scripts))
})
if foreign:
    sys.stderr.write("foreign modules: " + ", ".join(foreign))
    code = 97
sys.exit(code)
"""


def _isolated_cli(repo: Path, *argv: str) -> tuple[int, dict[str, Any]]:
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "GIT_"))}
    env.update(h.GIT_ENV)
    done = subprocess.run(
        [sys.executable, "-I", "-S", "-c", _ISOLATED, str(sup.SCRIPTS / "work-supervisor.py"),
         sysconfig.get_paths()["stdlib"], str(sup.SCRIPTS), *argv],
        cwd=repo, env=env, capture_output=True, text=True, timeout=600, check=False,
    )
    assert done.returncode != 97, done.stderr
    return done.returncode, (json.loads(done.stdout) if done.stdout.strip() else {})


@sup.INTEGRATION
def test_uninterrupted_run_completes_on_the_standard_library_alone(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    monkeypatch.setattr(h, "run_cli", _isolated_cli)
    code, started = h.start(repo)
    assert code == 0, started
    end = h.Controller(repo, tmp_path / "effects.log").drive()
    assert end.get("terminal"), end
    assert (tmp_path / "effects.log").read_text("utf-8").split() == [f"{started['run_id']}:push"]


def test_nothing_in_the_skill_but_the_supervisor_invokes_it() -> None:
    own = {"work-supervisor.py", "supervisor-policy.json"} | {
        p.name for p in sup.SCRIPTS.glob("_supervisor_*.py")}
    offenders = []
    for path in sorted(SKILL.rglob("*")):
        if not path.is_file() or path.name in own or "__pycache__" in path.parts:
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        if "work-supervisor" in text or "_supervisor_" in text:
            offenders.append(str(path.relative_to(SKILL)))
    assert offenders == []
