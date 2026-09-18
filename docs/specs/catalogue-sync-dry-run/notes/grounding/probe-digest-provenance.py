"""Derive § Grounding's digest provenance for HTTPS catalogue forms."""

from __future__ import annotations

import ast
import sys

from _common import fail, read_text


def _function(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise ValueError(f"missing {name}")


def main() -> int:
    try:
        source = read_text("packages/agentbundle/agentbundle/https_catalogue.py")
        function = _function(ast.parse(source), "fetch_catalogue_archive_with_provenance")
        body = ast.get_source_segment(source, function) or ""
        archive_marker = "fragment.startswith(\"sha256=\")"
        descriptor_marker = 'archive_sha256=descriptor["sha256"]'
        if archive_marker not in body or descriptor_marker not in body:
            return fail("HTTPS resolver no longer exposes both digest provenance paths")
        print("archive+https digest: adopter-supplied URI fragment")
        print("catalogue+https digest: descriptor sha256 from resolved channel")
        print("residual: none")
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"digest-provenance derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
