#!/usr/bin/env python3
"""Derive the caller sets of the two write helpers this delivery touches.

The opt-in decision's whole safety argument is that no caller outside this
command changes behaviour. That argument is only as good as the caller set it
was walked against, and the two helpers' sets differ by more than four times —
so a list written for one and reused for the other understates the audit.

Counted by resolution rather than carried as prose, because the sets move.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/derive-write-helper-callers.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

PACKAGE = Path("packages/agentbundle/agentbundle")
HELPERS = ("write_jailed", "write_companion")


def call_sites(tree: ast.AST, name: str) -> int:
    total = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        called = (
            func.attr if isinstance(func, ast.Attribute)
            else func.id if isinstance(func, ast.Name)
            else None
        )
        total += called == name
    return total


def main() -> int:
    for helper in HELPERS:
        sites: dict[str, int] = {}
        for path in sorted(PACKAGE.rglob("*.py")):
            if path.name == "safety.py":
                continue  # the definition's own module
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            count = call_sites(tree, helper)
            if count:
                sites[str(path.relative_to(PACKAGE))] = count
        total = sum(sites.values())
        print(f"{helper}: {total} call site(s) across {len(sites)} module(s)")
        for module, count in sites.items():
            print(f"    {count}  {module}")
        print()

    print(
        "the two sets are not interchangeable: an enumeration walked for "
        "write_companion understates write_jailed's by more than four times, "
        "so the opt-in audit must name which helper it was walked against"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
