"""Self-host build mode — `make build-self` and `make build-check`.

Real-write (`make build-self`, no `DRY_RUN=1`) projects adapters
**directly into the working tree**, so the adapters' merge / splice
logic operates against the working tree's existing content — that's
what makes `merge-managed-key-only` (Claude Code) and
`preserve-outside-block` (Codex) correct against the adopter's actual
files.

Dry-run (`make build-self DRY_RUN=1`, and `make build-check`) clones
the adapter target subtree (`.claude/`, `tools/hooks/`, `.github/`,
`AGENTS.md`) into a fresh temp dir first, projects into the clone,
then diffs the clone against the working tree. The clone-then-project
pattern keeps the existing-content merge semantics intact under
dry-run too.

Marker resolution (`<adapt:NAME>` → discovery value) is the ONE place
install-time substitution happens — every other build mode copies
markers through unchanged (spec § Boundaries — Never do). The
`.adapt-discovery.toml` *materialisation* lives in the
`adapt-to-project` skill, out of scope here. T7 ships only the
consumer.

Self-host scope (see docs/specs/self-hosting/spec.md § Phased rollout):
the `SELF_HOST_ADAPTERS` allow-list runs `claude-code` and `codex`.
Kiro and Copilot stay distribution-only so self-host does not project
`.kiro/` or `.github/instructions/`.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS, codex
from agentbundle.build.contract import load as load_contract
from agentbundle.build.main import (
    CONTRACT_PATH,
    discover_packs,
    validate_pack_uniqueness,
)

# AC14: canonical lowercase-hyphen marker grammar. The self-host
# regex narrows from the prior wide `[A-Za-z0-9_-]+` form to match
# what the adapt-to-project skill writes. Legacy UPPER_SNAKE markers
# are tolerated with a one-shot warning per file (see `resolve_markers`).
ADAPT_MARKER_RE = re.compile(r"<adapt:([a-z][a-z0-9-]*)>")
_LEGACY_UPPER_RE = re.compile(r"<adapt:([A-Z_][A-Z0-9_]*)>")

# The adapter-target subtree — paths every adapter could touch. Used
# to clone working-tree state into a dry-run shadow.
TARGET_PATHS = (
    Path(".claude"),
    Path("tools") / "hooks",
    Path(".github") / "instructions",
    Path("AGENTS.md"),
)

# Self-host allow-list (see self-hosting spec § Phased rollout).
# Kiro and Copilot remain in the contract for distribution builds but
# are excluded from the self-host runner.
SELF_HOST_ADAPTERS: tuple[str, ...] = ("claude-code", "codex")


def is_dirty_tree(working_tree: Path) -> bool:
    """Return True if `git status --porcelain` against working_tree is non-empty.

    Fail-closed semantics — if git is missing, the directory isn't a
    git repo, or the call fails for any reason, return True so the
    destructive `--self` write still requires `--force`. The operator
    who knows the directory is safe can always pass `--force`; the
    operator who doesn't know what's there is protected.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=working_tree,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(
            f"self-host: warning — `git` binary not on PATH; treating "
            f"{working_tree} as dirty.",
            file=sys.stderr,
        )
        return True
    if result.returncode != 0:
        print(
            f"self-host: warning — `git status` failed in {working_tree} "
            f"(exit {result.returncode}); treating as dirty.",
            file=sys.stderr,
        )
        return True
    return bool(result.stdout.strip())


def resolve_markers(
    root: Path,
    discovery: dict[str, str],
    extra_paths: list[Path] | None = None,
) -> int:
    """Walk the bundle-owned subtree under `root` and substitute
    `<adapt:NAME>` markers.

    Scope is `TARGET_PATHS` (the adapter-target subtree) plus any
    `extra_paths` the caller passes — typically the seed-projected
    paths and the aggregated marketplace path. This avoids silently
    rewriting adopter-private files outside the bundle's owned region
    while still covering Phase-1's widened projection.
    """
    modified = 0
    candidates: list[Path] = []
    scope = list(TARGET_PATHS)
    if extra_paths:
        scope.extend(extra_paths)
    for relative in scope:
        target = root / relative
        if target.is_file():
            candidates.append(target)
        elif target.is_dir():
            candidates.extend(p for p in target.rglob("*") if p.is_file())
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "<adapt:" not in text:
            continue
        # AC14: legacy UPPER_SNAKE markers emit a single per-file warning
        # and are left in place (the narrowed regex below won't match
        # them; the warning surfaces them for the adopter to migrate).
        if _LEGACY_UPPER_RE.search(text):
            try:
                rel_label = path.relative_to(root)
            except ValueError:
                rel_label = path
            print(
                f"self-host: warning: legacy UPPER_SNAKE marker(s) in {rel_label}; "
                f"left in place (canonical form is <adapt:[a-z][a-z0-9-]*>)",
                file=sys.stderr,
            )
        replaced = ADAPT_MARKER_RE.sub(
            lambda match: discovery.get(match.group(1), match.group(0)),
            text,
        )
        if replaced != text:
            path.write_text(replaced, encoding="utf-8")
            modified += 1
    return modified


def _clone_target_subtree(working_tree: Path, destination: Path) -> None:
    """Copy adapter-target paths from working_tree into destination."""
    for relative in TARGET_PATHS:
        source = working_tree / relative
        if not source.exists():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def _project_all_adapters(
    output_root: Path,
    packs_dir: Path,
    contract: dict,
) -> None:
    """Run direct self-host adapter projections against every discovered pack."""
    packs = discover_packs(packs_dir)
    for pack in packs:
        validate_pack_uniqueness(pack)
    for adapter_name, project in ADAPTERS.items():
        if adapter_name not in contract["adapter"]:
            continue
        if adapter_name not in SELF_HOST_ADAPTERS:
            continue
        if adapter_name == "codex":
            # Codex writes into composed AGENTS.md; _compose_agents_md owns
            # that one-shot aggregate splice after the body seed is written.
            continue
        for pack in packs:
            project(pack.path, contract, output_root)


def _compose_agents_md(
    packs_dir: Path,
    output_root: Path,
    contract: dict,
) -> Path | None:
    """Compose root AGENTS.md from the core body seed, Codex skill block,
    and optional core footer fragment."""
    body_path = packs_dir / "core" / "seeds" / "AGENTS.md"
    if not body_path.exists():
        return None
    footer_path = packs_dir / "core" / "seeds" / "_agents-footer.md"
    target_path = output_root / "AGENTS.md"

    body = body_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if body and not body.endswith("\n"):
        body += "\n"
    target_path.write_text(body, encoding="utf-8")

    packs = discover_packs(packs_dir)
    codex.project_packs([pack.path for pack in packs], contract, output_root)

    if footer_path.exists():
        text = target_path.read_text(encoding="utf-8")
        footer = footer_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if text and not text.endswith("\n"):
            text += "\n"
        if footer and not footer.endswith("\n"):
            footer += "\n"
        target_path.write_text(text + footer, encoding="utf-8")
    return target_path


# ---------------------------------------------------------------------------
# Self-host follow-up additions (per docs/specs/self-hosting/spec.md):
# seed projection, marketplace aggregation, CLAUDE.md symlink recreation,
# missing-discovery fail-fast, drift source-naming, info-line emission.
# Comparison-rule strengthening (LF norm / mode bits / lstat) remains open.
# ---------------------------------------------------------------------------

# Excluded path patterns per RFC-0002 § What stays out. Phase-1
# implementation uses glob patterns matched against POSIX-style
# relative paths. `*` matches one path segment; `**` matches zero or
# more segments (including empty). Patterns *without* `/` (e.g.
# `README.md`) are anchored to the repo root — they do NOT match the
# same filename nested under subdirectories. Reviewers: extend this
# constant when an RFC authorises a new excluded class.
EXCLUDED_PATTERNS: tuple[str, ...] = (
    ".context/**",
    ".claude/settings.local.json",
    "docs/rfc/[0-9][0-9][0-9][0-9]-*.md",
    "docs/adr/[0-9][0-9][0-9][0-9]-*.md",
    "docs/specs/*/spec.md",
    "docs/specs/*/plan.md",
    "docs/specs/*/state.json",
    "docs/specs/*/notes/**",
    "docs/contracts/**",
    "docs/architecture/*.md",
    "docs/product/*.md",
    "docs/knowledge/*.md",
    "docs/guides/**/*.md",
    "README.md",  # root-level; nested README.md not excluded
    "LICENSE-*",
    ".gitignore",
    ".github/**",
    "AGENTS.local.md",
    "AGENTS.md",  # root-level; nested AGENTS.md not excluded
    ".kiro/**",
    "packages/agentbundle/**",
    "packs/**",
    "tools/**",
    ".adapt-discovery.toml",
    "Makefile",
    "dist/**",
    ".worktrees/**",
    "*.upstream.*",  # adopter-local upstream stash sidecars
)


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate an excluded-pattern glob into an anchored regex.

    `*` → one path segment (no slash); `**` → zero or more segments
    (including empty); `**/` → zero or more leading segments.
    Anchored to start and end so root-only patterns like `README.md`
    don't match nested files of the same name.
    """
    # Tokenise on `**` first so `*` doesn't grab `**` greedily.
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        elif pattern[i] == "[":
            # Pass character class through as-is, find closing ']'
            end = pattern.find("]", i + 1)
            if end == -1:
                out.append(re.escape(pattern[i]))
                i += 1
            else:
                out.append(pattern[i : end + 1])
                i = end + 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile(r"\A" + "".join(out) + r"\Z")


_EXCLUDED_REGEXES: tuple[re.Pattern[str], ...] = tuple(
    _glob_to_regex(p) for p in EXCLUDED_PATTERNS
)

# Hardcoded "Projected README" allow-list — paths classified as
# *Projected* even when EXCLUDED_PATTERNS would otherwise catch them.
# These are the seed READMEs RFC-0002 names explicitly. Phase 1 honours
# them via seed projection; without this allow-list the docs/**/*.md
# excluded patterns would mask them.
PROJECTED_README_OVERRIDES: tuple[str, ...] = (
    "docs/architecture/README.md",
    "docs/architecture/overview.md",
    "docs/product/README.md",
    "docs/product/roadmap.md",
    "docs/product/changelog.md",
    "docs/knowledge/README.md",
    "docs/knowledge/patterns.jsonl",
    "docs/guides/README.md",
    "docs/guides/tutorials/README.md",
    "docs/guides/how-to/README.md",
    "docs/guides/reference/README.md",
    "docs/guides/explanation/README.md",
    "docs/rfc/README.md",
    "docs/adr/README.md",
    "docs/specs/README.md",
    "docs/CHARTER.md",
    "docs/CONVENTIONS.md",
    "packages/README.md",
    "packages/_example/README.md",
    "packages/_example/AGENTS.md",
)


def _is_excluded(relative: Path) -> bool:
    """Return True if `relative` matches any EXCLUDED_PATTERNS entry, after
    honouring PROJECTED_README_OVERRIDES (a path appearing there is
    Projected even if an excluded pattern would also catch it)."""
    posix = relative.as_posix()
    if posix in PROJECTED_README_OVERRIDES:
        return False
    for regex in _EXCLUDED_REGEXES:
        if regex.match(posix):
            return True
    return False


def _project_seeds(packs_dir: Path, output_root: Path) -> dict[Path, Path]:
    """Copy `packs/<pack>/seeds/**` into `output_root` at seed-relative paths.

    Two packs may contribute to the same directory (historical canonical
    case: `docs/_templates/` — retired 2026-05-24 when each template
    moved into its owning skill's `assets/` folder; the merge rule still
    holds in principle for any future shared seed directory). File-level
    collisions (same target path, *different* content) raise `ValueError`
    naming both source paths — per spec § *Ask first* and AC7.

    Returns a `{relative_target → source}` map for use by the drift
    source-naming logic.
    """
    # Two-pass design (per spec § Always do): build the full
    # {relative → source} map and detect collisions *before* writing
    # anything, so a collision-mid-real-write doesn't leave a partial
    # projection on disk.
    seen: dict[Path, Path] = {}
    for pack_path in sorted(packs_dir.iterdir()):
        if not pack_path.is_dir() or not (pack_path / "pack.toml").exists():
            continue
        seeds_dir = pack_path / "seeds"
        if not seeds_dir.is_dir():
            continue
        for src in sorted(seeds_dir.rglob("*")):
            if not src.is_file():
                continue
            # Underscore-prefixed files are *composition fragments*
            # (e.g. `_agents-footer.md`), not standalone projection
            # targets. They live in seeds so adopters can edit them;
            # the Phase-2 composite-agents-md recipe consumes them
            # by reading `packs/core/seeds/_agents-footer.md`
            # directly. Skip standalone projection. Convention
            # documented in docs/CONVENTIONS.md § Pack source-of-truth
            # split.
            if src.name.startswith("_"):
                continue
            relative = src.relative_to(seeds_dir)
            if relative in seen:
                if src.read_bytes() != seen[relative].read_bytes():
                    raise ValueError(
                        f"seed collision at {relative.as_posix()}: "
                        f"{seen[relative]} and {src} differ — rename or "
                        f"consolidate one of them."
                    )
                continue
            seen[relative] = src
    # Second pass: collisions are clean, now write.
    for relative, src in seen.items():
        target = output_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target, follow_symlinks=False)
    return seen


def _aggregate_marketplace(
    packs_dir: Path,
    output_root: Path,
    owner: str = "eugenelim",
) -> Path:
    """Aggregate `packs/*/.claude-plugin/plugin.json` into
    `output_root/.claude-plugin/marketplace.json` so this repo is itself
    a usable marketplace at HEAD. `owner` defaults to this repo's
    concrete value but `run_self_host` overrides it from
    `.adapt-discovery.toml[adapt].owner` so adopters get their own."""
    entries: list[dict] = []
    for pack_path in sorted(packs_dir.iterdir()):
        if not pack_path.is_dir() or not (pack_path / "pack.toml").exists():
            continue
        manifest = pack_path / ".claude-plugin" / "plugin.json"
        if manifest.exists():
            entries.append(json.loads(manifest.read_text(encoding="utf-8")))
    target = output_root / ".claude-plugin" / "marketplace.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "owner": {"name": owner},
        "plugins": entries,
    }
    target.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target


def _is_windows() -> bool:
    """Detect native Windows. Both checks point at the same OS; using
    either alone is enough but checking both is robust against a future
    embedded build that fakes one without the other."""
    return sys.platform == "win32" or os.name == "nt"


def _recreate_claude_symlink(output_root: Path, *, force_copy: bool = False) -> Path:
    """Ensure `output_root/CLAUDE.md` mirrors `AGENTS.md`.

    On macOS / Linux (default) the mirror is a relative symlink to
    `AGENTS.md`, idempotent — leaves a correctly-pointing symlink alone.

    On native Windows, or when `force_copy=True` (set by the CLI's
    `--no-symlink` flag), the mirror is a regular file copy of
    `AGENTS.md`. Symlink creation on Windows requires Developer Mode or
    admin privileges; the copy path is the portable fallback. Emits a
    one-line stderr warning when the fallback fires so the operator
    knows the resulting CLAUDE.md is a copy, not a link, and must be
    regenerated when AGENTS.md changes.
    """
    claude = output_root / "CLAUDE.md"
    desired_target = "AGENTS.md"
    source = output_root / desired_target
    use_copy = force_copy or _is_windows()

    if use_copy:
        if not source.exists():
            # The POSIX symlink branch would create a dangling link
            # here (and some test fixtures rely on that); on Windows
            # the closest semantic equivalent is "no CLAUDE.md at
            # all" because we can't fabricate a copy of a missing
            # source. Log the divergence and return without writing.
            print(
                f"self-host: skipping CLAUDE.md copy — source {source} "
                f"missing; on POSIX a dangling symlink would have been "
                f"created instead.",
                file=sys.stderr,
            )
            return claude
        source_bytes = source.read_bytes()
        if (
            claude.is_file()
            and not claude.is_symlink()
            and claude.read_bytes() == source_bytes
        ):
            return claude
        if claude.is_symlink() or claude.exists():
            claude.unlink()
        claude.write_bytes(source_bytes)
        reason = "--no-symlink" if force_copy else "Windows host"
        print(
            f"self-host: CLAUDE.md written as a copy of AGENTS.md ({reason}); "
            f"regenerate after AGENTS.md changes.",
            file=sys.stderr,
        )
        return claude

    if claude.is_symlink():
        try:
            if os.readlink(claude) == desired_target:
                return claude
        except OSError:
            pass
        claude.unlink()
    elif claude.exists():
        # Regular file at CLAUDE.md — replace with symlink per spec.
        claude.unlink()
    claude.symlink_to(desired_target)
    return claude


def _build_projected_to_source_map(
    packs_dir: Path,
    contract: dict,
) -> dict[Path, Path]:
    """Build `{projected_relative_path → source_path}` for Phase-1
    self-host output. Used by `diff_against_working_tree` to name the
    source path + regeneration command in drift messages."""
    mapping: dict[Path, Path] = {}
    if "primitive" not in contract or "adapter" not in contract:
        return mapping
    for pack_path in sorted(packs_dir.iterdir()):
        if not pack_path.is_dir() or not (pack_path / "pack.toml").exists():
            continue
        for adapter_name in SELF_HOST_ADAPTERS:
            if adapter_name not in contract["adapter"]:
                continue
            for rule in contract["adapter"][adapter_name].get("projection", []):
                primitive_name = rule["primitive"]
                mode = rule["mode"]
                if mode in ("dropped", "degraded-info-log"):
                    continue
                primitive = contract["primitive"].get(primitive_name, {})
                source_path = primitive.get("source-path", "").rstrip("/")
                if not source_path:
                    continue
                source_dir = pack_path / source_path
                if not source_dir.exists():
                    continue
                target_prefix = Path(rule["target-path"].rstrip("/"))
                if mode == "direct-directory":
                    for entry in source_dir.iterdir():
                        if entry.is_dir():
                            mapping[target_prefix / entry.name] = entry
                elif mode == "direct-file":
                    for entry in source_dir.iterdir():
                        if entry.is_file():
                            mapping[target_prefix / entry.name] = entry
                elif mode in ("merge-json", "managed-block-inline"):
                    mapping.setdefault(
                        Path(rule["target-path"].lstrip("/")),
                        source_dir,
                    )
        # Seeds
        seeds_dir = pack_path / "seeds"
        if seeds_dir.is_dir():
            for entry in seeds_dir.rglob("*"):
                if entry.is_file():
                    mapping.setdefault(entry.relative_to(seeds_dir), entry)
    return mapping


def _lookup_source(
    projected_rel: Path,
    mapping: dict[Path, Path],
) -> Path | None:
    """Find the source path for a projected relative path. Walks up the
    projected path looking for a directory-level match and appends the
    remainder (e.g. `.claude/skills/work-loop/SKILL.md` →
    `packs/core/.apm/skills/work-loop/SKILL.md`)."""
    if projected_rel in mapping:
        return mapping[projected_rel]
    for ancestor in projected_rel.parents:
        if ancestor == Path("."):
            continue
        if ancestor in mapping:
            anchor = mapping[ancestor]
            if anchor.is_dir():
                try:
                    remainder = projected_rel.relative_to(ancestor)
                except ValueError:
                    continue
                return anchor / remainder
    return None


def _emit_info_for_unclassified(
    working_tree: Path,
    projected_paths: set[Path],
) -> None:
    """Walk `git ls-files --cached --others --exclude-standard` and emit
    `[info]` lines for paths that are neither Projected nor Excluded.

    Info-level — does not fail the build. Surfaces omissions so the
    next PR can classify them (per spec § *Always do*). If the working
    tree is not a git repo or git is unavailable, emits a single
    warning rather than silently skipping classification — an operator
    seeing "zero info lines" should not mis-attribute it to "fully
    classified."
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=working_tree,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print(
            "self-host: warning — `git` binary not on PATH; "
            "skipping unclassified-path enumeration.",
            file=sys.stderr,
        )
        return
    if result.returncode != 0:
        print(
            f"self-host: warning — `git ls-files` failed in "
            f"{working_tree} (exit {result.returncode}); skipping "
            "unclassified-path enumeration.",
            file=sys.stderr,
        )
        return
    for line in result.stdout.splitlines():
        path_str = line.strip()
        if not path_str:
            continue
        relative = Path(path_str)
        if relative in projected_paths:
            continue
        if _is_excluded(relative):
            continue
        on_disk = working_tree / relative
        if on_disk.is_symlink():
            # CLAUDE.md (projected as symlink) and any other symlinks are
            # implicitly classified — symlink target comparison is Phase 2.
            continue
        print(f"[info] unclassified: {relative.as_posix()}", file=sys.stderr)


def _is_text_like(data: bytes) -> bool:
    """A file that decodes as UTF-8 is text-like for LF normalisation.

    Empty files are text. Anything that fails UTF-8 decode is binary —
    binaries that happen to contain a 0x0D 0x0A byte pair must not be
    normalised, since the bytes carry value beyond line termination.
    """
    if not data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _normalise_lf(data: bytes) -> bytes:
    """Replace CRLF with LF for text-like equality comparison.

    Bare CR is left in place — it's neither a portable line terminator
    nor a `core.autocrlf` artefact, and rewriting it would hide real
    content drift in test fixtures that exercise mac-classic endings.
    """
    return data.replace(b"\r\n", b"\n")


def diff_against_working_tree(
    shadow: Path,
    working_tree: Path,
    source_map: dict[Path, Path] | None = None,
) -> list[str]:
    """Compare every file in `shadow` against the corresponding path in
    `working_tree`. When `source_map` is provided, drift messages name
    the source path and regeneration command per spec § *Always do*
    (`[drift] <projected>: edit <source>; run: make build-self`).

    Phase-2 strengthening per the self-hosting spec:

    - **CRLF→LF normalisation** for text-like files (those that decode
      as UTF-8). Binary content is compared byte-for-byte. A CRLF-on-
      disk text file no longer drifts against an LF-in-source file
      — the same content shape ``git status`` already accommodates via
      ``core.autocrlf``.
    - **File-mode permission bits** for regular files. A projected
      ``0o644`` against an on-disk ``0o755`` drifts. Only the low 9
      permission bits are compared; setuid/setgid/sticky are not part
      of the projection contract.
    - **Symlink targets via ``lstat``** — the gate never follows a
      symlink. A symlink/regular type mismatch drifts; matching
      symlinks with different targets drift.
    """
    drifts: list[str] = []
    for rendered in shadow.rglob("*"):
        try:
            shadow_st = os.lstat(rendered)
        except OSError:
            continue
        if not (stat.S_ISREG(shadow_st.st_mode) or stat.S_ISLNK(shadow_st.st_mode)):
            continue
        relative = rendered.relative_to(shadow)
        on_disk = working_tree / relative
        hint = ""
        if source_map is not None:
            source = _lookup_source(relative, source_map)
            if source is not None:
                hint = (
                    f": edit {source.as_posix()}; run: make build-self"
                )

        try:
            disk_st = os.lstat(on_disk)
        except FileNotFoundError:
            drifts.append(
                f"[drift] {relative.as_posix()} (missing on disk){hint}"
            )
            continue
        except OSError as exc:
            drifts.append(
                f"[drift] {relative.as_posix()} (unreadable: {exc}){hint}"
            )
            continue

        shadow_is_link = stat.S_ISLNK(shadow_st.st_mode)
        disk_is_link = stat.S_ISLNK(disk_st.st_mode)

        if shadow_is_link != disk_is_link:
            expected = "symlink" if shadow_is_link else "regular file"
            found = "regular file" if shadow_is_link else "symlink"
            drifts.append(
                f"[drift] {relative.as_posix()} "
                f"(expected {expected}, found {found} on disk){hint}"
            )
            continue

        if shadow_is_link:
            try:
                shadow_target = os.readlink(rendered)
                disk_target = os.readlink(on_disk)
            except OSError as exc:
                drifts.append(
                    f"[drift] {relative.as_posix()} "
                    f"(unreadable symlink: {exc}){hint}"
                )
                continue
            if shadow_target != disk_target:
                drifts.append(
                    f"[drift] {relative.as_posix()} "
                    f"(symlink target differs: {disk_target!r} vs {shadow_target!r})"
                    f"{hint}"
                )
            continue

        reasons: list[str] = []

        shadow_mode = stat.S_IMODE(shadow_st.st_mode)
        disk_mode = stat.S_IMODE(disk_st.st_mode)
        if shadow_mode != disk_mode:
            reasons.append(f"mode {oct(disk_mode)} vs {oct(shadow_mode)}")

        try:
            shadow_bytes = rendered.read_bytes()
            disk_bytes = on_disk.read_bytes()
        except OSError as exc:
            drifts.append(
                f"[drift] {relative.as_posix()} (unreadable: {exc}){hint}"
            )
            continue

        if shadow_bytes != disk_bytes:
            if _is_text_like(shadow_bytes) and _is_text_like(disk_bytes):
                if _normalise_lf(shadow_bytes) != _normalise_lf(disk_bytes):
                    reasons.append("content differs")
            else:
                reasons.append("content differs")

        if reasons:
            tag = " (" + "; ".join(reasons) + ")"
            drifts.append(f"[drift] {relative.as_posix()}{tag}{hint}")
    return drifts


def run_self_host(
    working_tree: Path,
    packs_dir: Path,
    dry_run: bool,
    force: bool,
    contract: dict | None = None,
    no_symlink: bool = False,
) -> int:
    """Execute `make build-self` (or `make build-self DRY_RUN=1`).

    Phase-1 orchestration: dirty-tree refusal → fail-fast on missing
    `.adapt-discovery.toml` → adapter projection (allow-listed) → seed
    projection → marketplace aggregation → CLAUDE.md symlink → marker
    resolution. Under `dry_run`, all writes happen in a shadow temp
    dir and the result is diffed against the working tree.
    """
    if contract is None:
        contract = load_contract(CONTRACT_PATH)

    if not dry_run and is_dirty_tree(working_tree) and not force:
        print(
            "self-host: working tree is dirty — refusing to write. "
            "Pass --force to override (the dirty-tree check only).",
            file=sys.stderr,
        )
        return 2

    # AC14: fail-fast when .adapt-discovery.toml is missing. The file is
    # required by `make build-self` even when no source carries
    # `<adapt:NAME>` markers today — the contract is "if you run
    # build-self, you affirm the discovery values exist."
    discovery_path = working_tree / ".adapt-discovery.toml"
    if not discovery_path.exists():
        print(
            "missing .adapt-discovery.toml required by --self",
            file=sys.stderr,
        )
        return 3

    # AC9: read `.adapt-discovery.toml` via the typed loader. Legacy
    # `[adapt]` table, unknown `discovery-schema-version`, and any
    # other invalid shape surface as `ConfigError` and refuse with
    # the `self-host: ` prefix per spec.
    from agentbundle.config import ConfigError, load_adapt_discovery_typed

    try:
        discovery = load_adapt_discovery_typed(discovery_path, scope="repo")
    except ConfigError as exc:
        print(f"self-host: {exc}", file=sys.stderr)
        return 3
    discovery_flat = dict(discovery.markers)
    owner = discovery_flat.get("owner", "eugenelim")

    if dry_run:
        with tempfile.TemporaryDirectory(prefix="agentbundle-shadow-") as shadow_str:
            shadow = Path(shadow_str)
            _clone_target_subtree(working_tree, shadow)
            _project_all_adapters(shadow, packs_dir, contract)
            try:
                seed_map = _project_seeds(packs_dir, shadow)
            except ValueError as exc:
                print(f"self-host: {exc}", file=sys.stderr)
                return 4
            agents_path = _compose_agents_md(packs_dir, shadow, contract)
            _aggregate_marketplace(packs_dir, shadow, owner=owner)
            _recreate_claude_symlink(shadow, force_copy=no_symlink)
            extra_marker_paths = list(seed_map.keys()) + [
                Path(".claude-plugin") / "marketplace.json",
            ]
            if agents_path is not None:
                extra_marker_paths.append(Path("AGENTS.md"))
            resolve_markers(shadow, discovery_flat, extra_paths=extra_marker_paths)
            source_map = _build_projected_to_source_map(packs_dir, contract)
            projected_paths = {
                rendered.relative_to(shadow)
                for rendered in shadow.rglob("*")
                if rendered.is_file() or rendered.is_symlink()
            }
            drifts = diff_against_working_tree(shadow, working_tree, source_map)
            # AC6: info-level lines for unclassified paths.
            _emit_info_for_unclassified(working_tree, projected_paths)
            if drifts:
                print(
                    f"self-host: dry-run found {len(drifts)} drift(s):",
                    file=sys.stderr,
                )
                for drift in drifts:
                    print(f"  {drift}", file=sys.stderr)
                return 1
            return 0

    # Real write: project directly into the working tree so adapter
    # merge/splice logic sees existing content.
    _project_all_adapters(working_tree, packs_dir, contract)
    try:
        seed_map = _project_seeds(packs_dir, working_tree)
    except ValueError as exc:
        print(f"self-host: {exc}", file=sys.stderr)
        return 4
    agents_path = _compose_agents_md(packs_dir, working_tree, contract)
    _aggregate_marketplace(packs_dir, working_tree, owner=owner)
    _recreate_claude_symlink(working_tree, force_copy=no_symlink)
    extra_marker_paths = list(seed_map.keys()) + [
        Path(".claude-plugin") / "marketplace.json",
    ]
    if agents_path is not None:
        extra_marker_paths.append(Path("AGENTS.md"))
    resolve_markers(working_tree, discovery_flat, extra_paths=extra_marker_paths)
    return 0


def cmd_self(args) -> int:
    return run_self_host(
        working_tree=Path(args.output_dir).resolve(),
        packs_dir=Path(args.packs_dir).resolve(),
        dry_run=args.dry_run,
        force=args.force,
        no_symlink=getattr(args, "no_symlink", False),
    )


def cmd_check(args) -> int:
    """`make build-check` — strict dry-run against the working tree."""
    return run_self_host(
        working_tree=Path(args.output_dir).resolve(),
        packs_dir=Path(args.packs_dir).resolve(),
        dry_run=True,
        force=False,
        no_symlink=getattr(args, "no_symlink", False),
    )


# Re-export project_to_temp for any external caller that still relies
# on the older API (tests previously imported this helper). The new
# self-host implementation uses _project_all_adapters internally
# against the working tree (or a shadow clone of it).
def project_to_temp(working_tree: Path, packs_dir: Path, contract: dict) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="agentbundle-self-"))
    _clone_target_subtree(working_tree, temp_dir)
    _project_all_adapters(temp_dir, packs_dir, contract)
    return temp_dir
