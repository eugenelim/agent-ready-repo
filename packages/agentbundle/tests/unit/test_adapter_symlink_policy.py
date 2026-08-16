"""One symlink policy, shared by every direct-directory adapter.

Six adapters project a skill directory with `shutil.copytree`, and each used to
carry its own ignore callback. Six copies of one rule did what six copies do:
they drifted into two policies — `cursor`, `copilot`, `gemini` and `kiro`
dropping every symlink, `claude_code` and `codex` dropping only absolute
targets and preserving relative ones.

Pass-through is the surviving policy, and it is the one the repo already
specified. `docs/specs/codex-native-skills/spec.md`: *"the symlink-pass-through
is the path-traversal-safety invariant; never resolve a symlink to its target at
projection time."* Resolving is what materialises a target's bytes into the
output. Preserving the link does not — and `render._collect_tree` refuses to
read through a link, so a preserved link cannot become a file on an adopter's
disk by that route either.

What the existing suites already cover is the ABSOLUTE case, because every one
of their fixtures uses `/etc/passwd` or a resolved tmp path. This file covers
what those cannot see: that a *relative* link survives as a link, uniformly,
and that no adapter has grown a seventh private policy.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from agentbundle.build.projections.direct_directory import ignore_absolute_symlinks

_ADAPTERS = ("cursor", "copilot", "gemini", "kiro", "claude_code", "codex")


def _tree(root: Path) -> Path:
    skill = root / "skill"
    (skill / "nested").mkdir(parents=True)
    (skill / "real.md").write_text("real\n", encoding="utf-8")
    (skill / "nested" / "keep.md").write_text("keep\n", encoding="utf-8")

    outside = root / "outside-secret.txt"
    outside.write_text("SECRET\n", encoding="utf-8")

    (skill / "abs.md").symlink_to(outside)                       # absolute — dropped
    (skill / "intra.md").symlink_to(Path("real.md"))             # relative in-tree — kept
    (skill / "up.md").symlink_to(Path("..") / "outside-secret.txt")  # relative up — kept
    return skill


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_absolute_links_are_dropped_and_relative_ones_preserved(tmp_path) -> None:
    skill = _tree(tmp_path)
    dest = tmp_path / "out"
    shutil.copytree(skill, dest, symlinks=True, ignore=ignore_absolute_symlinks)

    assert not (dest / "abs.md").exists(), "an absolute-target symlink must be dropped"
    assert (dest / "intra.md").is_symlink(), "a relative symlink must survive AS a link"
    assert (dest / "up.md").is_symlink()
    # Preserved, never resolved — that distinction is the invariant. If these
    # were resolved, the out-of-tree bytes would be sitting in the projection.
    assert (dest / "up.md").readlink() == Path("..") / "outside-secret.txt"
    assert (dest / "real.md").read_text() == "real\n"
    assert (dest / "nested" / "keep.md").read_text() == "keep\n"


@pytest.mark.skipif(not hasattr(Path, "symlink_to"), reason="no symlink support")
def test_no_regular_file_carries_out_of_tree_bytes(tmp_path) -> None:
    """Preserving a link must not become copying its target.

    The failure this guards is the whole reason the invariant exists: a
    `copytree` without `symlinks=True` dereferences, and the secret lands as a
    regular file under an innocent name.
    """
    skill = _tree(tmp_path)
    dest = tmp_path / "out"
    shutil.copytree(skill, dest, symlinks=True, ignore=ignore_absolute_symlinks)

    for path in dest.rglob("*"):
        if path.is_file() and not path.is_symlink():
            assert "SECRET" not in path.read_text(encoding="utf-8", errors="replace"), path


def test_pycache_is_still_excluded(tmp_path) -> None:
    """Unrelated to symlinks and load-bearing: `.pyc` files embed absolute
    source paths, so they can never be byte-identical across machines."""
    (tmp_path / "__pycache__").mkdir()
    assert "__pycache__" in ignore_absolute_symlinks(str(tmp_path), ["__pycache__", "a.py"])


def test_every_adapter_uses_the_shared_policy() -> None:
    """No adapter may keep a private symlink policy.

    Six private copies is how the two policies diverged; this fails if a seventh
    appears, or if one stops passing `symlinks=True` (which would silently turn
    preservation back into resolution).
    """
    import agentbundle.build.adapters as adapters_pkg

    adapters_dir = Path(adapters_pkg.__file__).parent
    offenders: list[str] = []
    for name in _ADAPTERS:
        src = (adapters_dir / f"{name}.py").read_text(encoding="utf-8")
        if "def _ignore_symlinks" in src or "def _ignore_absolute_symlinks" in src:
            offenders.append(f"{name}: defines a private symlink policy")
        # Check the CALL, not the file. A whole-file `"symlinks=True" in src`
        # passes while the direct-directory copytree has lost it, because these
        # modules contain other copytree calls — verified by mutation: dropping
        # it from one call left a file-level check green.
        for call in re.finditer(r"shutil\.copytree\((?:[^()]|\([^()]*\))*\)", src):
            text = call.group(0)
            if "ignore_absolute_symlinks" not in text:
                continue  # a different copytree, not the direct-directory one
            if "symlinks=True" not in text:
                offenders.append(
                    f"{name}: direct-directory copytree without symlinks=True — "
                    "it would resolve links instead of preserving them"
                )
        if "ignore=ignore_absolute_symlinks" not in src:
            offenders.append(f"{name}: does not use the shared policy")
    assert not offenders, offenders


def test_the_policy_is_defined_exactly_once() -> None:
    from agentbundle.build.projections import direct_directory

    src = Path(direct_directory.__file__).read_text(encoding="utf-8")
    assert src.count("def ignore_absolute_symlinks") == 1
