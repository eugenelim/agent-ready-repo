"""The Meets relation, the repository-path check, and the concurrent Git gates.

Pure functions: no repository and no process, so this suite runs in the pack lane.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


def _load() -> ModuleType:
    alias = "core_work_loop_supervisor_concurrency_meets"
    spec = importlib.util.spec_from_file_location(alias, str(_SCRIPTS / "_supervisor_concurrency.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


c = _load()
A = c.Access


# (read or write, write, meets, why)
ROWS = [
    # a missing-path lookup and a write creating that path
    (A("missing", "a/b"), A("write", "a/b"), True, "missing vs create"),
    (A("missing", "a/b"), A("rename-to", "a/b"), True, "missing vs rename target"),
    (A("missing", "a/b"), A("write", "a/b/c"), True, "missing vs create under it (ancestor)"),
    (A("missing", "a/b"), A("write", "a/c"), False, "missing vs a sibling"),
    (A("missing", "a/b"), A("delete", "a/b"), False, "missing vs delete creates nothing"),
    (A("missing", "a/b"), A("mode", "a/b"), False, "missing vs mode change"),
    (A("missing", "a/b/c"), A("write", "a/b", subtree=True), True, "missing vs declared root/**"),
    (A("missing", "a"), A("write", "ab"), False, "a prefix is not an ancestor"),
    # a listing of a directory and a write adding, removing, or renaming an entry directly in it
    (A("listing", "a"), A("write", "a/x"), True, "listing vs direct entry"),
    (A("listing", "a"), A("delete", "a/x"), True, "listing vs direct removal"),
    (A("listing", "a"), A("rename-from", "a/x"), True, "listing vs rename source"),
    (A("listing", "a"), A("rename-to", "a/x"), True, "listing vs rename target"),
    (A("listing", "a"), A("write", "a/b/c"), True, "listing vs deeper write (ancestor entry)"),
    (A("listing", "a/b"), A("write", "a/b/c/d"), True, "listing vs deeper write, nested"),
    (A("listing", "a/b"), A("write", "a/c"), False, "listing vs a sibling directory's entry"),
    (A("listing", "a"), A("mode", "a/x"), False, "a mode change adds no entry"),
    (A("listing", "a/b"), A("write", "a"), False, "listing vs write to its parent"),
    (A("listing", "a"), A("write", "a", subtree=True), True, "listing vs declared a/**"),
    (A("listing", "a/b"), A("write", "a", subtree=True), True, "listing under a declared root"),
    (A("listing", "b"), A("write", "a", subtree=True), False, "listing outside a declared root"),
    (A("listing", "a"), A("write", "a/b", subtree=True), True, "listing of the root's parent"),
    # a walk of a root and any write at or under it
    (A("walk", "a"), A("write", "a/b/c"), True, "walk vs deep write"),
    (A("walk", "a"), A("write", "a"), True, "walk vs write at root"),
    (A("walk", "a"), A("mode", "a/b"), True, "walk vs mode change under it"),
    (A("walk", "a/b"), A("write", "a/c"), False, "walk vs write beside it"),
    (A("walk", "a/b"), A("write", "a"), False, "walk vs write to its parent file"),
    (A("walk", "a/b"), A("write", "a", subtree=True), True, "walk under a declared root"),
    (A("walk", "a"), A("write", "a/b", subtree=True), True, "declared root under a walk"),
    (A("walk", "a"), A("write", "b", subtree=True), False, "walk beside a declared root"),
    # any other read or write and a write to the same path
    (A("file", "a/b"), A("write", "a/b"), True, "file vs same path"),
    (A("file", "a/b"), A("delete", "a/b"), True, "file vs delete"),
    (A("file", "a/b"), A("write", "a/c"), False, "file vs another file"),
    (A("file", "a/b"), A("write", "a/b/c"), True, "file vs a write that makes it a directory"),
    (A("file", "a"), A("write", "a/b"), True, "file vs write under it (ancestor)"),
    (A("file", "a/b/c"), A("write", "a/b"), False, "file under a written file path"),
    (A("file", "a/b"), A("write", "a", subtree=True), True, "file under a declared root"),
    (A("file", "ab"), A("write", "a", subtree=True), False, "file beside a declared root"),
    (A("write", "a/b"), A("write", "a/b"), True, "write vs same-path write"),
    (A("write", "a/b"), A("write", "a/c"), False, "sibling writes do not meet"),
    (A("write", "a/b/c"), A("write", "a/b"), True, "write vs write to its ancestor"),
    (A("write", "a/b"), A("write", "a/b/c"), True, "write whose path the other makes a directory"),
    (A("write", "x/y"), A("write", "a", subtree=True), False, "write outside a declared root"),
    (A("write", "a/b"), A("write", "a", subtree=True), True, "write inside a declared root"),
    (A("write", "a", subtree=True), A("write", "a/b", subtree=True), True, "nested roots"),
    (A("write", "a", subtree=True), A("write", "b", subtree=True), False, "disjoint roots"),
]


@pytest.mark.parametrize(("access", "write", "expected", "why"), ROWS, ids=[r[3] for r in ROWS])
def test_meets_row(access: object, write: object, expected: bool, why: str) -> None:
    assert c.meets(access, write) is expected


def test_the_second_argument_must_be_a_write() -> None:
    with pytest.raises(ValueError):
        c.meets(A("file", "a"), A("file", "a"))


def test_unknown_kinds_are_refused() -> None:
    with pytest.raises(ValueError):
        A("scan", "a")
    with pytest.raises(ValueError):
        A("delete", "a", subtree=True)


def test_paths_compare_in_nfc_and_fold_case_only_when_asked() -> None:
    composed, decomposed = "café/x", "café/x"
    assert c.meets(A("file", composed), A("write", decomposed))
    assert not c.meets(A("file", "Docs/A"), A("write", "docs/a"))
    assert c.meets(A("file", "Docs/A"), A("write", "docs/a"), ignore_case=True)
    assert c.meets(A("listing", "DOCS"), A("write", "docs/new"), ignore_case=True)
    assert not c.meets(A("listing", "DOCS"), A("write", "docs/new"))


def test_declared_entries_map_to_accesses() -> None:
    assert c.declared_reads(["a/b.py", "src/", "lib/**"]) == [
        A("file", "a/b.py"), A("listing", "src"), A("walk", "lib"),
    ]
    assert c.declared_writes(["a/b.py", "out/**"]) == [
        A("write", "a/b.py"), A("write", "out", subtree=True),
    ]


def test_tasks_meet_in_either_direction_and_a_disjoint_pair_does_not() -> None:
    reads_a, writes_a = c.declared_reads(["src/"]), c.declared_writes(["src/a.py"])
    reads_b, writes_b = c.declared_reads(["docs/x.md"]), c.declared_writes(["src/b.py"])
    assert c.tasks_meet(reads_a, writes_a, reads_b, writes_b)  # a lists src; b adds src/b.py
    assert c.tasks_meet(reads_b, writes_b, reads_a, writes_a)
    reads_c, writes_c = c.declared_reads(["docs/y.md"]), c.declared_writes(["docs/z/**"])
    assert not c.tasks_meet(reads_a, writes_a, reads_c, writes_c)
    assert c.tasks_meet(reads_b, writes_b, reads_c, c.declared_writes(["docs/x.md"]))
    assert not c.tasks_meet([], c.declared_writes(["a/x"]), [], c.declared_writes(["a/y"]))


@pytest.mark.parametrize(
    "path",
    ["a", "a/b", "dir/file.txt", "café/x", "a b/c"],
)
def test_repository_path_accepts(path: str) -> None:
    assert c.is_repository_path(path)


@pytest.mark.parametrize(
    "path",
    ["", "/a", "a//b", "a/", "./a", "a/./b", "a/../b", "..", "a\\b", "a\0b", "a\nb", "a\x7fb"],
)
def test_repository_path_refuses(path: str) -> None:
    assert not c.is_repository_path(path)


def test_git_floor_reason_names_a_version_below_2_41() -> None:
    assert c.git_floor_reason((2, 40)) == "git-version"
    assert c.git_floor_reason((1, 99)) == "git-version"
    assert c.git_floor_reason((2, 41)) is None
    assert c.git_floor_reason((3, 0)) is None


def test_merge_config_floor_reason_ignores_drivers_and_other_scopes() -> None:
    git = c._git
    entry = git.ConfigEntry
    assert c.merge_config_floor_reason([entry("local", "merge.conflictstyle", "diff3")]) == (
        "merge-config"
    )
    assert c.merge_config_floor_reason([entry("worktree", "merge.ff", "false")]) == "merge-config"
    assert c.merge_config_floor_reason([entry("local", "merge.x.driver", "prog %O")]) is None
    assert c.merge_config_floor_reason([entry("global", "merge.ff", "false")]) is None
    assert c.merge_config_floor_reason([entry("local", "core.bare", "false")]) is None


@pytest.mark.parametrize(
    "name",
    [".git", ".GIT", ".Git", ".g‌it", ".gi‎t", "﻿.git", "git~1", "GIT~1",
     ".git.", ".git ", ".git. .", ".git:stream", "git~1."],
)
def test_dot_git_aliases(name: str) -> None:
    assert c.is_dot_git_name(name)


@pytest.mark.parametrize("name", [".gitignore", ".gitattributes", "git", "git~2", "x.git", ".gi"])
def test_non_aliases(name: str) -> None:
    assert not c.is_dot_git_name(name)
