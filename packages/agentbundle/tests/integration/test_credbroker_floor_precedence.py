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

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
PACKS = REPO_ROOT / "packs"

# The six edited consumer scripts (skill scripts/ dir, entry filename).
CONSUMER_SCRIPTS = [
    ("credential-brokers/.apm/skills/credential-setup/scripts", "setup.py"),
    ("figma/.apm/skills/figma/scripts", "figma.py"),
    ("atlassian/.apm/skills/jira/scripts", "jira.py"),
    ("atlassian/.apm/skills/jira-align/scripts", "jira_align.py"),
    ("atlassian/.apm/skills/confluence-crawler/scripts", "crawl_space.py"),
    ("atlassian/.apm/skills/confluence-publisher/scripts", "publish_page.py"),
]


# ─────────────────────── lens 1: source guard (×6) ───────────────────────

@pytest.mark.parametrize("skill_relpath,entry_name", CONSUMER_SCRIPTS)
def test_floor_appended_lowest_precedence_never_inserted(
    skill_relpath: str, entry_name: str,
) -> None:
    entry = PACKS / skill_relpath / entry_name
    if not entry.is_file():
        pytest.skip(f"{entry} not present in this checkout")
    src = entry.read_text(encoding="utf-8")

    # Source guard, by design: it pins the canonical floor idiom (the
    # path literal + expanduser + the append call) as well as the
    # no-insert-0 invariant below. The six scripts are repo-owned and
    # edited in lockstep, so a contract-preserving refactor (e.g. to
    # os.path.expanduser, or renaming _floor) is expected to update this
    # guard with it; the load-bearing Never-do is the no-insert-0 scan.
    # The floor is the expanded ~/.agentbundle/lib, appended (lowest
    # precedence) — not a literal "~" dir, not inserted.
    assert '"~/.agentbundle/lib").expanduser()' in src, (
        f"{entry_name}: floor must be ~/.agentbundle/lib resolved via expanduser()"
    )
    assert "sys.path.append(str(_floor))" in src, (
        f"{entry_name}: floor must be appended to sys.path"
    )

    # No-insert-0 guard: the floor must never appear in a sys.path.insert
    # call (which would prepend it and shadow a real pip-installed copy).
    for line in src.splitlines():
        if "sys.path.insert" in line:
            assert "_floor" not in line and "agentbundle/lib" not in line, (
                f"{entry_name}: floor must never be inserted (no-insert-0): {line!r}"
            )

    # Placement proves the floor is the lowest-precedence entry at the
    # point credbroker resolution can occur.
    if entry_name == "setup.py":
        # No bootstrap; top-level `from credbroker import` — the append
        # must run before it, or it runs too late.
        assert src.index("sys.path.append(str(_floor))") < src.index(
            "from credbroker import"
        ), "setup.py: floor-append must precede the top-level `from credbroker import`"
    else:
        # Inside the file-path bootstrap, after the skill-dir insert(0).
        assert src.index("sys.path.insert(0, str(_here.parent))") < src.index(
            "sys.path.append(str(_floor))"
        ), f"{entry_name}: floor-append must follow the skill-dir insert(0)"


# ─────────── lens 2: behavioral precedence on setup.py (eager) ───────────

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
    init.write_text(_FAKE_CREDBROKER, encoding="utf-8")
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
