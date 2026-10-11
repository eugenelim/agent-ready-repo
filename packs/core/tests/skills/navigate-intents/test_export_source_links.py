"""Contract tests for the source links in the offline view export.

Git repositories are built with the real ``git`` binary under ``tmp_path``; the author
identity is set only in the setup commands' own environment.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"

_INTENT = """# Feature: {title}

- **Slug:** `alpha`
- **Status:** Draft
- **Level:** feature
- **Owner:** placeholder-owner
- **Parent intent:** none
"""
_SPEC = """# Spec: {title}

- **Status:** draft
"""


def _load(path: pathlib.Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_links_nav")
view = _load(_SCRIPTS / "intent_view.py", "core_navigate_intents_links_view")

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
_SETUP_ENV = {
    **{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    "GIT_AUTHOR_NAME": "Example Author",
    "GIT_AUTHOR_EMAIL": "author@example.invalid",
    "GIT_COMMITTER_NAME": "Example Author",
    "GIT_COMMITTER_EMAIL": "author@example.invalid",
}
_OWNER_REPO = "octo-org/the.repo"


def _git(cwd: pathlib.Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(cwd), "-c", "protocol.file.allow=always", *args],
        env=_SETUP_ENV, capture_output=True, text=True, check=True, timeout=60,
    )
    return done.stdout.strip()


def _write_corpus(base: pathlib.Path, spec_dir: str = "alpha") -> None:
    intents = base / "docs" / "product" / "intents"
    intents.mkdir(parents=True, exist_ok=True)
    (intents / "FEAT-0001-alpha.md").write_text(_INTENT.format(title="Alpha"), encoding="utf-8")
    spec = base / "docs" / "specs" / spec_dir
    spec.mkdir(parents=True, exist_ok=True)
    (spec / "spec.md").write_text(_SPEC.format(title="Alpha"), encoding="utf-8")


def _pushed_repo(tmp_path: pathlib.Path, sub: str = "", spec_dir: str = "alpha",
                 remote_url: str | None = None) -> tuple[pathlib.Path, pathlib.Path]:
    """Return ``(repo, corpus root)`` with a clean pushed HEAD and a local bare origin."""
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], env=_SETUP_ENV, check=True)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], env=_SETUP_ENV, check=True)
    root = repo / sub if sub else repo
    _write_corpus(root, spec_dir)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "corpus")
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "-q", "origin", "main")
    _git(repo, "remote", "set-url", "origin",
         remote_url or f"https://github.com/{_OWNER_REPO}")
    return repo, root


def _links(root: pathlib.Path) -> tuple[dict[str, Any], str | None]:
    nodes = nav.build_view_payload(root, None)["nodes"]
    return view.source_links(root, nodes)


def _export(root: pathlib.Path, tmp_path: pathlib.Path) -> tuple[dict[str, Any], str]:
    dest = tmp_path / "out"
    dest.mkdir(exist_ok=True)
    result, code = nav.run_export(root, str(dest), None)
    assert code == 0, result
    html = pathlib.Path(result["path"]).read_text(encoding="utf-8")
    block = re.search(r'id="intent-data">(.*?)</script>', html, re.S)
    assert block is not None
    return json.loads(block.group(1)), html


def _kinds(links: dict[str, Any]) -> set[str]:
    return {v["kind"] for v in links.values()}


# ---------------------------------------------------------------------------
# AC-0023: recognition
# ---------------------------------------------------------------------------

_REJECTED = [
    "http://github.com/octo-org/repo",
    "file:///tmp/octo-org/repo",
    "javascript:alert(1)//github.com/octo-org/repo",
    "https://gitlab.com/octo-org/repo",
    "https://github.com.example/octo-org/repo",
    "https://user:secret@github.com/octo-org/repo",
    "https://user@github.com/octo-org/repo",
    "https://github.com/../repo",
    "https://github.com/octo-org/..",
    "https://github.com/octo-org/repo/extra",
    "git@github.com.example:octo-org/repo",
    "ssh://git@github.com.example/octo-org/repo",
    "ssh://user:pw@github.com/octo-org/repo",
    "https://github.com/octo-org/repo\nmore",
]


@needs_git
@pytest.mark.parametrize("remote", _REJECTED)
def test_unrecognised_remotes_are_inert(tmp_path: pathlib.Path, remote: str) -> None:
    repo, root = _pushed_repo(tmp_path)
    _git(repo, "remote", "set-url", "origin", remote)
    links, commit = _links(root)
    assert commit is None
    assert links and _kinds(links) == {"inert"}
    assert all("url" not in v for v in links.values())
    payload, html = _export(root, tmp_path)
    assert {v["kind"] for v in payload["source_links"].values()} == {"inert"}
    assert payload["provenance"]["commit"] is None
    assert "octo-org" not in html and "secret" not in html and "gitlab" not in html


@needs_git
def test_missing_remote_is_inert(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path)
    _git(repo, "remote", "remove", "origin")
    links, _ = _links(root)
    assert _kinds(links) == {"inert"}


@needs_git
@pytest.mark.parametrize("remote", [
    "https://github.com/octo-org/repo",
    "https://github.com/octo-org/repo.git",
    "git@github.com:octo-org/repo.git",
    "git@github.com:octo-org/repo",
    "ssh://git@github.com/octo-org/repo.git",
])
def test_recognised_remote_forms(tmp_path: pathlib.Path, remote: str) -> None:
    repo, root = _pushed_repo(tmp_path, remote_url=remote)
    links, commit = _links(root)
    assert commit is not None
    assert all(v["url"].startswith(f"https://github.com/octo-org/repo/blob/{commit}/")
               for v in links.values())


def test_no_git_and_no_enclosing_repository_is_inert(tmp_path: pathlib.Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "plain"
    _write_corpus(root)
    empty = tmp_path / "nobin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    payload, html = _export(root, tmp_path)
    assert {v["kind"] for v in payload["source_links"].values()} == {"inert"}
    # The view script carries the allowlisted prefix itself; no link may.
    assert "github.com" not in json.dumps(payload)


# ---------------------------------------------------------------------------
# AC-0024 / AC-0025 / AC-0026
# ---------------------------------------------------------------------------


@needs_git
def test_clean_pushed_head_gives_commit_links(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD")
    payload, _ = _export(root, tmp_path)
    assert payload["provenance"]["commit"] == head
    assert {v["kind"] for v in payload["source_links"].values()} == {"commit"}
    assert payload["source_links"]["spec:alpha"]["url"] == (
        f"https://github.com/{_OWNER_REPO}/blob/{head}/docs/specs/alpha/spec.md")


def _assert_latest(root: pathlib.Path) -> None:
    links, commit = _links(root)
    assert commit is None
    assert _kinds(links) == {"latest"}
    assert links["spec:alpha"]["url"] == (
        f"https://github.com/{_OWNER_REPO}/blob/HEAD/docs/specs/alpha/spec.md")


@needs_git
def test_modified_spec_gives_latest(tmp_path: pathlib.Path) -> None:
    _, root = _pushed_repo(tmp_path)
    (root / "docs/specs/alpha/spec.md").write_text(_SPEC.format(title="Changed"),
                                                   encoding="utf-8")
    _assert_latest(root)


@needs_git
def test_untracked_spec_gives_latest(tmp_path: pathlib.Path) -> None:
    _, root = _pushed_repo(tmp_path)
    extra = root / "docs/specs/beta"
    extra.mkdir()
    (extra / "spec.md").write_text(_SPEC.format(title="Beta"), encoding="utf-8")
    _assert_latest(root)


@needs_git
def test_ignored_spec_gives_latest(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path)
    (repo / ".gitignore").write_text("docs/specs/beta/\n", encoding="utf-8")
    _git(repo, "add", ".gitignore")
    _git(repo, "commit", "-q", "-m", "ignore")
    _git(repo, "push", "-q", str(tmp_path / "origin.git"), "main:refs/heads/main")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    extra = root / "docs/specs/beta"
    extra.mkdir()
    (extra / "spec.md").write_text(_SPEC.format(title="Beta"), encoding="utf-8")
    _assert_latest(root)


@needs_git
def test_unpushed_commit_gives_latest(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path)
    _git(repo, "commit", "-q", "--allow-empty", "-m", "local only")
    _assert_latest(root)


@needs_git
def test_detached_unpushed_head_gives_latest(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path)
    _git(repo, "checkout", "-q", "--detach")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "detached")
    _assert_latest(root)


@needs_git
def test_head_pushed_only_to_second_remote_gives_latest(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path)
    other = tmp_path / "other.git"
    subprocess.run(["git", "init", "-q", "--bare", str(other)], env=_SETUP_ENV, check=True)
    _git(repo, "commit", "-q", "--allow-empty", "-m", "second")
    _git(repo, "remote", "add", "second", str(other))
    _git(repo, "push", "-q", "second", "main")
    _assert_latest(root)


@needs_git
def test_root_below_top_level_prefixes_link_path(tmp_path: pathlib.Path) -> None:
    repo, root = _pushed_repo(tmp_path, sub="sub/dir")
    head = _git(repo, "rev-parse", "HEAD")
    payload, _ = _export(root, tmp_path)
    links = payload["source_links"]
    assert {v["kind"] for v in links.values()} == {"commit"}
    assert links["spec:alpha"]["url"] == (
        f"https://github.com/{_OWNER_REPO}/blob/{head}/sub/dir/docs/specs/alpha/spec.md")
    assert all("/sub/dir/" in v["url"] for v in links.values())
    (root / "docs/specs/alpha/spec.md").write_text("changed\n", encoding="utf-8")
    links, commit = _links(root)
    assert commit is None
    assert "/blob/HEAD/sub/dir/docs/specs/alpha/spec.md" in links["spec:alpha"]["url"]


# ---------------------------------------------------------------------------
# AC-0027: encoding
# ---------------------------------------------------------------------------


@needs_git
def test_path_segments_are_percent_encoded(tmp_path: pathlib.Path) -> None:
    # The derivation admits only slug-shaped spec directory names, so the special
    # characters ride in the corpus root's directory name, which is part of the link path.
    try:
        _, root = _pushed_repo(tmp_path, sub="a?b#c%d e")
    except OSError:
        pytest.skip("the file system refuses these names")
    links, commit = _links(root)
    assert commit is not None
    assert links["spec:alpha"]["url"].endswith(
        "/blob/" + commit + "/a%3Fb%23c%25d%20e/docs/specs/alpha/spec.md")


def test_encode_path_keeps_only_unreserved() -> None:
    assert view._encode_path("a b/c~d.e-f_g/?#%") == "a%20b/c~d.e-f_g/%3F%23%25"
    assert view._encode_path("é/+") == "%C3%A9/%2B"


# ---------------------------------------------------------------------------
# AC-0072: hardened Git calls
# ---------------------------------------------------------------------------


@needs_git
def test_every_git_call_is_hardened_and_runs_no_repository_program(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, root = _pushed_repo(tmp_path)
    marker = tmp_path / "marker.txt"
    script = tmp_path / "mark.sh"
    script.write_text(f"#!/bin/sh\necho ran >> '{marker}'\ncat\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    _git(repo, "config", "core.fsmonitor", str(script))
    _git(repo, "config", "filter.mark.clean", str(script))
    (repo / ".gitattributes").write_text("docs/** filter=mark\n", encoding="utf-8")
    (root / "docs/specs/alpha/spec.md").write_text("changed\n", encoding="utf-8")

    monkeypatch.setenv("GIT_DIR", str(tmp_path / "nowhere"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "nowhere"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    calls: list[dict[str, Any]] = []
    real_run = subprocess.run

    def recording(argv: Any, *args: Any, **kwargs: Any) -> Any:
        calls.append({"argv": argv, **kwargs})
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", recording)
    payload, _ = _export(root, tmp_path)
    monkeypatch.undo()

    assert not marker.exists()
    assert {v["kind"] for v in payload["source_links"].values()} == {"latest"}
    verbs = [c["argv"][c["argv"].index("protocol.allow=never") + 1] for c in calls]
    assert {"config", "rev-parse", "ls-tree", "for-each-ref"} <= set(verbs)
    for call in calls:
        argv = call["argv"]
        assert isinstance(argv, list) and argv[0] == "git"
        assert argv[1] == "--no-lazy-fetch" and argv[2] == "-C" and argv[4:8] == [
            "-c", "core.fsmonitor=false", "-c", "protocol.allow=never"
        ]
        assert call["shell"] is False
        assert call["timeout"] <= 5
        assert call["capture_output"] is True
        env = call["env"]
        assert env["GIT_TERMINAL_PROMPT"] == "0"
        assert [k for k in env if k.startswith("GIT_") and k != "GIT_TERMINAL_PROMPT"] == []


def _treeless_clone(tmp_path: pathlib.Path, name: str) -> tuple[pathlib.Path, pathlib.Path]:
    """Return ``(clone, marker)``: a treeless clone whose promisor upload-pack writes *marker*.

    The clone's ``origin`` URL reads as a GitHub remote, and ``insteadOf`` points real fetches at
    the local bare repository, so a lazy fetch would run the marker-writing program.
    """
    bare = tmp_path / f"{name}-origin.git"
    seed = tmp_path / f"{name}-seed"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], env=_SETUP_ENV, check=True)
    _git(bare, "config", "uploadpack.allowFilter", "true")
    _git(bare, "config", "uploadpack.allowAnySHA1InWant", "true")
    seed.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], env=_SETUP_ENV, check=True)
    _write_corpus(seed)
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "corpus")
    _git(seed, "push", "-q", str(bare), "main")
    clone = tmp_path / f"{name}-clone"
    _git(tmp_path, "clone", "-q", "--filter=tree:0", "--no-checkout", bare.as_uri(), str(clone))
    marker = tmp_path / f"{name}-marker.txt"
    script = tmp_path / f"{name}-upload-pack.sh"
    script.write_text(f"#!/bin/sh\necho ran >> '{marker}'\nexec git-upload-pack \"$@\"\n",
                      encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    _git(clone, "config", "remote.origin.uploadpack", str(script))
    github = f"https://github.com/{_OWNER_REPO}"
    _git(clone, "config", f"url.{bare.as_uri()}.insteadOf", github)
    _git(clone, "remote", "set-url", "origin", github)
    # A per-protocol allow key outranks protocol.allow=never; only --no-lazy-fetch holds.
    _git(clone, "config", "protocol.file.allow", "always")
    _write_corpus(clone)
    return clone, marker


@needs_git
def test_a_treeless_clone_never_starts_a_lazy_fetch(tmp_path: pathlib.Path) -> None:
    # Control: an unhardened Git call on the same fixture does reach the promisor program.
    control, control_marker = _treeless_clone(tmp_path, "control")
    _git(control, "ls-tree", "-r", "HEAD")
    assert control_marker.exists()

    clone, marker = _treeless_clone(tmp_path, "subject")
    payload, _ = _export(clone, tmp_path)
    assert not marker.exists()
    assert {v["kind"] for v in payload["source_links"].values()} == {"latest"}
