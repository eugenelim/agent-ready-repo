#!/usr/bin/env python3
"""Tests for check-base-freshness.py.

Run: python3 test-check-base-freshness.py
Exit 0 = all pass; exit non-zero = at least one failure.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
FRESHNESS = SCRIPT_DIR / "check-base-freshness.py"

failures: list[str] = []
ran = 0


def ok(name: str) -> None:
    global ran
    ran += 1
    print(f"ok   [{name}]")


def fail(name: str, reason: str) -> None:
    global ran
    ran += 1
    failures.append(name)
    print(f"FAIL [{name}]: {reason}", file=sys.stderr)


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


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def case_no_remote(tmp: Path) -> None:
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


def case_target_flag_bad_form(tmp: Path) -> None:
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


def case_no_remote_rebase_in_progress(tmp: Path) -> None:
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


def case_rebase_in_progress(tmp: Path) -> None:
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


def case_fresh_head(tmp: Path) -> None:
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


def case_behind_surfaces(tmp: Path) -> None:
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


def case_target_slashed_remote(tmp: Path) -> None:
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


def case_target_ambiguous_remote(tmp: Path) -> None:
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
    config_path.write_text(
        config_path.read_text()
        + f'\n[remote "team"]\n\turl = {origin}\n\tfetch = +refs/heads/*:refs/remotes/team/*\n'
        f'[remote "team/upstream"]\n\turl = {origin}\n\tfetch = +refs/heads/*:refs/remotes/team/upstream/*\n'
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


def case_multi_remote_surfaces(tmp: Path) -> None:
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


def case_target_empty_string(tmp: Path) -> None:
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


def case_no_common_ancestor(tmp: Path) -> None:
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


def main() -> int:
    orig_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tests = [
            case_no_remote,
            case_no_remote_rebase_in_progress,
            case_target_flag_bad_form,
            case_rebase_in_progress,
            case_fresh_head,
            case_target_slashed_remote,
            case_target_ambiguous_remote,
            case_multi_remote_surfaces,
            case_behind_surfaces,
            case_target_empty_string,
            case_no_common_ancestor,
        ]
        try:
            for t in tests:
                try:
                    t(tmp)
                except Exception as exc:
                    fail(t.__name__, f"uncaught exception: {exc}")
        finally:
            import os
            os.chdir(orig_cwd)

    total = ran
    passed = total - len(failures)
    print(f"\n{passed}/{total} passed")
    if failures:
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
