#!/usr/bin/env python3
"""Construction tests for tools/lint-plugin-route-docs.py.

Runs the gate against the real tree (it is a docs assertion, so the tree is its
subject) plus synthetic cases for the two failure shapes that matter: a site
that regresses, and a site that disappears.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "lint_plugin_route_docs", Path(__file__).parent / "lint-plugin-route-docs.py"
)
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

FAILURES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def main() -> int:
    print("test-lint-plugin-route-docs:")
    repo = Path(__file__).resolve().parents[1]

    _check("the real tree passes", lint.check(repo) == [], f"got {lint.check(repo)}")

    # The guard that actually locks in the round-four fix: five sites shipped
    # with an empty `forbidden` list, and "names at least one assertion" was
    # true for all of them because each had a `required` pin.
    by_path: dict[str, set[str]] = {}
    for path, forbidden, _ in lint.SITES:
        by_path.setdefault(path, set()).update(forbidden)
    missing = {
        p for p, pats in by_path.items()
        if not set(lint._NO_REPO_ONLY_OFFER).issubset(pats)
    }
    _check("every site forbids a repo-only pack offer, in both spellings",
           not missing, f"sites with no offer constraint: {sorted(missing)}")

    with tempfile.TemporaryDirectory() as tmp:
        # An empty tree: every site is missing, so every site must report.
        out = lint.check(Path(tmp))
        _check("a missing site reports rather than passing",
               len(out) == len(lint.SITES), f"got {len(out)} of {len(lint.SITES)}")

    if FAILURES:
        print(f"test-lint-plugin-route-docs: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-plugin-route-docs: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
