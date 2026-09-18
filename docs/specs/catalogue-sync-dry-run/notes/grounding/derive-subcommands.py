"""Derive § Grounding's catalogue direct-subcommand roster and nested residual."""

from __future__ import annotations

import ast
import sys

from _common import fail, read_text


def _add_parser_calls(tree: ast.AST, receiver: str) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_parser" or not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id != receiver or not node.args:
            continue
        name = node.args[0]
        if isinstance(name, ast.Constant) and isinstance(name.value, str):
            names.append(name.value)
    return names


def main() -> int:
    try:
        tree = ast.parse(read_text("packages/agentbundle/agentbundle/cli.py"))
        direct = _add_parser_calls(tree, "cat_subs")
        nested = _add_parser_calls(tree, "_contracts_subs")
        if not direct:
            return fail("catalogue parser has no direct subcommands")
        print("direct subcommands: " + ", ".join(direct))
        print("nested residual: contracts " + ", ".join(nested))
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"subcommand derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
