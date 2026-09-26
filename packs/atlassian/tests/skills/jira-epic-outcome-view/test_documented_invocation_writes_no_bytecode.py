"""The documented command leaves no bytecode cache in the installed tree.

The view promises the installed pack tree is byte-identical across a run.
A child interpreter is held to that by an environment variable, but the
view's own interpreter is not: importing the package compiles it into a
`__pycache__` directory beside its sources, and that happens before the
first statement of the program runs. No assignment inside `__init__.py`
can prevent its own compilation, so the guarantee has to come from the
command -- which means the command as documented is what this asserts.

The flags come out of `SKILL.md` rather than being restated here. A
command that loses the flag and a reader who follows the documentation
are then the same failure, and this catches both.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest

_INVOCATION = re.compile(r"^python3 (?P<flags>.*?)-m jira_epic_outcome_view\b", re.M)
_SKILL_MD = guarantees.VIEW_SKILL_DIR / "SKILL.md"


def documented_flag_sets() -> list[list[str]]:
    """The interpreter flags on every documented invocation, in order."""
    text = _SKILL_MD.read_text("utf-8")
    return [match.group("flags").split() for match in _INVOCATION.finditer(text)]


def test_the_documentation_shows_at_least_one_invocation():
    """A grammar that matched nothing would make every case below vacuous."""
    assert documented_flag_sets(), f"no documented invocation found in {_SKILL_MD}"


def test_every_documented_invocation_carries_the_same_flags():
    """One command that keeps the guarantee and one that quietly drops it
    is worse than neither: a reader copies whichever they saw first."""
    flag_sets = documented_flag_sets()

    assert len({tuple(flags) for flags in flag_sets}) == 1, flag_sets


@pytest.fixture
def cold_scripts_tree(tmp_path):
    """A copy of the skill's `scripts/` with no compiled cache in it.

    Copied rather than used in place, so the check starts cold whatever
    earlier tests imported, and so the assertion never depends on
    deleting anything from the tree the view promises not to change.
    """
    destination = tmp_path / "scripts"
    shutil.copytree(
        guarantees.VIEW_SCRIPTS_DIR,
        destination,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    assert not list(destination.rglob("__pycache__")), "the copy started warm"
    return destination


def test_the_documented_invocation_writes_no_bytecode_beside_the_sources(
    cold_scripts_tree,
):
    """Run with the flags the documentation shows, and nothing else. The
    environment variable the view sets for its child spawns is cleared
    first: it would otherwise answer for the parent process too and this
    would pass on a command that guarantees nothing.
    """
    flags = documented_flag_sets()[0]
    env = dict(os.environ)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    env["PYTHONPATH"] = str(cold_scripts_tree)

    completed = subprocess.run(
        [sys.executable, *flags, "-m", "jira_epic_outcome_view", "--help"],
        cwd=cold_scripts_tree,
        env=env,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert b"--project" in completed.stdout, "the run never reached the CLI"
    written = sorted(
        str(path.relative_to(cold_scripts_tree))
        for path in cold_scripts_tree.rglob("__pycache__")
    )
    assert written == [], (
        "importing the view compiled it into the tree beside its own sources: "
        f"{written}"
    )
