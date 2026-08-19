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
  8. The four Diátaxis subdirectories under guides/ exist.
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

import lint_git_ignore  # tools/ is sys.path[0] for a script run

MAX_ROOT_LINES = 120
MAX_ROOT_LOCAL_LINES = 60
MAX_SEED_LINES = 100
MAX_SCOPED_LINES = 80
MAX_EXAMPLE_LINES = 35
STALE_DAYS = 180  # warn-only threshold
_EXCLUDED_SEGMENTS = frozenset({"node_modules", ".git", "dist", "build"})
_EXCLUDED_SUBPATHS = ("_data/catalogue-scaffold", "tests/fixtures")
_FROZEN_DOC_DIRS = ("docs/specs/", "docs/rfc/", "docs/adr/")
# Portable-seed citations pending cleanup; keep this list visible and finite.
_SEED_VENDOR_ROOT_BACKLOG = frozenset({
    "packs/core/seeds/docs/architecture/overview.md",
    "packs/core/seeds/docs/knowledge/README.md",
    "packs/core/seeds/docs/specs/README.md",
    "packs/governance-extras/seeds/docs/adr/README.md",
    "packs/governance-extras/seeds/docs/rfc/README.md",
})


def _is_seed(path: Path) -> bool:
    return (
        path.name == "AGENTS.md"
        and path.parent.name == "seeds"
        and path.parent.parent.name == "core"
    )


def _is_fixture(path: Path) -> bool:
    return "fixtures" in path.parts and "tests" in path.parts


def _is_vendored(path: Path) -> bool:
    value = path.as_posix()
    return bool(_EXCLUDED_SEGMENTS.intersection(path.parts)) or any(
        part in value for part in _EXCLUDED_SUBPATHS
    )


def _is_frozen_record(path: Path) -> bool:
    return any(path.as_posix().startswith(prefix) for prefix in _FROZEN_DOC_DIRS)


def _slug(heading: str) -> str:
    """GitHub-compatible enough here: ``## Step 4. REVIEW`` -> step-4-review."""
    text = heading.lower()
    text = re.sub(r"[^a-z0-9 _-]", "", text)
    return re.sub(r"\s+", "-", text).strip("-")


def _claude_alias(path: Path, target: str, note) -> None:
    if path.is_symlink() and str(path.readlink()) == target:
        return
    target_file = path.parent / target
    accepted = {target}
    if target_file.is_file():
        accepted.add(target_file.read_text(encoding="utf-8"))
    if path.is_file() and path.read_text(
        encoding="utf-8", errors="replace"
    ).strip() in accepted:
        return
    note(f"{path}: alias must point to {target}; generated aliases belong beside AGENTS.md.")


def _repo_root() -> Path:
    # Scrubbed env here too: `rev-parse --show-toplevel` honours an ambient
    # GIT_WORK_TREE/GIT_DIR, which Git sets for hook processes — and this lint
    # runs from the pre-PR hook, then chdir()s to whatever this returns. An
    # unscrubbed call could redirect the entire lint to another tree.
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
            # repo_root=None: this call is *discovering* the root, so there is
            # nothing to fence to yet.
            env=lint_git_ignore.hermetic_git_env(os.environ, repo_root=None),
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


def main() -> int:
    repo_root = _repo_root()
    os.chdir(repo_root)
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
        target = str(claude_md.readlink())
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

    # 4. Every active instruction surface has its class cap.
    active_agents = sorted(
        set(Path().rglob("AGENTS.md")) | set(Path().rglob("AGENTS.local.md"))
    )
    for f in active_agents:
        # Match bash `find . -not -path './node_modules/*' -not -path './.git/*'`
        # — top-level exclusion only, not any-depth. A nested
        # packages/x/node_modules/y/AGENTS.md (if one ever appeared)
        # is still checked, matching bash semantics.
        if _is_vendored(f):
            continue
        if f == agents_md:
            continue
        lines = len(f.read_text(encoding="utf-8").splitlines())
        limit = MAX_ROOT_LOCAL_LINES if f == Path("AGENTS.local.md") else MAX_SCOPED_LINES
        # The core pack's governance seed has its own cap wherever it lands.
        # That covers packs/core/seeds/AGENTS.md and its build-projected copies
        # under dist/<route>/core/seeds/AGENTS.md (issue #190 ships seeds inside
        # the APM and Claude-plugin artifacts).
        if _is_seed(f):
            limit = MAX_SEED_LINES
        elif f.parent.name == "_example":
            limit = MAX_EXAMPLE_LINES
        if lines > limit:
            note(
                f"./{f.as_posix()} is {lines} lines (max {limit}). "
                "Move detail to its owning skill, schema, or documentation."
            )
        else:
            ok(f"./{f.as_posix()} is {lines} lines (≤ {limit}).")

    root_placeholders = (
        "<project-name>", "<one-line description", "<install command>",
        "<test command>", "<test all command>", "<lint command>",
        "<build command>", "<deploy command>", "<smoke command>",
        "<teardown command>", "<seed-test-data command>",
    )
    if agents_md.is_file():
        root_text = agents_md.read_text(encoding="utf-8")
        for marker in root_placeholders:
            if marker in root_text:
                note(
                    f"AGENTS.md contains unresolved adaptation placeholder "
                    f"{marker!r}; adapt it in the live root."
                )

    for f in active_agents:
        if (
            f in (agents_md, Path("AGENTS.local.md"))
            or _is_seed(f)
            or _is_fixture(f)
            or _is_vendored(f)
        ):
            continue
        text = f.read_text(encoding="utf-8")
        first_content = next(
            (
                line
                for line in text.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ),
            "",
        )
        missing = [
            token
            for token in ("Applies to ", "Inherits the root")
            if token not in first_content
        ]
        if missing:
            note(
                f"./{f.as_posix()} is missing {', '.join(missing)}; use "
                "'Applies to <path>. Inherits the root AGENTS.md. "
                "Scope-specific deltas only.'"
            )

    # 5. Internal markdown links and Markdown fragments resolve.
    link_re = re.compile(r"\]\(([^)]+)\)")
    link_files = [
        f for f in active_agents if not _is_vendored(f) and not _is_fixture(f)
    ] + [Path("docs/CONVENTIONS.md")]
    for f in link_files:
        f_str = f.as_posix()
        if not f.is_file():
            continue
        for match in link_re.findall(f.read_text(encoding="utf-8")):
            # Skip external schemes (http:, mailto:, etc.)
            if re.match(r"^[a-z]+:", match):
                continue
            target, _, fragment = match.partition("#")
            resolved = f if not target else f.parent / target
            if not resolved.exists():
                note(f"{f_str}: broken link → {match}")
                continue
            if fragment and resolved.suffix == ".md":
                headings = re.findall(
                    r"^#{1,6}\s+(.+?)\s*$",
                    resolved.read_text(encoding="utf-8"),
                    re.M,
                )
                if headings and fragment not in {_slug(h) for h in headings}:
                    note(
                        f"{f_str}: broken heading fragment → {match}; "
                        "link targets belong to their owning document."
                    )

    for alias in (Path("web/CLAUDE.md"), Path("docs-site/CLAUDE.md")):
        _claude_alias(alias, "AGENTS.md", note)

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
            "docs/constitution/ exists. This was replaced by docs/CHARTER.md"
            " — see docs/CONVENTIONS.md."
        )
    else:
        ok("No legacy docs/constitution/ directory.")

    # 8. Diátaxis structure under guides/ — accepted either at the top
    #    level (the by-quadrant scaffold an adopter installs) or under
    #    guides/_shared/ (the per-pack layout this catalogue uses, ADR-0020:
    #    quadrants live within each pack, with the cross-cutting writing-rule
    #    READMEs in _shared/).
    diataxis_dirs = ("tutorials", "how-to", "reference", "explanation")
    missing = [
        d
        for d in diataxis_dirs
        if not Path(f"guides/{d}").is_dir()
        and not Path(f"guides/_shared/{d}").is_dir()
    ]
    if missing:
        note(
            f"guides/ is missing Diátaxis subdirectories: {' '.join(missing)}. "
            f"See guides/README.md."
        )
    else:
        # Coarse scaffold check only: it confirms each quadrant name resolves to
        # a directory (top-level, or under _shared/ in the per-pack layout). It
        # does not validate that every per-pack guide home is well-formed —
        # cross-link resolution and the per-pack READMEs cover that.
        ok("guides/ exposes the four Diátaxis quadrants (top-level or _shared/ scaffold).")

    # 9. Stale living-doc check (warn-only)
    living_docs = (
        "docs/CHARTER.md",
        "ARCHITECTURE.md",
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

    # 10a — Phase-1 retry caps live in state.json template, not prose.
    drift_check(
        r'"max_implementation_retries":\s*[0-9]+',
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
    contract_path = Path("contracts/adapter.toml")
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
    #
    # One batched `check-ignore` for all three probes, not one per probe. Note
    # this check's assertion is *inverted* relative to the pack-boundary lint:
    # there, an ignored path is skipped; here, a probe that is NOT ignored is the
    # finding. That makes an unresolved ignore layer actively misleading — a
    # naive fail-open would report `.gitignore` drift when the truth is that git
    # never answered, sending the operator to fix a file that is fine. So a
    # degraded or refused resolution is reported as what it is.
    probes = (
        "docs/specs/example/state.json",
        "docs/specs/example/notes/implementer-T1-0.md",
        ".worktrees/T1/README.md",
    )
    try:
        resolution = lint_git_ignore.git_ignored_paths(
            repo_root,
            [Path(probe) for probe in probes],
            missing_git_policy=lint_git_ignore.MissingGitPolicy.FAIL_OPEN,
            timeout=30.0,
        )
    except lint_git_ignore.GitIgnoreError as exc:
        # Git RAN and exited outside {0, 1} — a nested repository root, or a probe
        # beyond a symlink. "Re-run where git works" is the wrong remedy: git works
        # fine, and the same run will fail the same way anywhere.
        note(
            f"drift-watch: git rejected the probe batch, so the session-scratch "
            f"gitignore probes could not be resolved ({exc}). This is not a "
            f".gitignore finding — one probe path was unusable."
        )
    except ValueError as exc:
        # The resolver refused before launching git: a probe outside the repository
        # root, or one carrying a leading `:` git would read as pathspec magic.
        note(
            f"drift-watch: a probe was refused before git was called, so the "
            f"session-scratch gitignore probes could not be resolved ({exc}). This "
            f"is not a .gitignore finding — the path is outside the repository root "
            f"or carries a leading `:`."
        )
    else:
        if resolution.degraded:
            note(
                f"drift-watch: git is unavailable, so the session-scratch "
                f"gitignore probes could not be resolved "
                f"({resolution.detail}). This is not a .gitignore finding — "
                f"re-run where git works."
            )
        else:
            ignored = set(resolution.ignored)
            for probe in probes:
                if Path(probe) not in ignored:
                    note(
                        f"drift-watch: '{probe}' should be gitignored "
                        f"(session-scratch — see "
                        f".claude/skills/work-loop/references/state-schema.md, "
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
    rt_source = "packs/core/.apm/skills/work-loop/SKILL.md"
    rt_files = (rt_source, rt_canonical, ".agents/skills/work-loop/SKILL.md")
    rt_blocks = {}
    source_marker_counts = (0, 0)
    for f in Path().rglob("*.md"):
        if _is_vendored(f) or _is_fixture(f) or _is_frozen_record(f):
            continue
        f_str = f.as_posix()
        if f_str not in rt_files and rt_start in f.read_text(encoding="utf-8"):
            note(
                f"risk-trigger-block drift: {f_str} carries risk triggers; "
                f"workflow detail belongs in {rt_source}."
            )
    for f_str in rt_files:
        f = Path(f_str)
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        if f_str == rt_source:
            source_marker_counts = (text.count(rt_start), text.count(rt_end))
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
    if rt_source not in rt_blocks:
        note(
            f"risk-trigger-block drift: {rt_source} must carry one complete "
            "risk-trigger block; workflow detail belongs in the work-loop skill."
        )
    elif source_marker_counts != (1, 1):
        note(
            f"risk-trigger-block drift: {rt_source} must carry exactly one "
            "complete risk-trigger block; workflow detail belongs in the work-loop skill."
        )
    if len(rt_blocks) >= 2 and len(set(rt_blocks.values())) > 1:
        ref = rt_blocks.get(rt_source)
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
                f"canonical block in {rt_source}. The "
                        f"`risk-triggers:start`..`:end` span must be "
                        f"byte-identical across all copies "
                        f"(work-loop-light-mode spec AC2)."
                    )

    # 10h — scaffolded instruction sources must be byte-identical to projections.
    for source, projection in (
        (
            "packs/AGENTS.md",
            "packages/agentbundle/agentbundle/_data/catalogue-scaffold/packs/AGENTS.md",
        ),
        (
            "profiles/AGENTS.md",
            "packages/agentbundle/agentbundle/_data/catalogue-scaffold/profiles/AGENTS.md",
        ),
    ):
        if (
            Path(source).is_file()
            and Path(projection).is_file()
            and Path(source).read_bytes() != Path(projection).read_bytes()
        ):
            note(
                f"scaffold drift: {projection} differs from {source}; run "
                "python3 tools/catalogue/sync_authoring_scaffold.py --write."
            )

    # 10i — exact parent/child repeats belong only in the parent.
    for child in active_agents:
        if (
            child in (agents_md, Path("AGENTS.local.md"))
            or _is_seed(child)
            or _is_fixture(child)
            or _is_vendored(child)
        ):
            continue
        parent = child.parent.parent
        ancestor = None
        while True:
            probe = parent / "AGENTS.md"
            if probe.is_file():
                ancestor = probe
                break
            if parent == Path() or parent == parent.parent:
                break
            parent = parent.parent
        if ancestor is None:
            continue
        child_lines = [
            line.rstrip()
            for line in child.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        parent_lines = [
            line.rstrip()
            for line in ancestor.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for start in range(len(child_lines) - 2):
            for end in range(start + 3, len(child_lines) + 1):
                run = child_lines[start:end]
                if sum(map(len, run)) >= 80 and any(
                    parent_lines[i : i + len(run)] == run
                    for i in range(len(parent_lines) - len(run) + 1)
                ):
                    note(
                        "duplication: delete the child copy — the parent already "
                        f"states it ({child} / {ancestor}): {run[0]}"
                    )
                    break
            else:
                continue
            break

    # 10j — shipped seeds name portable primitives, never one adapter's path.
    adapter_roots: set[str] = set()
    if contract_path.is_file():
        contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))
        for adapter in contract.get("adapter", {}).values():
            for projection in adapter.get("projection", []):
                target_path = projection.get("target-path", "")
                if target_path.startswith("."):
                    adapter_roots.add(target_path.split("/", 1)[0])
    vendor_path = re.compile(
        rf"(?:{'|'.join(re.escape(root) for root in sorted(adapter_roots))})/"
    )
    for seed_file in Path("packs").glob("*/seeds/**/*"):
        name = seed_file.as_posix()
        if (
            not seed_file.is_file()
            or seed_file.name == ".gitignore"
            or name in _SEED_VENDOR_ROOT_BACKLOG
        ):
            continue
        if vendor_path.search(seed_file.read_text(encoding="utf-8", errors="replace")):
            note(
                f"seed vendor path: {name}; name the skill instead of its adapter path; "
                "contracts/adapter.toml projects this primitive into seven different roots."
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
