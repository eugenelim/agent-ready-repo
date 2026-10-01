# STUB: AC-0007, AC-0008, AC-0009
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-old.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-old.md"
TOMBSTONE_DATE = date(2026, 9, 29)
HOSTILE_RESOLVE_PATHS = (
    "/outside/ABSOLUTE_HOSTILE.md",
    "docs/product/intents/FEAT-0002-hostile\nINJECTED.md",
)


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename_resolution", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


_SANDBOX_STAGE_REMOVALS: list[str] = []


def _sandbox_remove_empty_stage(parent_descriptor: int, name: str) -> None:
    """Replace only the sandbox-blocked final rmdir with an empty-dir proof."""
    descriptor = os.open(
        name,
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0),
        dir_fd=parent_descriptor,
    )
    try:
        assert os.listdir(descriptor) == []  # noqa: PTH208 - held no-follow fd
    finally:
        os.close(descriptor)
    _SANDBOX_STAGE_REMOVALS.append(name)


rename._remove_empty_stage = _sandbox_remove_empty_stage


def _tombstone(target: str) -> str:
    return (
        "# Tombstone: old\n\n"
        "- **Slug:** `old`\n"
        "- **Tombstone:** 2026-09-29\n"
        f"- **Reissued as:** {target}\n"
    )


def _commit(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.invalid"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test Runner"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _rename_fixture(root: Path) -> tuple[str, str]:
    old = "docs/product/intents/FEAT-0009-older.md"
    older = "docs/product/intents/FEAT-0008-oldest.md"
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Old\n\n"
        "- **Slug:** `old`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n",
        encoding="utf-8",
    )
    (root / old).write_text(_tombstone(SOURCE), encoding="utf-8")
    (root / older).write_text(_tombstone(SOURCE), encoding="utf-8")
    (root / "workspace.toml").write_text(
        "[backlog]\n"
        f'open = [{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "old", needs = []}]\n',
        encoding="utf-8",
    )
    _commit(root)
    return old, older


def test_ac_0007_missing_target_names_tombstone_and_target(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    path = tmp_path / old
    path.parent.mkdir(parents=True)
    path.write_text(_tombstone(target), encoding="utf-8")

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-target-missing"
    assert result.paths == (old, target)


def test_ac_0008_tombstone_target_names_both_tombstones(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    final = "docs/product/intents/CAP-0001-final.md"
    for relative, text in ((old, _tombstone(target)), (target, _tombstone(final))):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-target-is-tombstone"
    assert result.paths == (old, target)


def test_ac_0008_malformed_tombstone_target_is_not_a_live_successor(
    tmp_path: Path,
) -> None:
    """A target carrying `Tombstone:` is a tombstone even when its shape is invalid."""
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    malformed = "# Tombstone: new\n\n- **Slug:** `new`\n- **Tombstone:** 2026-09-29\n"
    for relative, text in ((old, _tombstone(target)), (target, malformed)):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    parsed = rename._tombstone.parse_tombstone(malformed)
    assert isinstance(parsed, str) and parsed != "not-tombstone"

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-target-is-tombstone"
    assert result.paths == (old, target)


def test_ac_0009_resolution_reads_only_the_target_preamble(tmp_path: Path) -> None:
    """Bytes after the first heading neither decode nor classify the target."""
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    (tmp_path / old).parent.mkdir(parents=True)
    (tmp_path / old).write_text(_tombstone(target), encoding="utf-8")
    (tmp_path / target).write_bytes(
        b"# New\n\n- **Slug:** `new`\n- **Status:** Draft\n\n## Body\n\n"
        b"- **Tombstone:** 2026-09-29\n\xff\xfe not utf-8\n"
    )

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone"
    assert result.paths == (old, target)


def test_resolution_is_confined_to_the_intents_parent(tmp_path: Path) -> None:
    """Neither the input nor a tombstone's target may leave the intents parent."""
    (tmp_path / "README.md").write_text("# Not an intent\n", encoding="utf-8")
    old = "docs/product/intents/FEAT-0001-old.md"
    (tmp_path / old).parent.mkdir(parents=True)
    (tmp_path / old).write_text(_tombstone("README.md"), encoding="utf-8")

    outside = rename.resolve_intent_path("README.md", repository_root=tmp_path)
    escaped = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert outside.code == "resolve-refused"
    # The tombstone contract itself rejects a target outside the intents parent.
    assert escaped.code == "tombstone-invalid"


def test_ac_0009_resolution_stops_without_returning_successor_content(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    for relative, text in ((old, _tombstone(target)), (target, "successor secret\n")):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone"
    assert result.paths == (old, target)
    assert not hasattr(result, "content")


def test_t5_transaction_repoints_two_inbound_tombstones(tmp_path: Path) -> None:
    first, second = _rename_fixture(tmp_path)

    result = rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=tmp_path, _today=lambda: TOMBSTONE_DATE
    )

    assert result.status is rename.RenameStatus.COMMITTED
    for relative in (first, second):
        parsed = rename._tombstone.parse_tombstone(  # type: ignore[attr-defined]
            (tmp_path / relative).read_text(encoding="utf-8")
        )
        assert not isinstance(parsed, str)
        assert parsed.reissued_as == SUCCESSOR


def test_t5_malformed_tombstone_value_refuses_resolution(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    path = tmp_path / old
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Tombstone: old\n\n"
        "- **Slug:** `old`\n"
        "- **Tombstone:** 2026-09-29\n"
        "- **Reissued as:** /etc/passwd\n",
        encoding="utf-8",
    )

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-invalid"
    assert result.paths == (old,)


@pytest.mark.parametrize("hostile_path", HOSTILE_RESOLVE_PATHS)
def test_t5_unconfined_source_refusal_echoes_no_operator_input(
    tmp_path: Path, hostile_path: str
) -> None:
    if "\n" in hostile_path:
        path = tmp_path / hostile_path
        path.parent.mkdir(parents=True)
        path.write_text("# Live even though its name is unsafe\n", encoding="utf-8")

    result = rename.resolve_intent_path(hostile_path, repository_root=tmp_path)

    assert result.code == "resolve-refused"
    assert result.paths == ()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink unavailable")
def test_t5_source_symlink_is_refused_without_following(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = tmp_path / "outside.md"
    target.write_text(_tombstone("docs/product/intents/STRAT-0001-new.md"), encoding="utf-8")
    link = tmp_path / old
    link.parent.mkdir(parents=True)
    link.symlink_to(target)

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "resolve-refused"
    assert result.paths == ()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink unavailable")
def test_t5_target_symlink_is_refused_without_following(tmp_path: Path) -> None:
    old = "docs/product/intents/FEAT-0001-old.md"
    target = "docs/product/intents/STRAT-0001-new.md"
    outside = tmp_path / "outside.md"
    outside.write_text("# Live\n\n- **Slug:** `new`\n", encoding="utf-8")
    path = tmp_path / old
    path.parent.mkdir(parents=True)
    path.write_text(_tombstone(target), encoding="utf-8")
    (tmp_path / target).symlink_to(outside)

    result = rename.resolve_intent_path(old, repository_root=tmp_path)

    assert result.code == "tombstone-target-refused"
    assert result.paths == (old, target)
