"""Unit tests for _classify_seeds — TDD red stubs for projection-dry-run-governance-seeds."""

import os
import tempfile
from pathlib import Path

import pytest


def _mk_seeds_dir(tmp_path: Path, files: dict) -> Path:
    """Create a seeds_dir with the given {relpath: bytes|None} mapping.

    None means create a symlink (target: /dev/null).
    """
    seeds = tmp_path / "seeds"
    seeds.mkdir()
    for relpath, content in files.items():
        dest = seeds / relpath
        dest.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            dest.symlink_to("/dev/null")
        else:
            dest.write_bytes(content)
    return seeds


def test_classify_seeds_absent(tmp_path):
    """Seed absent on disk → action == 'wrote'."""
    from agentbundle.commands._common import _classify_seeds

    seeds = _mk_seeds_dir(tmp_path, {"AGENTS.md": b"content"})
    root = tmp_path / "root"
    root.mkdir()

    results = _classify_seeds(seeds, root)
    assert len(results) == 1
    assert results[0].relpath == "AGENTS.md"
    assert results[0].action == "wrote"
    assert results[0].companion_relpath is None


def test_classify_seeds_identical(tmp_path):
    """Seed byte-identical on disk → action == 'skipped'."""
    from agentbundle.commands._common import _classify_seeds

    content = b"# identical"
    seeds = _mk_seeds_dir(tmp_path, {"docs/CHARTER.md": content})
    root = tmp_path / "root"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "CHARTER.md").write_bytes(content)

    results = _classify_seeds(seeds, root)
    assert len(results) == 1
    assert results[0].action == "skipped"
    assert results[0].companion_relpath is None


def test_classify_seeds_differs(tmp_path):
    """Seed differs on disk → action == 'companion' with correct companion_relpath."""
    from agentbundle.commands._common import _classify_seeds

    seeds = _mk_seeds_dir(tmp_path, {"docs/CONVENTIONS.md": b"new content"})
    root = tmp_path / "root"
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "CONVENTIONS.md").write_bytes(b"old content")

    results = _classify_seeds(seeds, root)
    assert len(results) == 1
    assert results[0].action == "companion"
    assert results[0].companion_relpath == "docs/CONVENTIONS.upstream.md"


def test_classify_seeds_agents_md_composition(tmp_path):
    """AGENTS.md classified against composed bytes (body+footer), not raw seed bytes."""
    from agentbundle.commands._common import _classify_seeds

    body = b"# Body\n"
    footer = b"# Footer\n"
    composed = body + footer

    seeds = _mk_seeds_dir(
        tmp_path,
        {"AGENTS.md": body, "_agents-footer.md": footer},
    )
    root = tmp_path / "root"
    root.mkdir()
    # Disk has composed bytes → should be skipped
    (root / "AGENTS.md").write_bytes(composed)

    results = _classify_seeds(seeds, root)
    # _agents-footer.md excluded; AGENTS.md compared against composed bytes
    agents = [r for r in results if r.relpath == "AGENTS.md"]
    assert len(agents) == 1
    assert agents[0].action == "skipped"


def test_classify_seeds_footer_excluded(tmp_path):
    """_agents-footer.md is excluded from the returned list."""
    from agentbundle.commands._common import _classify_seeds

    seeds = _mk_seeds_dir(
        tmp_path,
        {"AGENTS.md": b"body\n", "_agents-footer.md": b"footer\n"},
    )
    root = tmp_path / "root"
    root.mkdir()

    results = _classify_seeds(seeds, root)
    relpaths = [r.relpath for r in results]
    assert "_agents-footer.md" not in relpaths


def test_classify_seeds_symlink_file_skipped(tmp_path):
    """A symlinked seed file is not returned."""
    from agentbundle.commands._common import _classify_seeds

    seeds = tmp_path / "seeds"
    seeds.mkdir()
    (seeds / "real.md").write_bytes(b"real")
    (seeds / "link.md").symlink_to("/dev/null")

    root = tmp_path / "root"
    root.mkdir()

    results = _classify_seeds(seeds, root)
    relpaths = [r.relpath for r in results]
    assert "link.md" not in relpaths
    assert "real.md" in relpaths


def test_classify_seeds_symlink_dir_skipped(tmp_path):
    """A symlinked subdirectory inside seeds_dir is not descended into."""
    from agentbundle.commands._common import _classify_seeds

    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "secret.md").write_bytes(b"secret")

    seeds = tmp_path / "seeds"
    seeds.mkdir()
    (seeds / "normal.md").write_bytes(b"ok")
    (seeds / "linked_sub").symlink_to(real_dir)

    root = tmp_path / "root"
    root.mkdir()

    results = _classify_seeds(seeds, root)
    relpaths = [r.relpath for r in results]
    assert "linked_sub/secret.md" not in relpaths
    assert "normal.md" in relpaths


def test_classify_seeds_no_write_invariant(tmp_path):
    """Calling _classify_seeds writes nothing under root."""
    from agentbundle.commands._common import _classify_seeds

    seeds = _mk_seeds_dir(
        tmp_path,
        {"AGENTS.md": b"content", "docs/CHARTER.md": b"charter"},
    )
    root = tmp_path / "root"
    root.mkdir()

    before = set(str(p) for p in root.rglob("*"))
    _classify_seeds(seeds, root)
    after = set(str(p) for p in root.rglob("*"))

    assert before == after, f"_classify_seeds wrote files: {after - before}"
