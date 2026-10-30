"""A synthetic full code run reaches readiness through the installed skill alone.

The installed work-loop skill (the `.claude/skills/work-loop` projection) is copied
into an empty directory, so project-knowledge and every other skill are absent.
Each supervisor verb then runs under `python -I -S`, with `sys.path` limited to the
standard library and that copy's `scripts/` directory, and an import hook that
fails the run on any module found outside those two places. The controller loop,
the synthetic worker, reviewer, and effect source are the supervisor test
harness's, so the run takes the same path a real controller takes.

Roster-owned: it reads the repository's installed-skill projection and the pack's
shared harness, which no single pack suite may reach across. The Windows CI job
runs this module too.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLED_SKILL = REPO_ROOT / ".claude" / "skills" / "work-loop"
HARNESS = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop" / "supervisor_harness.py"

# The fence's rule, kept as source so the run and the controls share one copy. A path
# is allowed when it sits, by whole path components, inside the skill's scripts
# directory, the platform's extension-module directory, or the standard library
# directory outside any site-packages.
_FENCE_RULE_PATH = Path(__file__).resolve().with_name("supervisor_fence_rule.py")
_FENCE_RULE = _FENCE_RULE_PATH.read_text(encoding="utf-8")

# Runs one verb with an import fence. The fence resolves each import with the normal
# path finder and refuses any file module the rule does not allow, so a stray import
# fails where it happens.
_RUNNER = _FENCE_RULE + """
import importlib.machinery, runpy, sys
script, stdlib, extension_dir, scripts = sys.argv[1:5]
allowed = make_allowed(stdlib, extension_dir, scripts)


class Fence:
    def find_spec(self, name, path=None, target=None):
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        origin = getattr(spec, "origin", None)
        if origin in (None, "built-in", "frozen", "namespace"):
            return None
        if not allowed(origin):
            raise ImportError("import outside the standard library and scripts/: " + origin)
        return None


sys.meta_path.insert(0, Fence())
sys.path[:] = [p for p in sys.path if allowed(p)] + [scripts]
sys.argv = [script, *sys.argv[5:]]
code = 0
try:
    runpy.run_path(script, run_name="__main__")
except SystemExit as exc:
    code = exc.code if isinstance(exc.code, int) else 1
sys.exit(code)
"""


def _extension_dir() -> str:
    """The platform's standard extension-module directory."""
    if sys.platform == "win32":
        return str(Path(sys.base_prefix) / "DLLs")
    return str(Path(sysconfig.get_path("platstdlib")) / "lib-dynload")


def _fence_args() -> list[str]:
    return [sysconfig.get_path("stdlib"), _extension_dir()]


def _load_harness():
    name = "supervisor_harness_for_installed_run"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def h():
    return _load_harness()


def _install_copy(tmp_path: Path) -> Path:
    """Copy the installed skill into an empty directory; nothing else comes with it."""
    target = tmp_path / "installed" / "skills" / "work-loop"
    shutil.copytree(INSTALLED_SKILL, target, ignore=shutil.ignore_patterns("__pycache__"))
    assert sorted(p.name for p in target.parent.iterdir()) == ["work-loop"]
    return target / "scripts"


def _isolated_cli(h, scripts: Path):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "GIT_"))}
    env.update(h.GIT_ENV)

    def run(repo: Path, *argv: str) -> tuple[int, dict[str, Any]]:
        done = subprocess.run(
            [sys.executable, "-I", "-S", "-c", _RUNNER, str(scripts / "work-supervisor.py"),
             *_fence_args(), str(scripts), *argv],
            cwd=repo, env=env, capture_output=True, text=True, timeout=600, check=False,
        )
        assert "outside the standard library" not in done.stderr, done.stderr
        return done.returncode, (json.loads(done.stdout) if done.stdout.strip() else {})

    return run


def test_the_installed_skill_is_present_in_the_projection() -> None:
    assert (INSTALLED_SKILL / "scripts" / "work-supervisor.py").is_file()


def test_the_import_fence_fails_on_a_module_outside_the_allowed_places(tmp_path: Path) -> None:
    """The fence can fail: a module planted beside nothing allowed is refused."""
    planted = tmp_path / "planted"
    planted.mkdir()
    (planted / "foreign_module.py").write_text("VALUE = 1\n", encoding="utf-8")
    probe = (
        "import sys; sys.path.append(sys.argv[-1]); import foreign_module"
    )
    script = tmp_path / "probe.py"
    script.write_text(probe, encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    done = subprocess.run(
        [sys.executable, "-I", "-S", "-c", _RUNNER, str(script), *_fence_args(),
         str(scripts), "--", str(planted)],
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert done.returncode != 0
    assert "outside the standard library" in done.stderr


def test_extension_modules_import_under_the_fence(tmp_path: Path) -> None:
    """The platform's extension directory is admitted: unicodedata and _ctypes load."""
    script = tmp_path / "probe.py"
    script.write_text("import unicodedata, _ctypes\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    done = subprocess.run(
        [sys.executable, "-I", "-S", "-c", _RUNNER, str(script), *_fence_args(), str(scripts)],
        capture_output=True, text=True, timeout=120, check=False,
    )
    assert done.returncode == 0, done.stderr


def _rule(tmp_path: Path):
    spec = importlib.util.spec_from_file_location("roster_supervisor_fence_rule", _FENCE_RULE_PATH)
    assert spec is not None and spec.loader is not None
    rule = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rule)
    stdlib = tmp_path / "lib" / "python3.99"
    extension = stdlib / "lib-dynload"
    scripts = tmp_path / "skill" / "scripts"
    for directory in (stdlib / "site-packages", extension, scripts, tmp_path / "lib" / "python3.99-sibling"):
        directory.mkdir(parents=True)
    return rule.make_allowed(str(stdlib), str(extension), str(scripts)), stdlib, extension, scripts


def test_the_rule_admits_the_stdlib_the_extension_directory_and_scripts(tmp_path: Path) -> None:
    allowed, stdlib, extension, scripts = _rule(tmp_path)
    assert allowed(str(stdlib / "json" / "__init__.py"))
    assert allowed(str(extension / "unicodedata.so"))
    assert allowed(str(scripts / "work-supervisor.py"))


def test_the_rule_refuses_a_sibling_of_the_stdlib_directory(tmp_path: Path) -> None:
    """A string-prefix check would admit python3.99-sibling beside python3.99."""
    allowed, _stdlib, _extension, _scripts = _rule(tmp_path)
    planted = tmp_path / "lib" / "python3.99-sibling" / "planted.py"
    planted.write_text("VALUE = 1\n", encoding="utf-8")
    assert not allowed(str(planted))


def test_the_rule_refuses_site_packages_under_the_stdlib(tmp_path: Path) -> None:
    allowed, stdlib, _extension, _scripts = _rule(tmp_path)
    planted = stdlib / "site-packages" / "planted.py"
    planted.write_text("VALUE = 1\n", encoding="utf-8")
    assert not allowed(str(planted))


def test_a_full_code_run_reaches_readiness_from_the_installed_skill_alone(
    h, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """VI-7901: start, then next and report to terminal, with only the standard library."""
    scripts = _install_copy(tmp_path)
    repo = h.make_repo(tmp_path)
    monkeypatch.setattr(h, "run_cli", _isolated_cli(h, scripts))

    code, started = h.start(repo)
    assert code == 0, started
    assert started["status"] == "admitted", started
    end = h.Controller(repo, tmp_path / "effects.log").drive()

    assert end.get("terminal"), end
    assert (tmp_path / "effects.log").read_text("utf-8").split() == [f"{started['run_id']}:push"]
    assert (repo / h.SPEC_DIR / "delivery" / "approvals.jsonl").is_file()
    code, status = h.run_cli(repo, "status", h.SPEC_DIR, "--json", "--check")
    assert code == 0 and status["terminal"] is True, status
