"""Contract tests for where the offline view may be written and how it is published.

Every path is under ``tmp_path``.  Git repositories are built with the real ``git``
binary; the identity they need is set only in the setup commands' own environment.
"""

from __future__ import annotations

import errno
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_MIXED = pathlib.Path(__file__).resolve().parent / "fixtures" / "mixed"


def _load(path: pathlib.Path, module_name: str) -> Any:
    """Load a navigate-intents script by path under a pack-and-skill-unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_publication_nav")
view = _load(_SCRIPTS / "intent_view.py", "core_navigate_intents_publication_view")

_HAS_GIT = shutil.which("git") is not None
needs_git = pytest.mark.skipif(not _HAS_GIT, reason="git is not installed")
_SETUP_ENV = {
    **{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    "GIT_AUTHOR_NAME": "Example Author",
    "GIT_AUTHOR_EMAIL": "author@example.invalid",
    "GIT_COMMITTER_NAME": "Example Author",
    "GIT_COMMITTER_EMAIL": "author@example.invalid",
}


def _git(cwd: pathlib.Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(cwd), "-c", "protocol.file.allow=always", *args],
        env=_SETUP_ENV, capture_output=True, text=True, check=True, timeout=60,
    )
    return done.stdout


def _repo(path: pathlib.Path, *extra: str) -> pathlib.Path:
    """Create a repository with one commit; *extra* go to ``git init``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", *extra, str(path)], env=_SETUP_ENV, check=True,
        capture_output=True, timeout=60,
    )
    _git(path, "commit", "-q", "--allow-empty", "-m", "initial")
    return path


def _dir(path: pathlib.Path) -> pathlib.Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _refusal(root: pathlib.Path, destination: pathlib.Path | str | None,
             name: str | None = None) -> Any:
    with pytest.raises(view.ViewRefusal) as caught:
        view.validate_destination(root, None if destination is None else str(destination), name)
    return caught.value


def _refused_naming(root: pathlib.Path, destination: pathlib.Path, named: pathlib.Path) -> None:
    exc = _refusal(root, destination)
    assert exc.code == "invalid_destination"
    assert os.path.realpath(named) in exc.message


# ---------------------------------------------------------------------------
# AC-0014: defaults
# ---------------------------------------------------------------------------


def test_default_destination_and_name(tmp_path: pathlib.Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    default = _dir(tmp_path / "tmpdir")
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(default))
    root = _dir(tmp_path / "root")
    target = view.validate_destination(root, None, None)
    assert target.directory == os.path.realpath(default)
    assert re.fullmatch(r"intent-graph-\d{8}T\d{6}Z\.html", target.name)


# ---------------------------------------------------------------------------
# AC-0015: containment
# ---------------------------------------------------------------------------


def test_destination_equal_under_symlink_file_and_missing(tmp_path: pathlib.Path) -> None:
    root = _dir(tmp_path / "root")
    inner = _dir(root / "inner")
    _refused_naming(root, root, root)
    _refused_naming(root, inner, root)
    outside = _dir(tmp_path / "outside")
    link = outside / "link"
    link.symlink_to(inner)
    _refused_naming(root, link, root)
    plain = tmp_path / "file.txt"
    plain.write_text("x")
    assert _refusal(root, plain).code == "invalid_destination"
    assert _refusal(root, tmp_path / "missing").code == "invalid_destination"


@needs_git
def test_subdirectory_root_refuses_top_level_and_sibling(tmp_path: pathlib.Path) -> None:
    top = _repo(tmp_path / "repo")
    root = _dir(top / "sub" / "dir")
    sibling = _dir(top / "sub" / "other")
    _refused_naming(root, top, top)
    _refused_naming(root, sibling, top)
    assert view.validate_destination(root, str(_dir(tmp_path / "out")), None)


@needs_git
def test_linked_worktree_inside_main_checkout_refuses_main(tmp_path: pathlib.Path) -> None:
    main = _repo(tmp_path / "main")
    linked = main / ".worktrees" / "wt"
    _git(main, "worktree", "add", "-q", str(linked))
    _refused_naming(linked, _dir(main / "docs"), main)


@needs_git
def test_linked_worktree_outside_refuses_main_and_second_worktree(
    tmp_path: pathlib.Path,
) -> None:
    main = _repo(tmp_path / "main")
    first, second = tmp_path / "wt1", tmp_path / "wt2"
    _git(main, "worktree", "add", "-q", str(first))
    _git(main, "worktree", "add", "-q", str(second))
    _refused_naming(first, _dir(main / "docs"), main)
    _refused_naming(first, _dir(second / "docs"), second)
    assert view.validate_destination(first, str(_dir(tmp_path / "out")), None)


@needs_git
def test_relative_worktree_pointers_refuse_main(tmp_path: pathlib.Path) -> None:
    main = _repo(tmp_path / "main")
    linked = tmp_path / "wt"
    done = subprocess.run(
        ["git", "-C", str(main), "-c", "worktree.useRelativePaths=true",
         "worktree", "add", "-q", str(linked)],
        env=_SETUP_ENV, capture_output=True, check=False, timeout=60,
    )
    if done.returncode != 0:
        pytest.skip("this git does not support worktree.useRelativePaths")
    _refused_naming(linked, _dir(main / "docs"), main)


def _publish_with_default(root: pathlib.Path, default: pathlib.Path,
                          monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(default))
    shutil.copytree(_MIXED, root, dirs_exist_ok=True)
    result, code = nav.run_export(root, None, None, None)
    assert code == 0 and result["status"] == "ok", result
    assert pathlib.Path(result["path"]).parent == pathlib.Path(os.path.realpath(default))


@needs_git
def test_separate_git_dir_checkout_exports_to_default(tmp_path: pathlib.Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    main = tmp_path / "main"
    _repo(main, "--separate-git-dir", str(tmp_path / "sep.git"))
    _publish_with_default(main, _dir(tmp_path / "default"), monkeypatch)


@needs_git
def test_submodule_exports_to_default(tmp_path: pathlib.Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    lib = _repo(tmp_path / "lib", "-b", "main")
    bare = tmp_path / "bare.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(lib), str(bare)],
                   env=_SETUP_ENV, check=True, capture_output=True, timeout=60)
    sup = _repo(tmp_path / "sup")
    _git(sup, "submodule", "add", "-q", str(bare), "sm")
    _publish_with_default(sup / "sm", _dir(tmp_path / "default"), monkeypatch)


@needs_git
def test_outer_repository_enclosing_the_repository_is_refused(tmp_path: pathlib.Path) -> None:
    outer = _repo(tmp_path / "outer")
    inner = _repo(outer / "vendor" / "inner")
    _refused_naming(inner, _dir(outer / "docs"), outer)


@needs_git
def test_git_unavailable_refuses_while_a_git_entry_encloses_root(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path / "repo")
    out = _dir(tmp_path / "out")
    monkeypatch.setenv("PATH", str(_dir(tmp_path / "empty-bin")))
    exc = _refusal(repo, out)
    assert exc.code == "invalid_destination" and os.path.realpath(repo) in exc.message


def _fake_git(returncode: int, stdout: bytes = b"") -> Any:
    def run(root: pathlib.Path, args: list[str]) -> Any:
        return subprocess.CompletedProcess(args, returncode, stdout, b"")
    return run


def _timeout(root: pathlib.Path, args: list[str]) -> Any:
    raise subprocess.TimeoutExpired(args, 5)


@needs_git
@pytest.mark.parametrize("seam", [_fake_git(128), _timeout, _fake_git(0, b"")],
                         ids=["non-zero", "timeout", "empty"])
def test_listing_failures_refuse(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
                                 seam: Any) -> None:
    repo = _repo(tmp_path / "repo")
    out = _dir(tmp_path / "out")
    monkeypatch.setattr(view, "_git_run", seam)
    exc = _refusal(repo, out)
    assert exc.code == "invalid_destination" and os.path.realpath(repo) in exc.message


@needs_git
def test_listing_of_another_repository_refuses(tmp_path: pathlib.Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path / "repo")
    other = _repo(tmp_path / "other")
    out = _dir(tmp_path / "out")
    listing = f"worktree {os.path.realpath(other)}\0HEAD abc\0branch refs/heads/main\0\0"
    monkeypatch.setattr(view, "_git_run", _fake_git(0, listing.encode()))
    exc = _refusal(repo, out)
    assert exc.code == "invalid_destination"


@needs_git
def test_inherited_git_dir_cannot_redirect_the_listing(tmp_path: pathlib.Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    main = _repo(tmp_path / "main")
    first, second = tmp_path / "wt1", tmp_path / "wt2"
    _git(main, "worktree", "add", "-q", str(first))
    _git(main, "worktree", "add", "-q", str(second))
    unrelated = _repo(tmp_path / "unrelated")
    monkeypatch.setenv("GIT_DIR", str(unrelated / ".git"))
    _refused_naming(first, _dir(second / "docs"), second)


@needs_git
def test_linked_worktree_of_separate_git_dir_repo_accepts_main_checkout(
    tmp_path: pathlib.Path,
) -> None:
    """Pins the accepted limit: Git records the git directory, not the checkout."""
    main = tmp_path / "main"
    _repo(main, "--separate-git-dir", str(tmp_path / "sep.git"))
    linked = tmp_path / "wt"
    _git(main, "worktree", "add", "-q", str(linked))
    target = view.validate_destination(linked, str(_dir(main / "docs")), None)
    assert target.directory == os.path.realpath(main / "docs")


def test_git_calls_are_hardened(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> Any:
        seen.update(argv=argv, **kwargs)
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setenv("GIT_DIR", "/unrelated")
    monkeypatch.setattr(view.subprocess, "run", fake_run)
    view._git_run(tmp_path, ["worktree", "list"])
    assert seen["argv"][:7] == ["git", "-C", str(tmp_path), "-c", "core.fsmonitor=false",
                                "-c", "protocol.allow=never"]
    assert seen["shell"] is False and seen["timeout"] == 5
    assert seen["capture_output"] is True
    git_vars = {k: v for k, v in seen["env"].items() if k.startswith("GIT_")}
    assert git_vars == {"GIT_TERMINAL_PROMPT": "0"}


# ---------------------------------------------------------------------------
# AC-0016: case variants
# ---------------------------------------------------------------------------


def _case_insensitive(directory: pathlib.Path) -> bool:
    probe = _dir(directory / "CaseProbe")
    return (directory / "caseprobe").exists() and probe.exists()


def test_case_variant_of_a_contained_directory_is_refused(tmp_path: pathlib.Path) -> None:
    if not _case_insensitive(tmp_path):
        pytest.skip("the temporary file system is case sensitive")
    root = _dir(tmp_path / "Root")
    _dir(root / "Inner")
    variant = tmp_path / "root" / "inner"
    exc = _refusal(root, variant)
    assert exc.code == "invalid_destination"


# ---------------------------------------------------------------------------
# AC-0017 / AC-0018: name and existing entries
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", ["a/b.html", "x.htm", ".x.html", "a" * 101 + ".html", "a\\b.html", "x.html\n", ""],
)
def test_bad_names_are_refused(tmp_path: pathlib.Path, bad: str) -> None:
    out = _dir(tmp_path / "out")
    root = _dir(tmp_path / "root")
    assert _refusal(root, out, bad).code == "invalid_destination"
    assert list(out.iterdir()) == []


def test_a_valid_name_with_hundred_character_stem_is_accepted(tmp_path: pathlib.Path) -> None:
    out = _dir(tmp_path / "out")
    name = "a" * 99 + ".html"
    assert view.validate_destination(_dir(tmp_path / "root"), str(out), name).name == name


@pytest.mark.parametrize("kind", ["file", "dir", "symlink"])
def test_existing_entry_is_left_unchanged(tmp_path: pathlib.Path, kind: str) -> None:
    out = _dir(tmp_path / "out")
    entry = out / "x.html"
    if kind == "file":
        entry.write_bytes(b"old")
        os.utime(entry, (1_000_000, 1_000_000))
    elif kind == "dir":
        entry.mkdir()
    else:
        entry.symlink_to(tmp_path / "nowhere")
    before = os.lstat(entry)
    exc = _refusal(_dir(tmp_path / "root"), out, "x.html")
    assert exc.code == "destination_exists"
    after = os.lstat(entry)
    assert (before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size)
    if kind == "file":
        assert entry.read_bytes() == b"old"


# ---------------------------------------------------------------------------
# AC-0019 .. AC-0022: publication
# ---------------------------------------------------------------------------


def _target(tmp_path: pathlib.Path, name: str = "view.html") -> Any:
    out = _dir(tmp_path / "out")
    return view.validate_destination(_dir(tmp_path / "root"), str(out), name)


def test_published_file_is_regular_single_link_and_private(tmp_path: pathlib.Path) -> None:
    path = view.publish("<p>é</p>", _target(tmp_path))
    st = os.lstat(path)
    assert path.read_bytes() == "<p>é</p>".encode()
    assert (st.st_mode & 0o777, st.st_nlink) == (0o600, 1)
    assert sorted(p.name for p in path.parent.iterdir()) == ["view.html"]


@pytest.mark.parametrize("stage", ["write", "fsync", "link"])
def test_failures_leave_the_directory_unchanged(tmp_path: pathlib.Path,
                                                monkeypatch: pytest.MonkeyPatch,
                                                stage: str) -> None:
    target = _target(tmp_path)
    out = pathlib.Path(target.directory)
    (out / "keep.txt").write_text("k")
    before = sorted(p.name for p in out.iterdir())

    def boom(*_a: Any, **_k: Any) -> Any:
        raise OSError("injected")

    monkeypatch.setattr(os, {"write": "write", "fsync": "fsync", "link": "link"}[stage], boom)
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish("<p>x</p>", target)
    assert caught.value.code == "publish_failed"
    assert sorted(p.name for p in out.iterdir()) == before


@pytest.mark.parametrize("replacement", ["directory", "symlink"])
def test_swapped_destination_directory_writes_nothing(tmp_path: pathlib.Path,
                                                      monkeypatch: pytest.MonkeyPatch,
                                                      replacement: str) -> None:
    target = _target(tmp_path)
    directory = pathlib.Path(target.directory)
    moved = tmp_path / "moved"
    elsewhere = _dir(tmp_path / "elsewhere")
    real_open = os.open

    def swapping_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        if str(path) == target.directory and "dir_fd" not in kwargs:
            directory.rename(moved)
            if replacement == "directory":
                directory.mkdir()
            else:
                directory.symlink_to(elsewhere)
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swapping_open)
    # The wrapper stands in for os.open, so it must count as dir_fd-capable too.
    monkeypatch.setattr(os, "supports_dir_fd", {*os.supports_dir_fd, swapping_open})
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish("<p>x</p>", target)
    assert caught.value.code == "publish_failed"
    assert list(moved.iterdir()) == [] and list(elsewhere.iterdir()) == []
    if replacement == "directory":
        assert list(directory.iterdir()) == []


def test_directory_replaced_after_the_temporary_file_links_nothing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The directory is swapped after the temp file exists; the pre-link re-check must refuse."""
    target = _target(tmp_path)
    directory = pathlib.Path(target.directory)
    moved = tmp_path / "moved"
    real_fsync = os.fsync

    def swapping_fsync(fd: int) -> None:
        real_fsync(fd)
        directory.rename(moved)
        directory.mkdir()

    monkeypatch.setattr(os, "fsync", swapping_fsync)
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish("<p>x</p>", target)
    assert caught.value.code == "publish_failed"
    assert list(moved.iterdir()) == [] and list(directory.iterdir()) == []


def test_entry_created_after_validation_is_refused_and_left_unchanged(
    tmp_path: pathlib.Path,
) -> None:
    """A name taken between validation and linking is destination_exists, not publish_failed."""
    target = _target(tmp_path)
    entry = pathlib.Path(target.directory) / target.name
    entry.write_bytes(b"raced")
    before = os.lstat(entry)
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish("<p>x</p>", target)
    assert caught.value.code == "destination_exists"
    after = os.lstat(entry)
    assert entry.read_bytes() == b"raced"
    assert (before.st_mtime_ns, before.st_size) == (after.st_mtime_ns, after.st_size)
    assert [p.name for p in entry.parent.iterdir()] == [target.name]


@pytest.mark.parametrize("stage", ["create_temp", "write", "link"])
def test_publish_failed_names_the_stage_and_errno_without_a_path(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    target = _target(tmp_path)
    real_open = os.open

    def deny(*_a: Any, **_k: Any) -> Any:
        raise OSError(errno.ENOSPC, "no space")

    if stage == "create_temp":
        def failing_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            if "dir_fd" in kwargs:
                deny()
            return real_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(os, "open", failing_open)
        monkeypatch.setattr(os, "supports_dir_fd", {*os.supports_dir_fd, failing_open})
    else:
        monkeypatch.setattr(os, "write" if stage == "write" else "link", deny)
        # The stand-in must count as dir_fd-capable, or the platform check refuses first.
        monkeypatch.setattr(os, "supports_dir_fd", {*os.supports_dir_fd, deny})
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish("<p>x</p>", target)
    assert caught.value.code == "publish_failed"
    assert caught.value.observed == {"stage": stage, "errno": "ENOSPC"}
    assert target.directory not in json.dumps(caught.value.observed)


@pytest.mark.parametrize("missing", ["supports_dir_fd", "O_NOFOLLOW", "O_DIRECTORY"])
def test_platform_without_required_support_refuses(tmp_path: pathlib.Path,
                                                   monkeypatch: pytest.MonkeyPatch,
                                                   missing: str) -> None:
    target = _target(tmp_path)
    if missing == "supports_dir_fd":
        monkeypatch.setattr(os, "supports_dir_fd", set())
    else:
        monkeypatch.delattr(os, missing)
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish("<p>x</p>", target)
    assert caught.value.code == "publish_failed"
    assert list(pathlib.Path(target.directory).iterdir()) == []


def test_over_budget_refuses_with_limits_and_writes_nothing(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    html = "<p>é</p>"
    size = len(html.encode("utf-8"))
    monkeypatch.setattr(view, "EXPORT_BUDGET_BYTES", size - 1)
    target = _target(tmp_path)
    with pytest.raises(view.ViewRefusal) as caught:
        view.publish(html, target)
    exc = caught.value
    assert exc.code == "export_too_large"
    assert exc.limits == {"budget_bytes": size - 1, "bounded_route": "--from"}
    assert exc.observed == {"bytes": size}
    assert list(pathlib.Path(target.directory).iterdir()) == []


def test_budget_constant() -> None:
    assert view.EXPORT_BUDGET_BYTES == 104_857_600
