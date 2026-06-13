#!/usr/bin/env python3
"""Guards every copy of the knowledge-surface taxonomy against silent drift.

The `architect-design` reference
(`packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md`)
defines the **shared canonical core**: an eight-area MECE taxonomy. Other skills
reuse it under their own lens by *duplicating* the core (Route B — a single
shared file — was rejected), so the copies are anchored by a prose note, not a
shared artifact. That makes them free to drift when the canonical core next
changes. This lint is the mechanical guard the `architect-pe-knowledge-surface-drift`
backlog item called for, generalized to every copy that exists today:

  - `architect-review` reuses the full taxonomy as a verification lens ({1..8});
  - `frame-intent` reuses the problem-framing subset ({1, 2, 4, 8}); areas
    3/5/6/7 are deliberately omitted there as solution-design.

Invariants:
  (1) the canonical reference carries exactly the canonical set, areas {1..8};
  (2) each copy carries exactly its declared area set (full or subset);
  (3) for every area a copy carries, its **name** and its **question it answers**
      are byte-identical to the canonical definition.

A change to the canonical core (a renamed area, a reworded question, an added or
removed area) trips invariant (1) or (3) against every copy; a drift in a copy
trips (2) or (3). Either way the author is forced to reconcile all copies (and,
if a copy's area selection is being redesigned, to update the constants below
deliberately).

Exit 0 when every copy is in parity; exit 1 on any drift.

Fixture mode (used by the paired self-test): set KS_CANONICAL_FILE,
KS_REVIEW_FILE, KS_PE_FILE to lint different files.
"""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys

CANONICAL_AREAS = frozenset({1, 2, 3, 4, 5, 6, 7, 8})

# role -> (env override, default repo-relative path, expected area set). The
# first row is the canonical source; the rest are copies checked against it.
# Changing a copy's expected set is a deliberate redesign that must update this
# table *and* reconcile the files.
CANONICAL_ROLE = "architect-design (canonical)"
LAYOUT: tuple[tuple[str, str, str, frozenset[int]], ...] = (
    (
        CANONICAL_ROLE,
        "KS_CANONICAL_FILE",
        "packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md",
        CANONICAL_AREAS,
    ),
    (
        "architect-review",
        "KS_REVIEW_FILE",
        "packs/architect/.apm/skills/architect-review/references/knowledge-surfaces.md",
        CANONICAL_AREAS,
    ),
    (
        "frame-intent",
        "KS_PE_FILE",
        "packs/product-engineering/.apm/skills/frame-intent/references/knowledge-surfaces.md",
        frozenset({1, 2, 4, 8}),
    ),
)

# A taxonomy data row: "| <n> | <area> | <question> | ...". The first three
# columns (number, area, question-it-answers) are identical across every copy
# even where a table adds extra columns after them (frame-intent's "Weight").
# `\d+` (not `\d`) so a future two-digit area parses as itself rather than
# silently mis-parsing (e.g. "10" → "1" + stray "0").
_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|")


def _repo_root() -> pathlib.Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path(__file__).resolve().parent.parent


def parse_areas(path: pathlib.Path) -> dict[int, tuple[str, str]]:
    """Return {area_number: (area_name, question_it_answers)} from the file's
    taxonomy table. Raises ValueError on a duplicate area number."""
    areas: dict[int, tuple[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        num = int(m.group(1))
        name, question = m.group(2).strip(), m.group(3).strip()
        if num in areas:
            raise ValueError(f"{path}: duplicate area row #{num}")
        areas[num] = (name, question)
    if not areas:
        raise ValueError(
            f"{path}: no taxonomy table rows found — expected a "
            f"'| <n> | <area> | <question> | …' table (did the table get "
            f"reformatted, renamed, or removed?)"
        )
    return areas


def main() -> int:
    root = _repo_root()
    errors: list[str] = []

    resolved: dict[str, tuple[pathlib.Path, frozenset[int]]] = {}
    for role, env, rel, expected in LAYOUT:
        override = os.environ.get(env)
        p = pathlib.Path(override) if override else (root / rel)
        if not p.is_file():
            via = f" (via ${env})" if override else ""
            errors.append(f"{role} reference not found: {p}{via}")
        resolved[role] = (p, expected)
    if errors:
        for e in errors:
            print(f"knowledge-surface parity: ✖ {e}", file=sys.stderr)
        return 1

    parsed: dict[str, dict[int, tuple[str, str]]] = {}
    for role, (p, _expected) in resolved.items():
        try:
            parsed[role] = parse_areas(p)
        except ValueError as exc:
            print(f"knowledge-surface parity: ✖ {exc}", file=sys.stderr)
            return 1

    canonical = parsed[CANONICAL_ROLE]

    # (1) the canonical reference carries the full canonical set.
    if set(canonical) != CANONICAL_AREAS:
        errors.append(
            f"{CANONICAL_ROLE} areas {sorted(canonical)} != canonical "
            f"{sorted(CANONICAL_AREAS)} — the canonical core changed; reconcile "
            f"every copy and update this lint's constants if the redesign is "
            f"intentional"
        )

    for role, _env, _rel, expected in LAYOUT:
        if role == CANONICAL_ROLE:
            continue
        copy = parsed[role]
        # (2) the copy carries exactly its declared area set.
        if set(copy) != expected:
            errors.append(
                f"{role} reference areas {sorted(copy)} != expected "
                f"{sorted(expected)} — the area selection drifted"
            )
        # (3) every shared area's name + question is byte-identical.
        for num in sorted(set(copy) & set(canonical)):
            if copy[num] != canonical[num]:
                errors.append(
                    f"area #{num} diverged between {CANONICAL_ROLE} and {role}:\n"
                    f"    canonical: name={canonical[num][0]!r}\n"
                    f"               question={canonical[num][1]!r}\n"
                    f"    {role}: name={copy[num][0]!r}\n"
                    f"               question={copy[num][1]!r}"
                )

    if errors:
        for e in errors:
            print(f"knowledge-surface parity: ✖ {e}", file=sys.stderr)
        print(
            "knowledge-surface parity: the copies share a canonical core (see "
            "the shared-canonical-core anchor note in each); edit all of them, "
            "not one.",
            file=sys.stderr,
        )
        return 1

    n_copies = len(LAYOUT) - 1
    print(
        f"knowledge-surface parity: ✓ {n_copies} copies in parity with the "
        f"{len(CANONICAL_AREAS)}-area canonical core."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
