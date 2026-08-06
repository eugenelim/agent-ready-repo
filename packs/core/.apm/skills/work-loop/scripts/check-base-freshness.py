#!/usr/bin/env python3
"""check-base-freshness.py — verify HEAD is current against the merge target.

Run before reading workspace.toml or any spec.

Usage:
    python scripts/check-base-freshness.py [--target REMOTE/BRANCH]

    --target REMOTE/BRANCH  explicit merge target, e.g. 'origin/main'.
                            Required when the repo has more than one remote
                            (fork workflows, stacked PRs, release branches).
                            For remotes whose name begins with '-', use the
                            equals form: --target=-mirror/main.

Exit codes:
  0  head is current (or no remote / not on a branch)
  1  Surface required — JSON on stdout has the details

JSON (stdout): {"status": "ok"|"surface", "message": str, "target": str}
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_NETWORK_TIMEOUT = 60  # seconds; git fetch / ls-remote


def _quote_for_shell(s: str) -> str | None:
    """Quote s for the current platform's interactive shell, or None if unsafe.

    On POSIX, shlex.quote single-quotes the argument; single-quoted strings are
    inert in bash/zsh — no expansion, no substitution, no injection surface.

    On Windows, three common shells (cmd.exe, PowerShell, Git Bash) each have
    distinct injection vectors inside double-quoted strings: cmd.exe expands
    %VAR%, PowerShell expands $var and $(), and Git Bash performs `cmd`
    substitution. Maintaining a per-shell blocklist creates a whack-a-mole
    loop; the only safe choice is to never emit a runnable shell command on
    Windows and let the caller always use the non-command fallback.
    """
    if sys.platform == "win32":
        return None
    return shlex.quote(s)

# ── Environment ─────────────────────────────────────────────────────────────


_GIT_ENV: dict[str, str] | None = None


def _build_git_env() -> dict[str, str]:
    """Build the subprocess environment for all git calls.

    Adds GIT_TERMINAL_PROMPT=0 unconditionally.
    Adds LC_ALL=C unconditionally: git's diagnostics are gettext msgids, so a
    distro build with translation catalogues installed prints them in the
    user's language. This script classifies one fetch failure by matching
    git's own English wording, which a translated message would silently
    defeat. (GNU gettext ignores LANGUAGE when the locale is C, so LC_ALL
    alone is enough.)
    Adds GIT_SSH_COMMAND with BatchMode+ConnectTimeout ONLY when the user
    has no custom SSH transport configured — GIT_SSH_COMMAND is not
    guaranteed to be OpenSSH-compatible (plink, tortoiseplink, etc. reject
    -o flags), and GIT_SSH / core.sshCommand indicate non-standard wrappers.
    """
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}

    # Any of these signal a non-standard or variant SSH transport that may
    # not accept OpenSSH -o flags (plink, tortoiseplink, etc.).
    if env.get("GIT_SSH") or env.get("GIT_SSH_COMMAND") or env.get("GIT_SSH_VARIANT"):
        return env

    # Check git config for a custom SSH command or variant indicator
    for key in ("core.sshCommand", "ssh.variant"):
        r = subprocess.run(
            ["git", "config", "--get", key],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return env

    # No custom SSH transport — safe to add batch mode
    env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o ConnectTimeout=10"
    return env


def _get_env() -> dict[str, str]:
    global _GIT_ENV
    if _GIT_ENV is None:
        _GIT_ENV = _build_git_env()
    return _GIT_ENV


def _run(cmd: list[str], *, timeout: int | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_get_env(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, ""
    return r.returncode, r.stdout.strip()


def _run_with_stderr(
    cmd: list[str], *, timeout: int | None = None
) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_get_env(),
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", ""
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _emit(data: dict) -> None:
    print(json.dumps(data))


def _surface(message: str, target: str = "") -> int:
    _emit({"status": "surface", "message": message, "target": target})
    return 1


def _ok(message: str, target: str = "") -> int:
    _emit({"status": "ok", "message": message, "target": target})
    return 0


# ── Target resolution ────────────────────────────────────────────────────────


def _live_remote_head_branch(remote: str) -> tuple[str | None, str | None]:
    """Query the remote's current HEAD branch via ls-remote --symref.

    Returns (branch_name, error_message). Exactly one is non-None on each path:
    - (branch, None) — success; branch is the current HEAD branch name
    - (None, message) — timeout or transport/auth failure with a Surface message
    - (None, None) — ls-remote succeeded but HEAD is detached or unborn;
                     caller should ask the user to pass --target explicitly

    Uses the live remote query — not the cached refs/remotes/<remote>/HEAD,
    which git fetch does not update when the ref already exists.
    """
    rc, out, _err = _run_with_stderr(
        ["git", "ls-remote", "--symref", "--", remote, "HEAD"],
        timeout=_NETWORK_TIMEOUT,
    )
    if rc == 124:
        return None, f"ls-remote to {remote!r} timed out — check network/auth"
    if rc != 0:
        return None, f"ls-remote to {remote!r} failed — check network/auth"
    for line in out.splitlines():
        if line.startswith("ref:") and "\t" in line:
            ref = line.split("\t", 1)[0].replace("ref:", "").strip()
            if ref.startswith("refs/heads/"):
                return ref.removeprefix("refs/heads/"), None
    return None, None


# ── Target resolution helpers ────────────────────────────────────────────────


def _find_target_matches(
    target_arg: str, all_remotes: list[str]
) -> list[tuple[str, str]]:
    """Return all (remote, branch) parses of target_arg from configured remotes.

    Git allows remote names containing slashes (e.g. 'team/upstream').
    When remotes 'team' and 'team/upstream' both exist, the target
    'team/upstream/main' has two valid parses: (team, upstream/main) and
    (team/upstream, main).  Callers check the length: 0 → not found;
    1 → unambiguous; 2+ → ambiguous and must Surface for clarification.
    """
    return [
        (remote, target_arg[len(remote) + 1:])
        for remote in all_remotes
        if target_arg.startswith(f"{remote}/") and target_arg[len(remote) + 1:]
    ]


def _valid_branch(branch: str) -> bool:
    """Validate a branch name using git's own rules (not an ASCII allowlist).

    Delegates to git check-ref-format so valid refs like 'release+stable',
    'topic#42', or non-ASCII names are accepted.  shlex.quote in the Surface
    output handles shell-escaping regardless of what characters are present.
    """
    rc, _ = _run(["git", "check-ref-format", f"refs/heads/{branch}"])
    return rc == 0


# ── Argument parser ──────────────────────────────────────────────────────────


class _Parser(argparse.ArgumentParser):
    """ArgumentParser that emits Surface JSON instead of printing to stderr."""

    def error(self, message: str) -> None:
        _surface(f"argument error: {message}")
        sys.exit(1)


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = _Parser(
        prog="check-base-freshness",
        description="Verify HEAD is current against the merge target.",
    )
    parser.add_argument(
        "--target",
        metavar="REMOTE/BRANCH",
        help=(
            "explicit merge target, e.g. 'origin/main'. "
            "Required when more than one remote is configured. "
            "For remotes beginning with '-', use the equals form: "
            "--target=-mirror/main"
        ),
    )
    args = parser.parse_args()

    # In-progress rebase check first — applies even to local-only repos.
    # --git-path resolves correctly inside linked worktrees (.git is a file).
    for state_dir in ("rebase-merge", "rebase-apply"):
        rc_gp, path = _run(["git", "rev-parse", "--git-path", state_dir])
        if rc_gp == 0 and path and Path(path).exists():
            return _surface("rebase already in progress — resolve or abort it first")

    # Probe configured remotes.  rc != 0 means git itself failed (safe-directory
    # or permission error) — fail closed rather than pretending there's no remote.
    rc, remotes_raw = _run(["git", "remote"])
    if rc != 0:
        return _surface(
            "git remote probe failed — check repository permissions or safe-directory config"
        )
    if not remotes_raw:
        if args.target is not None:
            if not args.target:
                return _surface(
                    "--target value is empty — pass REMOTE/BRANCH form, e.g. 'origin/main'"
                )
            return _surface(
                f"--target {args.target!r} was supplied but this repository "
                "has no remotes configured — verify the remote exists"
            )
        return _ok("no remote configured")

    all_remotes = [r.strip() for r in remotes_raw.splitlines() if r.strip()]

    # Check HEAD state before any network work.
    # rc != 0 means the repo has no commits yet (unborn HEAD) — we Surface
    # rather than silently approving, since a nonempty remote may be ahead.
    # rc == 0 && cur == "HEAD" is a true detached HEAD; skip the network check.
    rc_cur, cur = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if rc_cur != 0:
        return _surface(
            "HEAD is unresolvable — repository may have no commits yet; "
            "make an initial commit before running the work-loop"
        )
    if not cur or cur == "HEAD":
        return _ok("not on a branch (detached HEAD)")

    # Validate --target or require it when the integration branch is ambiguous
    if args.target is not None:
        if not args.target:
            return _surface(
                "--target value is empty — pass REMOTE/BRANCH form, e.g. 'origin/main'"
            )
        if "/" not in args.target:
            return _surface(
                f"--target {args.target!r} must be in REMOTE/BRANCH form, "
                "e.g. 'origin/main'"
            )
        matches = _find_target_matches(args.target, all_remotes)
        if not matches:
            return _surface(
                f"--target {args.target!r} does not start with a configured "
                f"remote name ({all_remotes}) — verify the remote name and "
                "REMOTE/BRANCH form"
            )
        if len(matches) > 1:
            parses = "; ".join(f"remote={r!r} branch={b!r}" for r, b in matches)
            return _surface(
                f"--target {args.target!r} is ambiguous — it matches multiple "
                f"configured remotes ({parses}); rename the remotes so the "
                "intended REMOTE/BRANCH is unambiguous, or choose a --target "
                "value that starts with exactly one configured remote name"
            )
        fetch_remote, branch = matches[0]
        if not _valid_branch(branch):
            return _surface(
                f"--target branch {branch!r} is not a valid git branch name"
            )
        target = args.target
    elif len(all_remotes) > 1:
        return _surface(
            f"multiple remotes {all_remotes} — pass --target REMOTE/BRANCH "
            "to identify the integration branch (e.g. --target upstream/main)"
        )
    else:
        fetch_remote = all_remotes[0]
        # Resolve the remote's current HEAD live before fetching, so that
        # renamed default branches and single-branch clones are handled
        # correctly regardless of the local refspec configuration.
        branch, live_err = _live_remote_head_branch(fetch_remote)
        if live_err is not None:
            return _surface(live_err)
        if not branch:
            return _surface(
                f"could not determine {fetch_remote!r} HEAD — "
                "pass --target REMOTE/BRANCH explicitly"
            )
        if not _valid_branch(branch):
            return _surface(
                f"remote HEAD branch name {branch!r} is not valid — "
                "pass --target REMOTE/BRANCH explicitly"
            )
        target = f"{fetch_remote}/{branch}"

    # Fetch the target branch explicitly with a force-update refspec so that
    # single-branch clones and force-pushed stacked branches are refreshed.
    refspec = f"+refs/heads/{branch}:refs/remotes/{fetch_remote}/{branch}"
    rc, _, fetch_err = _run_with_stderr(
        ["git", "fetch", "--no-tags", "--recurse-submodules=no", "--", fetch_remote, refspec],
        timeout=_NETWORK_TIMEOUT,
    )
    if rc == 124:
        return _surface(f"git fetch {fetch_remote!r} timed out — check network/auth", target)
    if rc != 0:
        # Match git's own not-found wording only. A broader test (any stderr
        # mentioning 'remote ref') also catches transport failures that echo a
        # URL containing the phrase, and sends the agent off to correct a
        # branch name when the real cause was auth or network.
        if "couldn't find remote ref" in fetch_err.lower():
            return _surface(
                f"git fetch {fetch_remote!r}: branch {branch!r} not found on remote — "
                "verify the branch name in --target",
                target,
            )
        return _surface(f"git fetch {fetch_remote!r} failed — check network/auth", target)

    # Use the full remote-tracking ref for comparison to avoid DWIM resolving
    # a local branch or tag that shadows the shorthand 'REMOTE/BRANCH'.
    full_ref = f"refs/remotes/{fetch_remote}/{branch}"

    rc, count_str = _run(["git", "rev-list", "--count", f"HEAD..{full_ref}"])
    if rc != 0:
        return _surface(f"could not compare HEAD against {full_ref!r}", target)

    # Fail closed. Falling back to 0 here would read as 'head is current' on
    # the next line — the one answer this script must never give by accident.
    # isdecimal, not isdigit: '²'.isdigit() is True but int('²') raises.
    if not count_str.isdecimal():
        return _surface(
            "could not read the commit count from git rev-list against "
            f"{full_ref!r} — cannot confirm HEAD is current",
            target,
        )
    count = int(count_str)
    if count == 0:
        return _ok("head is current", target)

    # Guard against histories with no common ancestor (orphan branch, shallow
    # clone, or repointed remote) before recommending any rebase strategy.
    # git merge-base exits 1 when no common ancestor exists.
    rc_mb, _ = _run(["git", "merge-base", "HEAD", full_ref])
    if rc_mb != 0:
        return _surface(
            f"branch is {count} commit(s) behind {target!r} but HEAD and "
            f"{target!r} share no common ancestor — rebase is unsafe "
            "(orphan branch, shallow clone, or repointed remote); "
            "verify the target and repository history before rebasing",
            target,
        )

    # Detect merge commits in the local-only range. Plain rebase flattens them
    # and can lose merge-only conflict resolutions.
    rc_mc, merge_log = _run(["git", "log", "--merges", "--oneline", f"{full_ref}..HEAD"])
    has_local_merges = rc_mc == 0 and bool(merge_log)

    # Build a Surface message that tells the agent exactly what to do.
    # _quote_for_shell always returns None on Windows — cmd.exe, PowerShell,
    # and Git Bash each expand different ref-name characters inside double-
    # quoted strings, so no single quoting strategy is safe across all three.
    # On POSIX, shlex.quote single-quotes the ref, which is always injection-safe.
    # Use the full tracking ref for the same reason as the rev-list above.
    quoted = _quote_for_shell(full_ref)
    if quoted is not None:
        if has_local_merges:
            rebase_hint = (
                f"run: git rebase --rebase-merges {quoted} "
                "(local range has merge commits — plain rebase would flatten them)"
            )
        else:
            rebase_hint = f"run: git rebase {quoted}"
    else:
        rebase_hint = (
            f"rebase onto: {full_ref} "
            "(Windows: no runnable rebase command emitted — the ref name has no "
            "quoting that is safe in cmd.exe, PowerShell and Git Bash at once; "
            "invoke git directly as a subprocess with this ref as a literal "
            "argument. Commands elsewhere in this message interpolate nothing "
            "and are safe to run verbatim.)"
        )
        if has_local_merges:
            rebase_hint += "; add --rebase-merges (local range has merge commits)"
    rc_status, porcelain = _run(["git", "status", "--porcelain"])
    if rc_status != 0:
        return _surface(
            "git status --porcelain failed — index may be corrupt or unreadable; "
            "resolve the repository state before rebasing",
            target,
        )
    if porcelain:
        lines = [ln for ln in porcelain.splitlines() if ln.strip()]
        _conflict_xy = {"UU", "AA", "DD", "AU", "UA", "DU", "UD"}
        has_conflicts = any(ln[:2] in _conflict_xy for ln in lines)
        has_untracked = any(ln.startswith("??") for ln in lines)
        if has_conflicts:
            # Both escapes are closed here, and for different reasons: git
            # stash refuses to write an index with unmerged entries, while
            # 'git commit -a' — the very command the clean-tree branch below
            # recommends — happily stages and commits the conflict markers.
            return _surface(
                f"branch is {count} commit(s) behind {target!r} and has "
                "unmerged files — resolve the conflicts before rebasing "
                "('git stash' refuses them, and 'git commit -a' would commit "
                "the conflict markers)",
                target,
            )
        # Commit, don't stash. refs/stash is not a per-worktree ref, so every
        # linked worktree of this repository shares one stash stack — work
        # stashed here can be popped from another worktree and lost. The
        # commit command carries no interpolated data, so unlike rebase_hint
        # it is safe to emit verbatim on every platform.
        commit_cmd = (
            'git add -A, then git commit -m "chore: wip"'
            if has_untracked
            else 'git commit -a -m "chore: wip"'
        )
        return _surface(
            f"branch is {count} commit(s) behind {target!r} and has "
            "uncommitted changes. Commit them on this branch rather than "
            "stashing — the stash stack is shared across this repository's "
            "worktrees, so work stashed here can be popped from another one; "
            "undo the wip commit after rebasing with 'git reset HEAD~1' "
            "(mixed, not --soft: it restores untracked files as untracked). "
            f"Run {commit_cmd}, then {rebase_hint}",
            target,
        )
    return _surface(
        f"branch is {count} commit(s) behind {target!r} — {rebase_hint}",
        target,
    )


if __name__ == "__main__":
    sys.exit(main())
