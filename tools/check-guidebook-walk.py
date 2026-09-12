#!/usr/bin/env python3
"""Sweep every guidebook step's rendered navigation for disagreement.

Usage:
    python3 tools/check-guidebook-walk.py [BUILD_DIR]

A step's position is stated on five surfaces -- the page body, the frontmatter
the site projects, the right-hand rail, the mobile bar, and the sidebar entry.
Each is generated from the one before it, so any one of them can drift alone
and the page still renders. This walks the cross-product instead of spot-checking
a page: every step of every guidebook, against every surface that names it.

Checks, per guidebook:
  - the walk is contiguous 1..M with no gap, repeat, or off-by-one M
  - every step page states the same M
  - every page's rail lists the same steps, in the same order
  - exactly one entry is marked current, and it is that page
  - every link the rail offers resolves to a built page
  - the in-body onward link resolves
  - the rail, the mobile bar, and the body agree on N of M

Exit 0 means no findings.  Exit 1 means one or more.  Exit 2 means usage error.
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
RAIL = re.compile(r'<nav class="guidebook-walk.*?</nav>', re.S)
MOBILE = re.compile(r'<p class="guidebook-position.*?</p>', re.S)
BODY_STEP = re.compile(r"<strong>Step (\d+) of (\d+) —")
RAIL_STEP = re.compile(r"Step (\d+) of (\d+)")
ANCHOR = re.compile(r'<a href="([^"]*)"([^>]*)>(.*?)</a>', re.S)
CANONICAL = re.compile(r'<link rel="canonical" href="([^"]*)"')


@dataclass(frozen=True)
class Finding:
    page: str
    surface: str
    detail: str

    def render(self) -> str:
        return f"{self.page}: {self.surface}: {self.detail}"


def _text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def _rail_entries(fragment: str) -> list[tuple[str, str, bool]]:
    """(href, title, is_current) for each step the rail lists."""
    return [
        (href, _text(label), "aria-current" in attrs)
        for href, attrs, label in ANCHOR.findall(fragment)
    ]


def _suffix(page: Path, build: Path) -> str:
    return "/" + str(page.parent.relative_to(build)).replace("\\", "/") + "/"


def site_base(build: Path) -> str:
    """The route prefix the built site is served under, read from the pages.

    Derived rather than assumed. Comparing a build-relative path against an
    href that carries the site base is the shape of bug this sweep exists to
    catch, and the sweep's first run made exactly that mistake itself --
    reporting every real link as unbuilt.
    """
    for page in build.rglob("index.html"):
        canonical = CANONICAL.search(page.read_text(encoding="utf-8"))
        if canonical:
            suffix = _suffix(page, build)
            # Split the URL rather than pattern-matching it: a non-greedy match
            # from the first "/" starts inside "https://" and yields a base
            # carrying the host, which matches no href on the page.
            path = urlsplit(canonical.group(1)).path
            if path.endswith(suffix):
                return path[: -len(suffix)]
    return ""


def _route(page: Path, build: Path, base: str = "") -> str:
    return base + _suffix(page, build)


def check_guidebook(pages: list[Path], build: Path, base: str) -> list[Finding]:
    """Every cross-page agreement check for one guidebook."""
    findings: list[Finding] = []
    routes = {_route(p, build, base) for p in build.rglob("index.html")}
    declared: dict[int, Path] = {}
    reference: list[tuple[str, str]] | None = None

    for page in sorted(pages):
        name = str(page.parent.relative_to(build))
        text = page.read_text(encoding="utf-8")
        body = BODY_STEP.search(text)
        rail = RAIL.search(text)
        mobile = MOBILE.search(text)

        if body is None:
            findings.append(Finding(name, "body", "states no `Step N of M`"))
            continue
        step, total = int(body.group(1)), int(body.group(2))

        if step in declared:
            findings.append(Finding(
                name, "walk", f"step {step} is also claimed by {declared[step].parent.name}"))
        declared[step] = page

        if total != len(pages):
            findings.append(Finding(
                name, "body", f"says `of {total}` but the guidebook has {len(pages)} steps"))

        for surface, match in (("rail", rail), ("mobile bar", mobile)):
            if match is None:
                findings.append(Finding(name, surface, "is absent from a step page"))
                continue
            stated = RAIL_STEP.search(_text(match.group(0)))
            if stated is None:
                findings.append(Finding(name, surface, "names no position"))
            elif (int(stated.group(1)), int(stated.group(2))) != (step, total):
                findings.append(Finding(
                    name, surface,
                    f"says {stated.group(1)} of {stated.group(2)}; the body says {step} of {total}"))

        if rail is None:
            continue
        entries = _rail_entries(rail.group(0))
        listing = [(href, title) for href, title, _ in entries]
        if reference is None:
            reference = listing
        elif listing != reference:
            findings.append(Finding(name, "rail", "lists a different walk than its sibling steps"))

        current = [href for href, _, is_current in entries if is_current]
        if len(current) != 1:
            findings.append(Finding(name, "rail", f"marks {len(current)} entries current, not 1"))
        elif current[0] != _route(page, build, base):
            findings.append(Finding(name, "rail", f"marks {current[0]} current, not this page"))

        for href, title, _ in entries:
            if href.split("#")[0] not in routes:
                findings.append(Finding(name, "rail", f"`{title}` links to {href}, which is not built"))

        for href in re.findall(r'<strong>Next:</strong>\s*<a href="([^"]*)"', text):
            target = href.split("#")[0]
            if target not in routes:
                findings.append(Finding(name, "body", f"onward link {href} does not resolve"))

    expected = set(range(1, len(pages) + 1))
    if declared and set(declared) != expected:
        findings.append(Finding(
            str(pages[0].parent.parent.relative_to(build)), "walk",
            f"steps are {sorted(declared)}, not {sorted(expected)}"))
    return findings


def main(argv: list[str]) -> int:
    """Sweep every guidebook in a built site."""
    build = Path(argv[1]) if len(argv) > 1 else REPO_ROOT / "build" / "docs"
    if not build.is_dir():
        print(f"check-guidebook-walk: not a directory: {build}", file=sys.stderr)
        return 2

    guidebooks: dict[Path, list[Path]] = {}
    for page in build.rglob("index.html"):
        if BODY_STEP.search(page.read_text(encoding="utf-8")):
            guidebooks.setdefault(page.parent.parent, []).append(page)
    if not guidebooks:
        print(f"check-guidebook-walk: no guidebook step found under {build}", file=sys.stderr)
        return 2

    base = site_base(build)
    findings = [f for pages in guidebooks.values() for f in check_guidebook(pages, build, base)]
    for finding in findings:
        print(finding.render())
    if findings:
        return 1
    total = sum(len(p) for p in guidebooks.values())
    print(f"check-guidebook-walk: OK ({len(guidebooks)} guidebook(s), {total} step(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
