#!/usr/bin/env python3
"""Audit internal page and fragment targets in a generated HTML tree."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

PAGES_BASE = "/agent-ready-repo"
NON_NAVIGATION_SCHEMES = {
    "data",
    "javascript",
    "mailto",
    "sms",
    "tel",
}
EXTERNAL_SCHEMES = {"http", "https"}
MALFORMED_PERCENT = re.compile(r"%(?![0-9A-Fa-f]{2})")


class AuditError(Exception):
    """An invocation or build-tree error that makes an audit unsafe."""


@dataclass(frozen=True)
class Page:
    """The link-relevant data extracted from one emitted HTML page."""

    relative_path: PurePosixPath
    hrefs: tuple[str, ...]
    anchors: frozenset[str]


class LinkParser(HTMLParser):
    """Collect navigational hrefs and fragment targets from generated HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.anchors: set[str] = set()

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """Collect relevant attributes without interpreting page structure."""
        values = {name.lower(): value for name, value in attrs if value is not None}
        if tag.lower() in {"a", "area"} and "href" in values:
            self.hrefs.append(values["href"])
        identifier = values.get("id")
        if identifier:
            self.anchors.add(identifier)
        legacy_name = values.get("name")
        if tag.lower() == "a" and legacy_name:
            self.anchors.add(legacy_name)


def _is_confined(path: Path, root: Path) -> bool:
    """Return whether a resolved path is the build root or one of its children."""
    return path == root or path.is_relative_to(root)


def _resolve_confined(path: Path, root: Path, label: str) -> Path:
    """Resolve a candidate and fail before use when it escapes the build root."""
    try:
        resolved = path.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise AuditError(f"cannot resolve {label}") from exc
    if not _is_confined(resolved, root):
        raise AuditError(f"{label} escapes build root")
    return resolved


def _build_root(raw: str) -> Path:
    """Resolve and validate the operator-selected build boundary."""
    candidate = Path(raw)
    if not candidate.exists():
        raise AuditError(f"build directory does not exist: {raw}")
    try:
        root = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise AuditError(f"cannot resolve build directory: {raw}") from exc
    if not root.is_dir():
        raise AuditError(f"build path is not a directory: {raw}")
    return root


def _discover_html(root: Path) -> list[Path]:
    """Discover HTML pages deterministically without following directory links."""

    def fail_unreadable(error: OSError) -> None:
        failed = Path(error.filename) if error.filename else root
        try:
            label = failed.relative_to(root)
        except ValueError:
            label = failed
        raise AuditError(f"cannot read discovered directory: {label}") from error

    pages: list[Path] = []
    visited_directories: set[Path] = set()
    for dirpath, dirnames, filenames in os.walk(
        root,
        followlinks=False,
        onerror=fail_unreadable,
    ):
        current = _resolve_confined(Path(dirpath), root, "discovered directory")
        if current in visited_directories:
            dirnames[:] = []
            continue
        visited_directories.add(current)
        safe_dirs: list[str] = []
        for dirname in sorted(dirnames):
            child = Path(dirpath) / dirname
            resolved_child = _resolve_confined(
                child,
                root,
                f"discovered path {child.relative_to(root)}",
            )
            if resolved_child not in visited_directories and not child.is_symlink():
                safe_dirs.append(dirname)
        dirnames[:] = safe_dirs
        for filename in sorted(filenames):
            if not filename.endswith(".html"):
                continue
            candidate = current / filename
            resolved = _resolve_confined(
                candidate,
                root,
                f"discovered page {candidate.relative_to(root)}",
            )
            if not resolved.is_file():
                raise AuditError(
                    f"discovered page is not a regular file: {candidate.relative_to(root)}"
                )
            pages.append(resolved)
    pages.sort(key=lambda path: path.relative_to(root).as_posix())
    if not pages:
        raise AuditError("build tree contains no HTML pages")
    return pages


def _parse_page(path: Path, root: Path) -> Page:
    """Parse one UTF-8 HTML page into the audit inventory."""
    relative = PurePosixPath(path.relative_to(root).as_posix())
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AuditError(f"page {relative} is not valid UTF-8") from exc
    except OSError as exc:
        raise AuditError(f"page {relative} is unreadable") from exc

    parser = LinkParser()
    try:
        parser.feed(content)
        parser.close()
    except (ValueError, AssertionError) as exc:
        raise AuditError(f"page {relative} contains malformed HTML") from exc
    return Page(relative, tuple(parser.hrefs), frozenset(parser.anchors))


def _decode_url_component(raw: str, label: str) -> str:
    """Percent-decode a URL component while rejecting malformed escapes."""
    if MALFORMED_PERCENT.search(raw):
        raise AuditError(f"malformed percent escape in {label}")
    try:
        return unquote(raw, encoding="utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise AuditError(f"invalid UTF-8 escape in {label}") from exc


def _source_directory(page: Page) -> list[str]:
    """Return the URL directory parts used to resolve a page's relative hrefs."""
    return list(page.relative_path.parent.parts)


def _normalise_parts(page: Page, raw_path: str) -> tuple[list[str], bool]:
    """Normalize an internal URL path and reject traversal above the site root."""
    decoded = _decode_url_component(raw_path, "link path")
    if decoded == PAGES_BASE:
        decoded = "/"
    elif decoded.startswith(f"{PAGES_BASE}/"):
        decoded = decoded[len(PAGES_BASE) :]

    rooted = decoded.startswith("/")
    parts = [] if rooted else _source_directory(page)
    for part in decoded.split("/"):
        if not part or part == ".":
            continue
        if part == "..":
            if not parts:
                raise AuditError(f"internal target {raw_path or '#fragment'} escapes build root")
            parts.pop()
            continue
        parts.append(part)
    return parts, decoded.endswith("/")


def _target_candidates(parts: list[str], directory_route: bool) -> list[PurePosixPath]:
    """Return emitted-file candidates in route-preference order."""
    path = PurePosixPath(*parts) if parts else PurePosixPath()
    if directory_route or not parts:
        return [path / "index.html"]
    if path.suffix:
        return [path]
    return [path / "index.html", path.with_suffix(".html")]


def _resolve_target(
    page: Page,
    raw_path: str,
    root: Path,
) -> tuple[PurePosixPath, bool]:
    """Resolve an internal URL to one emitted file without leaving the root."""
    if not raw_path:
        return page.relative_path, True

    parts, directory_route = _normalise_parts(page, raw_path)
    candidates = _target_candidates(parts, directory_route)
    for relative in candidates:
        candidate = root.joinpath(*relative.parts)
        resolved = _resolve_confined(candidate, root, f"internal target {relative}")
        if resolved.is_file():
            return PurePosixPath(resolved.relative_to(root).as_posix()), True
    return candidates[0], False


def _classify_href(href: str) -> tuple[str, str] | None:
    """Return internal path/fragment components, or None for ignored links."""
    stripped = href.strip()
    if not stripped:
        return None
    try:
        parsed = urlsplit(stripped)
    except ValueError as exc:
        raise AuditError("malformed internal link") from exc
    scheme = parsed.scheme.lower()
    if parsed.netloc or scheme in EXTERNAL_SCHEMES | NON_NAVIGATION_SCHEMES:
        return None
    if scheme:
        raise AuditError(f"unsupported link scheme: {scheme}")
    return parsed.path, parsed.fragment


def audit(root: Path) -> tuple[int, int, list[str]]:
    """Audit the rendered tree and return page count, link count, and failures."""
    pages = [_parse_page(path, root) for path in _discover_html(root)]
    by_path = {page.relative_path: page for page in pages}
    failures: set[str] = set()
    link_count = 0

    for page in pages:
        for href in sorted(page.hrefs):
            try:
                classified = _classify_href(href)
                if classified is None:
                    continue
                link_count += 1
                raw_path, raw_fragment = classified
                target, exists = _resolve_target(page, raw_path, root)
                if not exists:
                    failures.add(f"BROKEN {page.relative_path}: {href} -> {target} (missing page)")
                    continue
                if not raw_fragment:
                    continue
                fragment = _decode_url_component(raw_fragment, "fragment")
                target_page = by_path.get(target)
                if target_page is None or fragment not in target_page.anchors:
                    failures.add(
                        f"BROKEN {page.relative_path}: {href} -> "
                        f"{target}#{fragment} (missing fragment)"
                    )
            except AuditError as exc:
                raise AuditError(f"page {page.relative_path}, href {href!r}: {exc}") from exc

    return len(pages), link_count, sorted(failures)


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Check internal links and fragments in generated HTML.",
    )
    parser.add_argument("--build-dir", required=True, help="generated site root")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the audit and implement the documented 0/1/2 exit contract."""
    args = _parser().parse_args(argv)
    try:
        root = _build_root(args.build_dir)
        page_count, link_count, failures = audit(root)
    except AuditError as exc:
        print(f"rendered-site-links: error: {exc}", file=sys.stderr)
        return 2

    if failures:
        print("\n".join(failures))
        failure_pages = {line.split(":", 1)[0] for line in failures}
        noun = "page" if len(failure_pages) == 1 else "pages"
        print(
            f"rendered-site-links: {len(failures)} broken target"
            f"{'s' if len(failures) != 1 else ''} across "
            f"{len(failure_pages)} {noun}"
        )
        return 1

    noun = "link" if link_count == 1 else "links"
    page_noun = "page" if page_count == 1 else "pages"
    print(f"rendered-site-links: {link_count} {noun} across {page_count} {page_noun}; clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
