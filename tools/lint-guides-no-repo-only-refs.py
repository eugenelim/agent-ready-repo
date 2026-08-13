#!/usr/bin/env python3
"""Reject repository-only governance references in shipped Markdown guides.

The scanner checks ``guides/**/*.md`` by default. Use ``--guides-root`` to
select another guide tree, including a fixture tree whose sibling
``docs/specs/`` directory supplies the real spec-slug set.

Rules:
  1. Markdown link targets must not contain an ``adr``, ``rfc``, or ``specs``
     path segment, or ``changelog`` anywhere in the path (case-insensitive).
  2. ``ADR-NN`` through ``ADR-NNNN`` and ``RFC-NN`` through ``RFC-NNNN``
     tokens are forbidden.
  3. ``spec/<slug>`` and ``docs/specs/<slug>`` references are forbidden when
     ``<slug>`` names a real directory below the runtime ``docs/specs/`` tree.
     Angle-bracket placeholders are excluded.

Rare legitimate exceptions may add
``<!-- guides-lint: allow <reason> -->`` on the violating line or immediately
above it. The reason is required and should explain why the shipped reference
is safe.

Known limitations — this is a regression fence, not a proof of absence:

  * Rule 3 cannot identify a citation to a pending spec whose directory does
    not exist yet. Human review must remove those; see
    ``docs/specs/governance-guides-cleanup/notes/scrub-judgment.md``.
  * Rule 3 is also allow-by-default in the other direction: an untouched guide
    starts failing the day someone creates a ``docs/specs/`` directory whose
    name collides with an invented tutorial slug.
  * Rule 1 sees inline and reference-style Markdown link targets. It does not
    see raw HTML anchors (``<a href=...>``), CommonMark autolinks, bare
    unlinked paths in prose or fenced blocks, or a reference definition whose
    target sits on the following line.
  * Rule 2 is case-sensitive by design, so lowercase ``rfc-0071`` passes.
  * Only the final component of ``--guides-root`` is checked for being a link.
    A symlinked ancestor is followed; resolved children are still confined to
    the selected root.

Exit codes:
  0  no violations
  1  one or more violations
  2  usage or filesystem error
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GUIDES_ROOT = REPO_ROOT / "guides"
OK_MESSAGE = "OK — no repo-only governance references in guides/"

ALLOW_RE = re.compile(r"<!--\s*guides-lint:\s*allow\s+.+?\s*-->")
GOVERNANCE_TOKEN_RE = re.compile(r"\b(?:ADR|RFC)-\d{2,4}\b")
SPEC_REFERENCE_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:docs/specs|spec)/(?P<slug>[A-Za-z0-9][A-Za-z0-9._-]*)"
)
MARKDOWN_LINK_RE = re.compile(
    r"!?\[[^\]\n]*\]\(\s*"
    r"(?P<target><[^>\n]+>|[^)\s]+)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
MARKDOWN_REFERENCE_DEFINITION_RE = re.compile(
    r"^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(?P<target><[^>\n]+>|\S+)"
)
EXTERNAL_URL_RE = re.compile(r"(?:[A-Za-z][A-Za-z0-9+.-]*:)?//")
# One-shot latch so the junction-unavailable warning is emitted once per run.
_JUNCTION_WARNED: list[bool] = []
GOVERNANCE_SEGMENTS = {"adr", "rfc", "specs"}


class LintUsageError(Exception):
    """A selected or discovered filesystem path cannot be scanned safely."""


@dataclass(frozen=True)
class Violation:
    """One actionable guide-lint diagnostic."""

    path: Path
    line: int
    reason: str


def _resolve(path: Path, label: str) -> Path:
    """Resolve ``path`` or raise a concise fail-closed usage error."""

    try:
        return path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise LintUsageError(f"cannot resolve {label}: {exc}") from exc


def _is_relative_to(path: Path, root: Path) -> bool:
    """Return whether ``path`` is confined to ``root``."""

    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _is_junction(path: Path) -> bool:
    """Detect Windows junctions, warning when the API is unavailable.

    `Path.is_junction` landed in Python 3.12 but this repository supports 3.11,
    so a plain `getattr` fallback of `False` turns every junction check into a
    silent no-op on the supported floor. Junctions only exist on Windows, so
    absence is safe on POSIX and warned about there.
    """

    checker = getattr(path, "is_junction", None)
    if checker is None:
        if os.name == "nt" and not _JUNCTION_WARNED:
            # Loud rather than fatal: refusing to run would make the tool
            # unusable on the supported floor, and resolved children are still
            # confined to the selected root, so an escape is still caught.
            print(
                "warning: this interpreter cannot detect Windows junctions "
                "(Path.is_junction requires Python 3.12) — junction checks are "
                "skipped; child paths remain confined to the selected root",
                file=sys.stderr,
            )
            _JUNCTION_WARNED.append(True)
        return False
    try:
        return bool(checker())
    except OSError as exc:
        raise LintUsageError(f"cannot inspect linked directory {path}: {exc}") from exc


def _runtime_roots(guides_argument: str) -> tuple[Path, Path, Path]:
    """Return confined repository, guides, and specs roots for this invocation."""

    guides_raw = Path(guides_argument).absolute()
    repo_root = _resolve(guides_raw.parent, "repository root")
    guides_root = _resolve(guides_raw, "guides root")
    if not _is_relative_to(guides_root, repo_root):
        raise LintUsageError(f"guides root resolves outside repository root: {guides_raw}")
    if guides_raw.is_symlink() or _is_junction(guides_raw):
        raise LintUsageError(f"linked guides root is not allowed: {guides_raw}")
    # Note: `is_symlink` inspects only the final component. A symlinked
    # *ancestor* of the selected root is followed. Requiring the argument to be
    # canonical would reject that, but also rejects ordinary paths on platforms
    # where a system directory is itself a link (macOS `/var`), so the
    # confinement that actually holds is of resolved children to the selected
    # root, below. See the module docstring's Known limitations.
    if not guides_root.is_dir():
        raise LintUsageError(f"guides root is not a directory: {guides_raw}")

    specs_raw = repo_root / "docs" / "specs"
    specs_root = _resolve(specs_raw, "specs root")
    if not _is_relative_to(specs_root, repo_root):
        raise LintUsageError(f"specs root resolves outside repository root: {specs_raw}")
    if specs_raw.is_symlink() or _is_junction(specs_raw):
        raise LintUsageError(f"linked specs root is not allowed: {specs_raw}")
    if not specs_root.is_dir():
        raise LintUsageError(f"specs root is not a directory: {specs_raw}")
    return repo_root, guides_root, specs_root


def _real_spec_slugs(specs_root: Path) -> set[str]:
    """Read real spec slugs from confined direct child directories."""

    slugs: set[str] = set()
    try:
        entries = sorted(os.scandir(specs_root), key=lambda entry: entry.name)
    except OSError as exc:
        raise LintUsageError(f"cannot read specs root {specs_root}: {exc}") from exc

    for entry in entries:
        path = Path(entry.path)
        try:
            is_link = entry.is_symlink()
            is_directory = entry.is_dir(follow_symlinks=True)
        except OSError as exc:
            raise LintUsageError(f"cannot inspect spec entry {path}: {exc}") from exc
        if not is_directory:
            continue
        resolved = _resolve(path, f"spec directory {path}")
        if not _is_relative_to(resolved, specs_root):
            raise LintUsageError(f"spec directory resolves outside the specs root: {path}")
        if is_link or _is_junction(path):
            raise LintUsageError(f"linked spec directory is not allowed: {path}")
        slugs.add(entry.name)
    return slugs


def _markdown_files(guides_root: Path) -> list[tuple[Path, Path]]:
    """Return display/resolved Markdown paths from a confined recursive walk."""

    files: list[tuple[Path, Path]] = []
    stack = [guides_root]
    visited: set[Path] = set()

    while stack:
        directory = stack.pop()
        resolved_directory = _resolve(directory, f"guide directory {directory}")
        if not _is_relative_to(resolved_directory, guides_root):
            raise LintUsageError(f"guide directory resolves outside the guides root: {directory}")
        if resolved_directory in visited:
            raise LintUsageError(f"guide directory cycle or alias detected: {directory}")
        visited.add(resolved_directory)

        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise LintUsageError(f"cannot read guide directory {directory}: {exc}") from exc

        child_directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            try:
                is_link = entry.is_symlink()
            except OSError as exc:
                raise LintUsageError(f"cannot inspect guide entry {path}: {exc}") from exc

            if is_link:
                resolved = _resolve(path, f"guide entry {path}")
                if resolved.is_dir():
                    raise LintUsageError(f"linked guide directory is not allowed: {path}")
                if path.suffix.lower() == ".md":
                    if not _is_relative_to(resolved, guides_root):
                        raise LintUsageError(
                            f"guide file resolves outside the guides root: {path}"
                        )
                    files.append((path, resolved))
                continue

            if _is_junction(path):
                raise LintUsageError(f"linked guide directory is not allowed: {path}")

            try:
                is_directory = entry.is_dir(follow_symlinks=False)
                is_file = entry.is_file(follow_symlinks=False)
            except OSError as exc:
                raise LintUsageError(f"cannot inspect guide entry {path}: {exc}") from exc

            if is_directory:
                resolved = _resolve(path, f"guide directory {path}")
                if not _is_relative_to(resolved, guides_root):
                    raise LintUsageError(
                        f"guide directory resolves outside the guides root: {path}"
                    )
                child_directories.append(path)
            elif is_file and path.suffix.lower() == ".md":
                resolved = _resolve(path, f"guide file {path}")
                if not _is_relative_to(resolved, guides_root):
                    raise LintUsageError(f"guide file resolves outside the guides root: {path}")
                files.append((path, resolved))

        stack.extend(reversed(child_directories))

    return sorted(files, key=lambda item: item[0].as_posix())


def _target_reasons(target: str) -> list[str]:
    """Return violation reasons for one Markdown link destination."""

    target = target.strip("<>")
    # Only repository-relative destinations can point at a repo-only record.
    # An external URL that happens to contain `/rfc/` or `changelog` — the
    # RFC Editor, keepachangelog.com — is a legitimate citation with no
    # in-repo fix available, so exempt it rather than force an allow marker.
    if EXTERNAL_URL_RE.match(target):
        return []
    path = target.split("#", 1)[0].split("?", 1)[0].replace("\\", "/")
    lower_path = path.lower()
    segments = {segment for segment in lower_path.split("/") if segment not in {"", ".", ".."}}
    reasons = [
        f"Markdown link target contains repo-only /{segment}/ segment: {target}"
        for segment in sorted(segments & GOVERNANCE_SEGMENTS)
    ]
    if "changelog" in lower_path:
        reasons.append(f"Markdown link target points to a changelog: {target}")
    return reasons


def _link_reasons(line: str) -> list[str]:
    """Return violation reasons for inline and reference-style link targets."""

    reasons = [
        reason
        for match in MARKDOWN_LINK_RE.finditer(line)
        for reason in _target_reasons(match.group("target"))
    ]
    reference = MARKDOWN_REFERENCE_DEFINITION_RE.match(line)
    if reference:
        reasons.extend(_target_reasons(reference.group("target")))
    return reasons


def _line_reasons(line: str, real_spec_slugs: set[str]) -> list[str]:
    """Return all distinct lint reasons for one non-exempt line."""

    reasons = _link_reasons(line)
    reasons.extend(
        f"repo-only governance token {match.group(0)}"
        for match in GOVERNANCE_TOKEN_RE.finditer(line)
    )
    reasons.extend(
        f"reference cites real spec '{match.group('slug')}' under docs/specs/"
        for match in SPEC_REFERENCE_RE.finditer(line)
        if match.group("slug") in real_spec_slugs
    )
    return list(dict.fromkeys(reasons))


def lint_guides(guides_argument: str) -> list[Violation]:
    """Scan one guide tree and return all actionable violations."""

    repo_root, guides_root, specs_root = _runtime_roots(guides_argument)
    real_spec_slugs = _real_spec_slugs(specs_root)
    violations: list[Violation] = []

    for display_path, resolved_path in _markdown_files(guides_root):
        try:
            lines = resolved_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise LintUsageError(f"cannot read guide file {display_path}: {exc}") from exc
        try:
            diagnostic_path = display_path.relative_to(repo_root)
        except ValueError:
            diagnostic_path = display_path

        for line_number, line in enumerate(lines, start=1):
            allowed = bool(ALLOW_RE.search(line))
            if line_number > 1:
                allowed = allowed or bool(ALLOW_RE.search(lines[line_number - 2]))
            if allowed:
                continue
            violations.extend(
                Violation(diagnostic_path, line_number, reason)
                for reason in _line_reasons(line, real_spec_slugs)
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    """Run the guide lint command."""

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--guides-root",
        default=str(DEFAULT_GUIDES_ROOT),
        help="Guide tree to scan (default: guides/).",
    )
    args = parser.parse_args(argv)

    try:
        violations = lint_guides(args.guides_root)
    except LintUsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if violations:
        for violation in violations:
            print(f"{violation.path}:{violation.line}: {violation.reason}")
        return 1

    print(OK_MESSAGE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
