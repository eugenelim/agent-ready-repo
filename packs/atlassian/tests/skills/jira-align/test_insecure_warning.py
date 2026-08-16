#!/usr/bin/env python3
"""`--insecure` must disclose itself on stderr.

`docs/CONVENTIONS.md` § *Five anti-patterns rejected by name* requires
``--insecure`` to be opt-in and to "emit a stderr warning". This CLI was silent.

Unlike ``jira.py`` and ``crawl_space.py`` there is no SSO-cookie path here, so
there is one message and no inert case to distinguish.

Driven as a subprocess, matching this directory's ``test_exit_codes.py``. The
warning is emitted in ``main`` right after logging is configured, so it lands
before the run fails on absent credentials — which is the point: a run that
cannot resolve a credential must still disclose that verification was asked to
be turned off.

``--insecure`` is a top-level flag, so it precedes the subcommand:
``jira_align.py --insecure check``, not ``jira_align.py check --insecure``
(argparse rejects the latter with "unrecognized arguments").

Run with pytest.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[3] / ".apm" / "skills" \
    / "jira-align" / "scripts"
if not HERE.is_dir():                     # wrong parents[] depth after a move
    raise SystemExit(f"skill scripts dir not found at {HERE}")
CLI = HERE / "jira_align.py"

_WARNING = "--insecure disables TLS certificate verification"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def _skip_if_deps_absent(proc: subprocess.CompletedProcess) -> None:
    """The import guard exits 2 before main runs when httpx is missing."""
    if proc.returncode == 2 and "missing dependency" in proc.stderr:
        pytest.skip("skill dependencies not installed in this environment")


def test_insecure_emits_a_stderr_warning() -> None:
    proc = _run("--insecure", "check")
    _skip_if_deps_absent(proc)
    assert _WARNING in proc.stderr, (
        f"--insecure must disclose itself on stderr; got: {proc.stderr!r}"
    )


def test_the_warning_goes_to_stderr_not_stdout() -> None:
    """stdout carries the CLI's data payload; a warning there would corrupt a
    piped `--format json` consumer."""
    proc = _run("--insecure", "check")
    _skip_if_deps_absent(proc)
    assert _WARNING not in proc.stdout


def test_no_warning_without_the_flag() -> None:
    proc = _run("check")
    _skip_if_deps_absent(proc)
    assert "--insecure" not in proc.stderr


def test_warning_precedes_credential_resolution() -> None:
    """A run with no credentials still discloses.

    The warning used to sit at client construction, after `load_credentials()`.
    On a machine with no credential configured that path returns first, so the
    disclosure never printed on exactly the runs most likely to be debugging a
    TLS problem.
    """
    proc = _run("--insecure", "check")
    _skip_if_deps_absent(proc)
    # `check` exits non-zero without a credential; the warning must be there anyway.
    assert proc.returncode != 0
    assert _WARNING in proc.stderr
