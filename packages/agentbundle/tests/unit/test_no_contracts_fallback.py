"""No module of the package builds a path into a repository `contracts/` folder.

Every contract the CLI applies is read from the bundled `_data/` copy. This
scan finds each string constant (including f-string parts, excluding
docstrings) that equals `contracts`, starts with `contracts/`, or contains
`/contracts/`, and compares the per-file counts against a fixed allow-list of
uses that build no load path.
"""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

import agentbundle

PACKAGE_DIR = Path(agentbundle.__file__).resolve().parent

# (file relative to the package, string, exact count, reason)
ALLOWED: tuple[tuple[str, str, int, str], ...] = (
    ("catalogue_tooling/package.py", "contracts", 2, "archive inclusion"),
    ("catalogue_tooling/config.py", "contracts", 1, "configuration key name"),
    ("catalogue_tooling/lint.py", "contracts", 2, "configuration key names"),
    ("cli.py", "contracts", 1, "CLI subcommand name"),
    ("commands/catalogue_contracts.py", "contracts", 1, "JSON output key name"),
    ("build/self_host.py", "contracts/**", 1, "self-host input glob"),
    ("pack_renames.py", "contracts", 1, "fixed rename-map path read from the reporting catalogue"),
)


def _is_contracts_string(value: str) -> bool:
    return value == "contracts" or value.startswith("contracts/") or "/contracts/" in value


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def _scan() -> tuple[Counter[tuple[str, str]], dict[tuple[str, str], list[int]]]:
    counts: Counter[tuple[str, str]] = Counter()
    lines: dict[tuple[str, str], list[int]] = {}
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        rel = path.relative_to(PACKAGE_DIR)
        if rel.parts[0] == "_data":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        skip = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in skip
                and _is_contracts_string(node.value)
            ):
                key = (rel.as_posix(), node.value)
                counts[key] += 1
                lines.setdefault(key, []).append(node.lineno)
    return counts, lines


def test_contracts_strings_match_allow_list() -> None:
    counts, lines = _scan()
    allowed = {(file, text): count for file, text, count, _ in ALLOWED}
    problems = [
        f"{file}:{lines[(file, text)]} {text!r} x{count} (allowed {allowed.get((file, text), 0)})"
        for (file, text), count in sorted(counts.items())
        if count != allowed.get((file, text), 0)
    ]
    problems += [
        f"{file} {text!r} allowed x{count} but found x{counts.get((file, text), 0)}"
        for (file, text), count in sorted(allowed.items())
        if (file, text) not in counts
    ]
    assert not problems, "contracts/ path strings outside the allow-list:\n" + "\n".join(problems)


def test_allow_list_entries_carry_reasons() -> None:
    assert all(reason for *_, reason in ALLOWED)
