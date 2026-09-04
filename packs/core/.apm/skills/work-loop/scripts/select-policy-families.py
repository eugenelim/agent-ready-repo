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
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

# Every `.apm/` script that prints reconfigures both streams before its first
# write; a cp1252 console otherwise turns a refusal into a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

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

    Fence-run semantics rather than a toggle: a toggle desyncs on a nested
    fence — a ```json inside a ```markdown example flips the state back — so
    only a bare run of the opening character, at least as long as the opener,
    closes. Indentation is not modelled, so a four-space-indented fence marker
    reads as a fence here where CommonMark would call it an indented code
    block; that direction fails closed, because the extra block makes the
    tagged-block count wrong and the registry is refused.

    Raises RegistryError on an unterminated fence, rather than dropping it —
    a truncated registry should say so instead of reporting zero blocks.
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
    if fence_char is not None:
        raise RegistryError(f"unterminated fenced block opened with {info!r}")
    return blocks


def load_registry(registry_path: Path) -> dict:
    """Parse and validate the registry block. Raises RegistryError."""
    try:
        text = registry_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RegistryError(f"cannot read registry {registry_path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise RegistryError(f"registry {registry_path} is not valid UTF-8: {exc}") from exc

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

    if not isinstance(registry, dict):
        raise RegistryError(
            f"registry block is a {type(registry).__name__}, expected an object"
        )

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
        if not isinstance(family, dict):
            raise RegistryError(
                f"family entry is a {type(family).__name__}, expected an object"
            )
        fid = family.get("id")
        if not isinstance(fid, str) or not fid:
            raise RegistryError(f"family entry has a non-string id {fid!r}")
        if fid in seen:
            raise RegistryError(f"duplicate family id {fid!r}")
        seen.add(fid)
        if family.get("tier") not in TIERS:
            raise RegistryError(
                f"family {fid!r} has tier {family.get('tier')!r}; expected one of "
                f"{sorted(TIERS)}"
            )
        module = family.get("module", "")
        if not isinstance(module, str):
            raise RegistryError(
                f"family {fid!r} has a non-string module {module!r}"
            )
        if not module.startswith(("skill:", "seed:")):
            raise RegistryError(
                f"family {fid!r} has module {module!r}; expected a 'skill:' or "
                f"'seed:' locator"
            )

    selection = registry.get("selection")
    if not isinstance(selection, dict):
        raise RegistryError("registry has no 'selection' object")
    for key, ids in selection.items():
        if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
            raise RegistryError(
                f"selection {key!r} is not a list of family ids"
            )
        if len(set(ids)) != len(ids):
            raise RegistryError(f"selection {key!r} repeats a family id")
        for fid in ids:
            if fid not in seen:
                raise RegistryError(f"selection {key!r} names unknown family {fid!r}")
    return registry


SCRIPT_DIR = Path(__file__).resolve().parent
_file_safety_module: Any | None = None


def _load_regular_sibling(path: Path, module_name: str, required: set[str]) -> Any:
    """Load a co-located helper, refusing anything that is not a regular file."""
    try:
        inspected = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"required helper is unavailable: {path.name}") from exc
    if not stat.S_ISREG(inspected.st_mode) or stat.S_ISLNK(inspected.st_mode):
        raise ImportError(f"required helper is not a regular file: {path.name}")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"required helper cannot be loaded: {path.name}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    missing = sorted(required - set(vars(module)))
    if missing:
        sys.modules.pop(module_name, None)
        raise ImportError(
            f"required helper is incomplete: {path.name}: {', '.join(missing)}"
        )
    return module


def file_safety() -> Any:
    """Load only the co-located byte projection of the blessed helper.

    Confinement is the repository's centralized control, not a local
    reimplementation. A hand-rolled canonicalize-then-prefix check misses what
    this helper already handles: a hard link to an out-of-root inode is
    canonically inside the boundary, `O_NOFOLLOW` plus an inode re-check closes
    the final-component swap between the check and the read, reparse points are
    rejected on Windows, and the digest streams rather than materializing the
    whole file.
    """
    global _file_safety_module
    if _file_safety_module is None:
        _file_safety_module = _load_regular_sibling(
            SCRIPT_DIR / "file_safety.py",
            "_select_policy_families_file_safety",
            {
                "UnsafeContentError",
                "validate_confined_directory",
                "sha256_confined_regular_file",
            },
        )
    return _file_safety_module


def digest_module(module: str, root: Path) -> str:
    """Return the SHA-256 of the file *module* names, confined to *root*.

    Candidates are tried in preference order — the copy an acting agent reads
    wins over the build source. Confinement, hard-link rejection, the
    check-to-read race, and the byte bound all belong to the blessed helper;
    this function only chooses which candidate to ask about.
    """
    safety = file_safety()
    namespace, _, remainder = module.partition(":")
    bases = _SKILL_ROOTS if namespace == "skill" else _SEED_ROOTS
    candidates = [root / base / remainder if base else root / remainder
                  for base in bases]
    for candidate in candidates:
        try:
            return safety.sha256_confined_regular_file(root, candidate)
        except safety.UnsafeContentError:
            # Not a confined regular file under root: try the next candidate.
            continue
        except OSError:
            # Absent or unreadable at this candidate; a later one may hold it.
            continue
    raise RegistryError(
        f"module {module!r} resolves to no file confined to {root} "
        f"(tried {', '.join(repr(str(c)) for c in candidates)})"
    )


def build_record(registry: dict, key: str, root: Path) -> dict:
    """Return the delivery record for *key*, digesting each family's module.

    Raises RegistryError for an unknown key or a module that does not resolve to
    a file confined to *root*.
    """
    if key not in registry["selection"]:
        raise RegistryError(f"unknown selection key {key!r}")
    by_id = {f["id"]: f for f in registry["families"]}
    families = []
    for fid in registry["selection"][key]:
        source = by_id[fid]
        families.append({
            "id": fid,
            "tier": source["tier"],
            "module": source["module"],
            "module_digest": digest_module(source["module"], root),
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
