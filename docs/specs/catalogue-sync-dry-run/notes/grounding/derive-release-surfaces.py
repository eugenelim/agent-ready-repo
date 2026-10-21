"""Derive § Grounding's version-bump release surfaces without version searching."""

from __future__ import annotations

import sys
import tomllib

from _common import fail, read_text


def main() -> int:
    try:
        package_rules = read_text("packages/AGENTS.md")
        coupling = read_text("docs/guides/explanation/release-coupling.md")
        package_config = tomllib.loads(read_text("packages/agentbundle/pyproject.toml"))
        required = "Non-cosmetic package changes update both `version.py` and `pyproject.toml`."
        trigger = "Adding a new `agentbundle catalogue <sub>` command"
        if required not in package_rules or trigger not in coupling:
            return fail("version-bump rule or CLI release trigger is absent")
        # `docs/CONVENTIONS.md` was retired upstream (#1345, "retire
        # docs/CONVENTIONS.md and re-home every obligation it carried"), so the
        # published-package changelog coupling this derivation used to read from
        # it is no longer readable there. Its re-homed operative location could
        # not be found in `packages/AGENTS.md`, root `AGENTS.md`,
        # `release-coupling.md`, or the work-loop skill; RFC-0095 D2 still states
        # the decision, but an accepted RFC is a decision record rather than an
        # operative rule, so this derivation does not cite it as one. The two
        # checks below remain live, and the package CHANGELOG surface stays
        # grounded in them plus the package's own declared metadata.
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
