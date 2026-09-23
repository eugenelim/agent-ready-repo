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
# Prose that *discusses* a field is not a surface that stamps or governs it. A
# decision record argues about the form, and a generated index inherits whatever
# its records are titled — this RFC's own title put `docs/rfc/README.md` into
# two `states` groups, which is noise AC-0009 would then quantify over.
DISCUSSES_ONLY_PREFIXES = ("docs/rfc/", "docs/adr/")
# A surface is something an author is guided by or that code consumes. A test
# fixture, an eval case and a saved review transcript contain the same header
# text and guide nobody: counting them put 198 of 455 entries in the inventory
# that no migration would ever need to touch. `examples/` is deliberately NOT
# here — a shipped example is author-facing, and the brief sweep repointed one.
NON_SURFACE_SEGMENTS = ("/tests/", "/test/", "/fixtures/", "/fixture/", "/evals/", "/eval/")
NON_SURFACE_PREFIXES = (".context/",)


def is_non_surface(relpath: str) -> bool:
    return relpath.startswith(NON_SURFACE_PREFIXES) or any(
        seg in f"/{relpath}" for seg in NON_SURFACE_SEGMENTS
    )


SKIP_DIRS = {".git", "node_modules", "build", "dist", ".venv", "__pycache__", ".pytest_cache"}

# A *generic* preamble parser opens with a line-anchored `- **`, captures the
# field name, and closes with `:**` — all inside one pattern. Testing for the
# opener and the closer independently was not enough: `lint-spec-status` has
# `^- \*\*Acceptance Criteria:\*\*` and a separate `\*\*Status:\*\*`,
# `lint-adr-shape` has `^- \*\*D(\d+):\*\*`, and neither parses arbitrary
# fields. The name must be a bare capture: a literal before it means the
# pattern is looking for one known field, not any of them.
_PREAMBLE_OPEN = "^- \\*\\*"
_PREAMBLE_CLOSE = ":\\*\\*"
_NAME_CAPTURE_WINDOW = 40


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


def code_only(text: str) -> str:
    """Strip comments and docstrings, so a field named in prose is not a read.

    `intake_router.py` mentions a field in a docstring and consumes nothing;
    matching raw source counted it as a consumer.
    """
    without_docstrings = re.sub(r'(?s)("""|\'\'\').*?\1', "", text)
    return re.sub(r"#[^\n]*", "", without_docstrings)


def reads_generically(text: str) -> bool:
    """True when the file parses preamble fields by pattern rather than by name."""
    start = 0
    while True:
        i = text.find(_PREAMBLE_OPEN, start)
        if i < 0:
            return False
        start = i + len(_PREAMBLE_OPEN)
        rest = text[start:start + _NAME_CAPTURE_WINDOW]
        # The captured name must follow the opener immediately; a literal
        # character there names one field instead of matching any.
        if rest.startswith("(") and _PREAMBLE_CLOSE in rest:
            return True


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
            code = code_only(text)
            lowered = code.lower()
            for field in FIELDS:
                # Acting on a field means naming it somewhere: as the header
                # form `Contract:`, or as the lower-cased key a generic parser
                # returns. The bare word alone is not enough — "Contract"
                # matches unrelated prose and inflated this list threefold.
                # Three ways a file acts on a field, and case is what separates
                # them from coincidence. Naming it in exact case inside a string
                # is deliberate — `field_re("Parent intent")` in the resolver.
                # Indexing a generic parser's output is deliberate —
                # `fields.get("brief")`. A bare lower-case `"brief"` is not:
                # `intake_router` uses it as an artifact *kind* and a route-table
                # key and never touches the pointer.
                named = re.search(rf"""["']{re.escape(field)}:?["']""", code)
                # A lower-cased key lookup only means "acts on this field" in a
                # file that parses preambles: that is where `fields["brief"]`
                # comes from. Elsewhere it is an unrelated dict —
                # `journey_validator` reads `data["contract"]` from a journey
                # manifest and never sees a pointer.
                looks_up = generic and re.search(
                    rf"""(?:get\(\s*|\[\s*)["']{re.escape(field.lower())}["']""",
                    lowered,
                )
                acts = f"{field}:" in code or bool(named) or bool(looks_up)
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
        if relpath.startswith(DISCUSSES_ONLY_PREFIXES) or is_non_surface(relpath):
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
        already = set(inventory[field]["reads"]) | set(inventory[field]["parses"])
        for relpath, text in py_text.items():
            if relpath in already:
                continue
            if any(_loads_module(text, stem) for stem in generic_stems):
                # It reaches the field through a generic parser and names no
                # field of its own, so it sees the value without acting on it.
                # `intent_corpus_lint` iterates `read_preamble`'s pairs and
                # names none of the four.
                inventory[field]["parses"].append(relpath)

    # Generated copies: byte-identical duplicates whose pack source is itself a
    # surface for this field. Matching on basename instead put every same-named
    # file in the tree under this role; the group is the evidence, so the group
    # is what decides. `states` counts alongside `reads` and `writes` — a
    # stating surface has projections like any other shipped file.
    groups: list[tuple[str, list[str]]] = []
    for members in by_digest.values():
        if len(members) < 2:
            continue
        sources = [m for m in members if "/.apm/" in m]
        if len(sources) == 1:
            groups.append((sources[0], [m for m in members if m != sources[0]]))
    for field in FIELDS:
        touched = (
            set(inventory[field]["reads"])
            | set(inventory[field]["writes"])
            | set(inventory[field]["states"])
        )
        inventory[field]["generated-copy"] = sorted(
            c for src, projections in groups if src in touched for c in projections
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
    ("Parent intent", "parses", "intent_corpus_lint.py", "reached via a dynamic import"),
    ("Brief", "reads", "workspace_status_engine.py", "acts on the value it parses"),
    ("Parent intent", "reads", "work-loop/scripts/lint-traceability.py", "the resolver itself"),
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
