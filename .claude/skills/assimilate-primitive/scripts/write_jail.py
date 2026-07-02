#!/usr/bin/env python3
"""Write-confinement for catalogue-curation (RFC-0059, spec "Write confinement
via the blessed helper").

A thin wrapper over the engine's blessed path-jail — `agentbundle.safety`
(`write_jailed` / `assert_under`: resolve → resolve symlinks → verify-prefix).
We **reuse** it, never roll our own path handling: a traversing/absolute path or
a symlink inside a fetched source cannot escape the jail root (`packs/` for
assimilate, the target root for export). Consuming the engine's public safety
helper read-only is sanctioned reuse, not a D6 engine change.

**Duplicated, by design.** `assimilate-primitive`, `assimilate-repo`, and
`export-catalogue` each carry a byte-identical copy under their own `scripts/`;
`tools/lint-catalogue-curation-guard.py` enforces the copies stay in sync.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.safety import PathJailError, assert_under, write_jailed

__all__ = ["PathJailError", "assert_under", "write_jailed", "jailed_write", "confined_target"]


def jailed_write(root: Path, relpath: str, content: bytes | str) -> Path:
    """Write `content` under `root/relpath`, atomically and jailed. Raises
    PathJailError if the resolved target escapes `root`. Never bypass this with
    hand-rolled `open()`."""
    return write_jailed(Path(root), relpath, content)


def confined_target(root: Path, target: Path) -> Path:
    """Assert `target` resolves under `root` (symlinks resolved first) and return
    the resolved path. Raises PathJailError otherwise. Use before reading a
    fetched-source file or choosing an export destination."""
    root = Path(root)
    assert_under(root, Path(target))
    return Path(target).resolve()


if __name__ == "__main__":  # pragma: no cover - smoke only
    import sys

    print("write_jail: wraps agentbundle.safety.write_jailed / assert_under", file=sys.stderr)
    sys.exit(0)
