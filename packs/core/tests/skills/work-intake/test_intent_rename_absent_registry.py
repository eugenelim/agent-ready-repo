# STUB: AC-0018, AC-0021, AC-0022
"""An intent rename runs without ``workspace.toml``, and refuses every one-sided state."""

from __future__ import annotations

import dataclasses
import importlib.util
import os
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = PACK_ROOT / ".apm/skills/work-intake/scripts"
SOURCE = "docs/product/intents/FEAT-0001-rename-test.md"
SUCCESSOR = "docs/product/intents/STRAT-0001-rename-test.md"
TOMBSTONE_DATE = date(2026, 9, 29)
NEITHER = "[backlog]\nopen = []\n"
REGISTERED = (
    "[backlog]\n"
    f'open = [{{path = "{SOURCE}", kind = "intent", '
    'source = {mode = "repo-origin"}, summary = "rename", needs = []}]\n'
)


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, path
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


rename = _load(SCRIPTS / "intent_rename.py", "core_work_intake_intent_rename_absent_registry")
request = _load(SCRIPTS / "intent_rename_request.py", "core_work_intake_request_absent_registry")


def _sandbox_remove_empty_stage(parent_descriptor: int, name: str) -> None:
    """Move a verified-empty stage out of the stage namespace instead of rmdir."""
    os.rename(
        name,
        ".sandbox-disposed-" + name,
        src_dir_fd=parent_descriptor,
        dst_dir_fd=parent_descriptor,
    )


rename._remove_empty_stage = _sandbox_remove_empty_stage


def _run(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)


def _commit(root: Path, message: str = "fixture") -> None:
    _run(root, "add", "-A")
    _run(root, "commit", "-m", message)


def _repo(root: Path, kind: str) -> None:
    """Plant one repository: ``absent``, ``twin``, ``deleted`` or ``twin-after``."""
    _run(root, "init")
    _run(root, "config", "user.email", "test@example.invalid")
    _run(root, "config", "user.name", "Test Runner")
    source = root / SOURCE
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Rename test\n\n"
        "- **Slug:** `rename-test`\n"
        "- **Status:** Draft\n"
        "- **Level:** feature\n"
        "- **Owner:** test-owner\n\n"
        f"Self: {SOURCE}\n",
        encoding="utf-8",
    )
    (root / "citation.md").write_text(f"See {SOURCE}.\n", encoding="utf-8")
    if kind == "twin":
        (root / "workspace.toml").write_text(NEITHER, encoding="utf-8")
    elif kind in {"deleted", "twin-after"}:
        (root / "workspace.toml").write_text(REGISTERED, encoding="utf-8")
    _commit(root)
    if kind == "deleted":
        _run(root, "rm", "-q", "workspace.toml")
        _commit(root, "delete the registry")
    elif kind == "twin-after":
        (root / "workspace.toml").write_text(NEITHER, encoding="utf-8")
        _commit(root, "rewrite the registry")


_KINDS = ("absent", "twin", "deleted", "twin-after")
_TEMPLATES: dict[str, Path] = {}


@pytest.fixture(scope="module", autouse=True)
def _repository_templates(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Build each repository kind once; tests copy a template, never mutate it."""
    base = tmp_path_factory.mktemp("templates")
    for kind in _KINDS:
        root = base / kind
        root.mkdir()
        _repo(root, kind)
        _TEMPLATES[kind] = root


def _make(tmp_path: Path, kind: str) -> Path:
    """An isolated copy of the ``kind`` template, ``.git`` included."""
    root = tmp_path / kind
    shutil.copytree(_TEMPLATES[kind], root, symlinks=True)
    return root


def _tracked_tree(root: Path) -> dict[str, bytes]:
    """Every regular file except ``workspace.toml``, ``.git`` and disposed stages."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and ".git" not in path.relative_to(root).parts
        and path.relative_to(root).as_posix() != "workspace.toml"
    }


def _snapshot(root: Path) -> tuple[object, bytes]:
    """The whole tree, links and directories included, plus the raw index."""
    entries: dict[str, object] = {}
    for current, directories, files in os.walk(root):
        relative_root = Path(current).relative_to(root)
        if ".git" in relative_root.parts:
            continue
        directories[:] = [name for name in directories if name != ".git"]
        for name in [*directories, *files]:
            path = Path(current) / name
            key = (relative_root / name).as_posix()
            if path.is_symlink():
                entries[key] = ("link", os.readlink(path))
            elif path.is_dir():
                entries[key] = ("dir",)
            else:
                try:
                    entries[key] = ("file", path.read_bytes())
                except PermissionError:
                    entries[key] = ("unreadable",)
    return entries, (root / ".git/index").read_bytes()


def _today() -> date:
    return TOMBSTONE_DATE


def _forward(root: Path, checkpoint: Any = None) -> Any:
    keyword = {} if checkpoint is None else {"_checkpoint": checkpoint}
    return rename.run_intent_rename(
        SOURCE, "STRAT", repository_root=root, _today=_today, **keyword
    )


def _recover(root: Path, direction: str) -> Any:
    return rename.recover_intent_rename(
        direction, SOURCE, "STRAT", TOMBSTONE_DATE.isoformat(), repository_root=root
    )


def _interrupt(name: str) -> Any:
    def checkpoint(checkpoint_name: str) -> None:
        if checkpoint_name == name:
            raise rename.InjectedInterruption(checkpoint_name)

    return checkpoint


def _outcome(result: Any) -> tuple[object, str]:
    return result.status, result.code


def _stage_dirs(root: Path) -> list[Path]:
    return sorted((root / "docs/product/intents").glob(".intent-rename-*"))


_ABSENT_KINDS = ["absent", "deleted"]


def _twin(tmp_path: Path, kind: str) -> Path:
    return _make(tmp_path, "twin" if kind == "absent" else "twin-after")


# ── AC-0018: the same answers as a repository whose registry names neither ───


@pytest.mark.parametrize("kind", _ABSENT_KINDS)
def test_ac_0018_request_matches_the_twin(tmp_path: Path, kind: str) -> None:
    absent = _make(tmp_path, kind)
    twin = _twin(tmp_path, kind)

    got = request.validate_rename_request(SOURCE, "STRAT", repository_root=absent)
    want = request.validate_rename_request(SOURCE, "STRAT", repository_root=twin)

    assert not isinstance(got, str), got
    assert not isinstance(want, str), want

    def resolved(value: Any, root: Path) -> dict[str, object]:
        fields = dataclasses.asdict(value)
        fields.pop("repository_root")
        fields["source"] = Path(fields["source"]).relative_to(root.resolve()).as_posix()
        return fields

    assert resolved(got, absent) == resolved(want, twin)
    assert not (absent / "workspace.toml").exists()


@pytest.mark.parametrize("kind", _ABSENT_KINDS)
def test_ac_0018_forward_rename_matches_the_twin(tmp_path: Path, kind: str) -> None:
    absent = _make(tmp_path, kind)
    twin = _twin(tmp_path, kind)

    got = _forward(absent)
    want = _forward(twin)

    assert _outcome(want) == (rename.RenameStatus.COMMITTED, "committed")
    assert _outcome(got) == _outcome(want)
    assert _tracked_tree(absent) == _tracked_tree(twin)
    assert (absent / SUCCESSOR).is_file()
    assert not (absent / "workspace.toml").exists()
    assert _stage_dirs(absent) == []


@pytest.mark.parametrize("kind", _ABSENT_KINDS)
@pytest.mark.parametrize("direction", ["forward", "back"])
def test_ac_0018_recovery_matches_the_twin(tmp_path: Path, kind: str, direction: str) -> None:
    absent = _make(tmp_path, kind)
    twin = _twin(tmp_path, kind)

    planted_absent = _forward(absent, _interrupt("after-successor"))
    planted_twin = _forward(twin, _interrupt("after-successor"))
    assert _outcome(planted_twin)[0] is rename.RenameStatus.PARTIAL
    assert _outcome(planted_absent) == _outcome(planted_twin)
    assert len(_stage_dirs(absent)) == 1

    got = _recover(absent, direction)
    want = _recover(twin, direction)

    assert _outcome(want)[0] in {
        rename.RenameStatus.COMMITTED,
        rename.RenameStatus.ROLLED_BACK,
    }
    assert _outcome(got) == _outcome(want)
    assert _tracked_tree(absent) == _tracked_tree(twin)
    assert not (absent / "workspace.toml").exists()
    assert _stage_dirs(absent) == []


_MARKER_PREFIX = b'{"completion_seal_sha256":"'


@pytest.mark.parametrize("kind", _ABSENT_KINDS)
@pytest.mark.parametrize("stage", ["empty", "torn-marker"])
@pytest.mark.parametrize("direction", ["forward", "back"])
def test_ac_0018_terminal_cleanup_disposes_only_the_stage(
    tmp_path: Path, kind: str, stage: str, direction: str
) -> None:
    absent = _make(tmp_path, kind)
    twin = _twin(tmp_path, kind)
    for root in (absent, twin):
        directory = root / "docs/product/intents" / f".intent-rename-{'ab' * 16}"
        directory.mkdir()
        if stage == "torn-marker":
            (directory / "cleanup.json").write_bytes(_MARKER_PREFIX)
    before = _tracked_tree(absent)
    assert len(_stage_dirs(absent)) == 1

    got = _recover(absent, direction)
    want = _recover(twin, direction)

    assert _outcome(want) == (rename.RenameStatus.ROLLED_BACK, "rolled-back")
    assert _outcome(got) == _outcome(want)
    assert _stage_dirs(absent) == []
    assert _tracked_tree(absent) == _tracked_tree(twin)
    # Only the stage's own marker is gone; every other file is untouched.
    assert _tracked_tree(absent) == {
        key: value for key, value in before.items() if not key.endswith("cleanup.json")
    }
    assert not (absent / "workspace.toml").exists()


# ── AC-0021: every refusal row writes nothing ────────────────────────────────


def _plant_link(root: Path) -> None:
    (root / "elsewhere.toml").write_text(NEITHER, encoding="utf-8")
    (root / "workspace.toml").symlink_to("elsewhere.toml")


def _plant_dangling(root: Path) -> None:
    (root / "workspace.toml").symlink_to("missing.toml")


def _plant_directory(root: Path) -> None:
    (root / "workspace.toml").mkdir()


def _plant_unreadable(root: Path) -> None:
    (root / "workspace.toml").write_text(NEITHER, encoding="utf-8")
    (root / "workspace.toml").chmod(0)


def _plant_invalid(root: Path) -> None:
    (root / "workspace.toml").write_text("not = [valid", encoding="utf-8")


@pytest.mark.parametrize(
    "plant",
    [_plant_link, _plant_dangling, _plant_directory, _plant_unreadable, _plant_invalid],
)
def test_ac_0021_unusable_registry_refuses_unparseable(tmp_path: Path, plant: Any) -> None:
    if plant is _plant_unreadable and os.geteuid() == 0:
        pytest.skip("a superuser reads a mode-0 file")
    root = _make(tmp_path, "absent")
    plant(root)
    before = _snapshot(root)
    try:
        got = request.validate_rename_request(SOURCE, "STRAT", repository_root=root)
        forward = _forward(root)
        after = _snapshot(root)
    finally:
        if (root / "workspace.toml").exists() and not (root / "workspace.toml").is_symlink():
            (root / "workspace.toml").chmod(0o644)

    assert got == "registry-unparseable"
    assert _outcome(forward) == (rename.RenameStatus.REFUSED, "registry-unparseable")
    assert after == before


def _plant_untracked(root: Path) -> None:
    (root / "workspace.toml").write_text(NEITHER, encoding="utf-8")


def _plant_deleted_from_disk(root: Path) -> None:
    Path(root / "workspace.toml").unlink()


def _plant_index_only(root: Path) -> None:
    (root / "workspace.toml").write_text(NEITHER, encoding="utf-8")
    _run(root, "add", "workspace.toml")
    Path(root / "workspace.toml").unlink()


_ONE_SIDED = [
    ("absent", _plant_untracked),
    ("twin", _plant_deleted_from_disk),
    ("absent", _plant_index_only),
]


def _derived(root: Path) -> Any:
    base = rename._head(root)
    allocation = rename._pinned_allocation(root, base, SOURCE, "STRAT")
    return rename._derive(
        root,
        operation_id="cd" * 16,
        base_commit=base,
        source=SOURCE,
        target_token="STRAT",
        date=TOMBSTONE_DATE.isoformat(),
        successor=allocation.successor,
        pinned_allocation=allocation,
    )


@pytest.mark.parametrize(("kind", "plant"), _ONE_SIDED)
def test_ac_0021_one_sided_registry_is_path_dirty(tmp_path: Path, kind: str, plant: Any) -> None:
    root = _make(tmp_path, kind)
    plant(root)
    before = _snapshot(root)

    got = request.validate_rename_request(SOURCE, "STRAT", repository_root=root)
    forward = _forward(root)

    assert got == "path-dirty"
    assert _outcome(forward) == (rename.RenameStatus.REFUSED, "path-dirty")
    assert rename._replacement_targets_are_dirty(root, _derived(root)) is True
    assert request._is_dirty(root, SOURCE) is True
    assert _snapshot(root) == before


def test_ac_0021_absent_everywhere_is_not_dirty(tmp_path: Path) -> None:
    root = _make(tmp_path, "absent")

    assert rename._replacement_targets_are_dirty(root, _derived(root)) is False
    assert request._is_dirty(root, SOURCE) is False


def test_ac_0021_failing_ls_files_counts_as_present(tmp_path: Path) -> None:
    root = _make(tmp_path, "absent")
    derived = _derived(root)
    (root / ".git/index").write_bytes(b"not an index")
    before = _snapshot(root)

    assert rename._registry_absent(root, derived.base_commit) is False
    assert rename._replacement_targets_are_dirty(root, derived) is True
    assert request._registry_absent(root) is False
    assert request._is_dirty(root, SOURCE) is True
    assert request.validate_rename_request(SOURCE, "STRAT", repository_root=root) == "path-dirty"
    assert _snapshot(root) == before


def test_ac_0021_a_present_registry_is_not_absent(tmp_path: Path) -> None:
    root = _make(tmp_path, "twin")

    assert rename._registry_absent(root, rename._head(root)) is False
    assert request._registry_absent(root) is False


def test_ac_0021_registry_deleted_by_a_later_commit_is_not_absent_at_the_old_one(
    tmp_path: Path,
) -> None:
    root = _make(tmp_path, "deleted")
    registered = _run(root, "rev-parse", "HEAD~1").stdout.decode().strip()

    assert rename._registry_absent(root, registered) is False
    assert rename._registry_absent(root, rename._head(root)) is True


# ── AC-0021: the pinned-commit lookup ────────────────────────────────────────


def _tree_output(mode: str, kind: str) -> bytes:
    return f"{mode} {kind} {'0' * 40}\tworkspace.toml\0".encode()


def _patch_ls_tree(monkeypatch: pytest.MonkeyPatch, outcome: bytes | None) -> None:
    """Make ``git ls-tree`` of ``workspace.toml`` fail (``None``) or list ``outcome``."""
    real = rename._git

    def patched(root: Path, arguments: Any, *, max_bytes: int) -> bytes:
        if arguments and arguments[0] == "ls-tree" and arguments[-1] == "workspace.toml":
            if outcome is None:
                raise ValueError("git-refused")
            return outcome
        return real(root, arguments, max_bytes=max_bytes)

    monkeypatch.setattr(rename, "_git", patched)


_BAD_LOOKUPS = {
    "failing": None,
    "tree": _tree_output("040000", "tree"),
    "link": _tree_output("120000", "blob"),
    "gitlink": _tree_output("160000", "commit"),
}


@pytest.mark.parametrize("lookup", sorted(_BAD_LOOKUPS))
def test_ac_0021_mode_refuses_a_bad_pinned_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lookup: str
) -> None:
    root = _make(tmp_path, "deleted")
    _patch_ls_tree(monkeypatch, _BAD_LOOKUPS[lookup])

    with pytest.raises(ValueError):
        rename._registry_mode(root, rename._head(root), SOURCE, SUCCESSOR)


@pytest.mark.parametrize("lookup", sorted(_BAD_LOOKUPS))
def test_ac_0021_forward_rename_refuses_a_bad_pinned_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lookup: str
) -> None:
    root = _make(tmp_path, "twin")
    before = _snapshot(root)
    _patch_ls_tree(monkeypatch, _BAD_LOOKUPS[lookup])

    result = _forward(root)

    assert result.status is rename.RenameStatus.REFUSED
    assert _stage_dirs(root) == []
    assert _snapshot(root) == before


@pytest.mark.parametrize("lookup", sorted(_BAD_LOOKUPS))
@pytest.mark.parametrize("direction", ["forward", "back"])
def test_ac_0021_recovery_refuses_a_bad_pinned_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, lookup: str, direction: str
) -> None:
    root = _make(tmp_path, "twin")
    assert _forward(root, _interrupt("after-successor")).status is rename.RenameStatus.PARTIAL
    before = _snapshot(root)
    _patch_ls_tree(monkeypatch, _BAD_LOOKUPS[lookup])

    result = _recover(root, direction)

    assert result.status is rename.RenameStatus.REFUSED
    assert len(_stage_dirs(root)) == 1
    assert _snapshot(root) == before


def test_ac_0021_a_stage_after_a_registry_deleting_commit_is_base_changed(
    tmp_path: Path,
) -> None:
    root = _make(tmp_path, "twin")
    assert _forward(root, _interrupt("after-successor")).status is rename.RenameStatus.PARTIAL
    _run(root, "rm", "-q", "workspace.toml")
    _run(root, "commit", "-q", "-m", "delete the registry")
    before = _snapshot(root)

    for direction in ("forward", "back"):
        result = _recover(root, direction)

        assert result.status is rename.RenameStatus.REFUSED
        assert result.code == "base-changed"
        assert _snapshot(root) == before
