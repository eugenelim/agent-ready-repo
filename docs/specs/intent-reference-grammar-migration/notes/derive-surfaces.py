#!/usr/bin/env python3
"""Derive the surface inventory for the four cross-artifact pointer fields.

Spec: docs/specs/intent-reference-grammar-migration/spec.md (AC-0019).

Why this exists: every surface list in this delivery that was written by
enumerating from memory, or by searching for a field's *name*, was wrong. A
name search cannot see a generic preamble parser (it keys on the lower-cased
name and never contains the literal), a generated copy, or a template that
emits the form without ever reading one. This derives all three by behaviour.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

FIELDS = ("Parent intent", "Brief", "Contract", "Discovery")

# Directories holding artifact *instances* that carry these fields. They are the
# data the fields point between, not surfaces that define or consume the form.
CORPUS_PREFIXES = ("docs/product/intents/", "docs/product/briefs/", "docs/specs/")
SKIP_DIRS = {".git", "node_modules", "build", "dist", ".venv", "__pycache__", ".pytest_cache"}

# Both real preamble parsers in this repository — `workspace_status_engine`'s
# `field_re` and `intent_shape._FIELD_LINE` — compile the same anchored shape:
# a line-start `- **`, a capture, `:**`, then a value capture. Matching bold
# markdown generally instead flagged 35 files, most of them shape linters and
# tests that regex `**...**` for unrelated reasons.
_PREAMBLE_BULLET = "^- \\*\\*"
_PREAMBLE_CLOSE = ":\\*\\*"


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def is_corpus(relpath: str) -> bool:
    return any(relpath.startswith(pre) for pre in CORPUS_PREFIXES)


def reads_generically(text: str) -> bool:
    """True when the file parses preamble fields by pattern rather than by name."""
    return _PREAMBLE_BULLET in text and _PREAMBLE_CLOSE in text


def _loads_module(text: str, stem: str) -> bool:
    """True when `text` imports `stem`, or names `<stem>.py` for a dynamic load.

    A bare mention of the stem is not enough: matching any occurrence pulled in
    every module that happens to use the word and inflated the inventory almost
    threefold.
    """
    s = re.escape(stem)
    return bool(
        re.search(rf"^\s*(?:from\s+[.\w]*\b{s}\b|import\s+[.\w]*\b{s}\b)", text, re.M)
        or re.search(rf"[\"']{s}(?:\.py)?[\"']", text)
    )


def derive(root: Path) -> dict[str, dict[str, list[str]]]:
    inventory: dict[str, dict[str, list[str]]] = {
        f: {"reads": [], "parses": [], "writes": [], "states": [], "generated-copy": []}
        for f in FIELDS
    }
    by_digest: dict[str, list[str]] = {}

    for path in iter_files(root):
        relpath = rel(root, path)
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        by_digest.setdefault(hashlib.sha256(raw).hexdigest(), []).append(relpath)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue

        if path.suffix == ".py":
            generic = reads_generically(text)
            lowered = text.lower()
            for field in FIELDS:
                # Acting on a field means naming it somewhere: as the header
                # form `Contract:`, or as the lower-cased key a generic parser
                # returns. The bare word alone is not enough — "Contract"
                # matches unrelated prose and inflated this list threefold.
                acts = f"{field}:" in text or f'"{field.lower()}"' in lowered
                if acts:
                    inventory[field]["reads"].append(relpath)
                elif generic:
                    # Sees the field but does nothing field-specific with it.
                    # `lint-adr-shape` parses every preamble line and mentions
                    # "brief" zero times; asking it to accept a new Brief form
                    # would be meaningless, so it is not a `reads` obligation.
                    inventory[field]["parses"].append(relpath)
            continue

        if path.suffix != ".md" or is_corpus(relpath):
            continue

        for field in FIELDS:
            # Writes: emits the header line itself (a template, seed or example).
            if re.search(rf"^\s*[-*]?\s*\*\*{re.escape(field)}:\*\*", text, re.M):
                inventory[field]["writes"].append(relpath)
            elif f"{field}:" in text:
                inventory[field]["states"].append(relpath)

    # One-hop propagation: a module that loads a reader — by `import`, or by
    # name through `importlib` — reads what that reader reads. `intent_corpus_lint`
    # reaches `Parent intent:` only this way, and a purely static scan of its own
    # text finds nothing, which is the third shape of invisible consumer.
    py_text: dict[str, str] = {}
    for path in iter_files(root):
        if path.suffix == ".py" and not path.is_symlink():
            try:
                py_text[rel(root, path)] = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
    # Propagate only from the *generic* parsers. Those are the readers a name
    # search cannot see, so their consumers are the ones at risk of being
    # missed. Propagating from every reader instead pulled in any module that
    # imports a commonly-named sibling and inflated the inventory sevenfold.
    generic_stems = {
        Path(r).stem for r, txt in py_text.items() if reads_generically(txt)
    }
    for field in FIELDS:
        readers = set(inventory[field]["reads"])
        relevant = {s for s in generic_stems if any(Path(r).stem == s for r in readers)}
        for relpath, text in py_text.items():
            if relpath in readers:
                continue
            if any(_loads_module(text, stem) for stem in relevant):
                inventory[field]["reads"].append(relpath)

    # Generated copies: byte-identical duplicates. The pack source is the one
    # under packs/*/.apm/; the rest are projections of it.
    copies: list[str] = []
    for members in by_digest.values():
        if len(members) < 2:
            continue
        if any("/.apm/" in m for m in members):
            copies.extend(m for m in members if "/.apm/" not in m)
    for field in FIELDS:
        touched = set(inventory[field]["reads"]) | set(inventory[field]["writes"])
        stems = {Path(m).name for m in touched}
        inventory[field]["generated-copy"] = sorted(
            c for c in copies if Path(c).name in stems
        )
    return inventory


def render(inventory: dict[str, dict[str, list[str]]]) -> str:
    out = [
        "# Surface inventory — the four cross-artifact pointer fields",
        "",
        "Generated by `derive-surfaces.py`. Do not hand-edit: re-run the script.",
        "",
        "`reads` consumes the value; `parses` sees it through a generic preamble",
        "parser but does nothing field-specific with it; `writes` emits the",
        "header; `states` describes",
        "the form in prose; `generated-copy` is a byte-identical projection of a",
        "pack source that reads or writes it.",
        "",
    ]
    for field in FIELDS:
        out.append(f"## `{field}:`")
        out.append("")
        for label in ("reads", "parses", "writes", "states", "generated-copy"):
            members = sorted(set(inventory[field][label]))
            out.append(f"### {label} ({len(members)})")
            out.append("")
            out.extend(f"- `{m}`" for m in members) if members else out.append("_none_")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


# The three classes a name search misses. A derivation returning none of these
# has reproduced the defect it exists to prevent, so it fails rather than ships.
# Each probe is *differential*: the named file must be unreachable by the
# mechanism the probe is not testing. `workspace_status_engine.py` contains the
# literal "Brief" six times, so asserting it under Brief/reads would pass on a
# plain name search and prove nothing about generic parsing. It contains
# "Parent intent" zero times and still parses that field, so Parent intent is
# the probe that only the generic path can satisfy. Mutation-checked: disabling
# generic detection with the Brief probe left the check green.
KNOWN_MEMBERS = (
    ("Parent intent", "parses", "workspace_status_engine.py", "generic preamble parser"),
    ("Discovery", "parses", "workspace_status_engine.py", "generic preamble parser"),
    ("Brief", "generated-copy", "workspace_status_engine.py", "generated projection"),
    ("Parent intent", "writes", "intent-template.md", "template emitting the form"),
    ("Parent intent", "reads", "intent_corpus_lint.py", "reader via dynamic import"),
    ("Brief", "reads", "workspace_status_engine.py", "acts on the value it parses"),
)


def self_check(inventory: dict[str, dict[str, list[str]]]) -> list[str]:
    failures = []
    for field, label, needle, why in KNOWN_MEMBERS:
        if not any(needle in m for m in inventory[field][label]):
            failures.append(f"{field!r} / {label}: no member matching {needle!r} ({why})")
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".", help="repository root")
    ap.add_argument("--out", default=None, help="inventory path (default: beside this script)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    out = Path(args.out) if args.out else Path(__file__).resolve().parent / "surface-inventory.md"

    inventory = derive(root)
    failures = self_check(inventory)
    if failures:
        print("derive-surfaces: self-check FAILED — the derivation missed a known class:")
        for f in failures:
            print(f"  - {f}")
        return 1

    out.write_text(render(inventory), encoding="utf-8")
    total = sum(len(set(v)) for f in FIELDS for v in inventory[f].values())
    print(
        f"derive-surfaces: {out.relative_to(root)} written "
        f"({total} entries across {len(FIELDS)} fields)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
