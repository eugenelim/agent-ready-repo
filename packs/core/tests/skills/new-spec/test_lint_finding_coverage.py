#!/usr/bin/env python3
"""Pytest coverage for the finding-coverage check.

The subject detects rules whose message no test observes. Its own suite is the
first place that failure would hide, so every case here is built from a fixture
skill tree rather than from this repository's layout — the check ships to
adopters whose directories are nothing like ours, and a suite that only runs
against our shape proves nothing about theirs.

Two cases carry the design:

  * `test_a_scan_where_nobody_opted_in_is_a_finding` — without it the check
    passes vacuously on any repository where no script declares a catalogue,
    which is precisely the defect it exists to detect, one level up again.

  * `test_the_suite_is_found_at_several_depths` — an installed skill, a pack in a
    catalogue and a loose script all sit at different distances from their tests.
    Guessing one depth finds nothing in the other two, silently.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "new-spec"
SUBJECT = _SKILL_DIR / "scripts" / "lint-finding-coverage.py"
if not SUBJECT.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {SUBJECT} — check the parents[] depth")

SCRIPT = '''#!/usr/bin/env python3
"""A fixture checker."""
FINDING_KINDS = {
    "alpha": "the alpha rule fired",
    "beta": "the beta rule fired",
}
'''


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SUBJECT), "--root", str(root), *args],
        capture_output=True, text=True, check=False,
    )


@pytest.fixture()
def root():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def _skill(root: Path, tests_at: str, body: str, script: str = SCRIPT) -> Path:
    """Build a fixture skill whose suite sits at a caller-chosen depth."""
    scripts = root / "packs" / "demo" / ".apm" / "skills" / "widget" / "scripts"
    scripts.mkdir(parents=True)
    subject = scripts / "check.py"
    subject.write_text(script, encoding="utf-8")
    suite = root / tests_at
    suite.mkdir(parents=True, exist_ok=True)
    (suite / "test_widget.py").write_text(body, encoding="utf-8")
    return subject


def test_a_fully_covered_subject_has_no_findings(root):
    subject = _skill(
        root, "packs/demo/tests/skills/widget",
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n')
    result = _run(root, str(subject))
    assert result.returncode == 0, result.stdout
    assert "0 finding(s); 1 subject(s) checked" in result.stdout


def test_an_unobserved_rule_is_named(root):
    subject = _skill(
        root, "packs/demo/tests/skills/widget",
        'def test_a():\n    assert "the alpha rule fired" in out\n')
    result = _run(root, str(subject))
    assert result.returncode == 1, result.stdout
    assert "can emit findings no test observes: beta" in result.stdout
    assert "alpha" not in result.stdout.split("observes:")[1]


def test_a_subject_without_a_catalogue_is_skipped_not_failed(root):
    """Opt-in: adding this check must fail nothing that has not opted in."""
    subject = _skill(root, "packs/demo/tests/skills/widget",
                     "def test_a():\n    pass\n",
                     script='"""No catalogue here."""\nVALUE = 1\n')
    result = _run(root, str(subject))
    assert result.returncode == 0, result.stdout
    assert "0 subject(s) checked, 1 skipped as not opted in" in result.stdout


def test_a_scan_where_nobody_opted_in_is_a_finding(root):
    """The vacuous-pass guard.

    A scan that finds no participant must say so and fail, or the check reports
    success over a repository it never examined — which is the defect it detects.
    """
    subject = _skill(root, "packs/demo/tests/skills/widget",
                     "def test_a():\n    pass\n",
                     script='"""No catalogue."""\n')
    result = _run(root, str(subject))
    assert result.returncode == 0, "a single non-participant is a skip, not a failure"
    result = _run(root, "--discover", str(root / "packs"))
    assert "no subject declares FINDING_KINDS" in result.stdout
    assert result.returncode == 1, result.stdout


def test_a_catalogue_with_no_suite_is_a_finding(root):
    subject = _skill(root, "unrelated", "def test_a():\n    pass\n")
    (root / "unrelated" / "test_widget.py").unlink()
    result = _run(root, str(subject))
    assert result.returncode == 1, result.stdout
    assert "declares findings but no test source was found" in result.stdout
    assert "looked in" in result.stdout, "the report must name the directories it considered"


@pytest.mark.parametrize(
    "tests_at",
    ["packs/demo/tests/skills/widget",
     "packs/demo/.apm/skills/widget/tests",
     "tests"],
)
def test_the_suite_is_found_at_several_depths(root, tests_at):
    """An adopter's layout is not this catalogue's, and the depth is not fixed."""
    subject = _skill(
        root, tests_at,
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n')
    result = _run(root, str(subject))
    assert result.returncode == 0, f"suite at {tests_at} was not found:\n{result.stdout}"


def test_an_explicit_tests_directory_overrides_discovery(root):
    subject = _skill(root, "unrelated", "def test_a():\n    pass\n")
    (root / "unrelated" / "test_widget.py").write_text(
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n', encoding="utf-8")
    result = _run(root, str(subject), "--tests", str(root / "unrelated"))
    assert result.returncode == 0, result.stdout


def test_the_searched_directory_list_is_capped(root):
    """The candidate set must be named without the naming itself flooding."""
    subject = _skill(
        root, "packs/demo/tests/skills/widget",
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n')
    extra = [root / f"extra{i}" for i in range(9)]
    for directory in extra:
        directory.mkdir()
        (directory / "test_x.py").write_text("def t():\n    pass\n", encoding="utf-8")
    result = _run(root, str(subject), *[a for d in extra for a in ("--tests", str(d))])
    line = next(l for l in result.stdout.splitlines() if "searched" in l)
    assert "more" in line, f"the list must be capped:\n{line}"
    assert len(line) < 700, f"a capped line must actually be short:\n{len(line)}"


def test_a_subject_outside_the_root_is_refused(root):
    _skill(root, "tests", "def test_a():\n    pass\n")
    result = _run(root, str(root.parent / "elsewhere.py"))
    assert result.returncode == 2, result.stdout
    assert "refusing path outside root" in result.stdout


def test_a_subject_that_cannot_be_parsed_is_reported_not_counted_as_a_skip(root):
    """Cannot-read is not declares-none.

    Both used to land in "skipped as not opted in", so an unreadable file read
    as a deliberate non-participant — a silent gap in exactly the inventory this
    check exists to make complete.
    """
    subject = _skill(root, "tests", "def test_a():\n    pass\n",
                     script="def broken(:\n")
    result = _run(root, str(subject))
    assert result.returncode == 1, result.stdout
    assert "could not be parsed" in result.stdout
    assert "0 skipped as not opted in, 1 unreadable" in result.stdout
    assert "Traceback" not in result.stderr


def test_discovery_mode_reports_an_unreadable_subject(root):
    """The unreadable branch was unreachable in the mode that scans blind.

    Discovery filtered candidates on a truthy catalogue, and an unparseable file
    reads as falsy — so the one mode scanning a tree the caller has not inspected
    was the one that could not report a file it could not read.
    """
    subject = _skill(
        root, "packs/demo/tests/skills/widget",
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n')
    (subject.parent / "broken.py").write_text("def x(:\n", encoding="utf-8")
    result = _run(root, "--discover", str(root / "packs"))
    assert result.returncode == 1, result.stdout
    assert "could not be parsed" in result.stdout
    assert "1 unreadable" in result.stdout


def test_the_searched_directories_are_named_on_a_clean_report(root):
    """Silence about the candidate set is what turns a heuristic into a false clean."""
    subject = _skill(
        root, "packs/demo/tests/skills/widget",
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n')
    result = _run(root, str(subject))
    assert result.returncode == 0, result.stdout
    assert "searched" in result.stdout and "skills/widget" in result.stdout


def test_the_repository_wide_tests_tree_is_only_a_fallback(root):
    """A specific match must not be widened by an unrelated suite.

    With both present, a fragment observed only by the repository-wide tree read
    as covered. The specific directory wins, and the wide one is taken only when
    nothing names the skill.
    """
    subject = _skill(root, "packs/demo/tests/skills/widget",
                     'def test_a():\n    assert "the alpha rule fired" in out\n')
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests" / "test_unrelated.py").write_text(
        'def test_z():\n    assert "the beta rule fired" in out\n', encoding="utf-8")
    result = _run(root, str(subject))
    assert result.returncode == 1, "the unrelated suite must not cover beta"
    assert "no test observes: beta" in result.stdout


def test_the_catalogue_is_read_without_importing_the_subject(root):
    """A subject with a side effect at import must not run because of this check."""
    marker = root / "imported.flag"
    subject = _skill(
        root, "packs/demo/tests/skills/widget",
        'def test_a():\n    assert "the alpha rule fired" in out\n'
        'def test_b():\n    assert "the beta rule fired" in out\n',
        script=f'import pathlib\npathlib.Path({str(marker)!r}).write_text("ran")\n' + SCRIPT)
    result = _run(root, str(subject))
    assert result.returncode == 0, result.stdout
    assert not marker.exists(), "the subject was imported; it must only be parsed"
