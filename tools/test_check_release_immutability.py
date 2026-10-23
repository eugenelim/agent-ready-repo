"""Tests for tools/catalogue/check_release_immutability.py (check 3, tree half).

Every case runs the real check against a throwaway git repository, so each
falsification case mutates a committed release and must turn the check red.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_CAT = Path(__file__).resolve().parent / "catalogue"


def _load(name: str):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, _CAT / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


check = _load("check_release_immutability")

_MEMBER = b'{"$id": "member-0.1"}\n'
_PAGE = b"# Overview 0.1\n"
_NEW_PAGE = b"# Overview 0.1, corrected\n"
_ZERO = "0" * 40


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _release(
    version: str = "0.1",
    *,
    date: str = "2026-01-01",
    adapter: str = "0.18",
    member: bytes = _MEMBER,
    page: bytes = _PAGE,
    page_key: str = "overview.md",
) -> str:
    return (
        f'[[release]]\nversion = "{version}"\ndate = "{date}"\n'
        f'adapter_contract = "{adapter}"\n'
        f'[release.members]\n"m.json" = "{_sha(member)}"\n'
        f'[release.pages]\n"{page_key}" = "{_sha(page)}"\n'
    )


def _correction(date: str, supersedes: str, page: bytes, note: str = "fix") -> str:
    return (
        f'[[correction]]\nversion = "0.1"\ndate = "{date}"\nnote = "{note}"\n'
        f'supersedes = "{supersedes}"\n[correction.pages]\n"overview.md" = "{_sha(page)}"\n'
    )


class Repo:
    """A fixture repository with helpers to write, commit and run the check."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args: str) -> str:
        out = subprocess.run(
            ["git", "-C", str(self.root), *args], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()

    def write(self, rel: str, data: bytes | str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.encode() if isinstance(data, str) else data)

    def manifest(self, *blocks: str) -> None:
        self.write("contracts/catalogue-spec.toml", "\n".join(blocks))

    def snapshot(self, version: str = "0.1", member: bytes = _MEMBER, page: bytes = _PAGE) -> None:
        base = f"contracts/releases/catalogue/{version}"
        self.write(f"{base}/m.json", member)
        self.write(f"{base}/overview.md", page)

    def commit(self, msg: str = "c") -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def run(self, **env: str) -> tuple[int, str]:
        import contextlib
        import io

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = check.main(root=self.root, env=env)
        return code, out.getvalue() + err.getvalue()

    def pr(self, base: str) -> tuple[int, str]:
        self.git("update-ref", "refs/remotes/origin/main", base)
        return self.run(GITHUB_EVENT_NAME="pull_request", GITHUB_BASE_REF="main")


@pytest.fixture()
def repo(tmp_path: Path) -> Repo:
    (tmp_path / "r").mkdir()
    r = Repo(tmp_path / "r")
    r.manifest(_release())
    r.snapshot()
    r.commit("release 0.1")
    return r


def _base(repo: Repo) -> str:
    return repo.git("rev-parse", "HEAD")


def test_head_equal_to_anchor_passes(repo: Repo) -> None:
    code, out = repo.pr(_base(repo))
    assert code == 0, out


def test_adding_release_row_and_snapshot_passes(repo: Repo) -> None:
    base = _base(repo)
    repo.manifest(_release(), _release("0.2", member=b"{}\n", page=b"p\n"))
    repo.snapshot("0.2", b"{}\n", b"p\n")
    repo.commit()
    code, out = repo.pr(base)
    assert code == 0, out


def _mutate_row(repo: Repo, text: str) -> None:
    repo.manifest(text)
    repo.commit("mutate")


@pytest.mark.parametrize(
    "mutation",
    [
        "delete_row",
        "edit_date",
        "edit_adapter",
        "edit_pages_key",
        "edit_member_digest",
        "edit_snapshot_member",
        "delete_snapshot_file",
        "delete_page_file",
    ],
)
def test_released_mutation_fails(repo: Repo, mutation: str) -> None:
    base = _base(repo)
    other = _release("0.2", member=b"{}\n", page=b"p\n")
    if mutation == "delete_row":
        _mutate_row(repo, other)
    elif mutation == "edit_date":
        _mutate_row(repo, _release(date="2026-02-02"))
    elif mutation == "edit_adapter":
        _mutate_row(repo, _release(adapter="0.19"))
    elif mutation == "edit_pages_key":
        repo.write("contracts/releases/catalogue/0.1/other.md", _PAGE)
        _mutate_row(repo, _release(page_key="other.md"))
    elif mutation == "edit_member_digest":
        _mutate_row(repo, _release(member=b"tampered\n"))
    elif mutation == "edit_snapshot_member":
        repo.write("contracts/releases/catalogue/0.1/m.json", b"tampered\n")
        repo.commit("mutate")
    elif mutation == "delete_snapshot_file":
        (repo.root / "contracts/releases/catalogue/0.1/m.json").unlink()
        repo.commit("mutate")
    else:
        (repo.root / "contracts/releases/catalogue/0.1/overview.md").unlink()
        repo.commit("mutate")
    code, out = repo.pr(base)
    assert code == 1, out
    assert "FAIL" in out


def test_snapshot_member_edit_is_never_admitted_by_a_correction(repo: Repo) -> None:
    base = _base(repo)
    repo.write("contracts/releases/catalogue/0.1/m.json", b"tampered\n")
    repo.manifest(_release(), _correction("2026-03-01", "0.1", b"tampered\n"))
    repo.commit()
    code, out = repo.pr(base)
    assert code == 1, out


def _with_correction(repo: Repo) -> str:
    repo.manifest(_release(), _correction("2026-03-01", "0.1", _NEW_PAGE))
    return repo.commit("correction")


def test_page_edit_with_matching_correction_passes(repo: Repo) -> None:
    base = _base(repo)
    repo.write("contracts/releases/catalogue/0.1/overview.md", _NEW_PAGE)
    _with_correction(repo)
    code, out = repo.pr(base)
    assert code == 0, out


def test_page_edit_without_correction_fails(repo: Repo) -> None:
    base = _base(repo)
    repo.write("contracts/releases/catalogue/0.1/overview.md", _NEW_PAGE)
    repo.commit()
    code, out = repo.pr(base)
    assert code == 1, out
    assert "no governing correction" in out


def test_page_edit_with_mismatched_correction_fails(repo: Repo) -> None:
    base = _base(repo)
    repo.write("contracts/releases/catalogue/0.1/overview.md", b"something else\n")
    _with_correction(repo)
    code, out = repo.pr(base)
    assert code == 1, out


def test_deleted_correction_row_fails(repo: Repo) -> None:
    repo.write("contracts/releases/catalogue/0.1/overview.md", _NEW_PAGE)
    base = _with_correction(repo)
    repo.manifest(_release())
    repo.commit("drop correction")
    code, out = repo.pr(base)
    assert code == 1, out
    assert "correction row 0.1 (2026-03-01) was deleted" in out


def test_edited_correction_row_fails(repo: Repo) -> None:
    repo.write("contracts/releases/catalogue/0.1/overview.md", _NEW_PAGE)
    base = _with_correction(repo)
    repo.manifest(_release(), _correction("2026-03-01", "0.1", _NEW_PAGE, note="rewritten"))
    repo.commit("edit correction")
    code, out = repo.pr(base)
    assert code == 1, out
    assert "was edited" in out


def test_superseding_correction_appended_passes(repo: Repo) -> None:
    repo.write("contracts/releases/catalogue/0.1/overview.md", _NEW_PAGE)
    base = _with_correction(repo)
    newer = b"# Overview 0.1, corrected again\n"
    repo.write("contracts/releases/catalogue/0.1/overview.md", newer)
    repo.manifest(
        _release(),
        _correction("2026-03-01", "0.1", _NEW_PAGE),
        _correction("2026-04-01", "2026-03-01", newer),
    )
    repo.commit("supersede")
    code, out = repo.pr(base)
    assert code == 0, out


def test_unreachable_base_fails(repo: Repo) -> None:
    code, out = repo.run(GITHUB_EVENT_NAME="pull_request", GITHUB_BASE_REF="main")
    assert code == 1
    assert "unreachable" in out


def test_no_event_uses_merge_base_and_unreachable_base_fails(repo: Repo) -> None:
    assert repo.run()[0] == 1
    base = _base(repo)
    repo.git("update-ref", "refs/remotes/origin/main", base)
    code, out = repo.run()
    assert code == 0, out
    assert "event=none" in out and base in out


def test_stale_branch_does_not_false_alarm(repo: Repo) -> None:
    cut = _base(repo)
    repo.git("checkout", "-q", "-b", "feature")
    repo.write("unrelated.txt", "x")
    repo.commit("feature work")
    repo.git("checkout", "-q", "main")
    repo.manifest(_release(), _release("0.2", member=b"{}\n", page=b"p\n"))
    repo.snapshot("0.2", b"{}\n", b"p\n")
    main_tip = repo.commit("release 0.2 lands on main")
    repo.git("checkout", "-q", "feature")
    repo.git("update-ref", "refs/remotes/origin/main", main_tip)
    code, out = repo.run(GITHUB_EVENT_NAME="pull_request", GITHUB_BASE_REF="main")
    assert code == 0, out
    assert cut in out  # anchored on the merge base, not on main's tip


def _push(repo: Repo, before: str | None, tmp_path: Path) -> tuple[int, str]:
    payload = tmp_path / "event.json"
    payload.write_text(json.dumps({} if before is None else {"before": before}))
    return repo.run(
        GITHUB_EVENT_NAME="push", GITHUB_REF="refs/heads/main", GITHUB_EVENT_PATH=str(payload)
    )


def test_main_push_tip_mutation_fails(repo: Repo, tmp_path: Path) -> None:
    before = _base(repo)
    repo.write("a.txt", "a")
    repo.commit("benign")
    repo.manifest(_release(date="2026-09-09"))
    repo.commit("mutate in tip")
    code, out = _push(repo, before, tmp_path)
    assert code == 1, out
    assert "event=push" in out and before in out


def test_main_push_earlier_commit_mutation_fails(repo: Repo, tmp_path: Path) -> None:
    before = _base(repo)
    repo.manifest(_release(date="2026-09-09"))
    repo.commit("mutate in earlier commit")
    repo.write("a.txt", "a")
    repo.commit("benign tip")
    # The tip's first parent already carries the mutation, so a first-parent
    # anchor would pass; the pre-push anchor must not.
    repo.git("update-ref", "refs/remotes/origin/main", before)
    assert repo.run(GITHUB_EVENT_NAME="workflow_dispatch")[0] == 0
    code, out = _push(repo, before, tmp_path)
    assert code == 1, out


def test_main_push_clean_passes(repo: Repo, tmp_path: Path) -> None:
    before = _base(repo)
    repo.write("a.txt", "a")
    repo.commit()
    code, out = _push(repo, before, tmp_path)
    assert code == 0, out


@pytest.mark.parametrize("kind", ["absent", "zero", "not_ancestor", "unknown"])
def test_push_fails_closed_without_an_ancestor_anchor(
    repo: Repo, tmp_path: Path, kind: str
) -> None:
    tip_before = _base(repo)
    repo.git("checkout", "-q", "-b", "other", "HEAD~0")
    repo.write("o.txt", "o")
    sibling = repo.commit("sibling")
    repo.git("checkout", "-q", "main")
    repo.write("a.txt", "a")
    repo.commit()
    before = {
        "absent": None,
        "zero": _ZERO,
        "not_ancestor": sibling,
        "unknown": "1" * 40,
    }[kind]
    assert tip_before
    code, out = _push(repo, before, tmp_path)
    assert code == 1, out
    assert "FAIL" in out


def test_push_without_payload_file_fails_closed(repo: Repo) -> None:
    code, _ = repo.run(GITHUB_EVENT_NAME="push", GITHUB_REF="refs/heads/main")
    assert code == 1


def test_workflow_dispatch_takes_first_parent_and_says_so(repo: Repo) -> None:
    parent = _base(repo)
    repo.write("a.txt", "a")
    repo.commit()
    code, out = repo.run(GITHUB_EVENT_NAME="workflow_dispatch")
    assert code == 0, out
    assert "event=workflow_dispatch" in out
    assert f"anchor={parent}" in out
    assert "self-consistency evidence only" in out


def test_other_anchors_are_not_marked_self_consistency(repo: Repo) -> None:
    code, out = repo.pr(_base(repo))
    assert code == 0, out
    assert "event=pull_request" in out and "self-consistency" not in out
