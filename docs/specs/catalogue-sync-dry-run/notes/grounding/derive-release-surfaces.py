"""Derive § Grounding's version-bump release surfaces without version searching."""

from __future__ import annotations

import sys
import tomllib

from _common import fail, read_text


def main() -> int:
    try:
        package_rules = read_text("packages/AGENTS.md")
        coupling = read_text("docs/guides/explanation/release-coupling.md")
        conventions = read_text("docs/CONVENTIONS.md")
        package_config = tomllib.loads(read_text("packages/agentbundle/pyproject.toml"))
        required = "Non-cosmetic package changes update both `version.py` and `pyproject.toml`."
        trigger = "Adding a new `agentbundle catalogue <sub>` command"
        if required not in package_rules or trigger not in coupling:
            return fail("version-bump rule or CLI release trigger is absent")
        if "published package also keeps its own `CHANGELOG.md`" not in conventions:
            return fail("published-package changelog coupling is absent")
        package = package_config.get("project", {})
        if package.get("name") != "agentbundle":
            return fail("agentbundle package metadata is absent")
        readme = package.get("readme")
        if not isinstance(readme, str):
            return fail("published package does not declare its readme surface")
        surfaces = [
            "packages/agentbundle/agentbundle/version.py",
            "packages/agentbundle/pyproject.toml",
            "packages/agentbundle/CHANGELOG.md",
            "docs/product/changelog.md",
            f"packages/agentbundle/{readme}",
        ]
        candidates = [
            "documentation for a new CLI command",
            "release automation tag assertions",
        ]
        print("release surfaces: " + ", ".join(surfaces))
        print("residual unclassified candidates: " + ", ".join(candidates))
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"release-surface derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
