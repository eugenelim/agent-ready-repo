#!/usr/bin/env python3
"""Roster tripwire: the published set, enumerated literally.

**Why this exists separately from `lint-plugin-membership.py`.** That gate
derives *both* sides of its comparison from the same predicate, so a predicate
bug moves them together and it stays green — a tautology. This one hard-codes
the expected rosters, so it is the only check that turns red when widening a
pack's `allowed-scopes` changes what gets published.

**If this fails, that is the gate working.** After
docs/specs/claude-plugin-route-scope, editing one line of `allowed-scopes`
publishes a pack's code to a public marketplace, or withdraws it. Do not "fix" a
failure by editing the lists below to match reality — confirm the change in
publication is what you meant (the spec's `Ask first` boundary), then update the
list in the same commit that changes the pack.

Both directions are pinned. Absences alone catch a fail-open bug; only the
present-set catches a fail-closed truncation that silently drops a pack.

Usage:
    python tools/lint-plugin-roster.py [--root .]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

GATE = "lint-plugin-roster"

# Repo-only: `allowed-scopes` omits "user", so the user-scope plugin route
# cannot honour an install of them.
NOT_PUBLISHED = frozenset({
    "catalogue-curation",
    "core",
    "governance-extras",
    "iac-terraform",
    "monorepo-extras",
    "release-engineering",
    "user-guide-diataxis",
})

# User-capable, and therefore offered on the route.
PUBLISHED = frozenset({
    "architect",
    "atlassian",
    "contracts",
    "converters",
    "credential-brokers",
    "desk-research",
    "experience-design",
    "figma",
    "frontend-engineering",
    "github",
    "linear",
    "product-documentation",
    "product-engineering",
    "product-strategy",
})


def check(root: Path) -> list[str]:
    marketplace = root / ".claude-plugin" / "marketplace.json"
    if not marketplace.exists():
        return [f"{GATE}: .claude-plugin/marketplace.json is missing"]
    listed = {
        p.get("name")
        for p in json.loads(marketplace.read_text(encoding="utf-8")).get("plugins", [])
        if p.get("name")
    }
    failures = []
    for name in sorted(listed & NOT_PUBLISHED):
        failures.append(
            f"{GATE}: {name!r} is published but is pinned repo-only. If you "
            f"widened its allowed-scopes, that publishes its code to a public "
            f"marketplace — see the spec's `Ask first` boundary — and this list "
            f"moves in the same commit."
        )
    for name in sorted(PUBLISHED - listed):
        failures.append(
            f"{GATE}: {name!r} is pinned as published but is absent from the "
            f"marketplace — a fail-closed truncation, or a deliberate narrowing "
            f"this list has not caught up with."
        )
    # A pack in neither list is new: force a decision rather than defaulting.
    for name in sorted(listed - PUBLISHED - NOT_PUBLISHED):
        failures.append(
            f"{GATE}: {name!r} is published but appears in neither roster — add "
            f"it to PUBLISHED if publishing it is intended."
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
    print(f"{GATE}: ok — {len(PUBLISHED)} published, {len(NOT_PUBLISHED)} withheld")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
