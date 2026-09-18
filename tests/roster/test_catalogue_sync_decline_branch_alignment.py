"""Keep T2's decline fixtures aligned with the repository grounding derivation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from packages.agentbundle.tests.unit.test_catalogue_tooling_self_hosted_init import (
    _STALE_DECLINE_FIXTURES,
    _UNDECIDED_STALE_DECLINE_REASONS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_DECLINE_BRANCH_DERIVATION = (
    REPO_ROOT
    / "docs/specs/catalogue-sync-dry-run/notes/grounding/derive-decline-branches.py"
)


def test_plan_stale_owned_paths_decline_fixture_count_matches_guard() -> None:
    """Keep independently pinned fixtures aligned with the grounding derivation."""
    result = subprocess.run(
        [
            sys.executable,
            str(_DECLINE_BRANCH_DERIVATION),
            "packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    branch_count = int(
        next(
            line.removeprefix("decline branches: ")
            for line in result.stdout.splitlines()
            if line.startswith("decline branches: ")
        )
    )
    assert branch_count == len(_STALE_DECLINE_FIXTURES)
    assert "residual silent lines: none" in result.stdout
    assert {fixture[4] for fixture in _STALE_DECLINE_FIXTURES} >= (
        _UNDECIDED_STALE_DECLINE_REASONS
    )
