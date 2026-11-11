"""Dispatch is self-contained: `work-loop` alone gives the same output as the full tree.

Spec: docs/specs/repair-only-workspace-status/spec.md (AC-0001).
Verification mode: TDD. A copy of only the `work-loop` skill directory sits in a
temporary `skills/` tree with no other skill. For each repository below, planted with
the builders `test_dispatch.py` uses, the output of that copy equals the output of the
real `core` skill tree.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

_HERE = Path(__file__).resolve().parent
_SKILLS = _HERE.parents[2] / ".apm" / "skills"
_COUNTER = itertools.count()


def _load_by_path(path: Path, stem: str) -> ModuleType:
    """Load a module by file path under a unique name that names its pack and skill."""
    name = f"core_work_loop_isolation_{stem}_{next(_COUNTER)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


TD = _load_by_path(_HERE / "test_dispatch.py", "dispatch_helpers")
Repo, entry, SPEC = TD.Repo, TD.entry, TD.SPEC


def _mixed(repo: Any) -> None:
    repo.spec("alpha")
    repo.spec("beta", "Implementing")
    repo.spec("gamma", "Shipped")
    repo.spec("noplan", plan=None)
    repo.spec("waits", depends="spec:alpha")
    repo.spec("waits-on-shipped", depends="spec:gamma")
    repo.put("docs/specs/loose/readme.txt", "x")


def _cooled(repo: Any) -> None:
    repo.spec("cooled", "Shipped")
    repo.spec("live")
    repo.cool(SPEC.format("cooled"))
    repo.put("docs/lifecycle/broken.json", "{not json")


def _cooled_child(repo: Any) -> None:
    repo.put("docs/product/briefs/parent.md", "# Brief: parent\n\n- **Status:** Executing\n")
    repo.put("docs/specs/kid/spec.md", "# Spec: kid\n\n- **Status:** Shipped\n")
    repo.cool(SPEC.format("kid"))


def _captured(repo: Any) -> None:
    repo.spec("waiter", depends="docs/product/captured/settled.md")
    repo.put(
        "docs/product/captured/settled.md",
        "# Defect\n\n- **Status:** Closed\n- **Kind:** defect\n- **Resolution:** fixed\n",
    )


def _unmigrated(repo: Any) -> None:
    repo.spec("alpha")
    repo.workspace(queue=[entry(SPEC.format("alpha"))])


def _invalid_workspace(repo: Any) -> None:
    repo.spec("alpha")
    repo.put("workspace.toml", "not = [valid")


def _authorization_only(repo: Any) -> None:
    repo.spec("alpha")
    repo.put("workspace.toml", '[authorization.migration]\napprover_roles = ["owner"]\n')


def _empty(repo: Any) -> None:
    repo.root.mkdir(parents=True, exist_ok=True)


_REPOSITORIES: dict[str, Callable[[Any], None]] = {
    "mixed": _mixed,
    "cooled": _cooled,
    "cooled-child": _cooled_child,
    "captured-dependency": _captured,
    "unmigrated": _unmigrated,
    "invalid-workspace": _invalid_workspace,
    "authorization-only": _authorization_only,
    "empty": _empty,
}


@pytest.fixture(scope="module")
def full_tree() -> ModuleType:
    """Dispatch as it runs from the real `core` skills tree, beside every other skill."""
    return _load_by_path(_SKILLS / "work-loop" / "scripts" / "dispatch.py", "full")


@pytest.fixture(scope="module")
def alone(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A `skills/` tree holding a copy of the `work-loop` directory and nothing else."""
    skills = tmp_path_factory.mktemp("isolated") / "skills"
    shutil.copytree(
        _SKILLS / "work-loop", skills / "work-loop",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    assert [child.name for child in skills.iterdir()] == ["work-loop"]
    return skills / "work-loop" / "scripts" / "dispatch.py"


@pytest.mark.parametrize("name", sorted(_REPOSITORIES))
def test_work_loop_alone_prints_the_full_tree_output(
    full_tree: ModuleType, alone: Path, tmp_path: Path, name: str
) -> None:
    repo = Repo(tmp_path / "r")
    _REPOSITORIES[name](repo)
    isolated = _load_by_path(alone, "alone")
    for mode, selector in ((None, None), ("start", "alpha"), ("resume", "beta"), ("start", "kid")):
        assert isolated.dispatch(repo.root, mode, selector) == full_tree.dispatch(
            repo.root, mode, selector
        ), (name, mode, selector)


def test_work_loop_alone_runs_as_a_command(
    full_tree: ModuleType, alone: Path, tmp_path: Path
) -> None:
    repo = Repo(tmp_path / "r")
    _mixed(repo)
    done = subprocess.run(
        [sys.executable, "-I", str(alone), "--root", str(repo.root)],
        capture_output=True, check=False,
    )
    assert done.returncode == 0 and done.stderr == b""
    assert json.loads(done.stdout.decode("utf-8")) == full_tree.dispatch(repo.root)
