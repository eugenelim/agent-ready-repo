"""T4: Unit tests for `agentbundle scaffold`.

Test cases:
  1. Happy path — empty target directory: every seed is reproduced byte-identical.
  2. Tier-2 fast-path — pre-existing AGENTS.md with adopter content:
       - AGENTS.md stays byte-unchanged.
       - AGENTS.upstream.md is written with the seed content.
"""

from __future__ import annotations

import argparse
import os
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


def _composed_agents_md(pack_fixture: Path) -> bytes:
    """Return the expected delivered AGENTS.md bytes: body seed + footer fragment.

    Mirrors `commands._common._compose_agents_md_bytes`; the footer fragment
    `_agents-footer.md` is folded in, not delivered standalone.
    """
    seeds = pack_fixture / "seeds"
    body = (seeds / "AGENTS.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    if body and not body.endswith("\n"):
        body += "\n"
    footer_path = seeds / "_agents-footer.md"
    if not footer_path.exists():
        return (seeds / "AGENTS.md").read_bytes()
    footer = footer_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if footer and not footer.endswith("\n"):
        footer += "\n"
    return (body + footer).encode("utf-8")


def _expected_delivered(pack_fixture: Path) -> dict[str, bytes]:
    """Return {relpath: bytes} for the seeds `scaffold` should deliver.

    Composition fragments (names starting with `_`) are *not* delivered
    standalone; `AGENTS.md` is delivered composed with its footer.
    """
    seeds = pack_fixture / "seeds"
    result: dict[str, bytes] = {}
    for f in seeds.rglob("*"):
        if not f.is_file() or f.name.startswith("_"):
            continue
        relpath = f.relative_to(seeds).as_posix()
        result[relpath] = _composed_agents_md(pack_fixture) if relpath == "AGENTS.md" else f.read_bytes()
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

    expected = _expected_delivered(FIXTURES_DIR)
    assert expected, "fixture pack must have at least one delivered seed file"

    for relpath, content in expected.items():
        on_disk = output / relpath
        assert on_disk.exists(), f"seed {relpath!r} was not written to output"
        assert on_disk.read_bytes() == content, (
            f"seed {relpath!r} content mismatch; expected byte-identical copy"
        )

    # Composition fragment is folded into AGENTS.md, not delivered standalone.
    assert not (output / "_agents-footer.md").exists(), (
        "_agents-footer.md is a composition fragment and must not be delivered standalone"
    )
    footer_line = (FIXTURES_DIR / "seeds" / "_agents-footer.md").read_bytes().rstrip()
    assert footer_line in (output / "AGENTS.md").read_bytes(), (
        "delivered AGENTS.md must contain the footer fragment content"
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

    # The companion carries the *composed* AGENTS.md (body + footer), the bytes
    # delivery would otherwise have written.
    assert upstream.read_bytes() == _composed_agents_md(FIXTURES_DIR), (
        "AGENTS.upstream.md must contain the composed seed content"
    )


def test_no_footer_agents_md_delivered_verbatim(tmp_path):
    """A seed-bearing pack with no _agents-footer.md delivers AGENTS.md verbatim."""
    packs_dir = tmp_path / "packs"
    seeds = packs_dir / "no-footer" / "seeds"
    seeds.mkdir(parents=True)
    body = b"# Body only, no footer\n"
    (seeds / "AGENTS.md").write_bytes(body)

    output = tmp_path / "out"
    output.mkdir()

    exit_code = run(_make_args(packs_dir, output, pack="no-footer"))

    assert exit_code == 0
    assert (output / "AGENTS.md").read_bytes() == body, (
        "footer-less pack must deliver AGENTS.md byte-for-byte unchanged"
    )


def _symlink_or_skip(src, dst) -> None:
    """Create a symlink dst → src, or skip the test if the OS refuses
    (Windows without privilege)."""
    try:
        os.symlink(src, dst)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unsupported on this platform: {exc}")


def test_symlinked_seed_file_is_not_delivered(tmp_path):
    """Defence-in-depth: a pack-shipped symlinked seed must not be read through
    and delivered (it could point at a host secret)."""
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP SECRET HOST FILE\n", encoding="utf-8")

    packs_dir = tmp_path / "packs"
    seeds = packs_dir / "evil" / "seeds"
    seeds.mkdir(parents=True)
    (seeds / "AGENTS.md").write_text("# ok\n", encoding="utf-8")
    _symlink_or_skip(secret, seeds / "leak.md")

    output = tmp_path / "out"
    output.mkdir()
    assert run(_make_args(packs_dir, output, pack="evil")) == 0
    assert (output / "AGENTS.md").exists(), "the real seed should still be delivered"
    assert not (output / "leak.md").exists(), "a symlinked seed must not be delivered"


def test_symlinked_seed_directory_is_not_traversed(tmp_path):
    """A symlinked seed *directory* must not be traversed — closes the
    Python 3.11/3.12 rglob-recurses-into-symlinks gap (os.walk followlinks=False)."""
    external = tmp_path / "external"
    external.mkdir()
    (external / "secret.txt").write_text("HOST SECRET\n", encoding="utf-8")

    packs_dir = tmp_path / "packs"
    seeds = packs_dir / "evil" / "seeds"
    seeds.mkdir(parents=True)
    (seeds / "AGENTS.md").write_text("# ok\n", encoding="utf-8")
    _symlink_or_skip(external, seeds / "evildir")

    output = tmp_path / "out"
    output.mkdir()
    assert run(_make_args(packs_dir, output, pack="evil")) == 0
    assert (output / "AGENTS.md").exists()
    assert not (output / "evildir" / "secret.txt").exists(), (
        "contents of a symlinked seed directory must not be delivered"
    )
    assert not (output / "evildir").exists(), "the symlinked seed dir must not be recreated"


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

    seed_content = _composed_agents_md(FIXTURES_DIR)
    agents_md = output / "AGENTS.md"
    agents_md.write_bytes(seed_content)

    exit_code = run(_make_args(packs_dir, output))

    assert exit_code == 0
    # Upstream companion must NOT have been written.
    assert not (output / "AGENTS.upstream.md").exists(), (
        "no companion should be created when file already matches the seed"
    )
    # Original must still be byte-identical to the composed seed.
    assert agents_md.read_bytes() == seed_content


def test_scaffold_refuses_path_jail_escape(tmp_path, monkeypatch):
    """A malicious seed relpath that would escape --output must be refused
    with exit 1 and a one-line stderr — not propagate PathJailError uncaught.
    (Blocker 2 from quality-engineer review.)
    """
    from agentbundle.commands import scaffold
    from agentbundle import safety

    # Build a fixture pack with an empty seeds/ dir, then monkey-patch the
    # walk to yield a malicious relpath that resolves outside --output.
    packs_dir = tmp_path / "packs"
    pack = packs_dir / "evil"
    (pack / "seeds").mkdir(parents=True)
    (pack / "seeds" / "ok.md").write_bytes(b"ok\n")

    output = tmp_path / "out"
    output.mkdir()

    # Force write_jailed to raise as if a malicious projection rule had
    # resolved outside the root.
    def _refuse(root, relpath, content):
        raise safety.PathJailError("refusing to write outside repo root: /etc")
    monkeypatch.setattr(safety, "write_jailed", _refuse)

    args = argparse.Namespace(pack="evil", packs_dir=str(packs_dir), output=str(output))
    rc = scaffold.run(args)
    assert rc == 1


def test_init_state_refuses_path_jail_escape(tmp_path, monkeypatch):
    """init-state must catch PathJailError and exit 1 with stderr (Blocker 2)."""
    from agentbundle.commands import init_state
    from agentbundle import safety

    packs_dir = tmp_path / "packs"
    pack = packs_dir / "core"
    (pack).mkdir(parents=True)
    (pack / "pack.toml").write_text('[pack]\nname = "core"\nversion = "0.1"\n', encoding="utf-8")

    def _refuse(root, relpath, content):
        raise safety.PathJailError("refusing to write outside repo root: /etc")
    monkeypatch.setattr(safety, "write_jailed", _refuse)

    args = argparse.Namespace(pack="core", packs_dir=str(packs_dir), root=str(tmp_path))
    rc = init_state.run(args)
    assert rc == 1
