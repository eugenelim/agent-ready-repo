"""The install walk must never read *through* a symlink.

`_collect_tree` walks a rendered projection and returns every file's bytes for
the caller to write into an adopter's tree. It used `Path.is_file()`, which
follows links, then `read_bytes()` — so a symlink in the projection had its
**target's** contents collected and written under the link's own relpath. The
relpath is innocent; only the link is not, which is why every path-confinement
check upstream passed it.

**This is the read half, and deliberately only that half.** Projection keeps its
symlinks. `docs/specs/codex-native-skills/spec.md:92` states the invariant
plainly — "the symlink-pass-through is the path-traversal-safety invariant;
never resolve a symlink to its target at projection time" — and
`build/main.py`'s `.apm` and `seeds` copytrees pass `symlinks=True` for the same
reason. Preserving a link is safe *because* nothing reads the target there.

Two layers, each correct alone; the composition was the defect. So it is closed
where the bytes are actually read, not where the link is copied.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle.render import _collect_tree


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_collect_tree_never_reads_through_a_symlink(tmp_path) -> None:
    root = tmp_path / "rendered"
    (root / "skills").mkdir(parents=True)
    (root / "skills" / "honest.md").write_text("honest\n", encoding="utf-8")

    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET\n", encoding="utf-8")
    # An absolute escape, preserved into the projection by design.
    (root / "skills" / "leak.md").symlink_to(secret)

    collected = _collect_tree(root)

    assert "skills/honest.md" in collected, "regular files must still be collected"
    assert "skills/leak.md" not in collected, (
        "a symlinked entry must not be collected — is_file() follows the link, so "
        "collecting it materialises the target's bytes on an adopter's disk"
    )
    assert all(b"SECRET" not in v for v in collected.values())


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_relative_traversal_is_skipped_too(tmp_path) -> None:
    """The shape an absolute-only filter would miss.

    `../../../secret.txt` escapes exactly as well as `/etc/passwd` and carries no
    leading slash. Skipping at the read covers every shape at once, which is the
    argument for fixing it here rather than in each projection filter.
    """
    root = tmp_path / "rendered"
    (root / "a" / "b").mkdir(parents=True)
    (tmp_path / "secret.txt").write_text("SECRET\n", encoding="utf-8")
    (root / "a" / "b" / "rel.md").symlink_to(Path("..") / ".." / ".." / "secret.txt")

    collected = _collect_tree(root)

    assert collected == {}, f"expected nothing collectable, got {sorted(collected)}"


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_a_symlinked_directory_contributes_nothing(tmp_path) -> None:
    """A linked *directory* is the same primitive with more reach.

    `rglob` descends into it, so without the skip every file beneath the target
    is collected under an in-tree relpath.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("SECRET\n", encoding="utf-8")

    root = tmp_path / "rendered"
    root.mkdir()
    (root / "keep.md").write_text("keep\n", encoding="utf-8")
    (root / "linked").symlink_to(outside, target_is_directory=True)

    collected = _collect_tree(root)

    assert "keep.md" in collected
    assert all("linked" not in k for k in collected), sorted(collected)
    assert all(b"SECRET" not in v for v in collected.values())
