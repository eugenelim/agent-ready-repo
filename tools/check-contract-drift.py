#!/usr/bin/env python3
"""Drift check for Digital Experience Contract copies (RFC-0071 Area A / D1).

Four packs each carry an identical copy of the Digital Experience Contract
template at a known anchor path within their skills tree. This tool verifies
all four copies share the same schema-version and structural fingerprint
(section headers + Required-tier annotations). Independent installability
requires each pack to carry its own copy; this check is the enforcement
mechanism that prevents them from drifting apart.

Algorithm:
  1. Confirm all four files exist.
  2. Byte-compare all four copies — exit 0 immediately if identical (fast path).
  3. On any byte divergence, fall back to structural-fingerprint comparison to
     produce a named diagnosis: which pack, which field or section, what was
     expected vs. found.

Usage:
    python tools/check-contract-drift.py [--root .]

``--root`` is the repo root containing ``packs/`` (default: CWD).

Exit codes: 0 = no drift, 1 = drift detected (diagnosis on stderr).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PACK_ANCHORS: dict[str, str] = {
    "product-strategy": (
        "packs/product-strategy/.apm/skills/"
        "synthesize-stakeholder-research/references/digital-experience-contract.md"
    ),
    "product-engineering": (
        "packs/product-engineering/.apm/skills/"
        "frame-intent/references/digital-experience-contract.md"
    ),
    "experience-design": (
        "packs/experience-design/.apm/skills/"
        "design-review/references/digital-experience-contract.md"
    ),
    "core": (
        "packs/core/.apm/skills/"
        "frontend-engineering/references/digital-experience-contract.md"
    ),
}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SCHEMA_VERSION_RE = re.compile(r'^schema-version:\s*"([^"]+)"', re.MULTILINE)
_H2_RE = re.compile(r"^## (.+)$", re.MULTILINE)
_H3_RE = re.compile(r"^### (.+)$", re.MULTILINE)
_REQUIRED_RE = re.compile(r"^<!-- Required: (.+?) -->$", re.MULTILINE)


def _parse_frontmatter(text: str, pack: str) -> str:
    """Extract schema-version from YAML frontmatter; exit 1 on failure."""
    m = _FRONTMATTER_RE.search(text)
    if not m:
        print(f"error: {pack}: no parseable frontmatter block (expected --- delimiters)", file=sys.stderr)
        sys.exit(1)
    version_m = _SCHEMA_VERSION_RE.search(m.group(1))
    if not version_m:
        print(f"error: {pack}: no schema-version key in frontmatter", file=sys.stderr)
        sys.exit(1)
    return version_m.group(1)


def _structural_fingerprint(text: str) -> list[tuple[str, str, str]]:
    """Return ordered list of (kind, text, annotation) tuples.

    kind: 'h2' | 'h3' | 'required'
    annotation: the tier string for 'required', empty otherwise.
    Captures only the structural markers; ignores prose comment lines.
    """
    fingerprint: list[tuple[str, str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            fingerprint.append(("h2", line[3:].strip(), ""))
        elif line.startswith("### "):
            fingerprint.append(("h3", line[4:].strip(), ""))
            # Peek at the next non-empty line for the Required annotation
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                req_m = _REQUIRED_RE.match(lines[j].strip())
                if req_m:
                    fingerprint.append(("required", lines[j].strip(), req_m.group(1)))
        i += 1
    return fingerprint


def _find_majority_index(fps: list[list[tuple[str, str, str]]]) -> int:
    """Return the index of the pack that matches the most others — majority reference.

    When one copy drifts, the three agreeing copies each have 2 matches; the
    drifting copy has 0. Picking the index with the highest match count avoids
    blaming the three innocent packs when the fixed reference (index 0) happens
    to be the drifter.
    """
    n = len(fps)
    match_counts = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if fps[i] == fps[j]:
                match_counts[i] += 1
                match_counts[j] += 1
    return match_counts.index(max(match_counts))


def _diagnose(
    packs: list[str],
    texts: list[str],
    versions: list[str],
    fps: list[list[tuple[str, str, str]]],
) -> None:
    """Print a named diagnosis of all drift found across the four copies."""
    ref_idx = _find_majority_index(fps)
    reference_pack = packs[ref_idx]
    ref_version = versions[ref_idx]
    ref_fp = fps[ref_idx]
    errors: list[str] = []

    for i, pack in enumerate(packs):
        if i == ref_idx:
            continue
        if versions[i] != ref_version:
            errors.append(
                f"  schema-version mismatch: {pack} has '{versions[i]}', "
                f"{reference_pack} has '{ref_version}'"
            )

    for i, pack in enumerate(packs):
        if i == ref_idx:
            continue
        fp = fps[i]
        if len(fp) != len(ref_fp):
            errors.append(
                f"  {pack}: structural fingerprint length differs from {reference_pack} "
                f"({len(fp)} vs {len(ref_fp)} entries)"
            )
            # Report first positional divergence
            for j, (ref_item, fp_item) in enumerate(
                zip(ref_fp, fp[: len(ref_fp)])
            ):
                if ref_item != fp_item:
                    errors.append(
                        f"    first divergence at position {j}: "
                        f"expected {ref_item}, got {fp_item}"
                    )
                    break
            # Report true extra / missing entries by set difference
            extra_items = [item for item in fp if item not in ref_fp]
            missing_items = [item for item in ref_fp if item not in fp]
            for item in extra_items:
                errors.append(f"    extra in {pack}: {item}")
            for item in missing_items:
                errors.append(f"    missing in {pack}: {item}")
        else:
            for j, (ref_item, fp_item) in enumerate(zip(ref_fp, fp)):
                if ref_item != fp_item:
                    errors.append(
                        f"  {pack}: divergence at position {j}: "
                        f"expected {ref_item!r}, got {fp_item!r}"
                    )

    if errors:
        print("DRIFT DETECTED:", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
    else:
        # Bytes differed but structure matches — likely whitespace/comment drift
        print(
            "drift: bytes differ but structural fingerprint matches — "
            "whitespace or comment-only divergence; all four copies must be byte-identical",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify all four Digital Experience Contract copies are equivalent."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root containing packs/ (default: CWD)",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    packs = list(PACK_ANCHORS.keys())
    paths = [root / rel for rel in PACK_ANCHORS.values()]

    # Step 1: confirm all four files exist
    missing = [str(p) for p in paths if not p.is_file()]
    if missing:
        for m in missing:
            print(f"error: missing contract copy: {m}", file=sys.stderr)
        return 1

    # Step 2: read all four files as bytes
    byte_contents = [p.read_bytes() for p in paths]

    # Step 3: byte-compare (fast path)
    if all(b == byte_contents[0] for b in byte_contents[1:]):
        return 0

    # Step 4: structural diagnosis
    texts = [b.decode("utf-8", errors="replace") for b in byte_contents]
    versions = [_parse_frontmatter(t, pack) for t, pack in zip(texts, packs)]
    fps = [_structural_fingerprint(t) for t in texts]
    _diagnose(packs, texts, versions, fps)
    return 1


if __name__ == "__main__":
    sys.exit(main())
