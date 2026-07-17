"""Publish dist/claude-plugins/ to the claude-plugins-dist branch.

Excludes catalogue-curation/ (operator-only pack, not for end-user installation).
Strips the catalogue-curation entry from marketplace.json before publishing.
Includes all other content, including marketplace.json, at the branch root.
Skips committing when the tree is byte-for-byte identical to the last publish.

Run from the repo root:
  python3 tools/publish-claude-plugins.py

Invoked by .github/workflows/publish-claude-plugins.yml after `make build`.
"""

from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DIST_DIR = Path("dist/claude-plugins")
BRANCH = "claude-plugins-dist"
EXCLUDE = {"catalogue-curation"}  # operator-only pack


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print(f"+ {shlex.join(cmd)}", flush=True)
    return subprocess.run(cmd, check=True, **kwargs)


def _check(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, **kwargs)


def _write_filtered_marketplace(src: Path, dest: Path) -> None:
    """Copy marketplace.json with excluded packs stripped from the plugins list."""
    data = json.loads(src.read_text(encoding="utf-8"))
    if "plugins" in data:
        data["plugins"] = [p for p in data["plugins"] if p.get("name") not in EXCLUDE]
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote filtered marketplace.json (excluded: {', '.join(sorted(EXCLUDE))})")


def main() -> None:
    if not DIST_DIR.exists():
        print(
            f"error: {DIST_DIR} not found — run `make build` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"]
    ).decode().strip()

    # Does the target branch already exist on remote?
    probe = _check(
        ["git", "ls-remote", "--heads", "origin", BRANCH],
        capture_output=True,
        text=True,
    )
    branch_exists = bool(probe.stdout.strip())

    worktree = Path(tempfile.mkdtemp(prefix="claude-plugins-publish-"))
    # mkdtemp creates the dir; git worktree needs it absent or empty.
    worktree.rmdir()

    try:
        if branch_exists:
            _run(["git", "fetch", "origin", BRANCH])
            _run(["git", "worktree", "add", str(worktree), f"origin/{BRANCH}"])
        else:
            # --orphan takes the branch name via -b; positional commit-ish is incompatible.
            _run(["git", "worktree", "add", "--orphan", "-b", BRANCH, str(worktree)])

        # Remove all tracked content from the worktree (preserve .git).
        for item in worktree.iterdir():
            if item.name == ".git":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Copy dist/claude-plugins/ into the worktree, skipping excluded packs.
        # marketplace.json is included but with excluded packs stripped from its list.
        for item in sorted(DIST_DIR.iterdir()):
            if item.name in EXCLUDE:
                print(f"  skip {item.name} (excluded from publish)")
                continue
            dest = worktree / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            elif item.name == "marketplace.json":
                _write_filtered_marketplace(item, dest)
            else:
                shutil.copy2(item, dest)

        # Stage everything.
        _run(["git", "-C", str(worktree), "add", "-A"])

        # Skip the commit if nothing changed.
        no_diff = _check(["git", "-C", str(worktree), "diff", "--cached", "--quiet"])
        if no_diff.returncode == 0:
            print("No changes to publish — branch is up to date.")
            return

        _run([
            "git", "-C", str(worktree), "commit",
            "-m", f"chore: publish claude-plugins [main@{sha}]",
        ])
        _run(["git", "-C", str(worktree), "push", "origin", f"HEAD:{BRANCH}"])
        print(f"Published to {BRANCH}.")
    finally:
        _run(["git", "worktree", "remove", "--force", str(worktree)])


if __name__ == "__main__":
    main()
