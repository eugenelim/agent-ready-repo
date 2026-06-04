"""Crawl a Confluence on-prem space by page hierarchy and write clean Markdown.

Invocation examples:

    python scripts/crawl_space.py --check
    python scripts/crawl_space.py --space ENG
    python scripts/crawl_space.py --space ENG --depth 3 --output ./out
    python scripts/crawl_space.py --space ENG --root 12345 --force
    python scripts/crawl_space.py --space ENG --no-attachments

Credentials are resolved via the build-projected ``credentials_shim`` sibling
(Tier 1 env → Tier 2 OS keyring → Tier 3 dotfile); run
``credential-setup`` skill to populate the namespace. The
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

# Bootstrap when invoked as ``python scripts/crawl_space.py`` so the
# relative imports of sibling modules — including ``_client``'s
# ``from .credentials_shim import …`` — resolve against the
# build-projected siblings in this directory. Gated on
# ``__spec__ is None`` so the block only fires for true file-path
# invocation; an importlib-based test harness is responsible for
# its own package context.
if __package__ in (None, "") and __spec__ is None:
    _here = Path(__file__).resolve().parent
    sys.path.insert(0, str(_here.parent))
    __package__ = _here.name

# Every third-party and sibling import goes inside this guard so a missing
# dependency yields the banded exit-2 "run pip install" message instead of
# a raw traceback. ``yaml`` / ``slugify`` (direct) and ``lxml`` /
# ``markdownify`` (transitively, via ._convert) must be in here too — when
# they sat above the guard a missing one bypassed the contract entirely.
try:
    import yaml  # noqa: E402
    from slugify import slugify  # noqa: E402

    from ._client import (  # noqa: E402
        AuthError,
        ConfluenceClient,
        ConfluenceError,
        Credentials,
        Page,
        load_credentials,
    )
    from ._convert import to_markdown  # noqa: E402
    from ._links import LinkTargets  # noqa: E402
except ModuleNotFoundError as _import_exc:  # noqa: E402
    # 1 = functional/internal (shim not projected); 2 = user must act (deps).
    if _import_exc.name and "credentials_shim" in _import_exc.name:
        sys.stderr.write(
            "error: credentials_shim sibling not projected — run "
            "`make build-self` or reinstall the credential-brokers pack.\n"
        )
        raise SystemExit(1)
    sys.stderr.write(
        f"error: missing dependency {_import_exc.name!r} — run: "
        "python -m pip install -r requirements.txt\n"
    )
    raise SystemExit(2)

log = logging.getLogger("confluence_crawler")

# Banded exit-code taxonomy (docs/specs/credentialed-cli-exit-code-contract):
#   0     success
#   1     functional / operational error — usage, server 5xx, transport,
#         partial crawl (some pages failed), keychain hard-fail, unexpected
#   2     user must act — credential missing/invalid/expired, 401/403
#   3-9   reserved for the credential/auth band (never reuse for functional)
#   130   interrupted (128 + SIGINT); outside the 0-9 table by POSIX convention
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USER_ACTION = 2
SLUG_MAX_LEN = 80
UNLIMITED_DEPTH = 9999

# Token-shaped CLI flags are rejected before argparse runs — argparse would
# otherwise echo the offending ``--flag VALUE`` verbatim in its
# "unrecognized arguments" error, leaking the secret to stderr / the agent
# transcript. The Confluence PAT (or Cloud API token used as a Basic-auth
# password) is resolved only via env / keyring / dotfile. Mirrors the
# sibling jira / jira-align idiom (exact-set match).
# Superset of the CONVENTIONS § "The argv ban" canonical six
# (--token, --api-token, --api-key, --bearer, --pat, --password) plus the
# short -t and a Confluence-specific alias.
TOKEN_CLI_FLAGS = frozenset({
    "--token", "--api-token", "--api-key", "--bearer", "-t",
    "--confluence-token", "--pat", "--password",
})


def _reject_token_on_cli(argv: list[str]) -> None:
    """Confluence tokens / PATs are secret; refuse to accept them as CLI args."""
    for arg in argv:
        head = arg.split("=", 1)[0]
        if head in TOKEN_CLI_FLAGS:
            sys.stderr.write(
                "error: API tokens must not be passed on the command line. "
                "Run `credential-setup` skill to store CONFLUENCE_API_TOKEN "
                "via env / keyring / dotfile.\n"
            )
            sys.exit(EXIT_ERROR)


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
        return EXIT_USER_ACTION
    identity = (
        me.get("username")
        or me.get("displayName")
        or me.get("publicName")
        or me.get("email")
        or me.get("accountId")
        or "<unknown>"
    )
    log.info("authenticated as %s (%s)", identity, flavor)
    return EXIT_OK


async def main_async(args: argparse.Namespace) -> int:
    try:
        creds: Credentials = load_credentials()
    except AuthError as exc:
        log.error("%s", exc)
        return EXIT_USER_ACTION

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
            return EXIT_ERROR

        root_id = args.root
        if not root_id:
            root_id = await client.get_space_homepage_id(args.space)
            if not root_id:
                log.error("space %s has no homepage; pass --root <page_id>", args.space)
                return EXIT_ERROR

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
        # Partial completion (some pages failed) is a functional outcome → 1,
        # not a credential/user-action; per-page detail is in the log above.
        return EXIT_OK if failed == 0 else EXIT_ERROR


def main() -> int:
    _reject_token_on_cli(sys.argv[1:])
    args = parse_args()
    _setup_logging(args.verbose)
    # Top-level catch-all: no exception escapes as a traceback. `except
    # Exception` deliberately does NOT catch KeyboardInterrupt (130 below) or
    # SystemExit (BaseException) — those pass through.
    try:
        return asyncio.run(main_async(args))
    except KeyboardInterrupt:
        log.warning("interrupted")
        return 130
    except Exception as exc:  # noqa: BLE001 — intentional functional catch-all
        name = type(exc).__name__
        if name == "Tier2HardFailError":
            sys.stderr.write(
                f"error: OS keyring unavailable ({name}); set CONFLUENCE_API_TOKEN "
                "via env or the dotfile, or run `credential-setup`.\n"
            )
        else:
            sys.stderr.write(f"error: unexpected {name}; report this if it persists.\n")
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
