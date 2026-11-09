"""Attempt directories and their ingestion into a Git tree.

Every test uses a real temporary repository. The refusals are checked from the
listing, so each one also asserts that the object store did not grow.
"""

from __future__ import annotations

import importlib.util
import os
import socket
import stat
import sys
import tracemalloc
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_HERE = Path(__file__).resolve().parent
_SCRIPTS = _HERE.parents[2] / ".apm" / "skills" / "work-loop" / "scripts"
_HELPER_PATHS = {
    "supervisor_harness": _HERE / "supervisor_harness.py",
    "supervisor_support": _HERE / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


def _concurrency() -> ModuleType:
    alias = "core_work_loop_supervisor_concurrency_ingestion"
    spec = importlib.util.spec_from_file_location(alias, str(_SCRIPTS / "_supervisor_concurrency.py"))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")
ing = _concurrency()
pytestmark = sup.INTEGRATION  # every test here drives real Git

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="attempt directories are POSIX")
TRUSTED = "docs/adr/0001-calculators-answer.md"
EXCLUDED = (f"{h.SPEC_DIR}/.supervisor/", ".loop-run/", f"{h.SPEC_DIR}/delivery/")
PROTECTED = ("delivery", f"{h.SPEC_DIR}/delivery")


class Rig:
    """A repository, its hardened Git helper, the source commit, and one attempt directory."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.repo = h.make_repo(tmp_path)
        self.git = h.workspace(self.repo).git.hardened
        self.source = h.git(self.repo, "rev-parse", "HEAD").strip()
        self.dir = ing.create_attempt_directory(
            self.git, self.source, parent=self.mkparent()
        )

    def mkparent(self) -> Path:
        parent = self.tmp / "attempts"
        parent.mkdir(exist_ok=True)
        return parent

    def write(self, rel: str, data: bytes | str = b"x\n") -> Path:
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)
        return path

    def link(self, rel: str, target: str) -> None:
        path = self.dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        Path(path).symlink_to(target)

    def loose(self) -> int:
        out = h.git(self.repo, "count-objects", "-v")
        return int(next(line for line in out.splitlines() if line.startswith("count:")).split()[1])

    def ingest(self, **kw: Any) -> Any:
        kw.setdefault("trusted_paths", (TRUSTED,))
        kw.setdefault("protected_prefixes", PROTECTED)
        kw.setdefault("excluded_prefixes", EXCLUDED)
        kw.setdefault("product_root", str(self.repo))
        return ing.ingest_attempt_directory(self.git, self.dir, source=self.source, **kw)

    def refused(self, code: str, **kw: Any) -> Any:
        """Ingest, expect *code*, and assert the object store did not grow."""
        before = self.loose()
        with pytest.raises(ing.AttemptRefused) as caught:
            self.ingest(**kw)
        assert caught.value.code == code, caught.value
        assert self.loose() == before, "a refused attempt must write no object"
        return caught.value

    def tree(self, tree: str) -> dict[str, tuple[str, str]]:
        out = h.git(self.repo, "ls-tree", "-r", "--full-tree", tree)
        found = {}
        for line in out.splitlines():
            meta, _, path = line.partition("\t")
            mode, _kind, oid = meta.split()
            found[path] = (mode, oid)
        return found


@pytest.fixture
def rig(tmp_path: Path) -> Rig:
    return Rig(tmp_path)


# ── attempt directory ───────────────────────────────────────────────────────


@posix_only
def test_attempt_directory_is_a_fresh_plain_directory_outside_every_protected_place(
    tmp_path: Path,
) -> None:
    repo = h.make_repo(tmp_path)
    git = h.workspace(repo).git.hardened
    source = h.git(repo, "rev-parse", "HEAD").strip()
    first = ing.create_attempt_directory(git, source)
    second = ing.create_attempt_directory(git, source)
    try:
        assert first != second
        for made in (first, second):
            assert made.name.startswith("agentbundle-attempt-")
            assert stat.S_IMODE(made.stat().st_mode) == 0o700
            assert not (made / ".git").exists() and not os.path.lexists(made / ".git")
            for protected in (git.pins.git_dir, git.pins.common_dir, git.pins.root):
                resolved = Path(os.path.realpath(protected))
                assert resolved != made and resolved not in made.parents
                assert made not in resolved.parents
            assert (made / "README.md").read_text() == "base\n"
            assert (made / ".gitignore").is_file()
        git.verify_control_state()
    finally:
        ing.remove_attempt_directory(first)
        ing.remove_attempt_directory(second)


@posix_only
@pytest.mark.parametrize("where", ["work-tree", "git-dir", "run-store"])
def test_attempt_directory_refuses_a_protected_location_and_leaves_nothing(
    tmp_path: Path, where: str
) -> None:
    repo = h.make_repo(tmp_path)
    git = h.workspace(repo).git.hardened
    source = h.git(repo, "rev-parse", "HEAD").strip()
    parent = {
        "work-tree": repo / "inside",
        "git-dir": repo / ".git" / "inside",
        "run-store": tmp_path / "store",
    }[where]
    parent.mkdir(parents=True, exist_ok=True)
    forbidden = [tmp_path / "store"] if where == "run-store" else []
    with pytest.raises(ing.AttemptRefused) as caught:
        ing.create_attempt_directory(git, source, parent=parent, forbidden=forbidden)
    assert caught.value.code == "attempt-location"
    assert list(parent.iterdir()) == []


# ── links and special files ─────────────────────────────────────────────────


@posix_only
def test_a_symbolic_link_is_recorded_as_a_link_and_never_read_through(rig: Rig) -> None:
    secret = rig.tmp / "outside-secret.txt"
    secret.write_text("never ingested\n")
    rig.link("note-link", "README.md")
    rig.link("dangling", "no-such-file")
    result = rig.ingest()
    entries = rig.tree(result.tree)
    for name, target in (("note-link", "README.md"), ("dangling", "no-such-file")):
        mode, oid = entries[name]
        assert mode == "120000"
        assert h.git(rig.repo, "cat-file", "blob", oid) == target
    entry = next(e for e in ing._entries.list_confined_entries(rig.dir) if e.path == "note-link")
    assert entry.kind == "link" and entry.target == "README.md"
    assert "never ingested" not in h.git(rig.repo, "cat-file", "-p", entries["note-link"][1])


@posix_only
def test_a_fifo_is_refused(rig: Rig) -> None:
    os.mkfifo(rig.dir / "pipe")
    assert rig.refused("attempt-special-file").path == "pipe"


@posix_only
def test_a_socket_is_refused(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(rig.dir)  # a relative name keeps the path under the socket length limit
    with socket.socket(socket.AF_UNIX) as sock:
        sock.bind("sock")
        assert rig.refused("attempt-special-file").path == "sock"


@posix_only
def test_a_device_node_is_refused(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    try:
        os.mknod(rig.dir / "dev", stat.S_IFCHR | 0o600, os.makedev(1, 3))
    except PermissionError:
        # A device node needs root to create, so report one file as a device instead.
        (rig.dir / "dev").write_text("stands in for a device\n")
        real = os.stat

        def stat_as_device(path: Any, *args: Any, **kwargs: Any) -> Any:
            found = real(path, *args, **kwargs)
            if path == "dev" and kwargs.get("dir_fd") is not None:
                return os.stat_result((stat.S_IFCHR | 0o600, found.st_ino, found.st_dev, 1, 0, 0, 0, 0, 0, 0))
            return found

        monkeypatch.setattr(ing._entries.os, "stat", stat_as_device)
        # The wrapper is not the function the descriptor-support table lists.
        monkeypatch.setattr(ing._entries, "_require_descriptor_walk", lambda: None)
    assert rig.refused("attempt-special-file").path == "dev"


@posix_only
def test_a_hard_linked_file_is_refused(rig: Rig) -> None:
    os.link(rig.dir / "README.md", rig.dir / "README-twin.md")
    rig.refused("attempt-hard-link")


@posix_only
@pytest.mark.parametrize(
    "name",
    [".git", ".GIT", ".Git", ".g‌it", "git~1", ".git.", ".git ", "sub/.git", "sub/.GIT/config"],
)
def test_a_git_equivalent_name_is_refused_before_any_object_is_written(
    rig: Rig, name: str
) -> None:
    try:
        rig.write(name, "x")
    except OSError:
        pytest.skip("this filesystem cannot create that name")
    rig.refused("attempt-git-name")


LINK_REFUSALS = [
    ("absolute-into-git", "l", "{repo}/.git/config"),
    ("relative-into-git", "a/l", "../.git/config"),
    ("directory-link-into-git", "d", ".git"),
    ("absolute-trusted", "l", "{repo}/" + TRUSTED),
    ("relative-trusted", "a/l", "../" + TRUSTED),
    ("outside-absolute", "l", "/etc/hosts"),
    ("outside-relative", "a/l", "../../outside"),
    ("into-delivery", "l", "delivery/approvals.jsonl"),
    ("into-spec-delivery", "l", f"{h.SPEC_DIR}/delivery/approvals.jsonl"),
]


@posix_only
@pytest.mark.parametrize(("label", "where", "target"), LINK_REFUSALS, ids=[r[0] for r in LINK_REFUSALS])
def test_a_link_that_reaches_git_a_trusted_file_delivery_or_outside_is_refused(
    rig: Rig, label: str, where: str, target: str
) -> None:
    rig.link(where, target.format(repo=rig.repo))
    assert rig.refused("attempt-unsafe-link").path == where


@posix_only
def test_a_link_through_a_directory_link_into_git_is_refused(rig: Rig) -> None:
    rig.link("d", ".git")
    rig.link("x", "d/config")
    assert rig.refused("attempt-unsafe-link").path in {"d", "x"}


@posix_only
def test_a_chain_of_links_into_a_trusted_file_is_refused(rig: Rig) -> None:
    rig.link("l1", "l2")
    rig.link("l2", "l3")
    rig.link("l3", TRUSTED)
    rig.refused("attempt-unsafe-link")


@posix_only
@pytest.mark.parametrize(
    ("tail", "refused"),
    [
        ("delivery/approvals.jsonl", True),
        (TRUSTED, True),
        ("../outside", True),
        ("README.md", False),
    ],
)
def test_the_link_then_dot_dot_pair_resolves_as_the_checked_out_tree_would(
    rig: Rig, tail: str, refused: bool
) -> None:
    # a/b/y resolves to the root-level z, so y/.. is the root, not a/b.
    rig.link("a/b/y", "../../z")
    rig.link("a/b/x", f"y/../{tail}")
    if refused:
        assert rig.refused("attempt-unsafe-link").path == "a/b/x"
    else:
        assert rig.ingest().tree


@posix_only
def test_forty_link_hops_pass_and_forty_one_fail(rig: Rig) -> None:
    for i in range(39):
        rig.link(f"c{i}", f"c{i + 1}")
    rig.link("c39", "README.md")  # c0 .. c39 is forty links
    assert rig.ingest().tree
    rig.link("c40", "README.md")
    Path(rig.dir / "c39").unlink()
    rig.link("c39", "c40")  # now forty-one links
    assert rig.refused("attempt-unsafe-link").path == "c0"


@posix_only
def test_a_link_cycle_is_refused_as_too_many_hops(rig: Rig) -> None:
    rig.link("p", "q")
    rig.link("q", "p")
    rig.refused("attempt-unsafe-link")


@posix_only
def test_a_link_inside_the_tree_to_an_untrusted_file_is_admitted(rig: Rig) -> None:
    rig.link("a/ok", "../README.md")
    assert rig.tree(rig.ingest().tree)["a/ok"][0] == "120000"


# ── caps ────────────────────────────────────────────────────────────────────


def test_more_paths_than_the_cap_is_refused_and_exactly_the_cap_passes(rig: Rig) -> None:
    held = len(ing._entries.list_confined_entries(rig.dir))
    assert rig.ingest(max_paths=held).tree  # exactly at the cap
    rig.write("one-more.txt")
    err = rig.refused("attempt-too-large", max_paths=held)
    assert "paths" in err.detail


def test_more_file_bytes_than_the_cap_is_refused_from_the_listing(rig: Rig) -> None:
    rig.write("big.bin", b"\0" * 5000)
    err = rig.refused("attempt-too-large", max_total_bytes=4096)
    assert "bytes" in err.detail
    assert rig.ingest(max_total_bytes=10**9).tree


def test_the_shipped_caps_are_the_specified_ones() -> None:
    assert ing.MAX_PATHS == 100_000
    assert ing.MAX_TOTAL_BYTES == 10 * 1024**3
    assert ing.GIT_FLOOR == (2, 41)


# ── descriptor reads ────────────────────────────────────────────────────────


@posix_only
def test_a_file_swapped_for_a_link_between_listing_and_read_fails_the_attempt(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = ing._entries.list_confined_entries

    def listing_then_swap(*args: Any, **kwargs: Any) -> Any:
        found = real(*args, **kwargs)
        (rig.dir / "README.md").unlink()
        Path(rig.dir / "README.md").symlink_to(rig.tmp / "elsewhere")
        return found

    (rig.tmp / "elsewhere").write_text("other\n")
    monkeypatch.setattr(ing._entries, "list_confined_entries", listing_then_swap)
    with pytest.raises(ing.AttemptRefused) as caught:
        rig.ingest()
    assert caught.value.code == "attempt-changed"
    assert caught.value.path == "README.md"


@posix_only
def test_a_parent_directory_swapped_for_a_link_between_listing_and_read_fails_the_attempt(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig.write("sub/inner.txt", "inner\n")
    decoy = rig.tmp / "decoy"
    decoy.mkdir()
    (decoy / "inner.txt").write_text("inner\n")
    real = ing._entries.list_confined_entries

    def listing_then_swap(*args: Any, **kwargs: Any) -> Any:
        found = real(*args, **kwargs)
        (rig.dir / "sub").rename(rig.tmp / "moved")
        Path(rig.dir / "sub").symlink_to(decoy)
        return found

    monkeypatch.setattr(ing._entries, "list_confined_entries", listing_then_swap)
    with pytest.raises(ing.AttemptRefused) as caught:
        rig.ingest()
    assert caught.value.code == "attempt-changed"


@posix_only
def test_a_file_replaced_by_another_of_the_same_size_or_grown_after_listing_fails(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = ing._entries.list_confined_entries

    def listing_then_replace(*args: Any, **kwargs: Any) -> Any:
        found = real(*args, **kwargs)
        path = rig.dir / "README.md"
        data = path.read_bytes()
        path.unlink()
        path.write_bytes(data.upper())  # same size, new inode
        return found

    monkeypatch.setattr(ing._entries, "list_confined_entries", listing_then_replace)
    with pytest.raises(ing.AttemptRefused) as caught:
        rig.ingest()
    assert caught.value.code == "attempt-changed"


@posix_only
def test_a_file_that_grows_after_listing_fails(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    real = ing._entries.list_confined_entries

    def listing_then_grow(*args: Any, **kwargs: Any) -> Any:
        found = real(*args, **kwargs)
        with (rig.dir / "README.md").open("ab") as handle:
            handle.write(b"more\n")
        return found

    monkeypatch.setattr(ing._entries, "list_confined_entries", listing_then_grow)
    with pytest.raises(ing.AttemptRefused) as caught:
        rig.ingest()
    assert caught.value.code == "attempt-changed"


@posix_only
def test_a_large_sparse_file_streams_in_bounded_memory(rig: Rig) -> None:
    size = 200 * 1024 * 1024
    with (rig.dir / "sparse.bin").open("wb") as handle:
        handle.truncate(size)
    tracemalloc.start()
    try:
        result = rig.ingest()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    mode, oid = rig.tree(result.tree)["sparse.bin"]
    assert mode == "100644"
    assert int(h.git(rig.repo, "cat-file", "-s", oid)) == size
    assert peak < 16 * 1024 * 1024, f"peak Python allocation was {peak} bytes"


# ── the floor's rules ───────────────────────────────────────────────────────


@posix_only
def test_ingestion_admits_exactly_what_the_floor_change_set_admits(rig: Rig) -> None:
    """Same edits to the live work tree and to the attempt directory give the same changes."""
    h.git(rig.repo, "config", "core.fileMode", "true")
    (rig.repo / "kept.log").write_text("tracked despite the ignore rule\n")
    h.git(rig.repo, "add", "-f", "kept.log")
    h.git(rig.repo, "commit", "-q", "-m", "track an ignored name")
    rig.source = h.git(rig.repo, "rev-parse", "HEAD").strip()
    ing.remove_attempt_directory(rig.dir)
    rig.dir = ing.create_attempt_directory(rig.git, rig.source, parent=rig.mkparent())

    def edit(root: Path) -> None:
        def put(rel: str, data: str, *, mode: int | None = None) -> None:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data)
            if mode is not None:
                path.chmod(mode)

        put("README.md", "changed\n")
        put("kept.log", "tracked and edited\n")
        put("new.txt", "new\n")
        put("tool.sh", "#!/bin/sh\n", mode=0o755)
        put("debug.log", "ignored\n")
        put("pkg/__pycache__/m.pyc", "ignored dir\n")
        put(".loop-run/state", "excluded\n")
        put(f"{h.SPEC_DIR}/.supervisor/s", "excluded\n")
        put(f"{h.SPEC_DIR}/delivery/evidence.jsonl", "excluded\n")
        (root / TRUSTED).unlink()
        Path(root / "alias").symlink_to("README.md")

    edit(rig.repo)
    edit(rig.dir)
    floor = h.workspace(rig.repo).git.working_changes()
    result = rig.ingest()
    out = h.git(rig.repo, "diff-tree", "-r", "--raw", "--no-abbrev", "--no-renames", rig.source, result.tree)
    ingested: dict[str, tuple[str, str] | None] = {}
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        fields = meta.split()
        ingested[path] = None if fields[4] == "D" else (fields[1], fields[3])
    assert ingested == floor
    assert "debug.log" in result.ignored and "pkg/__pycache__/m.pyc" in result.ignored
    assert "kept.log" in result.admitted
    # The excluded directories keep the source's entries rather than vanishing.
    assert f"{h.SPEC_DIR}/spec.md" in rig.tree(result.tree)
    assert "new.txt" in ingested and TRUSTED in ingested and ingested[TRUSTED] is None


def test_an_unchanged_attempt_directory_ingests_to_the_source_tree(rig: Rig) -> None:
    tree = h.git(rig.repo, "rev-parse", f"{rig.source}^{{tree}}").strip()
    assert rig.ingest().tree == tree
