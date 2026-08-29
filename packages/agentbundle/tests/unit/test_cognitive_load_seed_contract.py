"""Package-scope contract for the cognitive-load seed lookups.

Shipped: `gate-export-boundary` runs this suite inside the agentbundle sdist,
which has no `packs/`, no `docs/`, and no checkout. Every assertion here must
therefore hold against the package alone. The repository-scope half — the seed
bodies, the generated projections, and the per-pack eval inventory — lives in
`tests/roster/test_cognitive_load_repository_contract.py`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling import file_safety
from agentbundle.catalogue_tooling import lint as catalogue_lint

HOSTS = ("claude", "codex", "gemini")


def test_seed_linter_rejects_nested_docs_lookup_path(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "AGENTS.md"
    docs.parent.mkdir(parents=True)
    docs.write_text("Read `.agents/rules/extra.md`.\n", encoding="utf-8")

    assert catalogue_lint._seeds_check_file(docs, tmp_path) == [
        f"{docs}: agent-rules-routing-topic-invalid"
    ]


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("case", ("missing", "symlink", "hardlink", "oversized", "directory", "escape"))
def test_agent_directed_lookup_refuses_unsafe_targets(
    tmp_path: Path, host: str, case: str
) -> None:
    del host  # Every adapter uses the same tool-neutral lookup contract.
    root = tmp_path / "repo"
    root.mkdir()
    target = root / "rule.md"
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    if case == "missing":
        pass
    elif case == "symlink":
        try:
            target.symlink_to(outside)
        except OSError:
            pytest.skip("symlinks unavailable")
    elif case == "hardlink":
        target.write_text("rule\n", encoding="utf-8")
        try:
            os.link(target, root / "second.md")
        except OSError:
            pytest.skip("hard links unavailable")
    elif case == "oversized":
        target.write_bytes(b"x" * 65)
    elif case == "directory":
        target.mkdir()
    elif case == "escape":
        target = outside

    with pytest.raises(file_safety.UnsafeContentError):
        file_safety.read_confined_regular_file(root, target, max_bytes=64)


@pytest.mark.parametrize("host", HOSTS)
def test_agent_directed_lookup_refuses_reparse_like_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    del host
    target = tmp_path / "rule.md"
    target.write_text("rule\n", encoding="utf-8")
    target_stat = target.stat()
    monkeypatch.setattr(
        file_safety,
        "_is_reparse_point",
        lambda inspected: (
            inspected.st_dev == target_stat.st_dev
            and inspected.st_ino == target_stat.st_ino
        ),
    )
    with pytest.raises(file_safety.UnsafeContentError, match="reparse"):
        file_safety.read_confined_regular_file(tmp_path, target, max_bytes=64)


@pytest.mark.parametrize("host", HOSTS)
def test_agent_directed_lookup_refuses_identity_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str
) -> None:
    del host
    target = tmp_path / "rule.md"
    replacement = tmp_path / "replacement.md"
    target.write_text("first\n", encoding="utf-8")
    replacement.write_text("second\n", encoding="utf-8")
    real_open = file_safety.os.open
    real_stat = file_safety.os.stat
    leaf_was_statted = False

    def observe_stat(
        path: str | os.PathLike[str],
        *,
        dir_fd: int | None = None,
        follow_symlinks: bool = True,
    ) -> os.stat_result:
        nonlocal leaf_was_statted
        inspected = real_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)
        if dir_fd is not None and os.fspath(path) == target.name:
            leaf_was_statted = True
        return inspected

    def swap_then_open(
        path: str | os.PathLike[str],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        if dir_fd is not None and os.fspath(path) == target.name:
            assert leaf_was_statted
            replacement.replace(target)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(file_safety.os, "stat", observe_stat)
    monkeypatch.setattr(file_safety.os, "open", swap_then_open)
    monkeypatch.setattr(file_safety, "_supports_descriptor_walk", lambda: True)
    with pytest.raises(file_safety.UnsafeContentError, match="changed while opening"):
        file_safety.read_confined_regular_file(tmp_path, target, max_bytes=64)
    assert leaf_was_statted
