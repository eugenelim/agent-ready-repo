#!/usr/bin/env python3
"""
Verify every active pack has a direct guide-home link in guides/README.md.

Exit 0 = all packs accounted for.
Exit 1 = at least one active pack is absent from the guide index.

Usage:
  python3 tools/check-guide-index.py
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PACKS_DIR = REPO_ROOT / "packs"
GUIDE_INDEX = REPO_ROOT / "guides" / "README.md"

# Packs excluded from the guide index — internal or compatibility-only
EXCLUDED_PACKS = {
    "_example",          # internal example only
    "user-guide-diataxis",  # deprecated compatibility pack; not a current recommendation
}

# Additional packs that are correctly omitted because they have no public guide
# (atomic 1-skill packs whose README is their only guide surface) — add here if needed
GUIDE_OPTIONAL_PACKS: set[str] = set()


def discover_active_packs() -> list[str]:
    """Return pack IDs for all packs with a pack.toml, excluding EXCLUDED_PACKS."""
    packs = []
    for pack_dir in sorted(PACKS_DIR.iterdir()):
        if not pack_dir.is_dir():
            continue
        if (pack_dir / "pack.toml").exists() and pack_dir.name not in EXCLUDED_PACKS:
            packs.append(pack_dir.name)
    return packs


def extract_linked_packs(guide_index: Path) -> set[str]:
    """Extract pack IDs from direct ``<pack>/`` guide-home links.

    The guide root may organize discovery by outcome, role, or another reader
    need. Requiring one direct link per active pack preserves complete coverage
    without requiring a duplicate all-packs table or a specific page layout.
    """
    if not guide_index.exists():
        return set()
    content = guide_index.read_text(encoding="utf-8")
    return set(re.findall(r"\]\(([a-z][a-z0-9-]*)/\)", content))


def find_missing_packs(
    active_packs: list[str], indexed_packs: set[str]
) -> list[str]:
    """Return active packs that have no required direct guide-home link."""
    return [
        p for p in active_packs
        if p not in indexed_packs and p not in GUIDE_OPTIONAL_PACKS
    ]


def report_coverage(active_packs: list[str], indexed_packs: set[str]) -> int:
    """Report guide-index coverage and return its process exit code."""
    missing = find_missing_packs(active_packs, indexed_packs)

    if missing:
        print("check-guide-index: FAIL — active packs missing from guides/README.md:")
        for p in missing:
            print(f"  ✗ {p}")
        guide_index_rel = GUIDE_INDEX.relative_to(REPO_ROOT)
        print(
            "\nFix: add a direct '<pack>/' guide-home link for each missing "
            f"pack in {guide_index_rel}"
        )
        return 1

    print(
        f"check-guide-index: OK — all {len(active_packs)} active packs present in guide index"
    )
    return 0


def main() -> int:
    """Check the repository guide index."""
    return report_coverage(
        discover_active_packs(), extract_linked_packs(GUIDE_INDEX)
    )


if __name__ == "__main__":
    sys.exit(main())
