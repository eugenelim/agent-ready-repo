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
import tomllib
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

    # 2. CLAUDE.md is a symlink to AGENTS.md — or a Windows-materialised
    #    symlink (`git config core.symlinks false`, the default on
    #    Windows without Developer Mode, writes the link target as the
    #    file's literal content). Either shape is accepted.
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
        # Windows-materialised symlink: the file content is the link
        # target string ("AGENTS.md", with or without trailing newline).
        # Anything else is a real duplicate file and a drift hazard.
        content = claude_md.read_text(encoding="utf-8", errors="replace").strip()
        if content == "AGENTS.md":
            ok("CLAUDE.md → AGENTS.md (Windows-materialised symlink).")
        else:
            note(
                "CLAUDE.md is a regular file with content other than the link "
                "target 'AGENTS.md'. Replace with a symlink (Unix: "
                "`ln -sf AGENTS.md CLAUDE.md`) or a one-line file containing "
                "exactly 'AGENTS.md' (Windows without Developer Mode)."
            )
    else:
        note("CLAUDE.md is missing. Create it with: ln -s AGENTS.md CLAUDE.md")

    # 3. Root AGENTS.md size
    if agents_md.is_file():
        lines = len(agents_md.read_text(encoding="utf-8").splitlines())
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
        lines = len(f.read_text(encoding="utf-8").splitlines())
        limit = MAX_SUB_LINES
        # The core pack's governance seed (AGENTS.md) is a root-class doc
        # (250-line cap), not a nested package AGENTS.md — wherever it lands.
        # That covers packs/core/seeds/AGENTS.md and its build-projected copies
        # under dist/<route>/core/seeds/AGENTS.md (issue #190 ships seeds inside
        # the APM and Claude-plugin artifacts).
        if (
            f.name == "AGENTS.md"
            and f.parent.name == "seeds"
            and f.parent.parent.name == "core"
        ):
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
        for match in link_re.findall(f.read_text(encoding="utf-8")):
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

    # 8. Diátaxis structure under docs/guides/ — accepted either at the top
    #    level (the by-quadrant scaffold an adopter installs) or under
    #    docs/guides/_shared/ (the per-pack layout this catalogue uses, ADR-0020:
    #    quadrants live within each pack, with the cross-cutting writing-rule
    #    READMEs in _shared/).
    diataxis_dirs = ("tutorials", "how-to", "reference", "explanation")
    missing = [
        d
        for d in diataxis_dirs
        if not Path(f"docs/guides/{d}").is_dir()
        and not Path(f"docs/guides/_shared/{d}").is_dir()
    ]
    if missing:
        note(
            f"docs/guides/ is missing Diátaxis subdirectories: {' '.join(missing)}. "
            f"See docs/guides/README.md."
        )
    else:
        ok("docs/guides/ has all four Diátaxis subdirectories (top-level or _shared/).")

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
            if cpath.is_file() and not regex.search(cpath.read_text(encoding="utf-8")):
                note(
                    f"drift-watch: '{pattern}' missing from canonical home {canonical}."
                )
        for forb in forbidden:
            fpath = Path(forb)
            if not fpath.is_file():
                continue
            if regex.search(fpath.read_text(encoding="utf-8")):
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
    for f_str in ("AGENTS.md", "docs/CONVENTIONS.md", "docs/CHARTER.md"):
        f = Path(f_str)
        if not f.is_file():
            continue
        if vendor_re.search(f.read_text(encoding="utf-8")):
            note(
                f"drift-watch: vendor token (ultrathink / 'Plan Mode (Shift+Tab') in {f_str}. "
                f"Move it under .claude/."
            )

    # 10f — Legacy Codex managed-skills block must not survive a
    # post-RFC-0009 install. When the contract declares Codex `skill`
    # as `direct-directory`, the projected AGENTS.md should not carry
    # the `<!-- agent-skills:start -->` literal — the one-shot
    # migration strip should have removed it. Warning-only (does not
    # `note(...)` / fail) so adopters mid-migration aren't blocked.
    contract_path = Path("docs/contracts/adapter.toml")
    legacy_marker = "<!-- agent-skills:start -->"
    if contract_path.is_file():
        try:
            contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            contract = None
        codex_skill_is_direct_directory = False
        if contract is not None:
            for entry in contract.get("adapter", {}).get("codex", {}).get("projection", []):
                if entry.get("primitive") == "skill" and entry.get("mode") == "direct-directory":
                    codex_skill_is_direct_directory = True
                    break
        if codex_skill_is_direct_directory:
            for probe in ("AGENTS.md", "packs/core/seeds/AGENTS.md"):
                f = Path(probe)
                if f.is_file() and legacy_marker in f.read_text(encoding="utf-8"):
                    warn(
                        f"legacy-codex-skill-block: {probe} still contains "
                        f"{legacy_marker!r}. Codex `skill` is now "
                        f"`direct-directory`; run `make build-self` to let "
                        f"the migration strip remove the block."
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

    # 10g — risk-trigger block byte-identical across the four docs that
    # carry it (work-loop-light-mode spec AC2): the projected work-loop
    # SKILL.md (canonical wording), root AGENTS.md, the seed AGENTS.md, and
    # projected docs/CONVENTIONS.md. Source↔projection equality for SKILL.md
    # and CONVENTIONS.md is build-self's job (projection drift gate); this
    # check guards the four doc homes against a hand-edit diverging one from
    # the rest — the standing guard the spec's one-time grep could not
    # provide. Marker-driven, mirroring 10f's precedent.
    rt_start = "<!-- risk-triggers:start"
    rt_end = "risk-triggers:end -->"
    rt_canonical = ".claude/skills/work-loop/SKILL.md"
    rt_files = (
        rt_canonical,
        "AGENTS.md",
        "packs/core/seeds/AGENTS.md",
        "docs/CONVENTIONS.md",
    )
    rt_blocks = {}
    for f_str in rt_files:
        f = Path(f_str)
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        i = text.find(rt_start)
        if i == -1:
            continue
        j = text.find(rt_end, i)
        if j == -1:
            # Asymmetric markers (start without end) are themselves drift —
            # fail closed rather than silently dropping the copy.
            note(
                f"risk-trigger-block drift: {f_str} has a `risk-triggers:start` "
                f"marker with no matching `risk-triggers:end` (truncated block)."
            )
            continue
        rt_blocks[f_str] = text[i : j + len(rt_end)]
    if len(rt_blocks) >= 2 and len(set(rt_blocks.values())) > 1:
        ref = rt_blocks.get(rt_canonical)
        if ref is None:
            note(
                "risk-trigger-block drift: copies carrying the "
                "`risk-triggers` markers are not byte-identical to each other."
            )
        else:
            for f_str, block in rt_blocks.items():
                if f_str != rt_canonical and block != ref:
                    note(
                        f"risk-trigger-block drift: {f_str} differs from the "
                        f"canonical block in {rt_canonical}. The "
                        f"`risk-triggers:start`..`:end` span must be "
                        f"byte-identical across all copies "
                        f"(work-loop-light-mode spec AC2)."
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
