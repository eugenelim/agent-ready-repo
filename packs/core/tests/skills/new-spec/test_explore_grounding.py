#!/usr/bin/env python3
"""Pytest coverage for the grounding explorer.

Runs the explorer as a subprocess against fixture trees, following the precedent
in `packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py`.

Three cases carry the design rather than a feature, and each exists because a
prototype failed at it first:

  * `test_portability_fixture_with_foreign_top_levels` builds a repository whose
    top-level names share nothing with this catalogue's. The prototype hardcoded
    an allowlist of top-level directories, and a seeded reference under a name it
    omitted returned zero findings and read as clean. A suite that only ever runs
    against this repository's shape would have passed on that.

  * `test_co_change_reports_unavailable_without_history` covers the outcome that
    is neither found nor none. The work-loop is used on repositories before git
    is initialised, and a probe that returns empty when its input is missing is
    indistinguishable from a clean result.

  * `test_boilerplate_phrase_is_excluded` carries the calibration. Uncalibrated,
    this probe returned every skill in the catalogue because they share a shipped
    rendering block. Its mutation proof is in the assertion: the same phrase in
    few files must still be reported, so a probe that simply stopped reporting
    phrases would fail the sibling case.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "new-spec"
EXPLORER = _SKILL_DIR / "scripts" / "explore-grounding.py"
if not EXPLORER.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {EXPLORER} — check the parents[] depth")

LONG = "The seed file states a rule long enough to be distinctive when quoted elsewhere."


def _run(root: Path, *seeds: str, extra: list[str] | None = None) -> str:
    result = subprocess.run(
        [sys.executable, str(EXPLORER), "--root", str(root), *(extra or []), *seeds],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, f"explorer must report, never decide:\n{result.stdout}\n{result.stderr}"
    return result.stdout


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)


@pytest.fixture()
def root():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def _seeded(root: Path, top: str = "lib") -> str:
    """A tree whose top-level name is a parameter, so the suite cannot assume ours."""
    (root / top).mkdir(parents=True)
    (root / top / "seed.md").write_text(f"# Seed\n\n{LONG}\n", encoding="utf-8")
    (root / top / "AGENTS.md").write_text("scoped guidance\n", encoding="utf-8")
    (root / "AGENTS.md").write_text("root guidance\n", encoding="utf-8")
    (root / "consumer.md").write_text(f"We depend on {top}/seed.md for this.\n", encoding="utf-8")
    (root / "Makefile").write_text(f"check:\n\tpytest {top}/seed.md\n", encoding="utf-8")
    return f"{top}/seed.md"


def test_portability_fixture_with_foreign_top_levels(root):
    """Top-level names are derived, not declared.

    `app/` appears in no allowlist this catalogue could ship. A hardcoded list
    finds nothing here and reports it as a clean run.
    """
    seed = _seeded(root, top="app")
    out = _run(root, seed)
    assert "consumer.md" in out, out
    assert "app/AGENTS.md" in out and "AGENTS.md" in out, out


def test_scoped_rules_walks_to_the_root_not_to_the_nearest(root):
    seed = _seeded(root)
    out = _run(root, seed)
    block = out.split("scoped rules", 1)[1]
    assert "lib/AGENTS.md" in block and "\n      AGENTS.md" in block, out


def test_gate_reachability_reports_unreached_as_the_finding(root):
    """A seed no runner names is the finding, not the absence of one."""
    seed = _seeded(root)
    (root / "Makefile").write_text("check:\n\techo nothing\n", encoding="utf-8")
    out = _run(root, seed)
    assert "UNREACHED" in out, out
    assert "considered" in out, "the report must name how many runners it looked at"


def test_gate_reachability_finds_a_runner_that_names_the_seed(root):
    seed = _seeded(root)
    out = _run(root, seed)
    assert "UNREACHED" not in out, out
    assert "Makefile" in out, out


def test_boilerplate_phrase_is_excluded_but_a_real_pin_is_kept(root):
    """The cutoff, and the proof it did not simply stop reporting phrases."""
    seed = _seeded(root)
    for index in range(6):
        (root / f"boiler{index}.md").write_text(LONG + "\n", encoding="utf-8")
    (root / "pinner.md").write_text(f"quoting: {LONG}\n", encoding="utf-8")
    out = _run(root, seed)
    assert "boiler0.md" not in out, "a phrase in many files is boilerplate, not a pin"

    for index in range(6):
        (root / f"boiler{index}.md").unlink()
    kept = _run(root, seed)
    assert "pinner.md" in kept, "with the boilerplate gone the same phrase must be reported"


def test_co_change_reports_unavailable_without_history(root):
    """Neither found nor none: the input is missing and the output must say so."""
    seed = _seeded(root)
    out = _run(root, seed)
    assert "unavailable" in out, out
    assert "not a clean result" in out, out


def test_co_change_finds_a_partner_from_history(root):
    seed = _seeded(root)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.invalid")
    _git(root, "config", "user.name", "t")
    partner = root / "lib" / "partner.md"
    for index in range(4):
        (root / seed).write_text(f"# Seed {index}\n\n{LONG}\n", encoding="utf-8")
        partner.write_text(f"partner {index}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"c{index}")
    out = _run(root, seed)
    assert "lib/partner.md" in out, out
    assert "confidence" in out, "a raw count without its ratio is not calibrated"


def test_result_cap_reports_an_exact_remainder(root):
    seed = _seeded(root)
    for index in range(9):
        (root / f"ref{index}.md").write_text(f"see lib/seed.md\n", encoding="utf-8")
    out = _run(root, seed, extra=["--cap", "3"])
    assert "capped at 3" in out, out
    # The remainder must be exact, not approximate: derive it from the reported
    # total rather than hardcoding, so the case survives a fixture change.
    total = int(re.search(r"path refs\s+(\d+)", out).group(1))
    assert f"and {total - 3} more" in out, f"remainder must be exact:\n{out}"


def test_seed_outside_the_root_is_refused(root):
    result = subprocess.run(
        [sys.executable, str(EXPLORER), "--root", str(root), "../escape.md"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2, result.stdout
    assert "refusing seed outside root" in result.stdout


def test_missing_git_is_announced_not_hidden(root):
    seed = _seeded(root)
    out = _run(root, seed)
    assert "git unavailable" in out, "a degraded run must say it degraded"
