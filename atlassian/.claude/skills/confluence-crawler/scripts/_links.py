"""Resolve Confluence internal links to either a relative Markdown path or
an absolute Confluence URL, based on what was crawled."""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass


@dataclass(frozen=True)
class LinkTargets:
    """Lookup tables populated after crawling completes."""
    base_url: str
    default_space_key: str
    slug_by_page_id: dict[str, str]
    slug_by_title: dict[tuple[str, str], str]  # (space_key, title) -> slug
    attachment_rel_by_page_id: dict[str, dict[str, str]]  # page_id -> {filename: rel_path}


def absolute(base_url: str, path: str) -> str:
    if not path:
        return base_url
    if path.startswith(("http://", "https://")):
        return path
    return urllib.parse.urljoin(base_url + "/", path.lstrip("/"))


def page_href(
    targets: LinkTargets,
    *,
    space_key: str | None,
    title: str | None,
    page_id: str | None,
    webui_fallback: str | None,
) -> str:
    """Resolve a page reference.

    Returns a relative `.md` path if the page was crawled, otherwise an
    absolute Confluence URL built from the webui path or a display URL.
    """
    if page_id and page_id in targets.slug_by_page_id:
        return f"{targets.slug_by_page_id[page_id]}.md"

    effective_space = space_key or targets.default_space_key
    if title and (effective_space, title) in targets.slug_by_title:
        return f"{targets.slug_by_title[(effective_space, title)]}.md"

    if webui_fallback:
        return absolute(targets.base_url, webui_fallback)
    if title and effective_space:
        encoded = urllib.parse.quote(title.replace(" ", "+"), safe="+")
        return absolute(targets.base_url, f"/display/{effective_space}/{encoded}")
    if page_id:
        return absolute(targets.base_url, f"/pages/viewpage.action?pageId={page_id}")
    return targets.base_url


def attachment_href(
    targets: LinkTargets,
    *,
    page_id: str,
    filename: str,
) -> str:
    """Resolve an attachment reference to a relative path if downloaded,
    otherwise an absolute Confluence download URL."""
    rel = targets.attachment_rel_by_page_id.get(page_id, {}).get(filename)
    if rel:
        return rel
    encoded_file = urllib.parse.quote(filename)
    return absolute(
        targets.base_url,
        f"/download/attachments/{page_id}/{encoded_file}",
    )
