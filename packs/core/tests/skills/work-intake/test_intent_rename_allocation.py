# STUB: AC-0012
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

_PARENTS = Path(__file__).resolve().parents
PACK_ROOT = _PARENTS[3] if len(_PARENTS) > 3 else Path.cwd() / "packs/core"
SCRIPT = PACK_ROOT / ".apm/skills/work-intake/scripts/intent_rename.py"
SOURCE = "docs/product/intents/FEAT-0001-rename-test.md"
SUCCESSOR_0002 = "docs/product/intents/STRAT-0002-rename-test.md"


def _load() -> Any:
    spec = importlib.util.spec_from_file_location("core_work_intake_intent_rename_allocation", SCRIPT)
    assert spec and spec.loader, SCRIPT
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load()


def _init_git(root: Path) -> None:
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


def _commit(root: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "fixture"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _fixture(root: Path) -> None:
    _init_git(root)
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Rename test\n\n"
        "- **Slug:** `rename-test`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n",
        encoding="utf-8",
    )
    entry = (
        f'{{path = "{SOURCE}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}'
    )
    (root / "workspace.toml").write_text(
        f"[backlog]\nopen = [{entry}]\n",
        encoding="utf-8",
    )
    _commit(root)


def _install_origin_only_name(root: Path, name: str) -> None:
    """Expose one higher ordinal only through a local origin-tracking ref."""
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "switch", "-c", "remote-seed"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "docs/product/intents" / name).write_text(
        "- **Slug:** `remote-only`\n", encoding="utf-8"
    )
    _commit(root)
    remote_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "switch", "--detach", base],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", "."],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", remote_commit],
        cwd=root,
        check=True,
        capture_output=True,
    )


@pytest.mark.parametrize("token", rename._ordinal.NAMESPACE_TOKENS)  # type: ignore[attr-defined]
def test_ac_0012_uses_allocator_next_for_every_namespace_token(
    token: str, tmp_path: Path
) -> None:
    intents = tmp_path / "docs/product/intents"
    intents.mkdir(parents=True)
    (tmp_path / SOURCE).write_text("- **Slug:** `rename-test`\n", encoding="utf-8")
    (intents / f"{token}-0002-existing.md").write_text(
        "- **Slug:** `existing`\n", encoding="utf-8"
    )

    successor = rename.derive_successor_path(
        SOURCE, token, repository_root=tmp_path
    )

    assert successor == f"docs/product/intents/{token}-0003-rename-test.md"
    assert successor != f"docs/product/intents/{token}-0001-rename-test.md"


def test_ac_0012_counts_tombstones_in_the_target_namespace(tmp_path: Path) -> None:
    intents = tmp_path / "docs/product/intents"
    intents.mkdir(parents=True)
    (tmp_path / SOURCE).write_text("- **Slug:** `rename-test`\n", encoding="utf-8")
    (intents / "STRAT-0002-old-name.md").write_text(
        "# Tombstone: old-name\n\n"
        "- **Slug:** `old-name`\n"
        "- **Tombstone:** 2026-09-21\n"
        "- **Reissued as:** docs/product/intents/STRAT-0003-new-name.md\n",
        encoding="utf-8",
    )

    successor = rename.derive_successor_path(SOURCE, "STRAT", repository_root=tmp_path)

    assert successor == "docs/product/intents/STRAT-0003-rename-test.md"


def test_ac_0012_rename_pins_one_origin_union_for_planning_and_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fixture(tmp_path)
    _install_origin_only_name(tmp_path, "STRAT-0009-remote-only.md")
    remote_view = rename._ordinal.remote_view  # type: ignore[attr-defined]
    answered = False

    def origin_moves_after_first_look(directory: Path, deadline: float | None = None) -> Any:
        # The first look is the real origin view. Any later look sees origin
        # move to STRAT-0020, which would allocate 0021 if it were consulted.
        nonlocal answered
        view = remote_view(directory, deadline)
        if not answered:
            answered = True
            return view
        return view._replace(names=frozenset(view.names) | {"STRAT-0020-moved.md"})

    monkeypatch.setattr(
        rename._ordinal, "remote_view", origin_moves_after_first_look  # type: ignore[attr-defined]
    )

    def interrupt(checkpoint: str) -> None:
        if checkpoint == "after-seal":
            raise rename.InjectedInterruption(checkpoint)

    result = rename.run_intent_rename(
        SOURCE,
        "STRAT",
        repository_root=tmp_path,
        _checkpoint=interrupt,
        _today=lambda: date(2026, 9, 30),
    )

    assert result.status is rename.RenameStatus.PARTIAL
    stage = next((tmp_path / "docs/product/intents").glob(".intent-rename-*"))
    record = json.loads((stage / "record.json").read_text(encoding="ascii"))
    assert record["registry"]["successor"] == (
        "docs/product/intents/STRAT-0010-rename-test.md"
    )


def test_ac_0013_non_regular_in_namespace_entry_refuses_allocation(tmp_path: Path) -> None:
    """The pinned snapshot keeps entry types, so the allocator refuses what it cannot count."""
    _fixture(tmp_path)
    (tmp_path / "docs/product/intents/STRAT-0005-link.md").symlink_to("elsewhere.md")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "link"], cwd=tmp_path, check=True, capture_output=True)

    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert (result.status, result.code) == (rename.RenameStatus.REFUSED, "allocation-refused")
    assert not list((tmp_path / "docs/product/intents").glob(".intent-rename-*"))


def test_ac_0013_untyped_legacy_source_renames_into_a_typed_successor(
    tmp_path: Path,
) -> None:
    """The request contract admits an untyped intent; its stem becomes the slug."""
    legacy = "docs/product/intents/legacy-intent.md"
    _init_git(tmp_path)
    source = tmp_path / legacy
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Legacy intent\n\n"
        "- **Slug:** `legacy-intent`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n",
        encoding="utf-8",
    )
    entry = (
        f'{{path = "{legacy}", kind = "intent", '
        'source = {mode = "repo-origin"}, summary = "rename", needs = []}'
    )
    (tmp_path / "workspace.toml").write_text(f"[backlog]\nopen = [{entry}]\n", encoding="utf-8")
    _commit(tmp_path)

    result = rename.run_intent_rename(legacy, "STRAT", repository_root=tmp_path)

    successor = "docs/product/intents/STRAT-0001-legacy-intent.md"
    assert result.status is rename.RenameStatus.COMMITTED, result
    assert (tmp_path / successor).is_file()
    assert f"- **Reissued as:** {successor}" in source.read_text(encoding="utf-8")


def test_ac_0012_allocator_refusal_refuses_successor_derivation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    intents = tmp_path / "docs/product/intents"
    intents.mkdir(parents=True)
    (tmp_path / SOURCE).write_text("- **Slug:** `rename-test`\n", encoding="utf-8")
    monkeypatch.setattr(
        rename._ordinal,  # type: ignore[attr-defined]
        "next_typed_ordinal",
        lambda _directory, _token: None,
    )

    assert rename.derive_successor_path(SOURCE, "STRAT", repository_root=tmp_path) is None


@pytest.mark.parametrize("tracked", [False, True])
def test_ac_0012_occupied_successor_refuses_before_staging(
    tracked: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fixture(tmp_path)
    occupied = tmp_path / SUCCESSOR_0002
    occupied.write_text("- **Slug:** `occupied`\n", encoding="utf-8")
    if tracked:
        subprocess.run(["git", "add", SUCCESSOR_0002], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "occupied successor"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
    monkeypatch.setattr(
        rename._ordinal,  # type: ignore[attr-defined]
        "next_typed_ordinal",
        lambda _directory, _token: 2,
    )

    result = rename.run_intent_rename(SOURCE, "STRAT", repository_root=tmp_path)

    assert result.status is rename.RenameStatus.REFUSED
    assert result.code == "successor-exists"
    assert not list((tmp_path / "docs/product/intents").glob(".intent-rename-*"))
