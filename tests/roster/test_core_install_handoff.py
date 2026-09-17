"""AC1: a real core install prints the deterministic handoff, at both scopes.

These two cases install the repository's *real* `core` pack, so they can only
run inside a checkout that carries `packs/core/`. That is why they live here
rather than under `packages/agentbundle/tests/`: the export-boundary gate builds
an sdist of `agentbundle` and runs the shipped suite inside it, where no
`packs/` tree exists, and a shipped test that needs the repository catalogue
fails there with `install: pack 'core' not found in catalogue`.

Both scopes are asserted side by side on purpose — the handoff must not vary by
scope, and the local case additionally pins the omissions that make the printed
line the only reliable onboarding path.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

# The contract copy of AC1's text, deliberately hard-coded: this literal *is*
# the acceptance criterion, so it should fail loudly if the manifest text moves.
CORE_NEXT_ACTION = (
    "Ask your agent to run adapt-to-project for a read-only readiness check; "
    "start a new session if the skill is unavailable."
)


def _core_install_args(repo: Path, *, scope: str) -> argparse.Namespace:
    """Build arguments for installing the repository's real core pack.

    Parsed rather than hand-built: `install.run` reads every dest the `install`
    subparser declares, so a namespace assembled by hand omits whichever ones
    this test did not think about and fails where no adopter can.
    `packages/agentbundle/tests/_support.cli_namespace` is the same idea, but
    that `tests` package is shadowed by this one at the repository root.

    `--emit-install-routes` is deliberately absent: the old fixture pinned
    `emit_install_routes=False`, and the parser default is also False.
    """
    from agentbundle.cli import _build_parser

    return _build_parser().parse_args([
        "install",
        str(REPOSITORY_ROOT),
        "--pack",
        "core",
        "--output",
        str(repo),
        "--scope",
        scope,
        "--adapter",
        "codex",
        "--yes",
    ])


def _install(repo: Path, *, scope: str) -> tuple[int, str]:
    """Run a real core install, returning its exit code and captured stdout."""
    from agentbundle.commands.install import run as install_run

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = install_run(_core_install_args(repo, scope=scope))
    return rc, out.getvalue()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A minimal git repository, which local scope requires for its exclude."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q", "."], cwd=repo, check=True, capture_output=True
    )
    return repo


def test_real_core_repo_install_emits_deterministic_next_action(
    tmp_path: Path,
) -> None:
    """Repository scope prints the pack-owned handoff verbatim."""
    repo = tmp_path / "repo"
    repo.mkdir()

    rc, output = _install(repo, scope="repo")

    assert rc == 0, f"install failed: {output}"
    assert f"Next:     {CORE_NEXT_ACTION}" in output


def test_real_core_local_install_emits_next_without_marker_or_seeds(
    git_repo: Path,
) -> None:
    """Local scope prints the same handoff while writing none of the extras."""
    rc, output = _install(git_repo, scope="local")

    assert rc == 0, f"install failed: {output}"
    assert "installed: core @ local" in output
    assert f"Next:     {CORE_NEXT_ACTION}" in output

    # Projection and local state still land.
    assert (git_repo / ".codex" / "hooks.json").is_file()
    assert (git_repo / ".agentbundle-local-state.toml").is_file()

    # The omissions that make the printed line the only reliable path.
    assert not (git_repo / "AGENTS.md").exists()
    assert not (git_repo / ".adapt-install-marker.toml").exists()
    assert not (git_repo / "agentbundle-layout.toml").exists()
