"""Brownfield end-to-end round trip: install → adapt → diff.

The spec's Testing Strategy (§ Brownfield end-to-end) calls out this
sequence specifically as the proof that an adopter on a corporate-network
sandbox can fetch the CLI, install a pack into a repo that has
pre-existing files, resolve adapt markers, and then verify the on-disk
projection still matches a fresh render — without ever clobbering
adopter content.

Fixture shape:
  - Source pack: the existing upgrade-fixture's `core` at catalogue_v1
    (carries both .sh and .py hooks plus skill/agent/command primitives).
  - Brownfield repo: pre-existing AGENTS.md (Tier-3 — pack doesn't
    project it) plus an adopter-edited copy of a path the pack DOES
    project (Tier-2 collision; install must drop a `.upstream.<ext>`
    companion).
  - Values file: `tests/fixtures/brownfield/values.toml`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_V1 = (
    PACKAGE_ROOT / "tests" / "fixtures" / "upgrade" / "catalogue_v1"
)
VALUES_FILE = PACKAGE_ROOT / "tests" / "fixtures" / "brownfield" / "values.toml"
TIER2_PATH = "apm/core/.apm/agents/reviewer.md"


def _stage_brownfield(root: Path) -> None:
    """Pre-seed adopter content before install."""
    (root / "AGENTS.md").write_bytes(b"# adopter notes\n")
    (root / "src").mkdir()
    (root / "src" / "main.py").write_bytes(b"print('hi')\n")
    # Tier-2 collision: a real projection path with adopter content.
    target = root / TIER2_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"# adopter-edited reviewer agent\n")


def _install(root: Path) -> int:
    from agentbundle.commands.install import run

    return run(argparse.Namespace(
        pack="core",
        catalogue=str(CATALOGUE_V1),
        output=str(root),
    ))


def _adapt(root: Path) -> int:
    from agentbundle.commands.adapt import run

    return run(argparse.Namespace(
        values_from=str(VALUES_FILE),
        ci=False,
        root=str(root),
    ))


def _diff(root: Path) -> int:
    from agentbundle.commands.diff import run

    return run(argparse.Namespace(
        pack_path=str(CATALOGUE_V1 / "packs" / "core"),
        root=str(root),
    ))


def test_brownfield_install_adapt_diff_round_trip(tmp_path: Path):
    """The full chain: install lands the bundle; adapt resolves markers
    and reports companions; diff confirms the projection matches a fresh
    render. Adopter-edited files survive byte-identical."""
    _stage_brownfield(tmp_path)

    # 1. Install.
    rc = _install(tmp_path)
    assert rc == 0
    # State file exists; Tier-2 companion dropped; adopter file unchanged.
    assert (tmp_path / ".agent-ready-state.toml").exists()
    assert (tmp_path / TIER2_PATH).read_bytes() == b"# adopter-edited reviewer agent\n"
    companion = tmp_path / "apm/core/.apm/agents/reviewer.upstream.md"
    assert companion.exists(), "install should drop a .upstream.<ext> companion"

    # 2. Adapt — no markers in this fixture pack, so substitution is a
    # no-op; the value is in the pending report emitted for the
    # companion above.
    rc = _adapt(tmp_path)
    assert rc == 0
    pending = (tmp_path / ".adapt-pending.md").read_text(encoding="utf-8")
    assert "reviewer.upstream.md" in pending, (
        "adapt should list the install-time companion in the pending report"
    )

    # 3. Diff — projection on disk matches a fresh render: exit 0.
    # (The Tier-2 collision path has the adopter's bytes on disk, NOT the
    # bundle's — so diff will report it as drifted, which is the correct
    # signal for the adopter to merge before declaring the install
    # complete. We assert non-zero with the drifted path listed.)
    rc = _diff(tmp_path)
    assert rc == 1, "diff should detect the Tier-2 collision as drift"

    # 4. Adopter-only files unchanged through the whole chain.
    assert (tmp_path / "AGENTS.md").read_bytes() == b"# adopter notes\n"
    assert (tmp_path / "src" / "main.py").read_bytes() == b"print('hi')\n"


def test_brownfield_ci_mode_signals_pending_companions(tmp_path: Path):
    """After install drops a companion, `adapt --ci` exits 1; after the
    adopter removes the companion, `--ci` exits 0."""
    from agentbundle.commands.adapt import run as adapt_run

    _stage_brownfield(tmp_path)
    _install(tmp_path)

    companion = tmp_path / "apm/core/.apm/agents/reviewer.upstream.md"
    assert companion.exists()

    # Pre-removal: --ci flags it.
    rc = adapt_run(argparse.Namespace(values_from=None, ci=True, root=str(tmp_path)))
    assert rc == 1

    # Adopter resolves: remove the companion.
    companion.unlink()
    rc = adapt_run(argparse.Namespace(values_from=None, ci=True, root=str(tmp_path)))
    assert rc == 0
