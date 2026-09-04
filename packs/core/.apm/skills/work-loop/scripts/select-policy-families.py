#!/usr/bin/env python3
"""select-policy-families — turn a work-loop phase into its policy families.

Reads the registry block from `references/policy-families.md`, selects the
families a phase teaches, and prints one delivery record as JSON on stdout.

Selection only. This script never assembles a dispatch brief and never decides
whether a policy was obeyed; `assembled_brief_digest` is declared and left null
for the slice that performs assembly.

Usage:
    select-policy-families.py --registry <file> --root <dir> <selection-key>

`--root` resolves a family's `module` locator. It is the tree the acting agent
reads, which is not always the tree the registry was read from: an adapter
projection carries the skill but no seeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROGRAM = "select-policy-families"
SUPPORTED_SCHEMA_VERSION = 1
INFO_STRING_PREFIX = "json policy-registry."
TIERS = frozenset({"precise", "advisory"})

# Candidate roots per locator namespace, in preference order. The installed copy
# an acting agent reads wins over the catalogue source it was built from.
_SKILL_ROOTS = (".claude/skills", ".agents/skills", "packs/core/.apm/skills")
_SEED_ROOTS = ("", "packs/core/seeds")


class RegistryError(Exception):
    """A registry or argument state the selector refuses to act on."""


def _fenced_blocks(text: str) -> list[tuple[str, str]]:
    """Return `(info_string, body)` for each top-level fenced block.

    CommonMark fence semantics, not a toggle. A toggle desyncs on a nested fence
    — a ```json inside a ```markdown example flips the state back — so only a
    bare run of the opening character, at least as long as the opener, closes.
    """
    blocks: list[tuple[str, str]] = []
    fence_char: str | None = None
    fence_len = 0
    info = ""
    body: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:1]
        if marker in ("`", "~"):
            run = len(stripped) - len(stripped.lstrip(marker))
            rest = stripped[run:].strip()
            if fence_char is None:
                if run >= 3:
                    fence_char, fence_len, info, body = marker, run, rest, []
                continue
            if marker == fence_char and run >= fence_len and not rest:
                blocks.append((info, "\n".join(body)))
                fence_char, fence_len, info, body = None, 0, "", []
                continue
        if fence_char is not None:
            body.append(line)
    return blocks


def load_registry(registry_path: Path) -> dict:
    """Parse and validate the registry block. Raises RegistryError."""
    try:
        text = registry_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RegistryError(f"cannot read registry {registry_path}: {exc}") from exc

    tagged = [(i, b) for i, b in _fenced_blocks(text) if i.startswith(INFO_STRING_PREFIX)]
    if len(tagged) != 1:
        raise RegistryError(
            f"expected exactly one '{INFO_STRING_PREFIX}*' block in {registry_path}, "
            f"found {len(tagged)}"
        )
    info, body = tagged[0]
    try:
        registry = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RegistryError(f"registry block is not valid JSON: {exc}") from exc

    version = registry.get("schema_version")
    # Order matters: the pair check runs first, so the fixture that exercises the
    # version check must carry a *consistent* unsupported pair.
    if info != f"{INFO_STRING_PREFIX}v{version}":
        raise RegistryError(
            f"info string {info!r} disagrees with schema_version {version!r}"
        )
    if version != SUPPORTED_SCHEMA_VERSION:
        raise RegistryError(
            f"unsupported schema_version {version!r}; this selector reads "
            f"{SUPPORTED_SCHEMA_VERSION}"
        )

    families = registry.get("families")
    if not isinstance(families, list) or not families:
        raise RegistryError("registry has no 'families' array")
    seen: set[str] = set()
    for family in families:
        fid = family.get("id")
        if fid in seen:
            raise RegistryError(f"duplicate family id {fid!r}")
        seen.add(fid)
        if family.get("tier") not in TIERS:
            raise RegistryError(
                f"family {fid!r} has tier {family.get('tier')!r}; expected one of "
                f"{sorted(TIERS)}"
            )
        module = family.get("module", "")
        if not (module.startswith("skill:") or module.startswith("seed:")):
            raise RegistryError(
                f"family {fid!r} has module {module!r}; expected a 'skill:' or "
                f"'seed:' locator"
            )

    selection = registry.get("selection")
    if not isinstance(selection, dict):
        raise RegistryError("registry has no 'selection' object")
    for key, ids in selection.items():
        if len(set(ids)) != len(ids):
            raise RegistryError(f"selection {key!r} repeats a family id")
        for fid in ids:
            if fid not in seen:
                raise RegistryError(f"selection {key!r} names unknown family {fid!r}")
    return registry


def resolve_module(module: str, root: Path) -> Path:
    """Resolve a logical locator against *root*. Raises RegistryError."""
    namespace, _, remainder = module.partition(":")
    if namespace == "skill":
        candidates = [root / base / remainder for base in _SKILL_ROOTS]
    else:
        candidates = [root / base / remainder if base else root / remainder
                      for base in _SEED_ROOTS]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RegistryError(
        f"module {module!r} resolves to no file under {root} "
        f"(tried {', '.join(str(c) for c in candidates)})"
    )


def build_record(registry: dict, key: str, root: Path) -> dict:
    if key not in registry["selection"]:
        raise RegistryError(f"unknown selection key {key!r}")
    by_id = {f["id"]: f for f in registry["families"]}
    families = []
    for fid in registry["selection"][key]:
        source = by_id[fid]
        resolved = resolve_module(source["module"], root)
        families.append({
            "id": fid,
            "tier": source["tier"],
            "module": source["module"],
            "module_digest": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        })
    return {
        "selection_key": key,
        "families": families,
        # Selection does not assemble. The slice that does populates this.
        "assembled_brief_digest": None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("key")
    args = parser.parse_args(argv)

    try:
        registry = load_registry(args.registry)
        record = build_record(registry, args.key, args.root)
    except RegistryError as exc:
        print(f"{PROGRAM}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
