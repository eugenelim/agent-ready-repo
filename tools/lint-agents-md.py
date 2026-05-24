#!/usr/bin/env python3
"""Lints AGENTS.md and docs hygiene. Exit non-zero if any check fails.

Checks:
  1. AGENTS.md exists at repo root.
  2. CLAUDE.md is a symlink to AGENTS.md (not a duplicate file).
  3. Root AGENTS.md is under MAX_ROOT_LINES.
  4. No subdirectory AGENTS.md exceeds MAX_SUB_LINES.
  5. Internal markdown links resolve.
  6. docs/CHARTER.md exists.
  7. No legacy docs/constitution/ directory exists.
  8. The four Diátaxis subdirectories under docs/guides/ exist.
  9. Living docs aren't suspiciously stale (warn-only, not a fail).
 10. Drift-watch — phrases that must live in exactly one canonical home.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

MAX_ROOT_LINES = 250
MAX_SUB_LINES = 150
STALE_DAYS = 180  # warn-only threshold


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


def main() -> int:
    os.chdir(_repo_root())
    fail = 0

    def note(msg: str) -> None:
        nonlocal fail
        print(f"✖ {msg}", file=sys.stderr)
        fail = 1

    def warn(msg: str) -> None:
        print(f"⚠ {msg}", file=sys.stderr)

    def ok(msg: str) -> None:
        print(f"✓ {msg}")

    # 1. Root AGENTS.md exists
    agents_md = Path("AGENTS.md")
    if not agents_md.is_file():
        note("AGENTS.md is missing at the repository root.")
    else:
        ok("Root AGENTS.md exists.")

    # 2. CLAUDE.md is a symlink to AGENTS.md
    claude_md = Path("CLAUDE.md")
    if claude_md.is_symlink():
        target = os.readlink(claude_md)
        if target == "AGENTS.md":
            ok("CLAUDE.md → AGENTS.md (symlink).")
        else:
            note(
                f"CLAUDE.md is a symlink, but points to '{target}' instead of 'AGENTS.md'."
            )
    elif claude_md.is_file():
        note(
            "CLAUDE.md is a regular file. It should be a symlink to AGENTS.md to stay in sync."
        )
    else:
        note("CLAUDE.md is missing. Create it with: ln -s AGENTS.md CLAUDE.md")

    # 3. Root AGENTS.md size
    if agents_md.is_file():
        lines = len(agents_md.read_text().splitlines())
        if lines > MAX_ROOT_LINES:
            note(
                f"AGENTS.md is {lines} lines (max {MAX_ROOT_LINES}). "
                f"Move detail to docs/ or .claude/skills/."
            )
        else:
            ok(f"AGENTS.md is {lines} lines (≤ {MAX_ROOT_LINES}).")

    # 4. Per-package AGENTS.md size
    for f in sorted(Path(".").rglob("AGENTS.md")):
        # Match bash `find . -not -path './node_modules/*' -not -path './.git/*'`
        # — top-level exclusion only, not any-depth. A nested
        # packages/x/node_modules/y/AGENTS.md (if one ever appeared)
        # is still checked, matching bash semantics.
        if f.parts[:1] in (("node_modules",), (".git",)):
            continue
        if f == agents_md:
            continue
        lines = len(f.read_text().splitlines())
        limit = MAX_SUB_LINES
        if f.as_posix() == "packs/core/seeds/AGENTS.md":
            limit = MAX_ROOT_LINES
        if lines > limit:
            note(f"./{f.as_posix()} is {lines} lines (max {limit}). Trim or split.")
        else:
            ok(f"./{f.as_posix()} is {lines} lines (≤ {limit}).")

    # 5. Internal markdown links resolve
    link_re = re.compile(r"\]\(([^)]+)\)")
    for f_str in ("AGENTS.md", "docs/CONVENTIONS.md"):
        f = Path(f_str)
        if not f.is_file():
            continue
        for match in link_re.findall(f.read_text()):
            # Skip external schemes (http:, mailto:, etc.)
            if re.match(r"^[a-z]+:", match):
                continue
            target = match.split("#", 1)[0]
            if not target:
                continue
            resolved = f.parent / target
            if not resolved.exists():
                note(f"{f_str}: broken link → {match}")

    # 6. docs/CHARTER.md exists
    if not Path("docs/CHARTER.md").is_file():
        note(
            "docs/CHARTER.md is missing. The charter (mission, scope, principles) is foundational."
        )
    else:
        ok("docs/CHARTER.md exists.")

    # 7. No legacy constitution/ folder
    if Path("docs/constitution").is_dir():
        note(
            "docs/constitution/ exists. This was replaced by docs/CHARTER.md — see docs/CONVENTIONS.md."
        )
    else:
        ok("No legacy docs/constitution/ directory.")

    # 8. Diátaxis structure under docs/guides/
    diataxis_dirs = ("tutorials", "how-to", "reference", "explanation")
    missing = [d for d in diataxis_dirs if not Path(f"docs/guides/{d}").is_dir()]
    if missing:
        note(
            f"docs/guides/ is missing Diátaxis subdirectories: {' '.join(missing)}. "
            f"See docs/guides/README.md."
        )
    else:
        ok("docs/guides/ has all four Diátaxis subdirectories.")

    # 9. Stale living-doc check (warn-only)
    living_docs = (
        "docs/CHARTER.md",
        "docs/architecture/overview.md",
        "docs/product/roadmap.md",
    )
    now_epoch = time.time()
    for f_str in living_docs:
        f = Path(f_str)
        if not f.is_file():
            continue
        try:
            mtime = f.stat().st_mtime
        except OSError:
            mtime = now_epoch
        age = int((now_epoch - mtime) // 86400)
        if age > STALE_DAYS:
            warn(
                f"{f_str} hasn't been touched in {age} days "
                f"(threshold: {STALE_DAYS}). Consider whether it's still accurate."
            )

    # 10. Drift-watch — single-source phrases.
    # See bash source lines 141-204 — three _drift_check invocations + vendor-token
    # loop + gitignore probe loop. Each enumerated below.
    def drift_check(pattern: str, canonical: str, forbidden: list[str]) -> None:
        regex = re.compile(pattern)
        if canonical:
            cpath = Path(canonical)
            if cpath.is_file() and not regex.search(cpath.read_text()):
                note(
                    f"drift-watch: '{pattern}' missing from canonical home {canonical}."
                )
        for forb in forbidden:
            fpath = Path(forb)
            if not fpath.is_file():
                continue
            if regex.search(fpath.read_text()):
                note(
                    f"drift-watch: '{pattern}' re-appeared in {forb} (canonical: {canonical})."
                )

    # 10a — iteration-cap value lives in state.json template, not prose.
    drift_check(
        r'"max_iterations":\s*[0-9]+',
        ".claude/skills/work-loop/assets/state.json",
        [
            ".claude/skills/work-loop/SKILL.md",
            "AGENTS.md",
            "docs/CONVENTIONS.md",
        ],
    )

    # 10b — prose probe for the cap value (belt-and-braces).
    drift_check(
        r"(hard )?cap of (five|5) (in-session )?iterations?",
        "",
        [
            ".claude/skills/work-loop/SKILL.md",
            "AGENTS.md",
            "docs/CONVENTIONS.md",
        ],
    )

    # 10c — verification-mode triplet single-sourced in work-loop SKILL.
    drift_check(
        r"\*\*Goal-based check\*\*",
        ".claude/skills/work-loop/SKILL.md",
        ["AGENTS.md", "docs/CONVENTIONS.md"],
    )

    # 10d — Vendor-specific UX tokens belong under .claude/ only.
    vendor_re = re.compile(r"\bultrathink\b|Plan Mode \(Shift\+Tab")
    for f_str in ("AGENTS.md", "docs/CONVENTIONS.md", "docs/CHARTER.md", "docs/APPROACH.md"):
        f = Path(f_str)
        if not f.is_file():
            continue
        if vendor_re.search(f.read_text()):
            note(
                f"drift-watch: vendor token (ultrathink / 'Plan Mode (Shift+Tab') in {f_str}. "
                f"Move it under .claude/."
            )

    # 10e — Session-scratch artifacts must be gitignored.
    for probe in (
        "docs/specs/example/state.json",
        "docs/specs/example/notes/implementer-T1-0.md",
        ".worktrees/T1/README.md",
    ):
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", probe],
            capture_output=True, check=False,
        )
        if result.returncode != 0:
            note(
                f"drift-watch: '{probe}' should be gitignored "
                f"(session-scratch — see .claude/skills/work-loop/references/state-schema.md, "
                f"CONVENTIONS.md#supervisor-mode)."
            )

    if fail:
        print()
        print("Docs lint: failed.")
        return 1
    print()
    print("Docs lint: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
