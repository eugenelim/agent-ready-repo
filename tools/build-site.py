#!/usr/bin/env python3
"""
Aggregate repo content into docs-site/src/content/docs/ for the Starlight build.

Copies:
  packs/*/README.md         → docs-site/src/content/docs/packs/<name>.md
  guides/**                 → docs-site/src/content/docs/guides/**
                              (README.md renamed to index.md; frontmatter injected)
  docs/product/changelog.md → docs-site/src/content/docs/changelog.md (links rewritten)
  CONTRIBUTING.md           → docs-site/src/content/docs/contributing.md (links rewritten)

Generates:
  docs-site/src/content/docs/packs/index.md  (pack catalogue summary page)

Usage:
  python tools/build-site.py
  python tools/build-site.py --dry-run
  python tools/build-site.py --clean
"""
import argparse
import json
import re
import shutil
import sys
import tomllib
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).parent.parent.resolve()
SITE_DOCS = REPO_ROOT / "docs-site" / "src" / "content" / "docs"
GITHUB_BASE = "https://github.com/eugenelim/agent-ready-repo/blob/main"
SITE_BASE = "/agent-ready-repo/docs"
NOW_PROJECTION = (
    REPO_ROOT / "web" / "src" / "lib" / "now-highlights.generated.json"
)
MARKETING_SHARED_CHROME_PROJECTION = (
    REPO_ROOT / "web" / "src" / "lib" / "shared-chrome.generated.json"
)
DOCS_SHARED_CHROME_PROJECTION = (
    REPO_ROOT / "docs-site" / "src" / "shared-chrome.generated.json"
)
# Seven calendar days ending on launch day, inclusive (brief decision 19): the
# launch date itself plus the six dates before it.
NOW_WINDOW_DAYS = 7

# Guide-specific frontmatter fields that are stripped before writing to the
# docs-site. These are understood by validate_guides.py but not by Starlight.
_GUIDE_ONLY_FIELDS = frozenset({
    "pack", "kind", "summary", "slug", "aliases", "status", "journey", "order",
})
_GUIDE_SLUG_PART_RE = re.compile(r"^[a-z0-9_][a-z0-9_-]*$")


# ---------------------------------------------------------------------------
# Shared chrome contract
# ---------------------------------------------------------------------------

_SHARED_CHROME_KINDS = frozenset({"internal", "external"})
_SHARED_CHROME_FIELDS = frozenset({
    "header", "docs_band", "docs_product_navigation", "destinations", "groups",
})
_SHARED_DESTINATION_FIELDS = frozenset({"id", "label", "target", "kind", "group"})
_SHARED_GROUP_FIELDS = frozenset({"id", "label", "destinations"})


def _shared_chrome_string(value: object, field: str, identifier: str) -> str:
    """Require a non-empty shared-chrome string field with its owning ID named."""
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"shared chrome {identifier} has invalid '{field}'; expected a non-empty string"
        )
    return value


def _validate_internal_shared_target(target: str, destination_id: str) -> None:
    """Require a safe root-relative page target or non-empty fragment target."""
    identifier = f"destination '{destination_id}'"
    if not target.startswith("/"):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "expected a root-relative target"
        )
    if target.startswith("//"):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "protocol-relative targets are not allowed"
        )
    if "\\" in target:
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "backslashes are not allowed"
        )
    if ".." in target:
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "parent-directory segments are not allowed"
        )
    if any(character.isspace() for character in target):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "whitespace is not allowed"
        )

    path, separator, fragment = target.partition("#")
    if separator:
        if "#" in fragment:
            raise ValueError(
                f"shared chrome {identifier} has invalid internal target {target!r}; "
                "expected at most one fragment"
            )
        if not fragment:
            raise ValueError(
                f"shared chrome {identifier} has invalid internal target {target!r}; "
                "fragment must be non-empty"
            )
        return
    if not path.endswith("/"):
        raise ValueError(
            f"shared chrome {identifier} has invalid internal target {target!r}; "
            "expected a '/'-terminated path or '#fragment' form"
        )


def _reject_shared_chrome_fields(
    record: dict, allowed: frozenset[str], identifier: str
) -> None:
    """Reject renderer presentation or state from the shared destination contract."""
    for field in record:
        if field not in allowed:
            raise ValueError(
                f"shared chrome {identifier} has unsupported field '{field}'; "
                "presentation and state belong to renderer-local components"
            )


def _validate_shared_chrome_destination_list(
    raw_destination_ids: object, field: str, destinations_by_id: dict[str, dict]
) -> list[str]:
    """Validate an ordered, duplicate-free list of declared destination IDs."""
    if not isinstance(raw_destination_ids, list):
        raise ValueError(
            f"site.toml shared_chrome.{field} must be an ordered destination ID array"
        )

    destination_ids: list[str] = []
    for raw_destination_id in raw_destination_ids:
        destination_id = _shared_chrome_string(raw_destination_id, field, field)
        if destination_id not in destinations_by_id:
            raise ValueError(
                f"shared chrome {field} references missing destination '{destination_id}'"
            )
        if destination_id in destination_ids:
            raise ValueError(
                f"shared chrome {field} repeats destination '{destination_id}'"
            )
        destination_ids.append(destination_id)
    return destination_ids


def validate_shared_chrome_contract(contract: object) -> dict:
    """Validate and normalize the renderer-neutral shared-chrome contract.

    The result contains only the fields a renderer may receive. Validation is
    deliberately complete before projection so malformed source cannot produce
    partial renderer data.
    """
    if not isinstance(contract, dict):
        raise ValueError("site.toml shared_chrome must be a table")
    _reject_shared_chrome_fields(contract, _SHARED_CHROME_FIELDS, "contract")

    raw_destinations = contract.get("destinations")
    raw_groups = contract.get("groups")
    raw_header = contract.get("header")
    raw_docs_band = contract.get("docs_band")
    raw_docs_product_navigation = contract.get("docs_product_navigation")
    if not isinstance(raw_destinations, list):
        raise ValueError("site.toml shared_chrome.destinations must be an ordered table array")
    if not isinstance(raw_groups, list):
        raise ValueError("site.toml shared_chrome.groups must be an ordered table array")

    destinations: list[dict] = []
    destinations_by_id: dict[str, dict] = {}
    for index, raw_destination in enumerate(raw_destinations):
        if not isinstance(raw_destination, dict):
            raise ValueError(f"shared chrome destination at position {index + 1} must be a table")
        raw_id = raw_destination.get("id")
        identifier = (
            f"destination '{raw_id}'"
            if isinstance(raw_id, str) and raw_id
            else f"destination at position {index + 1}"
        )
        _reject_shared_chrome_fields(
            raw_destination, _SHARED_DESTINATION_FIELDS, identifier
        )
        destination_id = _shared_chrome_string(raw_id, "id", identifier)
        if destination_id in destinations_by_id:
            raise ValueError(f"shared chrome duplicate destination ID '{destination_id}'")
        label = _shared_chrome_string(raw_destination.get("label"), "label", identifier)
        target = _shared_chrome_string(raw_destination.get("target"), "target", identifier)
        kind = _shared_chrome_string(raw_destination.get("kind"), "kind", identifier)
        if kind not in _SHARED_CHROME_KINDS:
            raise ValueError(
                f"shared chrome destination '{destination_id}' has unsupported kind "
                f"'{kind}'; expected 'internal' or 'external'"
            )
        if kind == "internal":
            _validate_internal_shared_target(target, destination_id)
        group = raw_destination.get("group")
        if group is not None and (not isinstance(group, str) or not group):
            raise ValueError(
                f"shared chrome destination '{destination_id}' has invalid 'group'; "
                "expected a non-empty group ID"
            )
        destination = {
            "id": destination_id,
            "label": label,
            "target": target,
            "kind": kind,
            "group": group,
        }
        destinations.append(destination)
        destinations_by_id[destination_id] = destination

    groups: list[dict] = []
    groups_by_id: dict[str, dict] = {}
    for index, raw_group in enumerate(raw_groups):
        if not isinstance(raw_group, dict):
            raise ValueError(f"shared chrome group at position {index + 1} must be a table")
        raw_id = raw_group.get("id")
        identifier = (
            f"group '{raw_id}'"
            if isinstance(raw_id, str) and raw_id
            else f"group at position {index + 1}"
        )
        _reject_shared_chrome_fields(raw_group, _SHARED_GROUP_FIELDS, identifier)
        group_id = _shared_chrome_string(raw_id, "id", identifier)
        if group_id in groups_by_id:
            raise ValueError(f"shared chrome duplicate group ID '{group_id}'")
        label = _shared_chrome_string(raw_group.get("label"), "label", identifier)
        raw_members = raw_group.get("destinations")
        if not isinstance(raw_members, list):
            raise ValueError(
                f"shared chrome group '{group_id}' has invalid 'destinations'; "
                "expected an ordered destination ID array"
            )
        members: list[str] = []
        for raw_member in raw_members:
            member = _shared_chrome_string(
                raw_member, "destinations", f"group '{group_id}'"
            )
            if member in members:
                raise ValueError(
                    f"shared chrome group '{group_id}' repeats destination '{member}'"
                )
            members.append(member)
        group = {"id": group_id, "label": label, "destinations": members}
        groups.append(group)
        groups_by_id[group_id] = group

    for group in groups:
        for member in group["destinations"]:
            destination = destinations_by_id.get(member)
            if destination is None:
                raise ValueError(
                    f"shared chrome group '{group['id']}' references missing "
                    f"destination '{member}'"
                )
            if destination["group"] != group["id"]:
                raise ValueError(
                    f"shared chrome destination '{member}' references group "
                    f"'{destination['group']}', not '{group['id']}'"
                )

    for destination in destinations:
        group_id = destination["group"]
        if group_id is None:
            continue
        if group_id not in groups_by_id:
            raise ValueError(
                f"shared chrome destination '{destination['id']}' references missing "
                f"group '{group_id}'"
            )
        if destination["id"] not in groups_by_id[group_id]["destinations"]:
            raise ValueError(
                f"shared chrome destination '{destination['id']}' references group "
                f"'{group_id}' but is missing from that group's destinations"
            )

    header = _validate_shared_chrome_destination_list(
        raw_header, "header", destinations_by_id
    )
    docs_band = _validate_shared_chrome_destination_list(
        raw_docs_band, "docs_band", destinations_by_id
    )
    docs_product_navigation = _validate_shared_chrome_destination_list(
        raw_docs_product_navigation, "docs_product_navigation", destinations_by_id
    )

    return {
        "header": header,
        "docs_band": docs_band,
        "docs_product_navigation": docs_product_navigation,
        "destinations": destinations,
        "groups": groups,
    }


def load_shared_chrome_contract(site_toml: Path) -> dict:
    """Load and validate the shared-chrome table from the site recipe."""
    with site_toml.open("rb") as f:
        site = tomllib.load(f)
    return validate_shared_chrome_contract(site.get("shared_chrome"))


def project_shared_chrome(contract: object) -> dict[str, dict]:
    """Create independent renderer-local data from one validated contract."""
    canonical = validate_shared_chrome_contract(contract)
    destinations_by_id = {
        destination["id"]: destination for destination in canonical["destinations"]
    }

    def link(destination_id: str) -> dict:
        destination = destinations_by_id[destination_id]
        return {
            "id": destination["id"],
            "label": destination["label"],
            "target": destination["target"],
            "kind": destination["kind"],
        }

    def footer_projection() -> list[dict]:
        return [
            {
                "id": group["id"],
                "label": group["label"],
                "destinations": [
                    link(destination_id) for destination_id in group["destinations"]
                ],
            }
            for group in canonical["groups"]
        ]

    marketing = {
        "header": [link(destination_id) for destination_id in canonical["header"]],
        "footer": footer_projection(),
    }
    docs = {
        "product_orientation_band": [
            link(destination_id) for destination_id in canonical["docs_band"]
        ],
        "product_navigation": [
            link(destination_id)
            for destination_id in canonical["docs_product_navigation"]
        ],
        "footer": footer_projection(),
    }

    return {"marketing": marketing, "docs": docs}


def generate_marketing_shared_chrome_projection(
    contract: object,
    output: Path = MARKETING_SHARED_CHROME_PROJECTION,
    dry_run: bool = False,
) -> dict:
    """Project the marketing chrome input before and after its site build."""
    payload = project_shared_chrome(contract)["marketing"]
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def assert_marketing_shared_chrome_projection_current(
    contract: object, output: Path = MARKETING_SHARED_CHROME_PROJECTION
) -> None:
    """Reject a committed marketing input that no longer matches ``site.toml``."""
    expected = project_shared_chrome(contract)["marketing"]
    actual = json.loads(output.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError(
            f"{output} is stale — run `python3 tools/build-site.py --journeys-only`"
        )


def generate_docs_shared_chrome_projection(
    contract: object,
    output: Path = DOCS_SHARED_CHROME_PROJECTION,
    dry_run: bool = False,
) -> dict:
    """Project the docs chrome input in the full pre-docs-build pass."""
    payload = project_shared_chrome(contract)["docs"]
    if not dry_run:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def assert_docs_shared_chrome_projection_current(
    contract: object, output: Path = DOCS_SHARED_CHROME_PROJECTION
) -> None:
    """Reject a committed docs input that no longer matches ``site.toml``."""
    expected = project_shared_chrome(contract)["docs"]
    actual = json.loads(output.read_text(encoding="utf-8"))
    if actual != expected:
        raise ValueError(
            f"{output} is stale — run `python3 tools/build-site.py`"
        )


def discover_packs(root: Path, site_toml: Path) -> list[dict]:
    """Return packs ordered by site.toml groups, ungrouped packs appended alphabetically.

    Each dict: {slug, display_name, version, scope, description, group}.
    """
    with site_toml.open("rb") as f:
        site = tomllib.load(f)
    groups = site.get("groups", [])

    packs_by_slug: dict[str, dict] = {}
    for pack_toml in sorted((root / "packs").glob("*/pack.toml")):
        slug = pack_toml.parent.name
        if slug.startswith("_"):
            continue
        with pack_toml.open("rb") as f:
            data = tomllib.load(f)
        p = data.get("pack", {})
        name = p.get("name", slug)
        display_name = p.get("display_name") or name.replace("-", " ").replace("_", " ").title()
        packs_by_slug[slug] = {
            "slug": slug,
            "display_name": display_name,
            "version": p.get("version", ""),
            "scope": p.get("install", {}).get("default-scope", "repo"),
            "description": p.get("description", ""),
            "group": None,
        }

    ordered: list[dict] = []
    grouped: set[str] = set()
    for group in groups:
        label = group.get("label")
        if not label:
            print("  warn  site.toml group missing 'label' — skipping", file=sys.stderr)
            continue
        for slug in group.get("packs", []):
            if slug not in packs_by_slug:
                print(
                    f"  warn  site.toml slug '{slug}' in group '{label}'"
                    f" has no packs/{slug}/pack.toml",
                    file=sys.stderr,
                )
                continue
            if slug not in grouped:
                packs_by_slug[slug]["group"] = label
                ordered.append(packs_by_slug[slug])
                grouped.add(slug)

    for slug in sorted(packs_by_slug):
        if slug not in grouped:
            print(
                f"  warn  pack '{slug}' not in any site.toml group — placed in 'Other'",
                file=sys.stderr,
            )
            packs_by_slug[slug]["group"] = "Other"
            ordered.append(packs_by_slug[slug])

    return ordered

# ---------------------------------------------------------------------------
# Frontmatter injection
# ---------------------------------------------------------------------------


def _inject_frontmatter(text: str, path: Path) -> str:
    """Prepend minimal Starlight frontmatter (title: ) if none present.

    Starlight's docsSchema() requires a `title` field. Files without YAML
    frontmatter get one derived from a leading H1 heading, or from the
    filename as a fallback.
    """
    if text.startswith("---"):
        return text  # already has frontmatter
    # Take the title from a *leading* H1 and strip that same heading, so
    # Starlight doesn't render it a second time beneath its own page title.
    heading = leading_h1(text)
    if heading is not None:
        title = heading.strip().replace('"', '\\"')
        body = _strip_leading_h1(text)
    else:
        print(
            f"  warn  {_relpath(path)}: no leading H1 — page title derived from "
            "the filename",
            file=sys.stderr,
        )
        title = path.stem.replace("-", " ").replace("_", " ").title()
        body = text
    return f'---\ntitle: "{title}"\n---\n\n' + body


# ---------------------------------------------------------------------------
# Guide frontmatter helpers (for catalogue-facing guide routing)
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a file's text; return {} if absent or invalid."""
    import yaml
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    yaml_block = text[3:end]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _normalise_guide_slug(
    value: object, source_path: Path | None = None, field: str = "slug"
) -> str | None:
    """Return a confined guide slug, or ``None`` when frontmatter is invalid."""
    if value is None:
        return None
    if not isinstance(value, str):
        if source_path is not None:
            print(
                f"  warn  {_relpath(source_path)}: non-string '{field}' ignored",
                file=sys.stderr,
            )
        return None

    slug = value.strip().strip("/")
    if slug.endswith("/index"):
        slug = slug[: -len("/index")]
    parts = slug.split("/")
    valid = (
        len(parts) >= 2
        and parts[0] == "guides"
        and all(_GUIDE_SLUG_PART_RE.fullmatch(part) for part in parts[1:])
    )
    if valid:
        return slug

    if source_path is not None:
        print(
            f"  warn  {_relpath(source_path)}: invalid '{field}' ignored",
            file=sys.stderr,
        )
    return None


# Counters for the two silent body/frontmatter transforms, reported alongside
# the per-stage counts the rest of this module prints. Without them, a change
# that stops the summary→description mapping firing would drop the meta
# description from 46 pages and leave the build green with nothing to compare.
_TRANSFORM_COUNTS = {"h1_stripped": 0, "summary_mapped": 0}

_LEADING_H1_RE = re.compile(r"\A#[ \t]+(.+?)[ \t]*(?:\n|\Z)")


def leading_h1(body: str) -> str | None:
    """Return the text of the body's *leading* ``# `` heading, or None.

    The single definition of "the page-title H1". ``tools/lint-guide-titles.py``
    imports this rather than re-deriving it: the lint's whole job is to guard an
    invariant this module defines, so a second copy of the rule could drift and
    the gate would stop guarding without failing.

    Anchored to the start deliberately. A free ``re.search`` for ``^# `` would
    also match a shell comment inside a fenced code block — there are 42 such
    lines across 14 guides — so it would promote a bash comment to the page
    title, and, worse, silently delete it from the code sample. Anchoring is
    what keeps this transform lossless.
    """
    m = _LEADING_H1_RE.match(body.lstrip("\n"))
    return m.group(1) if m else None


def _strip_leading_h1(body: str) -> str:
    """Drop a leading ``# `` heading so Starlight's title is the only H1.

    Starlight renders ``title:`` as the page ``<h1>``. A body H1 on top of that
    produces two — and, because the two strings are maintained independently,
    usually two *different* ones.
    """
    stripped = body.lstrip("\n")
    m = _LEADING_H1_RE.match(stripped)
    if not m:
        return body
    _TRANSFORM_COUNTS["h1_stripped"] += 1
    return stripped[m.end():].lstrip("\n")


def _strip_guide_metadata(text: str) -> str:
    """Remove guide-specific frontmatter fields before writing to the docs-site.

    Keeps Starlight-required/compatible fields (title, description, sidebar, etc.).
    Drops the body's leading H1 whenever the frontmatter carries a ``title``,
    which is the field Starlight renders as the page heading — keeping both
    produced 38 double-titled pages. A guide with frontmatter but no ``title``
    keeps its H1, because that heading is then the page's only title source.
    """
    import yaml
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    yaml_block = text[3:end]
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return text
    if not isinstance(data, dict):
        return text

    body = text[end + 4:]
    if data.get("title"):
        body = _strip_leading_h1(body)

    # `summary` is the guide-vocabulary name for what Starlight calls
    # `description`. Carry it across rather than dropping it with the other
    # guide-only fields: it feeds <meta name="description">, the search
    # snippet, and the rendered deck. An explicit `description` wins.
    if data.get("summary") and not data.get("description"):
        data = dict(data)
        data["description"] = str(data["summary"]).strip()
        _TRANSFORM_COUNTS["summary_mapped"] += 1

    # Exclude None values so yaml.safe_dump doesn't emit `key: null` noise.
    cleaned = {
        k: v for k, v in data.items()
        if k not in _GUIDE_ONLY_FIELDS and v is not None
    }
    if cleaned == {k: v for k, v in data.items() if v is not None}:
        # Frontmatter needs no rewrite; the body may still have lost its H1.
        return text[: end + 4] + "\n\n" + body.lstrip("\n")

    # Reconstruct frontmatter
    if not cleaned:
        # All fields were guide-only; keep an empty frontmatter block so Starlight
        # doesn't inject a duplicate title from H1 (injection only fires when no ---)
        return "---\n---\n\n" + body.lstrip("\n")

    fm_body = yaml.safe_dump(
        cleaned, default_flow_style=False, sort_keys=False, allow_unicode=True,
    ).rstrip("\n")
    fm_text = "---\n" + fm_body + "\n---"
    return fm_text + "\n\n" + body.lstrip("\n")


def _make_redirect_stub(target_url: str) -> str:
    """Generate a Starlight-compatible page with a meta-refresh redirect."""
    return (
        '---\ntitle: "Redirecting..."\n---\n\n'
        f'<meta http-equiv="refresh" content="0; url={target_url}">\n\n'
        f'This page has moved. [Click here]({target_url}) '
        "if you are not redirected automatically.\n"
    )


# ---------------------------------------------------------------------------
# Guide inventory — the collate step that precedes projection.
# Contract: docs/specs/guides-sidebar-generation/spec.md § Layer 1
# ---------------------------------------------------------------------------

VALID_GUIDE_KINDS = frozenset({"tutorial", "how-to", "reference", "explanation"})

# The on-disk directory is plural; contracts/guide.schema.json's enum is
# singular. Without this, the first page under tutorials/ to gain frontmatter
# splits its pack into a "Tutorial" bucket and a "Tutorials" bucket.
_KIND_DIR_ALIASES = {"tutorials": "tutorial"}

# Maintainer context. Still mirrored — so still reachable by URL — but never
# surfaced in reader navigation.
_NAV_INELIGIBLE_NAMES = frozenset({"AGENTS.md"})


def guide_slug_for(rel_parts: list[str]) -> str:
    """Starlight slug of the file ``mirror_guides`` writes for these parts.

    ``mirror_guides`` renames ``README.md`` to ``index.md`` before deriving its
    ``canonical_slug``, so a pack README's canonical slug is
    ``guides/<pack>/index``. Starlight serves that at ``guides/<pack>``, which
    is the value navigation needs — hence the trailing ``/index`` strip.
    """
    parts = list(rel_parts)
    if parts[-1] == "README.md":
        parts[-1] = "index.md"
    if parts[-1].endswith(".md"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "index":
        parts.pop()
    return "guides/" + "/".join(parts) if parts else "guides"


def build_guide_inventory(guides_root: Path, enumerator=None) -> list[dict]:
    """Collate every ``.md`` file under ``guides_root`` into one record each.

    Path structure is the source and frontmatter refines it: most guides carry
    no frontmatter, so a frontmatter-sourced inventory would omit them.

    ``enumerator`` is the determinism seam — a callable taking the root and
    returning an iterable of paths. Output order does not depend on it; the
    records are sorted by slug before returning.
    """
    paths = enumerator(guides_root) if enumerator else guides_root.rglob("*.md")

    records: list[dict] = []
    for path in paths:
        if path.suffix != ".md" or not path.is_file():
            continue
        rel_parts = list(path.relative_to(guides_root).parts)
        fm = _parse_frontmatter(path.read_text(encoding="utf-8"))

        # A file directly under guides/ has no pack segment — the root README
        # belongs to the tree itself, not to a pack called "README.md".
        pack = rel_parts[0] if len(rel_parts) > 1 else None

        kind = fm.get("kind") if fm.get("kind") in VALID_GUIDE_KINDS else None
        if kind is None and len(rel_parts) >= 3:
            candidate = _KIND_DIR_ALIASES.get(rel_parts[1], rel_parts[1])
            kind = candidate if candidate in VALID_GUIDE_KINDS else None

        # bool is an int subclass; a YAML `order: true` must not sort as 1.
        raw_order = fm.get("order")
        is_int = isinstance(raw_order, int) and not isinstance(raw_order, bool)
        order = raw_order if is_int else None

        # Frontmatter is adopter-authored: invalid route metadata must degrade
        # to the derived value, not crash or write outside the guide route tree.
        override = _normalise_guide_slug(fm.get("slug"), path)

        title = fm.get("title") or None
        if title is not None and not isinstance(title, str):
            print(f"  warn  {_relpath(path)}: non-string 'title' ignored", file=sys.stderr)
            title = None

        # Every navigation exclusion is announced — a silently missing page is
        # the defect this whole change exists to remove.
        is_section_index = path.name == "README.md" and len(rel_parts) >= 3
        nav_eligible = path.name not in _NAV_INELIGIBLE_NAMES and not is_section_index
        if not nav_eligible:
            why = ("section index (README more than one directory below guides/)"
                   if is_section_index else "maintainer context")
            print(f"  note  {_relpath(path)}: {why}; mirrored but not in navigation",
                  file=sys.stderr)

        records.append({
            "source_path": path,
            "pack": pack,
            "kind": kind,
            "order": order,
            "title": title,
            "slug": override or guide_slug_for(rel_parts),
            "is_index": path.name == "README.md",
            # A README below kind level is a section-authoring template
            # ("Writing a how-to"), addressed to whoever writes the guides — not
            # to the adopter this tree serves. None was in the pre-change
            # sidebar, so keeping them out preserves the status quo.
            "nav_eligible": nav_eligible,
        })

    # Secondary key on the path: a duplicate slug would otherwise resolve by
    # enumerator arrival order, breaking determinism.
    records.sort(key=lambda r: (r["slug"], str(r["source_path"])))

    # A repeated slug renders twice and orders by enumerator arrival, which
    # would break determinism. Set-equality tests cannot see it.
    seen: dict[str, Path] = {}
    for rec in records:
        if rec["slug"] in seen:
            print(
                f"  warn  duplicate guide slug '{rec['slug']}':"
                f" {_relpath(rec['source_path'])} also claimed by"
                f" {_relpath(seen[rec['slug']])}",
                file=sys.stderr,
            )
        seen[rec["slug"]] = rec["source_path"]

    return records


# ---------------------------------------------------------------------------
# Guide sidebar projection — inventory becomes Starlight groups.
# Contract: docs/specs/guides-sidebar-generation/spec.md § Layer 2
# ---------------------------------------------------------------------------

# Reader-visible bucket labels, in the canonical sequence.
_KIND_BUCKETS = (
    ("tutorial", "Tutorials"),
    ("how-to", "How-to"),
    ("reference", "Reference"),
    ("explanation", "Explanation"),
)


def _guide_label(record: dict, baseline: dict) -> str:
    """Resolve a sidebar label: frozen baseline, then the page's own title,
    then the filename.

    Baseline first is deliberate. Thirteen pages carry a ``title:`` that differs
    from the label they show in navigation today, so putting frontmatter first
    would rewrite them silently. Removing a baseline entry is the reviewable act
    that adopts a page's own title.
    """
    if record["slug"] in baseline:
        return baseline[record["slug"]]
    if record["title"]:
        return record["title"]
    if record["is_index"]:
        # Filename derivation would read "Readme"; every index entry in the
        # pre-change tree reads "Overview".
        return "Overview"
    return record["slug"].rsplit("/", 1)[-1].replace("-", " ").title()


def project_guide_sidebar(records: list[dict], guide_groups: list[dict],
                          baseline: dict) -> dict:
    """Project inventory records into the Starlight ``Guides`` sidebar group.

    Emission order within a pack group is fixed: index pages, then records
    declaring ``order`` (ascending, across kinds), then kind-less non-index
    records, then the kind buckets in canonical sequence.
    """
    eligible = [r for r in records if r["nav_eligible"]]

    # Warn and skip on a malformed entry rather than raising a bare KeyError
    # mid-build, matching discover_packs()'s handling of the sibling table.
    valid_groups = []
    for i, g in enumerate(guide_groups):
        if not g.get("dir") or not g.get("label"):
            print(
                f"  warn  site.toml [[guide_groups]] entry {i} missing 'dir' or"
                " 'label' — skipping",
                file=sys.stderr,
            )
            continue
        valid_groups.append(g)

    declared = [g["dir"] for g in valid_groups]
    labels = {g["dir"]: g["label"] for g in valid_groups}
    # An undeclared directory still gets a group rather than vanishing.
    extra = sorted({r["pack"] for r in eligible if r["pack"] and r["pack"] not in labels})
    for d in extra:
        labels[d] = d.replace("-", " ").replace("_", " ").strip().title()

    items: list[dict] = []

    # Files directly under guides/ belong to the tree itself, not to any pack.
    # Index first, then any other loose page — otherwise a future
    # guides/CONTRIBUTING.md would be eligible and emitted nowhere.
    root_level = [r for r in eligible if r["pack"] is None]
    for rec in sorted(root_level, key=lambda r: (not r["is_index"], r["slug"])):
        items.append({"label": _guide_label(rec, baseline), "slug": rec["slug"]})

    for pack in [d for d in declared if d in {r["pack"] for r in eligible}] + extra:
        members = [r for r in eligible if r["pack"] == pack]
        group_items: list[dict] = []

        def entry(r):
            return {"label": _guide_label(r, baseline), "slug": r["slug"]}

        for rec in sorted((r for r in members if r["is_index"]), key=lambda r: r["slug"]):
            group_items.append(entry(rec))
        for rec in sorted((r for r in members if r["order"] is not None and not r["is_index"]),
                          key=lambda r: (r["order"], r["slug"])):
            group_items.append(entry(rec))
        for rec in sorted((r for r in members
                           if r["order"] is None and not r["is_index"] and r["kind"] is None),
                          key=lambda r: r["slug"]):
            group_items.append(entry(rec))

        for kind, bucket_label in _KIND_BUCKETS:
            bucket = [r for r in members
                      if r["kind"] == kind and r["order"] is None and not r["is_index"]]
            if not bucket:
                continue
            bucket.sort(key=lambda r: (_guide_label(r, baseline).casefold(), r["slug"]))
            group_items.append({
                "label": bucket_label,
                "items": [entry(r) for r in bucket],
            })

        if group_items:
            items.append({"label": labels[pack], "items": group_items})

    return {"label": "Guides", "items": items}


# ---------------------------------------------------------------------------
# Guide-aware mirror (replaces the bare mirror_dir call for guides/)
# ---------------------------------------------------------------------------

def mirror_guides(src: Path, site_docs: Path, dry_run: bool = False) -> int:
    """Mirror src/ into site_docs/guides/ with frontmatter-aware routing.

    - Files with ``slug:`` frontmatter are written to site_docs/<slug>.md
      (overriding the default path-based placement).
    - Files with ``aliases:`` frontmatter get meta-refresh redirect stubs.
    - Guide-specific metadata (pack, kind, summary, slug, aliases, status,
      journey, order) is stripped before writing so Starlight doesn't see it.
    - Files without frontmatter receive the existing title-injection treatment.
    - docs/guides/ is not the src here and is never mirrored.
    """
    guides_out = site_docs / "guides"
    count = 0
    if not src.exists():
        src_display = (
            src.relative_to(REPO_ROOT) if src.is_relative_to(REPO_ROOT) else src
        )
        print(f"  warn  source dir missing: {src_display}", file=sys.stderr)
        return 0
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        rel_parts = list(rel.parts)
        if rel_parts[-1] == "README.md":
            rel_parts[-1] = "index.md"

        if path.suffix != ".md":
            target = guides_out / Path(*rel_parts)
            if dry_run:
                print(f"  copy  {_relpath(path)} → {_relpath(target)}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            count += 1
            continue

        text = path.read_text(encoding="utf-8")
        text = _rewrite_guide(text, path)
        fm = _parse_frontmatter(text)

        # Determine canonical slug and output path
        override = _normalise_guide_slug(fm.get("slug"), path) if fm else None
        if override:
            canonical_slug = override
            target = site_docs / (canonical_slug + ".md")
        else:
            # Derive slug from the (possibly renamed) relative parts
            slug_parts = list(rel_parts)
            if slug_parts[-1].endswith(".md"):
                slug_parts[-1] = slug_parts[-1][:-3]
            canonical_slug = "guides/" + "/".join(slug_parts)
            target = guides_out / Path(*rel_parts)

        # Strip guide-specific metadata; fall through to title injection if needed
        if fm:
            text = _strip_guide_metadata(text)

        if not text.startswith("---"):
            text = _inject_frontmatter(text, path)

        if dry_run:
            action = "rename" if path.name == "README.md" else "copy"
            if override:
                action = "route"
            print(f"  {action} {_relpath(path)} → {_relpath(target)}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        count += 1

        # Generate redirect stubs for aliases
        aliases = fm.get("aliases") if fm else None
        if isinstance(aliases, list):
            canonical_url = f"{SITE_BASE}/{canonical_slug}/"
            for alias in aliases:
                alias_slug = _normalise_guide_slug(alias, path, "aliases")
                if not alias_slug:
                    continue
                stub_target = site_docs / (alias_slug + ".md")
                stub_content = _make_redirect_stub(canonical_url)
                if dry_run:
                    print(f"  stub  {alias_slug} → {canonical_slug}")
                else:
                    stub_target.parent.mkdir(parents=True, exist_ok=True)
                    stub_target.write_text(stub_content, encoding="utf-8")
        elif aliases is not None:
            print(
                f"  warn  {_relpath(path)}: non-list 'aliases' ignored",
                file=sys.stderr,
            )

    return count


def _relpath(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except ValueError:
        return str(p)


# ---------------------------------------------------------------------------
# Link rewriters
# ---------------------------------------------------------------------------

def _strip_md_suffixes(text: str) -> str:
    """Strip .md suffixes from intra-site markdown links.

    Starlight serves content at clean URLs (no .md). Links like
    [label](other-file.md) and [label](path/README.md) must become
    [label](other-file/) and [label](path/) so they resolve correctly.

    External links (http/https) are never touched.
    """
    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        # Skip external links and anchor-only links
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        if path.endswith(".md"):
            # README.md → ../../ style; otherwise strip .md, add /
            if path.endswith("/README.md"):
                path = path[: -len("README.md")]  # e.g. "foo/README.md" → "foo/"
            elif path == "README.md":
                path = "./"
            else:
                path = path[:-3] + "/"  # strip .md, add /
        return f"{prefix}{path}{anchor})"

    return re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)


def _rewrite_changelog(text: str) -> str:
    """Fix links in changelog.md when moved from docs/product/ to docs-site content.

    In source: relative to docs/product/changelog.md
      ../guides/... → base-qualified technical guide route
      ../rfc/...    → GitHub URL  (not in site)
      ../specs/...  → GitHub URL  (not in site)
    """
    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if path.startswith("../guides/"):
            return f"{prefix}{SITE_BASE}/{path[3:]}{anchor})"
        if path.startswith("../"):
            # Convert to GitHub URL
            clean = path[3:]  # remove ../
            return f"{prefix}{GITHUB_BASE}/{clean}{anchor})"
        return m.group(0)

    result = re.sub(r"(\]\()(\.\./[^)#]*)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _rewrite_pack_readme(text: str, pack_src_path: Path) -> str:
    """Rewrite links in pack READMEs moved from packs/<slug>/README.md
    to docs-site/src/content/docs/packs/<slug>.md.

    Pack-home links (../other-pack/README.md) → base-qualified pack route.
    Other repository files, including files beside the README → GitHub URL.
    """
    packs_root = (REPO_ROOT / "packs").resolve()
    repo_root = REPO_ROOT.resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        try:
            resolved = (pack_src_path.parent / path).resolve()
        except Exception:
            return m.group(0)

        if _is_relative_to(resolved, packs_root):
            # A pack README is served at /docs/packs/<slug>/, so a bare sibling
            # slug would incorrectly nest below the current pack route.
            rel = resolved.relative_to(packs_root)
            pack_name = rel.parts[0]
            if resolved.is_dir() or rel.parts[1:] == ("README.md",):
                return f"{prefix}{SITE_BASE}/packs/{pack_name}/{anchor})"
            repo_rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{repo_rel}{anchor})"

        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _rewrite_guide(text: str, guide_src_path: Path) -> str:
    """Rewrite links in guide files that exit the guides tree.

    Links within guides/ are normalised to relative Starlight URLs.
    Links that resolve within the repo but outside guides/ are
    converted to GitHub URLs so they don't produce dead references.
    """
    guides_root = (REPO_ROOT / "guides").resolve()
    repo_root = REPO_ROOT.resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)

        # Resolve the link relative to the guide file's source position
        try:
            resolved = (guide_src_path.parent / path).resolve()
        except Exception:
            return m.group(0)

        # Within guides/ → route to the mirrored page from the docs root.
        # A relative source link cannot be preserved: Starlight serves each
        # Markdown file as a directory route, so `sibling.md` from
        # `/guide-name/` would incorrectly become `/guide-name/sibling/`.
        if _is_relative_to(resolved, guides_root) and resolved.exists():
            site_url = _guide_site_url(resolved, guides_root)
            return f"{prefix}{site_url}{anchor})"
        # Stale link within guides/ — fall through

        # Within repo but outside guides/ → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


def _guide_site_url(path: Path, guides_root: Path) -> str:
    """Return the base-qualified technical-doc URL for a guide source path."""
    source = path / "README.md" if path.is_dir() else path
    rel = source.relative_to(guides_root)

    if source.suffix == ".md" and source.exists():
        frontmatter = _parse_frontmatter(source.read_text(encoding="utf-8"))
        slug = _normalise_guide_slug(frontmatter.get("slug"), source)
        if not slug:
            parts = list(rel.parts)
            if parts[-1] == "README.md":
                parts = parts[:-1]
            else:
                parts[-1] = Path(parts[-1]).stem
            slug = "/".join(("guides", *parts))
        return f"{SITE_BASE}/{slug}/"

    return f"{SITE_BASE}/guides/{rel.as_posix()}"


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _rewrite_contributing(text: str) -> str:
    """Fix links in CONTRIBUTING.md when placed at docs-site content root.

    CONTRIBUTING.md lives at the repo root; links are repo-root-relative.
    Most targets (AGENTS.md, docs/CONVENTIONS.md, etc.) aren't in the site,
    so we convert them to GitHub URLs using proper Path resolution.
    """
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    repo_root = REPO_ROOT.resolve()
    guides_root = (REPO_ROOT / "guides").resolve()

    def replace(m: re.Match) -> str:
        prefix, path, anchor = m.group(1), m.group(2), m.group(3) or ""
        if not path or path.startswith(("http://", "https://", "#")):
            return m.group(0)
        try:
            resolved = (contributing_src.parent / path).resolve()
        except Exception:
            return m.group(0)

        # Links within guides/ → base-qualified mirrored guide route.
        # CONTRIBUTING is served from /docs/contributing/, so a `guides/...`
        # href would otherwise nest under that page.
        if _is_relative_to(resolved, guides_root) and resolved.exists():
            site_url = _guide_site_url(resolved, guides_root)
            return f"{prefix}{site_url}{anchor})"

        # Any other repo-relative link → GitHub URL
        if _is_relative_to(resolved, repo_root):
            rel = resolved.relative_to(repo_root)
            return f"{prefix}{GITHUB_BASE}/{rel}{anchor})"

        return m.group(0)

    result = re.sub(r"(\]\()([^)#\"'\s]+)(#[^)]+)?\)", replace, text)
    return _strip_md_suffixes(result)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def copy_file(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> None:
    """Copy src to dst, applying an optional rewriter(text) → text transform.

    For .md files, injects Starlight frontmatter (title:) if none present.
    """
    if dry_run:
        print(f"  copy  {src.relative_to(REPO_ROOT)} → {dst.relative_to(REPO_ROOT)}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    text = src.read_text(encoding="utf-8")
    if rewriter:
        text = rewriter(text)
    if dst.suffix == ".md" and not text.startswith("---"):
        text = _inject_frontmatter(text, src)
    dst.write_text(text, encoding="utf-8")


def mirror_dir(src: Path, dst: Path, rewriter=None, dry_run: bool = False) -> int:
    """Mirror src into dst, applying an optional per-file rewriter to .md files.

    README.md files are renamed to index.md to preserve directory-index URLs
    in Starlight (prevents /guides/core/readme/ instead of /guides/core/).
    Starlight frontmatter (title:) is injected into .md files that lack it.
    """
    count = 0
    if not src.exists():
        print(f"  warn  source dir missing: {src.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 0
    for path in sorted(src.rglob("*")):
        if path.is_file():
            rel = path.relative_to(src)
            # Rename README.md → index.md to preserve Starlight directory-index URLs
            rel_parts = list(rel.parts)
            if rel_parts[-1] == "README.md":
                rel_parts[-1] = "index.md"
            target = dst / Path(*rel_parts)
            if dry_run:
                action = "rename" if path.name == "README.md" else "copy"
                print(
                    f"  {action} {path.relative_to(REPO_ROOT)}"
                    f" → {target.relative_to(REPO_ROOT)}"
                )
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if path.suffix == ".md":
                    text = path.read_text(encoding="utf-8")
                    if rewriter:
                        text = rewriter(text, path)
                    if not text.startswith("---"):
                        text = _inject_frontmatter(text, path)
                    target.write_text(text, encoding="utf-8")
                else:
                    shutil.copy2(path, target)
            count += 1
    return count


def build_pack_index(packs: list[dict], out_dir: Path, dry_run: bool = False) -> None:
    header = (
        '---\ntitle: "Pack Catalogue"\n'
        f'description: "{len(packs)} curated packs for the AI operating model."\n'
        "---\n\n"
        # No body H1 — Starlight renders `title:` as the page heading.
        f"{len(packs)} curated packs — each distilled from the best practices of its discipline\n"
        "through practitioner research and RFC-and-ADR governance.\n\n"
        "Install any pack in one command:\n\n"
        "```bash\n"
        "agentbundle install --pack <name>               # repo scope (default)\n"
        "agentbundle install --pack <name> --scope user  # user scope\n"
        "```\n\n"
        "| Pack | Scope | Description |\n"
        "|---|---|---|\n"
    )
    lines = [header]
    for p in packs:
        lines.append(
            f"| [**{p['display_name']}**]({p['slug']}/) |"
            f" `{p['scope']}` | {p['description']} |\n"
        )

    content = "".join(lines)
    index_md = out_dir / "index.md"
    if dry_run:
        print(f"  gen   docs-site/src/content/docs/packs/index.md ({len(content)} bytes)")
    else:
        index_md.write_text(content, encoding="utf-8")


def _fm_split(text: str) -> tuple[str, str]:
    """Return (frontmatter_body, rest). Empty string if no frontmatter block."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def _fm_scalar(fm: str, key: str) -> str | None:
    """Extract a simple scalar value from raw frontmatter text."""
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.MULTILINE)
    return m.group(1).strip() if m else None


def _inject_generated_marker(text: str) -> str:
    """Inject or set generated: true in the JOURNEY.md frontmatter block."""
    if not text.startswith("---\n"):
        return text
    fm_end = text.find("\n---", 3)
    if fm_end == -1:
        return text
    fm = text[3:fm_end]
    if re.search(r"^generated:", fm, re.MULTILINE):
        fm = re.sub(r"^generated:.*$", "generated: true", fm, flags=re.MULTILINE)
        return "---" + fm + text[fm_end:]
    return "---\ngenerated: true" + text[3:]


def sync_pack_journeys(
    packs_dir: Path,
    journey_dir: Path,
    dry_run: bool = False,
) -> int:
    """Generate central journey files from packs/*/JOURNEY.md.

    Performs dual-ownership checks before writing. Returns count of files synced.
    """
    sources = sorted(packs_dir.glob("*/JOURNEY.md"))
    if not sources:
        return 0

    central: dict[str, tuple[str, str]] = {}
    if journey_dir.exists():
        for jf in journey_dir.glob("*.md"):
            cfm, _ = _fm_split(jf.read_text(encoding="utf-8"))
            central[jf.stem] = (
                _fm_scalar(cfm, "pack") or "",
                _fm_scalar(cfm, "generated") or "",
            )

    count = 0
    for src in sources:
        pack_name = src.parent.name
        text = src.read_text(encoding="utf-8")
        fm, _ = _fm_split(text)

        journey_id = _fm_scalar(fm, "journey_id")
        if not journey_id:
            print(f"error  {src}: missing journey_id — cannot sync", file=sys.stderr)
            sys.exit(1)

        for stem, (cf_pack, cf_generated) in central.items():
            if cf_generated == "true":
                continue
            if stem == journey_id:
                print(
                    f"error  dual canonical ownership: {src} (journey_id={journey_id!r})"
                    f" and non-generated central file '{stem}.md' share the same slug",
                    file=sys.stderr,
                )
                sys.exit(1)
            if cf_pack == pack_name:
                print(
                    f"error  dual canonical ownership: {src} and non-generated"
                    f" central file '{stem}.md' both claim pack {pack_name!r}",
                    file=sys.stderr,
                )
                sys.exit(1)

        target = journey_dir / f"{journey_id}.md"
        out_text = _inject_generated_marker(text)

        if dry_run:
            print(
                f"  sync  {src.relative_to(REPO_ROOT)}"
                f" → {target.relative_to(REPO_ROOT)}"
            )
        else:
            journey_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(out_text, encoding="utf-8")
            print(
                f"  sync  {src.relative_to(REPO_ROOT)}"
                f" → {target.relative_to(REPO_ROOT)}"
            )
        count += 1

    return count


# ---------------------------------------------------------------------------
# Released changelog Highlights → the public /now/ projection.
#
# `spec/site-now-surface`. The only content source is an optional `Highlights`
# subsection of an existing `docs/product/changelog.md` release entry. Two rules
# make an entry eligible, and both are structural rather than textual:
#
#   1. it carries a package/version identity AND a release date, and
#   2. it is not beneath an `[Unreleased]` heading.
#
# Rule 2 is relative, not positional. `changelog.md` currently holds three
# separate `## [Unreleased]` regions, and the newest release-shaped entries are
# nested *inside* the first one as `###` children. A date beneath `Unreleased`
# does not make an entry released — the spec is explicit that Unreleased content
# never projects "even if they contain Highlights" — so eligibility has to be
# decided by enclosing structure. An `Unreleased` heading at level N opens a
# region that every following heading deeper than N belongs to; the region ends
# at the next heading of level N or shallower.
#
# The projection is pure: same source bytes in, same JSON out, no clock, no
# network, no model. `--now-date` supplies the launch day so a fixture can pin
# the window instead of drifting with the calendar.
# ---------------------------------------------------------------------------

_CHANGELOG_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
# Any heading that says "unreleased" and is not itself a release entry opens an
# Unreleased region. Deliberately broad, and it FAILS CLOSED.
#
# Three narrower rules were tried and each leaked. An exact `^\[?unreleased\]?$`
# anchor missed `## [Unreleased] — 2026-08-18`. Adding `(?:\W|$)` still missed
# `## (Unreleased)`, `## **Unreleased**`, `## _Unreleased_`, `## 🚧 Unreleased`,
# `## — Unreleased —` and `## Next (unreleased)`. Leading-token matching misses
# the last of those. In every miss the region was recorded as RELEASED and every
# dated child beneath it published — and the emitted vocabulary check cannot see
# it, because the leaked bullet need not contain the word "unreleased" at all.
#
# The two error directions are not symmetric. A false positive withholds content
# from `/now/`, which the generation report names out loud and an author fixes by
# rewording a heading. A false negative publishes in-progress work, which the
# spec forbids outright. So this errs toward withholding.
_UNRELEASED_RE = re.compile(r"unreleased", re.IGNORECASE)
# `[core][2.7.4] and [architect][0.14.5] — 2026-08-17` — one entry may release
# several packages at once, so identity is a list, not a scalar.
_RELEASE_PKG_RE = re.compile(r"\[([A-Za-z0-9][A-Za-z0-9._-]*)\]\[([^\]]+)\]")
# The pair must LEAD the heading. Markdown reference links share the `[a][b]`
# shape, so searching anywhere makes ordinary prose look like a release:
# `## Thanks to [everyone][credits] who filed issues` and
# `## Migrating from [v1][v1-docs] to [v2][v2-docs]` each hard-failed the whole
# site build before this was anchored.
_RELEASE_LEAD_RE = re.compile(r"^\[([A-Za-z0-9][A-Za-z0-9._-]*)\]\[([^\]]+)\]")
_RELEASE_DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s*$")
_HIGHLIGHTS_RE = re.compile(r"^highlights$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^[ \t]*[-*+][ \t]+(.*)$")
# Two orthogonal rules, and conflating them cost a regression each way.
#
# 1. Capture the marker CHARACTER and run LENGTH. A bare `(```|~~~)` closes a
#    ````-fenced block on the ``` inside it, and the trailing markers then
#    restore parity so the unterminated-fence raise never fires — sample content
#    publishes as a real release.
# 2. Keep the leading-whitespace allowance permissive. Tightening it to
#    `^ {0,3}` while fixing (1) lost 4-space-indented fences, so a sample nested
#    under a list item stopped being skipped and its ```bash lines published as
#    highlight prose. Being permissive here fails closed: more content skipped,
#    never less.
_FENCE_RE_CHANGELOG = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")


# `_backtick_runs` and the run-pairing rule below are COPIED from
# packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py:158
# (`_code_span_ranges`), not imported: tools/ must not couple to a
# content-pinned, independently versioned pack tree. Copied as a run scanner
# plus an interleaved pairing step rather than as one whole-line helper,
# because a whole-line span list cannot express "a comment's interior
# contributes no delimiters" -- see `_strip_changelog_comments`. The pairing
# is also precomputed here instead of probed per run: upstream's probe loop
# rescans on every unmatched run, measured 0.46 s against this file's 0.17 s
# on 2,000 strictly-increasing runs.
def _backtick_runs(line: str) -> list[tuple[int, int]]:
    """Every maximal backtick run on one line, as ``(start, length)``.

    Split out of `_code_span_ranges` so the comment stripper can pair runs
    lazily. The scan itself is unchanged.
    """
    runs: list[tuple[int, int]] = []
    index, length = 0, len(line)
    while index < length:
        if line[index] == "`":
            end = index
            while end < length and line[end] == "`":
                end += 1
            runs.append((index, end - index))
            index = end
        else:
            index += 1
    return runs


def _strip_changelog_comments(line: str) -> tuple[str, bool]:
    r"""Strip real HTML comments and report an unclosed opener on this line.

    ONE left-to-right pass in which comment detection and code-span pairing
    interleave; whichever construct starts earlier at the cursor consumes its
    extent. An opener inside a code span is a mention. Once a real opener is
    found, its closer search is code-span blind -- Markdown is not parsed
    inside an HTML comment.

    The interleaving is the correctness argument, and two earlier shapes got it
    wrong in ways worth naming, because both looked right:

    1. Pair over the WHOLE line, then mask openers that fall inside a span. A
       backtick inside one real comment paired with a backtick inside the NEXT
       one; the bogus span covered the second comment's opener, so it read as a
       mention and its body published. Measured leak:
       ``- Ship it <!-- don`t publish --> <!-- TODO: internal `note` -->``.
    2. Same, plus discarding spans that start before the current segment. That
       stops a comment interior CREATING a bogus span, but not from STEALING
       the partner of a later legitimate mention -- the interior still supplies
       a delimiter, one level down. Measured hard failure:
       ``<!-- drop the ` here --> Write `<!--` to mention it`` raised
       "unterminated HTML comment" on a line containing no such thing, failing
       the whole site build.

    Both are the same root cause: filtering the OUTPUT of a whole-line pairing
    cannot express "a comment's interior contributes no delimiters". Only
    interleaving can, because a skipped comment's runs are never examined.

    Linear by construction. `_next_run_of_same_length` is precomputed in one
    backward pass, so pairing is O(1) per run and never rescans -- no quadratic
    recompute (a per-segment re-pair measured 4.6 s on 3,000 inline pairs) and
    no backtracking regex (measured 74 s on a 12 KB backtick run).
    """
    runs = _backtick_runs(line)
    # run index -> index of the next run of identical length, or -1.
    next_same: list[int] = [-1] * len(runs)
    latest: dict[int, int] = {}
    for index in range(len(runs) - 1, -1, -1):
        next_same[index] = latest.get(runs[index][1], -1)
        latest[runs[index][1]] = index
    run_at = {start: index for index, (start, _) in enumerate(runs)}

    pieces: list[str] = []
    kept_from = 0
    position = 0
    length = len(line)

    while position < length:
        if line.startswith("<!--", position):
            # A real comment: emit what precedes it and skip its whole extent.
            # Its interior is never scanned, so nothing inside it can pair.
            pieces.append(line[kept_from:position])
            closer = line.find("-->", position + len("<!--"))
            if closer < 0:
                return "".join(pieces), True
            kept_from = closer + len("-->")
            position = kept_from
            continue
        if line[position] == "`":
            index = run_at[position]
            partner = next_same[index]
            if partner < 0:
                # An unpaired run is literal text, not a delimiter.
                position += runs[index][1]
            else:
                # A code span: skip it whole, mention and all.
                position = runs[partner][0] + runs[partner][1]
            continue
        position += 1

    pieces.append(line[kept_from:])
    return "".join(pieces), False


def _slug_base(text: str) -> str:
    """Reproduce `github-slugger`'s slug for one heading's text.

    Starlight generates heading anchors with `github-slugger`, so the fragment a
    Now source link must point at is decided by that algorithm — not by anything
    this repository chooses. Reimplemented rather than guessed: the accompanying
    construction test asserts this function reproduces every `<h2>` id in the
    emitted changelog page, which is the only evidence that the two agree.
    """
    slug = text.strip().lower()
    # github-slugger strips a fixed control/punctuation set and keeps word
    # characters, spaces and hyphens. Notably `[`, `]`, `.` and the em dash all
    # vanish, while the spaces around a removed em dash each survive as one
    # hyphen — which is why the emitted ids carry a `--`.
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    return slug.replace(" ", "-")


class _Slugger:
    """github-slugger's duplicate handling: the Nth repeat gains a `-N` suffix.

    Load-bearing for correctness, not tidiness. `changelog.md` repeats
    `[core][2.3.0] — 2026-08-07`, so the second occurrence is emitted as
    `core230--2026-08-07-1`. A slug derived from heading text alone would send a
    Now source link to the wrong release.
    """

    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        base = _slug_base(text)
        count = self._seen.get(base, 0)
        self._seen[base] = count + 1
        return base if count == 0 else f"{base}-{count}"


def _parse_release_identity(title: str) -> dict | None:
    """Return package/version/date identity for a release heading, else None.

    None means "not a release entry" — an `[Unreleased]` heading, a `### Added`
    group, or prose. A heading that looks like a release but carries a malformed
    date is a source defect and raises, because silently dropping it would
    under-report the launch window.
    """
    if _RELEASE_LEAD_RE.match(title) is None:
        return None
    packages = [
        {"name": name, "version": version}
        for name, version in _RELEASE_PKG_RE.findall(title)
    ]
    # `## [Unreleased][unreleased] — 2026-08-18` is a RELEASE-SHAPED heading that
    # means the opposite: it is the Markdown reference-link form older Keep a
    # Changelog templates ship, and this file still carries the matching
    # `[Unreleased]: https://…compare/v1.0.0...HEAD` definition it pairs with.
    #
    # Returning None hands it to the Unreleased region test, which is the only
    # correct destination. The two alternatives both fail: treating it as a
    # release publishes every dated child beneath it, and letting it reach the
    # date check hard-fails the site build on the undated form.
    #
    # Checked across EVERY pair and BOTH slots. Scoping it to the first pair's
    # name left two live bypasses: `## [agentbundle][unreleased] — 2026-08-18`
    # published its Highlights and rendered the public label
    # "agentbundle unreleased" — a version left as `unreleased` while the number
    # is still being cut is the realistic trigger — and the multi-package form
    # `## [Unreleased][unreleased] and [core][2.7.4] — 2026-08-17`, which is a
    # shape this changelog actually uses, skipped the guard entirely. Neither
    # produced any diagnostic, so the required pin could not see them either.
    #
    # An exact-token test, not a substring one, so `unreleased-tools` and
    # `my-unreleased` keep releasing. The guard this replaced compared through
    # `_UNRELEASED_RE` and died silently when that pattern was broadened to a
    # bare `unreleased` — `.match` against a string starting with `[` can never
    # succeed.
    if any(
        part.casefold() == "unreleased"
        for pkg in packages
        for part in (pkg["name"], pkg["version"])
    ):
        return None
    date_match = _RELEASE_DATE_RE.search(title)
    if date_match is None:
        # Package identity but no trailing date — e.g.
        # `## [pkg][1.0.0] — 2026-08-17 (yanked)`. Returning None here treats it
        # as "not a release", which silently drops its Highlights or donates
        # them to whichever entry happens to be open. Fail closed instead; the
        # real changelog has no such heading (verified), so this can only fire
        # on a genuine authoring mistake.
        raise ValueError(
            "changelog release heading carries a package version but no "
            f"trailing release date: {title!r}"
        )
    year, month, day = (int(g) for g in date_match.groups())
    try:
        # `date()` rather than a 1..31 range check: the range accepts
        # 2026-02-31, which then renders as "31 February 2026" behind an invalid
        # <time datetime>.
        release_date = date(year, month, day)
    except ValueError as exc:
        raise ValueError(
            f"changelog release heading has an impossible date: {title!r}"
        ) from exc
    return {"packages": packages, "date": release_date.isoformat()}


class ParsedChangelog(NamedTuple):
    """Release records plus the authoring problems worth reporting.

    Diagnostics are returned, not stashed on the function: as a function attribute
    they were hidden module state assigned only on the success path, and they
    forced a second parse.
    """

    releases: list[dict]
    diagnostics: dict


def parse_changelog_releases(text: str) -> ParsedChangelog:
    """Extract every release entry, its optional Highlights, and any diagnostics.

    Releases are source-order records carrying package identity, release date,
    heading text, anchor slug, whether the entry sits beneath `Unreleased`, and
    the Highlights bullets when the entry declares them.
    """
    lines = text.splitlines()
    slugger = _Slugger()
    releases: list[dict] = []

    # (level, is_unreleased) for every heading currently enclosing this line.
    stack: list[tuple[int, bool]] = []
    current: dict | None = None
    # Heading level of the release entry `current` refers to. Tracked because a
    # release entry's scope has to CLOSE: without it, `current` survives every
    # following non-release heading, and a `### Highlights` under a later
    # `## Notes for maintainers` appends its bullets to the previous release.
    entry_level: int | None = None
    # Level of the Highlights heading whose bullets we are collecting, if any.
    highlights_level: int | None = None
    in_fence = False
    fence_opened_at: int | None = None
    fence_marker: str | None = None
    in_comment = False
    comment_opened_at: int | None = None
    ambiguous: list[tuple[int, str]] = []
    misplaced: list[tuple[int, int, str]] = []

    for lineno, raw in enumerate(lines, start=1):
        # Fenced code wins over comment syntax: `<!--` inside a shell sample is
        # sample text, not a comment.
        if in_fence:
            closer = _FENCE_RE_CHANGELOG.match(raw)
            # CommonMark's closer rule has THREE parts, and each missing one was
            # its own fail-open: same marker character, run at least as long as
            # the opener, and nothing but whitespace after the run. Without the
            # third, ```` ```bash ```` closes a ```` ``` ```` block, the sample's
            # release heading becomes a real entry, and the two trailing markers
            # restore parity so the unterminated-fence raise never fires.
            if (
                closer is not None
                and fence_marker is not None
                and closer.group(2)[0] == fence_marker[0]
                and len(closer.group(2)) >= len(fence_marker)
                and closer.group(3).strip() == ""
            ):
                in_fence = False
                fence_opened_at = None
                fence_marker = None
            # A `#` inside a fenced block is shell syntax, not a heading, and a
            # `-` inside one is not a bullet.
            continue

        # HTML comments must be skipped, not merely ignored as unmatched text.
        # `changelog.md` ships a commented-out `## [1.0.0] — YYYY-MM-DD` release
        # template, and without this a commented-out entry publishes its
        # Highlights — trailing `-->` and all. It also consumes a `_Slugger`
        # slot that `github-slugger` never sees, which would shift every later
        # `-N` suffix and point source links at the wrong release.
        if in_comment:
            # Deliberately code-span blind: Markdown is not parsed inside an
            # HTML comment, so backticks cannot mask its real closer.
            if "-->" not in raw:
                continue
            in_comment = False
            comment_opened_at = None
            raw = raw.split("-->", 1)[1]
        raw, opens_comment = _strip_changelog_comments(raw)
        if opens_comment:
            in_comment = True
            comment_opened_at = lineno
            # Deliberate divergence from lint-spec-status.py: this builder does
            # not treat an unterminated real opener as literal text. The final
            # raise prevents one typo from silently swallowing later releases.

        opener = _FENCE_RE_CHANGELOG.match(raw)
        if opener is not None:
            # The opener is matched LOOSELY on indentation. A fence indented four
            # spaces is the ordinary shape inside a list item, and tightening
            # this to `^ {0,3}` while fixing the closer rule regressed those into
            # published copy — literal backticks and sample lines reaching the
            # public page. For this parser a loose opener fails closed (more
            # content skipped) and a strict closer fails closed (the fence stays
            # open, and if it never closes the raise below fires).
            in_fence = True
            fence_opened_at = lineno
            fence_marker = opener.group(2)
            continue

        heading = _CHANGELOG_HEADING_RE.match(raw)
        if heading is None:
            if highlights_level is not None and current is not None:
                bullet = _BULLET_RE.match(raw)
                if bullet is not None:
                    body = bullet.group(1).strip()
                    if body:
                        current["highlights"].append(body)
                elif raw.strip() and current["highlights"]:
                    # A continuation line of the previous bullet: changelog
                    # bullets wrap, and dropping the tail would truncate copy
                    # mid-sentence on the public page.
                    current["highlights"][-1] += " " + raw.strip()
            continue

        level = len(heading.group(1))
        title = heading.group(2).strip()
        slug = slugger.slug(title)

        while stack and stack[-1][0] >= level:
            stack.pop()
        if highlights_level is not None and level <= highlights_level:
            highlights_level = None
        # A heading at or above the open entry's level ends that entry, whatever
        # it is. `### Added` under `## [pkg][1.0.0]` is deeper and leaves the
        # entry open, which is correct; `## Notes for maintainers` is a sibling
        # and closes it.
        if entry_level is not None and level <= entry_level:
            current = None
            entry_level = None

        beneath_unreleased = any(is_unreleased for _, is_unreleased in stack)

        identity = _parse_release_identity(title)

        # Release identity is decided FIRST. A release heading is never an
        # Unreleased region opener, so a package literally named `unreleased-foo`
        # cannot suppress its own entry.
        if identity is None and _UNRELEASED_RE.search(title):
            stack.append((level, True))
            current = None
            entry_level = None
            if title.strip().strip("[]").casefold() != "unreleased":
                # A non-canonical opener. Honoured — nothing beneath it publishes
                # — but reported, so an author whose section stopped publishing
                # can see which heading did it.
                ambiguous.append((lineno, title))
            continue

        if identity is not None:
            current = {
                "packages": identity["packages"],
                "date": identity["date"],
                "heading": title,
                "anchor": slug,
                "unreleased": beneath_unreleased,
                "highlights": [],
            }
            entry_level = level
            releases.append(current)
            stack.append((level, False))
            continue

        # A `Highlights` heading counts only as the entry's IMMEDIATE child. At
        # any other depth it belongs to something else, and attaching its
        # bullets to the nearest open release publishes copy under a release
        # that does not claim it.
        if _HIGHLIGHTS_RE.match(title):
            if entry_level is not None and level == entry_level + 1:
                highlights_level = level
            else:
                # Refused — and silently so without this. A `#### Highlights`
                # under `### Changed` is the second-likeliest authoring mistake
                # and produced output identical to writing nothing.
                misplaced.append((lineno, level, title))
        stack.append((level, False))

    if in_fence:
        # One stray fence would otherwise swallow every release after it, and
        # the drift gate cannot see the loss because expected and committed
        # values come from this same parser.
        raise ValueError(
            "changelog has an unterminated code fence opened at line "
            f"{fence_opened_at}; every release after it would be ignored"
        )
    if in_comment:
        raise ValueError(
            "changelog has an unterminated HTML comment opened at line "
            f"{comment_opened_at}; every release after it would be ignored"
        )

    return ParsedChangelog(
        releases=releases,
        diagnostics={
            "withheld_unreleased": [
                (r["heading"], len(r["highlights"]))
                for r in releases
                if r["unreleased"] and r["highlights"]
            ],
            "misplaced_highlights": misplaced,
            "unreleased_regions": ambiguous,
        },
    )


_INLINE_MD_RE = re.compile(r"\*\*(.+?)\*\*|`(.+?)`", re.DOTALL)


def highlight_segments(bullet: str) -> list[dict]:
    """Split one Highlights bullet into typed render segments.

    Changelog bullets are Markdown, and the Now renderer must not receive raw
    Markdown (it would print literal asterisks) nor a raw HTML string (it would
    hand an authored file an injection seam into a public page). Segments keep
    the emphasis the house style relies on — `**Lead.** Body` — while leaving
    escaping to the template, which escapes text nodes by default.

    Only the two inline forms the changelog actually uses are recognised. An
    unsupported form stays literal rather than being silently dropped, so the
    text on the page is never less than what the source says.
    """
    segments: list[dict] = []
    cursor = 0
    for match in _INLINE_MD_RE.finditer(bullet):
        if match.start() > cursor:
            segments.append({"type": "text", "value": bullet[cursor:match.start()]})
        strong, code = match.group(1), match.group(2)
        if strong is not None:
            segments.append({"type": "strong", "value": strong})
        else:
            segments.append({"type": "code", "value": code})
        cursor = match.end()
    if cursor < len(bullet):
        segments.append({"type": "text", "value": bullet[cursor:]})
    return segments


def launch_window(end_date: str, days: int = NOW_WINDOW_DAYS) -> tuple[str, str]:
    """Inclusive [start, end] ISO dates for the `days`-long launch-seed window.

    Sole caller is
    `tools/test_build_site_routing.py::test_the_launch_seed_covers_exactly_the_released_entries_in_its_window`.
    Deliberately not called by the generator — see below.

    The window is an AUTHORING rule, not a render filter. It decides which
    released entries should have gained a `Highlights` block by launch day; it
    never limits what `/now/` publishes afterwards. Keeping it out of the
    projection is what makes the projection deterministic — a date window
    evaluated at build time would change the page every midnight from unchanged
    source, which the spec forbids.
    """
    end = date.fromisoformat(end_date)
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def project_now_highlights(text: str) -> dict:
    """Project the public `/now/` payload from changelog source.

    Only released entries — versioned, dated, and outside every `Unreleased`
    region — that declare Highlights reach the payload. Groups sort by release
    date descending and preserve source order for equal dates.

    Pure and clock-free: the same source bytes always produce the same payload.
    """
    return _project_parsed(parse_changelog_releases(text))


def _project_parsed(parsed: ParsedChangelog) -> dict:
    """Build the payload from an already-parsed changelog."""
    eligible = [
        r for r in parsed.releases if not r["unreleased"] and r["highlights"]
    ]

    # `sorted` is stable, so equal dates keep source order without a tiebreak
    # key. An index tiebreak would have to be reversed alongside the date and is
    # easy to get backwards; leaning on stability cannot drift.
    ordered = sorted(eligible, key=lambda r: r["date"], reverse=True)

    return {
        "schemaVersion": 1,
        "groups": [
            {
                "packages": r["packages"],
                "date": r["date"],
                "heading": r["heading"],
                "changelogAnchor": r["anchor"],
                "highlights": [
                    {"source": bullet, "segments": highlight_segments(bullet)}
                    for bullet in r["highlights"]
                ],
            }
            for r in ordered
        ],
    }


def generate_now_projection(
    out: Path,
    changelog: Path,
    dry_run: bool = False,
) -> tuple[dict, dict]:
    """Write the `/now/` projection JSON; return (payload, diagnostics).

    Diagnostics come back with the payload so the caller does not parse a
    4,000-line file a second time to report them.
    """
    parsed = parse_changelog_releases(changelog.read_text(encoding="utf-8"))
    payload = _project_parsed(parsed)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if not dry_run:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    return payload, parsed.diagnostics


def _report_now_projection(changelog: Path, dry_run: bool = False) -> None:
    """Emit the `/now/` projection and print what reached the public page.

    Also names what did NOT publish. Writing a `Highlights` block under an entry
    that is still `[Unreleased]` is the overwhelmingly likely authoring mistake,
    and it is indistinguishable from writing nothing at all if generation only
    reports successes — the author is left reading the parser to find out why
    their copy never appeared.
    """
    if not changelog.exists():
        # Returning here would leave the marketing build rendering whatever
        # projection was last committed — a stale public page reported as a
        # successful build.
        raise FileNotFoundError(
            f"{changelog} is missing; /now/ cannot be projected"
        )
    payload, diagnostics = generate_now_projection(
        NOW_PROJECTION, changelog, dry_run=dry_run
    )
    groups = payload["groups"]
    bullets = sum(len(g["highlights"]) for g in groups)
    print(
        f"  {bullets} released highlight(s) in {len(groups)} release group(s)"
        + (" (dry run)" if dry_run else "")
    )
    for heading, count in diagnostics["withheld_unreleased"]:
        print(
            f"  note  {count} highlight(s) not published — "
            f"beneath [Unreleased]: {heading}"
        )
    for lineno, level, title in diagnostics["misplaced_highlights"]:
        print(
            f"  note  line {lineno}: '{'#' * level} {title}' is not a release "
            "entry's immediate child, so its bullets do not publish"
        )
    for lineno, title in diagnostics["unreleased_regions"]:
        print(
            f"  note  line {lineno}: heading {title!r} reads as Unreleased, so "
            "nothing beneath it publishes; reword it if that is wrong"
        )


def load_guide_baseline(path: Path) -> dict:
    """Read the frozen pre-change ``(slug, label)`` navigation baseline.

    Missing file returns ``{}`` — the generator still produces a sidebar, it
    just derives every label instead of preserving the curated ones.
    """
    if not path.exists():
        return {}
    with path.open("rb") as f:
        data = tomllib.load(f)
    baseline = {}
    for i, e in enumerate(data.get("entry", [])):
        if not e.get("slug") or not e.get("label"):
            print(
                f"  warn  {path.name} entry {i} missing 'slug' or 'label' — skipping",
                file=sys.stderr,
            )
            continue
        baseline[e["slug"]] = e["label"]
    return baseline


def build_guides_sidebar_group(repo_root: Path, site_toml: Path) -> dict | None:
    """Collate the guides tree and project it into the ``Guides`` sidebar group."""
    guides_root = repo_root / "guides"
    if not guides_root.exists():
        return None
    with site_toml.open("rb") as f:
        guide_groups = tomllib.load(f).get("guide_groups", [])
    records = build_guide_inventory(guides_root)
    baseline = load_guide_baseline(repo_root / "guide-nav-baseline.toml")
    group = project_guide_sidebar(records, guide_groups, baseline)

    # The failure this change removes — pages published but unreachable — was
    # invisible precisely because nothing counted. Report on every run.
    eligible = sum(1 for r in records if r["nav_eligible"])
    declared = {g.get("dir") for g in guide_groups}
    fallback = sorted({r["pack"] for r in records
                       if r["nav_eligible"] and r["pack"] and r["pack"] not in declared})
    n_groups = sum(1 for i in group["items"] if "items" in i)
    print(f"  guides  {eligible} navigable page(s) in {n_groups} group(s)")
    if fallback:
        print(f"  warn    undeclared in site.toml [[guide_groups]]: {', '.join(fallback)}",
              file=sys.stderr)
    return group


def generate_sidebar_config(packs: list[dict], out: Path, dry_run: bool = False,
                            guides_group: dict | None = None) -> None:
    """Write docs-site/src/sidebar-config.json — an array of Starlight sidebar groups."""
    groups_seen: list[str] = []
    groups_map: dict[str, list[dict]] = {}
    for p in packs:
        g = p["group"]
        if g not in groups_map:
            groups_seen.append(g)
            groups_map[g] = []
        groups_map[g].append({"label": p["display_name"], "slug": f"packs/{p['slug']}"})

    sidebar: list[dict] = [
        {"label": "Pack Catalogue", "items": [{"label": "All Packs", "slug": "packs"}]},
    ]
    for g in groups_seen:
        sidebar.append({"label": g, "items": groups_map[g]})

    if guides_group:
        sidebar.append(guides_group)

    payload = json.dumps(sidebar, indent=2)
    if dry_run:
        print(
            f"  gen   docs-site/src/sidebar-config.json"
            f" ({len(payload)} bytes, {len(sidebar)} groups)"
        )
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--journeys-only",
        action="store_true",
        help="Sync pack-local JOURNEY.md files only; skip Starlight aggregation.",
    )
    args = parser.parse_args()

    packs_dir = REPO_ROOT / "packs"

    changelog_src = REPO_ROOT / "docs" / "product" / "changelog.md"
    site_toml = REPO_ROOT / "site.toml"
    # Validate the complete shared vocabulary before either build path can
    # project or clean renderer inputs.
    shared_chrome_contract = load_shared_chrome_contract(site_toml)

    if args.journeys_only:
        journey_dir = REPO_ROOT / "web" / "src" / "content" / "journeys"
        n = sync_pack_journeys(packs_dir, journey_dir, dry_run=args.dry_run)
        print(
            f"build-site: synced {n} pack journey(s)"
            + (" (dry run)" if args.dry_run else "")
        )
        # Both marketing-renderer inputs are projected in this pre-build phase.
        # Ordering is load-bearing: the workflow runs this pass BEFORE
        # `npm run build --prefix web`, and the full pass only afterwards, so a
        # projection emitted solely by the full pass would always be one build
        # stale for the renderer that consumes it.
        generate_marketing_shared_chrome_projection(
            shared_chrome_contract, dry_run=args.dry_run
        )
        _report_now_projection(changelog_src, dry_run=args.dry_run)
        return

    packs_out = SITE_DOCS / "packs"
    guides_src = REPO_ROOT / "guides"
    guides_out = SITE_DOCS / "guides"

    if args.clean and not args.dry_run:
        for d in (packs_out, guides_out):
            if d.exists():
                shutil.rmtree(d)
                print(f"  clean {d.relative_to(REPO_ROOT)}/")

    packs = discover_packs(REPO_ROOT, site_toml)

    print("build-site: copying pack READMEs …")
    # Guarded: every other write in this script honours --dry-run, and this one
    # did not, so `--dry-run` created generated directories on its way to
    # reporting that it would create them. That makes the flag useless as a
    # read-only check — it fails outright against a non-writable tree, and
    # against a writable one it leaves directories behind.
    if not args.dry_run:
        packs_out.mkdir(parents=True, exist_ok=True)
    for p in packs:
        src = packs_dir / p["slug"] / "README.md"
        dst = packs_out / f"{p['slug']}.md"
        if src.exists():
            copy_file(
                src, dst,
                rewriter=lambda t, s=src: _rewrite_pack_readme(t, s),
                dry_run=args.dry_run,
            )
        else:
            print(f"  warn  packs/{p['slug']}/README.md missing", file=sys.stderr)

    print("build-site: generating packs/index.md …")
    build_pack_index(packs, packs_out, dry_run=args.dry_run)

    print("build-site: syncing pack journeys …")
    _n_journeys = sync_pack_journeys(
        packs_dir,
        REPO_ROOT / "web" / "src" / "content" / "journeys",
        dry_run=args.dry_run,
    )
    if _n_journeys:
        print(f"  {_n_journeys} pack-local JOURNEY.md files synced")

    print("build-site: generating sidebar-config.json …")
    sidebar_out = REPO_ROOT / "docs-site" / "src" / "sidebar-config.json"
    guides_group = build_guides_sidebar_group(REPO_ROOT, site_toml)
    generate_sidebar_config(packs, sidebar_out, dry_run=args.dry_run,
                            guides_group=guides_group)

    print("build-site: mirroring guides …")
    n = mirror_guides(guides_src, SITE_DOCS, dry_run=args.dry_run)
    print(f"  {n} files from guides/")

    print("build-site: projecting released changelog highlights …")
    _report_now_projection(changelog_src, dry_run=args.dry_run)

    print("build-site: projecting marketing shared chrome …")
    generate_marketing_shared_chrome_projection(
        shared_chrome_contract, dry_run=args.dry_run
    )

    # Docs runs last in the load-bearing build order. Its committed input is
    # therefore refreshed only here, immediately before `npm run build --prefix
    # docs-site`; unlike marketing, it is not needed in the journeys-only pass.
    print("build-site: projecting docs shared chrome …")
    generate_docs_shared_chrome_projection(
        shared_chrome_contract, dry_run=args.dry_run
    )

    print("build-site: copying changelog …")
    changelog_dst = SITE_DOCS / "changelog.md"
    # Unconditional: `_report_now_projection` above already raised if the source
    # were absent, so an `exists()` guard here would read as a supported
    # missing-changelog path that cannot occur.
    copy_file(changelog_src, changelog_dst, rewriter=_rewrite_changelog, dry_run=args.dry_run)

    print("build-site: copying contributing guide …")
    contributing_src = REPO_ROOT / "CONTRIBUTING.md"
    contributing_dst = SITE_DOCS / "contributing.md"
    if contributing_src.exists():
        copy_file(
            contributing_src, contributing_dst,
            rewriter=_rewrite_contributing,
            dry_run=args.dry_run,
        )
    else:
        print("  warn  CONTRIBUTING.md missing", file=sys.stderr)

    # No design-token copy. `docs-site/src/styles/starlight.css` is a self-contained
    # token sheet and stopped importing the copied file; ADR-0085 makes docs
    # rendering site-local, superseding ADR-0055's token-sharing sub-decision. The
    # copy was vestigial, and the accompanying hard failure —
    # "web/src/styles/tokens.css missing — docs-site CSS depends on it" — asserted a
    # dependency that no longer existed, so a marketing-side change could stop
    # generation for a file the docs site does not read.

    # Whole-build totals, printed last: the two transforms run across the guide
    # mirror AND the pack-README copies, so a per-stage line would attribute
    # pack strips to the guides stage. `--dry-run` short-circuits copy_file
    # before the transform, so its totals are lower by design.
    print(
        f"build-site: {_TRANSFORM_COUNTS['h1_stripped']} body H1(s) stripped, "
        f"{_TRANSFORM_COUNTS['summary_mapped']} summary→description"
        + (" (dry run — copies short-circuited)" if args.dry_run else "")
    )
    print("build-site: done." + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
