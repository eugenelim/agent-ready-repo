#!/usr/bin/env python3
"""Pytest coverage for check-base-freshness.py.

Run with pytest.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"

if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")
FRESHNESS = SCRIPT_DIR / "check-base-freshness.py"


def ok(name: str) -> None:
    """Pytest reports the independently collected case."""


def fail(name: str, reason: str) -> None:
    pytest.fail(f"{name}: {reason}")


def run_freshness(cwd: Path, *args: str) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(FRESHNESS)] + list(args),
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd),
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test"]
        + list(args),
        check=True,
        capture_output=True,
        cwd=str(cwd),
    )


def load_freshness_module():
    spec = importlib.util.spec_from_file_location(
        "core_work_loop_check_base_freshness", FRESHNESS
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {FRESHNESS}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_skipped_notice(data: dict[str, object]) -> None:
    assert data.get("status") == "skipped"
    message = str(data.get("message", ""))
    assert "not verified" in message
    assert "may continue" in message
    assert "separately" in message


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_no_remote(tmp: Path) -> None:
    """No remote → exit 0, status ok."""
    repo = tmp / "no-remote"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")

    rc, out, err = run_freshness(repo)
    if rc != 0:
        fail("no_remote", f"expected exit 0, got {rc}; out={out!r} err={err!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("no_remote", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "ok":
        fail("no_remote", f"expected status=ok, got {data!r}")
        return
    ok("no_remote")


def test_target_flag_bad_form(tmp: Path) -> None:
    """--target without slash → exit 1 with a clear error."""
    repo = tmp / "flag-bad"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    git(repo, "remote", "add", "origin", "https://example.invalid/repo.git")

    rc, out, err = run_freshness(repo, "--target", "notaslash")
    if rc != 1:
        fail("target_flag_bad_form", f"expected exit 1, got {rc}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("target_flag_bad_form", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "surface":
        fail("target_flag_bad_form", f"expected status=surface, got {data!r}")
        return
    ok("target_flag_bad_form")


def test_unavailable_remote_head_skips(tmp: Path) -> None:
    repo = tmp / "unavailable-remote-head"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    git(repo, "remote", "add", "origin", str(tmp / "missing.git"))

    rc, out, _err = run_freshness(repo)
    data = json.loads(out)

    assert rc == 0
    assert_skipped_notice(data)


def test_fetch_denied_remote_tracking_ref_skips(tmp: Path) -> None:
    origin = tmp / "denied-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "denied-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    (origin / "b.txt").write_text("b")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "B")

    refs_dir = clone / ".git" / "refs" / "remotes" / "origin"
    original_mode = refs_dir.stat().st_mode
    refs_dir.chmod(0o500)
    try:
        rc, out, _err = run_freshness(clone, "--target=origin/main")
    finally:
        refs_dir.chmod(original_mode)
    data = json.loads(out)

    assert rc == 0
    assert data.get("target") == "origin/main"
    assert_skipped_notice(data)


def test_ls_remote_timeout_skips(tmp: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp / "ls-remote-timeout"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    git(repo, "remote", "add", "origin", str(tmp / "origin.git"))

    module = load_freshness_module()
    original = module._run_with_stderr

    def fake_run_with_stderr(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
        if len(cmd) > 1 and cmd[1] == "ls-remote":
            return 124, "", ""
        return original(cmd, timeout=timeout)

    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["check-base-freshness"])
    monkeypatch.setattr(module, "_run_with_stderr", fake_run_with_stderr)

    rc = module.main()
    data = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert_skipped_notice(data)


def test_fetch_timeout_skips(tmp: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    origin = tmp / "fetch-timeout-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "fetch-timeout-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )

    module = load_freshness_module()
    original = module._run_with_stderr

    def fake_run_with_stderr(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
        if len(cmd) > 1 and cmd[1] == "fetch":
            return 124, "", ""
        return original(cmd, timeout=timeout)

    monkeypatch.chdir(clone)
    monkeypatch.setattr(sys, "argv", ["check-base-freshness", "--target=origin/main"])
    monkeypatch.setattr(module, "_run_with_stderr", fake_run_with_stderr)

    rc = module.main()
    data = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert data.get("target") == "origin/main"
    assert_skipped_notice(data)


@pytest.mark.parametrize(
    ("stderr", "category"),
    [
        (
            "fatal: unable to access 'https://example.invalid/repo.git/': "
            "Could not resolve host: example.invalid",
            "remote host could not be resolved",
        ),
        ("git@example.invalid: Permission denied (publickey).", "remote authentication failed"),
        (
            "fatal: 'missing.git' does not appear to be a git repository",
            "remote repository is unavailable",
        ),
    ],
)
def test_remote_unavailable_classifier_closed_categories(stderr: str, category: str) -> None:
    module = load_freshness_module()

    assert module._classify_remote_unavailable(stderr) == category


@pytest.mark.parametrize(
    "stderr",
    [
        "fatal: bad revision syntax",
        (
            "fatal: unable to access 'bad::url': URL using bad/illegal "
            "format or missing URL"
        ),
        "fatal: protocol 'bad' is not supported",
        (
            "fatal: unable to access 'https://example.invalid/repo.git/': "
            "URL rejected: malformed input to a URL function"
        ),
    ],
)
def test_remote_unavailable_classifier_rejects_unmatched_diagnostics(stderr: str) -> None:
    module = load_freshness_module()

    assert module._classify_remote_unavailable(stderr) is None


@pytest.mark.parametrize(
    "stderr",
    [
        "error: cannot lock ref 'refs/remotes/origin/main': Unable to create '.git/refs/remotes/origin/main.lock': Operation not permitted",
        "error: unable to update local ref refs/remotes/origin/main: Permission denied",
        "fatal: remote-tracking ref update failed: read-only file system",
    ],
)
def test_fetch_metadata_denied_classifier_closed_categories(stderr: str) -> None:
    module = load_freshness_module()

    assert (
        module._classify_fetch_metadata_denied(stderr)
        == "git metadata write was denied by local policy"
    )


def test_fetch_unclassified_failure_surfaces_without_raw_stderr(
    tmp: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    origin = tmp / "fetch-unclassified-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "fetch-unclassified-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )

    module = load_freshness_module()
    original = module._run_with_stderr
    raw_stderr = (
        "fatal: unable to access 'bad::url': URL using bad/illegal format "
        "or missing URL"
    )

    def fake_run_with_stderr(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
        if len(cmd) > 1 and cmd[1] == "fetch":
            return 128, "", raw_stderr
        return original(cmd, timeout=timeout)

    monkeypatch.chdir(clone)
    monkeypatch.setattr(sys, "argv", ["check-base-freshness", "--target=origin/main"])
    monkeypatch.setattr(module, "_run_with_stderr", fake_run_with_stderr)

    rc = module.main()
    data = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert data.get("status") == "surface"
    assert "unclassified diagnostics" in data.get("message", "")
    assert raw_stderr not in data.get("message", "")


def test_ls_remote_unclassified_failure_surfaces_without_raw_stderr(
    tmp: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp / "ls-remote-unclassified"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    git(repo, "remote", "add", "origin", "bad::url")

    module = load_freshness_module()
    original = module._run_with_stderr
    raw_stderr = "fatal: protocol 'bad' is not supported"

    def fake_run_with_stderr(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str, str]:
        if len(cmd) > 1 and cmd[1] == "ls-remote":
            return 128, "", raw_stderr
        return original(cmd, timeout=timeout)

    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["check-base-freshness"])
    monkeypatch.setattr(module, "_run_with_stderr", fake_run_with_stderr)

    rc = module.main()
    data = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert data.get("status") == "surface"
    assert "unclassified diagnostics" in data.get("message", "")
    assert raw_stderr not in data.get("message", "")


def test_no_remote_rebase_in_progress(tmp: Path) -> None:
    """Local-only repo with rebase in progress → exit 1, not exit 0.

    Regression guard for P2-A: the rebase check must run before the
    'no remote → ok' shortcut so a local rebase is always caught.
    """
    repo = tmp / "no-remote-rebase"
    repo.mkdir()
    git(tmp, "init", str(repo))
    (repo / "f.txt").write_text("init")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    (repo / ".git" / "rebase-merge").mkdir(parents=True, exist_ok=True)

    rc, out, err = run_freshness(repo)
    if rc != 1:
        fail("no_remote_rebase_in_progress", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("no_remote_rebase_in_progress", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "surface":
        fail("no_remote_rebase_in_progress", f"expected status=surface, got {data!r}")
        return
    if "already in progress" not in data.get("message", ""):
        fail("no_remote_rebase_in_progress", f"expected 'already in progress', got {data!r}")
        return
    ok("no_remote_rebase_in_progress")


def test_rebase_in_progress(tmp: Path) -> None:
    """rebase-merge directory present → exit 1, message mentions 'already in progress'."""
    origin = tmp / "rip-origin"
    origin.mkdir()
    git(tmp, "init", "--bare", str(origin))

    clone = tmp / "rip-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Simulate in-progress rebase by creating the sentinel directory
    (clone / ".git" / "rebase-merge").mkdir(parents=True, exist_ok=True)

    rc, out, err = run_freshness(clone)
    if rc != 1:
        fail("rebase_in_progress", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("rebase_in_progress", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "surface":
        fail("rebase_in_progress", f"expected status=surface, got {data!r}")
        return
    if "already in progress" not in data.get("message", ""):
        fail(
            "rebase_in_progress",
            f"expected 'already in progress' in message, got {data!r}",
        )
        return
    ok("rebase_in_progress")


def test_fresh_head(tmp: Path) -> None:
    """Clone whose HEAD already equals origin/main → exit 0, status ok."""
    origin = tmp / "fresh-origin"
    origin.mkdir()
    git(tmp, "init", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "fresh-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )

    rc, out, err = run_freshness(clone)
    if rc != 0:
        fail("fresh_head", f"expected exit 0, got {rc}; out={out!r} err={err!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("fresh_head", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "ok":
        fail("fresh_head", f"expected status=ok, got {data!r}")
        return
    ok("fresh_head")


def test_behind_surfaces(tmp: Path) -> None:
    """Feature branch behind integration target → exit 1, surface with rebase command."""
    origin = tmp / "behind-origin"
    origin.mkdir()
    git(tmp, "init", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "behind-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )

    # Advance origin by one commit
    (origin / "b.txt").write_text("b")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "B")

    # Create a local feature branch
    git(clone, "checkout", "-b", "feature/x")

    rc, out, err = run_freshness(clone)
    if rc != 1:
        fail("behind_surfaces", f"expected exit 1, got {rc}; out={out!r} err={err!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("behind_surfaces", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "surface":
        fail("behind_surfaces", f"expected status=surface, got {data!r}")
        return
    if "behind" not in data.get("message", "") or "rebase" not in data.get("message", ""):
        fail("behind_surfaces", f"expected 'behind' and 'rebase' in message, got {data!r}")
        return
    ok("behind_surfaces")


def test_target_slashed_remote(tmp: Path) -> None:
    """--target REMOTE/BRANCH where REMOTE itself contains a slash is parsed correctly."""
    origin = tmp / "slashed-origin"
    origin.mkdir()
    git(tmp, "init", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "slashed-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Detect the default branch before renaming the remote
    br = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True, cwd=str(clone),
    ).stdout.strip()

    # Rename origin → team/upstream (slash-containing remote name)
    git(clone, "remote", "rename", "origin", "team/upstream")

    rc, out, err = run_freshness(clone, "--target", f"team/upstream/{br}")
    if rc != 0:
        fail(
            "target_slashed_remote",
            f"expected exit 0 (clone is current), got {rc}; out={out!r} err={err!r}",
        )
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("target_slashed_remote", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "ok":
        fail("target_slashed_remote", f"expected status=ok, got {data!r}")
        return
    ok("target_slashed_remote")


def test_target_ambiguous_remote(tmp: Path) -> None:
    """--target whose prefix matches two configured remotes → exit 1 with 'ambiguous'."""
    origin = tmp / "ambig-origin"
    origin.mkdir()
    git(tmp, "init", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "ambig-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Detect the default branch before any remote manipulation
    br = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True, cwd=str(clone),
    ).stdout.strip()

    # Write 'team' and 'team/upstream' directly into .git/config, bypassing
    # 'git remote add'.  Git ≥ 2.38 rejects 'remote add' when the new name's
    # refs/remotes/{name}/ directory already exists (created by a prior rename
    # or fetch), or when an existing remote name is a config-level prefix of
    # the new name.  Direct config writes avoid both guards.
    # check-base-freshness.py surfaces "ambiguous" before fetching, so the
    # URLs do not need to be reachable for this test.
    git(clone, "remote", "remove", "origin")
    config_path = clone / ".git" / "config"
    team_fetch = "+refs/heads/*:refs/remotes/team/*"
    upstream_fetch = "+refs/heads/*:refs/remotes/team/upstream/*"
    config_path.write_text(
        config_path.read_text()
        + f'\n[remote "team"]\n\turl = {origin}\n\tfetch = {team_fetch}\n'
        f'[remote "team/upstream"]\n\turl = {origin}\n\tfetch = {upstream_fetch}\n'
    )

    rc, out, err = run_freshness(clone, "--target", f"team/upstream/{br}")
    if rc != 1:
        fail(
            "target_ambiguous_remote",
            f"expected exit 1 (ambiguous), got {rc}; out={out!r} err={err!r}",
        )
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("target_ambiguous_remote", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "surface":
        fail("target_ambiguous_remote", f"expected status=surface, got {data!r}")
        return
    if "ambiguous" not in data.get("message", ""):
        fail(
            "target_ambiguous_remote",
            f"expected 'ambiguous' in message, got {data!r}",
        )
        return
    ok("target_ambiguous_remote")


def test_multi_remote_surfaces(tmp: Path) -> None:
    """Multiple remotes without --target → exit 1, message names them."""
    origin = tmp / "multi-origin"
    origin.mkdir()
    git(tmp, "init", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "multi-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Add a second remote to make the integration target ambiguous
    git(clone, "remote", "add", "upstream", str(origin))

    rc, out, err = run_freshness(clone)
    if rc != 1:
        fail("multi_remote_surfaces", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("multi_remote_surfaces", f"invalid JSON: {exc}; out={out!r}")
        return
    if data.get("status") != "surface":
        fail("multi_remote_surfaces", f"expected status=surface, got {data!r}")
        return
    if "multiple remotes" not in data.get("message", ""):
        fail(
            "multi_remote_surfaces",
            f"expected 'multiple remotes' in message, got {data!r}",
        )
        return
    ok("multi_remote_surfaces")


def test_target_empty_string(tmp: Path) -> None:
    """--target= (empty string) → exit 1, message says empty."""
    origin = tmp / "empty-tgt-origin"
    origin.mkdir()
    git(tmp, "init", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "empty-tgt-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )

    rc, out, _err = run_freshness(clone, "--target=")
    if rc != 1:
        fail("target_empty_string", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("target_empty_string", f"invalid JSON: {exc}; out={out!r}")
        return
    msg = data.get("message", "")
    if "empty" not in msg.lower():
        fail("target_empty_string", f"expected 'empty' in message, got {msg!r}")
        return
    ok("target_empty_string")


def test_no_common_ancestor(tmp: Path) -> None:
    """Target and HEAD share no common ancestor → exit 1, unsafe rebase message."""
    # Build two unrelated repos, wire orphan-remote as a "remote" in clone.
    orphan = tmp / "orphan-origin"
    orphan.mkdir()
    git(tmp, "init", "-b", "main", str(orphan))
    (orphan / "x.txt").write_text("x")
    git(orphan, "add", ".")
    git(orphan, "commit", "-m", "orphan-commit")

    origin = tmp / "nca-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "nca-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Make clone one commit behind origin so count > 0.
    (origin / "b.txt").write_text("b")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "B")
    # Point origin remote at the orphan repo (different history).
    git(clone, "remote", "set-url", "origin", str(orphan))

    rc, out, _err = run_freshness(clone, "--target=origin/main")
    if rc != 1:
        fail("no_common_ancestor", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("no_common_ancestor", f"invalid JSON: {exc}; out={out!r}")
        return
    msg = data.get("message", "")
    if "common ancestor" not in msg and "unsafe" not in msg:
        fail("no_common_ancestor", f"expected unsafe/ancestor warning, got {msg!r}")
        return
    ok("no_common_ancestor")


def test_fetch_missing_branch(tmp: Path) -> None:
    """--target names a branch the remote does not have → 'not found on remote'."""
    origin = tmp / "missing-branch-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "missing-branch-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )

    rc, out, _err = run_freshness(clone, "--target=origin/no-such-branch")
    if rc != 1:
        fail("fetch_missing_branch", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("fetch_missing_branch", f"invalid JSON: {exc}; out={out!r}")
        return
    msg = data.get("message", "")
    if "not found on remote" not in msg:
        fail("fetch_missing_branch", f"expected 'not found on remote', got {msg!r}")
        return
    ok("fetch_missing_branch")


def test_fetch_transport_error_mentioning_remote_ref(tmp: Path) -> None:
    """A transport failure whose stderr echoes 'remote ref' is NOT a missing branch.

    Regression guard: the classifier used to accept any stderr containing the
    substring 'remote ref', so an unreachable remote whose URL happens to carry
    that phrase was reported as a wrong branch name — sending the agent to fix
    --target when the real cause was auth or network.  Git echoes the URL in
    'does not appear to be a git repository', which is how the phrase gets into
    the stderr of a failure that has nothing to do with a missing ref.
    """
    origin = tmp / "transport-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    clone = tmp / "transport-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Repoint origin at a path that does not exist and that contains the
    # literal substring 'remote ref'.
    unreachable = tmp / "has remote ref in path" / "gone.git"
    git(clone, "remote", "set-url", "origin", str(unreachable))

    rc, out, _err = run_freshness(clone, "--target=origin/main")
    if rc != 0:
        fail(
            "fetch_transport_error_mentioning_remote_ref",
            f"expected exit 0, got {rc}; out={out!r}",
        )
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail(
            "fetch_transport_error_mentioning_remote_ref",
            f"invalid JSON: {exc}; out={out!r}",
        )
        return
    msg = data.get("message", "")
    if data.get("status") != "skipped":
        fail(
            "fetch_transport_error_mentioning_remote_ref",
            f"expected status=skipped, got {data!r}",
        )
        return
    if "not found on remote" in msg:
        fail(
            "fetch_transport_error_mentioning_remote_ref",
            f"transport failure misreported as a missing branch: {msg!r}",
        )
        return
    if "not verified" not in msg:
        fail(
            "fetch_transport_error_mentioning_remote_ref",
            f"expected the skipped freshness notice, got {msg!r}",
        )
        return
    ok("fetch_transport_error_mentioning_remote_ref")


def test_dirty_tree_says_commit_not_stash(tmp: Path) -> None:
    """Behind the target with a dirty tree → commit guidance, never 'git stash'.

    refs/stash is not a per-worktree ref: every linked worktree of a repository
    shares one stash stack, so a stash pushed here can be popped from another
    worktree and lost.  Covers both the tracked-only and the untracked variant,
    which select different commit commands.
    """
    origin = tmp / "dirty-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "a.txt").write_text("a")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "A")

    for label, make_dirty in (
        ("tracked", lambda repo: (repo / "a.txt").write_text("locally modified")),
        ("untracked", lambda repo: (repo / "new.txt").write_text("brand new")),
    ):
        name = f"dirty_tree_says_commit_not_stash[{label}]"
        clone = tmp / f"dirty-clone-{label}"
        subprocess.run(
            ["git", "clone", str(origin), str(clone)],
            check=True,
            capture_output=True,
        )
        # Advance origin so the clone is behind, then dirty the clone.
        (origin / f"b-{label}.txt").write_text("b")
        git(origin, "add", ".")
        git(origin, "commit", "-m", f"B-{label}")
        make_dirty(clone)

        rc, out, _err = run_freshness(clone, "--target=origin/main")
        if rc != 1:
            fail(name, f"expected exit 1, got {rc}; out={out!r}")
            continue
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            fail(name, f"invalid JSON: {exc}; out={out!r}")
            continue
        msg = data.get("message", "")
        if "git stash" in msg:
            fail(name, f"message still recommends stashing: {msg!r}")
            continue
        if "uncommitted changes" not in msg:
            fail(name, f"expected the behind-with-dirty-tree message, got {msg!r}")
            continue
        if "git commit" not in msg:
            fail(name, f"expected a commit command, got {msg!r}")
            continue
        # The discriminator between the two variants, asserted both ways so
        # neither branch can silently collapse into the other.
        stages_untracked = "git add -A" in msg
        if stages_untracked != (label == "untracked"):
            fail(
                name,
                f"'git add -A' should be {'present' if label == 'untracked' else 'absent'} "
                f"for the {label} variant, got {msg!r}",
            )
            continue
        if "rebase" not in msg:
            fail(name, f"expected the rebase hint to survive, got {msg!r}")
            continue
        ok(name)


def test_unmerged_files_message_is_truthful(tmp: Path) -> None:
    """Behind the target with conflicts → no advice that would commit the markers.

    'git commit -a' stages and commits an unmerged file with its conflict
    markers intact, so this branch must not read as though committing is
    simply unavailable — the sibling clean-tree branch recommends exactly
    that command.
    """
    origin = tmp / "unmerged-origin"
    origin.mkdir()
    git(tmp, "init", "-b", "main", str(origin))
    (origin / "f.txt").write_text("base\n")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "base")

    clone = tmp / "unmerged-clone"
    subprocess.run(
        ["git", "clone", str(origin), str(clone)],
        check=True,
        capture_output=True,
    )
    # Diverge the clone on a side branch, then advance origin so the clone is
    # behind, then produce a real UU by merging the side branch back.
    git(clone, "checkout", "-b", "side")
    (clone / "f.txt").write_text("side\n")
    git(clone, "commit", "-am", "side")
    git(clone, "checkout", "main")
    (clone / "f.txt").write_text("local\n")
    git(clone, "commit", "-am", "local")
    subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test",
         "merge", "side"],
        capture_output=True, check=False, cwd=str(clone),
    )
    (origin / "b.txt").write_text("b")
    git(origin, "add", ".")
    git(origin, "commit", "-m", "B")

    porcelain = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, check=True, cwd=str(clone),
    ).stdout
    if not any(ln.startswith("UU") for ln in porcelain.splitlines()):
        fail(
            "unmerged_files_message_is_truthful",
            f"fixture did not produce an unmerged file; porcelain={porcelain!r}",
        )
        return

    rc, out, _err = run_freshness(clone, "--target=origin/main")
    if rc != 1:
        fail("unmerged_files_message_is_truthful", f"expected exit 1, got {rc}; out={out!r}")
        return
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail("unmerged_files_message_is_truthful", f"invalid JSON: {exc}; out={out!r}")
        return
    msg = data.get("message", "")
    if "unmerged files" not in msg:
        fail("unmerged_files_message_is_truthful", f"expected the unmerged branch, got {msg!r}")
        return
    if "git commit -a" not in msg or "conflict markers" not in msg:
        fail(
            "unmerged_files_message_is_truthful",
            f"expected the message to warn that 'git commit -a' commits the "
            f"conflict markers, got {msg!r}",
        )
        return
    ok("unmerged_files_message_is_truthful")
