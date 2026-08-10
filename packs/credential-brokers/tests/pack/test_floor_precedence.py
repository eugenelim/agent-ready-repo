"""credbroker-user-scope T1: consumer bootstraps append the vendored
``~/.agentbundle/lib`` floor at LOWEST ``sys.path`` precedence.

Two lenses, parametric across all six edited consumer scripts (the five
API CLIs + ``credential-setup``'s ``setup.py``):

1. **Source guard (always runs, deps-free) — the precedence mechanism.**
   Each script *appends* the floor and *never* inserts it (the spec's
   "never prepend" Never-do: a stale floor must never shadow a real
   pip-installed ``credbroker``). Because ``sys.path`` is searched in
   order and the floor is the last entry, any earlier entry — including
   site-packages — wins. Placement is checked too: the CLIs append after
   their ``sys.path.insert(0, str(_here.parent))`` skill-dir insert;
   ``setup.py`` (no bootstrap, top-level ``from credbroker import``)
   appends *before* that import so the floor is reachable when it runs.

2. **Behavioral precedence (``credbroker.__file__``) on ``setup.py``.**
   ``setup.py`` is the one *eager*, dependency-free importer — it does
   ``from credbroker import …`` at module top with only stdlib siblings,
   so a real ``python scripts/setup.py`` invocation observably resolves a
   planted ``credbroker`` (floor-only → the floor; an earlier sys.path
   copy present → that copy, never the floor). The five API CLIs import
   ``credbroker`` *lazily* (only inside an ``httpx``-requiring credential
   verb), so their end-to-end floor resolution through a real consumer is
   T4's explicit integration test; at T1 their precedence is proven
   structurally by lens 1 (identical bootstrap edit). Per
   ``test_credential_user_scope_invocation.py``'s convention — and
   ``feedback_test_real_invocation_not_synthesised_import`` — these use
   real subprocess invocation, no ``runpy.run_path`` / importlib
   synthesis / package-context forging.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]  # pack tests -> repository root
PACKS = REPO_ROOT / "packs"

_FAKE_CREDBROKER = (
    "import os as _os\n"
    "_p = _os.environ.get('FLOOR_PROBE')\n"
    "if _p:\n"
    "    with open(_p, 'w', encoding='utf-8') as _f:\n"
    "        _f.write(__file__)\n"
    "def __getattr__(_name):\n"  # satisfy `from credbroker import <names>`
    "    return object()\n"
)


def _plant_credbroker(parent: pathlib.Path) -> pathlib.Path:
    """Write a self-reporting fake ``credbroker`` package under *parent*;
    returns the package __init__.py (its __file__ when imported)."""
    pkg = parent / "credbroker"
    pkg.mkdir(parents=True)
    init = pkg / "__init__.py"
    init.write_text(_FAKE_CREDBROKER, encoding="utf-8", newline="\n")
    return init


def _stage_setup_scripts(tmp_path: pathlib.Path) -> pathlib.Path:
    """Stage credential-setup's scripts/ dir as user-scope install would:
    a flat scripts/ with no __init__.py. Returns the staged scripts/ dir."""
    src = PACKS / "credential-brokers/.apm/skills/credential-setup/scripts"
    staged = tmp_path / "skill" / "scripts"
    staged.mkdir(parents=True)
    for entry in src.iterdir():
        # Match the delivered shape: ship the entry-point + its siblings,
        # not the test files (user-scope install does not place test_*.py).
        if entry.is_file() and entry.suffix == ".py" and not entry.name.startswith("test_"):
            (staged / entry.name).write_bytes(entry.read_bytes())
    assert not (staged / "__init__.py").exists()
    return staged


def _run_setup_help(
    scripts_dir: pathlib.Path,
    *,
    home: pathlib.Path,
    probe: pathlib.Path,
    pythonpath: str | None,
    no_site: bool,
) -> subprocess.CompletedProcess:
    env = {
        k: v
        for k, v in os.environ.items()
        if k in {"PATH", "SystemRoot", "TMPDIR", "TEMP", "TMP"}
    }
    env.pop("PYTHONPATH", None)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["FLOOR_PROBE"] = str(probe)
    if pythonpath is not None:
        env["PYTHONPATH"] = pythonpath
    argv = [sys.executable]
    if no_site:
        argv.append("-S")
    argv += ["scripts/setup.py", "--help"]
    return subprocess.run(
        argv,
        cwd=str(scripts_dir.parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def test_setup_floor_is_lowest_precedence(tmp_path: pathlib.Path) -> None:
    """setup.py's appended floor is the LOWEST-precedence credbroker.

    Two real ``python scripts/setup.py`` runs (no run_path), observing
    ``credbroker.__file__`` via a planted self-reporting fake. The pair is
    mutation-complete — neither half passes vacuously against the other's
    failure mode:

    * **floor-only** (``-S`` hides any pip-installed credbroker): the floor
      resolves. Goes red if the append is absent/broken — the floor is then
      unreachable and ``from credbroker import`` cannot resolve at all.
    * **floor + an earlier sys.path copy** (PYTHONPATH, modelling a pip
      install): the earlier copy wins, never the floor. Goes red if the
      floor is *prepended* (``insert(0)``) — a prepended floor sits at
      index 0, ahead of the PYTHONPATH copy, and would shadow the real
      install (the spec's "never prepend" Never-do).
    """
    scripts_dir = _stage_setup_scripts(tmp_path)
    home = tmp_path / "home"
    floor_init = _plant_credbroker(home / ".agentbundle" / "lib")

    # floor-only → the floor resolves (proves the append ran and is reachable).
    floor_probe = tmp_path / "probe_floor.txt"
    proc = _run_setup_help(
        scripts_dir, home=home, probe=floor_probe, pythonpath=None, no_site=True
    )
    assert floor_probe.is_file(), (
        "floor-only: credbroker was never imported by setup.py "
        f"(rc={proc.returncode}); stderr:\n{proc.stderr}"
    )
    assert floor_probe.read_text(encoding="utf-8") == str(floor_init), (
        "floor-only: import credbroker must resolve from ~/.agentbundle/lib"
    )

    # floor + earlier copy → the earlier copy wins (proves the floor is
    # appended, not prepended; would flip if the floor were insert(0)'d).
    site_dir = tmp_path / "site"
    site_init = _plant_credbroker(site_dir)
    site_probe = tmp_path / "probe_site.txt"
    proc = _run_setup_help(
        scripts_dir, home=home, probe=site_probe, pythonpath=str(site_dir), no_site=False
    )
    assert site_probe.is_file(), (
        "site+floor: credbroker was never imported by setup.py "
        f"(rc={proc.returncode}); stderr:\n{proc.stderr}"
    )
    assert site_probe.read_text(encoding="utf-8") == str(site_init), (
        "precedence: an earlier sys.path credbroker must win over the appended floor"
    )
