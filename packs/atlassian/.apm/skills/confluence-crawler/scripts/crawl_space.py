"""Crawl a Confluence on-prem space by page hierarchy and write clean Markdown.

Invocation examples:

    python scripts/crawl_space.py --check
    python scripts/crawl_space.py --space ENG
    python scripts/crawl_space.py --space ENG --depth 3 --output ./out
    python scripts/crawl_space.py --space ENG --root 12345 --force
    python scripts/crawl_space.py --space ENG --no-attachments

Credentials are resolved via the ``agentbundle.credentials`` loader
(Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile); run
``agentbundle creds setup confluence`` to populate the namespace. The
PAT is never accepted on the command line.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml
from slugify import slugify

# Ensure sibling modules resolve when script is invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _client import (  # noqa: E402
    AuthError,
    ConfluenceClient,
    ConfluenceError,
    Credentials,
    Page,
    load_credentials,
)
from _convert import to_markdown  # noqa: E402
from _links import LinkTargets  # noqa: E402

log = logging.getLogger("confluence_crawler")
SLUG_MAX_LEN = 80
UNLIMITED_DEPTH = 9999


@dataclass
class DiscoveredPage:
    id: str
    title: str
    version: int
    parent_id: str | None
    depth: int


@dataclass
class CrawlPlan:
    base_url: str
    space_key: str
    output_dir: Path
    discovered: list[DiscoveredPage]
    slug_by_id: dict[str, str]
    existing_by_id: dict[str, tuple[Path, int]]
    to_fetch: set[str] = field(default_factory=set)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--space", help="Confluence space key (e.g., ENG)")
    parser.add_argument("--root", help="Page ID to start from (default: space homepage)")
    parser.add_argument("--depth", type=int, default=UNLIMITED_DEPTH, help="Max hierarchy depth (default: unlimited)")
    parser.add_argument("--output", type=Path, default=Path("./confluence-out"), help="Output directory")
    parser.add_argument("--force", action="store_true", help="Re-fetch and overwrite even if version unchanged")
    parser.add_argument("--no-attachments", action="store_true", help="Skip downloading attachments")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--min-delay-ms", type=int, default=100)
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification (not recommended)")
    parser.add_argument("--check", action="store_true", help="Verify credentials and connectivity, then exit")
    parser.add_argument("--verbose", "-v", action="store_true")
    return parser.parse_args(argv)


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def _safe_slug(title: str, fallback: str) -> str:
    base = slugify(title, max_length=SLUG_MAX_LEN) or slugify(fallback, max_length=SLUG_MAX_LEN) or fallback
    return base


def _assign_slugs(discovered: Iterable[DiscoveredPage]) -> dict[str, str]:
    """Stable slug assignment. Duplicates fall back to slug + page_id suffix."""
    slug_by_id: dict[str, str] = {}
    seen: dict[str, str] = {}  # slug -> page_id that claimed it
    for page in discovered:
        base = _safe_slug(page.title, page.id)
        if base in seen and seen[base] != page.id:
            slug_by_id[page.id] = f"{base}-{page.id}"
        else:
            seen.setdefault(base, page.id)
            slug_by_id[page.id] = base
    return slug_by_id


def _scan_existing(output_dir: Path) -> dict[str, tuple[Path, int]]:
    """Build {confluence_id: (path, version)} from existing markdown files."""
    index: dict[str, tuple[Path, int]] = {}
    if not output_dir.is_dir():
        return index
    for path in output_dir.glob("*.md"):
        try:
            front = _read_frontmatter(path)
        except Exception as exc:
            log.warning("could not parse frontmatter from %s: %s", path.name, exc)
            continue
        cid = front.get("confluence_id")
        version = front.get("version")
        if cid and isinstance(version, int):
            index[str(cid)] = (path, version)
    return index


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    block = text[4:end]
    data = yaml.safe_load(block) or {}
    return data if isinstance(data, dict) else {}


def _render_frontmatter(data: dict) -> str:
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip()
    return f"---\n{body}\n---\n"


async def _discover(
    client: ConfluenceClient,
    root_id: str,
    max_depth: int,
) -> list[DiscoveredPage]:
    root = await client.get_page(root_id)
    discovered = [
        DiscoveredPage(id=root.id, title=root.title, version=root.version, parent_id=None, depth=0)
    ]
    queue: deque[tuple[str, int]] = deque([(root.id, 0)])
    seen = {root.id}
    while queue:
        pid, d = queue.popleft()
        if d >= max_depth:
            continue
        async for child in client.iter_children(pid):
            cid = str(child["id"])
            if cid in seen:
                continue
            seen.add(cid)
            version = int((child.get("version") or {}).get("number", 1))
            discovered.append(
                DiscoveredPage(
                    id=cid,
                    title=child.get("title", ""),
                    version=version,
                    parent_id=pid,
                    depth=d + 1,
                )
            )
            queue.append((cid, d + 1))
    return discovered


async def _fetch_attachments_for(
    client: ConfluenceClient,
    page_id: str,
    output_dir: Path,
) -> dict[str, str]:
    rel_by_filename: dict[str, str] = {}
    attach_dir = output_dir / "attachments" / page_id
    async for att in client.iter_attachments(page_id):
        if not att.download_path:
            continue
        dest = attach_dir / att.filename
        try:
            await client.download_attachment(att.download_path, dest)
            rel_by_filename[att.filename] = f"attachments/{page_id}/{att.filename}"
        except ConfluenceError as exc:
            log.warning("attachment %s on page %s failed: %s", att.filename, page_id, exc)
    return rel_by_filename


def _build_frontmatter(page: Page, slug_by_id: dict[str, str], base_url: str) -> dict:
    url = f"{base_url.rstrip('/')}{page.webui_path}" if page.webui_path else ""
    return {
        "title": page.title,
        "confluence_id": page.id,
        "space_key": page.space_key,
        "version": page.version,
        "updated": page.updated,
        "author": page.author,
        "parent_id": page.parent_id,
        "labels": list(page.labels),
        "url": url,
        "slug": slug_by_id.get(page.id, page.id),
    }


async def _fetch_and_write(
    client: ConfluenceClient,
    page_id: str,
    plan: CrawlPlan,
    targets: LinkTargets,
    download_attachments: bool,
) -> tuple[str, str]:
    page = await client.get_page(page_id)

    if download_attachments:
        rel = await _fetch_attachments_for(client, page.id, plan.output_dir)
        # targets.attachment_rel_by_page_id was pre-seeded but may need updating
        targets.attachment_rel_by_page_id[page.id] = rel

    body_md = to_markdown(page.storage_xhtml, page_id=page.id, targets=targets)
    front = _build_frontmatter(page, plan.slug_by_id, plan.base_url)
    content = _render_frontmatter(front) + f"\n# {page.title}\n\n" + body_md

    slug = plan.slug_by_id[page.id]
    path = plan.output_dir / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".md.part")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)
    return page.id, str(path)


async def _run_check(client: ConfluenceClient, flavor: str) -> int:
    try:
        me = await client.whoami()
    except AuthError as exc:
        log.error("%s", exc)
        return 2
    identity = (
        me.get("username")
        or me.get("displayName")
        or me.get("publicName")
        or me.get("email")
        or me.get("accountId")
        or "<unknown>"
    )
    log.info("authenticated as %s (%s)", identity, flavor)
    return 0


async def main_async(args: argparse.Namespace) -> int:
    try:
        creds: Credentials = load_credentials()
    except AuthError as exc:
        log.error("%s", exc)
        return 2

    async with ConfluenceClient(
        creds,
        concurrency=args.concurrency,
        min_delay_ms=args.min_delay_ms,
        verify_tls=not args.insecure,
    ) as client:
        if args.check:
            return await _run_check(client, creds.flavor)

        if not args.space:
            log.error("--space is required unless --check is used")
            return 2

        root_id = args.root
        if not root_id:
            root_id = await client.get_space_homepage_id(args.space)
            if not root_id:
                log.error("space %s has no homepage; pass --root <page_id>", args.space)
                return 2

        log.info("discovering hierarchy from page %s (depth=%s)", root_id, args.depth)
        discovered = await _discover(client, root_id, args.depth)
        log.info("discovered %d pages", len(discovered))

        slug_by_id = _assign_slugs(discovered)
        existing = _scan_existing(args.output)

        to_fetch = set()
        for page in discovered:
            if args.force:
                to_fetch.add(page.id)
                continue
            existing_entry = existing.get(page.id)
            if existing_entry is None or existing_entry[1] < page.version:
                to_fetch.add(page.id)

        log.info("%d pages need fetching (skipping %d unchanged)", len(to_fetch), len(discovered) - len(to_fetch))

        plan = CrawlPlan(
            base_url=creds.base_url,
            space_key=args.space,
            output_dir=args.output,
            discovered=discovered,
            slug_by_id=slug_by_id,
            existing_by_id=existing,
            to_fetch=to_fetch,
        )
        args.output.mkdir(parents=True, exist_ok=True)

        slug_by_title = {
            (args.space, page.title): slug_by_id[page.id] for page in discovered if page.title
        }
        targets = LinkTargets(
            base_url=creds.base_url,
            default_space_key=args.space,
            slug_by_page_id=dict(slug_by_id),
            slug_by_title=slug_by_title,
            attachment_rel_by_page_id={},
        )

        # Fetch pages concurrently, bounded by client semaphore.
        async def _task(pid: str) -> tuple[str, str] | None:
            try:
                return await _fetch_and_write(
                    client, pid, plan, targets, download_attachments=not args.no_attachments
                )
            except ConfluenceError as exc:
                log.error("page %s failed: %s", pid, exc)
                return None

        results = await asyncio.gather(*(_task(pid) for pid in to_fetch))
        success = sum(1 for r in results if r is not None)
        failed = len(to_fetch) - success

        log.info("wrote %d pages (failed: %d, skipped: %d)", success, failed, len(discovered) - len(to_fetch))
        return 0 if failed == 0 else 1


def main() -> int:
    args = parse_args()
    _setup_logging(args.verbose)
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        log.warning("interrupted")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
