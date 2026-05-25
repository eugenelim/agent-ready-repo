"""Resolve the target page for a publish.

The agent passes one of: --page-id, --url, --from-frontmatter (read
``confluence_id`` from YAML frontmatter on the input file), or
--space + --title. This module turns each into a concrete page-id
plus the body content (with frontmatter stripped when present).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

# Matches ".../pages/<id>/..." or ".../pages/<id>" in a Confluence URL.
_PAGE_ID_FROM_URL_RE = re.compile(r"/pages/(\d+)(?:/|$)")

# Crawler-shape frontmatter delimiters.
_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<yaml>.*?)\n---\s*\n?(?P<body>.*)\Z",
    re.DOTALL,
)


class TargetResolutionError(Exception):
    """Raised when target-mode flags are missing, conflicting, or invalid."""


@dataclass(frozen=True)
class ResolvedTarget:
    page_id: Optional[str]
    space_key: Optional[str]
    title: Optional[str]
    parent_id: Optional[str]
    body_text: str
    frontmatter: dict


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter (if present) from the body."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        data = yaml.safe_load(match.group("yaml")) or {}
    except yaml.YAMLError as exc:
        raise TargetResolutionError(f"invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise TargetResolutionError("YAML frontmatter must be a mapping")
    return data, match.group("body")


def page_id_from_url(url: str) -> str:
    match = _PAGE_ID_FROM_URL_RE.search(url)
    if not match:
        raise TargetResolutionError(
            f"could not extract page ID from URL {url!r}; expected '/pages/<id>'"
        )
    return match.group(1)


def read_input(path: str) -> str:
    if path == "-":
        import sys
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def resolve_target(
    *,
    raw_body: str,
    page_id: Optional[str],
    url: Optional[str],
    from_frontmatter: bool,
    space: Optional[str],
    title: Optional[str],
    parent_id: Optional[str],
) -> ResolvedTarget:
    """Apply the target-mode rules; return the resolved identifiers + body.

    Exactly one of {page_id, url, from_frontmatter, space+title} must be
    supplied. Frontmatter is always parsed (used for title/version
    fallback even in other modes), and its body half replaces raw_body
    when present.
    """
    id_modes = sum(bool(x) for x in (page_id, url, from_frontmatter))
    have_lookup = bool(space and title)

    # In id-mode, `--title` is a documented update-time override and
    # `--space` is redundant-but-tolerated context. The partial-lookup
    # check only matters when the user is *trying* to use lookup mode
    # (i.e. no id-mode is set).
    have_lookup_partial = (id_modes == 0) and (bool(space) ^ bool(title))

    if id_modes == 0 and not have_lookup and not have_lookup_partial:
        raise TargetResolutionError(
            "no target specified — pass one of --page-id, --url, "
            "--from-frontmatter, or --space + --title"
        )
    if id_modes > 1:
        raise TargetResolutionError(
            "conflicting target flags — pass at most one of "
            "--page-id, --url, --from-frontmatter"
        )
    if have_lookup_partial:
        raise TargetResolutionError(
            "--space and --title must be passed together"
        )
    if have_lookup and id_modes > 0:
        raise TargetResolutionError(
            "--space/--title is a lookup mode; do not combine with "
            "--page-id/--url/--from-frontmatter"
        )

    frontmatter, body = split_frontmatter(raw_body)

    resolved_id: Optional[str] = None
    resolved_title: Optional[str] = title
    resolved_space: Optional[str] = space

    if page_id:
        resolved_id = str(page_id)
    elif url:
        resolved_id = page_id_from_url(url)
    elif from_frontmatter:
        fm_id = frontmatter.get("confluence_id") or frontmatter.get("id")
        if not fm_id:
            raise TargetResolutionError(
                "--from-frontmatter set but input has no 'confluence_id' field"
            )
        resolved_id = str(fm_id)
        if not resolved_space:
            resolved_space = frontmatter.get("space_key") or frontmatter.get("space")

    return ResolvedTarget(
        page_id=resolved_id,
        space_key=resolved_space,
        title=resolved_title,
        parent_id=str(parent_id) if parent_id else None,
        body_text=body,
        frontmatter=frontmatter,
    )
