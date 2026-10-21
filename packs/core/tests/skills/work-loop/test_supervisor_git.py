"""The supervisor's hardened Git helper and the admission check on Git settings.

VI-5010 (AC-0009), VI-5011 (AC-0010, AC-0011), VI-5012 (AC-0012). Every test
uses a real temporary repository; a marker file proves a planted command ran.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="marker scripts are POSIX shell")

RUN = "run-0123456789abcdef"
SECRET = "s3cr3t-value-never-echoed"


def _script(directory: Path, name: str, marks: Path, body: str = "") -> str:
    """An executable that leaves ``marks/<name>`` behind, then runs *body*."""
    path = directory / f"{name}.sh"
    path.write_text(f"#!/bin/sh\n: > '{marks / name}'\n{body}", encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def _config(repo: Path, *pairs: str) -> None:
    for key, value in zip(pairs[::2], pairs[1::2], strict=True):
        h.git(repo, "config", "--local", key, value)


def _global_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> Path:
    """Point the harness's pinned global config at a file holding *text*."""
    path = tmp_path / "global.gitconfig"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setitem(h.GIT_ENV, "GIT_CONFIG_GLOBAL", str(path))
    return path


# ── VI-5010: start refuses a Git setting that runs code ─────────────────────

_CODE_RUNNING = [
    "filter.x.clean",
    "filter.x.smudge",
    "filter.x.process",
    "diff.x.textconv",
    "diff.x.command",
    "diff.external",
    "core.sshCommand",
    "core.fsmonitor",
    "core.hooksPath",
    "gpg.program",
    "gpg.openpgp.program",
    "gpg.ssh.defaultKeyCommand",
    "include.path",
    "includeIf.gitdir:/never/.path",
    "tool.unlisted.command",
    "tool.unlisted.program",
]


def _refusal(out: dict[str, Any]) -> dict[str, str]:
    return out["refusal"]


def _start_refuses(repo: Path, key: str) -> None:
    before = h.git(repo, "rev-parse", "HEAD")
    code, out = h.start(repo)
    assert code == 1, out
    refusal = _refusal(out)
    assert refusal["code"] == "unsupported-git-config"
    assert key.lower() in refusal["detail"].lower()
    assert SECRET not in json.dumps(out)
    assert h.git(repo, "rev-parse", "HEAD") == before


@pytest.mark.parametrize("key", ["gpg.ssh.defaultKeyCommand", "tool.unlisted.command"])
def test_start_refuses_a_code_running_key_in_repository_config(tmp_path: Path, key: str) -> None:
    repo = h.make_repo(tmp_path)
    _config(repo, key, SECRET)
    _start_refuses(repo, key)


def test_every_listed_code_running_key_is_refused_by_name_never_by_value(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    for key in _CODE_RUNNING:
        _config(repo, key, SECRET)
        with pytest.raises(h.admission.Refusal) as caught:
            h.admission.check_git_config(h.workspace(repo))
        refusal = caught.value
        assert refusal.code == "unsupported-git-config", key
        assert key.lower() in refusal.detail.lower(), key
        assert SECRET not in refusal.detail, key
        h.git(repo, "config", "--local", "--unset-all", key)
    h.admission.check_git_config(h.workspace(repo))


def test_start_refuses_a_code_running_key_in_worktree_config(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    h.git(repo, "config", "--local", "extensions.worktreeConfig", "true")
    h.git(repo, "config", "--worktree", "core.fsmonitor", SECRET)
    code, out = h.start(repo)
    assert code == 1, out
    assert _refusal(out)["code"] == "unsupported-git-config"
    assert "core.fsmonitor" in _refusal(out)["detail"]
    assert SECRET not in json.dumps(out)


def test_a_boolean_fsmonitor_runs_no_program_and_does_not_refuse(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    _config(repo, "core.fsmonitor", "false")
    code, out = h.start(repo)
    assert code == 0, out


_LFS = '[filter "lfs"]\n\tclean = git-lfs clean -- %f\n\tsmudge = git-lfs smudge -- %f\n'


def _attributes(repo: Path, where: str, line: str) -> None:
    if where == "root":
        target = repo / ".gitattributes"
    elif where == "nested":
        target = repo / "assets" / "deep" / ".gitattributes"
    else:
        target = repo / ".git" / "info" / "attributes"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(line + "\n", encoding="utf-8")


@pytest.mark.parametrize("where", ["root", "nested", "info"])
def test_start_refuses_a_global_filter_that_an_attributes_file_uses(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, where: str) -> None:
    repo = h.make_repo(tmp_path)
    _global_config(tmp_path, monkeypatch, _LFS)
    _attributes(repo, where, "*.bin filter=lfs diff=lfs merge=lfs -text")
    code, out = h.start(repo)
    assert code == 1, out
    refusal = _refusal(out)
    assert refusal["code"] == "unsupported-git-config"
    assert "filter.lfs" in refusal["detail"]
    assert "git-lfs" not in json.dumps(out)


def test_start_refuses_a_global_filter_kept_under_xdg_config_home(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    xdg_config = tmp_path / "xdg" / "git" / "config"
    xdg_config.parent.mkdir(parents=True)
    xdg_config.write_text(_LFS, encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.delitem(h.GIT_ENV, "GIT_CONFIG_GLOBAL")
    monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config.parent.parent))
    _attributes(repo, "root", "*.bin filter=lfs -text")
    code, out = h.start(repo)
    assert code == 1, out
    assert _refusal(out)["code"] == "unsupported-git-config"
    assert "filter.lfs" in _refusal(out)["detail"]


def _security_reasons(repo: Path) -> list[str]:
    path = h.workspace(repo).local.security_events
    if not path.exists():
        return []
    return [json.loads(line)["reason_code"] for line in path.read_text().splitlines()]


def test_an_unreadable_config_refuses_and_writes_a_security_event(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    _global_config(tmp_path, monkeypatch, "[unterminated\n")
    code, out = h.start(repo)
    assert code == 1, out
    assert _refusal(out)["code"] == "denied-git-failed"
    assert _security_reasons(repo) == ["denied-git-failed"]


def test_a_verified_config_refusal_writes_no_security_event(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    _config(repo, "core.sshCommand", SECRET)
    _start_refuses(repo, "core.sshCommand")
    assert _security_reasons(repo) == []


def test_the_store_refuses_a_run_id_that_is_not_a_run_id(tmp_path: Path) -> None:
    repo, _run_id = _started(tmp_path)
    git = h.workspace(repo).git
    for bad in ("../escape", "run-0123456789abcdef/../x", "run-XYZ"):
        with pytest.raises(h.commit_module.SupervisorGitError) as caught:
            git.record_made(bad, "0" * 40)
        assert caught.value.code == "denied-invalid-run-id"
        with pytest.raises(h.commit_module.SupervisorGitError):
            git.made_commits(bad)
    assert not (tmp_path / "x").exists()


def test_a_global_filter_that_no_attribute_uses_does_not_refuse(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    _global_config(tmp_path, monkeypatch, _LFS)
    code, out = h.start(repo)
    assert code == 0, out
    _attributes(repo, "root", "*.bin filter=other\n*.txt -filter")
    code, out = h.start(repo)
    assert code == 0, out


# ── VI-5011: no planted code runs during any supervisor git call ────────────


def _plant(tmp_path: Path, repo: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Plant every code-running setting the helper must neutralize; return the marks dir."""
    marks = tmp_path / "marks"
    marks.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()

    def script(name: str, body: str = "") -> str:
        return _script(bin_dir, name, marks, body)

    for hook in ("reference-transaction", "post-index-change", "pre-commit", "commit-msg",
                 "post-commit", "fsmonitor-watchman"):
        hooks = repo / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        target = hooks / hook
        target.write_text(f"#!/bin/sh\n: > '{marks / ('hook-' + hook)}'\n", encoding="utf-8")
        target.chmod(0o755)
    other_hooks = tmp_path / "other-hooks"
    other_hooks.mkdir()
    for hook in ("reference-transaction", "post-index-change"):
        target = other_hooks / hook
        target.write_text(f"#!/bin/sh\n: > '{marks / ('hookspath-' + hook)}'\n", encoding="utf-8")
        target.chmod(0o755)
    included = tmp_path / "included.gitconfig"
    included.write_text(
        f"[core]\n\tfsmonitor = {script('include-fsmonitor')}\n"
        f"\thooksPath = {other_hooks}\n[diff]\n\texternal = {script('include-extdiff')}\n",
        encoding="utf-8",
    )
    _config(
        repo,
        "core.fsmonitor", script("fsmonitor"),
        "core.hooksPath", str(other_hooks),
        "filter.m.clean", script("filter-clean", "cat\n"),
        "filter.m.smudge", script("filter-smudge", "cat\n"),
        "filter.m.process", script("filter-process"),
        "filter.m.required", "true",
        "diff.m.textconv", script("textconv", 'cat "$1"\n'),
        "diff.m.command", script("diff-command"),
        "diff.external", script("extdiff"),
        "commit.gpgSign", "true",
        "tag.gpgSign", "true",
        "gpg.format", "ssh",
        "user.signingKey", "key",
        "gpg.ssh.program", script("ssh-sign"),
        "gpg.program", script("gpg"),
        "gpg.ssh.defaultKeyCommand", script("ssh-key"),
        "core.sshCommand", script("ssh"),
        "include.path", str(included),
    )
    (repo / ".gitattributes").write_text("* filter=m diff=m\n", encoding="utf-8")
    global_text = (
        f"[core]\n\tfsmonitor = {script('global-fsmonitor')}\n\thooksPath = {other_hooks}\n"
        f'[filter "g"]\n\tclean = {script("global-filter", "cat" + chr(10))}\n'
    )
    _global_config(tmp_path, monkeypatch, global_text)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.fsmonitor")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", script("env-fsmonitor"))
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", script("env-extdiff"))
    return marks


@posix_only
def test_planted_code_runs_nothing_during_any_supervisor_git_call(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "README.md").write_text("base\nmore\n", encoding="utf-8")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    marks = _plant(tmp_path, repo, monkeypatch)
    ws = h.workspace(repo)
    with h.git_identity():
        assert ws.git.change_set() == [".gitattributes", "README.md", "new.txt"]
        made = ws.git.build_commit(
            run_id=RUN, step="probe:1", operation="replan", paths=["README.md", "new.txt"]
        )
        assert made is not None
        assert [c.step for c in ws.git.supervisor_commits(RUN)] == ["probe:1"]
        ws.git.run("log", "-p", "-2")
        ws.git.run("diff", "HEAD~1", "HEAD")
        ws.git.run("diff-tree", "-p", "--root", "HEAD")
        ws.git.run("archive", "--format=tar", "HEAD")
    assert sorted(p.name for p in marks.iterdir()) == []


@posix_only
def test_carried_autocrlf_stages_the_bytes_plain_git_add_stages(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _global_config(tmp_path, monkeypatch, "[core]\n\tautocrlf = true\n")
    repo = h.make_repo(tmp_path)
    body = b"one\r\ntwo\r\n"
    (repo / "crlf.txt").write_bytes(body)
    ws = h.workspace(repo)
    with h.git_identity():
        made = ws.git.build_commit(
            run_id=RUN, step="probe:crlf", operation="replan", paths=["crlf.txt"]
        )
    assert made is not None
    plain = tmp_path / "plain"
    subprocess.run(["git", "init", "-q", str(plain)], check=True, env={**os.environ, **h.GIT_ENV})
    (plain / "crlf.txt").write_bytes(body)
    env = {**os.environ, **h.GIT_ENV, "GIT_CONFIG_GLOBAL": str(config)}
    subprocess.run(["git", "add", "crlf.txt"], cwd=plain, check=True, env=env)
    expected = subprocess.run(
        ["git", "rev-parse", ":crlf.txt"], cwd=plain, check=True, env=env,
        capture_output=True, text=True,
    ).stdout.strip()
    staged = h.git(repo, "rev-parse", f"{made}:crlf.txt").strip()
    assert staged == expected
    assert ws.git.show("crlf.txt", made) == b"one\ntwo\n"


# ── VI-5012: forged history is never read as a supervisor commit ────────────


def _started(tmp_path: Path) -> tuple[Path, str]:
    repo = h.make_repo(tmp_path)
    code, out = h.start(repo)
    assert code == 0, out
    return repo, out["run_id"]


def _view(repo: Path, run_id: str) -> list[tuple[str, str]]:
    commits = h.workspace(repo).git.supervisor_commits(run_id)
    return [(c.sha, c.step) for c in commits]


def _forged(repo: Path, run_id: str, parent: str | None, step: str) -> str:
    """A commit that claims to be the supervisor's *step* of *run_id*."""
    tree = h.git(repo, "rev-parse", "HEAD^{tree}").strip()
    message = f"forged\n\nSupervisor-Run: {run_id}\nSupervisor-Step: {step}\n"
    message += "Supervisor-Operation: replan\n"
    args = ["commit-tree", tree, *(["-p", parent] if parent else [])]
    return subprocess.run(
        ["git", *args], cwd=repo, env={**os.environ, **h.GIT_ENV}, input=message,
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def test_a_replaced_supervisor_commit_is_read_as_the_original(tmp_path: Path) -> None:
    repo, run_id = _started(tmp_path)
    before = _view(repo, run_id)
    original = before[0][0]
    fake = _forged(repo, run_id, h.git(repo, "rev-parse", "HEAD^").strip(), "forged:replace")
    h.git(repo, "replace", original, fake)
    assert _view(repo, run_id) == before


def test_a_graft_is_never_read(tmp_path: Path) -> None:
    repo, run_id = _started(tmp_path)
    before = _view(repo, run_id)
    orphan = _forged(repo, run_id, None, "forged:graft")
    head = h.git(repo, "rev-parse", "HEAD").strip()
    (repo / ".git" / "info" / "grafts").write_text(f"{head} {orphan}\n", encoding="utf-8")
    try:
        after = _view(repo, run_id)
    except h.commit_module.SupervisorGitError as exc:
        assert exc.code == "denied-git-control-state"
    else:
        assert after == before


def test_a_message_preserving_rebase_still_reads_the_supervisor_commits(tmp_path: Path) -> None:
    repo, run_id = _started(tmp_path)
    before = _view(repo, run_id)
    root = h.git(repo, "rev-list", "--max-parents=0", "HEAD").strip()
    h.git(repo, "checkout", "-q", "-b", "upstream", root)
    (repo / "OTHER.md").write_text("upstream\n", encoding="utf-8")
    h.git(repo, "add", "OTHER.md")
    h.git(repo, "commit", "-q", "-m", "unrelated upstream change")
    h.git(repo, "checkout", "-q", "main")
    h.git(repo, "rebase", "-q", "upstream")
    after = _view(repo, run_id)
    assert [step for _sha, step in after] == [step for _sha, step in before]
    assert [sha for sha, _step in after] != [sha for sha, _step in before]
