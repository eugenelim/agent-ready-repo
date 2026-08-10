"""Publish dist/claude-plugins/ to the claude-plugins-dist branch.

Excludes catalogue-curation/ (operator-only pack, not for end-user installation).
Strips the catalogue-curation entry from marketplace.json before publishing.
Includes all other content, including marketplace.json, at the branch root.
Skips committing when the tree is byte-for-byte identical to the last publish.

Run from the repo root:
  python3 tools/catalogue/publish_claude_plugins.py

Invoked by .github/workflows/publish-claude-plugins.yml after `make build`.
"""

from __future__ import annotations

import importlib.util as _ilu
import json
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

DIST_DIR = Path("dist/claude-plugins")
PACKS_DIR = Path("packs")
BRANCH = "claude-plugins-dist"
EXCLUDE = {"catalogue-curation"}  # operator-only pack


_ps = _ilu.spec_from_file_location(
    "pack_scope", Path(__file__).resolve().parents[1] / "pack_scope.py"
)
_pack_scope = _ilu.module_from_spec(_ps)
_ps.loader.exec_module(_pack_scope)
_allowed_scopes = _pack_scope.allowed_scopes


def _publishable_from_source() -> set[str]:
    """Re-derive the publishable set from ``packs/``, never from ``dist/``.

    Re-deriving from ``dist/`` would compare the tree against itself and could
    not catch the stale directory this check exists for: ``make build`` has no
    dependency on ``clean``, so a narrowed pack's old declaration survives in
    ``dist/`` and would republish contrary to current intent.
    """
    if not PACKS_DIR.is_dir():
        return set()
    names: set[str] = set()
    for pack_dir in sorted(PACKS_DIR.iterdir()):
        if not pack_dir.is_dir() or pack_dir.name.startswith("_"):
            continue
        pack_toml = pack_dir / "pack.toml"
        if not pack_toml.exists():
            continue
        if not (pack_dir / ".claude-plugin" / "plugin.json").exists():
            continue
        meta = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
        if "user" in _allowed_scopes(meta):
            names.add(pack_dir.name)
    return names


def _assert_membership(published_dirs: set[str], marketplace_names: set[str]) -> None:
    """Fail loud before pushing.

    Three checks, none of which the build's own gates cover:

    1. every published directory is publishable per the *source* tree;
    2. the published marketplace names equal the published directories — an
       entry whose directory is absent is a dangling fetch for every adopter;
    3. the repo-root marketplace is a subset of what is published, so the
       branch cannot advertise less than the root claims.

    This catches build/publish desync and stale-``dist/`` republication. It does
    **not** constrain an actor: the same push that widens a pack's scopes can
    edit this file, so publication remains gated by push access to `main`.
    """
    # `- EXCLUDE` here is belt-and-braces: `main()` already skips EXCLUDE names
    # before they reach `published_dirs`, so on the real path this subtraction
    # changes nothing. Kept because this function is also called directly (by
    # the sibling gate test), where the caller controls both sets. The
    # subtraction that *is* load-bearing is the one on the root marketplace
    # below, whose input this function does not construct.
    expected = _publishable_from_source() - EXCLUDE
    stale = published_dirs - expected
    if stale:
        raise SystemExit(
            "publish: refusing — these directories are not publishable from the "
            f"source tree (stale dist/, or scopes narrowed since the build): "
            f"{', '.join(sorted(stale))}"
        )
    dangling = marketplace_names - published_dirs
    if dangling:
        raise SystemExit(
            "publish: refusing — marketplace entries with no published "
            f"directory: {', '.join(sorted(dangling))}"
        )
    orphaned = published_dirs - marketplace_names
    if orphaned:
        raise SystemExit(
            "publish: refusing — published directories with no marketplace "
            f"entry: {', '.join(sorted(orphaned))}"
        )
    root = Path(".claude-plugin/marketplace.json")
    if root.exists():
        root_names = {
            p.get("name")
            for p in json.loads(root.read_text(encoding="utf-8")).get("plugins", [])
        } - EXCLUDE
        unbacked = root_names - published_dirs
        if unbacked:
            raise SystemExit(
                "publish: refusing — the repo-root marketplace advertises packs "
                f"the branch does not publish: {', '.join(sorted(unbacked))}"
            )


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
        published_dirs: set[str] = set()
        marketplace_names: set[str] = set()
        for item in sorted(DIST_DIR.iterdir()):
            # Name exclusion is applied FIRST and is exempt from the membership
            # assertion below — catalogue-curation is operator-only, a different
            # reason from being repo-only, and folding the two would re-publish
            # it if its scopes were ever widened.
            if item.name in EXCLUDE:
                print(f"  skip {item.name} (excluded from publish)")
                continue
            dest = worktree / item.name
            if item.is_dir():
                published_dirs.add(item.name)
                shutil.copytree(item, dest)
            elif item.name == "marketplace.json":
                _write_filtered_marketplace(item, dest)
                marketplace_names = {
                    p.get("name")
                    for p in json.loads(dest.read_text(encoding="utf-8")).get(
                        "plugins", []
                    )
                }
            else:
                shutil.copy2(item, dest)

        _assert_membership(published_dirs, marketplace_names)

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
