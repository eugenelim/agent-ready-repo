#!/usr/bin/env python3
"""Run the OKF compiler's check mode over every pack declaring managed OKF metadata.

Check mode re-renders each declared bundle and compares the result against the
committed tree, so "this command passed on this platform" is the evidence that
the committed output is what this platform produces. That is why the gate runs
on Linux and Windows rather than only where the output was authored.

It lives in its own script rather than inline in one aggregator because two
callers need it: the Linux path reaches it through
`tools/catalogue/pre_pr_catalogue.py`, the Windows path through the compat
suite's stage list. Two copies of the pack-discovery rule would eventually
disagree about which packs are managed, and the platform that scanned fewer
packs would report a pass it had not earned.

Every way of scanning fewer packs than exist is therefore an error here, not a
`continue`: a missing `packs/` tree, an unreadable `pack.toml`, and a
wrong-shaped `metadata.okf` all fail loudly. A gate that silently narrows its
own scope is worse than no gate, because it reports success.

Usage:
    python tools/check-okf-managed-packs.py [--root DIR]

Exits 0 when every managed pack checks clean, 1 otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

_COMPILER_RELATIVE = Path(
    "packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py"
)

# A hung compiler would otherwise block until the CI job's own ceiling, which is
# reported as a job timeout and names neither this gate nor the pack.
_COMPILE_TIMEOUT_SECONDS = 600


def compiler_script(repo_root: Path) -> Path:
    """Path to the authoring compiler the catalogue ships as a Skill script."""
    return repo_root / _COMPILER_RELATIVE


def managed_pack_dirs(repo_root: Path) -> list[Path]:
    """Every pack directory declaring managed OKF metadata, in sorted order.

    This is repo-level experiment plumbing, not public catalogue discovery:
    underscore-prefixed pilot packs are intentionally included here while normal
    list/install/publish surfaces still skip them.

    Raises ``ValueError`` when a pack cannot be classified, so a typo in an OKF
    block removes the pack from the gate loudly rather than silently.
    """
    packs_root = repo_root / "packs"
    if not packs_root.is_dir():
        raise ValueError(f"no packs/ directory under {repo_root}")
    managed: list[Path] = []
    for pack_dir in sorted(packs_root.iterdir(), key=lambda path: path.name):
        # `packs/` also holds a few authoring `.md` files; only directories are
        # candidates. A directory without a manifest IS an error — that is the
        # shape a half-deleted or half-created pack takes, and skipping it is
        # how a pack leaves the gate unnoticed.
        if not pack_dir.is_dir():
            continue
        pack_toml = pack_dir / "pack.toml"
        if not pack_toml.is_file():
            raise ValueError(f"{pack_dir.name}/ has no pack.toml")
        try:
            data = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(f"{pack_dir.name}/pack.toml is unreadable: {exc}") from exc
        pack = data.get("pack")
        if not isinstance(pack, dict):
            raise ValueError(
                f"{pack_dir.name}/pack.toml has no [pack] table"
                if pack is None
                else f"{pack_dir.name}/pack.toml declares pack as "
                f"{type(pack).__name__}, not a table"
            )
        metadata = pack.get("metadata")
        # A pack with no metadata, or metadata carrying no okf block, is simply
        # not an OKF pack — the only sanctioned skip in this loop.
        if metadata is None:
            continue
        if not isinstance(metadata, dict):
            raise ValueError(
                f"{pack_dir.name}/pack.toml declares pack.metadata as "
                f"{type(metadata).__name__}, not a table"
            )
        if "okf" not in metadata:
            continue
        okf = metadata["okf"]
        if not isinstance(okf, dict):
            raise ValueError(
                f"{pack_dir.name}/pack.toml declares metadata.okf as "
                f"{type(okf).__name__}, not a table"
            )
        managed.append(pack_dir)
    return managed


def _check_pack(compiler: Path, repo_root: Path, pack_dir: Path) -> bool:
    """Check one pack; return True when clean, forwarding the compiler's output."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(compiler),
                "--root",
                str(repo_root),
                "--pack",
                pack_dir.name,
                "--check",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            # The compiler's diagnostics are the only way to tell an OKF011 drift
            # from an OKF012 non-determinism. Losing them to a decode error would
            # leave a Windows-only failure with nothing to act on.
            errors="replace",
            check=False,
            timeout=_COMPILE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(
            f"okf-check: ✖ {pack_dir.name} timed out after "
            f"{_COMPILE_TIMEOUT_SECONDS}s",
            file=sys.stderr,
        )
        return False

    if result.returncode != 0:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        print(f"okf-check: ✖ {pack_dir.name} failed", file=sys.stderr)
        return False

    print(f"okf-check: ✓ {pack_dir.name}")
    return True


def main(argv: list[str] | None = None) -> int:
    # Windows cp1252 guard. Inside main() so importing this module for its
    # helpers does not reconfigure stdout for an entire pytest process, and
    # guarded because a redirected stream is not always a real text file.
    for stream, errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors=errors)

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        default=str(_REPO_ROOT),
        help="catalogue repository root (default: this checkout)",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.root).resolve()
    try:
        packs = managed_pack_dirs(repo_root)
    except ValueError as exc:
        print(f"okf-check: ✖ {exc}", file=sys.stderr)
        return 1

    if not packs:
        print("okf-check: ✓ no packs declare managed OKF metadata")
        return 0

    compiler = compiler_script(repo_root)
    # Managed packs with no compiler is a broken checkout, not a reason to report
    # clean — the packs declare output that nothing can verify.
    if not compiler.is_file():
        print(
            f"okf-check: ✖ {len(packs)} managed pack(s) but no compiler at "
            f"{_COMPILER_RELATIVE}",
            file=sys.stderr,
        )
        return 1

    # Every pack runs even after one fails. A platform-specific defect usually
    # affects more than one pack, and each check costs about a second; stopping
    # at the first would cost another full Windows job to learn the rest.
    failed: list[str] = []
    for pack_dir in packs:
        if not _check_pack(compiler, repo_root, pack_dir):
            failed.append(pack_dir.name)
    if failed:
        print(
            f"okf-check: ✖ {len(failed)} of {len(packs)} pack(s) failed: "
            f"{', '.join(failed)}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
