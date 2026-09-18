"""Derive § Grounding's mypy wrapper scope and optionality-mode claim."""

from __future__ import annotations

import ast
import sys
import tomllib
from pathlib import Path

from _common import REPO_ROOT, fail, read_text, validate_confined_directory


def _typed_packages(tree: ast.AST) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "TYPED_PACKAGES"
            for target in node.targets
        ):
            value = ast.literal_eval(node.value)
            if isinstance(value, list) and all(isinstance(item, str) for item in value):
                return value
    raise ValueError("TYPED_PACKAGES assignment is not a string list")


def main() -> int:
    if len(sys.argv) != 3:
        return fail("usage: probe-mypy-scope.py tools/lint-mypy.py pyproject.toml")
    try:
        wrapper = Path(sys.argv[1])
        config = Path(sys.argv[2])
        if wrapper.is_absolute() or config.is_absolute():
            return fail("arguments must be repository-relative")
        wrapper_text = read_text(wrapper.as_posix())
        config_data = tomllib.loads(read_text(config.as_posix()))
        packages = _typed_packages(ast.parse(wrapper_text))
        configured = config_data["tool"]["mypy"]["files"]
        strict_optional = config_data["tool"]["mypy"].get("no_strict_optional")
        for package in packages:
            validate_confined_directory(REPO_ROOT, REPO_ROOT / package)
        if any(package.startswith("docs/") for package in packages):
            return fail("mypy wrapper includes docs")
        print("wrapper packages: " + ", ".join(packages))
        print("configured packages: " + ", ".join(configured))
        print(f"no_strict_optional: {strict_optional}")
        print("residual: none")
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"mypy-scope derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
