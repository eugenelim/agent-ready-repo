"""Construction checks for documentation-entry navigation links.

This deliberately checks authored sources only. The site build mirrors guides
and pack READMEs into generated pages, so route existence is reconstructed from
those source trees rather than from generated output.
"""

from __future__ import annotations

import importlib.util
import re
import string
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).parent.parent
SITE_BASE = "/agent-ready-repo"
DOCS_BASE = f"{SITE_BASE}/docs"

DOC_SOURCES = (
    "README.md",
    "CONTRIBUTING.md",
    "guides/README.md",
    "guides/_shared/explanation/pack-catalogue.md",
    "docs-site/src/content/docs/index.mdx",
    "docs-site/src/content/docs/getting-started/index.mdx",
    "docs-site/src/content/docs/getting-started/install.md",
    "docs-site/src/content/docs/getting-started/three-loops.md",
    "docs/architecture/overview.md",
    "docs/specs/catalogue-wave8-readme-contributing/plan.md",
    "docs/specs/catalogue-wave8-readme-contributing/spec.md",
    "docs/specs/documentation-entry-navigation/spec.md",
    "docs/specs/documentation-entry-navigation/plan.md",
    "docs/specs/documentation-entry-navigation/notes/information-architecture.md",
    "docs/specs/documentation-entry-navigation/notes/verification.md",
)

MARKETING_SOURCES = (
    "web/src/components/layout/SiteNav.astro",
    "web/src/components/marketing/BuildYourOrg.astro",
    "web/src/components/marketing/Hero.astro",
    "web/src/components/marketing/PackCatalogue.astro",
    "web/src/pages/catalogue/index.astro",
    "web/src/pages/index.astro",
)

MARKDOWN_LINK_RE = re.compile(
    r"(?<!\!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)"
)
WITH_BASE_RE = re.compile(r"withBase\(['\"]([^'\"]+)['\"]\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
ID_RE = re.compile(r"id=[\"']([^\"']+)[\"']")


def _load_build_site():
    spec = importlib.util.spec_from_file_location(
        "build_site_entry_link_check", REPO_ROOT / "tools" / "build-site.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_site_entry_link_check"] = module
    spec.loader.exec_module(module)
    return module


BUILD_SITE = _load_build_site()


def _strip_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _split_anchor(raw: str) -> tuple[str, str | None]:
    target, _marker, anchor = raw.partition("#")
    return target, anchor or None


def _slugify(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[`*_{}\[\](),:]", "", text)
    text = text.strip().lower()
    keep = string.ascii_lowercase + string.digits + " -_"
    text = "".join(ch for ch in text if ch in keep)
    return re.sub(r"\s+", "-", text)


def _anchors_for(path: Path) -> set[str]:
    if path.is_dir():
        path = path / "README.md"
    if not path.exists() or path.suffix not in {".astro", ".md", ".mdx"}:
        return set()
    text = _strip_fences(path.read_text(encoding="utf-8"))
    return {_slugify(h) for h in HEADING_RE.findall(text)} | set(ID_RE.findall(text))


def _resolve_local(source: Path, target: str) -> Path | None:
    candidate = (source.parent / target).resolve()
    if candidate.exists():
        return candidate
    if target.endswith("/"):
        readme = candidate / "README.md"
        return readme if readme.exists() else None
    if candidate.suffix == "":
        for alt in (
            candidate / "README.md",
            candidate.with_suffix(".md"),
            candidate.with_suffix(".mdx"),
        ):
            if alt.exists():
                return alt
    return None


def _docs_routes() -> set[str]:
    routes = {DOCS_BASE, f"{DOCS_BASE}/"}
    docs_root = REPO_ROOT / "docs-site/src/content/docs"
    for source in docs_root.rglob("*"):
        if source.suffix not in {".md", ".mdx"}:
            continue
        rel = source.relative_to(docs_root)
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "index":
            parts = parts[:-1]
        route = f"{DOCS_BASE}/" + "/".join(parts)
        routes.add(route.rstrip("/"))
        routes.add(route.rstrip("/") + "/")

    guides_root = (REPO_ROOT / "guides").resolve()
    for source in guides_root.rglob("*.md"):
        route = BUILD_SITE._guide_site_url(source.resolve(), guides_root)
        routes.add(route.rstrip("/"))
        routes.add(route.rstrip("/") + "/")

    for source in (REPO_ROOT / "packs").glob("*/README.md"):
        slug = source.parent.name
        if slug.startswith("_"):
            continue
        routes.add(f"{DOCS_BASE}/packs/{slug}")
        routes.add(f"{DOCS_BASE}/packs/{slug}/")
    routes.add(f"{DOCS_BASE}/packs")
    routes.add(f"{DOCS_BASE}/packs/")
    return routes


def _web_routes() -> set[str]:
    routes = {SITE_BASE, f"{SITE_BASE}/", f"{SITE_BASE}/catalogue", f"{SITE_BASE}/catalogue/"}
    for source in (REPO_ROOT / "packs").glob("*/pack.toml"):
        slug = source.parent.name
        if not slug.startswith("_"):
            routes.add(f"{SITE_BASE}/packs/{slug}")
            routes.add(f"{SITE_BASE}/packs/{slug}/")
    return routes


def _homepage_anchors() -> set[str]:
    sources = (
        "web/src/pages/index.astro",
        "web/src/components/marketing/AdapterMatrix.astro",
        "web/src/components/marketing/BuildYourOrg.astro",
        "web/src/components/marketing/HumanGates.astro",
        "web/src/components/marketing/InstallTerminal.astro",
        "web/src/components/marketing/PackCatalogue.astro",
        "web/src/components/marketing/TheProblem.astro",
        "web/src/components/marketing/ThreeLoops.astro",
    )
    anchors: set[str] = set()
    for rel in sources:
        anchors |= _anchors_for(REPO_ROOT / rel)
    return anchors


def _check_site_route(
    route: str,
    anchor: str | None,
    docs_routes: set[str],
    web_routes: set[str],
    homepage_anchors: set[str],
) -> str | None:
    normalized = route.rstrip("/") or SITE_BASE
    if normalized.startswith(DOCS_BASE):
        if normalized not in {r.rstrip("/") for r in docs_routes}:
            return f"missing docs route {route}"
        return None
    if normalized not in {r.rstrip("/") for r in web_routes}:
        return f"missing web route {route}"
    if anchor and normalized == SITE_BASE and anchor not in homepage_anchors:
        return f"missing homepage anchor #{anchor}"
    return None


def test_changed_markdown_links_resolve() -> None:
    docs_routes = _docs_routes()
    web_routes = _web_routes()
    homepage_anchors = _homepage_anchors()
    failures: list[str] = []

    for rel in DOC_SOURCES:
        source = REPO_ROOT / rel
        content = _strip_fences(source.read_text(encoding="utf-8"))
        for raw in MARKDOWN_LINK_RE.findall(content):
            target, anchor = _split_anchor(raw)
            parsed = urlparse(target)
            if parsed.scheme in {"http", "https"}:
                if parsed.netloc != "eugenelim.github.io":
                    continue
                failure = _check_site_route(
                    parsed.path, anchor, docs_routes, web_routes, homepage_anchors
                )
                if failure:
                    failures.append(f"{rel}: {failure}")
                continue
            if target.startswith(("mailto:", "#")):
                if target.startswith("#") and target[1:] not in _anchors_for(source):
                    failures.append(f"{rel}: missing local anchor {target}")
                continue
            if target.startswith(SITE_BASE):
                failure = _check_site_route(
                    target, anchor, docs_routes, web_routes, homepage_anchors
                )
                if failure:
                    failures.append(f"{rel}: {failure}")
                continue

            resolved = _resolve_local(source, target)
            if resolved is None:
                failures.append(f"{rel}: missing local target {target}")
                continue
            if anchor and anchor not in _anchors_for(resolved):
                failures.append(
                    f"{rel}: missing anchor #{anchor} in {resolved.relative_to(REPO_ROOT)}"
                )

    assert not failures, "\n".join(failures)


def test_changed_marketing_routes_resolve() -> None:
    docs_routes = _docs_routes()
    web_routes = _web_routes()
    homepage_anchors = _homepage_anchors()
    failures: list[str] = []

    for rel in MARKETING_SOURCES:
        content = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for raw in WITH_BASE_RE.findall(content):
            target, anchor = _split_anchor(raw)
            route = SITE_BASE + target if target.startswith("/") else target
            failure = _check_site_route(
                route, anchor, docs_routes, web_routes, homepage_anchors
            )
            if failure:
                failures.append(f"{rel}: {failure}")

    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_") and callable(function):
            function()
    print("test-documentation-entry-links: all cases passed.")
