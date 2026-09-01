#!/usr/bin/env python3
"""Assert the published direct diagnostic-code table equals `DIRECT_CODES`.

`DIRECT_CODES` is read from the worktree source by `ast` parse rather than
imported. Importing would resolve whatever `agentbundle` is first on
`sys.path` — a stale editable install, or an unrelated copy — and the check
would then pass against a registry that is not the one being changed.

Exit 0 = the table and the registry name exactly the same codes.
Exit 1 = a code is registered but unpublished, or published but unregistered.

Usage:
  python3 tools/lint-direct-code-table.py [--root .]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REGISTRY_RELPATH = "packages/agentbundle/agentbundle/catalogue_tooling/diagnostics.py"
TABLE_RELPATH = "guides/catalogue-curation/reference/direct-install-diagnostics.md"
TABLE_ROW = re.compile(r"^\|\s*`(CAT-D\d+)`\s*\|")


def registered_codes(registry: Path) -> set[str]:
    """Read the `DIRECT_CODES` frozenset literal without importing the module.

    Only an explicit frozenset literal of enum members is readable this way,
    which is why the registry is written that way: a comprehension or a filter
    over `DiagnosticCode` would be invisible here.
    """

    tree = ast.parse(registry.read_text(encoding="utf-8"))
    values = {
        node.targets[0].id: node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    annotated = {
        node.target.id: node.value
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.value is not None
    }
    values.update(annotated)

    direct = values.get("DIRECT_CODES")
    if direct is None:
        raise SystemExit(f"{registry}: DIRECT_CODES is not a module-level assignment")
    if not (
        isinstance(direct, ast.Call)
        and isinstance(direct.func, ast.Name)
        and direct.func.id == "frozenset"
        and direct.args
        and isinstance(direct.args[0], ast.Set)
    ):
        raise SystemExit(
            f"{registry}: DIRECT_CODES must be an explicit frozenset literal of "
            f"DiagnosticCode members so it can be read without importing it"
        )

    members = set()
    for element in direct.args[0].elts:
        if not (isinstance(element, ast.Attribute) and isinstance(element.value, ast.Name)):
            raise SystemExit(f"{registry}: DIRECT_CODES holds a non-member element")
        members.add(element.attr)

    # Resolve each `CAT_Dnnn` member to its string value from the enum body.
    literals: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for statement in node.body:
                if (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                ):
                    literals[statement.targets[0].id] = statement.value.value

    missing = members - set(literals)
    if missing:
        raise SystemExit(f"{registry}: cannot resolve {sorted(missing)} to code strings")
    return {literals[member] for member in members}


def published_codes(table: Path) -> set[str]:
    """Read every code the published table names."""

    if not table.exists():
        raise SystemExit(f"{table}: the published direct code table is missing")
    codes: set[str] = set()
    for line in table.read_text(encoding="utf-8").splitlines():
        matched = TABLE_ROW.match(line)
        if matched:
            codes.add(matched.group(1))
    return codes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    registered = registered_codes(root / REGISTRY_RELPATH)
    published = published_codes(root / TABLE_RELPATH)

    unpublished = sorted(registered - published)
    unregistered = sorted(published - registered)
    if unpublished:
        print(
            f"lint-direct-code-table: registered but not published: "
            f"{', '.join(unpublished)}",
            file=sys.stderr,
        )
    if unregistered:
        print(
            f"lint-direct-code-table: published but not registered: "
            f"{', '.join(unregistered)}",
            file=sys.stderr,
        )
    if unpublished or unregistered:
        print(f"  registry: {REGISTRY_RELPATH}", file=sys.stderr)
        print(f"  table:    {TABLE_RELPATH}", file=sys.stderr)
        return 1

    print(f"ok: direct code table publishes all {len(registered)} registered codes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
