#!/usr/bin/env python3
"""Guard the pack rename map at ``contracts/renames/pack-renames.toml``.

A rename map names each retired pack and the pack that replaced it. Two things
keep the map honest, and this lint fails on either: a pack under ``packs/`` that
still carries a retired name (the rename did not happen), and a map target that
is not a pack in the catalogue (the hint would send adopters to nothing).

A pack is a directory ``packs/<name>/`` holding a ``pack.toml``. A retired name
counts as present when ``packs/<name>/`` exists at all, so a half-renamed
directory is still caught.
"""

from __future__ import annotations

import argparse
import tomllib
from pathlib import Path

from lint_harness import Outcome, Rule, RuleAbort, run

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MAP = Path("contracts") / "renames" / "pack-renames.toml"
_NAME = "lint-pack-renames"


def _parse(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_REPO_ROOT)
    return parser.parse_args(argv).root


def _files(root: Path) -> list[Path] | None:
    path = root / _MAP
    return [path] if path.is_file() else None


def _renames(path: Path) -> list[tuple[str, str]]:
    """Return the ``(from, to)`` pairs, aborting with status 2 on a bad map."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuleAbort(Outcome(f"{_NAME}: cannot read {path}: {exc}", 2)) from exc
    entries = data.get("rename")
    pairs: list[tuple[str, str]] = []
    if not isinstance(entries, list):
        raise RuleAbort(Outcome(f"{_NAME}: {path} has no [[rename]] array", 2))
    for entry in entries:
        old = entry.get("from") if isinstance(entry, dict) else None
        new = entry.get("to") if isinstance(entry, dict) else None
        if not isinstance(old, str) or not isinstance(new, str):
            raise RuleAbort(Outcome(f"{_NAME}: {path} has a rename without string from/to", 2))
        pairs.append((old, new))
    return pairs


def _predicate(path: Path) -> list[str]:
    root = path.parents[2]
    findings: list[str] = []
    for old, new in _renames(path):
        if (root / "packs" / old).exists():
            findings.append(f"{_NAME}: packs/{old}/ is named after the retired name '{old}'")
        if not (root / "packs" / new / "pack.toml").is_file():
            findings.append(
                f"{_NAME}: rename target '{new}' (from '{old}') is not a pack: "
                f"packs/{new}/pack.toml is missing"
            )
    return findings


def _main() -> int:
    rule = Rule(
        parse=_parse,
        files=_files,
        predicate=_predicate,
        pass_line=lambda _root, _n: f"{_NAME}: ok",
        empty_scan=lambda root: Outcome(f"{_NAME}: nothing to scan under {root}", 2),
        absent_root=lambda root: Outcome(f"{_NAME}: missing {root / _MAP}", 2),
    )
    return run(rule)


if __name__ == "__main__":
    raise SystemExit(_main())
