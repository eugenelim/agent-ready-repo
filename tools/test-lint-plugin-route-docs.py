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
    # Literal, not derived from `lint._offers`. Comparing the sites against
    # `_NO_REPO_ONLY_OFFER` compared two values built by the same helper, so
    # narrowing `_offers` to one spelling left this green while the check named
    # "in both spellings" constrained neither.
    expected = {"claude plugin install core@", "/plugin install core@"}
    _check("both offer spellings are still generated",
           set(lint._offers("core")) == expected,
           f"lint._offers('core') = {sorted(lint._offers('core'))}")
    required = {pat for p in lint.REPO_ONLY for pat in
                (f"claude plugin install {p}@", f"/plugin install {p}@")}
    missing = {p for p, pats in by_path.items() if not required.issubset(pats)}
    _check("every site forbids a repo-only pack offer, in both spellings",
           not missing, f"sites with no offer constraint: {sorted(missing)}")

    # The checks above all derive both sides from `lint.SITES`, so deleting a
    # row — or emptying the list — satisfies every one of them vacuously.
    # Verified: removing the README row and putting the offer back into
    # README.md left this whole file green. The roster of *which* files are
    # guarded is a claim in its own right, so it is enumerated literally here.
    expected_paths = {
        ".github/workflows/publish-claude-plugins.yml",
        "README.md",
        "docs-site/src/content/docs/getting-started/install.md",
        "guides/_shared/explanation/install-routes.md",
        "guides/_shared/explanation/pack-catalogue.md",
        "guides/core/how-to/adapt-to-project.md",
        "packs/core/.apm/hook-wiring/session-start.toml",
        "tools/hooks/README.md",
    }
    actual_paths = {p for p, _, _ in lint.SITES}
    _check("the guarded-site roster is unchanged",
           actual_paths == expected_paths,
           f"dropped: {sorted(expected_paths - actual_paths)}; "
           f"added: {sorted(actual_paths - expected_paths)}")
    # Two files carry two entries each (separate claims in the same file), so
    # the entry count is not the path count. Pin it too: collapsing two entries
    # into one silently drops a claim.
    _check("the entry count is unchanged", len(lint.SITES) == 9,
           f"{len(lint.SITES)} entries, expected 9")

    with tempfile.TemporaryDirectory() as tmp:
        # An empty tree: every site is missing, so every site must report.
        out = lint.check(Path(tmp))
        _check("a missing site reports rather than passing",
               len(out) == len(lint.SITES) and len(out) > 0,
               f"got {len(out)} of {len(lint.SITES)}")

    if FAILURES:
        print(f"test-lint-plugin-route-docs: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-plugin-route-docs: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
