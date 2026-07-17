"""Publish dist/claude-plugins/ to the claude-plugins-dist branch.

Excludes catalogue-curation/ (operator-only pack, not for end-user installation).
Includes marketplace.json at the branch root.
Skips committing when the tree is byte-for-byte identical to the last publish.

Run from the repo root:
  python3 tools/publish-claude-plugins.py

Invoked by .github/workflows/publish-claude-plugins.yml after `make build`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

DIST_DIR = Path("dist/claude-plugins")
BRANCH = "claude-plugins-dist"
EXCLUDE = {"catalogue-curation"}  # operator-only pack


def _run(cmd: str, **kwargs) -> subprocess.CompletedProcess:
    print(f"+ {cmd}", flush=True)
    return subprocess.run(cmd, shell=True, check=True, **kwargs)


def _check(cmd: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, check=False, **kwargs)


def _write_filtered_marketplace(src: Path, dest: Path) -> None:
    """Copy marketplace.json with excluded packs stripped from the plugins list."""
    data = json.loads(src.read_text(encoding="utf-8"))
    if "plugins" in data:
        data["plugins"] = [p for p in data["plugins"] if p.get("name") not in EXCLUDE]
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote filtered marketplace.json (excluded: {', '.join(EXCLUDE)})")


def main() -> None:
    if not DIST_DIR.exists():
        print(
            f"error: {DIST_DIR} not found — run `make build` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    sha = subprocess.check_output(
        "git rev-parse --short HEAD", shell=True
    ).decode().strip()

    worktree = Path("/tmp/claude-plugins-publish")
    if worktree.exists():
        shutil.rmtree(worktree)

    # Does the target branch already exist on remote?
    probe = _check(
        f"git ls-remote --heads origin {BRANCH}",
        capture_output=True,
        text=True,
    )
    branch_exists = bool(probe.stdout.strip())

    if branch_exists:
        _run(f"git fetch origin {BRANCH}")
        _run(f"git worktree add {worktree} origin/{BRANCH}")
    else:
        # --orphan takes branch name via -b; the positional commit-ish is incompatible.
        _run(f"git worktree add --orphan -b {BRANCH} {worktree}")

    try:
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
        _run(f"git -C {worktree} add -A")

        # Skip the commit if nothing changed.
        no_diff = _check(f"git -C {worktree} diff --cached --quiet")
        if no_diff.returncode == 0:
            print("No changes to publish — branch is up to date.")
            return

        _run(
            f'git -C {worktree} commit -m '
            f'"chore: publish claude-plugins [main@{sha}]"'
        )
        _run(f"git -C {worktree} push origin HEAD:{BRANCH}")
        print(f"Published to {BRANCH}.")
    finally:
        _run(f"git worktree remove --force {worktree}")


if __name__ == "__main__":
    main()
