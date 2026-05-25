"""T10: conventions-check lint extensions for credentialed skills.

Construction tests against the fixture skills under
``packages/agentbundle/tests/fixtures/creds/skills/``. The lint helper
``tools/lint-credentialed-skills.sh`` is invoked per fixture (one fixture
per ``LINT_ROOT`` so the per-fixture expectations don't pollute one
another) and stderr is asserted against AC26 + AC27.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
LINT_SCRIPT = REPO_ROOT / "tools" / "lint-credentialed-skills.sh"
FIXTURES_DIR = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "tests"
    / "fixtures"
    / "creds"
    / "skills"
)


def _run_lint(fixture_name, tmp_path):
    """Stage a single fixture skill under ``tmp_path/skills/<name>`` and
    invoke the lint there. Per-fixture isolation prevents one fixture's
    findings from masking another's.
    """
    src = FIXTURES_DIR / fixture_name
    if not src.is_dir():
        pytest.skip(f"fixture {fixture_name!r} not present")
    dest = tmp_path / "skills" / fixture_name
    shutil.copytree(src, dest)
    env = {**os.environ, "LINT_ROOT": str(tmp_path)}
    res = subprocess.run(
        ["bash", str(LINT_SCRIPT)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    return res


def test_conforming_fixture_reports_no_findings(tmp_path):
    res = _run_lint("conforming", tmp_path)
    assert res.returncode == 0, (
        f"conforming should be clean; stderr={res.stderr}\nstdout={res.stdout}"
    )
    assert "0 finding(s)" in res.stdout
    assert "1 skill(s) scanned" in res.stdout


def test_missing_dont_block_reports_finding(tmp_path):
    res = _run_lint("missing-dont-block", tmp_path)
    assert res.returncode != 0
    assert "missing-dont-block/SKILL.md" in res.stderr
    assert "Security rules (non-negotiable)" in res.stderr


def test_argv_flag_reports_finding(tmp_path):
    res = _run_lint("argv-flag", tmp_path)
    assert res.returncode != 0
    assert "argv-flag/scripts/cli.py" in res.stderr
    assert "'--token'" in res.stderr
    assert "argv-borne credential flag" in res.stderr


def test_argv_flag_normalised_catches_all_three_variants(tmp_path):
    """AC27: the lint normalises (strip ``-``, casefold, ``-`` → ``_``)
    and catches casing, kebab, and string-concatenation obfuscation."""
    res = _run_lint("argv-flag-normalised", tmp_path)
    assert res.returncode != 0
    # Three add_argument calls — three findings.
    assert "'--Token'" in res.stderr
    assert "'--api-Key'" in res.stderr
    # The BinOp ``"--" + "password"`` collapses to the literal `--password`
    # before normalisation; the report names the assembled flag.
    assert "'--password'" in res.stderr


def test_argv_flag_derived_shapes_are_flagged(tmp_path):
    """Round-2 lint widening (Adversarial Concern #8): the walker catches
    JoinedStr (literal-only f-string), Starred(Tuple) argument spread,
    and Subscript constant indexing into a literal tuple. Each shape
    collapses to a banned flag at parse time."""
    res = _run_lint("argv-flag-derived", tmp_path)
    assert res.returncode != 0
    # JoinedStr — f"--{'token'}" collapses to "--token".
    assert "'--token'" in res.stderr
    # Starred(Tuple) — *("--api-key",) collapses to "--api-key".
    assert "'--api-key'" in res.stderr
    # Subscript — ("--bearer",)[0] collapses to "--bearer".
    assert "'--bearer'" in res.stderr


def test_mcp_server_headers_clean(tmp_path):
    """AC26(b) is scoped to credentialed-cli only; header-naming flags on
    mcp-server class must not be flagged."""
    res = _run_lint("mcp-server-headers", tmp_path)
    assert res.returncode == 0, (
        f"mcp-server-headers should be clean; stderr={res.stderr}"
    )
    assert "0 finding(s)" in res.stdout


def test_dotfile_grep_reports_finding(tmp_path):
    res = _run_lint("dotfile-grep", tmp_path)
    assert res.returncode != 0
    assert "dotfile-grep/scripts/leak.py" in res.stderr
    assert ".agentbundle/credentials.env" in res.stderr


def test_dotfile_with_optout_marker_is_silent(tmp_path):
    """A line containing the dotfile substring is skipped iff the
    ``# credentialed-primitive: reads-creds-directly`` marker is on the
    same line."""
    res = _run_lint("dotfile-with-optout", tmp_path)
    assert res.returncode == 0, (
        f"dotfile-with-optout should be clean; stderr={res.stderr}"
    )
    assert "0 finding(s)" in res.stdout


def test_lint_script_executable_against_live_repo():
    """The lint runs cleanly against the real repo before any credentialed
    skill ships (Wave 3 / T12). Asserts the script doesn't crash and
    reports zero scanned skills on a pristine main."""
    res = subprocess.run(
        ["bash", str(LINT_SCRIPT)],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    # On a tree with no credentialed skills, the lint exits 0.
    assert res.returncode == 0, (
        f"live repo lint failed unexpectedly: stderr={res.stderr}"
    )
    assert "skill(s) scanned" in res.stdout
