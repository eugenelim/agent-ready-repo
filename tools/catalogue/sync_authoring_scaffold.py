#!/usr/bin/env python3
"""Sync the catalogue authoring scaffold between the repo root and the
AgentBundle package-data projection at
``packages/agentbundle/agentbundle/_data/catalogue-scaffold/``.

Usage:
  python3 tools/catalogue/sync_authoring_scaffold.py --check   # exits non-zero if out of sync
  python3 tools/catalogue/sync_authoring_scaffold.py --write   # overwrites _data/ from repo root
  python3 tools/catalogue/sync_authoring_scaffold.py --check --verbose  # show diffs

The canonical source is always the repo root.  The _data/ copy is a projection
that must be kept byte-identical to the source.  Run --write after any change
to packs/README.md, packs/AGENTS.md, packs/_example/**, profiles/README.md,
profiles/AGENTS.md, profiles/_example/**, or
guides/_shared/reference/catalogue-ci-contract.md.

`make build-self` and `make build-check` invoke this with --check to gate CI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_ROOT = (
    _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "catalogue-scaffold"
)

# Pairs: (repo-root source path, relative path inside catalogue-scaffold/).
# Order is stable; new files must be added here to participate in sync.
_SYNC_PAIRS: list[tuple[Path, str]] = [
    (_REPO_ROOT / "packs" / "README.md", "packs/README.md"),
    (_REPO_ROOT / "packs" / "AGENTS.md", "packs/AGENTS.md"),
    (_REPO_ROOT / "packs" / "_example" / "pack.toml", "packs/_example/pack.toml"),
    (
        _REPO_ROOT / "packs" / "_example" / ".claude-plugin" / "plugin.json",
        "packs/_example/.claude-plugin/plugin.json",
    ),
    (
        _REPO_ROOT / "packs" / "_example" / ".apm" / "skills" / "example-skill" / "SKILL.md",
        "packs/_example/.apm/skills/example-skill/SKILL.md",
    ),
    (
        _REPO_ROOT / "packs" / "_example" / ".apm" / "skills" / "example-skill"
        / "evals" / "eval_queries.json",
        "packs/_example/.apm/skills/example-skill/evals/eval_queries.json",
    ),
    (_REPO_ROOT / "packs" / "_example" / "README.md", "packs/_example/README.md"),
    (_REPO_ROOT / "profiles" / "README.md", "profiles/README.md"),
    (_REPO_ROOT / "profiles" / "AGENTS.md", "profiles/AGENTS.md"),
    (_REPO_ROOT / "profiles" / "_example" / "profile.toml", "profiles/_example/profile.toml"),
    (_REPO_ROOT / "profiles" / "_example" / "README.md", "profiles/_example/README.md"),
    (
        _REPO_ROOT / "guides" / "_shared" / "reference" / "catalogue-ci-contract.md",
        "guides/_shared/reference/catalogue-ci-contract.md",
    ),
    (
        _REPO_ROOT / "guides" / "_shared" / "reference" / "catalogue-authoring-standards.md",
        "guides/_shared/reference/catalogue-authoring-standards.md",
    ),
    (
        _REPO_ROOT / "tests" / "conformance" / "test_gemini_admissibility.py",
        "tests/conformance/test_gemini_admissibility.py",
    ),
    (
        _REPO_ROOT / "tests" / "conformance" / "test_pack_metadata.py",
        "tests/conformance/test_pack_metadata.py",
    ),
    (
        _REPO_ROOT / "tests" / "conformance" / "test_shared_library_boundaries.py",
        "tests/conformance/test_shared_library_boundaries.py",
    ),
]


def _check(verbose: bool) -> list[str]:
    """Return a list of out-of-sync relative paths (empty = clean)."""
    drifts: list[str] = []
    for src, rel in _SYNC_PAIRS:
        dst = _DATA_ROOT / rel
        if not src.exists():
            print(f"  MISSING source: {src.relative_to(_REPO_ROOT)}", file=sys.stderr)
            drifts.append(rel)
            continue
        if not dst.exists():
            drifts.append(rel)
            if verbose:
                print(f"  MISSING in _data: {rel}")
            continue
        src_bytes = src.read_bytes()
        dst_bytes = dst.read_bytes()
        if src_bytes != dst_bytes:
            drifts.append(rel)
            if verbose:
                print(f"  DRIFT: {rel}")
    drifts.extend(_check_manifest(verbose=verbose))
    return drifts


def _check_manifest(*, verbose: bool = False) -> list[str]:
    """Report drift between manifest.json's hashes and the projected files.

    Content equality between the repo root and _data/ is not sufficient:
    `agentbundle catalogue init` verifies these recorded SHA-256s at adopter
    runtime and fails init on a mismatch, so a stale manifest breaks adopters
    while a content-only check reports "ok".
    """
    manifest_path = _DATA_ROOT / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if verbose:
            print("  DRIFT: manifest.json is missing")
        return ["manifest.json (missing)"]
    except (OSError, json.JSONDecodeError):
        if verbose:
            print("  DRIFT: manifest.json is unreadable")
        return ["manifest.json (unreadable)"]

    recorded = manifest.get("files", {})
    expected = {
        rel: hashlib.sha256((_DATA_ROOT / rel).read_bytes()).hexdigest()
        for _src, rel in _SYNC_PAIRS
        if (_DATA_ROOT / rel).exists()
    }
    drifts = []
    for rel in sorted(set(recorded) | set(expected)):
        if recorded.get(rel) != expected.get(rel):
            drifts.append(f"manifest.json:{rel}")
            if verbose:
                print(f"  DRIFT: manifest.json hash for {rel}")
    return drifts


def _write_manifest() -> None:
    """Write manifest.json with SHA-256 hashes of all synced files."""
    files: dict[str, str] = {}
    for _src, rel in _SYNC_PAIRS:
        dst = _DATA_ROOT / rel
        if dst.exists():
            files[rel] = hashlib.sha256(dst.read_bytes()).hexdigest()
    manifest = {"version": 1, "files": files}
    manifest_path = _DATA_ROOT / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("  synced: manifest.json")


def _write() -> None:
    """Overwrite every _data/ copy from its repo-root source."""
    for src, rel in _SYNC_PAIRS:
        dst = _DATA_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        print(f"  synced: {rel}")
    _write_manifest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="Report drift and exit non-zero if out of sync.")
    group.add_argument("--write", action="store_true",
                       help="Sync _data/ from repo root (overwrites).")
    parser.add_argument("--verbose", action="store_true",
                        help="Show per-file details during --check.")
    args = parser.parse_args()

    if args.write:
        _write()
        print("sync_authoring_scaffold: ok — _data/ is up to date.")
        return 0

    # --check
    drifts = _check(verbose=args.verbose)
    if drifts:
        print(
            f"sync_authoring_scaffold: DRIFT — {len(drifts)} file(s) out of sync:\n"
            + "\n".join(f"  {r}" for r in drifts),
            file=sys.stderr,
        )
        print("Run: python3 tools/catalogue/sync_authoring_scaffold.py --write", file=sys.stderr)
        return 1
    print("sync_authoring_scaffold: ok — _data/ matches repo root.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
