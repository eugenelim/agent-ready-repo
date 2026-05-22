"""T4: Unit tests for `agentbundle scaffold`.

Test cases:
  1. Happy path — empty target directory: every seed is reproduced byte-identical.
  2. Tier-2 fast-path — pre-existing AGENTS.md with adopter content:
       - AGENTS.md stays byte-unchanged.
       - AGENTS.upstream.md is written with the seed content.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from agentbundle.commands.scaffold import run

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "scaffold" / "test-pack"


def _make_args(packs_dir: Path, output: Path, pack: str = "test-pack") -> argparse.Namespace:
    """Build a minimal Namespace matching the scaffold subparser's shape."""
    return argparse.Namespace(
        pack=pack,
        packs_dir=str(packs_dir),
        output=str(output),
    )


# ---------------------------------------------------------------------------
# Helper: collect the expected seed tree from the fixture
# ---------------------------------------------------------------------------


def _seed_contents(pack_fixture: Path) -> dict[str, bytes]:
    """Return {relpath: bytes} for every file under pack_fixture/seeds/."""
    seeds = pack_fixture / "seeds"
    result: dict[str, bytes] = {}
    for f in seeds.rglob("*"):
        if f.is_file():
            relpath = f.relative_to(seeds).as_posix()
            result[relpath] = f.read_bytes()
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_happy_path_empty_output(tmp_path):
    """Empty target directory: every seed is written byte-identical."""
    packs_dir = FIXTURES_DIR.parent  # parent of 'test-pack'
    output = tmp_path / "out"
    output.mkdir()

    exit_code = run(_make_args(packs_dir, output))

    assert exit_code == 0, "scaffold should return 0 on success"

    expected = _seed_contents(FIXTURES_DIR)
    assert expected, "fixture pack must have at least one seed file"

    for relpath, content in expected.items():
        on_disk = output / relpath
        assert on_disk.exists(), f"seed {relpath!r} was not written to output"
        assert on_disk.read_bytes() == content, (
            f"seed {relpath!r} content mismatch; expected byte-identical copy"
        )


def test_tier2_fastpath_existing_adopter_content(tmp_path):
    """Pre-existing AGENTS.md with adopter content triggers Tier-2 fast-path.

    After scaffold:
      - AGENTS.md bytes are unchanged (original preserved).
      - AGENTS.upstream.md contains the seed content.
    """
    packs_dir = FIXTURES_DIR.parent
    output = tmp_path / "out"
    output.mkdir()

    adopter_content = b"# This is my custom AGENTS.md\n"
    agents_md = output / "AGENTS.md"
    agents_md.write_bytes(adopter_content)

    exit_code = run(_make_args(packs_dir, output))

    assert exit_code == 0

    # Original must be byte-unchanged.
    assert agents_md.read_bytes() == adopter_content, (
        "scaffold must not overwrite an existing file whose content differs from the seed"
    )

    # Companion must contain the seed content.
    upstream = output / "AGENTS.upstream.md"
    assert upstream.exists(), "AGENTS.upstream.md companion was not created"

    seed_content = (FIXTURES_DIR / "seeds" / "AGENTS.md").read_bytes()
    assert upstream.read_bytes() == seed_content, (
        "AGENTS.upstream.md must contain the seed content verbatim"
    )


def test_no_seeds_dir_returns_nonzero(tmp_path):
    """A pack with no seeds/ sub-directory causes scaffold to exit non-zero."""
    # Create a pack directory without a seeds/ sub-directory.
    packs_dir = tmp_path / "packs"
    (packs_dir / "empty-pack").mkdir(parents=True)

    output = tmp_path / "out"
    output.mkdir()

    exit_code = run(_make_args(packs_dir, output, pack="empty-pack"))

    assert exit_code != 0, "scaffold must return non-zero when pack has no seeds/"


def test_up_to_date_seed_is_skipped(tmp_path):
    """If a file already matches the seed content exactly, it is left alone (no write)."""
    packs_dir = FIXTURES_DIR.parent
    output = tmp_path / "out"
    output.mkdir()

    seed_content = (FIXTURES_DIR / "seeds" / "AGENTS.md").read_bytes()
    agents_md = output / "AGENTS.md"
    agents_md.write_bytes(seed_content)

    mtime_before = agents_md.stat().st_mtime_ns

    exit_code = run(_make_args(packs_dir, output))

    assert exit_code == 0
    # Upstream companion must NOT have been written.
    assert not (output / "AGENTS.upstream.md").exists(), (
        "no companion should be created when file already matches the seed"
    )
    # Original must still be byte-identical to the seed.
    assert agents_md.read_bytes() == seed_content
