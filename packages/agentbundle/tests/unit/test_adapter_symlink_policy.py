"""Every direct-directory adapter drops every symlink, by one shared rule.

Six adapters project a skill directory with `shutil.copytree`, and each used to
carry its own ignore callback. They had drifted into two policies:

* `cursor`, `copilot`, `gemini`, `kiro` — drop **every** symlink;
* `claude_code`, `codex` — drop only symlinks with **absolute** targets,
  preserving relative ones as "intra-skill cross-references".

The permissive rule had a hole its own docstring papered over: "absolute
symlinks always escape the tree" is true and incomplete, because a relative
symlink escapes just as well — `../../../../etc/passwd` needs no leading slash.
Preserved as a symlink into the projection, it is dereferenced later by the
install walker's `read_bytes()`, embedding out-of-tree content in an adopter's
tree.

The capability that rule protected is unusable: no symlink exists under
`packs/`, and `lint_packs.py` rejects any pack shipping one, so the only way a
symlink reaches an adapter is an untrusted catalogue — exactly the case where
preserving it is the hazard.

The relative-traversal case below is the regression that matters: it passed
`_ignore_absolute_symlinks` unfiltered.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from agentbundle.build.projections.direct_directory import ignore_symlinks


def _tree_with_symlinks(root: Path) -> Path:
    """A skill dir carrying one honest file and four symlink shapes."""
    skill = root / "skill"
    (skill / "nested").mkdir(parents=True)
    (skill / "real.md").write_text("real\n", encoding="utf-8")
    (skill / "nested" / "keep.md").write_text("keep\n", encoding="utf-8")

    outside = root / "outside-secret.txt"
    outside.write_text("SECRET\n", encoding="utf-8")

    # absolute — the only shape the permissive rule caught
    (skill / "abs.md").symlink_to(outside)
    # relative traversal — escapes just as well, and was NOT caught
    (skill / "rel.md").symlink_to(Path("..") / "outside-secret.txt")
    # nested relative traversal, below the caller's top-level is_symlink() check
    (skill / "nested" / "rel.md").symlink_to(Path("..") / ".." / "outside-secret.txt")
    # in-tree relative — the "intra-skill cross-reference" the old rule kept
    (skill / "intra.md").symlink_to(Path("real.md"))
    return skill


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_copytree_with_the_shared_callback_reproduces_no_symlink(tmp_path) -> None:
    skill = _tree_with_symlinks(tmp_path)
    dest = tmp_path / "out"

    shutil.copytree(skill, dest, ignore=ignore_symlinks)

    survivors = [p for p in dest.rglob("*") if p.is_symlink()]
    assert not survivors, f"symlinks reproduced into the projection: {survivors}"

    # The honest files still land — the filter must not be a blanket refusal.
    assert (dest / "real.md").read_text() == "real\n"
    assert (dest / "nested" / "keep.md").read_text() == "keep\n"

    # And no copy carries the out-of-tree content, by link or by value.
    for path in dest.rglob("*"):
        if path.is_file():
            assert "SECRET" not in path.read_text(encoding="utf-8", errors="replace"), path


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_relative_traversal_is_dropped_not_just_absolute(tmp_path) -> None:
    """The specific regression: a relative escape used to survive.

    Named separately from the sweep above so a failure says *which* shape came
    back, rather than only that something did.
    """
    skill = _tree_with_symlinks(tmp_path)
    ignored = ignore_symlinks(str(skill), [p.name for p in skill.iterdir()])
    assert "rel.md" in ignored, "a relative traversal symlink must be dropped"
    assert "abs.md" in ignored, "an absolute symlink must be dropped"
    assert "intra.md" in ignored, (
        "an in-tree relative symlink is dropped too — packs ship none, "
        "lint_packs rejects them, and preserving the shape is what left the hole"
    )
    assert "real.md" not in ignored, "regular files must survive"


def test_pycache_is_still_excluded(tmp_path) -> None:
    """Unrelated to symlinks, and load-bearing: .pyc files embed absolute
    source paths, so they can never be byte-identical across machines."""
    (tmp_path / "__pycache__").mkdir()
    assert "__pycache__" in ignore_symlinks(str(tmp_path), ["__pycache__", "a.py"])


def test_every_direct_directory_adapter_uses_the_shared_callback() -> None:
    """No adapter may keep a private symlink policy.

    Six copies of one security rule is how the two policies diverged in the
    first place; this fails if a seventh appears.
    """
    import agentbundle.build.adapters as adapters_pkg

    adapters_dir = Path(adapters_pkg.__file__).parent
    offenders: list[str] = []
    for path in sorted(adapters_dir.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        if "shutil.copytree(" not in src:
            continue
        if "ignore=ignore_symlinks" not in src:
            offenders.append(f"{path.name}: copytree without the shared callback")
        if "_ignore_absolute_symlinks" in src or "def _ignore_symlinks" in src:
            offenders.append(f"{path.name}: still defines a private symlink policy")
    assert not offenders, offenders


# ---------------------------------------------------------------------------
# The install-side walk
#
# The adapter filter above stops a symlink entering a direct-directory
# projection. It does not cover the build's `.apm` / `seeds` copytrees, which
# pass symlinks=True deliberately — preserving a link rather than dereferencing
# it is SAFE at that layer, because nothing reads the target there. `_collect_tree`
# then read it. The composition was the hole, so it is closed at the read.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_collect_tree_never_reads_through_a_symlink(tmp_path) -> None:
    from agentbundle.render import _collect_tree

    root = tmp_path / "rendered"
    (root / "skills").mkdir(parents=True)
    (root / "skills" / "honest.md").write_text("honest\n", encoding="utf-8")

    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET\n", encoding="utf-8")
    # The relpath is innocent; only the link is not. That is what made this
    # bypass every path check upstream.
    (root / "skills" / "leak.md").symlink_to(secret)

    collected = _collect_tree(root)

    assert "skills/honest.md" in collected
    assert "skills/leak.md" not in collected, (
        "a symlinked entry must not be collected — is_file() follows the link, "
        "so collecting it would materialise the target's bytes on an adopter's disk"
    )
    assert all(b"SECRET" not in v for v in collected.values())
