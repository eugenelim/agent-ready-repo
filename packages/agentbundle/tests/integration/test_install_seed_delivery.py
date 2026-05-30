"""Integration tests for CLI `install` seed delivery (spec core-install-seed-delivery).

`agentbundle install` must deliver the `core` pack's governance seeds into the
adopter repo (AC1), record each in `.agentbundle-state.toml` (AC2), compose
`AGENTS.md` from body+footer while not delivering `_agents-footer.md` standalone
(AC1b), and drop `*.upstream.<ext>` companions on adopter-edited collisions
(AC1 Tier-2) — never overwriting the adopter's file.

The catalogue is this repo's own clone (REPO_ROOT); the pack is the real
`packs/core/`, installed at repo scope via the per-IDE route (not the legacy
dist-tree producer).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CORE_SEEDS = REPO_ROOT / "packs" / "core" / "seeds"


def _install_core(target: Path) -> tuple[int, str, str]:
    from agentbundle.commands.install import run as install_run

    args = argparse.Namespace(
        pack="core",
        catalogue=str(REPO_ROOT),
        output=str(target),
        scope="repo",
        emit_install_routes=False,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install_run(args)
    return rc, out.getvalue(), err.getvalue()


def test_install_delivers_seeds(tmp_path):
    """AC1: a documented `install` lands the governance seeds in the repo."""
    target = tmp_path / "repo"
    target.mkdir()
    rc, _out, err = _install_core(target)
    assert rc == 0, f"install failed: {err}"
    for rel in (
        "AGENTS.md",
        "docs/CHARTER.md",
        "docs/CONVENTIONS.md",
        "docs/backlog.md",
        "docs/specs/README.md",
        "docs/architecture/overview.md",
    ):
        assert (target / rel).exists(), f"seed {rel!r} was not delivered (stderr: {err})"


def test_install_records_seeds_in_state(tmp_path):
    """AC2: each delivered seed is recorded in core's state `files` map."""
    target = tmp_path / "repo"
    target.mkdir()
    rc, _out, err = _install_core(target)
    assert rc == 0, err
    state = tomllib.loads((target / ".agentbundle-state.toml").read_text(encoding="utf-8"))
    files = state["pack"]["core"]["files"]
    for rel in ("AGENTS.md", "docs/CHARTER.md", "docs/CONVENTIONS.md"):
        assert rel in files, f"seed {rel!r} not recorded in state files map"
        # AC2: same {sha, from-pack-version} shape as primitives.
        assert files[rel]["sha"], f"seed {rel!r} state entry missing sha"
        assert files[rel]["from-pack-version"], (
            f"seed {rel!r} state entry missing from-pack-version"
        )


def test_install_composes_agents_md_and_skips_footer(tmp_path):
    """AC1b: AGENTS.md is composed body+footer; _agents-footer.md is not standalone."""
    target = tmp_path / "repo"
    target.mkdir()
    rc, _out, err = _install_core(target)
    assert rc == 0, err
    assert not (target / "_agents-footer.md").exists(), (
        "_agents-footer.md is a composition fragment — must not be delivered standalone"
    )
    footer = (CORE_SEEDS / "_agents-footer.md").read_bytes().rstrip()
    assert footer in (target / "AGENTS.md").read_bytes(), (
        "delivered AGENTS.md must contain the footer fragment content"
    )
    assert "_agents-footer.md" not in (
        tomllib.loads((target / ".agentbundle-state.toml").read_text(encoding="utf-8"))
        ["pack"]["core"]["files"]
    ), "the composition fragment must not be state-tracked as a standalone file"


def test_install_seed_collision_drops_companion(tmp_path):
    """AC1 Tier-2: an adopter-edited seed is left untouched and gets a companion."""
    target = tmp_path / "repo"
    target.mkdir()
    (target / "docs").mkdir()
    edited = b"# my own charter, do not touch\n"
    (target / "docs" / "CHARTER.md").write_bytes(edited)

    rc, _out, err = _install_core(target)
    assert rc == 0, err
    assert (target / "docs" / "CHARTER.md").read_bytes() == edited, (
        "install must not overwrite an adopter-edited seed"
    )
    assert (target / "docs" / "CHARTER.upstream.md").exists(), (
        "an adopter-edited seed collision must drop a .upstream companion"
    )


def test_install_gitignore_collision_drops_companion(tmp_path):
    """AC1 Tier-2: the highest-probability brownfield collision — repo-root .gitignore."""
    target = tmp_path / "repo"
    target.mkdir()
    existing = b"node_modules/\n.env\n"
    (target / ".gitignore").write_bytes(existing)

    rc, _out, err = _install_core(target)
    assert rc == 0, err
    assert (target / ".gitignore").read_bytes() == existing, (
        "install must not overwrite an adopter's existing .gitignore"
    )
    assert (target / ".gitignore.upstream").exists(), (
        ".gitignore collision must drop a .gitignore.upstream companion"
    )


def test_install_records_no_phantom_unresolved_markers(tmp_path):
    """AC10: a fresh core install records no phantom `unresolved-markers`.

    The only `<adapt:...>` token in core's projection is the inline-code doc
    example in adapt-to-project/SKILL.md; the marker scanner now ignores it.
    """
    target = tmp_path / "repo"
    target.mkdir()
    rc, _out, err = _install_core(target)
    assert rc == 0, err
    marker_file = target / ".adapt-install-marker.toml"
    assert marker_file.exists(), "install must write the adapt-install marker"
    data = tomllib.loads(marker_file.read_text(encoding="utf-8"))
    core_entries = [e for e in data.get("packs-installed", []) if e.get("name") == "core"]
    assert core_entries, "core entry missing from install marker"
    assert core_entries[0].get("unresolved-markers", []) == [], (
        f"fresh core install must record no phantom unresolved-markers, got "
        f"{core_entries[0].get('unresolved-markers')!r}"
    )


def test_install_identical_seed_skipped(tmp_path):
    """AC1 Tier-1: a pre-existing byte-identical seed is a clean no-op (no companion)."""
    target = tmp_path / "repo"
    target.mkdir()
    (target / "docs").mkdir()
    # docs/CHARTER.md is not composed, so the delivered bytes equal the raw seed.
    (target / "docs" / "CHARTER.md").write_bytes((CORE_SEEDS / "docs" / "CHARTER.md").read_bytes())

    rc, _out, err = _install_core(target)
    assert rc == 0, err
    assert not (target / "docs" / "CHARTER.upstream.md").exists(), (
        "no companion should be created when the seed already matches on disk"
    )
