#!/usr/bin/env python3
"""
Phase 4B regression check: verify every active pack appears in guides/README.md
All-packs table.

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


def extract_indexed_packs(guide_index: Path) -> set[str]:
    """
    Extract pack IDs from the '## All packs' table in guides/README.md.
    Only scans between the '## All packs' heading and the next '##' heading
    to avoid false-positives from role/loop tables earlier in the file.
    """
    if not guide_index.exists():
        return set()
    content = guide_index.read_text(encoding="utf-8")
    # Slice to the "## All packs" section only
    match = re.search(r"^## All packs\b", content, re.MULTILINE)
    if not match:
        return set()
    section_start = match.end()
    next_heading = re.search(r"^##", content[section_start:], re.MULTILINE)
    if next_heading:
        section = content[section_start : section_start + next_heading.start()]
    else:
        section = content[section_start:]
    # Match rows like: | [`core`](core/) | ...
    return set(re.findall(r"\|\s*\[`([a-z][a-z\-]+)`\]", section))


def main() -> int:
    active_packs = discover_active_packs()
    indexed_packs = extract_indexed_packs(GUIDE_INDEX)

    missing = [
        p for p in active_packs
        if p not in indexed_packs and p not in GUIDE_OPTIONAL_PACKS
    ]

    if missing:
        print("check-guide-index: FAIL — active packs missing from guides/README.md:")
        for p in missing:
            print(f"  ✗ {p}")
        guide_index_rel = GUIDE_INDEX.relative_to(REPO_ROOT)
        print(f"\nFix: add each missing pack to the 'All packs' table in {guide_index_rel}")
        return 1

    print(
        f"check-guide-index: OK — all {len(active_packs)} active packs present in guide index"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
