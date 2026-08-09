#!/usr/bin/env python3
"""Assert no doc offers the Claude-plugin route for a pack that cannot use it.

Per-site `(path, pattern, expected)` rather than one repo-wide grep, because the
sites do not share a pattern — `README.md` writes `claude plugin install`,
several guides write `/plugin install`, and two files name the dist-tree path
`<output>/claude-plugins/core/…`. A single `! grep -q 'claude plugin install'`
would pass green on most of them.

Each entry also asserts its file **exists**, so a rename is not a silent pass —
the failure mode of every absence-only check.

The `forbidden` patterns are literal substrings; `required` ones pin the
canonical statement so the precondition cannot quietly vanish.

Usage:
    python tools/lint-plugin-route-docs.py [--root .]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "lint-plugin-route-docs"

# A repo-only pack must never be named as the subject of a plugin install.
REPO_ONLY = ("core", "governance-extras", "iac-terraform", "monorepo-extras",
             "release-engineering", "user-guide-diataxis", "catalogue-curation")

SITES: list[tuple[str, list[str], list[str]]] = [
    # (path, forbidden substrings, required substrings)
    ("README.md",
     [f"claude plugin install {p}@" for p in REPO_ONLY],
     ["user-scope"]),
    ("docs-site/src/content/docs/getting-started/install.md",
     [f"claude plugin install {p}@" for p in REPO_ONLY],
     ["Repo-scoped packs"]),
    ("guides/_shared/explanation/install-routes.md",
     [],
     ["The plugin route is user-scope only", "allowed-scopes"]),
    ("guides/_shared/explanation/pack-catalogue.md", [], ["install-routes.md"]),
    ("guides/core/how-to/adapt-to-project.md", [], ["repo-scoped"]),
    (".github/workflows/publish-claude-plugins.yml",
     ["so adopters can install any pack with"],
     ["user-scope"]),
    ("tools/hooks/README.md", [], ["`claude-plugins/core/` subtree"]),
    ("packs/core/.apm/hook-wiring/session-start.toml",
     [], ["There is no `claude-plugins/core/` dist-tree copy"]),
]


def check(root: Path) -> list[str]:
    failures: list[str] = []
    for rel, forbidden, required in SITES:
        path = root / rel
        if not path.is_file():
            failures.append(
                f"{GATE}: {rel} does not exist — this list is stale, or a site "
                f"was renamed and its assertion silently stopped running"
            )
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        for pat in forbidden:
            if pat in body:
                failures.append(
                    f"{GATE}: {rel} contains {pat!r} — that pack cannot be "
                    f"installed by the user-scope plugin route"
                )
        for pat in required:
            if pat not in body:
                failures.append(
                    f"{GATE}: {rel} is missing {pat!r} — the scope precondition "
                    f"is stated once and referenced; this reference is gone"
                )
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    failures = check(Path(args.root).resolve())
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        print(f"{GATE}: FAIL ({len(failures)} issue(s))", file=sys.stderr)
        return 1
    print(f"{GATE}: ok — {len(SITES)} site(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
