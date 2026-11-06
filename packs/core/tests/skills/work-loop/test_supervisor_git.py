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
import time
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
pytestmark = sup.INTEGRATION  # every test here drives real Git

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


@pytest.mark.parametrize("carried", [True, False], ids=["global-excludes", "none"])
def test_a_global_excludes_file_is_carried_into_the_change_set_read(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, carried: bool) -> None:
    excludes = tmp_path / "global-ignore"
    excludes.write_text("ignored-by-user.txt\n", encoding="utf-8")
    _global_config(tmp_path, monkeypatch,
                   f"[core]\n\texcludesFile = {excludes.as_posix()}\n" if carried else "")
    repo = h.make_repo(tmp_path)
    (repo / "ignored-by-user.txt").write_text("x\n", encoding="utf-8")
    with h.git_identity():
        changed = h.workspace(repo).git.change_set()
    assert ("ignored-by-user.txt" in changed) is not carried


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


# ── control-state comparison: unverifiable versus a verified mismatch ───────

_git_module = h.cli._supervisor("_supervisor_git.py")


@posix_only
def test_a_path_that_cannot_be_stated_is_an_unverifiable_control_check(tmp_path: Path) -> None:
    sealed = tmp_path / "sealed"
    inner = sealed / "repo.git"
    inner.mkdir(parents=True)
    sealed.chmod(0)
    try:
        with pytest.raises(_git_module.SupervisorGitError) as caught:
            _git_module._same(inner, inner)
    finally:
        sealed.chmod(0o700)
    assert caught.value.code == "denied-git-control-state"
    assert caught.value.unverifiable


def test_a_named_path_that_does_not_exist_is_a_verified_mismatch(tmp_path: Path) -> None:
    assert _git_module._same(tmp_path / "missing", tmp_path) is False


# ── VI-5041: a git child's environment is exactly one of the two forms ──────

_BASE_ENV = ("PATH", "HOME", "LANG", "TMPDIR")
_WINDOWS_ENV = ("SYSTEMROOT", "TEMP", "TMP", "PATHEXT", "COMSPEC")
_CONFIG_LOCATION = ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM", "GIT_CONFIG_NOSYSTEM", "XDG_CONFIG_HOME")
_WINDOWS_LOCATION = ("USERPROFILE", "HOMEDRIVE", "HOMEPATH")


def _record_children(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], dict[str, str]]]:
    """Wrap the one process launcher so each git child's argv and environment is kept."""
    seen: list[tuple[list[str], dict[str, str]]] = []
    real = _git_module._launch

    def _recording(argv: list[str], **kwargs: Any) -> Any:
        seen.append((list(argv), dict(kwargs["env"])))
        return real(argv, **kwargs)

    monkeypatch.setattr(_git_module, "_launch", _recording)
    return seen


def _base_from_host() -> dict[str, str]:
    names = _BASE_ENV + (_WINDOWS_ENV if os.name == "nt" else ())
    return {name: os.environ[name] for name in names if name in os.environ}


def _set_ambient(monkeypatch: pytest.MonkeyPatch, script: str) -> None:
    monkeypatch.setenv("GIT_SSH_COMMAND", script)
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", script)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.sshCommand")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", script)


def test_a_helper_call_carries_exactly_the_helper_form(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "README.md").write_text("base\nmore\n", encoding="utf-8")
    ws = h.workspace(repo)
    _set_ambient(monkeypatch, str(tmp_path / "never-run"))
    seen = _record_children(monkeypatch)
    with h.git_identity():
        ws.git.change_set()
        ws.git.run("diff", "HEAD")
        ws.git.run("log", "-1")
        ws.git.build_commit(
            run_id=RUN, step="probe:env", operation="replan", paths=["README.md"]
        )
    helper_calls = [env for argv, env in seen if "--show-scope" not in argv]
    assert len(helper_calls) >= 4
    expected = {**_base_from_host(), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": ""}
    for env in helper_calls:
        # A call that uses the private index additionally carries GIT_INDEX_FILE.
        assert {k: v for k, v in env.items() if k != "GIT_INDEX_FILE"} == expected, env
    assert "GIT_INDEX_FILE" in {k for env in helper_calls for k in env}, "no private-index call seen"


@pytest.mark.parametrize("host_sets_nosystem", [False, True])
def test_an_out_of_helper_config_read_carries_exactly_the_hosts_location_values(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host_sets_nosystem: bool) -> None:
    repo = h.make_repo(tmp_path)
    ws = h.workspace(repo)
    system = tmp_path / "system.gitconfig"
    system.write_text("[user]\n\tname = System Name\n", encoding="utf-8")
    for name in _CONFIG_LOCATION:
        monkeypatch.delitem(h.GIT_ENV, name, raising=False)
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(system))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    if host_sets_nosystem:
        monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    _set_ambient(monkeypatch, str(tmp_path / "never-run"))
    seen = _record_children(monkeypatch)
    entries = ws.git.hardened.config_entries()
    reads = [env for argv, env in seen if "--show-scope" in argv]
    assert len(reads) == 1
    names = _CONFIG_LOCATION + (_WINDOWS_LOCATION if os.name == "nt" else ())
    expected = {
        **_base_from_host(),
        **{name: os.environ[name] for name in names if name in os.environ},
    }
    assert reads[0] == expected
    assert ("GIT_CONFIG_NOSYSTEM" in reads[0]) is host_sets_nosystem
    assert "GIT_CONFIG_GLOBAL" not in reads[0]
    # The read resolves the host's system file unless the host itself hid it.
    sees_system = any(e.key == "user.name" and e.scope == "system" for e in entries)
    assert sees_system is not host_sets_nosystem


# ── VI-5044: a system-scope filter is refused and never runs ────────────────


def _system_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A system-scope filter that leaves a marker; the host reads system config."""
    marks = tmp_path / "marks"
    marks.mkdir()
    clean = _script(tmp_path, "system-filter", marks, "cat\n")
    system = tmp_path / "system.gitconfig"
    system.write_text(f'[filter "sys"]\n\tclean = {clean}\n', encoding="utf-8")
    monkeypatch.delitem(h.GIT_ENV, "GIT_CONFIG_NOSYSTEM")
    monkeypatch.delenv("GIT_CONFIG_NOSYSTEM", raising=False)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(system))
    return marks


@posix_only
def test_start_refuses_a_system_filter_that_an_attributes_file_uses(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    marks = _system_filter(tmp_path, monkeypatch)
    _attributes(repo, "root", "*.bin filter=sys -text")
    code, out = h.start(repo)
    assert code == 1, out
    assert _refusal(out)["code"] == "unsupported-git-config"
    assert "filter.sys" in _refusal(out)["detail"]
    assert sorted(p.name for p in marks.iterdir()) == []


@posix_only
def test_a_system_filter_runs_in_no_helper_call(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    marks = _system_filter(tmp_path, monkeypatch)
    (repo / ".gitattributes").write_text("* filter=sys\n", encoding="utf-8")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    ws = h.workspace(repo)
    with h.git_identity():
        assert "new.txt" in ws.git.change_set()
        assert ws.git.build_commit(
            run_id=RUN, step="probe:sys", operation="replan", paths=[".gitattributes", "new.txt"]
        ) is not None
        ws.git.run("diff", "HEAD~1", "HEAD")
    assert sorted(p.name for p in marks.iterdir()) == []


# ── The helper's environment needs Git 2.32 to honour GIT_CONFIG_GLOBAL ─────


@pytest.mark.parametrize(("banner", "refused"), [
    (b"git version 2.31.8\n", True),
    (b"git version 1.9.0\n", True),
    (b"not a version banner\n", True),
    (b"git version 2.32.0\n", False),
    (b"git version 2.47.1.windows.1\n", False),
    (b"git version 3.0.0\n", False),
])
def test_a_git_older_than_2_32_is_refused_before_discovery(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, banner: bytes, refused: bool) -> None:
    repo = h.make_repo(tmp_path)
    real = _git_module._launch

    def _version_banner(argv: list[str], **kwargs: Any) -> Any:
        if argv[-1:] == ["version"]:
            return subprocess.CompletedProcess(argv, 0, banner, b"")
        return real(argv, **kwargs)

    monkeypatch.setattr(_git_module, "_launch", _version_banner)
    if refused:
        with pytest.raises(_git_module.SupervisorGitError) as caught:
            _git_module.discover(repo)
        assert caught.value.code == "unsupported-git-version"
    else:
        assert _git_module.discover(repo).root == repo.resolve()


def test_every_verb_reports_an_old_git_by_its_own_code(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    real = _git_module._launch

    def _old_git(argv: list[str], **kwargs: Any) -> Any:
        if argv[-1:] == ["version"]:
            return subprocess.CompletedProcess(argv, 0, b"git version 2.31.8\n", b"")
        return real(argv, **kwargs)

    monkeypatch.setattr(_git_module, "_launch", _old_git)
    code, out = h.run_cli(repo, "status", h.SPEC_DIR)
    assert code != 0
    assert "unsupported-git-version" in out["detail"], out
    assert "2.32" in out["detail"], out


# ── the whole-tree scans seed their private index from the work tree's own ──


def _cold_scan(ws: Any) -> tuple[list[str], dict[str, Any]]:
    """The same two scans, each from a ``read-tree HEAD`` index, as the reference answer."""
    port = type(ws.git)
    real = port._private_index
    port._private_index = lambda self, *, warm=False, rehash=(): real(self, warm=False)  # type: ignore[method-assign]
    try:
        return ws.git.change_set(), ws.git.working_changes()
    finally:
        port._private_index = real  # type: ignore[method-assign]


@posix_only
def test_a_warm_scan_reads_no_tree_and_names_what_a_cold_scan_names(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "kept.txt").write_text("kept\n", encoding="utf-8")
    h.git(repo, "add", "kept.txt")
    h.git(repo, "commit", "-q", "-m", "kept")
    # A mix the work tree's index and ``HEAD`` disagree on: staged edit, staged new file,
    # staged removal, a force-staged ignored file, then unstaged edits on top.
    (repo / "README.md").write_text("staged edit\n", encoding="utf-8")
    h.git(repo, "add", "README.md")
    (repo / "README.md").write_text("then edited again\n", encoding="utf-8")
    (repo / "added.txt").write_text("added\n", encoding="utf-8")
    h.git(repo, "add", "added.txt")
    h.git(repo, "rm", "-q", "--cached", "kept.txt")
    (repo / "forced.log").write_text("forced\n", encoding="utf-8")
    h.git(repo, "add", "-f", "forced.log")
    (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")
    ws = h.workspace(repo)
    seen = _record_children(monkeypatch)
    with h.git_identity():
        names, entries = ws.git.change_set(), ws.git.working_changes()
        warm_calls = [argv for argv, _env in seen]
        assert (names, entries) == _cold_scan(ws)
    assert not any("read-tree" in argv for argv in warm_calls)
    # The ignored file stays out and the unstaged removal of kept.txt is undone by the scan.
    assert names == ["README.md", "added.txt", "untracked.txt"]


@posix_only
def test_a_skip_worktree_entry_sends_the_scan_back_to_a_cold_index(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    h.git(repo, "update-index", "--skip-worktree", "README.md")
    (repo / "README.md").write_text("edited\n", encoding="utf-8")
    ws = h.workspace(repo)
    seen = _record_children(monkeypatch)
    with h.git_identity():
        names = ws.git.change_set()
    assert "README.md" in names
    assert any("read-tree" in argv for argv, _env in seen)


@posix_only
def test_a_missing_work_tree_index_falls_back_to_a_cold_index(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    (repo / ".git" / "index").unlink()
    ws = h.workspace(repo)
    with h.git_identity():
        assert ws.git.change_set() == ["new.txt"]


def _index_leftovers(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.glob("work-supervisor-index-*"))


@posix_only
def test_a_same_size_same_mtime_edit_is_seen_even_under_a_weakened_stat_check(
        tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    cited = repo / "cited.md"
    cited.write_text("cited v1\n", encoding="utf-8")
    old = (cited.stat().st_atime_ns - 3600 * 10**9, cited.stat().st_mtime_ns - 3600 * 10**9)
    os.utime(cited, ns=old)  # older than the index, so Git does not treat the entry as racy
    h.git(repo, "add", "cited.md")
    h.git(repo, "commit", "-q", "-m", "cited")
    h.git(repo, "config", "core.checkStat", "minimal")
    h.git(repo, "config", "core.trustctime", "false")
    time.sleep(1.1)  # some Git builds compare ctime to the second only
    cited.write_text("cited v2\n", encoding="utf-8")
    os.utime(cited, ns=old)
    # The weakened settings really do hide the edit from plain Git...
    assert h.git(repo, "status", "--short").strip() == ""
    ws = h.workspace(repo)
    # ...and the pinned scan still sees it.
    with h.git_identity():
        assert ws.git.change_set() == ["cited.md"]
        assert "cited.md" in ws.git.working_changes()


@posix_only
def test_a_failed_seeding_leaves_no_index_copy_behind(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr("tempfile.tempdir", str(scratch))
    ws = h.workspace(repo)
    real = _git_module._launch

    def _fail_on_diff_index(argv: list[str], **kwargs: Any) -> Any:
        if "diff-index" in argv:
            raise _git_module.SupervisorGitError("denied-git-unavailable", "timed out")
        return real(argv, **kwargs)

    monkeypatch.setattr(_git_module, "_launch", _fail_on_diff_index)
    with h.git_identity(), pytest.raises(_git_module.SupervisorGitError):
        ws.git.change_set()
    assert _index_leftovers(scratch) == []


def _scan_pair(ws: Any) -> tuple[list[str], dict[str, Any]]:
    return ws.git.change_set(), ws.git.working_changes()


@posix_only
def test_an_assume_unchanged_entry_sends_the_scan_back_to_a_cold_index(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    h.git(repo, "update-index", "--assume-unchanged", "README.md")
    (repo / "README.md").write_text("edited\n", encoding="utf-8")
    ws = h.workspace(repo)
    seen = _record_children(monkeypatch)
    with h.git_identity():
        names = ws.git.change_set()
        assert (names, ws.git.working_changes()) == _cold_scan(ws)
    assert "README.md" in names
    assert any("read-tree" in argv for argv, _env in seen)


@posix_only
def test_an_unmerged_index_sends_the_scan_back_to_a_cold_index(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    h.git(repo, "checkout", "-q", "-b", "side")
    (repo / "README.md").write_text("side\n", encoding="utf-8")
    h.git(repo, "commit", "-qam", "side")
    h.git(repo, "checkout", "-q", "main")
    (repo / "README.md").write_text("main\n", encoding="utf-8")
    h.git(repo, "commit", "-qam", "main")
    with h.git_identity():
        subprocess.run(["git", "merge", "side"], cwd=repo, capture_output=True, check=False)
    ws = h.workspace(repo)
    seen = _record_children(monkeypatch)
    with h.git_identity():
        assert _scan_pair(ws) == _cold_scan(ws)
    assert any("read-tree" in argv for argv, _env in seen)


@posix_only
def test_typechange_exec_bit_and_intent_to_add_read_as_a_cold_scan_reads(
        tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "tool.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (repo / "link-me").write_text("x\n", encoding="utf-8")
    h.git(repo, "add", "tool.sh", "link-me")
    h.git(repo, "commit", "-q", "-m", "files")
    (repo / "tool.sh").chmod(0o755)
    (repo / "link-me").unlink()
    (repo / "link-me").symlink_to("README.md")
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    h.git(repo, "add", "-N", "later.txt")
    ws = h.workspace(repo)
    with h.git_identity():
        names, entries = _scan_pair(ws)
        assert (names, entries) == _cold_scan(ws)
    assert {"tool.sh", "link-me", "later.txt"} <= set(names)


@posix_only
def test_a_write_to_the_real_index_keeps_its_untracked_cache(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "extra.txt").write_text("x\n", encoding="utf-8")
    h.git(repo, "update-index", "--untracked-cache")
    h.git(repo, "status", "--short")
    assert b"UNTR" in (repo / ".git" / "index").read_bytes()
    ws = h.workspace(repo)
    with h.git_identity():
        ws.git.refresh_index(["README.md"])
    assert b"UNTR" in (repo / ".git" / "index").read_bytes()


def _forge_entry_oid(repo: Path, path: str, oid: str) -> None:
    """Rewrite one version-2 index entry's object id, keeping the stat data it holds."""
    import hashlib

    index = repo / ".git" / "index"
    data = bytearray(index.read_bytes())
    at = bytes(data).index(path.encode() + b"\0")
    start = at - 2 - 20  # the 20-byte id and 2 flag bytes sit before the path
    data[start:start + 20] = bytes.fromhex(oid)
    data[-20:] = hashlib.sha1(bytes(data[:-20])).digest()
    index.write_bytes(bytes(data))


def _forged_edit(tmp_path: Path, rel: str) -> Path:
    """A repo whose index claims *rel* is unchanged while its bytes are edited."""
    repo = h.make_repo(tmp_path)
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text("aaaa\n", encoding="utf-8")
        h.git(repo, "add", rel)
        h.git(repo, "commit", "-q", "-m", "seed")
    head_oid = h.git(repo, "rev-parse", f"HEAD:{rel}").strip()
    target.write_text("zzzz\n" if target.read_text(encoding="utf-8") == "aaaa\n" else "zzzz\n",
                      encoding="utf-8")
    old = target.stat().st_mtime_ns - 3600 * 10**9
    os.utime(target, ns=(old, old))
    h.git(repo, "add", rel)
    _forge_entry_oid(repo, rel, head_oid)
    return repo


@posix_only
def test_a_forged_index_entry_cannot_hide_an_edit_to_the_spec_directory(tmp_path: Path) -> None:
    rel = f"{h.SPEC_DIR}/spec.md"
    repo = _forged_edit(tmp_path, rel)
    assert h.git(repo, "status", "--short").strip() == "", "the forgery hides the edit from Git"
    ws = h.workspace(repo)
    with h.git_identity():
        assert rel in ws.git.change_set()
        assert rel in ws.git.working_changes()


@posix_only
def test_a_forged_index_entry_cannot_hide_an_edit_to_a_named_cited_path(tmp_path: Path) -> None:
    repo = _forged_edit(tmp_path, "docs/adr/cited.md")
    assert h.git(repo, "status", "--short").strip() == ""
    ws = h.workspace(repo)
    with h.git_identity():
        assert "docs/adr/cited.md" in ws.git.change_set(rehash=["docs/adr/cited.md"])


@posix_only
def test_an_index_that_is_not_a_regular_file_or_is_too_large_scans_cold(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    ws = h.workspace(repo)
    commit_module = sys.modules[type(ws.git).__module__]
    seen = _record_children(monkeypatch)
    with h.git_identity():
        monkeypatch.setattr(commit_module, "_MAX_INDEX_BYTES", 16)
        assert ws.git.change_set() == ["new.txt"]
    assert any("read-tree" in argv for argv, _env in seen)


@posix_only
def test_a_split_index_copy_writes_no_shared_index_into_the_git_directory(
        tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    h.git(repo, "update-index", "--split-index")
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    before = sorted(p.name for p in (repo / ".git").glob("sharedindex.*"))
    ws = h.workspace(repo)
    with h.git_identity():
        assert ws.git.change_set() == ["new.txt"]
    assert sorted(p.name for p in (repo / ".git").glob("sharedindex.*")) == before


@posix_only
def test_a_private_index_scan_leaves_no_file_descriptor_open(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    (repo / "new.txt").write_text("new\n", encoding="utf-8")
    ws = h.workspace(repo)

    def open_fds() -> int:
        return len(list(Path("/dev/fd").iterdir()))

    with h.git_identity():
        ws.git.change_set()  # a first call settles any lazy handles
        before = open_fds()
        for _ in range(5):
            ws.git.change_set()  # warm
            with ws.git._private_index():  # cold, as build_commit opens it
                pass
    assert open_fds() == before
