"""Windows-portability lint — refuse packs that carry content that
will break on native Windows.

Two checks, applied to every file and directory under each pack's
`seeds/` and `.apm/` subtrees:

  1. **No symlinks** — `Path.is_symlink()` against the entry. Windows
     symlink creation requires Developer Mode or admin privileges, and
     packs distributed via git/zip/zipapp lose symlink fidelity along
     the way. A pack that ships symlinks is hostile to a slice of
     adopters, so reject at build time rather than at install time.
  2. **No Windows-poisonous names** — every path is run through
     `safety.assert_portable_name`, which rejects reserved device names
     (CON/PRN/AUX/NUL/COM1-9/LPT1-9), trailing dots or spaces, and the
     `<>:"|?*` character set. The guard runs on every OS because pack
     content authored on macOS still ships to Windows.

The lint is Python-only so it runs on every CI platform without
shelling out, and it is wired into `make build` / `make build-self` /
`make build-check` as a hard prerequisite — a failing lint stops the
build before any artefact is written.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentbundle.safety import PathJailError, assert_portable_name

# Subtrees in a pack that ship to adopters. `seeds/` is the
# adopter-facing surface; `.apm/` is the primitives the APM adapter
# unpacks. Both must be portable. `pack.toml` and `.claude-plugin/`
# live outside the walk because their schemas already constrain
# their content.
_PACK_SUBTREES = ("seeds", ".apm")


def lint_pack(pack_dir: Path) -> list[str]:
    """Return a list of human-readable violation strings for one pack.

    Empty list ⇒ clean. Each string is suitable for stderr emission;
    callers decide how to format / exit.
    """
    findings: list[str] = []
    for subtree_name in _PACK_SUBTREES:
        subtree = pack_dir / subtree_name
        if not subtree.exists():
            continue
        # Walk via `rglob("*")` so directory entries are also checked;
        # a reserved-name *directory* (e.g. `seeds/NUL/`) is just as
        # poisonous as a reserved-name file.
        for entry in sorted(subtree.rglob("*")):
            relpath = entry.relative_to(pack_dir).as_posix()
            if entry.is_symlink():
                findings.append(
                    f"{pack_dir.name}: symlink not portable to Windows: {relpath}"
                )
                # Don't descend into symlinks — they may target outside
                # the pack and trigger spurious findings. The symlink
                # itself is already the violation.
                continue
            try:
                assert_portable_name(relpath)
            except PathJailError as exc:
                findings.append(f"{pack_dir.name}: {exc}")
    return findings


def lint_all_packs(packs_dir: Path) -> dict[str, list[str]]:
    """Walk every immediate subdirectory of `packs_dir` that contains a
    `pack.toml`, return `{pack_name: [findings...]}`.

    Missing `packs_dir` returns an empty dict — caller decides whether
    that's an error in their context.
    """
    result: dict[str, list[str]] = {}
    if not packs_dir.exists():
        return result
    for entry in sorted(packs_dir.iterdir()):
        if not entry.is_dir():
            continue
        if not (entry / "pack.toml").exists():
            continue
        result[entry.name] = lint_pack(entry)
    return result


def cmd_lint_packs(args: argparse.Namespace) -> int:
    """argparse entrypoint. Exit code:
        0 — every pack clean
        1 — at least one finding
    """
    packs_dir = Path(args.packs_dir).resolve()
    if not packs_dir.exists():
        print(f"lint-packs: packs-dir not found: {packs_dir}", file=sys.stderr)
        return 1
    results = lint_all_packs(packs_dir)
    total = 0
    for pack_name, findings in results.items():
        for finding in findings:
            print(finding, file=sys.stderr)
            total += 1
    if total:
        print(
            f"lint-packs: {total} portability violation(s) across "
            f"{sum(1 for f in results.values() if f)} pack(s)",
            file=sys.stderr,
        )
        return 1
    return 0
