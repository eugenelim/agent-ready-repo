"""AC-0012: the repair-only CLI and engine hold no unreached top-level code."""

from __future__ import annotations

import ast
from pathlib import Path

_SCRIPTS = (
    Path(__file__).resolve().parents[3] / ".apm" / "skills" / "workspace-status" / "scripts"
)
_FILES = ("workspace_status.py", "workspace_status_engine.py")
_Node = tuple[str, str]


def _top_level(tree: ast.Module) -> dict[str, ast.stmt]:
    """Map each top-level function, class and assigned name to its statement."""
    named: dict[str, ast.stmt] = {}
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            named[stmt.name] = stmt
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                for leaf in ast.walk(target):
                    if isinstance(leaf, ast.Name):
                        named[leaf.id] = stmt
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            named[stmt.target.id] = stmt
    return named


def _references(node: ast.AST) -> set[str]:
    """Every Name and Attribute reference inside a node."""
    found: set[str] = set()
    for leaf in ast.walk(node):
        if isinstance(leaf, ast.Name):
            found.add(leaf.id)
        elif isinstance(leaf, ast.Attribute):
            found.add(leaf.attr)
        elif isinstance(leaf, ast.Constant) and isinstance(leaf.value, str):
            # `_bind_engine` binds a module global to the engine name by string key.
            found.add(leaf.value)
    return found


def _closure() -> tuple[dict[_Node, ast.stmt], set[_Node]]:
    """Return every top-level node of both files and the set `main` reaches."""
    nodes: dict[_Node, ast.stmt] = {}
    roots: set[str] = set()
    by_name: dict[str, list[_Node]] = {}
    for filename in _FILES:
        tree = ast.parse((_SCRIPTS / filename).read_text(encoding="utf-8"))
        for name, stmt in _top_level(tree).items():
            nodes[(filename, name)] = stmt
            by_name.setdefault(name, []).append((filename, name))
        # Statements that run at import time are roots too.
        for stmt in tree.body:
            if not isinstance(
                stmt,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import,
                 ast.ImportFrom, ast.Assign, ast.AnnAssign),
            ):
                roots |= _references(stmt)
    reached: set[_Node] = set()
    pending = [("workspace_status.py", "main")]
    pending += [n for name in roots for n in by_name.get(name, [])]
    while pending:
        node = pending.pop()
        if node in reached or node not in nodes:
            continue
        reached.add(node)
        for name in _references(nodes[node]):
            pending.extend(by_name.get(name, []))
    return nodes, reached


def _unreached() -> list[str]:
    nodes, reached = _closure()
    return sorted(
        f"{filename}:{name}"
        for (filename, name), stmt in nodes.items()
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and (filename, name) not in reached
    )


def test_closure_is_rooted_at_main_and_reaches_the_repair() -> None:
    _, reached = _closure()
    assert ("workspace_status.py", "main") in reached
    assert ("workspace_status_engine.py", "analyze") in reached
    assert ("workspace_status_engine.py", "compute_repair_plan") in reached


def test_scripts_hold_no_prune_or_retirement_module() -> None:
    stray = sorted(
        path.name
        for path in _SCRIPTS.glob("*.py")
        if "prune" in path.name or "retirement" in path.name
    )
    assert stray == []


def test_every_top_level_def_is_reached_from_main() -> None:
    assert _unreached() == []
