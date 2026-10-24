"""Contract tests for the Build a Catalogue sidebar group.

docs/specs/catalogue-wave6-technical-docs-ia, T2: AC-0002 pins the top-level
labels to the RFC 0076 D9 tree; every slug and link must resolve to a guide
source or a generated reference page.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDES = ROOT / "guides"
NAV = ROOT / "docs-site" / "src" / "build-a-catalogue-nav.json"
RFC = ROOT / "docs" / "rfc" / "0076-catalogue-contracts-composition-semantics-discovery.md"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


build_site = _load("build_site", ROOT / "tools" / "build-site.py")
sfr = _load("schema_field_reference", ROOT / "tools" / "schema_field_reference.py")


SPEC_LATEST_LINK = "/spec/catalogue/latest/"


def _nav() -> dict:
    return json.loads(NAV.read_text(encoding="utf-8"))


def _entries(node: dict):
    for item in node["items"]:
        if "items" in item:
            yield from _entries(item)
        else:
            yield item


def _d9_labels() -> list[str]:
    text = RFC.read_text(encoding="utf-8")
    section = text.split("### D9", 1)[1]
    fence = re.search(r"```\n(.*?)\n```", section, re.S)
    assert fence, "no fenced tree under ### D9"
    labels = []
    for line in fence.group(1).splitlines():
        m = re.match(r"\s*[├└]── (.*)", line)
        if m:
            labels.append(re.split(r"  |\(", m.group(1), maxsplit=1)[0].strip())
    return labels


def _guide_routes() -> set[str]:
    base = build_site.SITE_BASE + "/"
    routes = set()
    for src in GUIDES.rglob("*.md"):
        url = build_site._guide_site_url(src, GUIDES)
        routes.add(url.removeprefix(base).strip("/"))
    return routes


def _release_routes() -> set[str]:
    """The index and member page routes of every release row in the manifest."""
    inventory = _load("sync_contract_inventory", ROOT / "tools" / "catalogue" / "sync_contract_inventory.py")
    releases, _ = inventory.load_releases(ROOT / "contracts")
    routes: set[str] = set()
    for row in releases:
        routes.add(f"spec/catalogue/{row.version}")
        routes |= {
            f"spec/catalogue/{row.version}/{Path(key).name.replace('.', '-')}" for key in row.members
        }
    return routes


def _known_routes() -> set[str]:
    return (
        _guide_routes()
        | {p["slug"] for p in sfr.PAGES}
        | {SPEC_LATEST_LINK.strip("/")}
        | _release_routes()
    )


def test_top_level_labels_match_d9_tree():
    """AC-0002: the tab's top-level labels equal the RFC D9 tree, in order."""
    labels = [item["label"] for item in _nav()["items"]]
    assert len(labels) == 10
    assert labels == _d9_labels()


def test_contract_group_leads_with_the_latest_specification():
    """Catalogue spec release AC 17: the group's first item links latest/."""
    group = next(i for i in _nav()["items"] if i["label"] == "Contract and schema reference")
    assert group["items"][0] == {
        "label": "Catalogue specification",
        "link": SPEC_LATEST_LINK,
    }
    assert len(group["items"]) == 5  # latest/, three references, then the 0.1 release group


def test_every_release_has_its_pages_in_the_tab():
    """A release page left out of the nav would land the reader in the Docs tab."""
    slugs = {e["slug"] for e in _entries(_nav()) if "slug" in e}
    assert _release_routes() <= slugs


def test_every_slug_resolves():
    known = _known_routes()
    slugs = [e["slug"] for e in _entries(_nav()) if "slug" in e]
    assert slugs
    missing = [s for s in slugs if s not in known]
    assert not missing, missing


def test_every_link_path_resolves():
    known = _known_routes()
    links = [e["link"] for e in _entries(_nav()) if "link" in e]
    assert len(links) == 3
    for link in links:
        path = link.split("#", 1)[0].strip("/")
        assert path in known, link
