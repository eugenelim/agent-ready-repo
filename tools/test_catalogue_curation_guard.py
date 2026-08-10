"""Tests for lint-catalogue-curation-guard.py."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_dup_groups_do_not_reference_export_catalogue() -> None:
    guard_path = REPO_ROOT / "tools" / "lint-catalogue-curation-guard.py"
    tree = ast.parse(guard_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "DUP_GROUPS"
            for target in node.targets
        ):
            continue
        values = {
            child.value
            for child in ast.walk(node.value)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        }
        assert "export-catalogue" not in values
