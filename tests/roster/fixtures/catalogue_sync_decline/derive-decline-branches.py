"""Derive § Grounding's removal-guard decline branches from its own AST."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from _common import fail, read_text


def _guard(tree: ast.AST) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_plan_stale_owned_paths":
            return node
    raise ValueError("_plan_stale_owned_paths is absent")


def _continues(node: ast.AST) -> list[ast.Continue]:
    return [item for item in ast.walk(node) if isinstance(item, ast.Continue)]


def _emits_reason(node: ast.AST) -> bool:
    for item in ast.walk(node):
        if (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and item.func.attr == "append"
            and isinstance(item.func.value, ast.Name)
            and item.func.value.id in {"reasons", "warnings"}
        ):
            return True
    return False


def main() -> int:
    if len(sys.argv) != 2:
        return fail("usage: derive-decline-branches.py <initialise_self_hosted.py>")
    try:
        path = Path(sys.argv[1])
        if path.is_absolute():
            return fail("argument must be repository-relative")
        guard = _guard(ast.parse(read_text(path.as_posix())))
        branches: list[tuple[int, bool]] = []
        for node in ast.walk(guard):
            if isinstance(node, (ast.If, ast.ExceptHandler)) and _continues(node):
                branches.append((node.lineno, _emits_reason(node)))
        if not branches:
            return fail("removal guard has no decline branches")
        named = [str(line) for line, emits in branches if emits]
        silent = [str(line) for line, emits in branches if not emits]
        print(f"decline branches: {len(branches)}")
        print("reason-emitting lines: " + (", ".join(named) or "none"))
        print("residual silent lines: " + (", ".join(silent) or "none"))
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"decline-branch derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
