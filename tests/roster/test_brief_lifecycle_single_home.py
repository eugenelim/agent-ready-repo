#!/usr/bin/env python3
"""AC-0019: exactly one *.py under packs/*/.apm/ carries all six status tokens.

Why this file exists and lives here. The check scans ``packs/`` for any
``*.py`` file under a ``.apm/`` subtree that contains a collection literal
whose directly enumerated string members include all six brief status tokens.
That is the mechanical proxy for "no second executable definition of the
vocabulary".  Because the search crosses pack boundaries, it is a
repository-level assertion and lives in ``tests/roster/`` rather than a
pack's own test tree (``tools/lint-pack-test-boundary.py`` enforces that
boundary).

Match rule (from AC-0019):
- Collection literal types: ``ast.Set``, ``ast.List``, ``ast.Tuple``,
  ``ast.Dict`` (dict keys count as members).
- Membership: only directly enumerated ``str`` constants; nested collections
  are not flattened.
- Case-sensitive comparison against the six tokens.
- A superset counts — adding a seventh member such as ``"missing"`` is still
  a second definition.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]

_TOKENS: frozenset[str] = frozenset(
    {"Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled"}
)


def _direct_string_members(node: ast.expr) -> set[str]:
    """Return the set of string constants directly enumerated in a collection node.

    For ``ast.Set``, ``ast.List``, ``ast.Tuple``: collects ``ast.Constant``
    elements whose value is ``str``.  For ``ast.Dict``: collects string-valued
    keys.  Nested collections are not recursed into; their token members are
    not the containing literal's direct members.
    """
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        return {
            elt.value
            for elt in node.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        }
    if isinstance(node, ast.Dict):
        return {
            key.value
            for key in node.keys
            if key is not None
            and isinstance(key, ast.Constant)
            and isinstance(key.value, str)
        }
    return set()


def _find_matches(py_path: Path) -> list[int]:
    """Return line numbers of collection literals containing all six status tokens."""
    try:
        source = py_path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(py_path))
    except SyntaxError:
        return []
    matches: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Set, ast.List, ast.Tuple, ast.Dict)):
            members = _direct_string_members(node)
            if members >= _TOKENS:
                matches.append(getattr(node, "lineno", 0))
    return matches


def test_brief_lifecycle_single_home() -> None:
    """AC-0019: exactly one *.py file under packs/*/.apm/ enumerates all six tokens.

    The only expected match is ``brief_shape.py``, which is the single home
    for the brief status vocabulary.  Any other file with such a literal is a
    second definition that can drift from it.
    """
    packs_dir = _REPO / "packs"
    hits: dict[str, list[int]] = {}

    for apm_dir in sorted(packs_dir.glob("*/.apm")):
        for py_path in sorted(apm_dir.rglob("*.py")):
            lines = _find_matches(py_path)
            if lines:
                rel = py_path.relative_to(_REPO).as_posix()
                hits[rel] = lines

    expected = {
        "packs/core/.apm/skills/author-delivery-brief/scripts/brief_shape.py"
    }
    actual = set(hits.keys())
    assert actual == expected, (
        f"Expected exactly brief_shape.py to carry all six status tokens.\n"
        f"Got: {sorted(actual)!r}\n"
        f"Line numbers: {dict(hits)!r}"
    )
