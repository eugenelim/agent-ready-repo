"""Derive § Grounding's AC-0012 terminal-safe sink-class claim."""

from __future__ import annotations

import ast
import sys

from _common import fail, read_text


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise ValueError(f"missing function {name}")


def main() -> int:
    try:
        source = read_text(
            "packages/agentbundle/agentbundle/catalogue_tooling/initialise_self_hosted.py"
        )
        tree = ast.parse(source)
        check = _function(tree, "_is_safe_recipe_text")
        shape = ast.dump(check, include_attributes=False)
        required = ("isinstance", "_RECIPE_TEXT_MAX_LENGTH", "strip", "unicodedata")
        missing = [name for name in required if name not in shape]
        if missing:
            return fail("sink check lacks " + ", ".join(missing))

        from agentbundle.catalogue_tooling.initialise_self_hosted import (
            _RECIPE_TEXT_MAX_LENGTH,
            _is_safe_recipe_text,
        )

        # The value kinds are the complete current Assumptions enumeration, not
        # a sample discovered from today's state file.  The values themselves
        # are representatives to exercise the implementation's scalar boundary.
        values = {
            "schema_version": "3",
            "source_revision_tag": "v0.47.0",
            "source_revision_sha": "a" * 40,
            "archive_sha256": "b" * 64,
            "managed_path": "packs/core/pack.toml",
            "planned_path": "profiles/default.toml",
            "companion_path": "AGENTS.upstream.md",
            "pack_version": "0.47.0",
            "adapter_contract_version": "0.3",
            "dependency_edge_name": "catalogue-curation",
            "source_uri": "catalogue+https://example.test/channel.json",
            "artifact_url": "https://example.test/catalogue.tar.gz",
        }
        rejected: list[str] = []
        for name, value in values.items():
            if not _is_safe_recipe_text(value):
                rejected.append(name)
            for hostile in (f" {value}", f"{value}\x1b[31m", f"{value}\u200b"):
                if _is_safe_recipe_text(hostile):
                    return fail(f"sink accepts hostile {name} variant")
        for value in (None, 3, [], {"value": "text"}):
            if _is_safe_recipe_text(value):
                return fail("sink accepts a non-string shape")
        if not _is_safe_recipe_text("x" * _RECIPE_TEXT_MAX_LENGTH):
            return fail("sink rejects its declared length bound")
        if _is_safe_recipe_text("x" * (_RECIPE_TEXT_MAX_LENGTH + 1)):
            return fail("sink accepts beyond its declared length bound")
        if rejected:
            return fail("sink rejects declared class member(s): " + ", ".join(rejected))
        print("sink class: " + ", ".join(values))
        print(f"length bound: {_RECIPE_TEXT_MAX_LENGTH}")
        print("residual: none")
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"sink-class derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
