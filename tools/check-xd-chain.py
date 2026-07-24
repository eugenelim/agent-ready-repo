#!/usr/bin/env python3
"""Cross-pack XD chain deterministic checker (ini-003 M5 / spec/cross-pack-experience-eval).

Validates five structural invariants of the XD skill chain without running an LLM:

  1. Chain completeness   — all five chain skills exist at their expected SKILL.md paths
  2. Phantom-handoff      — every backtick-quoted name in the description resolves to an
                             existing SKILL.md within the pack; cross-pack references
                             (a name qualified with "in the <pack> pack" nearby) are exempt,
                             as are pack names themselves
  3. Boundary guards      — each chain skill's description backtick-references its
                             required neighbors per the spec adjacency map
  4. Contract copies      — Digital Experience Contract copies exist in all four packs
  5. Description length   — each chain skill description is ≤1024 chars (agentbundle cap)

Report-only by default: exits 0 regardless of findings so the checker can ship alongside
new evals without becoming a gate immediately. Pass --gate to make it fail-closed (exit 1
on any failure), matching the lint tools' convention. See docs/guides/experience-design/
how-to/run-cross-pack-eval.md.

Usage:
    python3 tools/check-xd-chain.py [--root .] [--gate]

Exit codes:
  0 — clean in report-only mode; or all checks passed with --gate
  1 — at least one check failed (only when --gate is set)
  2 — tool error (unreadable SKILL.md, malformed frontmatter, invalid root)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ── Chain definition ──────────────────────────────────────────────────────────

CHAIN_SKILLS: list[str] = [
    "design-token-taxonomy",
    "design-system-foundations",
    "information-architecture",
    "copy-direction",
    "design-review",
]

# Explicit adjacency map: each skill's description must backtick-reference
# these neighbor skills. Derived from actual 1.5.0 frontmatter; see spec.md
# "Boundary guard adjacency map" section.
CHAIN_GUARD_REQUIREMENTS: dict[str, list[str]] = {
    "design-token-taxonomy":     ["design-system-foundations"],
    "design-system-foundations": ["design-token-taxonomy", "information-architecture"],
    "information-architecture":  ["copy-direction"],
    "copy-direction":            ["content-design", "tone-of-voice"],
    "design-review":             ["copy-direction"],
}

# Digital Experience Contract anchor paths (same as check-contract-drift.py).
CONTRACT_ANCHORS: dict[str, str] = {
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

# Description-length cap (agentbundle max).
DESC_MAX_CHARS: int = 1024

# ── Helpers ───────────────────────────────────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
_BACKTICK_NAME_RE = re.compile(r"`([a-z][a-z0-9-]+)`")


def _repo_root(root_arg: str | None) -> Path:
    if root_arg:
        p = Path(root_arg).resolve()
        if not p.is_dir():
            print(f"error: --root {root_arg!r} is not a directory", file=sys.stderr)
            sys.exit(2)
        return p
    import subprocess
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return Path.cwd()


def _skill_path(root: Path, pack: str, skill: str) -> Path:
    return root / "packs" / pack / ".apm" / "skills" / skill / "SKILL.md"


def _read_description(skill_path: Path) -> str:
    """Return the raw `description:` value from SKILL.md YAML frontmatter.

    Handles both quoted (`description: "..."`) and bare (`description: ...`) forms
    via regex extraction. SKILL.md frontmatter is YAML, not TOML, so parsing is
    regex-based rather than library-based.
    Exits 2 on unreadable file or missing frontmatter.
    """
    try:
        text = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {skill_path}: {exc}", file=sys.stderr)
        sys.exit(2)
    m = _FRONTMATTER_RE.match(text)
    if not m:
        print(f"error: no YAML frontmatter found in {skill_path}", file=sys.stderr)
        sys.exit(2)
    frontmatter = m.group(1)
    # Quoted form: description: "..."
    dm = re.search(
        r'^description:\s*"((?:[^"\\]|\\.)*)"\s*$',
        frontmatter,
        re.MULTILINE | re.DOTALL,
    )
    if dm:
        return dm.group(1).replace('\\"', '"')
    # Bare form: description: some text without quotes
    dm = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if dm:
        return dm.group(1).strip()
    return ""


def _is_cross_pack_ref(name: str, description: str) -> bool:
    """Return True if `name` is a cross-pack reference in `description`.

    A cross-pack reference is one where the backtick-quoted name is accompanied
    by a phrase like "in the `product-engineering` pack" or "in the product-engineering
    pack" nearby in the same context window.
    """
    for match in re.finditer(r"`" + re.escape(name) + r"`", description):
        start = max(0, match.start() - 120)
        end = min(len(description), match.end() + 120)
        context = description[start:end]
        if re.search(r"in the `?[\w-]+`? pack", context):
            return True
    return False


def _all_pack_skills(root: Path, pack: str = "experience-design") -> set[str]:
    """Return the set of skill names in the pack (based on directory names)."""
    skills_dir = root / "packs" / pack / ".apm" / "skills"
    if not skills_dir.is_dir():
        return set()
    return {
        d.name
        for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    }


# ── Checks ────────────────────────────────────────────────────────────────────

Finding = tuple[str, str]  # (check_name, message)


def check_chain_completeness(root: Path) -> list[Finding]:
    """Check 1 — each chain skill has a SKILL.md at its expected path."""
    findings: list[Finding] = []
    for skill in CHAIN_SKILLS:
        path = _skill_path(root, "experience-design", skill)
        if path.exists():
            print(f"  ✓ chain skill exists: {skill}")
        else:
            findings.append(("chain-completeness", f"missing SKILL.md for chain skill '{skill}' at {path}"))
            print(f"  ✖ chain skill missing: {skill} (expected {path})")
    return findings


def check_phantom_handoff(root: Path, pack_skills: set[str]) -> list[Finding]:
    """Check 2 — every backtick-quoted name in the description resolves to an
    existing skill in the pack.

    Cross-pack references (name accompanied by 'in the <pack> pack') are exempt.
    Pack names themselves are also exempt.
    """
    findings: list[Finding] = []
    pack_names = {
        "product-strategy", "product-engineering", "experience-design",
        "core", "architect", "desk-research",
    }
    for skill in CHAIN_SKILLS:
        path = _skill_path(root, "experience-design", skill)
        if not path.exists():
            continue
        description = _read_description(path)
        backtick_names = _BACKTICK_NAME_RE.findall(description)
        skill_ok = True
        for name in backtick_names:
            if name == skill:
                continue  # self-reference is fine
            if name in pack_names:
                continue  # pack name, not a skill reference
            if _is_cross_pack_ref(name, description):
                continue  # cross-pack reference is explicitly exempt
            if name not in pack_skills:
                findings.append((
                    "phantom-handoff",
                    f"'{skill}' description references `{name}` but no such skill exists in the pack",
                ))
                print(f"  ✖ phantom reference in {skill}: `{name}` not found in pack")
                skill_ok = False
        if skill_ok:
            print(f"  ✓ no phantom references in: {skill}")
    return findings


def check_boundary_guards(root: Path) -> list[Finding]:
    """Check 3 — each chain skill's description backtick-references its required neighbors."""
    findings: list[Finding] = []
    for skill, required_neighbors in CHAIN_GUARD_REQUIREMENTS.items():
        path = _skill_path(root, "experience-design", skill)
        if not path.exists():
            continue
        description = _read_description(path)
        backtick_names = set(_BACKTICK_NAME_RE.findall(description))
        missing = [n for n in required_neighbors if n not in backtick_names]
        if missing:
            findings.append((
                "boundary-guards",
                f"'{skill}' description is missing required guard reference(s): {missing}",
            ))
            print(f"  ✖ missing guard(s) in {skill}: {missing}")
        else:
            print(f"  ✓ boundary guards present in: {skill}")
    return findings


def check_contract_copies(root: Path) -> list[Finding]:
    """Check 4 — Digital Experience Contract files exist in all four packs."""
    findings: list[Finding] = []
    for pack, rel_path in CONTRACT_ANCHORS.items():
        full = root / rel_path
        if full.exists():
            print(f"  ✓ DEC copy present: {pack}")
        else:
            findings.append((
                "contract-copies",
                f"Digital Experience Contract missing in {pack} pack at {rel_path}",
            ))
            print(f"  ✖ DEC copy missing: {pack} (expected {rel_path})")
    return findings


def check_description_length(root: Path) -> list[Finding]:
    """Check 5 — each chain skill description is ≤1024 chars (agentbundle cap)."""
    findings: list[Finding] = []
    for skill in CHAIN_SKILLS:
        path = _skill_path(root, "experience-design", skill)
        if not path.exists():
            continue
        description = _read_description(path)
        length = len(description)
        if length > DESC_MAX_CHARS:
            findings.append((
                "description-length",
                f"'{skill}' description is {length} chars (cap is {DESC_MAX_CHARS})",
            ))
            print(f"  ✖ description over cap in {skill}: {length}/{DESC_MAX_CHARS} chars")
        else:
            print(f"  ✓ description within cap: {skill} ({length}/{DESC_MAX_CHARS} chars)")
    return findings


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="XD chain structural-invariant checker (report-only by default).",
    )
    parser.add_argument(
        "--root",
        metavar="DIR",
        default=None,
        help="Repo root (default: git toplevel or CWD).",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Exit 1 on any failure (fail-closed gate mode).",
    )
    args = parser.parse_args()

    root = _repo_root(args.root)
    pack_skills = _all_pack_skills(root)

    all_findings: list[Finding] = []

    print("\n[check-xd-chain] Check 1: chain completeness")
    all_findings.extend(check_chain_completeness(root))

    print("\n[check-xd-chain] Check 2: phantom-handoff detection")
    all_findings.extend(check_phantom_handoff(root, pack_skills))

    print("\n[check-xd-chain] Check 3: boundary guards")
    all_findings.extend(check_boundary_guards(root))

    print("\n[check-xd-chain] Check 4: contract copies")
    all_findings.extend(check_contract_copies(root))

    print("\n[check-xd-chain] Check 5: description length")
    all_findings.extend(check_description_length(root))

    print()
    if not all_findings:
        print("[check-xd-chain] All checks passed.")
        return 0

    print(f"[check-xd-chain] {len(all_findings)} finding(s):")
    for check_name, msg in all_findings:
        prefix = "::warning ::" if not args.gate else "::error ::"
        print(f"  {prefix}[{check_name}] {msg}")

    if args.gate:
        return 1
    print("[check-xd-chain] Report-only mode — run with --gate to fail-close.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
