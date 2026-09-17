"""Each `packages/*` suite must import its own package from this worktree.

**The defect.** Pytest reads exactly one configfile: it walks up from the
invocation's arguments, takes the nearest one carrying a pytest section, and
stops. The root `pyproject.toml` declares `pythonpath` for all three
distributions, but each carries its own `[tool.pytest.ini_options]`, so
`pytest packages/<pkg>/` never sees that list and nothing merges the two.

The omission has two outcomes and which one you get depends on what happens to
be installed. With a copy in `site-packages` the suite passes while testing the
RELEASED package: it would still catch a regression already published, and miss
one introduced by the diff under review. With nothing installed, collection
fails outright. The quiet outcome is the dangerous one, and a gate whose result
turns on the contents of `site-packages` is the defect either way.

**Why this asks pytest instead of reading the config.** An earlier version of
this file parsed the pyproject and modelled what pytest would do with it, and
that model has to keep pace with configfile precedence across seven candidate
filenames, ini-mode versus pytest 9's native TOML mode, `pythonpath` entry
order, symlinks, and module suffixes. Every one of those is a way for the model
to disagree with the tool and report clean. Running a real child invocation and
asking where the package actually came from needs no model, and covers the
shapes the model had to enumerate -- including a config file this module would
not have known to read.

The probe targets each package's declared `testpaths`, the innermost directory a
real invocation names, so any config at or above it is in scope.

**Why it cannot live in a package test tree.** It reads sibling packages' and
the repository root's `pyproject.toml`. `packages/agentbundle/tests/` ships in
the agentbundle sdist and is re-run against an extracted workspace holding
neither, so a test there would pass locally and fail the sdist artifact gate.
`tests/AGENTS.md` owns that boundary.

`build-check.yml` names this file explicitly; roster is not auto-discovered.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PACKAGES = _REPO / "packages"
_PROBE_DIR = Path(__file__).resolve().parent / "fixtures"


def _load(pyproject: Path) -> dict[str, object]:
    """Parse a pyproject with the TOML library rather than a line pattern."""
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def _distributions() -> list[Path]:
    """Return every `packages/*/pyproject.toml`, sorted for a stable report."""
    return sorted(_PACKAGES.glob("*/pyproject.toml"))


def _suite_target(pyproject: Path) -> Path:
    """Return the innermost directory a real invocation of this suite names."""
    table = _load(pyproject).get("tool", {})
    if isinstance(table, dict):
        ini = table.get("pytest", {})
        ini = ini.get("ini_options", {}) if isinstance(ini, dict) else {}
        paths = ini.get("testpaths") if isinstance(ini, dict) else None
        if isinstance(paths, list) and paths and isinstance(paths[0], str):
            candidate = pyproject.parent / paths[0]
            if candidate.is_dir():
                return candidate
    return pyproject.parent


def _import_name(pyproject: Path) -> str:
    """Derive the importable name from the distribution name.

    A distribution name is not an import name in general, but it is for all
    three here. A future package where they diverge fails loudly below as
    `unimportable` rather than passing quietly, which is the safe direction.
    """
    project = _load(pyproject).get("project")
    name = project.get("name") if isinstance(project, dict) else None
    assert isinstance(name, str) and name, (
        f"{pyproject.relative_to(_REPO)} declares no [project].name, so the "
        "package this check should import cannot be derived"
    )
    return name.replace("-", "_")


def _probe(target: Path, import_name: str, output: Path) -> dict[str, object]:
    """Run a child pytest against `target` and report where `import_name` came from."""
    env = dict(os.environ)
    env["PYTEST_RESOLUTION_PROBE_IMPORT"] = import_name
    env["PYTEST_RESOLUTION_PROBE_OUTPUT"] = str(output)
    # Only the probe's own directory goes on the child's PYTHONPATH. It holds no
    # distribution, so it cannot affect the resolution being measured.
    env["PYTHONPATH"] = str(_PROBE_DIR)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(target),
            "-p",
            "pytest_resolution_probe",
            "--collect-only",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
            "-q",
        ],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert output.is_file(), (
        f"the probe against {target.relative_to(_REPO)} wrote no verdict, so this "
        "check measured nothing and a clean result below would prove nothing. "
        f"exit={completed.returncode}\nstdout:\n{completed.stdout[-2000:]}"
        f"\nstderr:\n{completed.stderr[-2000:]}"
    )
    return json.loads(output.read_text(encoding="utf-8"))


def test_every_package_suite_resolves_its_package_inside_its_own_directory(
    tmp_path: Path,
) -> None:
    """The real invocation must import the worktree's copy, not an installed one."""
    distributions = _distributions()
    assert distributions, (
        f"no packages/*/pyproject.toml under {_PACKAGES.relative_to(_REPO)} -- this "
        "check walked an empty domain and would report clean however broken the "
        "packages were"
    )

    failures: list[str] = []
    for pyproject in distributions:
        package_dir = pyproject.parent
        label = str(package_dir.relative_to(_REPO))
        import_name = _import_name(pyproject)
        target = _suite_target(pyproject)
        verdict = _probe(target, import_name, tmp_path / f"{import_name}.json")
        invocation = f"pytest {target.relative_to(_REPO)}/"

        if verdict["state"] == "unimportable":
            failures.append(
                f"{label}: `{invocation}` cannot import {import_name} at all "
                f"({verdict['detail']}). Its [tool.pytest.ini_options] shadows the "
                "root table, so it needs a `pythonpath` of its own"
            )
            continue

        resolved = Path(str(verdict["path"])).resolve()
        if package_dir not in resolved.parents:
            failures.append(
                f"{label}: `{invocation}` imports {import_name} from {resolved}, "
                f"outside {label}/. The suite is therefore reporting on that copy "
                "rather than on the tree under test. Give this package's "
                '[tool.pytest.ini_options] `pythonpath = ["."]`, listed before any '
                "entry that resolves elsewhere"
            )

    assert not failures, "\n".join(failures)


def test_the_root_pythonpath_still_names_every_package() -> None:
    """The root list is a per-package literal, so it goes stale silently.

    The probe above covers each package's own invocation. It does not cover a
    bare `pytest` from the repository root, which is what this list exists for --
    and nothing else compares the list against the packages that exist.
    """
    table = _load(_REPO / "pyproject.toml")["tool"]["pytest"]["ini_options"]  # type: ignore[index]
    declared = {str(entry) for entry in table["pythonpath"]}  # type: ignore[index]
    missing = sorted(
        str(p.parent.relative_to(_REPO)) for p in _distributions()
        if str(p.parent.relative_to(_REPO)) not in declared
    )
    assert not missing, (
        f"the root pyproject's `pythonpath` does not name {', '.join(missing)}, so a "
        "bare `pytest` from the repository root resolves that package from "
        "site-packages. Add each missing directory to the list"
    )
