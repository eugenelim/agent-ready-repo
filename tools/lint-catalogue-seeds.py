#!/usr/bin/env python3
"""Lint first-party pack seed files for the scaffold contract defined by RFC-0002 § Amendments § 2026-05-25.

Pack seeds under `packs/<pack>/seeds/` ship to adopters on first
install. After the 2026-05-25 amendment, most former Projected paths
are Manual at the projected path — the on-disk file is this repo's
living instance, while the pack-side seed must remain a placeholder
template adopters can fill in.

**Opt-in by construction (RFC-0047 Decision 6 / ADR-0037 D4).** This
lint enforces its contract *only* on packs whose `pack.toml` carries
`[pack].lint-seeds = true` — the four first-party scaffold packs
(`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`).
Every other pack — including any organization pack, which intentionally
ships *instance* content (the inverse of the placeholder contract) — omits
the flag and is unenforced **by construction**: no edit to this lint and no
central first-party pack list. The gate lives at one chokepoint
(`_enumerate_seed_files`), so all checks below are gated together.

This lint enforces two contracts on the packs that opt in:

  1. **Blocklist (negative check).** No catalogue-specific strings
     appear in any seed file: `agent-ready-repo`, `RFC-NNNN` refs to
     this catalogue's RFCs, `K-NNNN` knowledge entries, our specific
     pack and spec names. The blocklist is the safety net against the
     leak class that the amendment closed.

  2. **Per-file required placeholders (positive check).** A handful
     of seeds whose adopter-facing shape is structured (filled tables,
     scaffolded content) must carry an explicit placeholder marker
     that proves the seed is template, not instance. Hardcoded
     per-file expectations live in REQUIRED_PLACEHOLDERS below.

The lint honours a single-line sentinel for exempting individual
lines from the blocklist:

    <!-- seed-content-lint-ignore: <short-reason> -->

The sentinel applies to the next non-empty non-comment line. The
following shapes are errors:

  - **Stacked sentinels** (two back-to-back) — pick one.
  - **Trailing sentinel** (no following content line) — meaningless.
  - **Sentinel inside a fenced ``` block** — ignored (the lint tracks
    fence open/close state and does not honour sentinels inside).

Exit codes: 0 = pass, 1 = lint failures (one or more violations).
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tomllib
from typing import Iterable


# Strings that must not appear in any pack seed (unless sentinel-exempt).
# Sourced from RFC-0002 § Amendments § 2026-05-25.
BLOCKLIST_PATTERNS: tuple[tuple[str, str], ...] = (
    # (regex, human-readable name for error messages)
    (r"agent-ready-repo", "catalogue name 'agent-ready-repo'"),
    (r"RFC-00\d\d", "catalogue RFC reference (RFC-NNNN)"),
    (r"K-00\d\d", "catalogue knowledge entry (K-NNNN)"),
    (
        # Spec names that are internal-only governance (don't ship as
        # skills). Skill names that DO ship — adapt-to-project,
        # work-loop, new-spec, etc. — are intentionally not blocked
        # because adopters install them and may legitimately reference
        # them by name.
        r"\b("
        r"distribution-adapters|self-hosting|agent-spec-cli|"
        r"user-scope-hooks|converters-pack|"
        r"claude-plugins-install-route|codex-native-skills|"
        r"apm-install-route-parity|skill-secrets|wire-session-start-hook|"
        r"kiro-ide-hook|windows-ci-bundler|windows-hooks-phase3"
        r")\b",
        "catalogue spec name",
    ),
)
_BLOCKLIST_RE = [(re.compile(p), name) for p, name in BLOCKLIST_PATTERNS]


# Per-file required placeholders. The seed at `packs/<pack>/seeds/<rel>`
# must contain at least one of the listed substring(s); if none match,
# the seed has been filled in with instance content rather than scaffold.
#
# Keyed by seed-relative path (the path under `packs/<pack>/seeds/`).
# Maintenance contract: when a new seed is added under any pack, declare
# its placeholder expectations here. The lint fails-loud on unknown seed
# files (see check_seed_file).
REQUIRED_PLACEHOLDERS: dict[str, tuple[str, ...]] = {
    "docs/CHARTER.md": (
        "<replace with one sentence>",
        "<bullet>",
        "<principle>",
    ),
    "docs/architecture/overview.md": (
        "<list your packs and packages here>",
        "<app-name>",
        "<package-name>",
    ),
    "docs/specs/README.md": ("<!-- no specs yet -->",),
    "docs/knowledge/patterns.jsonl": (),  # empty file required; see check
    "docs/rfc/README.md": ("<!-- no RFCs yet -->",),
    "docs/adr/README.md": ("<!-- no ADRs yet -->",),
    # governance-extras governance-index template (RFC-0065 D16)
    "governance/manifest.example.yaml": ("ADR-NNNN",),
    # Generic seeds — no specific placeholder required; the blocklist
    # plus the empty-content-allowed default catch leaks.
    "docs/architecture/README.md": (),
    "docs/knowledge/README.md": (),
    "docs/product/README.md": (),
    "docs/product/roadmap.md": ("YYYY-MM-DD",),
    "docs/product/changelog.md": ("Unreleased",),
    "docs/product/briefs/_template.md": ("<slug>", "<one-line outcome>"),
    # product-engineering's intent + rollup templates moved from repo-scaffolding
    # seeds/ into the owning skills' assets/ (frame-intent, align-value-stream) so
    # the pack ships no seeds/ and stays user-scope (enriched-pack-manifest;
    # AGENTS.local.md skill-template convention). They are skill reference content
    # now, not adopter seeds, so they leave the seed registry.
    "workspace.toml": ("[backlog]",),
    "docs/CONVENTIONS.md": (),
    "AGENTS.md": ("<project-name>",),
    "docs/guides/README.md": (),
    "docs/guides/tutorials/README.md": (),
    "docs/guides/how-to/README.md": (),
    "docs/guides/reference/README.md": (),
    "docs/guides/explanation/README.md": (),
    "packages/README.md": (),
    "packages/_example/README.md": ("`_example`",),
    "packages/_example/AGENTS.md": ("placeholder package",),
    ".gitignore": (),
    "_agents-footer.md": (),  # composition fragment; not a standalone seed
}


SENTINEL_RE = re.compile(
    r"^\s*<!--\s*seed-content-lint-ignore:\s*([^>]+?)\s*-->\s*$"
)
FENCE_RE = re.compile(r"^\s*```")


def _repo_root() -> pathlib.Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return pathlib.Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return pathlib.Path(__file__).resolve().parent.parent


def _is_blank_or_comment(line: str) -> bool:
    s = line.strip()
    return not s or (s.startswith("<!--") and s.endswith("-->"))


def _pack_opts_in(pack_dir: pathlib.Path) -> bool:
    """Return True iff the pack's `pack.toml` carries `[pack].lint-seeds = true`.

    The flag is the single source of truth for which packs this lint enforces
    (RFC-0047 Decision 6 / ADR-0037 D4): only the first-party scaffold packs
    carry it, so an org pack that ships *instance* content is unenforced **by
    construction** — no edit to this lint and no central pack list. A pack with
    no `pack.toml`, an unreadable/malformed one, or the flag absent or not
    literally `true` is skipped. No hardcoded first-party list backs this.
    """
    manifest = pack_dir / "pack.toml"
    if not manifest.is_file():
        return False
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    pack_table = data.get("pack")
    if not isinstance(pack_table, dict):
        return False
    return pack_table.get("lint-seeds") is True


def _enumerate_seed_files(repo_root: pathlib.Path) -> Iterable[pathlib.Path]:
    """Yield every file under `packs/*/seeds/` for packs that opt in.

    Only packs whose `pack.toml` carries `[pack].lint-seeds = true` are
    enumerated (see `_pack_opts_in`); every other pack — including any org
    pack — is skipped, so all checks below are gated at this one chokepoint.
    """
    packs_root = repo_root / "packs"
    if not packs_root.is_dir():
        return
    for pack_dir in sorted(packs_root.iterdir()):
        if not _pack_opts_in(pack_dir):
            continue
        seeds_dir = pack_dir / "seeds"
        if not seeds_dir.is_dir():
            continue
        for path in sorted(seeds_dir.rglob("*")):
            if path.is_file():
                yield path


def check_seed_file(path: pathlib.Path, seeds_root: pathlib.Path) -> list[str]:
    """Return a list of violation strings (empty list = clean)."""
    violations: list[str] = []
    try:
        relative = path.relative_to(seeds_root).as_posix()
    except ValueError:
        return [f"{path}: not under a seeds_root"]

    # Per-file required placeholders — fail-loud on unknown seeds.
    if relative not in REQUIRED_PLACEHOLDERS:
        return [
            f"{path}: unknown seed file — declare its expected "
            "placeholder shape in tools/lint-catalogue-seeds.py:REQUIRED_PLACEHOLDERS, "
            "or remove the file. (Fail-loud policy: every seed under "
            "packs/<pack>/seeds/ must have a declared shape.)"
        ]

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Binary files (rare in seeds; .keep markers, etc.) — skip.
        return []

    # Special case: docs/knowledge/patterns.jsonl must be empty.
    if relative == "docs/knowledge/patterns.jsonl":
        if content.strip():
            violations.append(
                f"{path}:1: patterns.jsonl seed must be empty "
                "(adopters' knowledge entries accumulate post-install; "
                "see RFC-0002 amendment 2026-05-25)"
            )
        return violations

    # Required placeholder check.
    required = REQUIRED_PLACEHOLDERS[relative]
    if required and not any(token in content for token in required):
        violations.append(
            f"{path}: required placeholder missing — expected at least "
            f"one of: {', '.join(repr(t) for t in required)}. "
            "Seeds are scaffold; restore placeholder shape."
        )

    # Blocklist scan with sentinel handling.
    lines = content.splitlines()
    pending_sentinel = False
    pending_sentinel_lineno = 0
    pending_sentinel_reason = ""
    in_fence = False

    for lineno, raw_line in enumerate(lines, start=1):
        # Fence tracking — sentinels inside fenced blocks are ignored.
        if FENCE_RE.match(raw_line):
            in_fence = not in_fence
            # A pending sentinel just before a fence open targets the
            # fence opener line, which is meaningless code-fence
            # punctuation. Clear the pending sentinel.
            pending_sentinel = False
            continue

        if in_fence:
            # Skip blocklist scanning AND sentinel handling inside fences.
            continue

        sentinel_match = SENTINEL_RE.match(raw_line)
        if sentinel_match:
            if pending_sentinel:
                violations.append(
                    f"{path}:{lineno}: stacked sentinel (previous on "
                    f"line {pending_sentinel_lineno}; pick one)"
                )
                pending_sentinel = False  # consume both; treat as error
            else:
                pending_sentinel = True
                pending_sentinel_lineno = lineno
                pending_sentinel_reason = sentinel_match.group(1)
            continue

        # If a sentinel is pending and this line is blank/comment, the
        # sentinel waits for the next non-empty non-comment line per
        # the documented contract.
        if _is_blank_or_comment(raw_line):
            continue

        # This is a content line. Apply blocklist (unless exempt).
        if pending_sentinel:
            pending_sentinel = False
            # Skip blocklist scan; sentinel exempts this single line.
            continue

        for regex, name in _BLOCKLIST_RE:
            if regex.search(raw_line):
                violations.append(
                    f"{path}:{lineno}: contains {name} — pack seeds must "
                    "be placeholder shape (RFC-0002 amendment 2026-05-25). "
                    "Add a `<!-- seed-content-lint-ignore: <reason> -->` "
                    "sentinel immediately above the line if the catalogue "
                    "string is genuinely required."
                )

    # Trailing sentinel — sentinel was last and never got a content line.
    if pending_sentinel:
        violations.append(
            f"{path}:{pending_sentinel_lineno}: trailing sentinel "
            f"(reason={pending_sentinel_reason!r}) — no content line "
            "follows; remove the sentinel."
        )

    return violations


def main() -> int:
    repo_root = _repo_root()
    seeds_packs = repo_root / "packs"
    if not seeds_packs.is_dir():
        print(f"lint-catalogue-seeds: {seeds_packs} not a directory", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    seed_count = 0

    for path in _enumerate_seed_files(repo_root):
        # Derive the per-pack seeds root (packs/<pack>/seeds/).
        seeds_root = None
        for ancestor in path.parents:
            if ancestor.name == "seeds" and ancestor.parent.parent == seeds_packs:
                seeds_root = ancestor
                break
        if seeds_root is None:
            continue
        seed_count += 1
        all_violations.extend(check_seed_file(path, seeds_root))

    if all_violations:
        for v in all_violations:
            print(v, file=sys.stderr)
        print(
            f"\nlint-catalogue-seeds: {len(all_violations)} violation(s) "
            f"across {seed_count} seed file(s).",
            file=sys.stderr,
        )
        return 1

    print(f"lint-catalogue-seeds: {seed_count} seed file(s) clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
